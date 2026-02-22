from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_main_menu_keyboard(language='en'):
    """منوی اصلی بر اساس زبان کاربر"""
    if language == 'fa':
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="💰 سرمایه‌گذاری"), KeyboardButton(text="👤 پروفایل")],
                [KeyboardButton(text="🎁 دعوت از دوستان"), KeyboardButton(text="ℹ️ درباره ما")],
                [KeyboardButton(text="🆘 پشتیبانی"), KeyboardButton(text="⚙️ تنظیمات")]
            ],
            resize_keyboard=True
        )
    elif language == 'ar':
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="💰 استثمار"), KeyboardButton(text="👤 الملف الشخصي")],
                [KeyboardButton(text="🎁 دعوة الأصدقاء"), KeyboardButton(text="ℹ️ من نحن")],
                [KeyboardButton(text="🆘 الدعم"), KeyboardButton(text="⚙️ الإعدادات")]
            ],
            resize_keyboard=True
        )
    else:  # انگلیسی
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="💰 Investment"), KeyboardButton(text="👤 Profile")],
                [KeyboardButton(text="🎁 Invite Friends"), KeyboardButton(text="ℹ️ About")],
                [KeyboardButton(text="🆘 Support"), KeyboardButton(text="⚙️ Settings")]
            ],
            resize_keyboard=True
        )

def get_back_keyboard(language='en'):
    """دکمه بازگشت"""
    if language == 'fa':
        return ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="🔙 بازگشت")]],
            resize_keyboard=True
        )
    elif language == 'ar':
        return ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="🔙 رجوع")]],
            resize_keyboard=True
        )
    else:
        return ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="🔙 Back")]],
            resize_keyboard=True
        )
