"""
Connection Manager for Multiple Database Support
Provides adapters for PostgreSQL, MySQL, SQL Server, SQLite
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
import json
import sqlite3


@dataclass
class DatabaseConfig:
    """Configuration for database connection"""
    name: str
    db_type: str  # "postgresql", "mysql", "sqlserver", "sqlite"
    host: Optional[str] = None
    port: Optional[int] = None
    database: str = ""
    username: Optional[str] = None
    password: Optional[str] = None
    filepath: Optional[str] = None  # For SQLite


class DatabaseAdapter(ABC):
    """Abstract base class for database adapters"""

    @abstractmethod
    def test_connection(self) -> Tuple[bool, str]:
        """Test connection and return (success, message)"""
        pass

    @abstractmethod
    def connect(self):
        """Context manager for database connection"""
        pass

    @abstractmethod
    def execute_query(self, query: str) -> Tuple[List[Dict], Optional[str]]:
        """Execute query and return (results, error)"""
        pass


class PostgreSQLAdapter(DatabaseAdapter):
    """PostgreSQL database adapter"""

    def __init__(self, config: DatabaseConfig):
        self.config = config

    def test_connection(self) -> Tuple[bool, str]:
        try:
            import psycopg2
            conn = psycopg2.connect(
                host=self.config.host,
                port=self.config.port or 5432,
                database=self.config.database,
                user=self.config.username,
                password=self.config.password,
            )
            conn.close()
            return True, "PostgreSQL connection successful"
        except ImportError:
            return False, "psycopg2 not installed"
        except Exception as e:
            return False, f"PostgreSQL connection failed: {str(e)}"

    def connect(self):
        """Context manager for PostgreSQL connection"""
        class PostgreSQLConnection:
            def __init__(self, adapter):
                self.adapter = adapter
                self.conn = None
                self.cursor = None

            def __enter__(self):
                import psycopg2
                self.conn = psycopg2.connect(
                    host=self.adapter.config.host,
                    port=self.adapter.config.port or 5432,
                    database=self.adapter.config.database,
                    user=self.adapter.config.username,
                    password=self.adapter.config.password,
                )
                self.cursor = self.conn.cursor()
                return self

            def __exit__(self, exc_type, exc_val, exc_tb):
                if self.cursor:
                    self.cursor.close()
                if self.conn:
                    self.conn.close()

            def execute(self, query: str):
                self.cursor.execute(query)
                return self.cursor.fetchall()

            def get_description(self):
                return self.cursor.description

        return PostgreSQLConnection(self)

    def execute_query(self, query: str) -> Tuple[List[Dict], Optional[str]]:
        try:
            with self.connect() as conn:
                results = conn.execute(query)
                columns = [desc[0] for desc in conn.get_description()]
                return [dict(zip(columns, row)) for row in results], None
        except Exception as e:
            return [], f"PostgreSQL query error: {str(e)}"


class MySQLAdapter(DatabaseAdapter):
    """MySQL database adapter"""

    def __init__(self, config: DatabaseConfig):
        self.config = config

    def test_connection(self) -> Tuple[bool, str]:
        try:
            import pymysql
            conn = pymysql.connect(
                host=self.config.host,
                port=self.config.port or 3306,
                database=self.config.database,
                user=self.config.username,
                password=self.config.password,
            )
            conn.close()
            return True, "MySQL connection successful"
        except ImportError:
            return False, "pymysql not installed"
        except Exception as e:
            return False, f"MySQL connection failed: {str(e)}"

    def connect(self):
        """Context manager for MySQL connection"""
        class MySQLConnection:
            def __init__(self, adapter):
                self.adapter = adapter
                self.conn = None
                self.cursor = None

            def __enter__(self):
                import pymysql
                self.conn = pymysql.connect(
                    host=self.adapter.config.host,
                    port=self.adapter.config.port or 3306,
                    database=self.adapter.config.database,
                    user=self.adapter.config.username,
                    password=self.adapter.config.password,
                )
                self.cursor = self.conn.cursor(pymysql.cursors.DictCursor)
                return self

            def __exit__(self, exc_type, exc_val, exc_tb):
                if self.cursor:
                    self.cursor.close()
                if self.conn:
                    self.conn.close()

            def execute(self, query: str):
                self.cursor.execute(query)
                return self.cursor.fetchall()

        return MySQLConnection(self)

    def execute_query(self, query: str) -> Tuple[List[Dict], Optional[str]]:
        try:
            with self.connect() as conn:
                results = conn.execute(query)
                return results, None
        except Exception as e:
            return [], f"MySQL query error: {str(e)}"


class SQLServerAdapter(DatabaseAdapter):
    """SQL Server database adapter"""

    def __init__(self, config: DatabaseConfig):
        self.config = config

    def test_connection(self) -> Tuple[bool, str]:
        try:
            from pyodbc import connect as pyodbc_connect
            conn_str = (
                f"Driver={{ODBC Driver 17 for SQL Server}};"
                f"Server={self.config.host},{self.config.port or 1433};"
                f"Database={self.config.database};"
                f"UID={self.config.username};"
                f"PWD={self.config.password};"
            )
            conn = pyodbc_connect(conn_str)
            conn.close()
            return True, "SQL Server connection successful"
        except ImportError:
            return False, "pyodbc not installed"
        except Exception as e:
            return False, f"SQL Server connection failed: {str(e)}"

    def connect(self):
        """Context manager for SQL Server connection"""
        class SQLServerConnection:
            def __init__(self, adapter):
                self.adapter = adapter
                self.conn = None
                self.cursor = None

            def __enter__(self):
                from pyodbc import connect as pyodbc_connect
                conn_str = (
                    f"Driver={{ODBC Driver 17 for SQL Server}};"
                    f"Server={self.adapter.config.host},{self.adapter.config.port or 1433};"
                    f"Database={self.adapter.config.database};"
                    f"UID={self.adapter.config.username};"
                    f"PWD={self.adapter.config.password};"
                )
                self.conn = pyodbc_connect(conn_str)
                self.cursor = self.conn.cursor()
                return self

            def __exit__(self, exc_type, exc_val, exc_tb):
                if self.cursor:
                    self.cursor.close()
                if self.conn:
                    self.conn.close()

            def execute(self, query: str):
                self.cursor.execute(query)
                return self.cursor.fetchall()

            def get_description(self):
                return self.cursor.description

        return SQLServerConnection(self)

    def execute_query(self, query: str) -> Tuple[List[Dict], Optional[str]]:
        try:
            with self.connect() as conn:
                results = conn.execute(query)
                columns = [desc[0] for desc in conn.get_description()]
                return [dict(zip(columns, row)) for row in results], None
        except Exception as e:
            return [], f"SQL Server query error: {str(e)}"


class SQLiteAdapter(DatabaseAdapter):
    """SQLite database adapter"""

    def __init__(self, config: DatabaseConfig):
        self.config = config

    def test_connection(self) -> Tuple[bool, str]:
        try:
            conn = sqlite3.connect(self.config.filepath)
            conn.close()
            return True, "SQLite connection successful"
        except Exception as e:
            return False, f"SQLite connection failed: {str(e)}"

    def connect(self):
        """Context manager for SQLite connection"""
        class SQLiteConnection:
            def __init__(self, adapter):
                self.adapter = adapter
                self.conn = None
                self.cursor = None

            def __enter__(self):
                self.conn = sqlite3.connect(self.adapter.config.filepath)
                self.conn.row_factory = sqlite3.Row
                self.cursor = self.conn.cursor()
                return self

            def __exit__(self, exc_type, exc_val, exc_tb):
                if self.cursor:
                    self.cursor.close()
                if self.conn:
                    self.conn.close()

            def execute(self, query: str):
                self.cursor.execute(query)
                return self.cursor.fetchall()

        return SQLiteConnection(self)

    def execute_query(self, query: str) -> Tuple[List[Dict], Optional[str]]:
        try:
            with self.connect() as conn:
                results = conn.execute(query)
                return [dict(row) for row in results], None
        except Exception as e:
            return [], f"SQLite query error: {str(e)}"


class ConnectionManager:
    """Manages database connections for different database types"""

    adapters = {
        "postgresql": PostgreSQLAdapter,
        "mysql": MySQLAdapter,
        "sqlserver": SQLServerAdapter,
        "sqlite": SQLiteAdapter,
    }

    @staticmethod
    def create_adapter(config: DatabaseConfig) -> Optional[DatabaseAdapter]:
        """Create appropriate adapter for database type"""
        adapter_class = ConnectionManager.adapters.get(config.db_type.lower())
        if adapter_class:
            return adapter_class(config)
        return None

    @staticmethod
    def create_connection(config: DatabaseConfig):
        """Create a database connection"""
        adapter = ConnectionManager.create_adapter(config)
        if adapter:
            return adapter.connect()
        return None

    @staticmethod
    def test_connection(config: DatabaseConfig) -> Tuple[bool, str]:
        """Test connection for a database config"""
        adapter = ConnectionManager.create_adapter(config)
        if not adapter:
            return False, f"Unsupported database type: {config.db_type}"
        return adapter.test_connection()

    @staticmethod
    def execute_query(config: DatabaseConfig, query: str) -> Tuple[List[Dict], Optional[str]]:
        """Execute query on a database"""
        adapter = ConnectionManager.create_adapter(config)
        if not adapter:
            return [], f"Unsupported database type: {config.db_type}"
        return adapter.execute_query(query)
