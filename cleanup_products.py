import os
from app import app, db, Product

def cleanup_products():
    print("--- 產品清理工具 (Product Cleanup Tool) ---")
    
    with app.app_context():
        # List all products
        products = Product.query.all()
        
        if not products:
            print("目前資料庫中沒有任何產品。")
            return

        print(f"\n找到 {len(products)} 個產品：")
        print("-" * 50)
        print(f"{'ID':<15} | {'名稱 (Name)':<30} | {'狀態'}")
        print("-" * 50)
        
        for p in products:
            status = "上架中" if getattr(p, 'is_visible', True) else "未上架"
            print(f"{p.id:<15} | {p.name:<30} | {status}")
            
        print("-" * 50)
        print("\n請輸入想要刪除的產品 ID (多個 ID 請用逗號隔開)：")
        print("例如: keychain, phone_case")
        
        user_input = input("輸入 (直接按 Enter 取消): ").strip()
        
        if not user_input:
            print("已取消，未做任何變更。")
            return
            
        ids_to_delete = [x.strip() for x in user_input.split(',')]
        
        count = 0
        for pid in ids_to_delete:
            p = Product.query.get(pid)
            if p:
                db.session.delete(p)
                print(f"已標記刪除: {p.name} ({pid})")
                count += 1
            else:
                print(f"找不到 ID: {pid}，跳過。")
        
        if count > 0:
            confirm = input(f"\n確定要永久刪除這 {count} 筆資料嗎？(y/n): ")
            if confirm.lower() == 'y':
                db.session.commit()
                print("刪除完成！")
            else:
                print("操作已取消。")
        else:
            print("沒有選取有效的產品。")

if __name__ == "__main__":
    cleanup_products()
