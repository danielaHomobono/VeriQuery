"""
SQL Connector Local - Usando SQLite para desarrollo local
Este archivo permite trabajar sin Azure SQL mientras tanto
"""
import sqlite3
import os
from dotenv import load_dotenv
from typing import List, Dict, Any
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()


class SQLConnectorLocal:
    """Conector SQLite para desarrollo local"""
    
    def __init__(self, db_path: str = "forensic_guardian.db"):
        """
        Inicializar el conector SQLite
        
        Args:
            db_path: Ruta al archivo de base de datos SQLite
        """
        self.db_path = db_path
        self.connection = None
        self._connect()
    
    def _connect(self):
        """Conectar a la base de datos SQLite"""
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row  # Para acceder a columnas por nombre
            logger.info(f"✅ Conectado a SQLite: {self.db_path}")
        except sqlite3.Error as e:
            logger.error(f"❌ Error de conexión: {e}")
            raise
    
    def execute_query(self, query: str, params: List[Any] = None) -> List[Dict[str, Any]]:
        """
        Ejecutar una consulta SELECT
        
        Args:
            query: Consulta SQL
            params: Parámetros para la consulta
            
        Returns:
            Lista de diccionarios con los resultados
        """
        try:
            cursor = self.connection.cursor()
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            # Convertir rows a diccionarios
            columns = [description[0] for description in cursor.description] if cursor.description else []
            results = []
            
            for row in cursor.fetchall():
                if isinstance(row, sqlite3.Row):
                    results.append(dict(row))
                else:
                    results.append(dict(zip(columns, row)))
            
            cursor.close()
            logger.info(f"✅ Consulta ejecutada. {len(results)} filas retornadas")
            return results
        
        except sqlite3.Error as e:
            logger.error(f"❌ Error en consulta: {e}")
            raise
    
    def execute_update(self, query: str, params: List[Any] = None) -> int:
        """
        Ejecutar una consulta INSERT, UPDATE o DELETE
        
        Args:
            query: Consulta SQL
            params: Parámetros para la consulta
            
        Returns:
            Número de filas afectadas
        """
        try:
            cursor = self.connection.cursor()
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            rows_affected = cursor.rowcount
            self.connection.commit()
            cursor.close()
            
            logger.info(f"✅ {rows_affected} filas afectadas")
            return rows_affected
        
        except sqlite3.Error as e:
            self.connection.rollback()
            logger.error(f"❌ Error en actualización: {e}")
            raise
    
    def create_table(self, table_name: str, schema: Dict[str, str]) -> bool:
        """
        Crear una tabla
        
        Args:
            table_name: Nombre de la tabla
            schema: Diccionario con nombre de columna y tipo SQL
            
        Returns:
            True si se creó exitosamente
        """
        try:
            columns = ", ".join([f'"{col}" {type_}' for col, type_ in schema.items()])
            query = f'CREATE TABLE IF NOT EXISTS "{table_name}" ({columns})'
            
            cursor = self.connection.cursor()
            cursor.execute(query)
            self.connection.commit()
            cursor.close()
            
            logger.info(f"✅ Tabla [{table_name}] creada")
            return True
        
        except sqlite3.Error as e:
            logger.error(f"❌ Error creando tabla: {e}")
            raise
    
    def drop_table(self, table_name: str) -> bool:
        """
        Eliminar una tabla
        
        Args:
            table_name: Nombre de la tabla
            
        Returns:
            True si se eliminó exitosamente
        """
        try:
            query = f'DROP TABLE IF EXISTS "{table_name}"'
            
            cursor = self.connection.cursor()
            cursor.execute(query)
            self.connection.commit()
            cursor.close()
            
            logger.info(f"✅ Tabla [{table_name}] eliminada")
            return True
        
        except sqlite3.Error as e:
            logger.error(f"❌ Error eliminando tabla: {e}")
            raise
    
    def table_exists(self, table_name: str) -> bool:
        """
        Verificar si una tabla existe
        
        Args:
            table_name: Nombre de la tabla
            
        Returns:
            True si existe, False en caso contrario
        """
        try:
            query = (
                "SELECT name FROM sqlite_master "
                "WHERE type='table' AND name=?"
            )
            results = self.execute_query(query, [table_name])
            return len(results) > 0
        except Exception as e:
            logger.error(f"❌ Error verificando tabla: {e}")
            return False
    
    def get_table_schema(self, table_name: str) -> Dict[str, str]:
        """
        Obtener el esquema de una tabla
        
        Args:
            table_name: Nombre de la tabla
            
        Returns:
            Diccionario con columnas y tipos
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute(f'PRAGMA table_info("{table_name}")')
            
            schema = {}
            for row in cursor.fetchall():
                col_name = row[1]
                data_type = row[2]
                schema[col_name] = data_type
            
            cursor.close()
            logger.info(f"✅ Esquema obtenido para [{table_name}]")
            return schema
        
        except Exception as e:
            logger.error(f"❌ Error obteniendo esquema: {e}")
            return {}
    
    def get_all_tables(self) -> List[str]:
        """
        Obtener lista de todas las tablas
        
        Returns:
            Lista de nombres de tablas
        """
        try:
            query = "SELECT name FROM sqlite_master WHERE type='table'"
            results = self.execute_query(query)
            tables = [row['name'] for row in results]
            logger.info(f"✅ {len(tables)} tablas encontradas")
            return tables
        except Exception as e:
            logger.error(f"❌ Error obteniendo tablas: {e}")
            return []
    
    def close(self):
        """Cerrar conexión"""
        if self.connection:
            self.connection.close()
            logger.info("✅ Conexión cerrada")


# Función de compatibilidad con sql_connector.py
class SQLConnector(SQLConnectorLocal):
    """Alias para compatibilidad con código existente"""
    pass


if __name__ == "__main__":
    print("=" * 60)
    print("TEST DE CONEXIÓN SQLITE LOCAL")
    print("=" * 60)
    
    try:
        # Conectar
        connector = SQLConnectorLocal()
        
        print("\n✅ Conexión exitosa a SQLite")
        
        # Crear tabla de ejemplo
        print("\n1️⃣ Creando tabla de ejemplo...")
        schema = {
            "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
            "nombre": "TEXT NOT NULL",
            "email": "TEXT UNIQUE",
            "edad": "INTEGER",
            "fecha_creacion": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
        }
        connector.create_table("usuarios", schema)
        
        # Insertar datos de ejemplo
        print("\n2️⃣ Insertando datos de ejemplo...")
        connector.execute_update(
            'INSERT INTO usuarios (nombre, email, edad) VALUES (?, ?, ?)',
            ["Juan Pérez", "juan@example.com", 30]
        )
        connector.execute_update(
            'INSERT INTO usuarios (nombre, email, edad) VALUES (?, ?, ?)',
            ["María García", "maria@example.com", 28]
        )
        
        # Consultar datos
        print("\n3️⃣ Consultando datos...")
        results = connector.execute_query('SELECT * FROM usuarios')
        for row in results:
            print(f"   - {row['nombre']} ({row['email']}) - {row['edad']} años")
        
        # Obtener esquema
        print("\n4️⃣ Esquema de la tabla:")
        schema = connector.get_table_schema("usuarios")
        for col, type_ in schema.items():
            print(f"   - {col}: {type_}")
        
        # Obtener todas las tablas
        print("\n5️⃣ Tablas en la BD:")
        tables = connector.get_all_tables()
        for table in tables:
            print(f"   - {table}")
        
        connector.close()
        print("\n✅ Test completado exitosamente")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
