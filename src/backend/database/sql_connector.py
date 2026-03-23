"""
SQL Connector para conectar a Azure SQL Database
"""
import pyodbc
import os
from dotenv import load_dotenv
from typing import List, Dict, Any
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()


class SQLConnector:
    """Conector para Azure SQL Database"""
    
    def __init__(self):
        """Inicializar el conector SQL"""
        self.server = os.getenv("SQL_SERVER")
        self.database = os.getenv("SQL_DATABASE")
        self.username = os.getenv("SQL_USERNAME")
        self.password = os.getenv("SQL_PASSWORD")
        self.port = os.getenv("SQL_PORT", "1433")
        
        # Validar que todas las variables estén configuradas
        if not all([self.server, self.database, self.username, self.password]):
            raise ValueError(
                "Faltan variables de entorno SQL. "
                "Configura: SQL_SERVER, SQL_DATABASE, SQL_USERNAME, SQL_PASSWORD"
            )
        
        self.connection = None
        self._connect()
    
    def _connect(self):
        """Conectar a la base de datos"""
        try:
            connection_string = (
                f"Driver={{ODBC Driver 18 for SQL Server}};"
                f"Server=tcp:{self.server},{self.port};"
                f"Database={self.database};"
                f"Uid={self.username};"
                f"Pwd={self.password};"
                f"Encrypt=yes;"
                f"TrustServerCertificate=no;"
                f"Connection Timeout=30;"
            )
            
            self.connection = pyodbc.connect(connection_string)
            logger.info(f"✅ Conectado a {self.database}")
        except pyodbc.Error as e:
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
            
            # Obtener nombres de columnas
            columns = [description[0] for description in cursor.description]
            
            # Convertir a lista de diccionarios
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            
            cursor.close()
            logger.info(f"✅ Consulta ejecutada. {len(results)} filas retornadas")
            return results
        
        except pyodbc.Error as e:
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
        
        except pyodbc.Error as e:
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
            columns = ", ".join([f"[{col}] {type_}" for col, type_ in schema.items()])
            query = f"CREATE TABLE [{table_name}] ({columns})"
            
            cursor = self.connection.cursor()
            cursor.execute(query)
            self.connection.commit()
            cursor.close()
            
            logger.info(f"✅ Tabla [{table_name}] creada")
            return True
        
        except pyodbc.Error as e:
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
            query = f"DROP TABLE IF EXISTS [{table_name}]"
            
            cursor = self.connection.cursor()
            cursor.execute(query)
            self.connection.commit()
            cursor.close()
            
            logger.info(f"✅ Tabla [{table_name}] eliminada")
            return True
        
        except pyodbc.Error as e:
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
                "SELECT COUNT(*) FROM information_schema.tables "
                "WHERE table_name = ?"
            )
            results = self.execute_query(query, [table_name])
            return results[0].get('', 0) > 0
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
            query = (
                "SELECT COLUMN_NAME, DATA_TYPE FROM information_schema.COLUMNS "
                "WHERE TABLE_NAME = ?"
            )
            results = self.execute_query(query, [table_name])
            
            schema = {}
            for row in results:
                col_name = row.get('COLUMN_NAME', '')
                data_type = row.get('DATA_TYPE', '')
                schema[col_name] = data_type
            
            logger.info(f"✅ Esquema obtenido para [{table_name}]")
            return schema
        
        except Exception as e:
            logger.error(f"❌ Error obteniendo esquema: {e}")
            return {}
    
    def close(self):
        """Cerrar conexión"""
        if self.connection:
            self.connection.close()
            logger.info("✅ Conexión cerrada")


if __name__ == "__main__":
    print("=" * 60)
    print("TEST DE CONEXIÓN SQL")
    print("=" * 60)
    
    try:
        # Conectar
        connector = SQLConnector()
        
        print("\n✅ Conexión exitosa a SQL Database")
        
        # Obtener información de la BD
        query = "SELECT @@version AS sql_version"
        result = connector.execute_query(query)
        print(f"\n🔍 SQL Server: {result[0]['sql_version'][:60]}...")
        
        # Cerrar
        connector.close()
        print("\n✅ Todo funciona correctamente")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\n🔧 Soluciona:")
        print("1. Verifica que .env tenga SQL_SERVER, SQL_DATABASE, SQL_USERNAME, SQL_PASSWORD")
        print("2. Instala ODBC Driver 18 for SQL Server")
        print("3. Verifica que la IP esté en el firewall de Azure")
