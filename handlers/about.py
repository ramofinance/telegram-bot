# handlers/about.py
from aiogram import F, Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
import asyncio

from database import Database

router = Router()
db = Database()

@router.message(F.text.in_(["ℹ️ About", "ℹ️ درباره ما", "ℹ️ من نحن"]))
async def about_command(message: Message):
    """دستور درباره ما"""
    user_id = message.from_user.id
    language = db.get_user_language(user_id)
    
    if language == "fa":
        await send_farsi_about(message)
    elif language == "en":
        await send_english_about(message)
    elif language == "ar":
        await send_arabic_about(message)
    else:
        await send_english_about(message)  # پیش‌فرض انگلیسی

async def send_farsi_about(message: Message):
    """ارسال متن درباره ما به فارسی"""
    about_part1 = (
        "🌐 **درباره RAMO FINANCE**\n\n"
        "RAMO FINANCE یک مجموعه تخصصی در حوزه بازارهای مالی است که فعالیت خود را با تمرکز بر 📊 تحلیل حرفه‌ای، 📈 مدیریت سرمایه و ارائه راهکارهای نوین سرمایه‌گذاری آغاز کرده است.\n\n"
        "👥 **تیم ما** متشکل از تحلیل‌گران و متخصصانی است که دارای چندین سال سابقه فعالیت عملی در بازارهای بین‌المللی هستند و تصمیم‌گیری‌های خود را همواره بر پایه داده، استراتژی و ⚖️ مدیریت ریسک انجام می‌دهند."
    )
    
    about_part2 = (
        "🤖 **بخشی از معاملات** این مجموعه به‌صورت کاملاً هوشمند انجام می‌شود. این معاملات توسط اکسپرت تریدینگ پیشرفته و اختصاصی RAMO FINANCE اجرا می‌گردد که بر پایه تحلیل داده، منطق الگوریتمی و مدیریت ریسک طراحی شده است.\n\n"
        "🔍 **شفافیت و ساختار حرفه‌ای** از اصول اصلی RAMO FINANCE است. به همین دلیل و با توجه به اطمینان این مجموعه به عملکرد سیستم معاملاتی خود، لینک MyFxBook مربوط به حسابی که معاملات آن توسط این اکسپرت انجام می‌شود در اختیار کاربران قرار می‌گیرد تا امکان بررسی عملکرد واقعی معاملات به‌صورت کاملاً شفاف فراهم باشد."
    )
    
    about_part3 = (
        "✅ **خدمات ما:**\n"
        "• 📈 سرمایه‌گذاری با سود ماهانه\n"
        "• 🔒 امنیت بالا و پشتیبانی شبکه BEP20\n"
        "• 📊 پنل مدیریت پیشرفته\n"
        "• 👥 پشتیبانی ۲۴/۷\n\n"
        
        "💼 **شرایط سرمایه‌گذاری:**\n"
        "💰 **حداقل سرمایه:** 1,000 دلار\n\n"
        
        "📈 **نرخ سود ماهانه:**\n"
        "• 🟢 ۴٪ ماهانه: برای سرمایه 1,000 تا 10,000 دلار\n"
        "• 🔵 ۵٪ ماهانه: برای سرمایه 10,000 دلار به بالا\n\n"
        
        "📋 **مراحل سرمایه‌گذاری:**\n"
        "1. واریز مبلغ به کیف پول شرکت\n"
        "2. تایید توسط پشتیبانی\n"
        "3. شروع محاسبه سود از روز بعد\n"
        "4. پرداخت سود ماهانه به کیف پول شما\n\n"
        
        "⚠️ **توجه:**\n"
        "• سود هر ماه به کیف پول BEP20 شما واریز می‌شود\n"
        "• امکان برداشت اصل سرمایه پس از ۳ ماه\n"
        "• پشتیبانی ۲۴ ساعته"
    )
    
    await message.answer(about_part1)
    await asyncio.sleep(0.5)
    await message.answer(about_part2)
    await asyncio.sleep(0.5)
    await message.answer(about_part3)

async def send_english_about(message: Message):
    """ارسال متن درباره ما به انگلیسی"""
    about_part1 = (
        "🌐 **About RAMO FINANCE**\n\n"
        "RAMO FINANCE is a professional financial group focused on 📊 advanced market analysis, 📈 capital management, and innovative investment solutions.\n\n"
        "👥 **Our team** consists of experienced analysts and specialists with extensive hands-on experience in international financial markets. All decisions are made based on data-driven strategies and ⚖️ professional risk management."
    )
    
    about_part2 = (
        "🤖 **A portion of our trading activities** is executed automatically through a proprietary and fully intelligent Expert Advisor, developed using algorithmic logic, data analysis, and structured risk management.\n\n"
        "🔍 **Transparency and professionalism** are core values at RAMO FINANCE. Therefore, and due to our confidence in the performance of our trading system, a MyFxBook link for the account traded by this expert is provided to users, allowing independent and transparent performance verification."
    )
    
    about_part3 = (
        "✅ **Our Services:**\n"
        "• 📈 Monthly profit investment\n"
        "• 🔒 High security with BEP20 network support\n"
        "• 📊 Advanced management panel\n"
        "• 👥 24/7 support\n\n"
        
        "💼 **Investment Conditions:**\n"
        "💰 **Minimum Investment:** $1,000\n\n"
        
        "📈 **Monthly Profit Rates:**\n"
        "• 🟢 4% monthly: For $1,000 to $10,000 investment\n"
        "• 🔵 5% monthly: For $10,000+ investment\n\n"
        
        "📋 **Investment Process:**\n"
        "1. Deposit to company wallet\n"
        "2. Confirmation by support\n"
        "3. Profit calculation starts next day\n"
        "4. Monthly profit sent to your wallet\n\n"
        
        "⚠️ **Important:**\n"
        "• Profit sent monthly to your BEP20 wallet\n"
        "• Principal withdrawal possible after 3 months\n"
        "• 24/7 support available"
    )
    
    await message.answer(about_part1)
    await asyncio.sleep(0.5)
    await message.answer(about_part2)
    await asyncio.sleep(0.5)
    await message.answer(about_part3)

async def send_arabic_about(message: Message):
    """ارسال متن درباره ما به عربی"""
    about_part1 = (
        "🌐 **عن RAMO FINANCE**\n\n"
        "RAMO FINANCE هي مجموعة متخصصة في الأسواق المالية، تركز على 📊 التحليل الاحترافي، 📈 إدارة رأس المال، وتقديم حلول استثمارية حديثة.\n\n"
        "👥 **يضم فريقنا** محللين وخبراء يمتلكون خبرة عملية واسعة في الأسواق المالية العالمية، حيث تعتمد جميع القرارات على البيانات والاستراتيجيات المدروسة و ⚖️ إدارة المخاطر الاحترافية."
    )
    
    about_part2 = (
        "🤖 **يتم تنفيذ جزء من عمليات التداول** بشكل آلي بالكامل من خلال إكسبيرت تداول ذكي ومطوّر خصيصًا، يعتمد على التحليل الخوارزمي والبيانات وإدارة المخاطر.\n\n"
        "🔍 **الشفافية والاحترافية** من القيم الأساسية في RAMO FINANCE، ولذلك وبناءً على الثقة في أداء النظام التداولي، يتم توفير رابط MyFxBook للحساب الذي يتم التداول عليه بواسطة هذا الإكسبيرت لتمكين المستخدمين من متابعة الأداء الحقيقي بكل وضوح."
    )
    
    about_part3 = (
        "✅ **خدماتنا:**\n"
        "• 📈 استثمار بربح شهري\n"
        "• 🔒 أمان عالي مع دعم شبكة BEP20\n"
        "• 📊 لوحة إدارة متقدمة\n"
        "• 👥 دعم على مدار الساعة\n\n"
        
        "💼 **شروط الاستثمار:**\n"
        "💰 **الحد الأدنى للاستثمار:** 1,000 دولار\n\n"
        
        "📈 **معدلات الربح الشهري:**\n"
        "• 🟢 ٤٪ شهرياً: للاستثمار من 1,000 إلى 10,000 دولار\n"
        "• 🔵 ٥٪ شهرياً: للاستثمار فوق 10,000 دولار\n\n"
        
        "📋 **خطوات الاستثمار:**\n"
        "1. إيداع المبلغ في محفظة الشركة\n"
        "2. التأكيد من الدعم الفني\n"
        "3. بدء حساب الربح من اليوم التالي\n"
        "4. إرسال الربح الشهري إلى محفظتك\n\n"
        
        "⚠️ **ملاحظة:**\n"
        "• يتم إرسال الربح كل شهر إلى محفظتك BEP20\n"
        "• يمكن سحب رأس المال بعد 3 أشهر\n"
        "• دعم فني على مدار 24 ساعة"
    )
    
    await message.answer(about_part1)
    await asyncio.sleep(0.5)
    await message.answer(about_part2)
    await asyncio.sleep(0.5)
    await message.answer(about_part3)