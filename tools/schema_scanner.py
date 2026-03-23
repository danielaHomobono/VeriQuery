"""
Automatic Database Schema Scanner
Detects and extracts schema information from various databases
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import json
import sqlite3

# Import database adapters
try:
    import psycopg2
except ImportError:
    psycopg2 = None

try:
    import pymysql
except ImportError:
    pymysql = None

try:
    import pyodbc as pyodbc_connect
except ImportError:
    pyodbc_connect = None

# Try relative import first, fall back to direct import
try:
    from .connection_manager import DatabaseConfig, ConnectionManager
except ImportError:
    from connection_manager import DatabaseConfig, ConnectionManager


@dataclass
class ColumnInfo:
    """Information about a database column"""
    name: str
    type: str
    nullable: bool
    is_primary_key: bool = False


@dataclass
class TableInfo:
    """Information about a database table"""
    name: str
    columns: List[ColumnInfo]
    row_count: int = 0
    sample_data: List[Dict] = None

    def __post_init__(self):
        if self.sample_data is None:
            self.sample_data = []


class SchemaScanner:
    """Scans and extracts schema information from databases"""

    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.adapter = ConnectionManager.create_adapter(config)

    def scan_schema(self) -> Tuple[Dict[str, TableInfo], Optional[str]]:
        """
        Scan entire database schema

        Returns:
            Tuple of (schema_dict, error_message)
        """
        if not self.adapter:
            return {}, f"Unsupported database type: {self.config.db_type}"

        db_type = self.config.db_type.lower()

        if db_type == "postgresql":
            return self._scan_postgresql()
        elif db_type == "mysql":
            return self._scan_mysql()
        elif db_type == "sqlserver":
            return self._scan_sqlserver()
        elif db_type == "sqlite":
            return self._scan_sqlite()
        else:
            return {}, f"Unsupported database type: {db_type}"

    def _scan_postgresql(self) -> Tuple[Dict[str, TableInfo], Optional[str]]:
        """Scan PostgreSQL schema"""
        if not psycopg2:
            return {}, "psycopg2 not installed. Install with: pip install psycopg2-binary"
        
        try:
            conn = psycopg2.connect(
                host=self.config.host,
                port=self.config.port or 5432,
                database=self.config.database,
                user=self.config.username,
                password=self.config.password,
            )
            cursor = conn.cursor()

            # Get all tables
            cursor.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            tables = [row[0] for row in cursor.fetchall()]

            schema = {}
            for table_name in tables:
                # Get columns
                cursor.execute(f"""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_name = '{table_name}'
                """)
                columns = []
                for col_name, col_type, nullable in cursor.fetchall():
                    columns.append(ColumnInfo(
                        name=col_name,
                        type=col_type,
                        nullable=nullable == "YES",
                    ))

                # Get primary keys using information_schema (more portable)
                cursor.execute(f"""
                    SELECT column_name
                    FROM information_schema.key_column_usage
                    WHERE table_name = '{table_name}' 
                    AND constraint_name LIKE '%pkey'
                    AND table_schema = 'public'
                """)
                pk_names = [row[0] for row in cursor.fetchall()]
                for col in columns:
                    if col.name in pk_names:
                        col.is_primary_key = True

                # Get row count
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                row_count = cursor.fetchone()[0]

                # Get sample data (3 rows)
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
                sample_data = []
                col_names = [col.name for col in columns]
                for row in cursor.fetchall():
                    sample_data.append(dict(zip(col_names, row)))

                schema[table_name] = TableInfo(
                    name=table_name,
                    columns=columns,
                    row_count=row_count,
                    sample_data=sample_data,
                )

            cursor.close()
            conn.close()
            return schema, None

        except Exception as e:
            return {}, f"PostgreSQL scan error: {str(e)}"

    def _scan_mysql(self) -> Tuple[Dict[str, TableInfo], Optional[str]]:
        """Scan MySQL schema"""
        if not pymysql:
            return {}, "pymysql not installed. Install with: pip install pymysql"
        
        try:
            conn = pymysql.connect(
                host=self.config.host,
                port=self.config.port or 3306,
                database=self.config.database,
                user=self.config.username,
                password=self.config.password,
            )
            cursor = conn.cursor()

            # Get all tables
            cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = %s",
                          (self.config.database,))
            tables = [row[0] for row in cursor.fetchall()]

            schema = {}
            for table_name in tables:
                # Get columns
                cursor.execute(f"""
                    SELECT column_name, column_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_name = '{table_name}' AND table_schema = '{self.config.database}'
                """)
                columns = []
                for col_name, col_type, nullable in cursor.fetchall():
                    columns.append(ColumnInfo(
                        name=col_name,
                        type=col_type,
                        nullable=nullable == "YES",
                    ))

                # Get primary keys
                cursor.execute(f"""
                    SELECT column_name FROM information_schema.key_column_usage
                    WHERE table_name = '{table_name}' AND constraint_name = 'PRIMARY'
                """)
                pk_names = [row[0] for row in cursor.fetchall()]
                for col in columns:
                    if col.name in pk_names:
                        col.is_primary_key = True

                # Get row count
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                row_count = cursor.fetchone()[0]

                # Get sample data (3 rows)
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
                sample_data = []
                col_names = [col.name for col in columns]
                for row in cursor.fetchall():
                    sample_data.append(dict(zip(col_names, row)))

                schema[table_name] = TableInfo(
                    name=table_name,
                    columns=columns,
                    row_count=row_count,
                    sample_data=sample_data,
                )

            cursor.close()
            conn.close()
            return schema, None

        except Exception as e:
            return {}, f"MySQL scan error: {str(e)}"

    def _scan_sqlserver(self) -> Tuple[Dict[str, TableInfo], Optional[str]]:
        """Scan SQL Server schema"""
        if not pyodbc_connect:
            return {}, "pyodbc not installed. Install with: pip install pyodbc"
        
        try:
            conn_str = (
                f"Driver={{ODBC Driver 17 for SQL Server}};"
                f"Server={self.config.host},{self.config.port or 1433};"
                f"Database={self.config.database};"
                f"UID={self.config.username};"
                f"PWD={self.config.password};"
            )
            conn = pyodbc_connect(conn_str)
            cursor = conn.cursor()

            # Get all tables
            cursor.execute("""
                SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_TYPE = 'BASE TABLE'
            """)
            tables = [row[0] for row in cursor.fetchall()]

            schema = {}
            for table_name in tables:
                # Get columns
                cursor.execute(f"""
                    SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
                    FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_NAME = '{table_name}'
                """)
                columns = []
                for col_name, col_type, nullable in cursor.fetchall():
                    columns.append(ColumnInfo(
                        name=col_name,
                        type=col_type,
                        nullable=nullable == "YES",
                    ))

                # Get primary keys
                cursor.execute(f"""
                    SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
                    WHERE TABLE_NAME = '{table_name}' AND CONSTRAINT_NAME LIKE '%PK%'
                """)
                pk_names = [row[0] for row in cursor.fetchall()]
                for col in columns:
                    if col.name in pk_names:
                        col.is_primary_key = True

                # Get row count
                cursor.execute(f"SELECT COUNT(*) FROM [{table_name}]")
                row_count = cursor.fetchone()[0]

                # Get sample data (3 rows)
                cursor.execute(f"SELECT TOP 3 * FROM [{table_name}]")
                sample_data = []
                col_names = [col.name for col in columns]
                for row in cursor.fetchall():
                    sample_data.append(dict(zip(col_names, row)))

                schema[table_name] = TableInfo(
                    name=table_name,
                    columns=columns,
                    row_count=row_count,
                    sample_data=sample_data,
                )

            cursor.close()
            conn.close()
            return schema, None

        except Exception as e:
            return {}, f"SQL Server scan error: {str(e)}"

    def _scan_sqlite(self) -> Tuple[Dict[str, TableInfo], Optional[str]]:
        """Scan SQLite schema"""
        try:
            conn = sqlite3.connect(self.config.filepath)
            cursor = conn.cursor()

            # Get all tables
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
            """)
            tables = [row[0] for row in cursor.fetchall()]

            schema = {}
            for table_name in tables:
                # Get columns
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = []
                for col_id, col_name, col_type, nullable, default, pk in cursor.fetchall():
                    columns.append(ColumnInfo(
                        name=col_name,
                        type=col_type,
                        nullable=not nullable,
                        is_primary_key=pk == 1,
                    ))

                # Get row count
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                row_count = cursor.fetchone()[0]

                # Get sample data (3 rows)
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
                sample_data = []
                col_names = [col.name for col in columns]
                for row in cursor.fetchall():
                    sample_data.append(dict(zip(col_names, row)))

                schema[table_name] = TableInfo(
                    name=table_name,
                    columns=columns,
                    row_count=row_count,
                    sample_data=sample_data,
                )

            cursor.close()
            conn.close()
            return schema, None

        except Exception as e:
            return {}, f"SQLite scan error: {str(e)}"

    def format_for_prompt(self) -> str:
        """Format schema for LLM prompt"""
        schema, error = self.scan_schema()
        if error:
            return f"Error: {error}"

        lines = []
        for table_name, table_info in schema.items():
            lines.append(f"\n## Table: {table_name}")
            lines.append(f"Rows: {table_info.row_count}")
            lines.append("Columns:")
            for col in table_info.columns:
                pk_marker = " (PRIMARY KEY)" if col.is_primary_key else ""
                nullable = "nullable" if col.nullable else "NOT NULL"
                lines.append(f"  - {col.name}: {col.type} [{nullable}]{pk_marker}")

            if table_info.sample_data:
                lines.append("Sample Data:")
                for row in table_info.sample_data[:2]:
                    lines.append(f"  {row}")

        return "\n".join(lines)

    def export_json(self) -> str:
        """Export schema as JSON"""
        schema, error = self.scan_schema()
        if error:
            return json.dumps({"error": error})

        schema_dict = {}
        for table_name, table_info in schema.items():
            schema_dict[table_name] = {
                "columns": [asdict(col) for col in table_info.columns],
                "row_count": table_info.row_count,
                "sample_data": table_info.sample_data,
            }

        return json.dumps(schema_dict, indent=2, default=str)

    def export_sql_schema(self) -> str:
        """Export schema as SQL CREATE statements (mock/reference)"""
        schema, error = self.scan_schema()
        if error:
            return f"-- Error: {error}"

        lines = []
        for table_name, table_info in schema.items():
            lines.append(f"\n-- Table: {table_name} ({table_info.row_count} rows)")
            lines.append(f"CREATE TABLE {table_name} (")
            
            col_defs = []
            for col in table_info.columns:
                col_def = f"  {col.name} {col.type}"
                if col.is_primary_key:
                    col_def += " PRIMARY KEY"
                if not col.nullable:
                    col_def += " NOT NULL"
                col_defs.append(col_def)
            
            lines.append(",\n".join(col_defs))
            lines.append(");")

        return "\n".join(lines)
