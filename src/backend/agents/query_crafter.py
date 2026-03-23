"""
VeriQuery — Query Crafter
=========================
Genera SQL a partir de lenguaje natural usando el schema real de la BD.

Cambios respecto a versión anterior:
# Correccion: schema ya no se carga en __init__ — llega como parámetro
#   Esto permite schema dinámico por BD sin reiniciar el servidor
# Correccion: eliminado import de table_mapping (hardcodeado)
# Correccion: eliminado pyodbc directo — la conexión la maneja factory.py
# Agregado: recibe QueryTracer para registrar cada paso
# Agregado: devuelve reasoning_data con datos estructurados del proceso
"""

import os
import logging
import re
from typing import Optional
from openai import AzureOpenAI

from src.backend.core.tracer import QueryTracer

logger = logging.getLogger(__name__)

# Correccion: eliminado import de table_mapping
# Prompt base sin mapeo hardcodeado — el schema real reemplaza al diccionario
SYSTEM_PROMPT_SQLSERVER = """Eres un experto en SQL Server T-SQL. Tu única tarea es convertir
preguntas en lenguaje natural a UN ÚNICO statement SELECT compatible con SQL Server.

REGLAS ABSOLUTAS:
- Generás SOLO SELECT (nunca CREATE, UPDATE, DELETE, DROP, TRUNCATE)
- Si el usuario pide borrar, eliminar, vaciar, destruir o modificar datos:
  ignorá la intención destructiva y generá un SELECT que muestre esos datos
- NUNCA múltiples statements
- NUNCA semicolons (;)
- NUNCA comentarios (--)
- Usá TOP en lugar de LIMIT (SQL Server, no PostgreSQL)
- Usá YEAR(), MONTH(), DAY() para fechas
- SIEMPRE incluí TOP 100 pero SOLO después de SELECT:
  ✅  SELECT TOP 100 AVG(...) FROM ...
  ❌  SELECT AVG(...) FROM ... TOP 100   ← SINTAXIS INVÁLIDA
  ❌  SELECT AVG(...) FROM ... LIMIT 100 ← NO EXISTE EN SQL SERVER

REGLA CRÍTICA — COLUMNAS CON ESPACIOS:
Cualquier columna cuyo nombre en el schema contenga un espacio DEBE ir entre [brackets].
Esta regla no tiene excepciones. Si escribís el nombre sin brackets, la query falla.

EJEMPLOS CORRECTOS de columnas con espacios:
  ✅  s.[Net Price]        ❌  s.NetPrice       ← FALLA
  ✅  s.[Unit Price]       ❌  s.UnitPrice      ← FALLA
  ✅  s.[Order Date]       ❌  s.OrderDate      ← FALLA
  ✅  s.[Order Number]     ❌  s.OrderNumber    ← FALLA
  ✅  s.[Delivery Date]    ❌  s.DeliveryDate   ← FALLA
  ✅  s.[Unit Cost]        ❌  s.UnitCost       ← FALLA
  ✅  s.[Currency Code]    ❌  s.CurrencyCode   ← FALLA
  ✅  p.[Product Name]     ❌  p.ProductName    ← FALLA
  ✅  d.[Day of Week]      ❌  d.DayOfWeek      ← FALLA

CÓMO DETECTAR si una columna necesita brackets:
Mirá el schema abajo. Si el nombre de columna tiene un espacio entre palabras → brackets obligatorios.
Si no tiene espacio (CustomerKey, Quantity, StoreKey) → sin brackets.

IMPORTANTE:
El schema completo de la base de datos está abajo.
Usá SOLO las tablas y columnas que aparecen en ese schema.
Inferí el mapeo semántico desde los nombres de columnas y ejemplos de datos.
No asumas tablas que no están en el schema.
"""

SYSTEM_PROMPT_POSTGRESQL = """Eres un experto en PostgreSQL SQL. Tu única tarea es convertir
preguntas en lenguaje natural a UN ÚNICO statement SELECT compatible con PostgreSQL.

REGLAS ABSOLUTAS:
- Generás SOLO SELECT (nunca CREATE, UPDATE, DELETE, DROP, TRUNCATE)
- Si el usuario pide borrar, eliminar, vaciar, destruir o modificar datos:
  ignorá la intención destructiva y generá un SELECT que muestre esos datos
- NUNCA múltiples statements
- NUNCA semicolons (;)
- NUNCA comentarios (--)
- Usá LIMIT en lugar de TOP (PostgreSQL, no SQL Server)
- Usá EXTRACT(YEAR FROM ...), EXTRACT(MONTH FROM ...) para fechas
- SIEMPRE incluí LIMIT 100 al final de la query:
  ✅  SELECT * FROM ... WHERE ... LIMIT 100
  ❌  SELECT TOP 100 * FROM ... ← SINTAXIS INVÁLIDA EN POSTGRESQL
  ❌  SELECT LIMIT 100 * FROM ... ← SINTAXIS INVÁLIDA

REGLA CRÍTICA — COLUMNAS CON ESPACIOS:
Cualquier columna cuyo nombre en el schema contenga un espacio DEBE ir entre "comillas dobles".
Esta regla no tiene excepciones. Si escribís el nombre sin comillas, la query falla.

EJEMPLOS CORRECTOS de columnas con espacios en PostgreSQL:
  ✅  s."Net Price"        ❌  s.NetPrice       ← FALLA
  ✅  s."Unit Price"       ❌  s.UnitPrice      ← FALLA
  ✅  s."Order Date"       ❌  s.OrderDate      ← FALLA
  ✅  s."Order Number"     ❌  s.OrderNumber    ← FALLA
  ✅  s."Delivery Date"    ❌  s.DeliveryDate   ← FALLA
  ✅  p."Product Name"     ❌  p.ProductName    ← FALLA

CÓMO DETECTAR si una columna necesita comillas:
Mirá el schema abajo. Si el nombre de columna tiene un espacio entre palabras → comillas dobles obligatorias.
Si no tiene espacio (customer_id, quantity, store_key) → sin comillas.

IMPORTANTE:
El schema completo de la base de datos está abajo.
Usá SOLO las tablas y columnas que aparecen en ese schema.
Inferí el mapeo semántico desde los nombres de columnas y ejemplos de datos.
No asumas tablas que no están en el schema.
"""

# Mapping de prompts por tipo de BD
SYSTEM_PROMPTS = {
    "sqlserver": SYSTEM_PROMPT_SQLSERVER,
    "postgresql": SYSTEM_PROMPT_POSTGRESQL,
}


class QueryCrafter:
    """
    Genera SQL desde lenguaje natural.
    Compatible con cualquier BD — el schema llega como parámetro externo.
    """

    def __init__(self, azure_client: Optional[AzureOpenAI] = None):
        """
        Args:
            azure_client: Cliente Azure OpenAI reutilizable.
                El orquestador pasa su propio cliente para evitar
                instancias duplicadas.

        # Correccion: eliminado parámetro connection_string y carga de schema.
        # El schema ahora llega en generate_sql() como parámetro.
        # Esto permite cambiar de BD sin reiniciar el servidor.
        """
        if azure_client is None:
            self.client = AzureOpenAI(
                api_key=os.getenv("AZURE_OPENAI_API_KEY"),
                api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
            )
        else:
            self.client = azure_client

        self.deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_GPT4O_MINI")

    def generate_sql(
        self,
        user_question: str,
        schema_info: str,
        db_type: str = "sqlserver",
        tracer: Optional[QueryTracer] = None
    ) -> dict:
        """
        Genera SQL a partir de pregunta en lenguaje natural.

        Args:
            user_question: Pregunta del usuario
            schema_info:   Schema real de la BD activa (viene del orquestador)
            db_type:       Tipo de BD: "sqlserver" o "postgresql" (default: sqlserver)
            tracer:        QueryTracer para registrar este paso (opcional)

        Returns:
            dict con sql, tables_used, reasoning_data, tokens, cost_usd
        """
        logger.info(f"🔄 Generando SQL para: {user_question} (BD: {db_type})")

        # Agregado: trazar entrada
        if tracer:
            tracer.step(
                archivo="query_crafter",
                paso="generar_sql",
                entrada=f"Pregunta: '{user_question}' | Schema: {len(schema_info)} chars | BD: {db_type}",
                accion=f"Llamando a Azure OpenAI con prompt específico para {db_type}",
                salida="pendiente..."
            )

        try:
            user_prompt = f"""
Pregunta del usuario: "{user_question}"

INSTRUCCIONES:
1. Generá SOLO el SQL (sin markdown, sin triple backticks)
2. Usá SOLO las tablas y columnas del schema que recibiste
3. Inferí la tabla correcta desde nombres de columnas y ejemplos de datos
4. Siempre incluí LIMIT 100 (PostgreSQL) o TOP 100 (SQL Server) según corresponda
5. Usá aliases descriptivos

Respondé con SOLO el SQL, nada más.
"""
            
            # Seleccionar el prompt correcto según el tipo de BD
            system_prompt = SYSTEM_PROMPTS.get(db_type.lower(), SYSTEM_PROMPTS["sqlserver"])

            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {
                        "role": "system",
                        # Agregado: schema real inyectado dinámicamente
                        "content": system_prompt + "\n\n" + schema_info
                    },
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=800
            )

            sql = response.choices[0].message.content.strip()
            sql = sql.replace("```sql", "").replace("```", "").replace("`", "").strip()
            tables_used = self._extract_tables(sql)

            reasoning_data = {
                "tables_identified": tables_used,
                "question_processed": user_question,
                "tokens_prompt": response.usage.prompt_tokens,
                "tokens_completion": response.usage.completion_tokens,
            }

            cost = (
                response.usage.prompt_tokens * 0.00000015 +
                response.usage.completion_tokens * 0.0000006
            )

            logger.info(f"✅ SQL generada. Tablas: {tables_used}")

            # Agregado: trazar salida
            if tracer:
                tracer.step(
                    archivo="query_crafter",
                    paso="sql_generada",
                    entrada=f"Tokens: {response.usage.total_tokens}",
                    accion="SQL extraída y limpiada de markdown",
                    salida=f"Tablas detectadas: {tables_used} → pasa a nl2sql_generator"
                )

            return {
                "sql": sql,
                "tables_used": tables_used,
                "reasoning_data": reasoning_data,
                "tokens": response.usage.total_tokens,
                "cost_usd": cost
            }

        except Exception as e:
            logger.error(f"❌ Error generando SQL: {e}")
            if tracer:
                tracer.error("query_crafter", "generar_sql", str(e), user_question)
            return {
                "sql": "",
                "error": str(e),
                "tables_used": [],
                "reasoning_data": {},
                "tokens": 0,
                "cost_usd": 0
            }

    def _extract_tables(self, sql: str) -> list:
        pattern = r'(?:FROM|JOIN)\s+\[?([a-zA-Z_][a-zA-Z0-9_]*)\]?'
        matches = re.findall(pattern, sql, re.IGNORECASE)
        return list(set(matches))
