"""
Guardian Database Manager - SQLite Version
For development/testing when PostgreSQL is not available
Uses SQLite for persistence instead of PostgreSQL
"""

import sqlite3
from pathlib import Path
import logging
import json
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Use SQLite database in project root
DB_PATH = Path(__file__).parent.parent.parent / "guardian.db"


class GuardianDBManagerSQLite:
    """Manages connections to Guardian database using SQLite"""
    
    def __init__(self):
        """Initialize Guardian DB connection"""
        self.db_path = DB_PATH
        self._connect()
        self._init_schema()
    
    def _connect(self):
        """Establish connection to Guardian DB"""
        try:
            self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            logger.info(f"✓ Connected to Guardian DB: {self.db_path}")
        except sqlite3.Error as e:
            logger.error(f"✗ Failed to connect to Guardian DB: {e}")
            raise
    
    def _init_schema(self):
        """Create tables if they don't exist"""
        cursor = self.conn.cursor()
        
        try:
            # Table: user_databases
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_databases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                db_name TEXT NOT NULL,
                db_type TEXT NOT NULL,
                display_name TEXT,
                description TEXT,
                host TEXT NOT NULL,
                port INTEGER DEFAULT 5432,
                database_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                UNIQUE(user_id, db_name)
            )
            """)
            
            # Table: user_sessions
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                session_id TEXT UNIQUE NOT NULL,
                active_db_name TEXT,
                schema_cache TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP
            )
            """)
            
            # Table: audit_log
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                action TEXT NOT NULL,
                resource_type TEXT,
                resource_id TEXT,
                details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            self.conn.commit()
            logger.info("✓ Guardian DB schema initialized")
        except sqlite3.Error as e:
            logger.error(f"✗ Failed to initialize schema: {e}")
            raise
    
    # =========================================================================
    # USER DATABASES MANAGEMENT
    # =========================================================================
    
    def add_user_database(self, user_id: str, db_name: str, db_type: str, 
                         display_name: str, host: str, port: int, 
                         database_name: str, description: str = None) -> Dict[str, Any]:
        """Add or update a database configuration for user"""
        cursor = self.conn.cursor()
        
        try:
            # Try to get existing ID
            cursor.execute("""
            SELECT id FROM user_databases
            WHERE user_id = ? AND db_name = ?
            """, (user_id, db_name))
            
            existing = cursor.fetchone()
            
            if existing:
                # Update existing
                cursor.execute("""
                UPDATE user_databases
                SET db_type = ?, display_name = ?, host = ?, port = ?, 
                    database_name = ?, description = ?, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ? AND db_name = ?
                """, (db_type, display_name, host, port, database_name, description, user_id, db_name))
                
                self._audit("update", "database", db_name, {"user_id": user_id, "db_type": db_type}, user_id)
                logger.info(f"Database '{db_name}' updated for user {user_id}")
            else:
                # Insert new
                cursor.execute("""
                INSERT INTO user_databases 
                (user_id, db_name, db_type, display_name, host, port, database_name, description)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (user_id, db_name, db_type, display_name, host, port, database_name, description))
                
                self._audit("create", "database", db_name, {"user_id": user_id, "db_type": db_type}, user_id)
                logger.info(f"Database '{db_name}' added for user {user_id}")
            
            self.conn.commit()
            
            return {
                "id": cursor.lastrowid,
                "created_at": datetime.now().isoformat()
            }
        except sqlite3.Error as e:
            logger.error(f"Error adding database: {e}")
            raise
    
    def get_user_databases(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all databases configured for a user"""
        cursor = self.conn.cursor()
        
        try:
            cursor.execute("""
            SELECT id, user_id, db_name, db_type, display_name, description, 
                   host, port, database_name, created_at, is_active
            FROM user_databases
            WHERE user_id = ? AND is_active = 1
            ORDER BY created_at DESC
            """, (user_id,))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Error getting databases: {e}")
            return []
    
    def get_user_database(self, user_id: str, db_name: str) -> Optional[Dict[str, Any]]:
        """Get specific database configuration for user"""
        cursor = self.conn.cursor()
        
        try:
            cursor.execute("""
            SELECT id, user_id, db_name, db_type, display_name, description,
                   host, port, database_name, created_at, is_active
            FROM user_databases
            WHERE user_id = ? AND db_name = ?
            LIMIT 1
            """, (user_id, db_name))
            
            row = cursor.fetchone()
            return dict(row) if row else None
        except sqlite3.Error as e:
            logger.error(f"Error getting database: {e}")
            return None
    
    # =========================================================================
    # SESSION MANAGEMENT
    # =========================================================================
    
    def create_session(self, user_id: str, session_id: str, db_name: str = None) -> Dict[str, Any]:
        """Create or update user session"""
        expires_at = datetime.utcnow() + timedelta(hours=8)
        cursor = self.conn.cursor()
        
        try:
            # Try insert, if exists update
            cursor.execute("""
            INSERT OR REPLACE INTO user_sessions (user_id, session_id, active_db_name, expires_at)
            VALUES (?, ?, ?, ?)
            """, (user_id, session_id, db_name, expires_at.isoformat()))
            
            self.conn.commit()
            self._audit("create", "session", session_id, {"user_id": user_id, "db_name": db_name}, user_id)
            
            return {
                "id": cursor.lastrowid,
                "created_at": datetime.now().isoformat(),
                "expires_at": expires_at.isoformat()
            }
        except sqlite3.Error as e:
            logger.error(f"Error creating session: {e}")
            raise
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get user session"""
        cursor = self.conn.cursor()
        
        try:
            cursor.execute("""
            SELECT id, user_id, session_id, active_db_name, schema_cache, created_at, expires_at
            FROM user_sessions
            WHERE session_id = ? AND (expires_at IS NULL OR expires_at > datetime('now'))
            LIMIT 1
            """, (session_id,))
            
            row = cursor.fetchone()
            if row:
                row_dict = dict(row)
                # Parse schema_cache JSON
                if row_dict.get('schema_cache'):
                    row_dict['schema_cache'] = json.loads(row_dict['schema_cache'])
                return row_dict
            return None
        except sqlite3.Error as e:
            logger.error(f"Error getting session: {e}")
            return None
    
    def update_session_database(self, session_id: str, db_name: str, schema: Dict = None) -> bool:
        """Update which database is active in session"""
        schema_json = json.dumps(schema) if schema else None
        cursor = self.conn.cursor()
        
        try:
            cursor.execute("""
            UPDATE user_sessions
            SET active_db_name = ?, schema_cache = ?, updated_at = datetime('now')
            WHERE session_id = ?
            """, (db_name, schema_json, session_id))
            
            self.conn.commit()
            self._audit("select", "session", session_id, {"active_db_name": db_name}, session_id)
            logger.info(f"Session {session_id} updated to database: {db_name}")
            return True
        except sqlite3.Error as e:
            logger.error(f"Error updating session: {e}")
            return False
    
    def get_active_database(self, session_id: str) -> Optional[str]:
        """Get currently active database for session"""
        cursor = self.conn.cursor()
        
        try:
            cursor.execute("""
            SELECT active_db_name
            FROM user_sessions
            WHERE session_id = ? AND (expires_at IS NULL OR expires_at > datetime('now'))
            LIMIT 1
            """, (session_id,))
            
            row = cursor.fetchone()
            if row:
                return row[0]
            return None
        except sqlite3.Error as e:
            logger.error(f"Error getting active database: {e}")
            return None
    
    # =========================================================================
    # AUDIT LOGGING
    # =========================================================================
    
    def _audit(self, action: str, resource_type: str, resource_id: str, 
              details: Dict = None, user_id: str = None) -> bool:
        """Log action for audit trail"""
        cursor = self.conn.cursor()
        
        try:
            details_json = json.dumps(details) if details else None
            cursor.execute("""
            INSERT INTO audit_log (user_id, action, resource_type, resource_id, details)
            VALUES (?, ?, ?, ?, ?)
            """, (user_id, action, resource_type, resource_id, details_json))
            
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            logger.warning(f"Audit logging failed: {e}")
            return False
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Guardian DB connection closed")


# Global instance
_guardian_manager = None


def get_guardian_manager() -> GuardianDBManagerSQLite:
    """Get or create Guardian DB manager singleton"""
    global _guardian_manager
    if _guardian_manager is None:
        _guardian_manager = GuardianDBManagerSQLite()
    return _guardian_manager
