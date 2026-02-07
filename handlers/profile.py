from aiogram import F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import Database
from keyboards.main_menu import get_main_menu_keyboard, get_back_keyboard
from handlers.start import get_phone_keyboard  # برای دکمه اشتراک‌گذاری شماره

db = Database()

class ProfileStates(StatesGroup):
    waiting_for_new_name = State()
    waiting_for_new_email = State()
    waiting_for_new_phone = State()
    waiting_for_new_wallet = State()

def get_profile_keyboard(language='en'):
    """منوی پروفایل"""
    if language == 'fa':
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="👁️ مشاهده اطلاعات")],
                [KeyboardButton(text="✏️ ویرایش اطلاعات")],
                [KeyboardButton(text="🔙 بازگشت")]
            ],
            resize_keyboard=True
        )
    else:
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="👁️ View Profile")],
                [KeyboardButton(text="✏️ Edit Profile")],
                [KeyboardButton(text="🔙 Back")]
            ],
            resize_keyboard=True
        )

def get_edit_profile_keyboard(language='en'):
    """منوی ویرایش پروفایل"""
    if language == 'fa':
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="✏️ ویرایش نام")],
                [KeyboardButton(text="📧 ویرایش ایمیل")],
                [KeyboardButton(text="📱 ویرایش تلفن")],
                [KeyboardButton(text="💰 ویرایش کیف پول")],
                [KeyboardButton(text="🔙 بازگشت")]
            ],
            resize_keyboard=True
        )
    else:
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="✏️ Edit Name")],
                [KeyboardButton(text="📧 Edit Email")],
                [KeyboardButton(text="📱 Edit Phone")],
                [KeyboardButton(text="💰 Edit Wallet")],
                [KeyboardButton(text="🔙 Back")]
            ],
            resize_keyboard=True
        )

async def profile_menu(message: Message, state: FSMContext):
    """منوی پروفایل"""
    user_id = message.from_user.id
    language = db.get_user_language(user_id)
    
    if language == 'fa':
        await message.answer(
            "👤 **منوی پروفایل**\n\n"
            "لطفاً یک گزینه را انتخاب کنید:",
            reply_markup=get_profile_keyboard(language)
        )
    else:
        await message.answer(
            "👤 **Profile Menu**\n\n"
            "Please choose an option:",
            reply_markup=get_profile_keyboard(language)
        )

async def view_profile(message: Message):
    """مشاهده اطلاعات پروفایل"""
    user_id = message.from_user.id
    user = db.get_user(user_id)
    language = db.get_user_language(user_id)
    
    if user:
        user_id, lang, full_name, email, phone, wallet, balance, registered_at = user
        
        if language == 'fa':
            text = (
                f"👤 **اطلاعات پروفایل شما:**\n\n"
                f"🔹 **نام:** {full_name or 'ثبت نشده'}\n"
                f"🔹 **ایمیل:** {email or 'ثبت نشده'}\n"
                f"🔹 **تلفن:** {phone or 'ثبت نشده'}\n"
                f"🔹 **کیف پول:** `{wallet[:10]}...{wallet[-10:] if wallet and len(wallet) > 20 else ''}`\n"
                f"🔹 **موجودی:** ${balance:.2f}\n"
                f"🔹 **تاریخ ثبت‌نام:** {registered_at[:10]}\n\n"
                f"💰 **آدرس کیف پول در شبکه BEP20 ذخیره شده است**"
            )
        else:
            text = (
                f"👤 **Your Profile Information:**\n\n"
                f"🔹 **Name:** {full_name or 'Not set'}\n"
                f"🔹 **Email:** {email or 'Not set'}\n"
                f"🔹 **Phone:** {phone or 'Not set'}\n"
                f"🔹 **Wallet:** `{wallet[:10]}...{wallet[-10:] if wallet and len(wallet) > 20 else ''}`\n"
                f"🔹 **Balance:** ${balance:.2f}\n"
                f"🔹 **Registration Date:** {registered_at[:10]}\n\n"
                f"💰 **Wallet address saved on BEP20 network**"
            )
        
        await message.answer(text, parse_mode="Markdown")
    else:
        if language == 'fa':
            await message.answer("❌ اطلاعات شما یافت نشد. لطفاً /start را بفرستید.")
        else:
            await message.answer("❌ Your data not found. Please send /start.")

async def edit_profile_menu(message: Message):
    """منوی ویرایش پروفایل"""
    user_id = message.from_user.id
    language = db.get_user_language(user_id)
    
    if language == 'fa':
        await message.answer(
            "✏️ **ویرایش اطلاعات پروفایل**\n\n"
            "چه اطلاعاتی را می‌خواهید ویرایش کنید؟",
            reply_markup=get_edit_profile_keyboard(language)
        )
    else:
        await message.answer(
            "✏️ **Edit Profile Information**\n\n"
            "What would you like to edit?",
            reply_markup=get_edit_profile_keyboard(language)
        )

# --- ویرایش نام ---
async def edit_name_start(message: Message, state: FSMContext):
    """شروع ویرایش نام"""
    user_id = message.from_user.id
    language = db.get_user_language(user_id)
    
    if language == 'fa':
        await message.answer("لطفاً نام جدید خود را وارد کنید:")
    else:
        await message.answer("Please enter your new name:")
    
    await state.set_state(ProfileStates.waiting_for_new_name)

async def edit_name_finish(message: Message, state: FSMContext):
    """اتمام ویرایش نام"""
    user_id = message.from_user.id
    language = db.get_user_language(user_id)
    
    # به روزرسانی نام در دیتابیس
    cursor = db.conn.cursor()
    cursor.execute("UPDATE users SET full_name = ? WHERE user_id = ?", (message.text, user_id))
    db.conn.commit()
    
    await state.clear()
    
    if language == 'fa':
        await message.answer("✅ نام شما با موفقیت به‌روز شد!", reply_markup=get_profile_keyboard(language))
    else:
        await message.answer("✅ Your name has been updated successfully!", reply_markup=get_profile_keyboard(language))

# --- ویرایش ایمیل ---
async def edit_email_start(message: Message, state: FSMContext):
    """شروع ویرایش ایمیل"""
    user_id = message.from_user.id
    language = db.get_user_language(user_id)
    
    if language == 'fa':
        await message.answer("لطفاً ایمیل جدید خود را وارد کنید:")
    else:
        await message.answer("Please enter your new email:")
    
    await state.set_state(ProfileStates.waiting_for_new_email)

async def edit_email_finish(message: Message, state: FSMContext):
    """اتمام ویرایش ایمیل"""
    user_id = message.from_user.id
    language = db.get_user_language(user_id)
    
    # اعتبارسنجی ایمیل
    if '@' not in message.text or '.' not in message.text:
        if language == 'fa':
            await message.answer("⚠️ ایمیل نامعتبر است. لطفاً ایمیل صحیح وارد کنید:")
        else:
            await message.answer("⚠️ Invalid email. Please enter a valid email:")
        return
    
    # به روزرسانی ایمیل در دیتابیس
    cursor = db.conn.cursor()
    cursor.execute("UPDATE users SET email = ? WHERE user_id = ?", (message.text, user_id))
    db.conn.commit()
    
    await state.clear()
    
    if language == 'fa':
        await message.answer("✅ ایمیل شما با موفقیت به‌روز شد!", reply_markup=get_profile_keyboard(language))
    else:
        await message.answer("✅ Your email has been updated successfully!", reply_markup=get_profile_keyboard(language))

# --- ویرایش تلفن ---
async def edit_phone_start(message: Message, state: FSMContext):
    """شروع ویرایش تلفن"""
    user_id = message.from_user.id
    language = db.get_user_language(user_id)
    
    if language == 'fa':
        await message.answer(
            "لطفاً شماره تلفن جدید خود را وارد کنید یا از دکمه اشتراک‌گذاری استفاده کنید:",
            reply_markup=get_phone_keyboard(language)
        )
    else:
        await message.answer(
            "Please enter your new phone number or use the share button:",
            reply_markup=get_phone_keyboard(language)
        )
    
    await state.set_state(ProfileStates.waiting_for_new_phone)

async def edit_phone_finish(message: Message, state: FSMContext):
    """اتمام ویرایش تلفن"""
    user_id = message.from_user.id
    language = db.get_user_language(user_id)
    
    # بررسی اگر کاربر skip زد
    if message.text in ["⏭️ رد کردن", "⏭️ Skip"]:
        phone = "Not provided"
    elif message.contact:
        # اگر از دکمه اشتراک‌گذاری استفاده کرد
        phone = message.contact.phone_number
    else:
        phone = message.text
    
    # به روزرسانی تلفن در دیتابیس
    cursor = db.conn.cursor()
    cursor.execute("UPDATE users SET phone = ? WHERE user_id = ?", (phone, user_id))
    db.conn.commit()
    
    await state.clear()
    
    if language == 'fa':
        await message.answer("✅ شماره تلفن شما با موفقیت به‌روز شد!", reply_markup=get_profile_keyboard(language))
    else:
        await message.answer("✅ Your phone number has been updated successfully!", reply_markup=get_profile_keyboard(language))

# --- ویرایش کیف پول ---
async def edit_wallet_start(message: Message, state: FSMContext):
    """شروع ویرایش کیف پول"""
    user_id = message.from_user.id
    language = db.get_user_language(user_id)
    
    if language == 'fa':
        await message.answer(
            "💰 **لطفاً آدرس کیف پول جدید خود را وارد کنید:**\n\n"
            "⚠️ **توجه مهم:**\n"
            "• این آدرس باید در شبکه **BEP20** باشد\n"
            "• سود ماهانه شما به این آدرس واریز خواهد شد\n"
            "• لطفاً در وارد کردن آدرس دقت کنید\n\n"
            "مثال: 0x742d35Cc6634C0532925a3b844Bc9e..."
        )
    else:
        await message.answer(
            "💰 **Please enter your new wallet address:**\n\n"
            "⚠️ **Important:**\n"
            "• This address must be on the **BEP20 network**\n"
            "• Your monthly profits will be sent to this address\n"
            "• Please double-check the address\n\n"
            "Example: 0x742d35Cc6634C0532925a3b844Bc9e..."
        )
    
    await state.set_state(ProfileStates.waiting_for_new_wallet)

async def edit_wallet_finish(message: Message, state: FSMContext):
    """اتمام ویرایش کیف پول"""
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
        else:
            await message.answer(
                "⚠️ Invalid wallet address!\n"
                "Address must start with '0x' and be at least 20 characters.\n"
                "Please enter again:"
            )
        return
    
    # به روزرسانی کیف پول در دیتابیس
    cursor = db.conn.cursor()
    cursor.execute("UPDATE users SET wallet_address = ? WHERE user_id = ?", (wallet_address, user_id))
    db.conn.commit()
    
    await state.clear()
    
    if language == 'fa':
        await message.answer(
            "✅ آدرس کیف پول شما با موفقیت به‌روز شد!\n\n"
            "⚠️ **توجه:** آدرس جدید در شبکه BEP20 ذخیره شد.",
            reply_markup=get_profile_keyboard(language)
        )
    else:
        await message.answer(
            "✅ Your wallet address has been updated successfully!\n\n"
            "⚠️ **Important:** New address saved on BEP20 network.",
            reply_markup=get_profile_keyboard(language)
        )