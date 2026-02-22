# handlers/referral.py
from aiogram import F, Router, Bot
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from datetime import datetime
import os

from database import Database

router = Router()
db = Database()

def get_referral_keyboard(language='fa'):
    """کیبورد منوی رفرال"""
    if language == 'fa':
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🔗 لینک دعوت من")],
                [KeyboardButton(text="📊 آمار دعوت‌ها")],
                [KeyboardButton(text="🔙 بازگشت")]
            ],
            resize_keyboard=True
        )
    elif language == 'ar':
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🔗 رابطتي")],
                [KeyboardButton(text="📊 الإحصائيات")],
                [KeyboardButton(text="🔙 رجوع")]
            ],
            resize_keyboard=True
        )
    else:
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🔗 My Referral Link")],
                [KeyboardButton(text="📊 Referral Stats")],
                [KeyboardButton(text="🔙 Back")]
            ],
            resize_keyboard=True
        )

def get_referral_texts(language):
    """متن‌های مربوط به رفرال"""
    texts = {
        'fa': {
            'menu': "🎁 **سیستم دعوت از دوستان**\n\n"
                    "با دعوت از دوستان خود، از مزایای ویژه بهره‌مند شوید:\n\n"
                    "✨ **مزایای دعوت:**\n"
                    "• دریافت پاداش برای هر دعوت موفق\n"
                    "• درصدی از سود سرمایه‌گذاری دوستان\n"
                    "• پاداش‌های ویژه ماهانه\n\n"
                    "لطفاً یک گزینه را انتخاب کنید:",
            
            'link': "🔗 **لینک دعوت اختصاصی شما**\n\n"
                    "این لینک را برای دوستان خود ارسال کنید:\n"
                    "`{link}`\n\n"
                    "📊 **آمار شما:**\n"
                    "• تعداد دعوت‌ها: {total}\n"
                    "• دعوت‌های فعال: {active}\n"
                    "• مجموع سرمایه‌گذاری: ${total_invested:.2f}\n\n"
                    "✅ هر نفر که از طریق لینک شما ثبت‌نام کند، دعوت موفق محسوب می‌شود.",
            
            'stats': "📊 **آمار دعوت‌های شما**\n\n"
                     "👥 **لیست دوستان دعوت شده:**\n{referrals_list}\n"
                     "📈 **مجموع:** {total} دعوت",
            
            'no_referrals': "📭 شما هنوز کسی را دعوت نکرده‌اید.\n"
                            "از بخش 'لینک دعوت من' لینک خود را دریافت کنید.",
            
            'referral_item': "• {full_name} - {date} - 💰 سرمایه: ${invested:.2f}\n",
            'back': "🔙 بازگشت به منوی اصلی"
        },
        'en': {
            'menu': "🎁 **Referral System**\n\n"
                    "Invite your friends and enjoy special benefits:\n\n"
                    "✨ **Benefits:**\n"
                    "• Reward for each successful referral\n"
                    "• Percentage of friends' investment profits\n"
                    "• Special monthly bonuses\n\n"
                    "Please choose an option:",
            
            'link': "🔗 **Your Personal Referral Link**\n\n"
                    "Send this link to your friends:\n"
                    "`{link}`\n\n"
                    "📊 **Your Stats:**\n"
                    "• Total Referrals: {total}\n"
                    "• Active Referrals: {active}\n"
                    "• Total Investment: ${total_invested:.2f}\n\n"
                    "✅ Anyone who registers through your link counts as a successful referral.",
            
            'stats': "📊 **Your Referral Statistics**\n\n"
                     "👥 **Referred Friends:**\n{referrals_list}\n"
                     "📈 **Total:** {total} referrals",
            
            'no_referrals': "📭 You haven't invited anyone yet.\n"
                            "Get your link from 'My Referral Link' section.",
            
            'referral_item': "• {full_name} - {date} - 💰 Investment: ${invested:.2f}\n",
            'back': "🔙 Back to main menu"
        },
        'ar': {
            'menu': "🎁 **نظام دعوة الأصدقاء**\n\n"
                    "ادعُ أصدقائك واستمتع بمزايا خاصة:\n\n"
                    "✨ **المزايا:**\n"
                    "• مكافأة لكل دعوة ناجحة\n"
                    "• نسبة من أرباح استثمارات الأصدقاء\n"
                    "• مكافآت شهرية خاصة\n\n"
                    "الرجاء اختيار خيار:",
            
            'link': "🔗 **رابط الدعوة الخاص بك**\n\n"
                    "أرسل هذا الرابط لأصدقائك:\n"
                    "`{link}`\n\n"
                    "📊 **إحصائياتك:**\n"
                    "• إجمالي الدعوات: {total}\n"
                    "• الدعوات النشطة: {active}\n"
                    "• إجمالي الاستثمار: ${total_invested:.2f}\n\n"
                    "✅ كل شخص يسجل عبر رابطك يعتبر دعوة ناجحة.",
            
            'stats': "📊 **إحصائيات دعواتك**\n\n"
                     "👥 **الأصدقاء المدعوون:**\n{referrals_list}\n"
                     "📈 **الإجمالي:** {total} دعوات",
            
            'no_referrals': "📭 لم تدع أحداً بعد.\n"
                            "احصل على رابطك من قسم 'رابط الدعوة الخاص بي'.",
            
            'referral_item': "• {full_name} - {date} - 💰 الاستثمار: ${invested:.2f}\n",
            'back': "🔙 العودة إلى القائمة الرئيسية"
        }
    }
    return texts.get(language, texts['en'])

@router.message(F.text.in_(["🎁 Invite Friends", "🎁 دعوت از دوستان", "🎁 دعوة الأصدقاء"]))
async def referral_menu(message: Message):
    """منوی اصلی رفرال"""
    user_id = message.from_user.id
    
    # اول چک کن کاربر اصلاً ثبت‌نام کرده یا نه
    user = db.get_user(user_id)
    if not user or not user[2]:  # user[2] = full_name
        language = db.get_user_language(user_id) or 'en'
        if language == 'fa':
            await message.answer("❌ لطفاً ابتدا ثبت‌نام کنید. /start را بزنید.")
        elif language == 'ar':
            await message.answer("❌ الرجاء التسجيل أولاً. أرسل /start")
        else:
            await message.answer("❌ Please register first. Send /start")
        return
    
    language = db.get_user_language(user_id)
    texts = get_referral_texts(language)
    
    # مطمئن شویم کاربر کد رفرال دارد
    db.get_user_referral_code(user_id)
    
    await message.answer(
        texts['menu'],
        reply_markup=get_referral_keyboard(language)
    )

@router.message(F.text.in_(["🔗 لینک دعوت من", "🔗 My Referral Link", "🔗 رابطتي"]))
async def show_referral_link(message: Message):
    """نمایش لینک دعوت کاربر"""
    user_id = message.from_user.id
    language = db.get_user_language(user_id)
    texts = get_referral_texts(language)
    
    # دریافت کد رفرال
    code = db.get_user_referral_code(user_id)
    print(f"🔍 User {user_id} has referral code: {code}")
    
    # ساخت لینک
    bot_username = (await message.bot.me()).username
    referral_link = f"https://t.me/{bot_username}?start=ref_{code}"
    
    # آمار
    stats = db.get_referral_stats(user_id)
    
    await message.answer(
        texts['link'].format(
            link=referral_link,
            total=stats['total'],
            active=stats['active'],
            total_invested=stats['total_invested']
        ),
        parse_mode="Markdown"
    )

@router.message(F.text.in_(["📊 آمار دعوت‌ها", "📊 Referral Stats", "📊 الإحصائيات"]))
async def show_referral_stats(message: Message):
    """نمایش آمار دعوت‌ها"""
    user_id = message.from_user.id
    language = db.get_user_language(user_id)
    texts = get_referral_texts(language)
    
    referrals = db.get_user_referrals(user_id)
    
    if not referrals:
        await message.answer(texts['no_referrals'])
        return
    
    referrals_list = ""
    for ref in referrals:
        referred_id, full_name, reg_date, invested = ref
        date_str = reg_date[:10] if reg_date else "Unknown"
        name = full_name or f"User {referred_id}"
        
        referrals_list += texts['referral_item'].format(
            full_name=name,
            date=date_str,
            invested=invested
        )
    
    await message.answer(
        texts['stats'].format(
            referrals_list=referrals_list,
            total=len(referrals)
        )
    )

@router.message(F.text.in_(["🔙 بازگشت", "🔙 Back", "🔙 رجوع"]))
async def back_to_main_from_referral(message: Message):
    """بازگشت به منوی اصلی"""
    user_id = message.from_user.id
    language = db.get_user_language(user_id)
    
    from keyboards.main_menu import get_main_menu_keyboard
    await message.answer(
        "🔙 بازگشت به منوی اصلی" if language == 'fa' else 
        "🔙 Back to main menu" if language == 'en' else 
        "🔙 العودة إلى القائمة الرئيسية",
        reply_markup=get_main_menu_keyboard(language)
    )
