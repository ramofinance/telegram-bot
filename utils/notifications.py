import os
from datetime import datetime
from aiogram import Bot

async def notify_admins(bot: Bot, message: str):
    """ارسال اعلان به تمام ادمین‌ها"""
    admin_ids_str = os.getenv("ADMIN_IDS", "")
    if admin_ids_str:
        admin_ids = [int(id_str.strip()) for id_str in admin_ids_str.split(",") if id_str.strip()]
        
        for admin_id in admin_ids:
            try:
                await bot.send_message(admin_id, message, parse_mode="HTML")
            except Exception as e:
                print(f"❌ Failed to notify admin {admin_id}: {e}")

async def notify_new_user(bot: Bot, user_id: int, full_name: str, username: str, email: str):
    """اعلان ثبت‌نام کاربر جدید"""
    username_text = f"@{username}" if username else "No username"
    
    message = (
        "🆕 <b>کاربر جدید ثبت‌نام کرد!</b>\n\n"
        f"👤 <b>نام:</b> {full_name}\n"
        f"🆔 <b>شناسه:</b> <code>{user_id}</code>\n"
        f"📱 <b>یوزرنیم:</b> {username_text}\n"
        f"📧 <b>ایمیل:</b> {email}\n"
        f"📅 <b>زمان:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    
    await notify_admins(bot, message)

async def notify_new_investment(bot: Bot, user_id: int, full_name: str, amount: float, package: str):
    """اعلان سرمایه‌گذاری جدید"""
    message = (
        "💰 <b>سرمایه‌گذاری جدید!</b>\n\n"
        f"👤 <b>کاربر:</b> {full_name}\n"
        f"🆔 <b>شناسه:</b> <code>{user_id}</code>\n"
        f"💵 <b>مبلغ:</b> ${amount:,.2f}\n"
        f"📦 <b>بسته:</b> {package}\n"
        f"📅 <b>زمان:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    
    await notify_admins(bot, message)