# fix_referral_codes.py
import sqlite3

def fix_referral_codes():
    """رفع مشکل کدهای رفرال"""
    conn = sqlite3.connect('finance_bot.db')
    cursor = conn.cursor()
    
    print("🔍 بررسی کدهای رفرال...")
    
    # همه کاربرانی که کد رفرال ندارند رو پیدا کن
    cursor.execute("SELECT user_id FROM users WHERE referral_code IS NULL OR referral_code = ''")
    users_without_code = cursor.fetchall()
    
    if users_without_code:
        print(f"📊 تعداد کاربران بدون کد رفرال: {len(users_without_code)}")
        
        for user in users_without_code:
            user_id = user[0]
            # ساخت کد رفرال جدید
            random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            code = f"RAMO{user_id}{random_part}"
            
            cursor.execute("UPDATE users SET referral_code = ? WHERE user_id = ?", (code, user_id))
            print(f"✅ کد رفرال برای کاربر {user_id} ساخته شد: {code}")
    else:
        print("✅ همه کاربران کد رفرال دارند!")
    
    # چک کن جدول referrals وجود داره
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='referrals'")
    if cursor.fetchone():
        print("✅ جدول referrals وجود دارد")
        
        # چک کن رکوردها درسته
        cursor.execute("SELECT COUNT(*) FROM referrals")
        count = cursor.fetchone()[0]
        print(f"📊 تعداد رکوردهای referrals: {count}")
    else:
        print("❌ جدول referrals وجود ندارد!")
    
    conn.commit()
    conn.close()
    
    print("\n✅ رفع مشکل انجام شد!")

if __name__ == "__main__":
    import random
    import string
    fix_referral_codes()
