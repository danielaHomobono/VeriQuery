"""
Guardian Database Manager
Wrapper that uses SQLite for persistent storage of user database configurations and sessions
"""

import logging

logger = logging.getLogger(__name__)

# Import SQLite version (works on all systems, no PostgreSQL required)
from guardian_db_manager_sqlite import GuardianDBManagerSQLite as GuardianDBManager

# Global instance
_guardian_manager = None


def get_guardian_manager() -> GuardianDBManager:
    """Get or create Guardian DB manager singleton"""
    global _guardian_manager
    if _guardian_manager is None:
        _guardian_manager = GuardianDBManager()
        logger.info("✓ Guardian DB Manager initialized (SQLite)")
    return _guardian_manager
