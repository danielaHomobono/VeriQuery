"""
Multi-Database Connector
Orchestrates connections to multiple databases with configuration persistence
"""

from typing import Dict, List, Optional, Tuple
import sys
from pathlib import Path

# Add tools to path
tools_path = str(Path(__file__).parent.parent.parent.parent / "tools")
if tools_path not in sys.path:
    sys.path.insert(0, tools_path)

from connection_manager import DatabaseConfig, ConnectionManager
from bd_config_manager import BDConfigManager
from schema_scanner import SchemaScanner


class MultiDatabaseConnector:
    """Manages connections to multiple databases"""

    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize multi-database connector

        Args:
            config_dir: Directory for storing database configurations
        """
        self.config_manager = BDConfigManager(config_dir)
        self.active_database: Optional[DatabaseConfig] = None

    def create_connection(self, config: DatabaseConfig):
        """
        Create a database connection

        Args:
            config: DatabaseConfig for connection

        Returns:
            Database connection object or None
        """
        return ConnectionManager.create_connection(config)

    def test_connection(self, config: DatabaseConfig) -> Tuple[bool, str]:
        """
        Test a database connection

        Args:
            config: DatabaseConfig to test

        Returns:
            Tuple of (success, message)
        """
        return ConnectionManager.test_connection(config)

    def set_active_database(self, database_name: str) -> Tuple[bool, str]:
        """
        Set the active database for queries

        Args:
            database_name: Name of saved database configuration

        Returns:
            Tuple of (success, message)
        """
        config = self.config_manager.get_database(database_name)
        if not config:
            return False, f"Database '{database_name}' not found"

        self.active_database = config
        return True, f"Active database set to '{database_name}'"

    def execute_query(self, query: str, database_name: Optional[str] = None) -> Tuple[List[Dict], Optional[str]]:
        """
        Execute query on active or specified database

        Args:
            query: SQL query to execute
            database_name: Optional specific database to use

        Returns:
            Tuple of (results, error)
        """
        if database_name:
            config = self.config_manager.get_database(database_name)
            if not config:
                return [], f"Database '{database_name}' not found"
        else:
            if not self.active_database:
                return [], "No active database set"
            config = self.active_database

        return ConnectionManager.execute_query(config, query)

    def save_database_config(
        self,
        name: str,
        db_type: str,
        database: str,
        host: Optional[str] = None,
        port: Optional[int] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        filepath: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """
        Save a database configuration

        Args:
            name: Configuration name
            db_type: Database type (postgresql, mysql, sqlserver, sqlite)
            database: Database name
            host: Host address
            port: Port number
            username: Username
            password: Password
            filepath: File path (for SQLite)

        Returns:
            Tuple of (success, message)
        """
        config = DatabaseConfig(
            name=name,
            db_type=db_type,
            host=host,
            port=port,
            database=database,
            username=username,
            password=password,
            filepath=filepath,
        )

        if self.config_manager.save_database(config):
            return True, f"Database '{name}' saved successfully"
        return False, f"Failed to save database '{name}'"

    def list_databases(self) -> List[str]:
        """
        List all saved database configurations

        Returns:
            List of database names
        """
        return self.config_manager.list_databases()

    def get_database_info(self, database_name: str) -> Optional[Dict]:
        """
        Get information about a saved database

        Args:
            database_name: Name of database configuration

        Returns:
            Dictionary with database info or None
        """
        config = self.config_manager.get_database(database_name)
        if not config:
            return None

        return {
            "db_name": config.name,  # Frontend expects db_name, not name
            "name": config.name,  # Keep both for compatibility
            "db_type": config.db_type,
            "host": str(config.host) if config.host else None,  # Ensure string
            "port": int(config.port) if config.port else None,  # Ensure integer
            "database": config.database,
            "username": config.username,
            "filepath": config.filepath,
            "active": config == self.active_database,
        }

    def delete_database_config(self, database_name: str) -> Tuple[bool, str]:
        """
        Delete a database configuration

        Args:
            database_name: Name of database configuration

        Returns:
            Tuple of (success, message)
        """
        if self.active_database and self.active_database.name == database_name:
            self.active_database = None

        if self.config_manager.delete_database(database_name):
            return True, f"Database '{database_name}' deleted"
        return False, f"Database '{database_name}' not found"

    def scan_schema(self, database_name: Optional[str] = None) -> Tuple[Dict, Optional[str]]:
        """
        Scan database schema

        Args:
            database_name: Optional specific database to scan

        Returns:
            Tuple of (schema_dict, error)
        """
        if database_name:
            config = self.config_manager.get_database(database_name)
            if not config:
                return {}, f"Database '{database_name}' not found"
        else:
            if not self.active_database:
                return {}, "No active database set"
            config = self.active_database

        scanner = SchemaScanner(config)
        schema, error = scanner.scan_schema()
        
        if error:
            return {}, error

        # Convert schema to serializable format
        schema_dict = {}
        for table_name, table_info in schema.items():
            schema_dict[table_name] = {
                "columns": [
                    {
                        "name": col.name,
                        "type": col.type,
                        "nullable": col.nullable,
                        "is_primary_key": col.is_primary_key,
                    }
                    for col in table_info.columns
                ],
                "row_count": table_info.row_count,
                "sample_data": table_info.sample_data,
            }

        return schema_dict, None

    def get_schema_for_prompt(self, database_name: Optional[str] = None) -> str:
        """
        Get formatted schema for LLM prompt

        Args:
            database_name: Optional specific database

        Returns:
            Formatted schema string
        """
        if database_name:
            config = self.config_manager.get_database(database_name)
            if not config:
                return f"Error: Database '{database_name}' not found"
        else:
            if not self.active_database:
                return "Error: No active database set"
            config = self.active_database

        scanner = SchemaScanner(config)
        return scanner.format_for_prompt()
