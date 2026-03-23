"""
VeriQuery — NL2SQL Generator (Orquestador)
==========================================
Coordina el flujo completo NL → SQL → Respuesta.

# Agregado: schema_name dinámico por tipo de BD
#   SQL Server → TABLE_SCHEMA = 'dbo'
#   PostgreSQL/Supabase → TABLE_SCHEMA = 'public'
#   Resuelve el problema de tablas no encontradas al cambiar de BD
# Agregado: QueryTracer con finalize() — escribe logs/queries/
# Agregado: schema_cache con db_name como clave
# Agregado: set_active_database() para cambio de BD en runtime
# Correccion: eliminado uso de core/schema.py y table_mapping
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dotenv import load_dotenv
from openai import AzureOpenAI

from src.backend.agents.ambiguity_detector import AmbiguityDetector
from src.backend.agents.query_crafter import QueryCrafter
from src.backend.database.factory import get_database_connector
from src.backend.core.tracer import QueryTracer

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Agregado: map de schema_name por tipo de BD
# Cada motor de BD usa un nombre distinto para el schema por defecto
DB_SCHEMA_NAMES = {
    "sqlserver":  "dbo",
    "postgresql": "public",   # PostgreSQL, Supabase, Azure PostgreSQL
    "sqlite":     "main",
}


class NL2SQLGenerator:
    """
    Orquestador del flujo NL → SQL.
    Compatible con SQL Server, PostgreSQL (Supabase, Azure), SQLite.
    """

    def __init__(self):
        self.client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )
        self.deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_GPT4O_MINI")

        # Caché de schemas: {db_name: schema_text}
        self._schema_cache: dict = {}
        self._active_db_name: Optional[str] = None
        self._active_db_type: Optional[str] = None
        self._active_connector = None

        self.ambiguity_detector = AmbiguityDetector()
        self.query_crafter = QueryCrafter(azure_client=self.client)

        self._load_default_database()
        logger.info("✅ NL2SQLGenerator inicializado")

    def _load_default_database(self) -> None:
        """Carga la BD configurada en .env al iniciar."""
        try:
            db_type = os.getenv("DATABASE_TYPE", "sqlserver").lower()
            db_name = os.getenv("DB_NAME", "default")

            connector = get_database_connector()
            connector.connect()

            schema = self._load_schema_from_connector(
                connector=connector,
                db_name=db_name,
                db_type=db_type
            )

            self._schema_cache[db_name] = schema
            self._active_db_name = db_name
            self._active_db_type = db_type
            self._active_connector = connector

            logger.info(
                f"✅ BD por defecto: {db_name} ({db_type}) "
                f"— {len(schema)} chars de schema"
            )
        except Exception as e:
            logger.error(f"❌ No se pudo cargar BD por defecto: {e}")

    def set_active_database_name(self, db_name: str) -> None:
        """
        Cambia el nombre de la BD activa y carga el schema desde Key Vault si es necesario.
        
        Args:
            db_name: Nombre de la BD (ej: "contoso_local", "supabase_prod")
        """
        # Primero, verificar si el schema ya está en caché
        if db_name in self._schema_cache:
            self._active_db_name = db_name
            # Detectar tipo por nombre
            if "postgres" in db_name.lower() or "supabase" in db_name.lower():
                self._active_db_type = "postgresql"
            else:
                self._active_db_type = "sqlserver"
            logger.info(f"✅ BD activa actualizada → '{db_name}' ({self._active_db_type}) — schema desde caché")
            return
        
        # Si no está en caché, intentar cargar desde Key Vault + connector dinámico
        try:
            from src.backend.core.secure_credential_store import SecureCredentialStore
            from src.backend.database import ConnectionConfig, SQLServerConnector, PostgreSQLConnector
            
            store = SecureCredentialStore()
            creds, error = store.get_credentials(db_name)
            
            if creds and not error:
                db_type = creds.get("db_type", "sqlserver").lower()
                
                # Crear connector específico según tipo de BD
                config = ConnectionConfig(
                    host=creds.get("host"),
                    port=int(creds.get("port", 1433 if db_type == "sqlserver" else 5432)),
                    username=creds.get("username"),
                    password=creds.get("password"),
                    database=creds.get("database"),
                    driver=creds.get("driver")
                )
                
                if db_type == "postgresql":
                    connector = PostgreSQLConnector(config)
                else:
                    connector = SQLServerConnector(config)
                
                connector.connect()
                
                # Cargar schema usando el connector conectado
                schema = self._load_schema_from_connector(
                    connector=connector,
                    db_name=db_name,
                    db_type=db_type
                )
                self._schema_cache[db_name] = schema
                self._active_db_name = db_name
                self._active_db_type = db_type
                self._active_connector = connector
                
                logger.info(f"✅ BD activa actualizada → '{db_name}' ({db_type}) — schema cargado desde Key Vault")
                return
        except Exception as e:
            logger.warning(f"⚠️ No se pudo cargar schema desde Key Vault para '{db_name}': {e}")
        
        # Si todo falla, usar el método simple de antes
        self._active_db_name = db_name
        if "postgres" in db_name.lower() or "supabase" in db_name.lower():
            self._active_db_type = "postgresql"
        else:
            self._active_db_type = "sqlserver"
        logger.info(f"✅ BD activa actualizada → '{db_name}' ({self._active_db_type}) — sin schema (usará genérico)")

    def set_active_database(
        self,
        db_name: str,
        connector,
        db_type: str = "sqlserver"
    ) -> dict:
        """
        Cambia la BD activa en runtime sin reiniciar el servidor.
        Llamado desde POST /api/connect en main.py.

        Args:
            db_name:   identificador de la BD (ej: "contoso", "supabase_ong")
            connector: instancia ya conectada
            db_type:   "sqlserver" | "postgresql" | "sqlite"

        Returns:
            dict con success, db_name, schema_chars, cached
        """
        # Usar caché si ya fue cargado para esta BD
        if db_name in self._schema_cache:
            self._active_db_name = db_name
            self._active_db_type = db_type
            self._active_connector = connector
            logger.info(f"✅ BD activa → '{db_name}' (desde caché)")
            return {
                "success": True,
                "db_name": db_name,
                "db_type": db_type,
                "schema_chars": len(self._schema_cache[db_name]),
                "cached": True
            }

        try:
            schema = self._load_schema_from_connector(
                connector=connector,
                db_name=db_name,
                db_type=db_type
            )
            self._schema_cache[db_name] = schema
            self._active_db_name = db_name
            self._active_db_type = db_type
            self._active_connector = connector

            logger.info(
                f"✅ BD activa → '{db_name}' ({db_type}) "
                f"— schema recargado {len(schema)} chars"
            )
            return {
                "success": True,
                "db_name": db_name,
                "db_type": db_type,
                "schema_chars": len(schema),
                "cached": False
            }
        except Exception as e:
            logger.error(f"❌ Error cargando schema de '{db_name}': {e}")
            return {"success": False, "error": str(e)}

    def get_active_schema(self) -> str:
        if self._active_db_name and self._active_db_name in self._schema_cache:
            return self._schema_cache[self._active_db_name]
        
        return "⚠️ Schema no disponible — conectá una BD primero"

    def generate_sql(
        self,
        natural_language_query: str,
        conversation_history: list = None
    ) -> dict:
        """
        Orquesta el flujo completo para una consulta.

        Returns:
            dict con type + trace_steps (si TRACE_RESPONSE=true)
        """
        if conversation_history is None:
            conversation_history = []

        tracer = QueryTracer(question=natural_language_query)

        # ── PASO 1: Ambigüedad ────────────────────────────────────────────
        tracer.step(
            archivo="ambiguity_detector",
            paso="detectar",
            entrada=natural_language_query,
            accion="Buscando keywords ambiguos: mejor, peor, más, menos...",
            salida="pendiente..."
        )

        ambiguity = self.ambiguity_detector.detect(natural_language_query)

        if ambiguity["is_ambiguous"]:
            tracer.step(
                archivo="ambiguity_detector",
                paso="resultado",
                entrada=f"Keywords: {ambiguity['keywords_found']}",
                accion="Ambigüedad detectada",
                salida=f"{len(ambiguity['clarifications'])} opciones → front"
            )
            trace_data = tracer.finalize()
            return {
                "type": "clarification",
                "keywords_found": ambiguity["keywords_found"],
                "clarifications": ambiguity["clarifications"],
                "confidence": ambiguity["confidence"],
                "natural_query": natural_language_query,
                "trace_steps": trace_data
            }

        tracer.step(
            archivo="ambiguity_detector",
            paso="resultado",
            entrada=natural_language_query,
            accion="Sin ambigüedad",
            salida="CLEAR → query_crafter"
        )

        # ── PASO 2: Historial ─────────────────────────────────────────────
        enriched_query = self._enrich_with_history(
            natural_language_query, conversation_history, tracer
        )

        # ── PASO 3: Schema activo ─────────────────────────────────────────
        schema_info = self.get_active_schema()

        tracer.step(
            archivo="nl2sql_generator",
            paso="schema",
            entrada=f"BD activa: {self._active_db_name} ({self._active_db_type})",
            accion="Obteniendo schema desde caché",
            salida=f"{len(schema_info)} chars → inyectar en prompt"
        )

        if "⚠️" in schema_info:
            tracer.error(
                "nl2sql_generator", "schema",
                "Schema no disponible — no hay BD activa"
            )
            trace_data = tracer.finalize()
            return {
                "type": "error",
                "message": "No hay base de datos activa. Conectá una BD primero.",
                "trace_steps": trace_data
            }

        # Avisar si el schema está vacío pero válido (no hay tablas)
        if "Total tablas: 0" in schema_info:
            logger.warning(
                f"[{tracer.question}] ⚠️  Schema vacío para BD '{self._active_db_name}' "
                "— no se encontraron tablas. LLM intentará generar SQL genérico."
            )
            tracer.step(
                archivo="nl2sql_generator",
                paso="schema_warning",
                entrada=f"BD: {self._active_db_name}",
                accion="Schema vacío detectado",
                salida="Procederá con generación genérica de SQL"
            )

        # ── PASO 4: Generar SQL ───────────────────────────────────────────
        crafter_result = self.query_crafter.generate_sql(
            user_question=enriched_query,
            schema_info=schema_info,
            db_type=self._active_db_type or "sqlserver",
            tracer=tracer
        )

        if "error" in crafter_result and not crafter_result.get("sql"):
            tracer.error(
                "query_crafter", "generar_sql",
                crafter_result.get("error", "Error desconocido"),
                enriched_query
            )
            trace_data = tracer.finalize()
            return {
                "type": "error",
                "message": f"No pude generar la consulta: {crafter_result.get('error')}",
                "trace_steps": trace_data
            }

        sql = crafter_result["sql"]
        tables_used = crafter_result.get("tables_used", [])

        # ── PASO 5: Validar SQL ───────────────────────────────────────────
        validation = self._validate_sql(sql, tracer)

        # ── PASO 6: Confidence ────────────────────────────────────────────
        confidence, confidence_label = self._calculate_confidence(
            sql, tables_used, validation
        )

        # ── PASO 7: Reasoning + Explanation ──────────────────────────────
        reasoning = self._build_reasoning(
            natural_language_query, enriched_query,
            sql, tables_used, validation, tracer
        )
        explanation = self._generate_explanation(
            natural_language_query, sql, tracer
        )

        # Finalizar tracer — escribe logs, devuelve dict si TRACE_RESPONSE=true
        trace_data = tracer.finalize()

        return {
            "type": "answer",
            "natural_query": natural_language_query,
            "sql": sql,
            "explanation": explanation,
            "reasoning": reasoning,
            "valid": validation["valid"],
            "validation_notes": validation["notes"],
            "tables_used": tables_used,
            "confidence": confidence,
            "confidence_label": confidence_label,
            "tokens_used": crafter_result.get("tokens", 0),
            "cost_usd": crafter_result.get("cost_usd", 0),
            "active_db": self._active_db_name,
            "active_db_type": self._active_db_type,
            "trace_steps": trace_data
        }

    # ── CARGA DE SCHEMA ───────────────────────────────────────────────────

    def _load_schema_from_connector(
        self,
        connector,
        db_name: str,
        db_type: str = "sqlserver"
    ) -> str:
        """
        Carga schema real desde cualquier conector.

        Agregado: db_type determina el TABLE_SCHEMA correcto:
          - sqlserver  → 'dbo'
          - postgresql → 'public'  (Supabase, Azure PostgreSQL)
          - sqlite     → 'main'

        Esto resuelve el problema de tablas no encontradas
        al conectar a PostgreSQL/Supabase desde código escrito para SQL Server.
        """
        # Agregado: resolver schema_name según el motor
        schema_name = DB_SCHEMA_NAMES.get(db_type.lower(), "dbo")
        logger.info(
            f"📊 Cargando schema de '{db_name}' "
            f"({db_type}) — TABLE_SCHEMA='{schema_name}'"
        )

        try:
            schema_text = (
                f"=== SCHEMA: {db_name} ({db_type}) ===\n"
                f"TABLE_SCHEMA: {schema_name}\n\n"
            )

            # Agregado: query parametrizada con schema_name dinámico
            tables_result = connector.execute_query(f"""
                SELECT TABLE_NAME
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_SCHEMA = '{schema_name}'
                ORDER BY TABLE_NAME
            """)

            if not tables_result.success:
                raise Exception(
                    f"No se pudieron obtener tablas: {tables_result.error}"
                )

            tables = [row.get("TABLE_NAME") or row.get("table_name") for row in tables_result.data]
            logger.info(f"  → {len(tables)} tablas encontradas")

            for table_name in tables:
                schema_text += f"\nTABLA: {table_name}\n" + "-" * 40 + "\n"

                # Columnas
                cols_result = connector.execute_query(f"""
                    SELECT
                        COLUMN_NAME,
                        DATA_TYPE,
                        CHARACTER_MAXIMUM_LENGTH,
                        IS_NULLABLE
                    FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_NAME = '{table_name}'
                      AND TABLE_SCHEMA = '{schema_name}'
                    ORDER BY ORDINAL_POSITION
                """)

                if cols_result.success:
                    for col in cols_result.data:
                        # PostgreSQL devuelve minúsculas, SQL Server mayúsculas
                        col_name = col.get("COLUMN_NAME") or col.get("column_name")
                        col_type = col.get("DATA_TYPE") or col.get("data_type")
                        col_len = col.get("CHARACTER_MAXIMUM_LENGTH") or col.get("character_maximum_length")
                        is_nullable = col.get("IS_NULLABLE") or col.get("is_nullable")
                        
                        type_str = (
                            f"{col_type}({col_len})"
                            if col_len and col_len > 0
                            else col_type
                        )
                        nullable = "" if is_nullable == "YES" else " [NOT NULL]"
                        schema_text += f"  {col_name:30} {type_str}{nullable}\n"

                # Ejemplos de datos (ayudan al LLM a inferir contenido)
                try:
                    # Agregado: sintaxis compatible con SQL Server y PostgreSQL
                    # SQL Server usa TOP, PostgreSQL usa LIMIT
                    if db_type.lower() == "sqlserver":
                        sample_sql = f"SELECT TOP 2 * FROM {table_name}"
                    else:
                        sample_sql = f"SELECT * FROM {table_name} LIMIT 2"

                    sample = connector.execute_query(sample_sql)
                    if sample.success and sample.data:
                        schema_text += "Ejemplos:\n"
                        for idx, row in enumerate(sample.data, 1):
                            pairs = [
                                f"{k}={str(v)[:25]}"
                                for k, v in list(row.items())[:5]
                            ]
                            schema_text += f"  Fila {idx}: {', '.join(pairs)}\n"
                except Exception:
                    pass

                schema_text += "\n"

            return schema_text

        except Exception as e:
            logger.error(f"❌ Error cargando schema de {db_name}: {e}")
            raise

    # ── MÉTODOS DE SOPORTE ────────────────────────────────────────────────

    def _enrich_with_history(
        self, question: str, history: list, tracer: QueryTracer
    ) -> str:
        if not history:
            return question
        recent = history[-4:]
        context = "\n".join(
            f"{'Usuario' if m['role']=='user' else 'Asistente'}: {m['content']}"
            for m in recent
        )
        try:
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Reformulá la pregunta actual como pregunta autónoma "
                            "usando el contexto si es necesario. "
                            "Si ya es completa, devolvela igual. Solo la pregunta."
                        )
                    },
                    {
                        "role": "user",
                        "content": f"Contexto:\n{context}\n\nPregunta: {question}"
                    }
                ],
                max_tokens=150, temperature=0.1
            )
            enriched = response.choices[0].message.content.strip()
            if enriched != question:
                tracer.step(
                    archivo="nl2sql_generator",
                    paso="enriquecer_historial",
                    entrada=f"Original: '{question}'",
                    accion="Reformulando con contexto de conversación",
                    salida=f"Enriquecida: '{enriched}'"
                )
            return enriched
        except Exception as e:
            logger.warning(f"⚠️ No se pudo enriquecer pregunta: {e}")
            return question

    def _validate_sql(self, sql: str, tracer: QueryTracer) -> dict:
        import re
        notes = []
        valid = True

        if not sql:
            valid = False
            notes.append("❌ SQL vacía")
        elif not sql.strip().upper().startswith("SELECT"):
            valid = False
            notes.append("❌ Debe comenzar con SELECT")
        else:
            for cmd in ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE"]:
                if re.search(rf"\b{cmd}\b", sql, re.IGNORECASE):
                    valid = False
                    notes.append(f"❌ Comando prohibido: {cmd}")

        if valid:
            notes.append("✅ SQL válida")

        tracer.step(
            archivo="nl2sql_generator",
            paso="validar_sql",
            entrada=sql[:80] + "..." if len(sql) > 80 else sql,
            accion="SELECT-only, sin comandos destructivos",
            salida=f"valid={valid} | {notes[0]}"
        )
        return {"valid": valid, "notes": notes}

    def _calculate_confidence(self, sql, tables, validation) -> tuple:
        import re
        confidence = 100.0
        if len(re.findall(r'\bJOIN\b', sql, re.IGNORECASE)) > 3:
            confidence -= 10
        if not validation["valid"]:
            confidence -= 50
        if not tables:
            confidence -= 20
        confidence = max(0, min(100, confidence))

        if confidence >= 90:
            label = "🟢 Muy alta"
        elif confidence >= 70:
            label = "🟡 Alta"
        elif confidence >= 50:
            label = "🟠 Media"
        else:
            label = "🔴 Baja — revisar"
        return confidence, label

    def _build_reasoning(
        self, question, enriched, sql, tables, validation, tracer
    ) -> str:
        data_text = (
            f"Tablas: {', '.join(tables) if tables else 'no detectadas'}\n"
            f"SQL válida: {'sí' if validation['valid'] else 'no'}\n"
        )
        if enriched != question:
            data_text += f"Pregunta interpretada: {enriched}\n"
        try:
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Explicá en 2-3 oraciones por qué se eligieron "
                            "estas tablas y filtros. Directo. Sin markdown."
                        )
                    },
                    {
                        "role": "user",
                        "content": f"Pregunta: '{question}'\n{data_text}\nSQL:\n{sql}"
                    }
                ],
                max_tokens=150, temperature=0.3
            )
            reasoning = response.choices[0].message.content.strip()
            tracer.step(
                archivo="nl2sql_generator",
                paso="reasoning",
                entrada=data_text,
                accion="LLM redacta razonamiento",
                salida=reasoning[:80] + "..." if len(reasoning) > 80 else reasoning
            )
            return reasoning
        except Exception:
            return f"Tablas usadas: {', '.join(tables)}."

    def _generate_explanation(self, question, sql, tracer) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "1-2 oraciones describiendo qué información va a traer "
                            "esta consulta. Sin mencionar SQL ni tablas."
                        )
                    },
                    {
                        "role": "user",
                        "content": f"Pregunta: '{question}'\nSQL:\n{sql}"
                    }
                ],
                max_tokens=100, temperature=0.3
            )
            explanation = response.choices[0].message.content.strip()
            tracer.step(
                archivo="nl2sql_generator",
                paso="explanation",
                entrada=f"Pregunta: '{question}'",
                accion="LLM genera respuesta amigable",
                salida=explanation[:80] + "..." if len(explanation) > 80 else explanation
            )
            return explanation
        except Exception:
            return "Consulta generada correctamente."
