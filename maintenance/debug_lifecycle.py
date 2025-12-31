import os
from app import app, db, Product

def debug_lifecycle():
    print("--- Debugging Visibility Lifecycle ---")
    
    # 1. Print Configured DB Path
    print(f"App Config DB URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
    
    # 2. Context
    with app.app_context():
        # 3. Fetch Product
        print("Fetching first product...")
        p = Product.query.first()
        if not p:
            print("No products found in DB!")
            return
            
        print(f"Product ID: {p.id}")
        print(f"Current is_visible: {p.is_visible} (Type: {type(p.is_visible)})")
        
        # 4. Toggle
        print("Toggling visibility...")
        old_val = p.is_visible
        # Simulate the logic in route
        p.is_visible = not bool(old_val)
        
        db.session.commit()
        print("Committed.")
        
        # 5. Re-fetch in same session
        print(f"Post-commit (Session): {p.is_visible}")
        
    # 6. Re-fetch in NEW Session (Simulating next request)
    print("Opening NEW session/connection...")
    with app.app_context():
        p2 = Product.query.get(p.id)
        print(f"Reloaded from DB: {p2.is_visible}")
        
        if p2.is_visible == p.is_visible:
            print("SUCCESS: Persistence confirmed.")
        else:
            print("FAILURE: Data reverted! (Write failed or Write to wrong file)")

if __name__ == "__main__":
    debug_lifecycle()
