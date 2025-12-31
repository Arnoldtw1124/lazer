import sqlite3
import os

# Database path
# Check root first (based on app.config 'sqlite:///orders_v2.db')
possible_paths = ["orders_v2.db", os.path.join("instance", "orders_v2.db")]
db_path = None

for p in possible_paths:
    if os.path.exists(p):
        db_path = p
        break

def fix_data():
    if not db_path:
        print(f"Error: Database not found. Searched in: {possible_paths}")
        print("Please ensure you are running this script from the project root directory.")
        return

    print(f"Connecting to database at: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Diagnostic: Check Table Info
        cursor.execute("PRAGMA table_info(product)")
        columns = [row[1] for row in cursor.fetchall()]
        print(f"Columns in 'product' table: {columns}")
        
        if 'is_visible' not in columns:
            print("CRITICAL ERROR: 'is_visible' column NOT FOUND. Migration failed.")
            print("Attempting to force add column...")
            cursor.execute("ALTER TABLE product ADD COLUMN is_visible BOOLEAN DEFAULT 1")
            print("Column forced added.")

        # Check existing data
        cursor.execute("SELECT count(*) FROM product")
        total_rows = cursor.fetchone()[0]
        print(f"Total products in DB: {total_rows}")
        
        cursor.execute("SELECT id, name, is_visible FROM product LIMIT 5")
        print("Sample data (first 5):")
        for r in cursor.fetchall():
            print(r)

        # Force Update
        print("Executing Update...")
        cursor.execute("UPDATE product SET is_visible = 1") # Unconditional Update
        
        print(f"Update executed. Changed {cursor.rowcount} rows.")
        
        conn.commit()
    except Exception as e:
        print(f"Error updating data: {e}")

    conn.close()

if __name__ == "__main__":
    fix_data()
