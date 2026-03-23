"""
Database Configuration Manager
Persists and manages database connection configurations with encryption
"""

import json
import os
from typing import Dict, List, Optional
from pathlib import Path
import base64

# Try relative import first, fall back to direct import
try:
    from .connection_manager import DatabaseConfig
except ImportError:
    from connection_manager import DatabaseConfig


class BDConfigManager:
    """Manages database configurations persistence"""

    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize config manager

        Args:
            config_dir: Directory to store configs (default: ~/.forensic_guardian)
        """
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            self.config_dir = Path.home() / ".forensic_guardian"
        
        self.config_file = self.config_dir / "databases.json"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self._ensure_config_file()

    def _ensure_config_file(self):
        """Ensure config file exists"""
        if not self.config_file.exists():
            self.config_file.write_text(json.dumps({"databases": {}}, indent=2))

    def _encrypt_password(self, password: str) -> str:
        """Simple base64 encryption for passwords"""
        return base64.b64encode(password.encode()).decode()

    def _decrypt_password(self, encrypted: str) -> str:
        """Simple base64 decryption for passwords"""
        return base64.b64decode(encrypted.encode()).decode()

    def save_database(self, config: DatabaseConfig) -> bool:
        """
        Save database configuration

        Args:
            config: DatabaseConfig object

        Returns:
            True if saved successfully
        """
        try:
            data = json.loads(self.config_file.read_text())
            
            db_entry = {
                "name": config.name,
                "db_type": config.db_type,
                "host": config.host,
                "port": config.port,
                "database": config.database,
                "username": config.username,
                "password": self._encrypt_password(config.password) if config.password else None,
                "filepath": config.filepath,
            }
            
            data["databases"][config.name] = db_entry
            self.config_file.write_text(json.dumps(data, indent=2))
            return True
        except Exception as e:
            print(f"Error saving database config: {e}")
            return False

    def get_database(self, name: str) -> Optional[DatabaseConfig]:
        """
        Get database configuration by name

        Args:
            name: Database configuration name

        Returns:
            DatabaseConfig or None if not found
        """
        try:
            data = json.loads(self.config_file.read_text())
            db_entry = data.get("databases", {}).get(name)
            
            if not db_entry:
                return None
            
            password = db_entry.get("password")
            if password:
                password = self._decrypt_password(password)
            
            return DatabaseConfig(
                name=db_entry["name"],
                db_type=db_entry["db_type"],
                host=db_entry.get("host"),
                port=db_entry.get("port"),
                database=db_entry.get("database", ""),
                username=db_entry.get("username"),
                password=password,
                filepath=db_entry.get("filepath"),
            )
        except Exception as e:
            print(f"Error reading database config: {e}")
            return None

    def list_databases(self) -> List[str]:
        """
        List all saved database names

        Returns:
            List of database configuration names
        """
        try:
            # Ensure config file exists first
            self._ensure_config_file()
            
            # Read and parse JSON
            content = self.config_file.read_text()
            data = json.loads(content)
            
            # Extract database names
            databases = list(data.get("databases", {}).keys())
            print(f"✅ Listed {len(databases)} databases: {databases}")
            return databases
            
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing databases.json: {e}")
            print(f"   File path: {self.config_file}")
            print(f"   File exists: {self.config_file.exists()}")
            # Return empty list on parse error
            return []
        except Exception as e:
            print(f"❌ Error listing databases: {e}")
            print(f"   File path: {self.config_file}")
            return []

    def delete_database(self, name: str) -> bool:
        """
        Delete database configuration

        Args:
            name: Database configuration name

        Returns:
            True if deleted successfully
        """
        try:
            data = json.loads(self.config_file.read_text())
            if name in data.get("databases", {}):
                del data["databases"][name]
                self.config_file.write_text(json.dumps(data, indent=2))
                return True
            return False
        except Exception as e:
            print(f"Error deleting database config: {e}")
            return False

    def get_all_databases(self) -> Dict[str, DatabaseConfig]:
        """
        Get all database configurations

        Returns:
            Dictionary of name -> DatabaseConfig
        """
        try:
            data = json.loads(self.config_file.read_text())
            configs = {}
            
            for name, db_entry in data.get("databases", {}).items():
                password = db_entry.get("password")
                if password:
                    password = self._decrypt_password(password)
                
                configs[name] = DatabaseConfig(
                    name=db_entry["name"],
                    db_type=db_entry["db_type"],
                    host=db_entry.get("host"),
                    port=db_entry.get("port"),
                    database=db_entry.get("database", ""),
                    username=db_entry.get("username"),
                    password=password,
                    filepath=db_entry.get("filepath"),
                )
            
            return configs
        except Exception as e:
            print(f"Error reading all database configs: {e}")
            return {}
