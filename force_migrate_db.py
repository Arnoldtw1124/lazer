import sqlite3
import os

# Defined absolute path matching app.py
DB_PATH = "/opt/lasercraft/orders_v2.db"

def migrate():
    print(f"Connecting to database at: {DB_PATH}")
    
    if not os.path.exists(DB_PATH):
        print("ERROR: Database file not found!")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check columns
        cursor.execute("PRAGMA table_info(product)")
        columns_info = cursor.fetchall()
        columns = [col[1] for col in columns_info]
        print(f"Current columns: {columns}")
        
        if 'is_visible' in columns:
            print("Column 'is_visible' already exists.")
        else:
            print("Column 'is_visible' MISSING. Adding it now...")
            cursor.execute("ALTER TABLE product ADD COLUMN is_visible BOOLEAN DEFAULT 1")
            print("Column added successfully.")

        if 'images' in columns:
            print("Column 'images' already exists.")
        else:
            print("Column 'images' MISSING. Adding it now...")
            cursor.execute("ALTER TABLE product ADD COLUMN images TEXT DEFAULT '[]'")
            print("Column 'images' added successfully.")
            
        # Force Update Data
        print("Updating all products to be visible...")
        cursor.execute("UPDATE product SET is_visible = 1 WHERE is_visible IS NULL")
        
        # Migrate single image to images list
        print("Migrating single images to gallery list...")
        cursor.execute("SELECT id, image, images FROM product")
        rows = cursor.fetchall()
        for row in rows:
            pid, img, imgs = row
            if img and (not imgs or imgs == '[]'):
                new_imgs = f'["{img}"]'
                cursor.execute("UPDATE product SET images = ? WHERE id = ?", (new_imgs, pid))
                print(f"Migrated image for {pid}")

        conn.commit()
        print("Data updated and committed.")
        
    except Exception as e:
        print(f"An error occurred: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
