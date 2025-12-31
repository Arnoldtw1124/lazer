import sqlite3
import os

# Database path
db_path = os.path.join("instance", "orders_v2.db")

def migrate_db():
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Add is_visible column
        # Default to 1 (True) so existing products remain visible
        cursor.execute("ALTER TABLE product ADD COLUMN is_visible BOOLEAN DEFAULT 1")
        print("Successfully added 'is_visible' column to 'product' table.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("Column 'is_visible' already exists.")
        else:
            print(f"Error adding column: {e}")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    migrate_db()
