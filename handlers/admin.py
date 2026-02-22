# handlers/admin.py
import os
from datetime import datetime
from aiogram import F, Router, Bot
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import Database

router = Router()
db = Database()

class BroadcastStates(StatesGroup):
    waiting_for_broadcast_message = State()

class AdminReplyStates(StatesGroup):
    waiting_for_reply = State()

class AdminStates(StatesGroup):
    waiting_for_user_search = State()
    viewing_user_details = State()

def is_admin(user_id: int) -> bool:
    """بررسی اینکه کاربر ادمین هست یا نه"""
    admin_ids_str = os.getenv("ADMIN_IDS", "")
    if admin_ids_str:
        admin_ids = [int(id_str.strip()) for id_str in admin_ids_str.split(",") if id_str.strip()]
        return user_id in admin_ids
    return False

def get_admin_keyboard(language='fa'):
    """منوی ادمین - با دکمه تعمیر رفرال"""
    if language == 'fa':
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="👥 مدیریت کاربران"), KeyboardButton(text="💰 سرمایه‌گذاری‌ها")],
                [KeyboardButton(text="📊 آمار کلی"), KeyboardButton(text="📢 اطلاع‌رسانی")],
                [KeyboardButton(text="🎫 تیکت‌ها"), KeyboardButton(text="🔍 جستجوی کاربر")],
                [KeyboardButton(text="🔧 تعمیر رفرال"), KeyboardButton(text="⚙️ تنظیمات سیستم")],
                [KeyboardButton(text="🔙 منوی اصلی")]
            ],
            resize_keyboard=True
        )
    elif language == 'ar':
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="👥 إدارة المستخدمين"), KeyboardButton(text="💰 الاستثمارات")],
                [KeyboardButton(text="📊 الإحصائيات"), KeyboardButton(text="📢 الإذاعة")],
                [KeyboardButton(text="🎫 التذاكر"), KeyboardButton(text="🔍 بحث المستخدم")],
                [KeyboardButton(text="🔧 إصلاح الإحالة"), KeyboardButton(text="⚙️ إعدادات النظام")],
                [KeyboardButton(text="🔙 القائمة الرئيسية")]
            ],
            resize_keyboard=True
        )
    else:
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="👥 User Management"), KeyboardButton(text="💰 Investments")],
                [KeyboardButton(text="📊 Statistics"), KeyboardButton(text="📢 Broadcast")],
                [KeyboardButton(text="🎫 Tickets"), KeyboardButton(text="🔍 Search User")],
                [KeyboardButton(text="🔧 Fix Referral"), KeyboardButton(text="⚙️ System Settings")],
                [KeyboardButton(text="🔙 Main Menu")]
            ],
            resize_keyboard=True
        )

@router.message(Command("admin"))
async def admin_panel(message: Message, state: FSMContext):
    """پنل ادمین"""
    if not is_admin(message.from_user.id):
        # تشخیص زبان کاربر
        user_id = message.from_user.id
        user_data = db.get_user(user_id)
        language = user_data[1] if user_data else 'en'
        
        if language == 'fa':
            await message.answer("⛔ دسترسی denied.")
        elif language == 'ar':
            await message.answer("⛔ تم رفض الوصول.")
        else:
            await message.answer("⛔ Access denied.")
        return
    
    await state.clear()
    
    # تشخیص زبان ادمین
    user_id = message.from_user.id
    user_data = db.get_user(user_id)
    language = user_data[1] if user_data else 'fa'
    
    if language == 'fa':
        await message.answer(
            "👑 **پنل مدیریت ادمین**\n\n"
            "لطفاً یک گزینه را انتخاب کنید:",
            reply_markup=get_admin_keyboard(language)
        )
    elif language == 'ar':
        await message.answer(
            "👑 **لوحة إدارة المسؤول**\n\n"
            "الرجاء اختيار خيار:",
            reply_markup=get_admin_keyboard(language)
        )
    else:
        await message.answer(
            "👑 **Admin Management Panel**\n\n"
            "Please choose an option:",
            reply_markup=get_admin_keyboard(language)
        )

@router.message(F.text.in_(["👥 مدیریت کاربران", "👥 User Management", "👥 إدارة المستخدمين"]))
async def admin_users_list(message: Message):
    """لیست کاربران"""
    if not is_admin(message.from_user.id):
        return
    
    # تشخیص زبان ادمین
    user_id = message.from_user.id
    user_data = db.get_user(user_id)
    language = user_data[1] if user_data else 'fa'
    
    # استفاده از تابع show_users_page از user_management.py
    from handlers.user_management import show_users_page
    await show_users_page(message, page=0, language=language, edit_message=False)

@router.message(F.text.in_(["💰 سرمایه‌گذاری‌ها", "💰 Investments", "💰 الاستثمارات"]))
async def admin_investments(message: Message):
    """لیست سرمایه‌گذاری‌ها"""
    if not is_admin(message.from_user.id):
        return
    
    # تشخیص زبان ادمین
    user_id = message.from_user.id
    user_data = db.get_user(user_id)
    language = user_data[1] if user_data else 'fa'
    
    cursor = db.conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM investments")
    total_investments = cursor.fetchone()[0] or 0
    
    cursor.execute("SELECT SUM(amount) FROM investments WHERE status = 'active'")
    total_active_amount = cursor.fetchone()[0] or 0
    
    cursor.execute("""
        SELECT i.amount, i.package, u.full_name, i.start_date
        FROM investments i
        JOIN users u ON i.user_id = u.user_id
        WHERE i.status = 'active'
        ORDER BY i.start_date DESC
        LIMIT 10
    """)
    recent_investments = cursor.fetchall()
    
    if language == 'fa':
        investments_list = ""
        for inv in recent_investments:
            amount, package, full_name, start_date = inv
            investments_list += f"• {full_name}: ${amount:,.2f} ({package}) - {start_date[:10]}\n"
        
        response = (
            f"💰 **آمار سرمایه‌گذاری‌ها**\n\n"
            f"📈 **کل سرمایه‌گذاری‌ها:** {total_investments}\n"
            f"💵 **کل مبلغ فعال:** ${total_active_amount:,.2f}\n\n"
            f"**آخرین سرمایه‌گذاری‌ها:**\n"
            f"{investments_list}"
        )
        
    elif language == 'ar':
        investments_list = ""
        for inv in recent_investments:
            amount, package, full_name, start_date = inv
            investments_list += f"• {full_name}: ${amount:,.2f} ({package}) - {start_date[:10]}\n"
        
        response = (
            f"💰 **إحصائيات الاستثمارات**\n\n"
            f"📈 **إجمالي الاستثمارات:** {total_investments}\n"
            f"💵 **إجمالي المبلغ النشط:** ${total_active_amount:,.2f}\n\n"
            f"**آخر الاستثمارات:**\n"
            f"{investments_list}"
        )
        
    else:
        investments_list = ""
        for inv in recent_investments:
            amount, package, full_name, start_date = inv
            investments_list += f"• {full_name}: ${amount:,.2f} ({package}) - {start_date[:10]}\n"
        
        response = (
            f"💰 **Investment Statistics**\n\n"
            f"📈 **Total Investments:** {total_investments}\n"
            f"💵 **Total Active Amount:** ${total_active_amount:,.2f}\n\n"
            f"**Recent Investments:**\n"
            f"{investments_list}"
        )
    
    await message.answer(response)

@router.message(F.text.in_(["📊 آمار کلی", "📊 Statistics", "📊 الإحصائيات"]))
async def admin_stats(message: Message):
    """آمار کلی"""
    if not is_admin(message.from_user.id):
        return
    
    # تشخیص زبان ادمین
    user_id = message.from_user.id
    user_data = db.get_user(user_id)
    language = user_data[1] if user_data else 'fa'
    
    cursor = db.conn.cursor()
    
    # آمار کاربران
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM users WHERE DATE(registered_at) = DATE('now')")
    today_users = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM users WHERE DATE(registered_at) >= DATE('now', '-7 days')")
    weekly_users = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM users WHERE wallet_address IS NOT NULL AND wallet_address != ''")
    users_with_wallet = cursor.fetchone()[0]
    
    # آمار سرمایه‌گذاری
    cursor.execute("SELECT COUNT(*) FROM investments")
    total_investments = cursor.fetchone()[0] or 0
    
    cursor.execute("SELECT SUM(amount) FROM investments WHERE status = 'active'")
    total_active_amount = cursor.fetchone()[0] or 0
    
    cursor.execute("SELECT SUM(amount) FROM investments WHERE DATE(start_date) = DATE('now')")
    today_investments = cursor.fetchone()[0] or 0
    
    # محاسبه سود ماهانه کل
    cursor.execute("""
        SELECT SUM(amount * monthly_profit_percent / 100) 
        FROM investments 
        WHERE status = 'active'
    """)
    monthly_profit = cursor.fetchone()[0] or 0
    
    # آمار مالی
    cursor.execute("SELECT SUM(balance) FROM users")
    total_balance = cursor.fetchone()[0] or 0
    
    # آمار تیکت‌ها
    cursor.execute("SELECT COUNT(*) FROM tickets WHERE status = 'open'")
    open_tickets = cursor.fetchone()[0] or 0
    
    cursor.execute("SELECT COUNT(*) FROM tickets WHERE status = 'answered'")
    answered_tickets = cursor.fetchone()[0] or 0
    
    cursor.execute("SELECT COUNT(*) FROM tickets")
    total_tickets = cursor.fetchone()[0] or 0
    
    if language == 'fa':
        stats_text = (
            "📈 **آمار کلی سیستم**\n\n"
            
            "👥 **آمار کاربران:**\n"
            f"   • کل کاربران: {total_users}\n"
            f"   • امروز: {today_users}\n"
            f"   • هفته گذشته: {weekly_users}\n"
            f"   • دارای کیف پول: {users_with_wallet}\n\n"
            
            "💰 **آمار مالی:**\n"
            f"   • مجموع موجودی‌ها: ${total_balance:,.2f}\n\n"
            
            "💼 **آمار سرمایه‌گذاری:**\n"
            f"   • تعداد کل: {total_investments}\n"
            f"   • مبلغ فعال: ${total_active_amount:,.2f}\n"
            f"   • امروز: ${today_investments:,.2f}\n"
            f"   • سود ماهانه: ${monthly_profit:,.2f}\n\n"
            
            "🎫 **آمار تیکت‌ها:**\n"
            f"   • کل تیکت‌ها: {total_tickets}\n"
            f"   • باز: {open_tickets}\n"
            f"   • پاسخ داده شده: {answered_tickets}\n\n"
            
            f"📅 **تاریخ:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
            f"🔄 **آخرین به‌روزرسانی:** {datetime.now().strftime('%H:%M:%S')}"
        )
    elif language == 'ar':
        stats_text = (
            "📈 **إحصائيات عامة للنظام**\n\n"
            
            "👥 **إحصائيات المستخدمين:**\n"
            f"   • إجمالي المستخدمين: {total_users}\n"
            f"   • اليوم: {today_users}\n"
            f"   • الأسبوع الماضي: {weekly_users}\n"
            f"   • لديهم محفظة: {users_with_wallet}\n\n"
            
            "💰 **الإحصائيات المالية:**\n"
            f"   • إجمالي الأرصدة: ${total_balance:,.2f}\n\n"
            
            "💼 **إحصائيات الاستثمار:**\n"
            f"   • الإجمالي: {total_investments}\n"
            f"   • المبلغ النشط: ${total_active_amount:,.2f}\n"
            f"   • اليوم: ${today_investments:,.2f}\n"
            f"   • الربح الشهري: ${monthly_profit:,.2f}\n\n"
            
            "🎫 **إحصائيات التذاكر:**\n"
            f"   • إجمالي التذاكر: {total_tickets}\n"
            f"   • المفتوحة: {open_tickets}\n"
            f"   • المجابة: {answered_tickets}\n\n"
            
            f"📅 **التاريخ:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
            f"🔄 **آخر تحديث:** {datetime.now().strftime('%H:%M:%S')}"
        )
    else:
        stats_text = (
            "📈 **System Statistics**\n\n"
            
            "👥 **User Statistics:**\n"
            f"   • Total Users: {total_users}\n"
            f"   • Today: {today_users}\n"
            f"   • Last 7 days: {weekly_users}\n"
            f"   • With Wallet: {users_with_wallet}\n\n"
            
            "💰 **Financial Statistics:**\n"
            f"   • Total Balance: ${total_balance:,.2f}\n\n"
            
            "💼 **Investment Statistics:**\n"
            f"   • Total: {total_investments}\n"
            f"   • Active Amount: ${total_active_amount:,.2f}\n"
            f"   • Today: ${today_investments:,.2f}\n"
            f"   • Monthly Profit: ${monthly_profit:,.2f}\n\n"
            
            "🎫 **Ticket Statistics:**\n"
            f"   • Total Tickets: {total_tickets}\n"
            f"   • Open: {open_tickets}\n"
            f"   • Answered: {answered_tickets}\n\n"
            
            f"📅 **Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
            f"🔄 **Last Update:** {datetime.now().strftime('%H:%M:%S')}"
        )
    
    await message.answer(stats_text)

@router.message(F.text.in_(["📢 اطلاع‌رسانی", "📢 Broadcast", "📢 الإذاعة"]))
async def broadcast_start(message: Message, state: FSMContext):
    """شروع ارسال اطلاعیه به همه"""
    if not is_admin(message.from_user.id):
        return
    
    # تشخیص زبان ادمین
    user_id = message.from_user.id
    user_data = db.get_user(user_id)
    language = user_data[1] if user_data else 'fa'
    
    if language == 'fa':
        await message.answer(
            "📢 **ارسال اطلاعیه به همه کاربران**\n\n"
            "لطفاً پیام خود را ارسال کنید:"
        )
    elif language == 'ar':
        await message.answer(
            "📢 **بث رسالة إلى جميع المستخدمين**\n\n"
            "الرجاء إرسال رسالتك:"
        )
    else:
        await message.answer(
            "📢 **Broadcast to all users**\n\n"
            "Please send your message:"
        )
    
    await state.set_state(BroadcastStates.waiting_for_broadcast_message)

@router.message(BroadcastStates.waiting_for_broadcast_message)
async def broadcast_send(message: Message, state: FSMContext, bot: Bot):
    """ارسال اطلاعیه به همه کاربران"""
    if not is_admin(message.from_user.id):
        return
    
    cursor = db.conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    all_users = cursor.fetchall()
    
    total_users = len(all_users)
    successful = 0
    failed = 0
    
    # تشخیص زبان ادمین
    user_id = message.from_user.id
    user_data = db.get_user(user_id)
    language = user_data[1] if user_data else 'fa'
    
    if language == 'fa':
        await message.answer(f"📤 ارسال اطلاعیه به {total_users} کاربر...")
    elif language == 'ar':
        await message.answer(f"📤 جاري إرسال الرسالة إلى {total_users} مستخدم...")
    else:
        await message.answer(f"📤 Sending broadcast to {total_users} users...")
    
    for user in all_users:
        user_id = user[0]
        try:
            await message.copy_to(user_id)
            successful += 1
        except Exception:
            failed += 1
    
    await state.clear()
    
    if language == 'fa':
        await message.answer(
            f"✅ **ارسال اطلاعیه تکمیل شد!**\n\n"
            f"📤 ارسال شده: {successful}\n"
            f"❌ ناموفق: {failed}\n"
            f"👥 کل کاربران: {total_users}",
            reply_markup=get_admin_keyboard(language)
        )
    elif language == 'ar':
        await message.answer(
            f"✅ **اكتمل البث!**\n\n"
            f"📤 تم الإرسال: {successful}\n"
            f"❌ فشل: {failed}\n"
            f"👥 إجمالي المستخدمين: {total_users}",
            reply_markup=get_admin_keyboard(language)
        )
    else:
        await message.answer(
            f"✅ **Broadcast completed!**\n\n"
            f"📤 Sent: {successful}\n"
            f"❌ Failed: {failed}\n"
            f"👥 Total Users: {total_users}",
            reply_markup=get_admin_keyboard(language)
        )

@router.message(F.text.in_(["🎫 تیکت‌ها", "🎫 Tickets", "🎫 التذاكر"]))
async def admin_tickets_menu(message: Message):
    """منوی تیکت‌های ادمین"""
    if not is_admin(message.from_user.id):
        return
    
    # تشخیص زبان ادمین
    user_id = message.from_user.id
    user_data = db.get_user(user_id)
    language = user_data[1] if user_data else 'fa'
    
    # دریافت تیکت‌های باز
    open_tickets = db.get_open_tickets()
    
    if language == 'fa':
        if open_tickets:
            tickets_text = "🎫 **تیکت‌های باز**\n\n"
            for ticket in open_tickets:
                ticket_id, subject, created_at, full_name, user_id = ticket
                tickets_text += (
                    f"🆔 #{ticket_id}\n"
                    f"📌 {subject[:30]}...\n"
                    f"👤 {full_name or 'بدون نام'}\n"
                    f"📅 {created_at[:10]}\n"
                    f"💬 /reply_{ticket_id}\n"
                    f"────────────────\n"
                )
            
            tickets_text += f"\n📊 **تعداد: {len(open_tickets)} تیکت باز**"
        else:
            tickets_text = "✅ **هیچ تیکت بازی وجود ندارد.**"
        
    elif language == 'ar':
        if open_tickets:
            tickets_text = "🎫 **التذاكر المفتوحة**\n\n"
            for ticket in open_tickets:
                ticket_id, subject, created_at, full_name, user_id = ticket
                tickets_text += (
                    f"🆔 #{ticket_id}\n"
                    f"📌 {subject[:30]}...\n"
                    f"👤 {full_name or 'بدون اسم'}\n"
                    f"📅 {created_at[:10]}\n"
                    f"💬 /reply_{ticket_id}\n"
                    f"────────────────\n"
                )
            
            tickets_text += f"\n📊 **العدد: {len(open_tickets)} تذكرة مفتوحة**"
        else:
            tickets_text = "✅ **لا توجد تذاكر مفتوحة.**"
        
    else:
        if open_tickets:
            tickets_text = "🎫 **Open Tickets**\n\n"
            for ticket in open_tickets:
                ticket_id, subject, created_at, full_name, user_id = ticket
                tickets_text += (
                    f"🆔 #{ticket_id}\n"
                    f"📌 {subject[:30]}...\n"
                    f"👤 {full_name or 'No name'}\n"
                    f"📅 {created_at[:10]}\n"
                    f"💬 /reply_{ticket_id}\n"
                    f"────────────────\n"
                )
            
            tickets_text += f"\n📊 **Count: {len(open_tickets)} open tickets**"
        else:
            tickets_text = "✅ **No open tickets.**"
    
    await message.answer(tickets_text)

@router.message(F.text.regexp(r'^/reply_\d+$'))
async def reply_to_ticket_start(message: Message, state: FSMContext):
    """شروع پاسخ به تیکت"""
    if not is_admin(message.from_user.id):
        return
    
    ticket_id = int(message.text.split('_')[1])
    
    ticket = db.get_ticket(ticket_id)
    
    if not ticket:
        # تشخیص زبان ادمین
        user_id = message.from_user.id
        user_data = db.get_user(user_id)
        language = user_data[1] if user_data else 'fa'
        
        if language == 'fa':
            await message.answer("❌ تیکت یافت نشد.")
        elif language == 'ar':
            await message.answer("❌ لم يتم العثور على التذكرة.")
        else:
            await message.answer("❌ Ticket not found.")
        return
    
    ticket_id, user_id, subject, ticket_message, status, created_at, admin_response, responded_at, full_name, email = ticket
    
    await state.update_data(ticket_id=ticket_id, user_id=user_id)
    
    # تشخیص زبان ادمین
    admin_data = db.get_user(message.from_user.id)
    language = admin_data[1] if admin_data else 'fa'
    
    if language == 'fa':
        await message.answer(
            f"🎫 **پاسخ به تیکت #{ticket_id}**\n\n"
            f"👤 **کاربر:** {full_name}\n"
            f"🆔 **شناسه:** {user_id}\n"
            f"📌 **موضوع:** {subject}\n"
            f"📝 **پیام کاربر:**\n{ticket_message}\n\n"
            f"📤 **لطفاً پاسخ خود را ارسال کنید:**"
        )
    elif language == 'ar':
        await message.answer(
            f"🎫 **الرد على التذكرة #{ticket_id}**\n\n"
            f"👤 **المستخدم:** {full_name}\n"
            f"🆔 **المعرف:** {user_id}\n"
            f"📌 **الموضوع:** {subject}\n"
            f"📝 **رسالة المستخدم:**\n{ticket_message}\n\n"
            f"📤 **الرجاء إرسال ردك:**"
        )
    else:
        await message.answer(
            f"🎫 **Reply to Ticket #{ticket_id}**\n\n"
            f"👤 **User:** {full_name}\n"
            f"🆔 **ID:** {user_id}\n"
            f"📌 **Subject:** {subject}\n"
            f"📝 **User Message:**\n{ticket_message}\n\n"
            f"📤 **Please send your reply:**"
        )
    
    await state.set_state(AdminReplyStates.waiting_for_reply)

@router.message(AdminReplyStates.waiting_for_reply)
async def process_admin_reply(message: Message, state: FSMContext, bot: Bot):
    """پردازش پاسخ ادمین"""
    if not is_admin(message.from_user.id):
        return
    
    data = await state.get_data()
    ticket_id = data.get('ticket_id')
    user_id = data.get('user_id')
    
    # به‌روزرسانی تیکت با پاسخ ادمین
    success = db.update_ticket_response(ticket_id, message.text)
    
    if success:
        # ارسال پاسخ به کاربر
        try:
            user_lang = db.get_user_language(user_id)
            
            if user_lang == 'fa':
                await bot.send_message(
                    user_id,
                    f"📨 **پاسخ به تیکت #{ticket_id}**\n\n"
                    f"👤 **پشتیبانی RAMO FINANCE**\n"
                    f"📝 **پاسخ:**\n{message.text}\n\n"
                    f"✅ برای مشاهده تیکت کامل: /viewticket_{ticket_id}"
                )
            elif user_lang == 'ar':
                await bot.send_message(
                    user_id,
                    f"📨 **الرد على التذكرة #{ticket_id}**\n\n"
                    f"👤 **دعم RAMO FINANCE**\n"
                    f"📝 **الرد:**\n{message.text}\n\n"
                    f"✅ لعرض التذكرة كاملة: /viewticket_{ticket_id}"
                )
            else:
                await bot.send_message(
                    user_id,
                    f"📨 **Response to Ticket #{ticket_id}**\n\n"
                    f"👤 **RAMO FINANCE Support**\n"
                    f"📝 **Reply:**\n{message.text}\n\n"
                    f"✅ To view full ticket: /viewticket_{ticket_id}"
                )
        except Exception as e:
            print(f"❌ Failed to send reply to user {user_id}: {e}")
        
        # تشخیص زبان ادمین برای پیام موفقیت
        admin_data = db.get_user(message.from_user.id)
        admin_lang = admin_data[1] if admin_data else 'fa'
        
        if admin_lang == 'fa':
            await message.answer(f"✅ پاسخ به تیکت #{ticket_id} ارسال شد.")
        elif admin_lang == 'ar':
            await message.answer(f"✅ تم إرسال الرد على التذكرة #{ticket_id}.")
        else:
            await message.answer(f"✅ Response to ticket #{ticket_id} sent.")
    else:
        admin_data = db.get_user(message.from_user.id)
        admin_lang = admin_data[1] if admin_data else 'fa'
        
        if admin_lang == 'fa':
            await message.answer("❌ خطا در ارسال پاسخ.")
        elif admin_lang == 'ar':
            await message.answer("❌ خطأ في إرسال الرد.")
        else:
            await message.answer("❌ Error sending reply.")
    
    await state.clear()

@router.message(F.text.in_(["🔍 جستجوی کاربر", "🔍 Search User", "🔍 بحث المستخدم"]))
async def search_user_menu(message: Message, state: FSMContext):
    """منوی جستجوی کاربر"""
    if not is_admin(message.from_user.id):
        return
    
    # تشخیص زبان ادمین
    user_id = message.from_user.id
    user_data = db.get_user(user_id)
    language = user_data[1] if user_data else 'fa'
    
    if language == 'fa':
        await message.answer(
            "🔍 **جستجوی کاربر**\n\n"
            "می‌توانید از روش‌های زیر جستجو کنید:\n"
            "1. با شناسه کاربر: /user_123456789\n"
            "2. با بخشی از نام: /find_نام\n"
            "3. با ایمیل: /find_email@example.com\n\n"
            "لطفاً شناسه یا نام کاربر را وارد کنید:"
        )
    elif language == 'ar':
        await message.answer(
            "🔍 **بحث المستخدم**\n\n"
            "يمكنك البحث بالطرق التالية:\n"
            "1. بمعرف المستخدم: /user_123456789\n"
            "2. بجزء من الاسم: /find_الاسم\n"
            "3. بالبريد الإلكتروني: /find_email@example.com\n\n"
            "الرجاء إدخال معرف أو اسم المستخدم:"
        )
    else:
        await message.answer(
            "🔍 **Search User**\n\n"
            "You can search by:\n"
            "1. User ID: /user_123456789\n"
            "2. Part of name: /find_name\n"
            "3. Email: /find_email@example.com\n\n"
            "Please enter user ID or name:"
        )
    
    await state.set_state(AdminStates.waiting_for_user_search)

@router.message(AdminStates.waiting_for_user_search)
async def search_user_execute(message: Message, state: FSMContext):
    """اجرای جستجوی کاربر"""
    if not is_admin(message.from_user.id):
        return
    
    search_term = message.text.strip()
    
    cursor = db.conn.cursor()
    
    # اگر عدد باشد (شناسه کاربر)
    if search_term.isdigit():
        cursor.execute("""
            SELECT user_id, full_name, email, registered_at 
            FROM users 
            WHERE user_id = ?
        """, (int(search_term),))
    else:
        # جستجو در نام یا ایمیل
        cursor.execute("""
            SELECT user_id, full_name, email, registered_at 
            FROM users 
            WHERE full_name LIKE ? OR email LIKE ?
            LIMIT 20
        """, (f'%{search_term}%', f'%{search_term}%'))
    
    results = cursor.fetchall()
    
    # تشخیص زبان ادمین
    user_id = message.from_user.id
    user_data = db.get_user(user_id)
    language = user_data[1] if user_data else 'fa'
    
    if results:
        if language == 'fa':
            result_text = f"🔍 **نتایج جستجو برای '{search_term}'**\n\n"
        elif language == 'ar':
            result_text = f"🔍 **نتائج البحث عن '{search_term}'**\n\n"
        else:
            result_text = f"🔍 **Search results for '{search_term}'**\n\n"
        
        for user in results:
            user_id, full_name, email, reg_date = user
            
            if language == 'fa':
                result_text += f"• {full_name or 'بدون نام'}\n"
                result_text += f"  🆔: {user_id}\n"
                result_text += f"  📧: {email or 'ندارد'}\n"
                result_text += f"  📅: {reg_date[:10]}\n"
                result_text += f"  👁️: /user_{user_id}\n\n"
            elif language == 'ar':
                result_text += f"• {full_name or 'بدون اسم'}\n"
                result_text += f"  🆔: {user_id}\n"
                result_text += f"  📧: {email or 'لا يوجد'}\n"
                result_text += f"  📅: {reg_date[:10]}\n"
                result_text += f"  👁️: /user_{user_id}\n\n"
            else:
                result_text += f"• {full_name or 'No name'}\n"
                result_text += f"  🆔: {user_id}\n"
                result_text += f"  📧: {email or 'None'}\n"
                result_text += f"  📅: {reg_date[:10]}\n"
                result_text += f"  👁️: /user_{user_id}\n\n"
        
        await message.answer(result_text)
    else:
        if language == 'fa':
            await message.answer("❌ هیچ کاربری یافت نشد.")
        elif language == 'ar':
            await message.answer("❌ لم يتم العثور على أي مستخدمين.")
        else:
            await message.answer("❌ No users found.")
    
    await state.clear()

# ========== دکمه تعمیر رفرال ==========
@router.message(F.text.in_(["🔧 تعمیر رفرال", "🔧 Fix Referral", "🔧 إصلاح الإحالة"]))
async def quick_fix_referral(message: Message):
    """تعمیر سریع دیتابیس رفرال"""
    if not is_admin(message.from_user.id):
        return
    
    status_msg = await message.answer("🔄 در حال تعمیر دیتابیس رفرال...")
    
    try:
        cursor = db.conn.cursor()
        
        # 1. بررسی و اضافه کردن ستون referral_code
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN referral_code TEXT")
            await message.answer("✅ ستون referral_code اضافه شد")
        except:
            await message.answer("ℹ️ ستون referral_code از قبل وجود دارد")
        
        # 2. بررسی و اضافه کردن ستون referred_by
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN referred_by INTEGER")
            await message.answer("✅ ستون referred_by اضافه شد")
        except:
            pass
        
        # 3. ساخت کد رفرال برای همه کاربران
        cursor.execute("SELECT user_id FROM users")
        users = cursor.fetchall()
        
        import random
        import string
        
        count = 0
        for user in users:
            user_id = user[0]
            # چک کن کد نداره
            cursor.execute("SELECT referral_code FROM users WHERE user_id = ?", (user_id,))
            existing = cursor.fetchone()
            
            if not existing or not existing[0]:
                random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
                code = f"RAMO{user_id}{random_part}"
                cursor.execute("UPDATE users SET referral_code = ? WHERE user_id = ?", (code, user_id))
                count += 1
        
        db.conn.commit()
        
        await message.answer(f"✅ کد رفرال برای {count} کاربر جدید ساخته شد!\n"
                            f"👥 کل کاربران: {len(users)}")
        
        # 4. ساخت جدول referrals اگر نیست
        try:
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
            db.conn.commit()
            await message.answer("✅ جدول referrals بررسی/ساخته شد")
        except Exception as e:
            await message.answer(f"⚠️ خطا در ساخت جدول: {e}")
        
        # 5. نمایش آمار نهایی
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM users WHERE referral_code IS NOT NULL")
        users_with_code = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM referrals")
        total_refs = cursor.fetchone()[0]
        
        await message.answer(
            f"📊 **آمار نهایی:**\n"
            f"👥 کل کاربران: {total_users}\n"
            f"🔗 کاربران دارای کد: {users_with_code}\n"
            f"🔄 تعداد رفرال‌های ثبت شده: {total_refs}"
        )
        
    except Exception as e:
        await message.answer(f"❌ خطا: {str(e)}")

# ========== دستورات اضطراری ==========
@router.message(Command("emergency_fix"))
async def emergency_fix(message: Message):
    """دستور اضطراری برای تعمیر"""
    if not is_admin(message.from_user.id):
        return
    
    try:
        # اجرای مستقیم دستورات SQL
        cursor = db.conn.cursor()
        
        # 1. اضافه کردن ستون
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN referral_code TEXT")
            await message.answer("✅ ستون referral_code اضافه شد")
        except:
            await message.answer("ℹ️ ستون referral_code از قبل وجود دارد")
        
        # 2. کد رفرال برای همه
        cursor.execute("SELECT user_id FROM users")
        users = cursor.fetchall()
        
        import random
        import string
        
        count = 0
        for user in users:
            user_id = user[0]
            cursor.execute("SELECT referral_code FROM users WHERE user_id = ?", (user_id,))
            existing = cursor.fetchone()
            
            if not existing or not existing[0]:
                random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
                code = f"RAMO{user_id}{random_part}"
                cursor.execute("UPDATE users SET referral_code = ? WHERE user_id = ?", (code, user_id))
                count += 1
        
        db.conn.commit()
        await message.answer(f"✅ تعمیر اضطراری انجام شد! {count} کاربر آپدیت شدند.")
        
    except Exception as e:
        await message.answer(f"❌ خطا: {str(e)}")

# ========== ادامه فایل ==========

@router.message(F.text.in_(["⚙️ تنظیمات سیستم", "⚙️ System Settings", "⚙️ إعدادات النظام"]))
async def system_settings(message: Message):
    """تنظیمات سیستم"""
    if not is_admin(message.from_user.id):
        return
    
    # تشخیص زبان ادمین
    user_id = message.from_user.id
    user_data = db.get_user(user_id)
    language = user_data[1] if user_data else 'fa'
    
    if language == 'fa':
        await message.answer(
            "⚙️ **تنظیمات سیستم**\n\n"
            "🔸 **دستورات مدیریت دیتابیس:**\n"
            "• /dbinfo - اطلاعات دیتابیس\n"
            "• /checkwallets - بررسی کیف پول‌ها\n"
            "• /resetdb - ریست کامل دیتابیس\n\n"
            "🔸 **دستورات تیکت:**\n"
            "• /reply_123 - پاسخ به تیکت\n"
            "• /close_123 - بستن تیکت\n\n"
            "🔸 **سایر دستورات:**\n"
            "• /myid - دریافت شناسه کاربری\n"
            "• /list_users - لیست تمام کاربران\n"
            "• /admin - بازگشت به منوی ادمین\n"
            "• /start - بازگشت به منوی اصلی"
        )
    elif language == 'ar':
        await message.answer(
            "⚙️ **إعدادات النظام**\n\n"
            "🔸 **أوامر إدارة قاعدة البيانات:**\n"
            "• /dbinfo - معلومات قاعدة البيانات\n"
            "• /checkwallets - فحص المحافظ\n"
            "• /resetdb - إعادة تعيين قاعدة البيانات\n\n"
            "🔸 **أوامر التذاكر:**\n"
            "• /reply_123 - الرد على التذكرة\n"
            "• /close_123 - إغلاق التذكرة\n\n"
            "🔸 **أوامر أخرى:**\n"
            "• /myid - الحصول على معرف المستخدم\n"
            "• /list_users - قائمة جميع المستخدمين\n"
            "• /admin - العودة إلى قائمة المسؤول\n"
            "• /start - العودة إلى القائمة الرئيسية"
        )
    else:
        await message.answer(
            "⚙️ **System Settings**\n\n"
            "🔸 **Database Management Commands:**\n"
            "• /dbinfo - Database information\n"
            "• /checkwallets - Check user wallets\n"
            "• /resetdb - Reset entire database\n\n"
            "🔸 **Ticket Commands:**\n"
            "• /reply_123 - Reply to ticket\n"
            "• /close_123 - Close ticket\n\n"
            "🔸 **Other Commands:**\n"
            "• /myid - Get user ID\n"
            "• /list_users - List all users\n"
            "• /admin - Back to admin menu\n"
            "• /start - Back to main menu"
        )

@router.message(F.text.in_(["🔙 منوی اصلی", "🔙 Main Menu", "🔙 القائمة الرئيسية"]))
async def back_to_main_menu(message: Message, state: FSMContext):
    """بازگشت به منوی اصلی"""
    user_id = message.from_user.id
    language = db.get_user_language(user_id)
    
    await state.clear()
    from keyboards.main_menu import get_main_menu_keyboard
    
    if language == 'fa':
        await message.answer(
            "🔙 بازگشت به منوی اصلی",
            reply_markup=get_main_menu_keyboard(language)
        )
    elif language == 'ar':
        await message.answer(
            "🔙 العودة إلى القائمة الرئيسية",
            reply_markup=get_main_menu_keyboard(language)
        )
    else:
        await message.answer(
            "🔙 Back to main menu",
            reply_markup=get_main_menu_keyboard(language)
        )

@router.message(F.text.regexp(r'^/close_\d+$'))
async def close_ticket_command(message: Message):
    """بستن تیکت"""
    if not is_admin(message.from_user.id):
        return
    
    ticket_id = int(message.text.split('_')[1])
    
    success = db.close_ticket(ticket_id)
    
    # تشخیص زبان ادمین
    user_id = message.from_user.id
    user_data = db.get_user(user_id)
    language = user_data[1] if user_data else 'fa'
    
    if success:
        if language == 'fa':
            await message.answer(f"✅ تیکت #{ticket_id} بسته شد.")
        elif language == 'ar':
            await message.answer(f"✅ تم إغلاق التذكرة #{ticket_id}.")
        else:
            await message.answer(f"✅ Ticket #{ticket_id} closed.")
    else:
        if language == 'fa':
            await message.answer("❌ خطا در بستن تیکت.")
        elif language == 'ar':
            await message.answer("❌ خطأ في إغلاق التذكرة.")
        else:
            await message.answer("❌ Error closing ticket.")

@router.message(F.text.regexp(r'^/tickets_\d+$'))
async def view_user_tickets(message: Message):
    """مشاهده تیکت‌های یک کاربر"""
    if not is_admin(message.from_user.id):
        return
    
    user_id = int(message.text.split('_')[1])
    
    cursor = db.conn.cursor()
    cursor.execute("""
        SELECT ticket_id, subject, status, created_at, admin_response
        FROM tickets 
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT 10
    """, (user_id,))
    
    tickets = cursor.fetchall()
    
    cursor.execute("SELECT full_name FROM users WHERE user_id = ?", (user_id,))
    user_data = cursor.fetchone()
    user_name = user_data[0] if user_data else "Unknown"
    
    # تشخیص زبان ادمین
    admin_id = message.from_user.id
    admin_data = db.get_user(admin_id)
    language = admin_data[1] if admin_data else 'fa'
    
    if tickets:
        if language == 'fa':
            result_text = f"🎫 **تیکت‌های کاربر: {user_name}**\n\n"
        elif language == 'ar':
            result_text = f"🎫 **تذاكر المستخدم: {user_name}**\n\n"
        else:
            result_text = f"🎫 **Tickets of user: {user_name}**\n\n"
        
        for ticket in tickets:
            ticket_id, subject, status, created_at, admin_response = ticket
            
            if language == 'fa':
                status_text = {
                    'open': '🔴 باز',
                    'answered': '🟢 پاسخ داده شده',
                    'closed': '⚫ بسته'
                }.get(status, status)
            elif language == 'ar':
                status_text = {
                    'open': '🔴 مفتوحة',
                    'answered': '🟢 مجابة',
                    'closed': '⚫ مغلقة'
                }.get(status, status)
            else:
                status_text = {
                    'open': '🔴 Open',
                    'answered': '🟢 Answered',
                    'closed': '⚫ Closed'
                }.get(status, status)
            
            result_text += f"🆔 **تیکت #{ticket_id}**\n" if language == 'fa' else f"🆔 **Ticket #{ticket_id}**\n"
            result_text += f"📌 موضوع: {subject}\n" if language == 'fa' else f"📌 Subject: {subject}\n"
            result_text += f"📊 وضعیت: {status_text}\n" if language == 'fa' else f"📊 Status: {status_text}\n"
            result_text += f"📅 تاریخ: {created_at[:10]}\n" if language == 'fa' else f"📅 Date: {created_at[:10]}\n"
            
            if admin_response:
                if language == 'fa':
                    result_text += f"📨 پاسخ داده شده\n"
                elif language == 'ar':
                    result_text += f"📨 تم الرد\n"
                else:
                    result_text += f"📨 Responded\n"
            
            result_text += f"💬 /reply_{ticket_id}\n"
            result_text += "─" * 20 + "\n\n"
        
        if language == 'fa':
            result_text += f"📊 **مجموع: {len(tickets)} تیکت**"
        elif language == 'ar':
            result_text += f"📊 **الإجمالي: {len(tickets)} تذكرة**"
        else:
            result_text += f"📊 **Total: {len(tickets)} tickets**"
    else:
        if language == 'fa':
            result_text = f"📭 کاربر **{user_name}** هیچ تیکتی ندارد."
        elif language == 'ar':
            result_text = f"📭 المستخدم **{user_name}** ليس لديه أي تذاكر."
        else:
            result_text = f"📭 User **{user_name}** has no tickets."
    
    await message.answer(result_text)

@router.message(Command("opentickets"))
async def open_tickets_command(message: Message):
    """دستور مشاهده تیکت‌های باز"""
    if not is_admin(message.from_user.id):
        return
    
    open_tickets = db.get_open_tickets()
    
    # تشخیص زبان ادمین
    user_id = message.from_user.id
    user_data = db.get_user(user_id)
    language = user_data[1] if user_data else 'fa'
    
    if open_tickets:
        if language == 'fa':
            tickets_text = "🎫 **تیکت‌های باز**\n\n"
        elif language == 'ar':
            tickets_text = "🎫 **التذاكر المفتوحة**\n\n"
        else:
            tickets_text = "🎫 **Open Tickets**\n\n"
        
        for ticket in open_tickets:
            ticket_id, subject, created_at, full_name, user_id = ticket
            
            # محاسبه زمان گذشته از ایجاد تیکت
            from datetime import datetime
            created_dt = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S')
            now_dt = datetime.now()
            diff = now_dt - created_dt
            
            hours = diff.seconds // 3600
            minutes = (diff.seconds % 3600) // 60
            
            if language == 'fa':
                tickets_text += (
                    f"🆔 **#{ticket_id}**\n"
                    f"📌 {subject[:40]}...\n"
                    f"👤 {full_name or 'بدون نام'}\n"
                    f"🆔 کاربر: {user_id}\n"
                    f"⏰ زمان گذشته: {hours}ساعت {minutes}دقیقه\n"
                    f"💬 /reply_{ticket_id} | 🔒 /close_{ticket_id}\n"
                    f"────────────────\n"
                )
            elif language == 'ar':
                tickets_text += (
                    f"🆔 **#{ticket_id}**\n"
                    f"📌 {subject[:40]}...\n"
                    f"👤 {full_name or 'بدون اسم'}\n"
                    f"🆔 المستخدم: {user_id}\n"
                    f"⏰ الوقت المنقضي: {hours}ساعة {minutes}دقيقة\n"
                    f"💬 /reply_{ticket_id} | 🔒 /close_{ticket_id}\n"
                    f"────────────────\n"
                )
            else:
                tickets_text += (
                    f"🆔 **#{ticket_id}**\n"
                    f"📌 {subject[:40]}...\n"
                    f"👤 {full_name or 'No name'}\n"
                    f"🆔 User: {user_id}\n"
                    f"⏰ Time passed: {hours}h {minutes}m\n"
                    f"💬 /reply_{ticket_id} | 🔒 /close_{ticket_id}\n"
                    f"────────────────\n"
                )
        
        if language == 'fa':
            tickets_text += f"\n📊 **تعداد: {len(open_tickets)} تیکت باز**"
        elif language == 'ar':
            tickets_text += f"\n📊 **العدد: {len(open_tickets)} تذكرة مفتوحة**"
        else:
            tickets_text += f"\n📊 **Count: {len(open_tickets)} open tickets**"
        
        await message.answer(tickets_text)
    else:
        if language == 'fa':
            await message.answer("✅ **هیچ تیکت بازی وجود ندارد.**")
        elif language == 'ar':
            await message.answer("✅ **لا توجد تذاكر مفتوحة.**")
        else:
            await message.answer("✅ **No open tickets.**")

@router.message(F.text.regexp(r'^/confirm_invest_\d+$'))
async def confirm_investment(message: Message, bot: Bot):
    """تایید سرمایه‌گذاری توسط ادمین"""
    if not is_admin(message.from_user.id):
        return
    
    try:
        investment_id = int(message.text.split('_')[2])
        
        cursor = db.conn.cursor()
        cursor.execute('''
            UPDATE investments 
            SET status = 'active', start_date = CURRENT_TIMESTAMP
            WHERE investment_id = ?
        ''', (investment_id,))
        
        # دریافت اطلاعات سرمایه‌گذاری
        cursor.execute('''
            SELECT i.user_id, i.amount, i.monthly_profit_percent, u.full_name, u.wallet_address, u.language
            FROM investments i
            JOIN users u ON i.user_id = u.user_id
            WHERE i.investment_id = ?
        ''', (investment_id,))
        
        invest_data = cursor.fetchone()
        
        if invest_data:
            user_id, amount, profit_percent, full_name, user_wallet, user_lang = invest_data
            db.conn.commit()
            
            # محاسبه سود ماهانه
            monthly_profit = (amount * profit_percent) / 100
            
            # ارسال پیام به کاربر بر اساس زبان
            if user_lang == 'fa':
                user_message = (
                    f"✅ **سرمایه‌گذاری شما تایید شد!**\n\n"
                    f"🎯 **شناسه سرمایه‌گذاری:** #{investment_id}\n"
                    f"💵 **مبلغ:** ${amount:,.2f}\n"
                    f"📈 **نرخ سود:** {profit_percent}% ماهانه\n"
                    f"💰 **سود ماهانه:** ${monthly_profit:,.2f}\n"
                    f"📅 **تاریخ شروع:** {datetime.now().strftime('%Y-%m-%d')}\n\n"
                    f"سود ماهانه شما از فردا محاسبه می‌شود و هر ماه به کیف پول شما واریز خواهد شد.\n\n"
                    f"🔐 **کیف پول شما:** {user_wallet[:10]}...\n\n"
                    f"📞 برای سوالات با پشتیبانی تماس بگیرید."
                )
            elif user_lang == 'ar':
                user_message = (
                    f"✅ **تم تأكيد استثمارك!**\n\n"
                    f"🎯 **معرف الاستثمار:** #{investment_id}\n"
                    f"💵 **المبلغ:** ${amount:,.2f}\n"
                    f"📈 **معدل الربح:** {profit_percent}% شهرياً\n"
                    f"💰 **الربح الشهري:** ${monthly_profit:,.2f}\n"
                    f"📅 **تاريخ البدء:** {datetime.now().strftime('%Y-%m-%d')}\n\n"
                    f"سيبدأ حساب ربحك الشهري من الغد وسيتم إرساله إلى محفظتك كل شهر.\n\n"
                    f"🔐 **محفظتك:** {user_wallet[:10]}...\n\n"
                    f"📞 اتصل بالدعم الفني لأي استفسارات."
                )
            else:
                user_message = (
                    f"✅ **Your investment has been confirmed!**\n\n"
                    f"🎯 **Investment ID:** #{investment_id}\n"
                    f"💵 **Amount:** ${amount:,.2f}\n"
                    f"📈 **Profit Rate:** {profit_percent}% monthly\n"
                    f"💰 **Monthly Profit:** ${monthly_profit:,.2f}\n"
                    f"📅 **Start Date:** {datetime.now().strftime('%Y-%m-%d')}\n\n"
                    f"Your monthly profit calculation starts tomorrow and will be sent to your wallet every month.\n\n"
                    f"🔐 **Your Wallet:** {user_wallet[:10]}...\n\n"
                    f"📞 Contact support for any questions."
                )
            
            await bot.send_message(user_id, user_message)
            
            # پیام به ادمین
            admin_lang = db.get_user_language(message.from_user.id)
            if admin_lang == 'fa':
                await message.answer(f"✅ سرمایه‌گذاری #{investment_id} تایید شد و به کاربر اطلاع داده شد.")
            elif admin_lang == 'ar':
                await message.answer(f"✅ تم تأكيد الاستثمار #{investment_id} وتم إعلام المستخدم.")
            else:
                await message.answer(f"✅ Investment #{investment_id} confirmed and user notified.")
        else:
            admin_lang = db.get_user_language(message.from_user.id)
            if admin_lang == 'fa':
                await message.answer("❌ سرمایه‌گذاری یافت نشد.")
            elif admin_lang == 'ar':
                await message.answer("❌ لم يتم العثور على الاستثمار.")
            else:
                await message.answer("❌ Investment not found.")
            
    except Exception as e:
        await message.answer(f"❌ خطا: {str(e)}")

@router.message(F.text.regexp(r'^/reject_invest_\d+$'))
async def reject_investment(message: Message, bot: Bot):
    """رد سرمایه‌گذاری توسط ادمین"""
    if not is_admin(message.from_user.id):
        return
    
    try:
        investment_id = int(message.text.split('_')[2])
        
        cursor = db.conn.cursor()
        cursor.execute('''
            UPDATE investments 
            SET status = 'rejected'
            WHERE investment_id = ?
        ''', (investment_id,))
        
        # دریافت اطلاعات سرمایه‌گذاری
        cursor.execute('''
            SELECT i.user_id, i.amount, u.full_name, u.language
            FROM investments i
            JOIN users u ON i.user_id = u.user_id
            WHERE i.investment_id = ?
        ''', (investment_id,))
        
        invest_data = cursor.fetchone()
        
        if invest_data:
            user_id, amount, full_name, user_lang = invest_data
            db.conn.commit()
            
            # ارسال پیام به کاربر بر اساس زبان
            if user_lang == 'fa':
                user_message = (
                    f"❌ **سرمایه‌گذاری شما رد شد.**\n\n"
                    f"🎯 **شناسه درخواست:** #{investment_id}\n"
                    f"💵 **مبلغ:** ${amount:,.2f}\n\n"
                    f"📞 **دلیل:** لطفاً با پشتیبانی تماس بگیرید.\n"
                    f"👤 پشتیبانی: @YourSupportUsername"
                )
            elif user_lang == 'ar':
                user_message = (
                    f"❌ **تم رفض استثمارك.**\n\n"
                    f"🎯 **معرف الطلب:** #{investment_id}\n"
                    f"💵 **المبلغ:** ${amount:,.2f}\n\n"
                    f"📞 **السبب:** الرجاء الاتصال بالدعم الفني.\n"
                    f"👤 الدعم: @YourSupportUsername"
                )
            else:
                user_message = (
                    f"❌ **Your investment has been rejected.**\n\n"
                    f"🎯 **Request ID:** #{investment_id}\n"
                    f"💵 **Amount:** ${amount:,.2f}\n\n"
                    f"📞 **Reason:** Please contact support.\n"
                    f"👤 Support: @YourSupportUsername"
                )
            
            await bot.send_message(user_id, user_message)
            
            # پیام به ادمین
            admin_lang = db.get_user_language(message.from_user.id)
            if admin_lang == 'fa':
                await message.answer(f"❌ سرمایه‌گذاری #{investment_id} رد شد و به کاربر اطلاع داده شد.")
            elif admin_lang == 'ar':
                await message.answer(f"❌ تم رفض الاستثمار #{investment_id} وتم إعلام المستخدم.")
            else:
                await message.answer(f"❌ Investment #{investment_id} rejected and user notified.")
        else:
            admin_lang = db.get_user_language(message.from_user.id)
            if admin_lang == 'fa':
                await message.answer("❌ سرمایه‌گذاری یافت نشد.")
            elif admin_lang == 'ar':
                await message.answer("❌ لم يتم العثور على الاستثمار.")
            else:
                await message.answer("❌ Investment not found.")
            
    except Exception as e:
        await message.answer(f"❌ خطا: {str(e)}")
