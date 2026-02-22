# main.py
import asyncio
import os
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.strategy import FSMStrategy
from aiogram.fsm.context import FSMContext

# Import handlers
from database import Database
from keyboards.main_menu import get_main_menu_keyboard
from handlers.start import (
    RegistrationStates, 
    process_full_name, 
    process_email,
    process_phone,
    process_wallet,
    cancel_registration
)
from handlers.profile import (
    profile_menu, 
    view_profile, 
    edit_profile_menu,
    ProfileStates,
    edit_name_start,
    edit_name_finish,
    edit_email_start,
    edit_email_finish,
    edit_phone_start,
    edit_phone_finish,
    edit_wallet_start,
    edit_wallet_finish
)
# Import routers
from handlers.about import router as about_router
from handlers.admin import router as admin_router
from handlers.user_management import router as user_management_router
from handlers.tickets import router as tickets_router
from handlers.investment import router as investment_router
from handlers.referral import router as referral_router  # اضافه شد

# Load env
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# تنظیم پروکسی
# PROXY_URL = "http://127.0.0.1:10809"
# session = AiohttpSession(proxy=PROXY_URL)

# ایجاد bot و dispatcher
storage = MemoryStorage()
# bot = Bot(token=BOT_TOKEN, session=session)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=storage, fsm_strategy=FSMStrategy.USER_IN_CHAT)

# اضافه کردن router به dispatcher
dp.include_router(about_router)
dp.include_router(admin_router)
dp.include_router(user_management_router)
dp.include_router(tickets_router)
dp.include_router(investment_router)
dp.include_router(referral_router)  # اضافه شد

# ایجاد دیتابیس
db = Database()

def language_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇮🇷 فارسی", callback_data="lang_fa"),
            InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en"),
        ],
        [
            InlineKeyboardButton(text="🇸🇦 العربية", callback_data="lang_ar"),
        ]
    ])

@dp.message(CommandStart())
async def start_handler(message: Message, state: FSMContext):
    """هندلر شروع با پشتیبانی از رفرال"""
    user_id = message.from_user.id
    
    # بررسی وجود کد رفرال در استارت
    args = message.text.split()
    referrer_id = None
    
    if len(args) > 1 and args[1].startswith('ref_'):
        referral_code = args[1][4:]  # حذف 'ref_' از ابتدا
        referrer_id = db.get_user_by_referral_code(referral_code)
        
        # اطمینان از اینکه کاربر خودش رو دعوت نکرده
        if referrer_id == user_id:
            referrer_id = None
    
    user = db.get_user(user_id)
    
    # اگر کاربر ثبت‌نام نکرده (full_name ندارد)
    if user is None or user[2] is None:  # user[2] = full_name
        # اگر کاربر جدید است و کد رفرال دارد
        if referrer_id:
            await state.update_data(referrer_id=referrer_id)
        
        # نمایش منوی زبان
        await message.answer(
            "🌐 Welcome! Please choose your language:",
            reply_markup=language_keyboard()
        )
    else:
        # کاربر ثبت‌نام کرده - منوی اصلی
        language = db.get_user_language(user_id)
        if language == 'fa':
            await message.answer(
                "🤝 خوش آمدید!\n"
                "لطفاً یک گزینه را انتخاب کنید:",
                reply_markup=get_main_menu_keyboard(language)
            )
        elif language == 'ar':
            await message.answer(
                "🤝 أهلاً بك!\n"
                "الرجاء اختيار خيار:",
                reply_markup=get_main_menu_keyboard(language)
            )
        else:
            await message.answer(
                "🤝 Welcome back!\n"
                "Please choose an option:",
                reply_markup=get_main_menu_keyboard(language)
            )

@dp.callback_query(lambda c: c.data.startswith("lang_"))
async def language_callback_handler(callback_query: CallbackQuery, state: FSMContext):
    """هندلر انتخاب زبان - با متن معرفی در 3 پارت"""
    lang_code = callback_query.data.split("_")[1]
    user_id = callback_query.from_user.id
    
    # ذخیره زبان کاربر
    db.add_user(user_id, lang_code)
    
    await callback_query.answer()
    
    # نمایش متن معرفی بر اساس زبان
    if lang_code == "fa":
        # فارسی - سه بخش
        intro_part1 = (
            "🌐 **به RAMO FINANCE خوش آمدید**\n\n"
            "RAMO FINANCE یک مجموعه تخصصی در حوزه بازارهای مالی است که فعالیت خود را با تمرکز بر 📊 تحلیل حرفه‌ای، 📈 مدیریت سرمایه و ارائه راهکارهای نوین سرمایه‌گذاری آغاز کرده است.\n\n"
            "👥 **تیم ما** متشکل از تحلیل‌گران و متخصصانی است که دارای چندین سال سابقه فعالیت عملی در بازارهای بین‌المللی هستند و تصمیم‌گیری‌های خود را همواره بر پایه داده، استراتژی و ⚖️ مدیریت ریسک انجام می‌دهند."
        )
        
        intro_part2 = (
            "🤖 **بخشی از معاملات** این مجموعه به‌صورت کاملاً هوشمند انجام می‌شود. این معاملات توسط اکسپرت تریدینگ پیشرفته و اختصاصی RAMO FINANCE اجرا می‌گردد که بر پایه تحلیل داده، منطق الگوریتمی و مدیریت ریسک طراحی شده است.\n\n"
            "🔍 *شفافیت و ساختار حرفه‌ای* از اصول اصلی RAMO FINANCE است. سیستم معاملاتی هوشمند ما بر اساس الگوریتم‌های پیشرفته و تحلیل داده‌های بازار طراحی شده که امکان تصمیم‌گیری منطقی و به‌موقع را فراهم می‌آورد. عملکرد این سیستم به‌طور مداوم توسط تیم متخصص ما نظارت و بهینه‌سازی می‌شود."
        )
        
        intro_part3 = (
            "✅ **در ادامه، با تکمیل فرآیند ثبت‌نام، می‌توانید از خدمات و امکانات این مجموعه استفاده کنید.**\n\n"
            "👇 **لطفاً نام و نام خانوادگی خود را وارد کنید:**"
        )
        
        await callback_query.message.answer(intro_part1)
        await asyncio.sleep(0.8)
        await callback_query.message.answer(intro_part2)
        await asyncio.sleep(0.8)
        await callback_query.message.answer(intro_part3)
        
    elif lang_code == "en":
        # انگلیسی - سه بخش
        intro_part1 = (
            "🌐 **Welcome to RAMO FINANCE**\n\n"
            "RAMO FINANCE is a professional financial group focused on 📊 advanced market analysis, 📈 capital management, and innovative investment solutions.\n\n"
            "👥 **Our team** consists of experienced analysts and specialists with extensive hands-on experience in international financial markets. All decisions are made based on data-driven strategies and ⚖️ professional risk management."
        )
        
        intro_part2 = (
            "🤖 **A portion of our trading activities** is executed automatically through a proprietary and fully intelligent Expert Advisor, developed using algorithmic logic, data analysis, and structured risk management.\n\n"
            "🔍 *Transparency and Professional Structure* are core principles at RAMO FINANCE. Our intelligent trading system is built on advanced algorithms and comprehensive market data analysis, enabling logical and timely decision-making. The system's performance is continuously monitored and optimized by our team of experts."
        )
        
        intro_part3 = (
            "✅ **Please proceed with the registration process to access our services and features.**\n\n"
            "👇 **Please enter your full name:**"
        )
        
        await callback_query.message.answer(intro_part1)
        await asyncio.sleep(0.8)
        await callback_query.message.answer(intro_part2)
        await asyncio.sleep(0.8)
        await callback_query.message.answer(intro_part3)
        
    elif lang_code == "ar":
        # عربی - سه بخش
        intro_part1 = (
            "🌐 **مرحبًا بكم في RAMO FINANCE**\n\n"
            "RAMO FINANCE هي مجموعة متخصصة في الأسواق المالية، تركز على 📊 التحليل الاحترافي، 📈 إدارة رأس المال، وتقديم حلول استثمارية حديثة.\n\n"
            "👥 **يضم فريقنا** محللين وخبراء يمتلكون خبرة عملية واسعة في الأسواق المالية العالمية، حيث تعتمد جميع القرارات على البيانات والاستراتيجيات المدروسة و ⚖️ إدارة المخاطر الاحترافية."
        )
        
        intro_part2 = (
            "🤖 **يتم تنفيذ جزء من عمليات التداول** بشكل آلي بالكامل من خلال إكسبيرت تداول ذكي ومطوّر خصيصًا، يعتمد على التحليل الخوارزمي والبيانات وإدارة المخاطر.\n\n"
            "🔍 *الشفافية والهيكل المهني* من المبادئ الأساسية في RAMO FINANCE. نظام التداول الذكي الخاص بنا يعتمد على خوارزميات متطورة وتحليل شامل لبيانات السوق، مما يتيح اتخاذ قرارات منطقية وفي الوقت المناسب. يتم مراقبة أداء النظام وتحسينه بشكل مستمر من قبل فريق الخبراء لدينا."
        )
        
        intro_part3 = (
            "✅ **يرجى إكمال عملية التسجيل للمتابعة والاستفادة من خدماتنا.**\n\n"
            "👇 **الرجاء إدخال اسمك الكامل:**"
        )
        
        await callback_query.message.answer(intro_part1)
        await asyncio.sleep(0.8)
        await callback_query.message.answer(intro_part2)
        await asyncio.sleep(0.8)
        await callback_query.message.answer(intro_part3)
    
    # تنظیم state برای دریافت نام
    await state.set_state(RegistrationStates.waiting_for_full_name)

# دستورات مدیریتی
@dp.message(Command("reset"))
async def reset_command(message: Message):
    """پاک کردن اطلاعات کاربر برای تست"""
    user_id = message.from_user.id
    
    # حذف کاربر از دیتابیس
    cursor = db.conn.cursor()
    cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
    db.conn.commit()
    
    await message.answer("✅ Your data has been reset! Send /start to begin again.")

@dp.message(Command("myid"))
async def get_my_id(message: Message):
    """دریافت شناسه کاربر"""
    user_id = message.from_user.id
    language = db.get_user_language(user_id) if db.get_user(user_id) else 'en'
    
    if language == 'fa':
        await message.answer(f"شناسه شما: {user_id}\n\nبرای افزودن به ادمین‌ها، این شناسه را به ADMIN_IDS در فایل .env اضافه کنید.")
    elif language == 'ar':
        await message.answer(f"معرفك: {user_id}\n\nلإضافة كمسؤول، أضف هذا المعرف إلى ADMIN_IDS في ملف .env.")
    else:
        await message.answer(f"Your ID: {user_id}\n\nTo add as admin, add this ID to ADMIN_IDS in .env file.")

@dp.message(Command("checkwallets"))
async def check_wallets_command(message: Message):
    """بررسی کیف پول‌های کاربران"""
    admin_ids_str = os.getenv("ADMIN_IDS", "")
    if not admin_ids_str:
        return
    
    admin_ids = [int(id_str.strip()) for id_str in admin_ids_str.split(",") if id_str.strip()]
    if message.from_user.id not in admin_ids:
        return
    
    cursor = db.conn.cursor()
    
    # شمارش کاربران با کیف پول
    cursor.execute("SELECT COUNT(*) FROM users WHERE wallet_address IS NOT NULL AND wallet_address != ''")
    with_wallet = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    
    cursor.execute("""
        SELECT user_id, full_name, wallet_address 
        FROM users 
        WHERE wallet_address IS NOT NULL AND wallet_address != ''
        LIMIT 10
    """)
    
    users_with_wallets = cursor.fetchall()
    
    result = (
        "💰 **بررسی کیف پول‌های کاربران**\n\n"
        f"👥 کل کاربران: {total_users}\n"
        f"🔐 کاربران با کیف پول: {with_wallet}\n"
        f"⚠️ کاربران بدون کیف پول: {total_users - with_wallet}\n\n"
    )
    
    if users_with_wallets:
        result += "**کیف پول‌های موجود:**\n"
        for user in users_with_wallets:
            user_id, full_name, wallet = user
            result += f"• {full_name or 'بدون نام'}\n"
            result += f"  🆔: {user_id}\n"
            if wallet and len(wallet) > 0:
                result += f"  🔐: {wallet[:25]}...{wallet[-25:] if len(wallet) > 60 else ''}\n\n"
            else:
                result += f"  🔐: خالی\n\n"
    else:
        result += "❌ هیچ کیف پولی ثبت نشده است.\n"
    
    result += "\n📌 نکته: اگر کیف پول‌ها نمایش داده نمی‌شوند:\n"
    result += "1. دیتابیس قدیمی است\n"
    result += "2. ستون wallet_address وجود ندارد\n"
    result += "3. دستور /resetdb را اجرا کنید"
    
    await message.answer(result)

@dp.message(Command("resetdb"))
async def reset_db_command(message: Message):
    """ریست دیتابیس"""
    admin_ids_str = os.getenv("ADMIN_IDS", "")
    if not admin_ids_str:
        return
    
    admin_ids = [int(id_str.strip()) for id_str in admin_ids_str.split(",") if id_str.strip()]
    if message.from_user.id not in admin_ids:
        return
    
    # حذف و ایجاد مجدد دیتابیس
    import os
    if os.path.exists('finance_bot.db'):
        os.remove('finance_bot.db')
        print("🗑️ دیتابیس قدیمی حذف شد")
    
    # ایجاد مجدد دیتابیس
    global db
    db = Database()
    
    await message.answer(
        "✅ دیتابیس با موفقیت ریست شد!\n\n"
        "حالا:\n"
        "1. کاربران باید دوباره ثبت‌نام کنند\n"
        "2. کیف پول‌ها ذخیره خواهند شد\n"
        "3. پنل ادمین کار خواهد کرد"
    )

@dp.message(Command("dbinfo"))
async def db_info_command(message: Message):
    """اطلاعات دیتابیس"""
    admin_ids_str = os.getenv("ADMIN_IDS", "")
    if not admin_ids_str:
        return
    
    admin_ids = [int(id_str.strip()) for id_str in admin_ids_str.split(",") if id_str.strip()]
    if message.from_user.id not in admin_ids:
        return
    
    cursor = db.conn.cursor()
    
    # بررسی جداول
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    info = "📊 **اطلاعات دیتابیس**\n\n"
    info += "**جدول‌های موجود:**\n"
    
    for table in tables:
        table_name = table[0]
        info += f"  📁 {table_name}\n"
        
        # بررسی ستون‌های هر جدول
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        
        for col in columns:
            col_id, col_name, col_type, notnull, default_val, pk = col
            info += f"    • {col_name} ({col_type})"
            if pk:
                info += " 🔑"
            info += "\n"
        
        # تعداد رکوردها
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        row_count = cursor.fetchone()[0]
        info += f"    📈 تعداد رکوردها: {row_count}\n\n"
    
    # اطلاعات فایل
    import os
    if os.path.exists('finance_bot.db'):
        size = os.path.getsize('finance_bot.db')
        info += f"**اطلاعات فایل:**\n"
        info += f"  📏 حجم: {size:,} بایت ({size/1024/1024:.2f} مگابایت)\n"
        info += f"  📅 آخرین تغییر: {os.path.getmtime('finance_bot.db'):.0f}"
    
    await message.answer(info)

@dp.message(Command("list_users"))
async def list_users_command(message: Message):
    """لیست تمام کاربران - دستور جدید"""
    admin_ids_str = os.getenv("ADMIN_IDS", "")
    if not admin_ids_str:
        return
    
    admin_ids = [int(id_str.strip()) for id_str in admin_ids_str.split(",") if id_str.strip()]
    if message.from_user.id not in admin_ids:
        return
    
    # تشخیص زبان ادمین
    user_id = message.from_user.id
    admin_data = db.get_user(user_id)
    admin_language = admin_data[1] if admin_data else 'fa'
    
    cursor = db.conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    
    cursor.execute("""
        SELECT user_id, full_name, email, phone, wallet_address, balance, registered_at 
        FROM users 
        ORDER BY registered_at DESC 
        LIMIT 15
    """)
    
    users = cursor.fetchall()
    
    if users:
        if admin_language == 'fa':
            result_text = f"📋 **لیست کاربران - کل: {total_users} نفر**\n\n"
            
            for user in users:
                user_id, full_name, email, phone, wallet, balance, reg_date = user
                
                # نمایش کیف پول اگر وجود دارد
                wallet_display = ""
                if wallet and wallet.strip():
                    if len(wallet) > 60:
                        wallet_display = f"{wallet[:8]}...{wallet[-6:]}"
                    else:
                        wallet_display = wallet
                
                result_text += f"👤 **{full_name or 'بدون نام'}**\n"
                result_text += f"  🆔: {user_id}\n"
                result_text += f"  📧: {email or 'ندارد'}\n"
                result_text += f"  📱: {phone or 'ندارد'}\n"
                result_text += f"  💰: ${balance:.2f}\n"
                if wallet_display:
                    result_text += f"  🔐: {wallet_display}\n"
                result_text += f"  📅: {reg_date[:10]}\n"
                result_text += f"  👁️: /user_{user_id}\n\n"
            
            result_text += "\n📌 **نکته:** برای مشاهده جزئیات کامل هر کاربر از دستور `/user_شناسه` استفاده کنید."
            
        elif admin_language == 'ar':
            result_text = f"📋 **قائمة المستخدمين - الإجمالي: {total_users} مستخدم**\n\n"
            
            for user in users:
                user_id, full_name, email, phone, wallet, balance, reg_date = user
                
                wallet_display = ""
                if wallet and wallet.strip():
                    if len(wallet) > 60:
                        wallet_display = f"{wallet[:8]}...{wallet[-6:]}"
                    else:
                        wallet_display = wallet
                
                result_text += f"👤 **{full_name or 'بدون نام'}**\n"
                result_text += f"  🆔: {user_id}\n"
                result_text += f"  📧: {email or 'لا يوجد'}\n"
                result_text += f"  📱: {phone or 'لا يوجد'}\n"
                result_text += f"  💰: ${balance:.2f}\n"
                if wallet_display:
                    result_text += f"  🔐: {wallet_display}\n"
                result_text += f"  📅: {reg_date[:10]}\n"
                result_text += f"  👁️: /user_{user_id}\n\n"
            
            result_text += "\n📌 **ملاحظة:** لعرض تفاصيل كاملة لأي مستخدم، استخدم الأمر `/user_المعرف`."
            
        else:
            result_text = f"📋 **Users List - Total: {total_users} users**\n\n"
            
            for user in users:
                user_id, full_name, email, phone, wallet, balance, reg_date = user
                
                wallet_display = ""
                if wallet and wallet.strip():
                    if len(wallet) > 60:
                        wallet_display = f"{wallet[:8]}...{wallet[-6:]}"
                    else:
                        wallet_display = wallet
                
                result_text += f"👤 **{full_name or 'No name'}**\n"
                result_text += f"  🆔: {user_id}\n"
                result_text += f"  📧: {email or 'None'}\n"
                result_text += f"  📱: {phone or 'None'}\n"
                result_text += f"  💰: ${balance:.2f}\n"
                if wallet_display:
                    result_text += f"  🔐: {wallet_display}\n"
                result_text += f"  📅: {reg_date[:10]}\n"
                result_text += f"  👁️: /user_{user_id}\n\n"
            
            result_text += "\n📌 **Note:** To view full details of any user, use the command `/user_ID`."
        
        await message.answer(result_text, parse_mode="Markdown")
    else:
        if admin_language == 'fa':
            await message.answer("❌ هیچ کاربری یافت نشد.")
        elif admin_language == 'ar':
            await message.answer("❌ لم يتم العثور على أي مستخدمين.")
        else:
            await message.answer("❌ No users found.")

# Handler برای دستور /user_
@dp.message(F.text.regexp(r'^/user_\d+$'))
async def handle_user_command(message: Message):
    """مشاهده جزئیات کامل یک کاربر"""
    admin_ids_str = os.getenv("ADMIN_IDS", "")
    if not admin_ids_str:
        return
    
    admin_ids = [int(id_str.strip()) for id_str in admin_ids_str.split(",") if id_str.strip()]
    if message.from_user.id not in admin_ids:
        return
    
    try:
        user_id = int(message.text.split('_')[1])
        
        cursor = db.conn.cursor()
        cursor.execute("""
            SELECT user_id, language, full_name, email, phone, wallet_address, balance, registered_at 
            FROM users 
            WHERE user_id = ?
        """, (user_id,))
        
        user = cursor.fetchone()
        
        if user:
            user_id, language, full_name, email, phone, wallet, balance, reg_date = user
            
            # دریافت سرمایه‌گذاری‌های کاربر
            cursor.execute("""
                SELECT COUNT(*), SUM(amount) 
                FROM investments 
                WHERE user_id = ? AND status = 'active'
            """, (user_id,))
            inv_count, inv_total = cursor.fetchone()
            inv_count = inv_count or 0
            inv_total = inv_total or 0
            
            # دریافت تیکت‌های کاربر
            cursor.execute("""
                SELECT COUNT(*)
                FROM tickets 
                WHERE user_id = ?
            """, (user_id,))
            ticket_count = cursor.fetchone()[0] or 0
            
            # تشخیص زبان ادمین برای نمایش پیام
            admin_data = db.get_user(message.from_user.id)
            admin_language = admin_data[1] if admin_data else 'fa'
            
            if admin_language == 'fa':
                details = (
                    "👤 **جزئیات کامل کاربر**\n\n"
                    f"🆔 **شناسه:** {user_id}\n"
                    f"🌐 **زبان:** {language}\n"
                    f"👤 **نام کامل:** {full_name or 'ثبت نشده'}\n"
                    f"📧 **ایمیل:** {email or 'ثبت نشده'}\n"
                    f"📱 **تلفن:** {phone or 'ثبت نشده'}\n"
                    f"💰 **موجودی:** ${balance:.2f}\n"
                    f"📅 **تاریخ ثبت‌نام:** {reg_date}\n\n"
                    
                    f"💼 **سرمایه‌گذاری‌ها:**\n"
                    f"   • تعداد فعال: {inv_count}\n"
                    f"   • مجموع مبلغ: ${inv_total:.2f}\n\n"
                    
                    f"🎫 **تیکت‌ها:**\n"
                    f"   • تعداد تیکت‌ها: {ticket_count}\n"
                    f"   • مشاهده: /tickets_{user_id}\n\n"
                )
                
                if wallet and len(wallet) > 0:
                    details += (
                        f"🔐 **آدرس کیف پول (BEP20):**\n"
                        f"{wallet}\n\n"
                        f"📏 **طول آدرس:** {len(wallet)} کاراکتر\n\n"
                    )
                else:
                    details += "🔐 **کیف پول:** ❌ ثبت نشده\n\n"
                
                details += (
                    "**دستورات مدیریت:**\n"
                    f"✏️ ویرایش کاربر: /edit_{user_id}\n"
                    f"💰 افزودن موجودی: /addbalance_{user_id}\n"
                    f"⚠️ مسدود کردن: /ban_{user_id}"
                )
                
            elif admin_language == 'ar':
                details = (
                    "👤 **تفاصيل كاملة للمستخدم**\n\n"
                    f"🆔 **المعرف:** {user_id}\n"
                    f"🌐 **اللغة:** {language}\n"
                    f"👤 **الاسم الكامل:** {full_name or 'غير مسجل'}\n"
                    f"📧 **البريد الإلكتروني:** {email or 'غير مسجل'}\n"
                    f"📱 **الهاتف:** {phone or 'غير مسجل'}\n"
                    f"💰 **الرصيد:** ${balance:.2f}\n"
                    f"📅 **تاريخ التسجيل:** {reg_date}\n\n"
                    
                    f"💼 **الاستثمارات:**\n"
                    f"   • عدد النشطة: {inv_count}\n"
                    f"   • إجمالي المبلغ: ${inv_total:.2f}\n\n"
                    
                    f"🎫 **التذاكر:**\n"
                    f"   • عدد التذاكر: {ticket_count}\n"
                    f"   • عرض: /tickets_{user_id}\n\n"
                )
                
                if wallet and len(wallet) > 0:
                    details += (
                        f"🔐 **عنوان المحفظة (BEP20):**\n"
                        f"{wallet}\n\n"
                        f"📏 **طول العنوان:** {len(wallet)} حرف\n\n"
                    )
                else:
                    details += "🔐 **المحفظة:** ❌ غير مسجلة\n\n"
                
                details += (
                    "**أوامر الإدارة:**\n"
                    f"✏️ تعديل المستخدم: /edit_{user_id}\n"
                    f"💰 إضافة رصيد: /addbalance_{user_id}\n"
                    f"⚠️ حظر: /ban_{user_id}"
                )
                
            else:
                details = (
                    "👤 **Full User Details**\n\n"
                    f"🆔 **ID:** {user_id}\n"
                    f"🌐 **Language:** {language}\n"
                    f"👤 **Full Name:** {full_name or 'Not registered'}\n"
                    f"📧 **Email:** {email or 'Not registered'}\n"
                    f"📱 **Phone:** {phone or 'Not registered'}\n"
                    f"💰 **Balance:** ${balance:.2f}\n"
                    f"📅 **Registration Date:** {reg_date}\n\n"
                    
                    f"💼 **Investments:**\n"
                    f"   • Active count: {inv_count}\n"
                    f"   • Total amount: ${inv_total:.2f}\n\n"
                    
                    f"🎫 **Tickets:**\n"
                    f"   • Ticket count: {ticket_count}\n"
                    f"   • View: /tickets_{user_id}\n\n"
                )
                
                if wallet and len(wallet) > 0:
                    details += (
                        f"🔐 **Wallet Address (BEP20):**\n"
                        f"{wallet}\n\n"
                        f"📏 **Address Length:** {len(wallet)} characters\n\n"
                    )
                else:
                    details += "🔐 **Wallet:** ❌ Not registered\n\n"
                
                details += (
                    "**Management Commands:**\n"
                    f"✏️ Edit user: /edit_{user_id}\n"
                    f"💰 Add balance: /addbalance_{user_id}\n"
                    f"⚠️ Ban: /ban_{user_id}"
                )
            
            await message.answer(details)
        else:
            admin_data = db.get_user(message.from_user.id)
            admin_language = admin_data[1] if admin_data else 'fa'
            
            if admin_language == 'fa':
                await message.answer("❌ کاربر یافت نشد.")
            elif admin_language == 'ar':
                await message.answer("❌ لم يتم العثور على المستخدم.")
            else:
                await message.answer("❌ User not found.")
            
    except Exception as e:
        await message.answer(f"❌ خطا: {str(e)}")

# Handler برای دستور /find_
@dp.message(F.text.regexp(r'^/find_.+$'))
async def find_user_command(message: Message):
    """دستور find برای جستجوی کاربر"""
    admin_ids_str = os.getenv("ADMIN_IDS", "")
    if not admin_ids_str:
        return
    
    admin_ids = [int(id_str.strip()) for id_str in admin_ids_str.split(",") if id_str.strip()]
    if message.from_user.id not in admin_ids:
        return
    
    search_term = message.text[6:]  # حذف /find_
    
    cursor = db.conn.cursor()
    cursor.execute("""
        SELECT user_id, full_name, email, phone, wallet_address, registered_at 
        FROM users 
        WHERE full_name LIKE ? OR email LIKE ? OR phone LIKE ? OR wallet_address LIKE ?
        LIMIT 15
    """, (f'%{search_term}%', f'%{search_term}%', f'%{search_term}%', f'%{search_term}%'))
    
    results = cursor.fetchall()
    
    # تشخیص زبان ادمین
    admin_data = db.get_user(message.from_user.id)
    admin_language = admin_data[1] if admin_data else 'fa'
    
    if results:
        if admin_language == 'fa':
            result_text = f"🔍 **نتایج جستجو برای '{search_term}'**\n\n"
            
            for user in results:
                user_id, full_name, email, phone, wallet, reg_date = user
                
                # نمایش کیف پول اگر وجود دارد
                wallet_display = ""
                if wallet:
                    if len(wallet) > 15:
                        wallet_display = f"{wallet[:8]}...{wallet[-6:]}"
                    else:
                        wallet_display = wallet
                
                result_text += f"• **{full_name or 'بدون نام'}**\n"
                result_text += f"  🆔: {user_id}\n"
                result_text += f"  📧: {email or 'ندارد'}\n"
                result_text += f"  📱: {phone or 'ندارد'}\n"
                if wallet_display:
                    result_text += f"  🔐: {wallet_display}\n"
                result_text += f"  📅: {reg_date[:10]}\n"
                result_text += f"  👁️: /user_{user_id}\n\n"
            
        elif admin_language == 'ar':
            result_text = f"🔍 **نتائج البحث عن '{search_term}'**\n\n"
            
            for user in results:
                user_id, full_name, email, phone, wallet, reg_date = user
                
                wallet_display = ""
                if wallet:
                    if len(wallet) > 15:
                        wallet_display = f"{wallet[:8]}...{wallet[-6:]}"
                    else:
                        wallet_display = wallet
                
                result_text += f"• **{full_name or 'بدون نام'}**\n"
                result_text += f"  🆔: {user_id}\n"
                result_text += f"  📧: {email or 'لا يوجد'}\n"
                result_text += f"  📱: {phone or 'لا يوجد'}\n"
                if wallet_display:
                    result_text += f"  🔐: {wallet_display}\n"
                result_text += f"  📅: {reg_date[:10]}\n"
                result_text += f"  👁️: /user_{user_id}\n\n"
            
        else:
            result_text = f"🔍 **Search results for '{search_term}'**\n\n"
            
            for user in results:
                user_id, full_name, email, phone, wallet, reg_date = user
                
                wallet_display = ""
                if wallet:
                    if len(wallet) > 15:
                        wallet_display = f"{wallet[:8]}...{wallet[-6:]}"
                    else:
                        wallet_display = wallet
                
                result_text += f"• **{full_name or 'No name'}**\n"
                result_text += f"  🆔: {user_id}\n"
                result_text += f"  📧: {email or 'None'}\n"
                result_text += f"  📱: {phone or 'None'}\n"
                if wallet_display:
                    result_text += f"  🔐: {wallet_display}\n"
                result_text += f"  📅: {reg_date[:10]}\n"
                result_text += f"  👁️: /user_{user_id}\n\n"
        
        await message.answer(result_text)
    else:
        if admin_language == 'fa':
            await message.answer("❌ هیچ کاربری یافت نشد.")
        elif admin_language == 'ar':
            await message.answer("❌ لم يتم العثور على أي مستخدمين.")
        else:
            await message.answer("❌ No users found.")

# هندلرهای منوی اصلی
@dp.message(F.text.in_(["👤 Profile", "👤 پروفایل", "👤 الملف الشخصي"]))
async def handle_profile(message: Message, state: FSMContext):
    await profile_menu(message, state)

# هندلر دعوت از دوستان
@dp.message(F.text.in_(["🎁 Invite Friends", "🎁 دعوت از دوستان", "🎁 دعوة الأصدقاء"]))
async def handle_referral(message: Message, state: FSMContext):
    from handlers.referral import referral_menu
    await referral_menu(message)

@dp.message(F.text.in_(["⚙️ Settings", "⚙️ تنظیمات", "⚙️ الإعدادات"]))
async def handle_settings(message: Message):
    user_id = message.from_user.id
    language = db.get_user_language(user_id)
    
    if language == 'fa':
        await message.answer("⚙️ **تنظیمات**\n\nاین بخش به زودی فعال خواهد شد...")
    elif language == 'ar':
        await message.answer("⚙️ **الإعدادات**\n\nسيتم تفعيل هذا القسم قريباً...")
    else:
        await message.answer("⚙️ **Settings**\n\nThis section will be available soon...")

# هندلرهای پروفایل
@dp.message(F.text.in_(["👁️ مشاهده اطلاعات", "👁️ View Profile", "👁️ عرض الملف"]))
async def handle_view_profile(message: Message):
    await view_profile(message)

@dp.message(F.text.in_(["✏️ ویرایش اطلاعات", "✏️ Edit Profile", "✏️ تعديل الملف"]))
async def handle_edit_profile_menu(message: Message):
    await edit_profile_menu(message)

# هندلرهای ویرایش پروفایل
@dp.message(F.text.in_(["✏️ ویرایش نام", "✏️ Edit Name", "✏️ تعديل الاسم"]))
async def handle_edit_name(message: Message, state: FSMContext):
    await edit_name_start(message, state)

@dp.message(F.text.in_(["📧 ویرایش ایمیل", "📧 Edit Email", "📧 تعديل البريد"]))
async def handle_edit_email(message: Message, state: FSMContext):
    await edit_email_start(message, state)

@dp.message(F.text.in_(["📱 ویرایش تلفن", "📱 Edit Phone", "📱 تعديل الهاتف"]))
async def handle_edit_phone(message: Message, state: FSMContext):
    await edit_phone_start(message, state)

@dp.message(F.text.in_(["💰 ویرایش کیف پول", "💰 Edit Wallet", "💰 تعديل المحفظة"]))
async def handle_edit_wallet(message: Message, state: FSMContext):
    await edit_wallet_start(message, state)

# هندلر برای contact (اشتراک‌گذاری شماره تماس)
@dp.message(F.contact)
async def handle_contact(message: Message, state: FSMContext):
    """هندل کردن شماره تماس از دکمه اشتراک‌گذاری"""
    current_state = await state.get_state()
    
    # اگر در حال ثبت‌نام هست
    if current_state == RegistrationStates.waiting_for_phone.state:
        await process_phone(message, state)
    # اگر در حال ویرایش پروفایل هست
    elif current_state == ProfileStates.waiting_for_new_phone.state:
        await edit_phone_finish(message, state)

# هندلر برای بازگشت به منوی اصلی
@dp.message(F.text.in_(["🔙 بازگشت", "🔙 Back", "🔙 رجوع"]))
async def handle_back_to_main(message: Message, state: FSMContext):
    user_id = message.from_user.id
    language = db.get_user_language(user_id)
    
    await state.clear()
    if language == 'fa':
        await message.answer("🔙 بازگشت به منوی اصلی", reply_markup=get_main_menu_keyboard(language))
    elif language == 'ar':
        await message.answer("🔙 الرجوع إلى القائمة الرئيسية", reply_markup=get_main_menu_keyboard(language))
    else:
        await message.answer("🔙 Back to main menu", reply_markup=get_main_menu_keyboard(language))

# هندلر برای skip شماره تلفن (هم در ثبت‌نام هم در ویرایش)
@dp.message(F.text.in_(["⏭️ رد کردن", "⏭️ Skip", "⏭️ تخطي"]))
async def handle_skip_phone(message: Message, state: FSMContext):
    """هندل کردن دکمه skip برای شماره تلفن"""
    current_state = await state.get_state()
    
    if current_state == RegistrationStates.waiting_for_phone.state:
        await process_phone(message, state)
    elif current_state == ProfileStates.waiting_for_new_phone.state:
        await edit_phone_finish(message, state)

# ثبت handlerهای ثبت‌نام
dp.message.register(process_full_name, RegistrationStates.waiting_for_full_name)
dp.message.register(process_email, RegistrationStates.waiting_for_email)
dp.message.register(process_phone, RegistrationStates.waiting_for_phone)
dp.message.register(process_wallet, RegistrationStates.waiting_for_wallet)

# ثبت handlerهای ویرایش پروفایل
dp.message.register(edit_name_finish, ProfileStates.waiting_for_new_name)
dp.message.register(edit_email_finish, ProfileStates.waiting_for_new_email)
dp.message.register(edit_phone_finish, ProfileStates.waiting_for_new_phone)
dp.message.register(edit_wallet_finish, ProfileStates.waiting_for_new_wallet)

async def main():
#    print(f"🤖 Bot is starting with proxy: {PROXY_URL}")
    print(f"🤖 Send /reset to clear your data for testing")
    print(f"🤖 Send /myid to get your user ID")
    print(f"🤖 Send /dbinfo to check database structure")
    print(f"🤖 Send /checkwallets to check user wallets")
    print(f"🤖 Send /resetdb to reset database (admin only)")
    print(f"🤖 Admins can use /admin command")
    print(f"🤖 Admins can use /list_users to see all users")
    print(f"🤖 Ticket system is active - users can use Support menu")
    print(f"🤖 Investment system is active - users can invest from $1,000")
    print(f"🤖 Referral system is active - users can invite friends")  # اضافه شد
    print(f"🤖 Admin investment commands: /confirm_invest_ID /reject_invest_ID")
    try:
        await dp.start_polling(bot)
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main())
