# 🚀 P2 CLEANUP ACTION PLAN

## Step-by-Step Execution Guide

**Estimated Time:** ~45 minutes  
**Risk Level:** LOW (only deleting dev files & dead code)  
**Backup:** Git history preserves all deletions

---

## PHASE 1: Delete Phantom Dev Files (5 mins)

### Step 1.1: Delete Dev Launcher Scripts from `/api`

These are old development files, NOT tracked in git (untracked):

```powershell
cd c:\Users\Daniela\Desktop\forensicGuardian\src\backend\api

# Verify files exist
ls -Name | grep -E "debug_|run_|start_|ultra_"

# Delete them
Remove-Item debug_server.py -Force
Remove-Item run_server.py -Force
Remove-Item start_server.py -Force
Remove-Item ultra_minimal.py -Force

# Verify deletion
ls *.py
```

Expected output after: Only `main.py`, `__init__.py`, and `routers/` folder remain in `/api`

### Step 1.2: Delete Phantom services/nl2sql_generator.py

This is an OLD PROTOTYPE that conflicts with the real one at root:

```powershell
cd c:\Users\Daniela\Desktop\forensicGuardian\src\backend\services

# Verify it's different from root nl2sql_generator.py
cat nl2sql_generator.py | head -20

# Delete
Remove-Item nl2sql_generator.py -Force

# Verify
ls *.py
```

Expected output: Only `query_service.py` and `__init__.py` remain

---

## PHASE 2: Delete Test Files from Root (5 mins)

These were moved to `/tests` already, so delete from `/src/backend/`:

```powershell
cd c:\Users\Daniela\Desktop\forensicGuardian\src\backend

# Verify they exist
ls test_*.py

# Stage for git removal (so they're tracked as deleted)
git rm test_query_crafter.py
git rm test_query_crafter_semantic.py
git rm test_semantic_mapping.py

# Verify they're staged for deletion
git status
```

Expected: 3 files show as "deleted"

---

## PHASE 3: Delete Empty Directories (5 mins)

```powershell
cd c:\Users\Daniela\Desktop\forensicGuardian\src\backend

# Verify they're empty
ls repositories/
ls exceptions/

# Stage for git removal
git rm -r repositories/
git rm -r exceptions/

# Verify
git status
```

Expected: Both directories show as "deleted"

---

## PHASE 4: Fix Stale Documentation (10 mins)

### Step 4.1: Delete or Refactor `verify_system.py`

This script tries to import deleted files. Options:

**OPTION A: Delete it (Simple)**
```powershell
git rm src/backend/verify_system.py
```

**OPTION B: Refactor it (Keep for CI/CD)**

If you want to keep it for system verification, update it:

```python
# Replace references to table_mapping with new approach
# Create a new verify_system.py that checks:
# - QueryService imports
# - Router includes
# - Database connectors available
# - Azure OpenAI config
```

**Recommendation:** Delete (OPTION A) — not part of main execution.

```powershell
git rm src/backend/verify_system.py
```

### Step 4.2: Update `TESTING_GUIDE.md`

This file still references `core.schema` (deleted). Update it:

```powershell
cd c:\Users\Daniela\Desktop\forensicGuardian\src\backend

# View the problematic line
cat TESTING_GUIDE.md | Select-String -Pattern "core.schema"

# Edit it manually:
# Change: from src.backend.core.schema import get_schema_prompt
# To: # Schema is now dynamically loaded from the database
# See: nl2sql_generator.py set_active_database() method
```

Or delete it if it's no longer useful:
```powershell
git rm TESTING_GUIDE.md
```

**Recommendation:** Delete (it's covered by inline documentation in code).

```powershell
git rm src/backend/TESTING_GUIDE.md
```

---

## PHASE 5: Review & Decide on multi_db_connector.py (15 mins)

This is the ONLY file that's actually in use but potentially redundant.

### Step 5.1: Understand Current Usage

```powershell
cd c:\Users\Daniela\Desktop\forensicGuardian\src\backend

# Find all references
grep -r "multi_db_connector" --include="*.py" | grep -v "__pycache__"
```

Expected output:
```
api/database_management_router.py: from database import multi_db_connector
api/schema_scanner_router.py: from database import multi_db_connector
```

### Step 5.2: Review What multi_db_connector Does

```powershell
# View the first 50 lines
cat src\backend\database\multi_db_connector.py | head -50
```

### Step 5.3: Decision

**OPTION A: Keep multi_db_connector.py**
- If database_management_router and schema_scanner_router are actively used
- Add comment: "Adapter for legacy routers. See factory.py for new code."
- Leave as-is for now

**OPTION B: Consolidate into factory.py** (Recommended)
- Merge multi_db_connector functionality into factory.py
- Update database_management_router and schema_scanner_router to use factory.py
- Delete multi_db_connector.py
- **This is P2.2 — can be done in separate PR**

**For NOW:** Just add a comment to document it as "legacy adapter"

```python
# At top of multi_db_connector.py, add:
"""
LEGACY ADAPTER — DO NOT USE IN NEW CODE

This module wraps ConnectionManager/BDConfigManager for backward compatibility
with database_management_router and schema_scanner_router.

New code should use database/factory.py directly.
See: ARCHITECTURE_AUDIT.md section P2.2 for consolidation plan.
"""
```

---

## PHASE 6: Commit Everything (5 mins)

```powershell
cd c:\Users\Daniela\Desktop\forensicGuardian

# View all staged changes
git status

# Commit
git commit -m "cleanup(P2): Delete dead dev files and obsolete tests

- Remove: api/debug_server.py, run_server.py, start_server.py, ultra_minimal.py
- Remove: services/nl2sql_generator.py (phantom prototype)
- Remove: test_*.py from root (already in /tests)
- Remove: repositories/ and exceptions/ empty directories
- Remove: verify_system.py (outdated)
- Remove: TESTING_GUIDE.md (covered by inline docs and ARCHITECTURE_AUDIT.md)

All changes documented in ARCHITECTURE_AUDIT.md section P2.1"

# Verify
git log --oneline -1
```

---

## PHASE 7: Verify System Still Works (5 mins)

After cleanup, verify the API still starts:

```powershell
cd c:\Users\Daniela\Desktop\forensicGuardian\src\backend\api

# Try to import main (no errors should occur)
python -c "import sys; sys.path.insert(0, '..'); from main import app; print('✅ main.py imports successfully')"

# Check git status
cd c:\Users\Daniela\Desktop\forensicGuardian
git status
```

Expected:
- main.py imports without errors
- git status shows "working tree clean" or only untracked __pycache__

---

## OPTIONAL: P2.2 QUICK CONSOLIDATION (30 mins, separate PR)

**Only if you want to do this now:**

### Consolidate multi_db_connector.py into factory.py

```python
# In database/factory.py, add this code:

class BDConfigManager:
    """Manager for database connections and metadata."""
    
    @staticmethod
    def get_connection_details(db_name: str) -> dict:
        """Get connection string and metadata for database."""
        # Logic from multi_db_connector.ConnectionManager
        
    @staticmethod
    def list_databases() -> list:
        """List available databases."""
        # Logic from multi_db_connector
```

Then in routers:
```python
# BEFORE
from database import multi_db_connector
schemas = multi_db_connector.get_schemas()

# AFTER  
from database.factory import BDConfigManager
schemas = BDConfigManager.get_schemas()
```

---

## ✅ SUCCESS CRITERIA

After P2 completion, you should have:

- ✅ `/src/backend/api/` contains ONLY: main.py, __init__.py, routers/
- ✅ `/src/backend/services/` contains ONLY: query_service.py, __init__.py
- ✅ `/src/backend/` contains NO test_*.py files (all moved to /tests)
- ✅ `/src/backend/repositories/` and `/src/backend/exceptions/` directories deleted
- ✅ `verify_system.py` and `TESTING_GUIDE.md` removed (outdated)
- ✅ API still starts without errors
- ✅ New file: ARCHITECTURE_AUDIT.md (reference documentation)
- ✅ Multi-DB support still works (database_management_router, schema_scanner_router functional)

**Final Result:** Clean, professional codebase ready for production.

---

## 🎯 QUICK REFERENCE COMMANDS

**Delete all at once (if confident):**
```powershell
cd c:\Users\Daniela\Desktop\forensicGuardian\src\backend

# Stage all removals
git rm api/debug_server.py api/run_server.py api/start_server.py api/ultra_minimal.py
git rm services/nl2sql_generator.py
git rm test_query_crafter.py test_query_crafter_semantic.py test_semantic_mapping.py
git rm -r repositories/ exceptions/
git rm verify_system.py TESTING_GUIDE.md

# Also manually delete untracked files
Remove-Item api/debug_server.py -ErrorAction SilentlyContinue
Remove-Item api/run_server.py -ErrorAction SilentlyContinue
Remove-Item api/start_server.py -ErrorAction SilentlyContinue
Remove-Item api/ultra_minimal.py -ErrorAction SilentlyContinue
Remove-Item services/nl2sql_generator.py -ErrorAction SilentlyContinue

# Commit
git commit -m "cleanup(P2): Remove all dead code (see ARCHITECTURE_AUDIT.md)"

# Verify
git status
```

---

**READY?** → Execute from PHASE 1 onwards. Questions? Review ARCHITECTURE_AUDIT.md.
