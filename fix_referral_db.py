# fix_referral_db.py
import sqlite3
import random
import string
import os

def fix_referral_database():
    """اضافه کردن ستون‌های رفرال به جدول users و ساخت کد"""
    
    print("🔄 شروع تعمیر دیتابیس برای رفرال...")
    
    # اتصال به دیتابیس
    if not os.path.exists('finance_bot.db'):
        print("❌ فایل دیتابیس وجود ندارد!")
        return
    
    conn = sqlite3.connect('finance_bot.db')
    cursor = conn.cursor()
    
    try:
        # بررسی ستون‌های جدول users
        cursor.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]
        
        print("\n📊 ستون‌های فعلی جدول users:")
        for col in columns:
            print(f"  • {col}")
        
        # اضافه کردن ستون referral_code اگر وجود ندارد
        if 'referral_code' not in columns:
            print("\n🔄 اضافه کردن ستون referral_code...")
            cursor.execute("ALTER TABLE users ADD COLUMN referral_code TEXT UNIQUE")
            print("✅ ستون referral_code اضافه شد")
        
        # اضافه کردن ستون referred_by اگر وجود ندارد
        if 'referred_by' not in columns:
            print("🔄 اضافه کردن ستون referred_by...")
            cursor.execute("ALTER TABLE users ADD COLUMN referred_by INTEGER")
            print("✅ ستون referred_by اضافه شد")
        
        # اضافه کردن ستون total_invested اگر وجود ندارد
        if 'total_invested' not in columns:
            print("🔄 اضافه کردن ستون total_invested...")
            cursor.execute("ALTER TABLE users ADD COLUMN total_invested REAL DEFAULT 0.0")
            print("✅ ستون total_invested اضافه شد")
        
        # اضافه کردن ستون total_withdrawn اگر وجود ندارد
        if 'total_withdrawn' not in columns:
            print("🔄 اضافه کردن ستون total_withdrawn...")
            cursor.execute("ALTER TABLE users ADD COLUMN total_withdrawn REAL DEFAULT 0.0")
            print("✅ ستون total_withdrawn اضافه شد")
        
        # حالا ساخت کد رفرال برای کاربرانی که ندارند
        print("\n🔄 ساخت کد رفرال برای کاربران...")
        cursor.execute("SELECT user_id FROM users WHERE referral_code IS NULL OR referral_code = ''")
        users_without_code = cursor.fetchall()
        
        if users_without_code:
            print(f"📊 تعداد کاربران بدون کد: {len(users_without_code)}")
            
            for user in users_without_code:
                user_id = user[0]
                random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
                code = f"RAMO{user_id}{random_part}"
                
                cursor.execute("UPDATE users SET referral_code = ? WHERE user_id = ?", (code, user_id))
                print(f"  ✅ کد {code} برای کاربر {user_id}")
            
            print(f"✅ کد رفرال برای {len(users_without_code)} کاربر ساخته شد")
        else:
            print("✅ همه کاربران کد رفرال دارند!")
        
        # چک کردن جدول referrals
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='referrals'")
        if not cursor.fetchone():
            print("\n🔄 ساخت جدول referrals...")
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS referrals (
                    referral_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    referrer_id INTEGER,
                    referred_id INTEGER,
                    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'completed',
                    reward_amount REAL DEFAULT 0.0,
                    reward_paid INTEGER DEFAULT 0,
                    FOREIGN KEY (referrer_id) REFERENCES users (user_id),
                    FOREIGN KEY (referred_id) REFERENCES users (user_id),
                    UNIQUE(referred_id)
                )
            ''')
            print("✅ جدول referrals ساخته شد")
        
        conn.commit()
        print("\n🎉 دیتابیس با موفقیت به‌روز شد!")
        
        # نمایش آمار نهایی
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM users WHERE referral_code IS NOT NULL")
        users_with_code = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM referrals")
        total_refs = cursor.fetchone()[0]
        
        print("\n📊 **آمار نهایی:**")
        print(f"  👥 کل کاربران: {total_users}")
        print(f"  🔗 کاربران دارای کد رفرال: {users_with_code}")
        print(f"  🔄 تعداد رفرال‌های ثبت شده: {total_refs}")
        
    except Exception as e:
        print(f"❌ خطا: {e}")
        conn.rollback()
    finally:
        conn.close()

def check_current_status():
    """بررسی وضعیت فعلی"""
    conn = sqlite3.connect('finance_bot.db')
    cursor = conn.cursor()
    
    print("\n📋 **بررسی وضعیت فعلی دیتابیس**")
    print("=" * 50)
    
    # بررسی جدول users
    cursor.execute("PRAGMA table_info(users)")
    columns = cursor.fetchall()
    print("\n📁 جدول users:")
    for col in columns:
        print(f"  • {col[1]} ({col[2]})")
    
    # نمونه کاربران
    cursor.execute("SELECT user_id, full_name, referral_code, referred_by FROM users LIMIT 3")
    users = cursor.fetchall()
    if users:
        print("\n👤 نمونه کاربران:")
        for user in users:
            print(f"  ID: {user[0]}, Name: {user[1]}, Code: {user[2]}, Referred By: {user[3]}")
    
    # بررسی جدول referrals
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='referrals'")
    if cursor.fetchone():
        cursor.execute("PRAGMA table_info(referrals)")
        columns = cursor.fetchall()
        print("\n📁 جدول referrals:")
        for col in columns:
            print(f"  • {col[1]} ({col[2]})")
        
        cursor.execute("SELECT COUNT(*) FROM referrals")
        count = cursor.fetchone()[0]
        print(f"  📊 تعداد رکوردها: {count}")
    
    conn.close()

if __name__ == "__main__":
    print("🔧 **ابزار تعمیر دیتابیس رفرال**")
    print("=" * 50)
    
    # اول وضعیت فعلی رو نشون بده
    check_current_status()
    
    print("\n" + "=" * 50)
    answer = input("آیا می‌خواهید دیتابیس را تعمیر کنید؟ (y/n): ")
    
    if answer.lower() == 'y':
        fix_referral_database()
        print("\n" + "=" * 50)
        check_current_status()
    else:
        print("❌ عملیات لغو شد.")
