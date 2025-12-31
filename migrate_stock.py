import sqlite3
import os

db_path = 'instance/orders_v2.db'

if os.path.exists(db_path):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if column exists
        cursor.execute("PRAGMA table_info(product)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if 'is_out_of_stock' not in columns:
            print("Adding is_out_of_stock column...")
            cursor.execute("ALTER TABLE product ADD COLUMN is_out_of_stock BOOLEAN DEFAULT 0")
            conn.commit()
            print("Migration successful.")
        else:
            print("Column already exists.")
            
        conn.close()
    except Exception as e:
        print(f"Error: {e}")
else:
    print("Database not found.")
