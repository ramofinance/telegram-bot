# database.py
import sqlite3
from datetime import datetime, timedelta
import random
import string

class Database:
    def __init__(self, db_name="finance_bot.db"):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.create_tables()
    
    def create_tables(self):
        cursor = self.conn.cursor()
        
        # جدول کاربران
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                language TEXT DEFAULT 'en',
                full_name TEXT,
                email TEXT,
                phone TEXT,
                wallet_address TEXT,
                balance REAL DEFAULT 0.0,
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active INTEGER DEFAULT 1,
                last_login TIMESTAMP,
                referral_code TEXT UNIQUE,
                referred_by INTEGER,
                total_invested REAL DEFAULT 0.0,
                total_withdrawn REAL DEFAULT 0.0
            )
        ''')
        
        # جدول سرمایه‌گذاری‌ها
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS investments (
                investment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                package TEXT,
                amount REAL,
                duration INTEGER,
                start_date TIMESTAMP,
                end_date TIMESTAMP,
                status TEXT DEFAULT 'pending',
                monthly_profit_percent REAL,
                transaction_receipt TEXT,
                receipt_type TEXT DEFAULT 'none',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                confirmed_by INTEGER,
                confirmed_at TIMESTAMP,
                notes TEXT,
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                FOREIGN KEY (confirmed_by) REFERENCES users (user_id)
            )
        ''')
        
        # جدول تیکت‌ها
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tickets (
                ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                subject TEXT,
                message TEXT,
                status TEXT DEFAULT 'open',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                admin_response TEXT,
                responded_at TIMESTAMP,
                responded_by INTEGER,
                priority TEXT DEFAULT 'normal',
                category TEXT,
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                FOREIGN KEY (responded_by) REFERENCES users (user_id)
            )
        ''')
        
        # جدول تراکنش‌ها
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                type TEXT,
                amount REAL,
                description TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                wallet_address TEXT,
                transaction_hash TEXT,
                admin_notes TEXT,
                processed_by INTEGER,
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                FOREIGN KEY (processed_by) REFERENCES users (user_id)
            )
        ''')
        
        # جدول پرداخت سود ماهانه
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS profit_payments (
                payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                investment_id INTEGER,
                amount REAL,
                payment_date TIMESTAMP,
                status TEXT DEFAULT 'pending',
                wallet_address TEXT,
                transaction_hash TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                FOREIGN KEY (investment_id) REFERENCES investments (investment_id)
            )
        ''')
        
        # جدول اعلان‌ها
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notifications (
                notification_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                type TEXT,
                title TEXT,
                message TEXT,
                is_read INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                related_id INTEGER,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # جدول لاگ‌های سیستم
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_logs (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT,
                details TEXT,
                ip_address TEXT,
                user_agent TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # جدول رفرال‌ها (جدید)
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
        
        self.conn.commit()
    
    # ===== توابع کاربران =====
    
    def add_user(self, user_id, language='en'):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR IGNORE INTO users (user_id, language) 
            VALUES (?, ?)
        ''', (user_id, language))
        self.conn.commit()
    
    def update_user_language(self, user_id, language):
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE users SET language = ? WHERE user_id = ?
        ''', (language, user_id))
        self.conn.commit()
    
    def update_user_profile(self, user_id, full_name, email, phone, wallet_address):
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE users 
            SET full_name = ?, email = ?, phone = ?, wallet_address = ?
            WHERE user_id = ?
        ''', (full_name, email, phone, wallet_address, user_id))
        self.conn.commit()
    
    def update_user_balance(self, user_id, amount, operation='add'):
        cursor = self.conn.cursor()
        
        if operation == 'add':
            cursor.execute('''
                UPDATE users 
                SET balance = balance + ?
                WHERE user_id = ?
            ''', (amount, user_id))
        elif operation == 'subtract':
            cursor.execute('''
                UPDATE users 
                SET balance = balance - ?
                WHERE user_id = ?
            ''', (amount, user_id))
        elif operation == 'set':
            cursor.execute('''
                UPDATE users 
                SET balance = ?
                WHERE user_id = ?
            ''', (amount, user_id))
        
        self.conn.commit()
    
    def get_user(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        return cursor.fetchone()
    
    def get_user_language(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT language FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        return result[0] if result else 'en'
    
    def get_all_users(self, limit=100, offset=0):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT user_id, language, full_name, email, phone, wallet_address, balance, registered_at 
            FROM users 
            ORDER BY registered_at DESC 
            LIMIT ? OFFSET ?
        ''', (limit, offset))
        return cursor.fetchall()
    
    def get_users_count(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM users')
        return cursor.fetchone()[0]
    
    def search_users(self, search_term):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT user_id, full_name, email, phone, wallet_address, registered_at 
            FROM users 
            WHERE full_name LIKE ? OR email LIKE ? OR phone LIKE ? OR wallet_address LIKE ?
            LIMIT 50
        ''', (f'%{search_term}%', f'%{search_term}%', f'%{search_term}%', f'%{search_term}%'))
        return cursor.fetchall()
    
    # ===== توابع سرمایه‌گذاری =====
    
    def create_investment(self, user_id, package, amount, duration, monthly_profit_percent, 
                         transaction_receipt='', receipt_type='none'):
        cursor = self.conn.cursor()
        
        start_date = datetime.now()
        if duration == 999:
            end_date = datetime(2099, 12, 31)
        else:
            end_date = start_date + timedelta(days=duration*30)
        
        cursor.execute('''
            INSERT INTO investments 
            (user_id, package, amount, duration, start_date, end_date, 
             status, monthly_profit_percent, transaction_receipt, receipt_type)
            VALUES (?, ?, ?, ?, ?, ?, 'pending', ?, ?, ?)
        ''', (user_id, package, amount, duration, start_date, end_date, 
              monthly_profit_percent, transaction_receipt, receipt_type))
        
        self.conn.commit()
        return cursor.lastrowid
    
    def get_user_investments(self, user_id, limit=20):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT investment_id, package, amount, start_date, status, 
                   monthly_profit_percent, transaction_receipt, created_at
            FROM investments 
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        ''', (user_id, limit))
        return cursor.fetchall()
    
    def get_investment(self, investment_id):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT i.*, u.full_name, u.wallet_address, u.language
            FROM investments i
            JOIN users u ON i.user_id = u.user_id
            WHERE i.investment_id = ?
        ''', (investment_id,))
        return cursor.fetchone()
    
    def update_investment_status(self, investment_id, status, confirmed_by=None, notes=''):
        cursor = self.conn.cursor()
        
        if confirmed_by:
            cursor.execute('''
                UPDATE investments 
                SET status = ?, confirmed_by = ?, confirmed_at = CURRENT_TIMESTAMP,
                    notes = ?, updated_at = CURRENT_TIMESTAMP
                WHERE investment_id = ?
            ''', (status, confirmed_by, notes, investment_id))
        else:
            cursor.execute('''
                UPDATE investments 
                SET status = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
                WHERE investment_id = ?
            ''', (status, notes, investment_id))
        
        self.conn.commit()
        return cursor.rowcount > 0
    
    def get_active_investments(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT i.*, u.full_name, u.wallet_address
            FROM investments i
            JOIN users u ON i.user_id = u.user_id
            WHERE i.status = 'active'
            ORDER BY i.start_date ASC
        ''')
        return cursor.fetchall()
    
    def get_pending_investments(self, limit=50):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT i.*, u.full_name, u.wallet_address, u.user_id
            FROM investments i
            JOIN users u ON i.user_id = u.user_id
            WHERE i.status = 'pending'
            ORDER BY i.created_at DESC
            LIMIT ?
        ''', (limit,))
        return cursor.fetchall()
    
    def get_investments_count(self, status=None):
        cursor = self.conn.cursor()
        
        if status:
            cursor.execute('SELECT COUNT(*) FROM investments WHERE status = ?', (status,))
        else:
            cursor.execute('SELECT COUNT(*) FROM investments')
        
        return cursor.fetchone()[0]
    
    def get_total_invested_amount(self, status='active'):
        cursor = self.conn.cursor()
        cursor.execute('SELECT SUM(amount) FROM investments WHERE status = ?', (status,))
        result = cursor.fetchone()[0]
        return result if result else 0
    
    def get_user_total_investment(self, user_id, status='active'):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT SUM(amount) 
            FROM investments 
            WHERE user_id = ? AND status = ?
        ''', (user_id, status))
        result = cursor.fetchone()[0]
        return result if result else 0
    
    def get_user_monthly_profit(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT SUM(amount * monthly_profit_percent / 100)
            FROM investments 
            WHERE user_id = ? AND status = 'active'
        ''', (user_id,))
        result = cursor.fetchone()[0]
        return result if result else 0
    
    # ===== توابع تیکت‌ها =====
    
    def create_ticket(self, user_id, subject, message):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO tickets (user_id, subject, message, status)
            VALUES (?, ?, ?, 'open')
        ''', (user_id, subject, message))
        self.conn.commit()
        return cursor.lastrowid
    
    def get_user_tickets(self, user_id, limit=10):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT ticket_id, subject, status, created_at, admin_response, responded_at
            FROM tickets 
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        ''', (user_id, limit))
        return cursor.fetchall()
    
    def get_ticket(self, ticket_id):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT t.*, u.full_name, u.email
            FROM tickets t
            JOIN users u ON t.user_id = u.user_id
            WHERE t.ticket_id = ?
        ''', (ticket_id,))
        return cursor.fetchone()
    
    def get_open_tickets(self, limit=20):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT t.ticket_id, t.subject, t.created_at, u.full_name, u.user_id
            FROM tickets t
            JOIN users u ON t.user_id = u.user_id
            WHERE t.status = 'open'
            ORDER BY t.created_at ASC
            LIMIT ?
        ''', (limit,))
        return cursor.fetchall()
    
    def update_ticket_response(self, ticket_id, admin_response, responded_by):
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE tickets 
            SET admin_response = ?, status = 'answered', 
                responded_at = CURRENT_TIMESTAMP, responded_by = ?
            WHERE ticket_id = ?
        ''', (admin_response, responded_by, ticket_id))
        self.conn.commit()
        return cursor.rowcount > 0
    
    def close_ticket(self, ticket_id):
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE tickets 
            SET status = 'closed'
            WHERE ticket_id = ?
        ''', (ticket_id,))
        self.conn.commit()
        return cursor.rowcount > 0
    
    def get_tickets_count(self, status=None):
        cursor = self.conn.cursor()
        
        if status:
            cursor.execute('SELECT COUNT(*) FROM tickets WHERE status = ?', (status,))
        else:
            cursor.execute('SELECT COUNT(*) FROM tickets')
        
        return cursor.fetchone()[0]
    
    # ===== توابع تراکنش‌ها =====
    
    def create_transaction(self, user_id, type, amount, description, 
                          status='pending', wallet_address='', transaction_hash=''):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO transactions 
            (user_id, type, amount, description, status, wallet_address, transaction_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, type, amount, description, status, wallet_address, transaction_hash))
        self.conn.commit()
        return cursor.lastrowid
    
    def get_user_transactions(self, user_id, limit=20):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT transaction_id, type, amount, description, status, created_at, transaction_hash
            FROM transactions 
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        ''', (user_id, limit))
        return cursor.fetchall()
    
    def update_transaction_status(self, transaction_id, status, processed_by=None, admin_notes=''):
        cursor = self.conn.cursor()
        
        if processed_by:
            cursor.execute('''
                UPDATE transactions 
                SET status = ?, processed_by = ?, completed_at = CURRENT_TIMESTAMP,
                    admin_notes = ?
                WHERE transaction_id = ?
            ''', (status, processed_by, admin_notes, transaction_id))
        else:
            cursor.execute('''
                UPDATE transactions 
                SET status = ?, completed_at = CURRENT_TIMESTAMP, admin_notes = ?
                WHERE transaction_id = ?
            ''', (status, admin_notes, transaction_id))
        
        self.conn.commit()
        return cursor.rowcount > 0
    
    # ===== توابع پرداخت سود =====
    
    def create_profit_payment(self, user_id, investment_id, amount, wallet_address):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO profit_payments 
            (user_id, investment_id, amount, payment_date, wallet_address, status)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP, ?, 'pending')
        ''', (user_id, investment_id, amount, wallet_address))
        self.conn.commit()
        return cursor.lastrowid
    
    def update_profit_payment(self, payment_id, status, transaction_hash=''):
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE profit_payments 
            SET status = ?, transaction_hash = ?
            WHERE payment_id = ?
        ''', (status, transaction_hash, payment_id))
        self.conn.commit()
        return cursor.rowcount > 0
    
    def get_pending_profit_payments(self, limit=50):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT p.*, u.full_name, u.wallet_address
            FROM profit_payments p
            JOIN users u ON p.user_id = u.user_id
            WHERE p.status = 'pending'
            ORDER BY p.payment_date ASC
            LIMIT ?
        ''', (limit,))
        return cursor.fetchall()
    
    # ===== توابع اعلان‌ها =====
    
    def create_notification(self, user_id, type, title, message, related_id=None):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO notifications (user_id, type, title, message, related_id)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, type, title, message, related_id))
        self.conn.commit()
        return cursor.lastrowid
    
    def get_user_notifications(self, user_id, unread_only=False, limit=20):
        cursor = self.conn.cursor()
        
        if unread_only:
            cursor.execute('''
                SELECT notification_id, type, title, message, created_at, is_read
                FROM notifications 
                WHERE user_id = ? AND is_read = 0
                ORDER BY created_at DESC
                LIMIT ?
            ''', (user_id, limit))
        else:
            cursor.execute('''
                SELECT notification_id, type, title, message, created_at, is_read
                FROM notifications 
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            ''', (user_id, limit))
        
        return cursor.fetchall()
    
    def mark_notification_as_read(self, notification_id):
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE notifications 
            SET is_read = 1
            WHERE notification_id = ?
        ''', (notification_id,))
        self.conn.commit()
        return cursor.rowcount > 0
    
    # ===== توابع لاگ‌های سیستم =====
    
    def add_system_log(self, user_id, action, details='', ip_address='', user_agent=''):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO system_logs (user_id, action, details, ip_address, user_agent)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, action, details, ip_address, user_agent))
        self.conn.commit()
        return cursor.lastrowid
    
    def get_system_logs(self, limit=100):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT l.*, u.full_name
            FROM system_logs l
            LEFT JOIN users u ON l.user_id = u.user_id
            ORDER BY l.created_at DESC
            LIMIT ?
        ''', (limit,))
        return cursor.fetchall()
    
    # ===== توابع آمار و گزارشات =====
    
    def get_system_statistics(self):
        cursor = self.conn.cursor()
        
        stats = {}
        
        # آمار کاربران
        cursor.execute("SELECT COUNT(*) FROM users")
        stats['total_users'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM users WHERE DATE(registered_at) = DATE('now')")
        stats['today_users'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM users WHERE DATE(registered_at) >= DATE('now', '-7 days')")
        stats['weekly_users'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM users WHERE wallet_address IS NOT NULL AND wallet_address != ''")
        stats['users_with_wallet'] = cursor.fetchone()[0]
        
        # آمار سرمایه‌گذاری
        cursor.execute("SELECT COUNT(*) FROM investments")
        stats['total_investments'] = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT SUM(amount) FROM investments WHERE status = 'active'")
        stats['total_active_amount'] = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT SUM(amount) FROM investments WHERE DATE(created_at) = DATE('now')")
        stats['today_investments'] = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT SUM(amount * monthly_profit_percent / 100) FROM investments WHERE status = 'active'")
        stats['monthly_profit'] = cursor.fetchone()[0] or 0
        
        # آمار مالی
        cursor.execute("SELECT SUM(balance) FROM users")
        stats['total_balance'] = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT SUM(amount) FROM transactions WHERE type = 'deposit' AND status = 'completed'")
        stats['total_deposits'] = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT SUM(amount) FROM transactions WHERE type = 'withdrawal' AND status = 'completed'")
        stats['total_withdrawals'] = cursor.fetchone()[0] or 0
        
        # آمار تیکت‌ها
        cursor.execute("SELECT COUNT(*) FROM tickets WHERE status = 'open'")
        stats['open_tickets'] = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT COUNT(*) FROM tickets WHERE status = 'answered'")
        stats['answered_tickets'] = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT COUNT(*) FROM tickets")
        stats['total_tickets'] = cursor.fetchone()[0] or 0
        
        return stats
    
    # ===== توابع رفرال (جدید) =====
    
    def generate_referral_code(self, user_id: int) -> str:
        """تولید کد رفرال یکتا برای کاربر"""
        # ترکیبی از user_id و کاراکترهای تصادفی
        random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        code = f"RAMO{user_id}{random_part}"
        
        # اطمینان از یکتا بودن
        cursor = self.conn.cursor()
        cursor.execute("SELECT user_id FROM users WHERE referral_code = ?", (code,))
        while cursor.fetchone():
            random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            code = f"RAMO{user_id}{random_part}"
            cursor.execute("SELECT user_id FROM users WHERE referral_code = ?", (code,))
        
        return code

    def set_user_referral_code(self, user_id: int, code: str = None):
        """تنظیم کد رفرال برای کاربر"""
        if not code:
            code = self.generate_referral_code(user_id)
        
        cursor = self.conn.cursor()
        cursor.execute("UPDATE users SET referral_code = ? WHERE user_id = ?", (code, user_id))
        self.conn.commit()
        return code

    def get_user_referral_code(self, user_id: int) -> str:
        """دریافت کد رفرال کاربر"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT referral_code FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        
        if result and result[0]:
            return result[0]
        else:
            # اگر کد نداشت، براش بساز
            return self.set_user_referral_code(user_id)

    def get_user_by_referral_code(self, code: str):
        """یافتن کاربر بر اساس کد رفرال"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT user_id FROM users WHERE referral_code = ?", (code,))
        result = cursor.fetchone()
        return result[0] if result else None

    def register_referral(self, referrer_id: int, referred_id: int):
        """ثبت یک دعوت جدید"""
        cursor = self.conn.cursor()
        
        # بررسی تکراری نبودن
        cursor.execute("SELECT * FROM referrals WHERE referred_id = ?", (referred_id,))
        if cursor.fetchone():
            return False
        
        cursor.execute('''
            INSERT INTO referrals (referrer_id, referred_id, status)
            VALUES (?, ?, 'completed')
        ''', (referrer_id, referred_id))
        
        self.conn.commit()
        
        # به‌روزرسانی کاربر دعوت‌شده
        cursor.execute("UPDATE users SET referred_by = ? WHERE user_id = ?", (referrer_id, referred_id))
        self.conn.commit()
        
        return True

    def get_user_referrals(self, user_id: int, limit: int = 20):
        """دریافت لیست دعوت‌های یک کاربر"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT r.referred_id, u.full_name, u.registered_at, u.total_invested
            FROM referrals r
            JOIN users u ON r.referred_id = u.user_id
            WHERE r.referrer_id = ?
            ORDER BY r.registered_at DESC
            LIMIT ?
        ''', (user_id, limit))
        
        return cursor.fetchall()

    def get_referral_stats(self, user_id: int):
        """آمار دعوت‌های یک کاربر"""
        cursor = self.conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM referrals WHERE referrer_id = ?", (user_id,))
        total_referrals = cursor.fetchone()[0] or 0
        
        cursor.execute('''
            SELECT COUNT(*) FROM referrals r
            JOIN users u ON r.referred_id = u.user_id
            WHERE r.referrer_id = ? AND u.total_invested > 0
        ''', (user_id,))
        active_referrals = cursor.fetchone()[0] or 0
        
        cursor.execute('''
            SELECT SUM(u.total_invested) FROM referrals r
            JOIN users u ON r.referred_id = u.user_id
            WHERE r.referrer_id = ?
        ''', (user_id,))
        total_invested = cursor.fetchone()[0] or 0
        
        return {
            'total': total_referrals,
            'active': active_referrals,
            'total_invested': total_invested
        }
    
    # ===== توابع عمومی =====
    
    def execute_query(self, query, params=()):
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        self.conn.commit()
        return cursor
    
    def get_table_info(self, table_name):
        cursor = self.conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        return cursor.fetchall()
    
    def get_all_tables(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        return cursor.fetchall()
    
    def backup_database(self, backup_name=None):
        """ایجاد بک‌آپ از دیتابیس"""
        import shutil
        import os
        
        if backup_name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"finance_bot_backup_{timestamp}.db"
        
        shutil.copy2("finance_bot.db", backup_name)
        return backup_name
    
    def close(self):
        self.conn.close()
