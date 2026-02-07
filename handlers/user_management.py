import os
from datetime import datetime
from aiogram import F, Router
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext

from database import Database

router = Router()
db = Database()

def is_admin(user_id: int) -> bool:
    """بررسی اینکه کاربر ادمین هست یا نه"""
    admin_ids_str = os.getenv("ADMIN_IDS", "")
    if admin_ids_str:
        admin_ids = [int(id_str.strip()) for id_str in admin_ids_str.split(",") if id_str.strip()]
        return user_id in admin_ids
    return False

def get_users_list_keyboard(page: int = 0, total_pages: int = 1, user_id: int = None):
    """کیبورد صفحه‌بندی کاربران با دکمه مشاهده جزئیات"""
    keyboard = []
    
    # دکمه‌های صفحه‌بندی
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ قبلی", callback_data=f"users_page_{page-1}"))
    
    nav_buttons.append(InlineKeyboardButton(text=f"📄 {page+1}/{total_pages}", callback_data="current_page"))
    
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton(text="➡️ بعدی", callback_data=f"users_page_{page+1}"))
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    # دکمه مشاهده جزئیات کاربر خاص
    if user_id:
        keyboard.append([
            InlineKeyboardButton(text="👁️ مشاهده جزئیات", callback_data=f"view_user_{user_id}")
        ])
    
    keyboard.append([InlineKeyboardButton(text="🔙 بازگشت به ادمین", callback_data="back_to_admin")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

@router.message(F.text.in_(["👥 مدیریت کاربران", "👥 User Management", 
                          "👥 لیست کاربران (جدید)", "👥 Users List (New)"]))
async def handle_all_user_list_buttons(message: Message):
    """هندلر همه دکمه‌های لیست کاربران"""
    if not is_admin(message.from_user.id):
        return
    
    language = 'fa' if any(text in message.text for text in ["👥 مدیریت کاربران", "👥 لیست کاربران"]) else 'en'
    
    await show_users_page(message, page=0, language=language)

async def show_users_page(message: Message, page: int = 0, language: str = 'fa', edit_message: bool = False):
    """نمایش صفحه کاربران"""
    limit = 6
    offset = page * limit
    
    cursor = db.conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    total_pages = max(1, (total_users + limit - 1) // limit)
    
    # **مهم: همه فیلدها رو بگیر**
    cursor.execute("""
        SELECT user_id, language, full_name, email, phone, wallet_address, balance, registered_at 
        FROM users 
        ORDER BY registered_at DESC 
        LIMIT ? OFFSET ?
    """, (limit, offset))
    
    users = cursor.fetchall()
    
    if language == 'fa':
        users_list = f"📋 <b>لیست کاربران - صفحه {page+1} از {total_pages}</b>\n\n"
        users_list += f"👥 کل کاربران: {total_users}\n"
        users_list += f"📍 نمایش: {len(users)} کاربر\n\n"
        users_list += "━" * 30 + "\n\n"
        
        for idx, user in enumerate(users, 1):
            user_id, lang, full_name, email, phone, wallet, balance, reg_date = user
            
            users_list += f"<b>🔸 {offset + idx}. {full_name or 'بدون نام'}</b>\n"
            users_list += f"   🆔: <code>{user_id}</code>\n"
            
            # ایمیل
            email_display = email if email and email not in ['ندارد', 'Not provided', ''] else '❌ ندارد'
            users_list += f"   📧: {email_display}\n"
            
            # تلفن
            phone_display = phone if phone and phone not in ['ندارد', 'Not provided', ''] else '❌ ندارد'
            users_list += f"   📱: {phone_display}\n"
            
            # موجودی
            users_list += f"   💰: ${balance:.2f}\n"
            
            # کیف پول
            if wallet and wallet.strip():
                if len(wallet) > 80:
                    wallet_display = f"{wallet[:15]}...{wallet[-10:]}"
                else:
                    wallet_display = wallet
                users_list += f"   🔐: <code>{wallet_display}</code>\n"
                users_list += f"   📏: {len(wallet)} کاراکتر\n"
            else:
                users_list += f"   🔐: ❌ ثبت نشده\n"
            
            users_list += f"   🌐: {lang}\n"
            users_list += f"   📅: {reg_date[:10]}\n"
            users_list += f"   👁️: دکمه پایین\n\n"
            users_list += "─" * 25 + "\n\n"
            
    else:
        users_list = f"📋 <b>Users List - Page {page+1} of {total_pages}</b>\n\n"
        users_list += f"👥 Total Users: {total_users}\n"
        users_list += f"📍 Showing: {len(users)} users\n\n"
        users_list += "━" * 30 + "\n\n"
        
        for idx, user in enumerate(users, 1):
            user_id, lang, full_name, email, phone, wallet, balance, reg_date = user
            
            users_list += f"<b>🔸 {offset + idx}. {full_name or 'No name'}</b>\n"
            users_list += f"   🆔: <code>{user_id}</code>\n"
            
            email_display = email if email and email not in ['None', 'Not provided', ''] else '❌ None'
            users_list += f"   📧: {email_display}\n"
            
            phone_display = phone if phone and phone not in ['None', 'Not provided', ''] else '❌ None'
            users_list += f"   📱: {phone_display}\n"
            
            users_list += f"   💰: ${balance:.2f}\n"
            
            if wallet and wallet.strip():
                if len(wallet) > 80:
                    wallet_display = f"{wallet[:15]}...{wallet[-10:]}"
                else:
                    wallet_display = wallet
                users_list += f"   🔐: <code>{wallet_display}</code>\n"
                users_list += f"   📏: {len(wallet)} chars\n"
            else:
                users_list += f"   🔐: ❌ Not set\n"
            
            users_list += f"   🌐: {lang}\n"
            users_list += f"   📅: {reg_date[:10]}\n"
            users_list += f"   👁️: Button below\n\n"
            users_list += "─" * 25 + "\n\n"
    
    if edit_message:
        await message.edit_text(
            users_list,
            parse_mode="HTML",
            reply_markup=get_users_list_keyboard(page, total_pages)
        )
    else:
        await message.answer(
            users_list,
            parse_mode="HTML",
            reply_markup=get_users_list_keyboard(page, total_pages)
        )

@router.callback_query(lambda c: c.data.startswith("users_page_"))
async def handle_users_pagination(callback_query: CallbackQuery):
    """مدیریت صفحه‌بندی کاربران"""
    if not is_admin(callback_query.from_user.id):
        return
    
    page = int(callback_query.data.split("_")[2])
    
    user_id = callback_query.from_user.id
    user_data = db.get_user(user_id)
    language = user_data[1] if user_data else 'fa'
    
    await show_users_page(callback_query.message, page=page, language=language, edit_message=True)
    await callback_query.answer()

@router.callback_query(lambda c: c.data.startswith("view_user_"))
async def handle_view_user(callback_query: CallbackQuery):
    """مشاهده جزئیات یک کاربر"""
    if not is_admin(callback_query.from_user.id):
        return
    
    try:
        user_id = int(callback_query.data.split("_")[2])
        
        cursor = db.conn.cursor()
        cursor.execute("""
            SELECT user_id, language, full_name, email, phone, wallet_address, balance, registered_at 
            FROM users 
            WHERE user_id = ?
        """, (user_id,))
        
        user = cursor.fetchone()
        
        if user:
            user_id, language, full_name, email, phone, wallet, balance, reg_date = user
            
            cursor.execute("""
                SELECT COUNT(*), SUM(amount) 
                FROM investments 
                WHERE user_id = ? AND status = 'active'
            """, (user_id,))
            inv_count, inv_total = cursor.fetchone()
            inv_count = inv_count or 0
            inv_total = inv_total or 0
            
            details = (
                "👤 <b>جزئیات کامل کاربر</b>\n\n"
                f"🆔 <b>شناسه:</b> <code>{user_id}</code>\n"
                f"🌐 <b>زبان:</b> {language}\n"
                f"👤 <b>نام کامل:</b> {full_name or 'ثبت نشده'}\n"
                f"📧 <b>ایمیل:</b> {email or 'ثبت نشده'}\n"
                f"📱 <b>تلفن:</b> {phone or 'ثبت نشده'}\n"
                f"💰 <b>موجودی:</b> ${balance:.2f}\n"
                f"📅 <b>تاریخ ثبت‌نام:</b> {reg_date}\n\n"
            )
            
            if wallet and wallet.strip():
                details += (
                    f"🔐 <b>آدرس کیف پول (BEP20):</b>\n"
                    f"<code>{wallet}</code>\n\n"
                    f"📏 <b>طول آدرس:</b> {len(wallet)} کاراکتر\n\n"
                )
            else:
                details += "🔐 <b>کیف پول:</b> ❌ ثبت نشده\n\n"
            
            details += (
                f"💼 <b>سرمایه‌گذاری‌ها:</b>\n"
                f"   • تعداد فعال: {inv_count}\n"
                f"   • مجموع مبلغ: ${inv_total:.2f}\n\n"
                
                "<b>دستورات مدیریت:</b>\n"
                f"✏️ ویرایش کاربر: /edit_{user_id}\n"
                f"💰 افزودن موجودی: /addbalance_{user_id}\n"
                f"📊 مشاهده تراکنش‌ها: /transactions_{user_id}\n"
                f"⚠️ مسدود کردن: /ban_{user_id}"
            )
            
            await callback_query.message.edit_text(
                details, 
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 بازگشت به لیست", callback_data="back_to_users_list")]
                ])
            )
        else:
            await callback_query.answer("❌ کاربر یافت نشد.", show_alert=True)
            
    except Exception as e:
        await callback_query.answer(f"❌ خطا: {str(e)}", show_alert=True)
    
    await callback_query.answer()

@router.callback_query(F.data == "back_to_users_list")
async def back_to_users_list(callback_query: CallbackQuery):
    """بازگشت به لیست کاربران"""
    if not is_admin(callback_query.from_user.id):
        return
    
    user_id = callback_query.from_user.id
    user_data = db.get_user(user_id)
    language = user_data[1] if user_data else 'fa'
    
    await show_users_page(callback_query.message, page=0, language=language, edit_message=True)
    await callback_query.answer()