import sqlite3
import os

# Database path
db_path = os.path.join("instance", "orders_v2.db")

def fix_data():
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Force all existing products to be visible (1) unless explicitly set to 0?
        # To be safe and restore "everything disappeared", let's set ALL to 1.
        # User implies they just added the feature, so nothing should be hidden yet.
        cursor.execute("UPDATE product SET is_visible = 1 WHERE is_visible IS NULL OR is_visible != 0")
        
        # Also check if rows were actually updated
        print(f"Updated {cursor.rowcount} rows to is_visible=1.")
        
        # Double check count
        cursor.execute("SELECT count(*) FROM product WHERE is_visible = 1")
        count = cursor.fetchone()[0]
        print(f"Total visible products: {count}")
        
    except Exception as e:
        print(f"Error updating data: {e}")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    fix_data()
