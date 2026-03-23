import sys
import os
sys.path.insert(0, os.path.join(os.getcwd(), 'src/backend'))

from database.factory import get_database_connector

try:
    db_connector = get_database_connector()
    db_connector.connect()
    
    # Get all table names
    result = db_connector.execute_query("""
        SELECT TABLE_NAME 
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_CATALOG='ContosoV210k' 
        AND TABLE_SCHEMA='dbo' 
        ORDER BY TABLE_NAME
    """)
    
    if result.success:
        print("Tables in ContosoV210k database:")
        print("-" * 50)
        for row in result.data:
            print(f"  - {row.get('TABLE_NAME')}")
            
        # Get columns from fact_asistencias if it exists
        result = db_connector.execute_query("""
            SELECT COLUMN_NAME, DATA_TYPE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_CATALOG='ContosoV210k'
            AND TABLE_SCHEMA='dbo'
            AND TABLE_NAME LIKE '%asistencia%'
            ORDER BY ORDINAL_POSITION
        """)
        
        if result.success and result.row_count > 0:
            print("\n\nColumns in asistencia-related tables:")
            print("-" * 50)
            for row in result.data:
                print(f"  - {row.get('COLUMN_NAME')} ({row.get('DATA_TYPE')})")
        else:
            print("\n\nNo asistencia-related tables found.")
    else:
        print(f"Error executing query: {result.error}")
        
    db_connector.disconnect()
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
