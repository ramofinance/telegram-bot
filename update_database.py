# update_database.py
import sqlite3

def update_investments_table():
    """اضافه کردن ستون‌های جدید به جدول investments"""
    conn = sqlite3.connect('finance_bot.db')
    cursor = conn.cursor()
    
    try:
        # بررسی وجود ستون‌ها
        cursor.execute("PRAGMA table_info(investments)")
        columns = [col[1] for col in cursor.fetchall()]
        
        print("📊 ستون‌های فعلی جدول investments:")
        for col in columns:
            print(f"  • {col}")
        
        # اضافه کردن ستون transaction_receipt اگر وجود ندارد
        if 'transaction_receipt' not in columns:
            cursor.execute("ALTER TABLE investments ADD COLUMN transaction_receipt TEXT")
            print("✅ ستون transaction_receipt اضافه شد")
        
        # اضافه کردن ستون receipt_type اگر وجود ندارد
        if 'receipt_type' not in columns:
            cursor.execute("ALTER TABLE investments ADD COLUMN receipt_type TEXT DEFAULT 'none'")
            print("✅ ستون receipt_type اضافه شد")
        
        # اضافه کردن ستون‌های دیگر اگر نیاز است
        if 'confirmed_by' not in columns:
            cursor.execute("ALTER TABLE investments ADD COLUMN confirmed_by INTEGER")
            print("✅ ستون confirmed_by اضافه شد")
        
        if 'confirmed_at' not in columns:
            cursor.execute("ALTER TABLE investments ADD COLUMN confirmed_at TIMESTAMP")
            print("✅ ستون confirmed_at اضافه شد")
        
        if 'notes' not in columns:
            cursor.execute("ALTER TABLE investments ADD COLUMN notes TEXT")
            print("✅ ستون notes اضافه شد")
        
        conn.commit()
        print("🎉 دیتابیس با موفقیت آپدیت شد!")
        
    except Exception as e:
        print(f"❌ خطا در آپدیت دیتابیس: {e}")
        conn.rollback()
    
    finally:
        conn.close()

def check_database_tables():
    """بررسی ساختار دیتابیس"""
    conn = sqlite3.connect('finance_bot.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    print("\n📋 جدول‌های موجود در دیتابیس:")
    for table in tables:
        print(f"\n📁 جدول: {table[0]}")
        cursor.execute(f"PRAGMA table_info({table[0]})")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  • {col[1]} ({col[2]})")
    
    conn.close()

if __name__ == "__main__":
    print("🔄 در حال آپدیت دیتابیس...")
    update_investments_table()
    check_database_tables()
    print("\n✅ آپدیت دیتابیس کامل شد! حالا می‌توانید بات را اجرا کنید.")