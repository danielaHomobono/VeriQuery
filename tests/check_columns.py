import sys
import os
sys.path.insert(0, os.path.join(os.getcwd(), 'src/backend'))

from database.factory import get_database_connector

try:
    db_connector = get_database_connector()
    db_connector.connect()
    
    tables = ["Customer", "Sales", "Product", "Store", "Date"]
    
    for table_name in tables:
        print(f"\n{'='*60}")
        print(f"Table: {table_name}")
        print('='*60)
        
        result = db_connector.execute_query(f"""
            SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_CATALOG='ContosoV210k'
            AND TABLE_SCHEMA='dbo'
            AND TABLE_NAME='{table_name}'
            ORDER BY ORDINAL_POSITION
        """)
        
        if result.success:
            for row in result.data:
                col_name = row.get('COLUMN_NAME')
                col_type = row.get('DATA_TYPE')
                is_null = row.get('IS_NULLABLE')
                print(f"  {col_name:30} | {col_type:20} | Nullable: {is_null}")
        else:
            print(f"Error: {result.error}")
            
    db_connector.disconnect()
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
