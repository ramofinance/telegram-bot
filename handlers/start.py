# handlers/start.py
from aiogram import F, Bot
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import os
from datetime import datetime
from aiogram.enums import ParseMode

from database import Database
from keyboards.main_menu import get_main_menu_keyboard, get_back_keyboard

db = Database()

class RegistrationStates(StatesGroup):
    waiting_for_full_name = State()
    waiting_for_email = State()
    waiting_for_phone = State()
    waiting_for_wallet = State()

def get_phone_keyboard(language='en'):
    """کیبورد برای شماره تلفن (با دکمه skip)"""
    if language == 'fa':
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📱 ارسال شماره تماس", request_contact=True)],
                [KeyboardButton(text="⏭️ رد کردن")]
            ],
            resize_keyboard=True,
            one_time_keyboard=True
        )
    elif language == 'ar':
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📱 مشاركة رقم الهاتف", request_contact=True)],
                [KeyboardButton(text="⏭️ تخطي")]
            ],
            resize_keyboard=True,
            one_time_keyboard=True
        )
    else:
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📱 Share phone number", request_contact=True)],
                [KeyboardButton(text="⏭️ Skip")]
            ],
            resize_keyboard=True,
            one_time_keyboard=True
        )

async def start_command(message: Message, state: FSMContext):
    """ورود کاربر جدید"""
    user_id = message.from_user.id
    
    # بررسی آیا کاربر ثبت‌نام کرده؟
    user = db.get_user(user_id)
    language = db.get_user_language(user_id)
    
    if user and user[2]:  # اگر full_name دارد یعنی ثبت‌نام کرده
        # نمایش منوی اصلی
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
    else:
        # شروع ثبت‌نام
        if language == 'fa':
            await message.answer(
                "👋 به ربات سرمایه‌گذاری خوش آمدید!\n\n"
                "برای شروع، لطفاً نام و نام خانوادگی خود را وارد کنید:",
                reply_markup=get_back_keyboard(language)
            )
        elif language == 'ar':
            await message.answer(
                "👋 أهلاً بك في بوت الاستثمار!\n\n"
                "للبدء، الرجاء إدخال اسمك الكامل:",
                reply_markup=get_back_keyboard(language)
            )
        else:
            await message.answer(
                "👋 Welcome to Investment Bot!\n\n"
                "To start, please enter your full name:",
                reply_markup=get_back_keyboard(language)
            )
        await state.set_state(RegistrationStates.waiting_for_full_name)

async def process_full_name(message: Message, state: FSMContext):
    """دریافت نام کامل"""
    user_id = message.from_user.id
    language = db.get_user_language(user_id)
    
    await state.update_data(full_name=message.text)
    
    if language == 'fa':
        await message.answer("📧 لطفاً ایمیل خود را وارد کنید:")
    elif language == 'ar':
        await message.answer("📧 الرجاء إدخال بريدك الإلكتروني:")
    else:
        await message.answer("📧 Please enter your email:")
    await state.set_state(RegistrationStates.waiting_for_email)

async def process_email(message: Message, state: FSMContext):
    """دریافت ایمیل"""
    user_id = message.from_user.id
    language = db.get_user_language(user_id)
    
    # اعتبارسنجی ساده ایمیل
    if '@' not in message.text or '.' not in message.text:
        if language == 'fa':
            await message.answer("⚠️ ایمیل نامعتبر است. لطفاً ایمیل صحیح وارد کنید:")
        elif language == 'ar':
            await message.answer("⚠️ بريد إلكتروني غير صالح. الرجاء إدخال بريد صحيح:")
        else:
            await message.answer("⚠️ Invalid email. Please enter a valid email:")
        return
    
    await state.update_data(email=message.text)
    
    # درخواست شماره تلفن با دکمه skip
    if language == 'fa':
        await message.answer(
            "📱 لطفاً شماره تماس خود را وارد کنید یا از دکمه‌های زیر استفاده کنید:",
            reply_markup=get_phone_keyboard(language)
        )
    elif language == 'ar':
        await message.answer(
            "📱 الرجاء إدخال رقم هاتفك أو استخدم الأزرار أدناه:",
            reply_markup=get_phone_keyboard(language)
        )
    else:
        await message.answer(
            "📱 Please enter your phone number or use buttons below:",
            reply_markup=get_phone_keyboard(language)
        )
    await state.set_state(RegistrationStates.waiting_for_phone)

async def process_phone(message: Message, state: FSMContext):
    """دریافت شماره تماس"""
    user_id = message.from_user.id
    language = db.get_user_language(user_id)
    
    # بررسی اگر کاربر skip زد
    if message.text in ["⏭️ رد کردن", "⏭️ Skip", "⏭️ تخطي"]:
        phone = "Not provided"
    elif message.contact:
        # اگر از دکمه اشتراک‌گذاری استفاده کرد
        phone = message.contact.phone_number
    else:
        phone = message.text
    
    await state.update_data(phone=phone)
    
    # درخواست آدرس کیف پول با تأکید روی شبکه BEP20
    if language == 'fa':
        await message.answer(
            "💰 **لطفاً آدرس کیف پول ارز دیجیتال خود را وارد کنید:**\n\n"
            "⚠️ **توجه مهم:**\n"
            "• این آدرس باید در شبکه **BEP20** باشد\n"
            "• سود ماهانه شما به این آدرس واریز خواهد شد\n"
            "• لطفاً در وارد کردن آدرس دقت کنید\n\n"
            "مثال: 0x742d35Cc6634C0532925a3b844Bc9e...",
            reply_markup=get_back_keyboard(language)
        )
    elif language == 'ar':
        await message.answer(
            "💰 **الرجاء إدخال عنوان محفظة العملات الرقمية:**\n\n"
            "⚠️ **مهم:**\n"
            "• يجب أن يكون هذا العنوان على شبكة **BEP20**\n"
            "• سيتم إرسال أرباحك الشهرية إلى هذا العنوان\n"
            "• الرجاء التحقق من العنوان بعناية\n\n"
            "مثال: 0x742d35Cc6634C0532925a3b844Bc9e...",
            reply_markup=get_back_keyboard(language)
        )
    else:
        await message.answer(
            "💰 **Please enter your cryptocurrency wallet address:**\n\n"
            "⚠️ **Important:**\n"
            "• This address must be on the **BEP20 network**\n"
            "• Your monthly profits will be sent to this address\n"
            "• Please double-check the address\n\n"
            "Example: 0x742d35Cc6634C0532925a3b844Bc9e...",
            reply_markup=get_back_keyboard(language)
        )
    await state.set_state(RegistrationStates.waiting_for_wallet)

async def process_wallet(message: Message, state: FSMContext):
    """دریافت آدرس کیف پول و تکمیل ثبت‌نام با پشتیبانی از رفرال"""
    user_id = message.from_user.id
    language = db.get_user_language(user_id)
    
    # اعتبارسنجی ساده آدرس کیف پول
    wallet_address = message.text.strip()
    
    # بررسی حداقل طول و شروع با 0x
    if not wallet_address.startswith('0x') or len(wallet_address) < 20:
        if language == 'fa':
            await message.answer(
                "⚠️ آدرس کیف پول نامعتبر است!\n"
                "آدرس باید با '0x' شروع شود و حداقل 20 کاراکتر باشد.\n"
                "لطفاً دوباره وارد کنید:"
            )
        elif language == 'ar':
            await message.answer(
                "⚠️ عنوان محفظة غير صالح!\n"
                "يجب أن يبدأ العنوان بـ '0x' ويحتوي على 20 حرفًا على الأقل.\n"
                "الرجاء إعادة الإدخال:"
            )
        else:
            await message.answer(
                "⚠️ Invalid wallet address!\n"
                "Address must start with '0x' and be at least 20 characters.\n"
                "Please enter again:"
            )
        return
    
    # دریافت تمام داده‌ها
    data = await state.get_data()
    
    # ذخیره در دیتابیس
    db.update_user_profile(
        user_id=user_id,
        full_name=data.get('full_name', ''),
        email=data.get('email', ''),
        phone=data.get('phone', 'Not provided'),
        wallet_address=wallet_address
    )
    
    # ثبت رفرال اگر وجود داشت
    referrer_id = data.get('referrer_id')
    if referrer_id:
        db.register_referral(referrer_id, user_id)
        
        # ارسال نوتیفیکیشن به دعوت‌کننده
        try:
            referrer_lang = db.get_user_language(referrer_id)
            if referrer_lang == 'fa':
                await message.bot.send_message(
                    referrer_id,
                    f"🎉 **تبریک!**\n\n"
                    f"یک نفر با لینک دعوت شما ثبت‌نام کرد.\n"
                    f"👤 کاربر: {data.get('full_name', '')}\n"
                    f"📅 تاریخ: {datetime.now().strftime('%Y-%m-%d')}"
                )
            elif referrer_lang == 'ar':
                await message.bot.send_message(
                    referrer_id,
                    f"🎉 **تهانينا!**\n\n"
                    f"شخص ما سجل عبر رابط دعوتك.\n"
                    f"👤 المستخدم: {data.get('full_name', '')}\n"
                    f"📅 التاريخ: {datetime.now().strftime('%Y-%m-%d')}"
                )
            else:
                await message.bot.send_message(
                    referrer_id,
                    f"🎉 **Congratulations!**\n\n"
                    f"Someone registered using your referral link.\n"
                    f"👤 User: {data.get('full_name', '')}\n"
                    f"📅 Date: {datetime.now().strftime('%Y-%m-%d')}"
                )
        except Exception as e:
            print(f"❌ Failed to send referral notification: {e}")
    
    # پاک کردن state
    await state.clear()
    
    # نمایش پیام موفقیت با تأکید روی شبکه BEP20
    if language == 'fa':
        await message.answer(
            "🎉 **ثبت‌نام شما با موفقیت تکمیل شد!**\n\n"
            f"📋 اطلاعات ثبت شده:\n"
            f"👤 نام: {data.get('full_name')}\n"
            f"📧 ایمیل: {data.get('email')}\n"
            f"📱 تلفن: {data.get('phone', 'ارسال نشده')}\n"
            f"💰 کیف پول: `{wallet_address[:10]}...{wallet_address[-10:]}`\n\n"
            "⚠️ **توجه:**\n"
            "• آدرس کیف پول شما در شبکه **BEP20** ذخیره شد\n"
            "• سود ماهانه به این آدرس واریز خواهد شد\n"
            "• برای تغییر آدرس به پروفایل مراجعه کنید\n\n"
            "حالا می‌توانید از منوی زیر استفاده کنید:",
            reply_markup=get_main_menu_keyboard(language),
            parse_mode="Markdown"
        )
    elif language == 'ar':
        await message.answer(
            "🎉 **اكتمل تسجيلك بنجاح!**\n\n"
            f"📋 المعلومات المسجلة:\n"
            f"👤 الاسم: {data.get('full_name')}\n"
            f"📧 البريد: {data.get('email')}\n"
            f"📱 الهاتف: {data.get('phone', 'غير مقدم')}\n"
            f"💰 المحفظة: `{wallet_address[:10]}...{wallet_address[-10:]}`\n\n"
            "⚠️ **ملاحظة:**\n"
            "• تم حفظ عنوان محفظتك على شبكة **BEP20**\n"
            "• سيتم إرسال الأرباح الشهرية إلى هذا العنوان\n"
            "• لتغيير العنوان، انتقل إلى الملف الشخصي\n\n"
            "يمكنك الآن استخدام القائمة أدناه:",
            reply_markup=get_main_menu_keyboard(language),
            parse_mode="Markdown"
        )
    else:
        await message.answer(
            "🎉 **Registration completed successfully!**\n\n"
            f"📋 Registered information:\n"
            f"👤 Name: {data.get('full_name')}\n"
            f"📧 Email: {data.get('email')}\n"
            f"📱 Phone: {data.get('phone', 'Not provided')}\n"
            f"💰 Wallet: `{wallet_address[:10]}...{wallet_address[-10:]}`\n\n"
            "⚠️ **Important:**\n"
            "• Your wallet address has been saved on **BEP20 network**\n"
            "• Monthly profits will be sent to this address\n"
            "• To change address, go to Profile\n\n"
            "Now you can use the menu below:",
            reply_markup=get_main_menu_keyboard(language),
            parse_mode="Markdown"
        )
    
    # ارسال نوتیفیکیشن به ادمین‌ها
    await send_admin_notification(message.bot, user_id, data.get('full_name', ''), 
                                  message.from_user.username, data.get('email', ''), 
                                  data.get('phone', 'Not provided'), wallet_address)

async def send_admin_notification(bot: Bot, user_id: int, full_name: str, username: str, 
                                  email: str, phone: str, wallet_address: str):
    """ارسال نوتیفیکیشن به ادمین‌ها"""
    admin_ids_str = os.getenv("ADMIN_IDS", "")
    if not admin_ids_str:
        print("⚠️ ADMIN_IDS not set in environment variables")
        return
    
    admin_ids = [int(id_str.strip()) for id_str in admin_ids_str.split(",") if id_str.strip()]
    
    for admin_id in admin_ids:
        try:
            notification_text = (
                "🆕 <b>کاربر جدید ثبت‌نام کرد!</b>\n\n"
                f"👤 <b>نام:</b> {full_name}\n"
                f"🆔 <b>شناسه:</b> <code>{user_id}</code>\n"
                f"📱 <b>یوزرنیم:</b> @{username or 'ندارد'}\n"
                f"📧 <b>ایمیل:</b> {email}\n"
                f"📞 <b>تلفن:</b> {phone}\n"
                f"💰 <b>کیف پول:</b> {wallet_address[:10]}...{wallet_address[-4:]}\n"
                f"📅 <b>زمان:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            
            await bot.send_message(
                admin_id, 
                notification_text, 
                parse_mode=ParseMode.HTML
            )
            print(f"✅ Admin notification sent to {admin_id}")
            
        except Exception as e:
            print(f"❌ Failed to send notification to admin {admin_id}: {e}")

async def cancel_registration(message: Message, state: FSMContext):
    """لغو ثبت‌نام"""
    user_id = message.from_user.id
    language = db.get_user_language(user_id)
    
    await state.clear()
    
    if language == 'fa':
        await message.answer("❌ ثبت‌نام لغو شد. برای شروع مجدد /start را بفرستید.")
    elif language == 'ar':
        await message.answer("❌ تم إلغاء التسجيل. أرسل /start للبدء من جديد.")
    else:
        await message.answer("❌ Registration cancelled. Send /start to begin again.")
