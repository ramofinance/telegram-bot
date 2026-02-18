# handlers/investment.py
from aiogram import F, Router, Bot
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, ContentType
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime, timedelta
import os

from database import Database

router = Router()
db = Database()

class InvestmentStates(StatesGroup):
    waiting_for_amount = State()
    waiting_for_confirmation = State()
    waiting_for_terms_agreement = State()  # مرحله جدید - قوانین
    waiting_for_wallet_payment = State()
    waiting_for_transaction_receipt = State()

def is_admin(user_id: int) -> bool:
    """بررسی اینکه کاربر ادمین هست یا نه"""
    admin_ids_str = os.getenv("ADMIN_IDS", "")
    if admin_ids_str:
        admin_ids = [int(id_str.strip()) for id_str in admin_ids_str.split(",") if id_str.strip()]
        return user_id in admin_ids
    return False

def get_investment_keyboard(language='fa'):
    """منوی سرمایه‌گذاری"""
    if language == 'fa':
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="💰 سرمایه‌گذاری جدید")],
                [KeyboardButton(text="📊 سرمایه‌گذاری‌های من")],
                [KeyboardButton(text="💵 موجودی و سود")],
                [KeyboardButton(text="🔙 بازگشت")]
            ],
            resize_keyboard=True
        )
    elif language == 'ar':
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="💰 استثمار جديد")],
                [KeyboardButton(text="📊 استثماراتي")],
                [KeyboardButton(text="💵 الرصيد والربح")],
                [KeyboardButton(text="🔙 رجوع")]
            ],
            resize_keyboard=True
        )
    else:
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="💰 New Investment")],
                [KeyboardButton(text="📊 My Investments")],
                [KeyboardButton(text="💵 Balance & Profit")],
                [KeyboardButton(text="🔙 Back")]
            ],
            resize_keyboard=True
        )

def get_receipt_keyboard(language='fa'):
    """کیبورد برای ارسال رسید"""
    if language == 'fa':
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📤 ارسال رسید تراکنش")],
                [KeyboardButton(text="⏭️ بدون رسید")]
            ],
            resize_keyboard=True,
            one_time_keyboard=True
        )
    elif language == 'ar':
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📤 إرسال إيصال المعاملة")],
                [KeyboardButton(text="⏭️ بدون إيصال")]
            ],
            resize_keyboard=True,
            one_time_keyboard=True
        )
    else:
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📤 Send Transaction Receipt")],
                [KeyboardButton(text="⏭️ No Receipt")]
            ],
            resize_keyboard=True,
            one_time_keyboard=True
        )

def calculate_annual_profit_percentage(amount: float) -> float:
    """محاسبه درصد سود سالانه بر اساس مبلغ"""
    if amount < 500:
        return 0
    elif amount <= 5000:
        return 50  # 50% سالانه
    elif amount <= 10000:
        return 60  # 60% سالانه
    else:
        return 70  # 70% سالانه

def calculate_monthly_profit_from_annual(amount: float, annual_percentage: float) -> float:
    """محاسبه سود ماهانه از سود سالانه"""
    # سود سالانه تقسیم بر 12 ماه
    annual_profit = (amount * annual_percentage) / 100
    monthly_profit = annual_profit / 12
    return monthly_profit

def calculate_monthly_profit_percentage(annual_percentage: float) -> float:
    """محاسبه درصد سود ماهانه از درصد سالانه"""
    # درصد سالانه تقسیم بر 12
    return annual_percentage / 12

def get_investment_texts(language):
    """متن‌های سرمایه‌گذاری بر اساس زبان"""
    texts = {
        'fa': {
            'menu': "💰 **سیستم سرمایه‌گذاری**\n\n📊 **شرایط سرمایه‌گذاری:**\n• حداقل سرمایه: ۵۰۰ دلار\n• سود سالانه با پرداخت ماهانه:\n   🟢 ۵۰٪ سالانه: برای ۵۰۰ تا ۵,۰۰۰ دلار\n   🔵 ۶۰٪ سالانه: برای ۵,۰۰۰ تا ۱۰,۰۰۰ دلار\n   🟣 ۷۰٪ سالانه: برای بالای ۱۰,۰۰۰ دلار\n\n📋 **مراحل:**\n1. انتخاب مبلغ سرمایه‌گذاری\n2. مطالعه و پذیرش قوانین\n3. دریافت آدرس کیف پول برای واریز\n4. واریز مبلغ\n5. ارسال رسید تراکنش\n6. تایید توسط پشتیبانی\n7. شروع محاسبه سود\n\nلطفاً یک گزینه را انتخاب کنید:",
            'no_wallet': "⚠️ **لطفاً ابتدا آدرس کیف پول خود را ثبت کنید!**\n\nبرای سرمایه‌گذاری نیاز دارید آدرس کیف پول BEP20 خود را در پروفایل ثبت کنید.\n\n🔹 به پروفایل بروید\n🔹 روی 'ویرایش کیف پول' کلیک کنید\n🔹 آدرس کیف پول خود را وارد کنید\n\nسپس می‌توانید سرمایه‌گذاری کنید.",
            'enter_amount': "💰 **سرمایه‌گذاری جدید**\n\nلطفاً مبلغ سرمایه‌گذاری خود را وارد کنید (به دلار):\n\n📊 **نرخ سود سالانه (پرداخت ماهانه):**\n• 🟢 ۵۰٪ سالانه: برای ۵۰۰ تا ۵,۰۰۰ دلار\n• 🔵 ۶۰٪ سالانه: برای ۵,۰۰۰ تا ۱۰,۰۰۰ دلار\n• 🟣 ۷۰٪ سالانه: برای بالای ۱۰,۰۰۰ دلار\n\n💰 **محاسبه پرداخت ماهانه:**\n(سود سالانه تقسیم بر ۱۲ ماه)\n• 🟢 ~۴.۱۷٪ ماهانه\n• 🔵 ~۵٪ ماهانه\n• 🟣 ~۵.۸۳٪ ماهانه\n\n💵 **حداقل مبلغ:** ۵۰۰ دلار\n\nمثال: ۵۰۰ یا ۷۵۰۰ یا ۱۵۰۰۰",
            'min_amount': "⚠️ مبلغ باید حداقل ۵۰۰ دلار باشد. لطفاً مجدداً وارد کنید:",
            'invalid_amount': "⚠️ لطفاً یک عدد معتبر وارد کنید (مثال: ۵۰۰):",
            'details': "✅ **جزئیات سرمایه‌گذاری**\n\n💵 **مبلغ سرمایه‌گذاری:** ${amount:,.2f}\n📈 **نرخ سود سالانه:** {annual_percentage}%\n📊 **پرداخت ماهانه:** ~{monthly_percentage:.2f}%\n💰 **سود ماهانه:** ${monthly_profit:,.2f}\n📅 **تاریخ شروع:** فردا\n⏳ **مدت زمان:** نامحدود\n\n⚠️ **توجه:**\n• پس از تایید پرداخت، سود ماهانه محاسبه می‌شود\n• سود هر ماه به کیف پول شما واریز می‌شود\n• امکان برداشت اصل سرمایه پس از ۳ ماه\n\nآیا مایل به ادامه هستید؟",
            'confirm_yes': "✅ بله، ادامه می‌دهم",
            'confirm_no': "❌ خیر، انصراف",
            
            # متن قوانین و مقررات فارسی
            'terms_and_conditions': (
                "📜 **قوانین و مقررات سرمایه‌گذاری RAMO FINANCE**\n\n"
                "**ماده ۱ – ماهیت همکاری**\n"
                "• این همکاری به صورت مدیریت سرمایه در بازارهای مالی بین‌المللی انجام می‌شود.\n"
                "• بازارهای مالی ذاتاً دارای ریسک بوده و امکان سود و زیان وجود دارد.\n"
                "• سرمایه‌گذار با علم و آگاهی کامل از ریسک‌های موجود، سرمایه خود را در اختیار تریدر قرار می‌دهد.\n"
                "• هیچ‌گونه سود تضمین‌شده‌ای وجود ندارد.\n\n"
                
                "**ماده ۲ – نحوه انجام معاملات**\n"
                "• تریدر متعهد است معاملات را با رعایت اصول حرفه‌ای مدیریت سرمایه انجام دهد.\n"
                "• تریدر مجاز است از روش‌های مختلف معاملاتی از جمله اسپات، مارجین، فیوچرز و سایر ابزارهای مالی استفاده نماید.\n"
                "• انجام معاملات می‌تواند از طریق پلتفرم‌های داخلی یا خارجی صورت گیرد.\n"
                "• در صورت بروز شرایط خاص یا نوسانات شدید بازار، اطلاع‌رسانی انجام خواهد شد.\n"
                "• سرمایه‌گذار آگاه است که تریدر دارای مجوز رسمی مدیریت سرمایه از نهادهای مالی بین‌المللی نمی‌باشد.\n\n"
                
                "**ماده ۳ – تقسیم سود و زیان**\n"
                "• سود و زیان حاصل از معاملات بر اساس درصد توافق‌شده بین طرفین تقسیم می‌شود.\n"
                "• پرداخت سود به صورت ماهانه و از طریق شبکه BEP20 به کیف پول اعلامی سرمایه‌گذار انجام می‌گردد.\n"
                "• در صورت بروز زیان، گزارش عملکرد ارائه خواهد شد.\n"
                "• حد ضرر کلی سرمایه ۲۰٪ تعیین می‌شود و در صورت رسیدن به این سطح، فعالیت معاملاتی متوقف می‌گردد.\n\n"
                
                "**ماده ۴ – تعهدات تریدر**\n"
                "• حفظ محرمانگی اطلاعات سرمایه‌گذار\n"
                "• مدیریت حرفه‌ای سرمایه\n"
                "• ارائه گزارش در شرایط خاص\n"
                "• خودداری از هرگونه اقدام مغایر با منافع سرمایه‌گذار\n\n"
                
                "**ماده ۵ – تعهدات سرمایه‌گذار**\n"
                "• واریز سرمایه در زمان مقرر\n"
                "• عدم مداخله در فرآیند اجرایی معاملات\n"
                "• پذیرش کامل ریسک بازار\n"
                "• عدم طرح ادعا در صورت زیان، مگر در صورت اثبات تخلف یا تقصیر تریدر\n\n"
                
                "**تبصره مهم:**\n"
                "سرمایه‌گذار تأیید می‌کند که هیچ‌گونه تضمین سود از سوی تریدر دریافت نکرده و تمامی تصمیمات سرمایه‌گذاری با آگاهی کامل از ریسک بازار اتخاذ شده است.\n\n"
                
                "**ماده ۶ – فسخ همکاری**\n"
                "• هر یک از طرفین در صورت نقض تعهدات می‌تواند با اعلام کتبی و پس از ۳۰ روز همکاری را خاتمه دهد.\n"
                "• در صورت فسخ، اصل سرمایه و سود محقق‌شده تا تاریخ فسخ تسویه می‌شود.\n\n"
                
                "**ماده ۷ – فورس ماژور**\n"
                "• در صورت وقوع شرایط خارج از کنترل طرفین (جنگ، قطعی اینترنت، تحریم، اختلال زیرساختی و...) مسئولیتی متوجه طرفین نخواهد بود.\n\n"
                
                "**ماده ۸ – تغییر اطلاعات تماس**\n"
                "• هرگونه تغییر در اطلاعات تماس باید به اطلاع طرف مقابل برسد.\n\n"
                
                "📚 **مطالعه کامل قوانین:**\n"
                "🔗 برای مطالعه کامل قوانین و مقررات به زبان فارسی، به لینک زیر مراجعه کنید:\n"
                "🌐 https://github.com/ramofinance/terms-and-conditions/blob/main/fa.md\n\n"
                
                "✅ با کلیک بر روی 'قوانین را مطالعه کردم و قبول دارم'، تأیید می‌کنید که:\n"
                "• قوانین بالا را مطالعه کرده‌اید\n"
                "• با تمام شرایط موافق هستید\n"
                "• مسئولیت سرمایه‌گذاری را می‌پذیرید"
            ),
            'agree_terms': "✅ قوانین را مطالعه کردم و قبول دارم",
            'disagree_terms': "❌ انصراف از سرمایه‌گذاری",
            
            'payment': "🎯 **مرحله پرداخت**\n\n💵 **مبلغ واریز:** ${amount:,.2f}\n📈 **نرخ سود سالانه:** {annual_percentage}%\n📊 **پرداخت ماهانه:** ~{monthly_percentage:.2f}%\n💰 **سود ماهانه:** ${monthly_profit:,.2f}\n\n🔐 **آدرس کیف پول شرکت (BEP20):**\n`{company_wallet}`\n\n📋 **دستورات مهم:**\n1. فقط به آدرس بالا واریز کنید\n2. حتماً از شبکه BEP20 استفاده کنید\n3. پس از واریز، رسید تراکنش را ارسال کنید\n4. منتظر تایید پشتیبانی باشید\n\n⏰ **تایید پرداخت:** حداکثر ۲۴ ساعت\n📞 **پشتیبانی:** @YourSupportUsername\n\n✅ پس از واریز، روی دکمه '📤 ارسال رسید تراکنش' کلیک کنید.",
            'receipt_request': "📤 **لطفاً رسید تراکنش خود را ارسال کنید**\n\nمی‌توانید:\n• هش تراکنش (Transaction Hash) را به صورت متن ارسال کنید\n• یا عکس/اسکرین‌شات رسید را ارسال کنید\n\nمثال هش تراکنش:\n`0x7d5a3f5c8e1a9b0c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6`\n\n⚠️ اگر رسید ندارید، می‌توانید '⏭️ بدون رسید' را بزنید.",
            'receipt_received': "✅ **رسید تراکنش شما دریافت شد!**\n\n📋 در حال ثبت درخواست سرمایه‌گذاری شما...",
            'receipt_skip': "⏭️ **بدون رسید ادامه می‌دهم**\n\n📋 در حال ثبت درخواست سرمایه‌گذاری شما...",
            'cancel_invest': "❌ انصراف از سرمایه‌گذاری",
            'investment_submitted': "✅ **درخواست سرمایه‌گذاری شما ثبت شد!**\n\n🎯 **شناسه درخواست:** #{investment_id}\n💵 **مبلغ:** ${amount:,.2f}\n📈 **نرخ سود سالانه:** {annual_percentage}%\n📊 **پرداخت ماهانه:** ~{monthly_percentage:.2f}%\n💰 **سود ماهانه:** ${monthly_profit:,.2f}\n\n⏳ **وضعیت:** در انتظار تایید پرداخت\n📞 **پیگیری:** از طریق پشتیبانی\n⏰ **زمان تایید:** حداکثر ۲۴ ساعت\n\nپس از تایید پرداخت، سرمایه‌گذاری شما فعال می‌شود و سود ماهانه از فردا محاسبه می‌گردد.",
            'no_investments': "📭 **هیچ سرمایه‌گذاری ندارید.**",
            'investments_title': "📊 **سرمایه‌گذاری‌های شما**\n\n",
            'investment_item': "💰 **سرمایه‌گذاری #{inv_id}**\n📦 **بسته:** {package}\n💵 **مبلغ:** ${amount:,.2f}\n📈 **نرخ سود سالانه:** {annual_percentage}%\n📊 **سود ماهانه:** ${monthly_profit:,.2f}\n🎯 **وضعیت:** {status_text}\n📅 **تاریخ شروع:** {start_date}\n",
            'active_status': "✅ **در حال کسب سود**\n",
            'total_active': "📈 **مجموع سرمایه فعال:** ${total_active:,.2f}",
            'balance_title': "💰 **وضعیت مالی شما**\n\n",
            'balance_details': "💵 **موجودی حساب:** ${balance:,.2f}\n📊 **سرمایه‌گذاری فعال:** ${total_investment:,.2f}\n📈 **سود ماهانه کل:** ${total_monthly_profit:,.2f}\n🔢 **تعداد سرمایه‌گذاری‌ها:** {active_count}\n\n📋 **جزئیات:**\n• موجودی قابل برداشت: ${balance:,.2f}\n• مجموع سود ماهانه: ${total_monthly_profit:,.2f}\n• سود روزانه: ${daily_profit:,.2f}\n\n💳 **برداشت موجودی:**\nبرای برداشت موجودی، با پشتیبانی تماس بگیرید.\n📞 پشتیبانی: @YourSupportUsername",
            'back': "🔙 بازگشت به منوی سرمایه‌گذاری",
            'cancelled': "❌ سرمایه‌گذاری لغو شد.",
            'choose_option': "⚠️ لطفاً یکی از گزینه‌ها را انتخاب کنید.",
            'invalid_receipt': "⚠️ لطفاً رسید تراکنش (هش) یا عکس رسید را ارسال کنید."
        },
        'ar': {
            'menu': "💰 **نظام الاستثمار**\n\n📊 **شروط الاستثمار:**\n• الحد الأدنى للاستثمار: ٥٠٠ دولار\n• ربح سنوي مع دفع شهري:\n   🟢 ٥٠٪ سنوياً: للاستثمار من ٥٠٠ إلى ٥,٠٠٠ دولار\n   🔵 ٦٠٪ سنوياً: للاستثمار من ٥,٠٠٠ إلى ١٠,٠٠٠ دولار\n   🟣 ٧٠٪ سنوياً: للاستثمار فوق ١٠,٠٠٠ دولار\n\n📋 **الخطوات:**\n1. اختيار مبلغ الاستثمار\n2. دراسة وقبول الشروط\n3. استلام عنوان المحفظة للإيداع\n4. إيداع المبلغ\n5. إرسال إيصال المعاملة\n6. التأكيد من الدعم الفني\n7. بدء حساب الربح\n\nالرجاء اختيار خيار:",
            'no_wallet': "⚠️ **الرجاء تسجيل عنوان محفظتك أولاً!**\n\nللاستثمار تحتاج إلى تسجيل عنوان محفظتك BEP20 في الملف الشخصي.\n\n🔹 اذهب إلى الملف الشخصي\n🔹 انقر على 'تعديل المحفظة'\n🔹 أدخل عنوان محفتك\n\nثم يمكنك الاستثمار.",
            'enter_amount': "💰 **استثمار جديد**\n\nالرجاء إدخال مبلغ استثمارك (بالدولار):\n\n📊 **معدل الربح السنوي (دفع شهري):**\n• 🟢 ٥٠٪ سنوياً: للاستثمار من ٥٠٠ إلى ٥,٠٠٠ دولار\n• 🔵 ٦٠٪ سنوياً: للاستثمار من ٥,٠٠٠ إلى ١٠,٠٠٠ دولار\n• 🟣 ٧٠٪ سنوياً: للاستثمار فوق ١٠,٠٠٠ دولار\n\n💰 **حساب الدفع الشهري:**\n(الربح السنوي مقسوم على ١٢ شهر)\n• 🟢 ~٤.١٧٪ شهرياً\n• 🔵 ~٥٪ شهرياً\n• 🟣 ~٥.٨٣٪ شهرياً\n\n💵 **الحد الأدنى:** ٥٠٠ دولار\n\nمثال: ٥٠٠ أو ٧٥٠٠ أو ١٥٠٠٠",
            'min_amount': "⚠️ يجب أن يكون المبلغ ٥٠٠ دولار على الأقل. الرجاء إعادة الإدخال:",
            'invalid_amount': "⚠️ الرجاء إدخال رقم صحيح (مثال: ٥٠٠):",
            'details': "✅ **تفاصيل الاستثمار**\n\n💵 **مبلغ الاستثمار:** ${amount:,.2f}\n📈 **معدل الربح السنوي:** {annual_percentage}%\n📊 **الدفع الشهري:** ~{monthly_percentage:.2f}%\n💰 **الربح الشهري:** ${monthly_profit:,.2f}\n📅 **تاريخ البدء:** غداً\n⏳ **المدة:** غير محدودة\n\n⚠️ **ملاحظة:**\n• بعد تأكيد الدفع، يبدأ حساب الربح الشهري\n• يتم إرسال الربح كل شهر إلى محفظتك\n• يمكن سحب رأس المال بعد ۳ شهراً\n\nهل ترغب في المتابعة؟",
            'confirm_yes': "✅ نعم، أتابع",
            'confirm_no': "❌ لا، إلغاء",
            
            # Arabic terms and conditions
            'terms_and_conditions': (
                "📜 **شروط وأحكام الاستثمار RAMO FINANCE**\n\n"
                "**المادة ۱ – طبيعة التعاون**\n"
                "• يتم هذا التعاون على أساس إدارة رأس المال في الأسواق المالية الدولية.\n"
                "• الأسواق المالية تنطوي بطبيعتها على مخاطر، ومن الممكن تحقيق الربح أو الخسارة.\n"
                "• يقدم المستثمر رأس المال مع إدراك كامل لمخاطر السوق.\n"
                "• لا يوجد ربح مضمون.\n\n"
                
                "**المادة ۲ – عمليات التداول**\n"
                "• يلتزم المتداول بإجراء الصفقات بشكل احترافي ومسؤول.\n"
                "• يجوز للمتداول استخدام طرق تداول مختلفة بما في ذلك التداول الفوري، والرافعة المالية، والعقود الآجلة، والأدوات المالية الأخرى.\n"
                "• قد يتم التداول عبر منصات محلية أو دولية.\n"
                "• سيتم إبلاغ المستثمر في حالة الأحداث السوقية الهامة.\n"
                "• يقر المستثمر بأن المتداول لا يحمل ترخيصًا رسميًا لإدارة الأصول المالية.\n\n"
                
                "**المادة ۳ – توزيع الأرباح والخسائر**\n"
                "• يتم توزيع الأرباح والخسائر بناءً على النسبة المتفق عليها.\n"
                "• يتم توزيع الأرباح شهريًا عبر شبكة BEP20 إلى المحفظة التي يحددها المستثمر.\n"
                "• في حالة الخسارة، سيتم تقديم تقرير أداء.\n"
                "• تم تحديد حد أقصى للخسارة بنسبة ۲۰٪ من إجمالي رأس المال. سيتم إيقاف نشاط التداول في حالة الوصول إلى هذا الحد.\n\n"
                
                "**المادة ۴ – التزامات المتداول**\n"
                "• الحفاظ على سرية معلومات المستثمر\n"
                "• إدارة رأس المال بشكل احترافي\n"
                "• تقديم تقارير شفافة\n"
                "• التصرف بحسن نية تجاه مصلحة المستثمر\n\n"
                
                "**المادة ۵ – التزامات المستثمر**\n"
                "• تحويل رأس المال في الوقت المحدد\n"
                "• عدم التدخل في تنفيذ الصفقات\n"
                "• قبول مخاطر السوق\n"
                "• عدم تقديم مطالبات في حالة الخسارة إلا في حالة إثبات سوء السلوك أو الإهمال\n\n"
                
                "**شرط مهم:**\n"
                "يؤكد المستثمر أنه لم يتم وعده بأي ربح مضمون من قبل المتداول، وأن جميع قرارات الاستثمار اتخذت مع الفهم الكامل لمخاطر السوق.\n\n"
                
                "**المادة ۶ – إنهاء التعاون**\n"
                "• يجوز لأي من الطرفين إنهاء التعاون بإخطار كتابي مدته ۳۰ يومًا في حالة الإخلال بالالتزامات.\n"
                "• عند الإنهاء، يتم تسوية رأس المال والأرباح المحققة حتى تاريخ الإنهاء.\n\n"
                
                "**المادة ۷ – القوة القاهرة**\n"
                "• لا يتحمل أي من الطرفين المسؤولية عن عدم الوفاء بالالتزامات بسبب أحداث خارجة عن إرادتهما (الحرب، انقطاع الإنترنت، العقوبات، فشل البنية التحتية، إلخ).\n\n"
                
                "**المادة ۸ – تغيير معلومات الاتصال**\n"
                "• يجب إبلاغ الطرف الآخر بأي تغيير في بيانات الاتصال.\n\n"
                
                "📚 **الشروط الكاملة:**\n"
                "🔗 للاطلاع على الشروط الكاملة باللغة العربية، قم بزيارة:\n"
                "🌐 https://github.com/ramofinance/terms-and-conditions/blob/main/ar.md\n\n"
                
                "✅ بالنقر على 'لقد قرأت وأوافق على الشروط'، تؤكد أن:\n"
                "• لقد قرأت القواعد أعلاه\n"
                "• أنت توافق على جميع الشروط\n"
                "• أنت تقبل مسؤولية الاستثمار"
            ),
            'agree_terms': "✅ لقد قرأت وأوافق على الشروط",
            'disagree_terms': "❌ إلغاء الاستثمار",
            
            'payment': "🎯 **مرحلة الدفع**\n\n💵 **مبلغ الإيداع:** ${amount:,.2f}\n📈 **معدل الربح السنوي:** {annual_percentage}%\n📊 **الدفع الشهري:** ~{monthly_percentage:.2f}%\n💰 **الربح الشهري:** ${monthly_profit:,.2f}\n\n🔐 **عنوان محفظة الشركة (BEP20):**\n`{company_wallet}`\n\n📋 **تعليمات مهمة:**\n1. قم بالإيداع فقط إلى العنوان أعلاه\n2. استخدم شبكة BEP20 فقط\n3. بعد الدفع، أرسل إيصال المعاملة\n4. انتظر تأكيد الدعم الفني\n\n⏰ **وقت التأكيد:** 24 ساعة كحد أقصى\n📞 **الدعم:** @YourSupportUsername\n\n✅ بعد الدفع، انقر على زر '📤 إرسال إيصال المعاملة'.",
            'receipt_request': "📤 **الرجاء إرسال إيصال المعاملة**\n\nيمكنك:\n• إرسال هاش المعاملة (Transaction Hash) كنص\n• أو إرسال صورة/لقطة شاشة للإيصال\n\nمثال لهاش المعاملة:\n`0x7d5a3f5c8e1a9b0c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6`\n\n⚠️ إذا لم يكن لديك إيصال، يمكنك النقر على '⏭️ بدون إيصال'.",
            'receipt_received': "✅ **تم استلام إيصال معاملتك!**\n\n📋 جاري تسجيل طلب الاستثمار...",
            'receipt_skip': "⏭️ **سأستمر بدون إيصال**\n\n📋 جاري تسجيل طلب الاستثمار...",
            'cancel_invest': "❌ إلغاء الاستثمار",
            'investment_submitted': "✅ **تم تقديم طلب الاستثمار!**\n\n🎯 **معرف الطلب:** #{investment_id}\n💵 **المبلغ:** ${amount:,.2f}\n📈 **معدل الربح السنوي:** {annual_percentage}%\n📊 **الدفع الشهري:** ~{monthly_percentage:.2f}%\n💰 **الربح الشهري:** ${monthly_profit:,.2f}\n\n⏳ **الحالة:** في انتظار تأكيد الدفع\n📞 **المتابعة:** عبر الدعم الفني\n⏰ **وقت التأكيد:** 24 ساعة كحد أقصى\n\nبعد تأكيد الدفع، سيكون استثمارك نشطاً ويبدأ حساب الربح الشهري من الغد.",
            'no_investments': "📭 **ليس لديك أي استثمارات.**",
            'investments_title': "📊 **استثماراتك**\n\n",
            'investment_item': "💰 **الاستثمار #{inv_id}**\n📦 **الباقة:** {package}\n💵 **المبلغ:** ${amount:,.2f}\n📈 **معدل الربح السنوي:** {annual_percentage}%\n📊 **الربح الشهري:** ${monthly_profit:,.2f}\n🎯 **الحالة:** {status_text}\n📅 **تاريخ البدء:** {start_date}\n",
            'active_status': "✅ **في طور جني الربح**\n",
            'total_active': "📈 **إجمالي الاستثمار النشط:** ${total_active:,.2f}",
            'balance_title': "💰 **وضعك المالي**\n\n",
            'balance_details': "💵 **رصيد الحساب:** ${balance:,.2f}\n📊 **الاستثمار النشط:** ${total_investment:,.2f}\n📈 **إجمالي الربح الشهري:** ${total_monthly_profit:,.2f}\n🔢 **عدد الاستثمارات:** {active_count}\n\n📋 **التفاصيل:**\n• الرصيد القابل للسحب: ${balance:,.2f}\n• إجمالي الربح الشهري: ${total_monthly_profit:,.2f}\n• الربح اليومي: ${daily_profit:,.2f}\n\n💳 **سحب الرصيد:**\nلاتصال بسحب الرصيد، اتصل بالدعم الفني.\n📞 الدعم: @YourSupportUsername",
            'back': "🔙 رجوع إلى قائمة الاستثمار",
            'cancelled': "❌ تم إلغاء الاستثمار.",
            'choose_option': "⚠️ الرجاء اختيار أحد الخيارات.",
            'invalid_receipt': "⚠️ الرجاء إرسال إيصال المعاملة (الهاش) أو صورة الإيصال."
        },
        'en': {
            'menu': "💰 **Investment System**\n\n📊 **Investment Conditions:**\n• Minimum: $500\n• Annual profit with monthly payout:\n   🟢 50% annually: For $500 to $5,000\n   🔵 60% annually: For $5,000 to $10,000\n   🟣 70% annually: For over $10,000\n\n📋 **Process:**\n1. Choose investment amount\n2. Read and accept terms\n3. Get wallet address for deposit\n4. Make deposit\n5. Send transaction receipt\n6. Confirmation by support\n7. Start profit calculation\n\nPlease choose an option:",
            'no_wallet': "⚠️ **Please register your wallet address first!**\n\nTo invest, you need to register your BEP20 wallet address in your profile.\n\n🔹 Go to Profile\n🔹 Click 'Edit Wallet'\n🔹 Enter your wallet address\n\nThen you can invest.",
            'enter_amount': "💰 **New Investment**\n\nPlease enter your investment amount (in USD):\n\n📊 **Annual Profit Rate (Monthly Payout):**\n• 🟢 50% annually: For $500 to $5,000\n• 🔵 60% annually: For $5,000 to $10,000\n• 🟣 70% annually: For over $10,000\n\n💰 **Monthly Payout Calculation:**\n(Annual rate divided by 12 months)\n• 🟢 ~4.17% monthly\n• 🔵 ~5% monthly\n• 🟣 ~5.83% monthly\n\n💵 **Minimum amount:** $500\n\nExample: 500 or 7500 or 15000",
            'min_amount': "⚠️ Amount must be at least $500. Please enter again:",
            'invalid_amount': "⚠️ Please enter a valid number (example: 500):",
            'details': "✅ **Investment Details**\n\n💵 **Investment Amount:** ${amount:,.2f}\n📈 **Annual Profit Rate:** {annual_percentage}%\n📊 **Monthly Payout:** ~{monthly_percentage:.2f}%\n💰 **Monthly Profit:** ${monthly_profit:,.2f}\n📅 **Start Date:** Tomorrow\n⏳ **Duration:** Unlimited\n\n⚠️ **Important:**\n• After payment confirmation, monthly profit calculation starts\n• Profit sent to your wallet every month\n• Principal withdrawal possible after 3 months\n\nDo you want to continue?",
            'confirm_yes': "✅ Yes, Continue",
            'confirm_no': "❌ No, Cancel",
            
            # English terms and conditions
            'terms_and_conditions': (
                "📜 **RAMO FINANCE Investment Terms & Conditions**\n\n"
                "**Article 1 – Nature of Cooperation**\n"
                "• This cooperation is based on capital management in international financial markets.\n"
                "• Financial markets inherently involve risk, and both profit and loss are possible.\n"
                "• The Investor provides capital with full awareness of market risks.\n"
                "• No guaranteed profit is provided.\n\n"
                
                "**Article 2 – Trading Operations**\n"
                "• The Trader commits to managing trades professionally and responsibly.\n"
                "• The Trader may use various trading methods including spot, margin, futures, and other financial instruments.\n"
                "• Trading may be conducted through domestic or international platforms.\n"
                "• The Investor will be informed in case of significant market events.\n"
                "• The Investor acknowledges that the Trader does not hold an official financial asset management license.\n\n"
                
                "**Article 3 – Profit and Loss Distribution**\n"
                "• Profits and losses shall be shared based on the agreed percentage.\n"
                "• Profits are distributed monthly via BEP20 network to the Investor's designated wallet.\n"
                "• In case of loss, a performance report will be provided.\n"
                "• A maximum drawdown limit of 20% of total capital is defined. Trading activity will be paused if this limit is reached.\n\n"
                
                "**Article 4 – Trader Obligations**\n"
                "• Maintain confidentiality\n"
                "• Professional capital management\n"
                "• Transparent reporting\n"
                "• Acting in good faith toward the Investor's interest\n\n"
                
                "**Article 5 – Investor Obligations**\n"
                "• Timely capital transfer\n"
                "• No interference in trading execution\n"
                "• Acceptance of market risks\n"
                "• No claims in case of loss unless proven misconduct or negligence\n\n"
                
                "**Important Clause:**\n"
                "The Investor confirms that no guaranteed profit has been promised by the Trader and that all investment decisions are made with full understanding of market risks.\n\n"
                
                "**Article 6 – Termination**\n"
                "• Either party may terminate the cooperation with 30 days written notice in case of breach.\n"
                "• Upon termination, capital and realized profit up to the termination date shall be settled.\n\n"
                
                "**Article 7 – Force Majeure**\n"
                "• Neither party shall be liable for failure to perform obligations due to events beyond their control (war, internet disruption, sanctions, infrastructure failure, etc.).\n\n"
                
                "**Article 8 – Change of Contact Information**\n"
                "• Any change in contact details must be communicated to the other party.\n\n"
                
                "📚 **Full Terms & Conditions:**\n"
                "🔗 For complete terms and conditions in English, visit:\n"
                "🌐 https://github.com/ramofinance/terms-and-conditions/blob/main/en.md\n\n"
                
                "✅ By clicking 'I have read and agree to the terms', you confirm that:\n"
                "• You have read the above rules\n"
                "• You agree to all conditions\n"
                "• You accept the investment responsibility"
            ),
            'agree_terms': "✅ I have read and agree to the terms",
            'disagree_terms': "❌ Cancel Investment",
            
            'payment': "🎯 **Payment Step**\n\n💵 **Deposit Amount:** ${amount:,.2f}\n📈 **Annual Profit Rate:** {annual_percentage}%\n📊 **Monthly Payout:** ~{monthly_percentage:.2f}%\n💰 **Monthly Profit:** ${monthly_profit:,.2f}\n\n🔐 **Company Wallet Address (BEP20):**\n`{company_wallet}`\n\n📋 **Important Instructions:**\n1. Send only to the address above\n2. Use BEP20 network only\n3. After payment, send transaction receipt\n4. Wait for support confirmation\n\n⏰ **Confirmation Time:** Max 24 hours\n📞 **Support:** @YourSupportUsername\n\n✅ After payment, click the '📤 Send Transaction Receipt' button.",
            'receipt_request': "📤 **Please send your transaction receipt**\n\nYou can:\n• Send Transaction Hash as text\n• Or send photo/screenshot of receipt\n\nTransaction Hash example:\n`0x7d5a3f5c8e1a9b0c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6`\n\n⚠️ If you don't have receipt, you can click '⏭️ No Receipt'.",
            'receipt_received': "✅ **Your transaction receipt has been received!**\n\n📋 Registering your investment request...",
            'receipt_skip': "⏭️ **I'll continue without receipt**\n\n📋 Registering your investment request...",
            'cancel_invest': "❌ Cancel Investment",
            'investment_submitted': "✅ **Investment Request Submitted!**\n\n🎯 **Request ID:** #{investment_id}\n💵 **Amount:** ${amount:,.2f}\n📈 **Annual Profit Rate:** {annual_percentage}%\n📊 **Monthly Payout:** ~{monthly_percentage:.2f}%\n💰 **Monthly Profit:** ${monthly_profit:,.2f}\n\n⏳ **Status:** Waiting for payment confirmation\n📞 **Follow up:** Through support\n⏰ **Confirmation Time:** Max 24 hours\n\nAfter payment confirmation, your investment will be active and monthly profit calculation starts tomorrow.",
            'no_investments': "📭 **You have no investments.**",
            'investments_title': "📊 **Your Investments**\n\n",
            'investment_item': "💰 **Investment #{inv_id}**\n📦 **Package:** {package}\n💵 **Amount:** ${amount:,.2f}\n📈 **Annual Profit Rate:** {annual_percentage}%\n📊 **Monthly Profit:** ${monthly_profit:,.2f}\n🎯 **Status:** {status_text}\n📅 **Start Date:** {start_date}\n",
            'active_status': "✅ **Earning profit**\n",
            'total_active': "📈 **Total Active Investment:** ${total_active:,.2f}",
            'balance_title': "💰 **Your Financial Status**\n\n",
            'balance_details': "💵 **Account Balance:** ${balance:,.2f}\n📊 **Active Investment:** ${total_investment:,.2f}\n📈 **Total Monthly Profit:** ${total_monthly_profit:,.2f}\n🔢 **Number of Investments:** {active_count}\n\n📋 **Details:**\n• Withdrawable Balance: ${balance:,.2f}\n• Total Monthly Profit: ${total_monthly_profit:,.2f}\n• Daily Profit: ${daily_profit:,.2f}\n\n💳 **Withdraw Balance:**\nTo withdraw balance, contact support.\n📞 Support: @YourSupportUsername",
            'back': "🔙 Back to investment menu",
            'cancelled': "❌ Investment cancelled.",
            'choose_option': "⚠️ Please choose one of the options.",
            'invalid_receipt': "⚠️ Please send transaction receipt (hash) or receipt photo."
        }
    }
    return texts.get(language, texts['en'])

async def forward_photo_to_admins(message: Message, bot: Bot, user_id: int):
    """فوروارد عکس به ادمین‌ها"""
    admin_ids_str = os.getenv("ADMIN_IDS", "")
    if not admin_ids_str:
        print("⚠️ ADMIN_IDS not set for photo forwarding")
        return
    
    admin_ids = [int(id_str.strip()) for id_str in admin_ids_str.split(",") if id_str.strip()]
    
    # دریافت اطلاعات کاربر برای کپشن
    user = db.get_user(user_id)
    user_name = user[2] if user else "Unknown"
    
    for admin_id in admin_ids:
        try:
            # فوروارد عکس با کپشن
            caption = f"📷 عکس رسید تراکنش\n👤 کاربر: {user_name}\n🆔 ID: {user_id}"
            
            # ارسال عکس (کپی به جای فوروارد برای اضافه کردن کپشن)
            await bot.send_photo(
                chat_id=admin_id,
                photo=message.photo[-1].file_id,
                caption=caption
            )
            
            print(f"✅ Photo forwarded to admin {admin_id}")
        except Exception as e:
            print(f"❌ Failed to forward photo to admin {admin_id}: {type(e).__name__}: {e}")

async def forward_document_to_admins(message: Message, bot: Bot, user_id: int):
    """فوروارد فایل به ادمین‌ها"""
    admin_ids_str = os.getenv("ADMIN_IDS", "")
    if not admin_ids_str:
        print("⚠️ ADMIN_IDS not set for document forwarding")
        return
    
    admin_ids = [int(id_str.strip()) for id_str in admin_ids_str.split(",") if id_str.strip()]
    
    # دریافت اطلاعات کاربر برای کپشن
    user = db.get_user(user_id)
    user_name = user[2] if user else "Unknown"
    
    for admin_id in admin_ids:
        try:
            # ارسال فایل (کپی به جای فوروارد برای اضافه کردن کپشن)
            caption = f"📄 فایل رسید تراکنش\n👤 کاربر: {user_name}\n🆔 ID: {user_id}"
            
            await bot.send_document(
                chat_id=admin_id,
                document=message.document.file_id,
                caption=caption
            )
            
            print(f"✅ Document forwarded to admin {admin_id}")
        except Exception as e:
            print(f"❌ Failed to forward document to admin {admin_id}: {type(e).__name__}: {e}")

@router.message(F.text.in_(["💰 Investment", "💰 سرمایه‌گذاری", "💰 استثمار"]))
async def investment_menu(message: Message):
    """منوی سرمایه‌گذاری"""
    user_id = message.from_user.id
    language = db.get_user_language(user_id)
    
    texts = get_investment_texts(language)
    
    await message.answer(
        texts['menu'],
        reply_markup=get_investment_keyboard(language)
    )

@router.message(F.text.in_(["💰 سرمایه‌گذاری جدید", "💰 New Investment", "💰 استثمار جديد"]))
async def start_new_investment(message: Message, state: FSMContext):
    """شروع سرمایه‌گذاری جدید"""
    user_id = message.from_user.id
    language = db.get_user_language(user_id)
    
    texts = get_investment_texts(language)
    
    # بررسی اینکه کاربر کیف پول ثبت کرده یا نه
    user = db.get_user(user_id)
    if not user or not user[5]:  # user[5] = wallet_address
        await message.answer(texts['no_wallet'])
        return
    
    await message.answer(texts['enter_amount'])
    await state.set_state(InvestmentStates.waiting_for_amount)

@router.message(InvestmentStates.waiting_for_amount)
async def process_investment_amount(message: Message, state: FSMContext):
    """پردازش مبلغ سرمایه‌گذاری"""
    user_id = message.from_user.id
    language = db.get_user_language(user_id)
    
    texts = get_investment_texts(language)
    
    try:
        amount = float(message.text.replace(',', ''))
        
        # بررسی حداقل مبلغ
        if amount < 500:
            await message.answer(texts['min_amount'])
            return
        
        # محاسبه سود سالانه
        annual_percentage = calculate_annual_profit_percentage(amount)
        monthly_profit = calculate_monthly_profit_from_annual(amount, annual_percentage)
        monthly_percentage = calculate_monthly_profit_percentage(annual_percentage)
        
        await state.update_data(
            amount=amount, 
            annual_percentage=annual_percentage, 
            monthly_profit=monthly_profit,
            monthly_percentage=monthly_percentage
        )
        
        confirmation_text = texts['details'].format(
            amount=amount,
            annual_percentage=annual_percentage,
            monthly_percentage=monthly_percentage,
            monthly_profit=monthly_profit
        )
        
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text=texts['confirm_yes'])],
                [KeyboardButton(text=texts['confirm_no'])]
            ],
            resize_keyboard=True
        )
        
        await message.answer(confirmation_text, reply_markup=keyboard)
        await state.set_state(InvestmentStates.waiting_for_confirmation)
        
    except ValueError:
        await message.answer(texts['invalid_amount'])

@router.message(InvestmentStates.waiting_for_confirmation)
async def process_investment_confirmation(message: Message, state: FSMContext, bot: Bot):
    """پردازش تأیید سرمایه‌گذاری"""
    user_id = message.from_user.id
    language = db.get_user_language(user_id)
    
    texts = get_investment_texts(language)
    
    if message.text == texts['confirm_no']:
        await state.clear()
        await message.answer(texts['cancelled'], reply_markup=get_investment_keyboard(language))
        return
    
    if message.text != texts['confirm_yes']:
        await message.answer(texts['choose_option'])
        return
    
    data = await state.get_data()
    amount = data.get('amount')
    annual_percentage = data.get('annual_percentage')
    monthly_profit = data.get('monthly_profit')
    monthly_percentage = data.get('monthly_percentage')
    
    # ذخیره مجدد داده‌ها (برای استفاده در مراحل بعد)
    await state.update_data(
        amount=amount,
        annual_percentage=annual_percentage,
        monthly_profit=monthly_profit,
        monthly_percentage=monthly_percentage
    )
    
    # نمایش قوانین و مقررات
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=texts['agree_terms'])],
            [KeyboardButton(text=texts['disagree_terms'])]
        ],
        resize_keyboard=True
    )
    
    await message.answer(
        texts['terms_and_conditions'],
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await state.set_state(InvestmentStates.waiting_for_terms_agreement)

@router.message(InvestmentStates.waiting_for_terms_agreement)
async def process_terms_agreement(message: Message, state: FSMContext, bot: Bot):
    """پردازش تأیید قوانین توسط کاربر"""
    user_id = message.from_user.id
    language = db.get_user_language(user_id)
    
    texts = get_investment_texts(language)
    
    # اگر کاربر انصراف داد
    if message.text == texts['disagree_terms']:
        await state.clear()
        await message.answer(
            texts['cancelled'], 
            reply_markup=get_investment_keyboard(language)
        )
        return
    
    # اگر کاربر قوانین را تأیید کرد
    if message.text == texts['agree_terms']:
        data = await state.get_data()
        amount = data.get('amount')
        annual_percentage = data.get('annual_percentage')
        monthly_profit = data.get('monthly_profit')
        monthly_percentage = data.get('monthly_percentage')
        
        # آدرس کیف پول شرکت
        company_wallet = os.getenv("COMPANY_WALLET", "0x1234567890abcdef1234567890abcdef12345678")
        
        payment_instructions = texts['payment'].format(
            amount=amount,
            annual_percentage=annual_percentage,
            monthly_percentage=monthly_percentage,
            monthly_profit=monthly_profit,
            company_wallet=company_wallet
        )
        
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📤 ارسال رسید تراکنش" if language == 'fa' else 
                               "📤 إرسال إيصال المعاملة" if language == 'ar' else 
                               "📤 Send Transaction Receipt")],
                [KeyboardButton(text=texts['cancel_invest'])]
            ],
            resize_keyboard=True
        )
        
        await message.answer(payment_instructions, reply_markup=keyboard)
        await state.set_state(InvestmentStates.waiting_for_wallet_payment)
        return
    
    # اگر کاربر گزینه نامعتبر انتخاب کرد
    await message.answer(texts['choose_option'])

@router.message(InvestmentStates.waiting_for_wallet_payment)
async def process_payment_step(message: Message, state: FSMContext):
    """پردازش مرحله پرداخت - کاربر روی دکمه ارسال رسید کلیک می‌کند"""
    user_id = message.from_user.id
    language = db.get_user_language(user_id)
    
    texts = get_investment_texts(language)
    
    # بررسی اینکه کاربر روی کدام دکمه کلیک کرده
    if message.text == texts['cancel_invest']:
        await state.clear()
        await message.answer(texts['cancelled'], reply_markup=get_investment_keyboard(language))
        return
    
    # اگر کاربر روی دکمه ارسال رسید کلیک کرد
    if message.text in ["📤 ارسال رسید تراکنش", "📤 إرسال إيصال المعاملة", "📤 Send Transaction Receipt"]:
        # درخواست رسید تراکنش
        await message.answer(
            texts['receipt_request'],
            reply_markup=get_receipt_keyboard(language)
        )
        await state.set_state(InvestmentStates.waiting_for_transaction_receipt)
        return
    
    await message.answer(texts['choose_option'])

@router.message(InvestmentStates.waiting_for_transaction_receipt)
async def process_transaction_receipt(message: Message, state: FSMContext, bot: Bot):
    """پردازش رسید تراکنش ارسالی کاربر"""
    user_id = message.from_user.id
    language = db.get_user_language(user_id)
    
    texts = get_investment_texts(language)
    
    # بررسی اگر کاربر "بدون رسید" زد
    if message.text in ["⏭️ بدون رسید", "⏭️ بدون إيصال", "⏭️ No Receipt"]:
        await message.answer(texts['receipt_skip'])
        receipt_text = "بدون رسید"
        receipt_type = "none"
        await complete_investment_with_receipt(message, state, bot, receipt_text, receipt_type)
        return
    
    # بررسی اگر کاربر عکس ارسال کرد
    if message.content_type == ContentType.PHOTO:
        # ذخیره اطلاعات عکس
        receipt_text = f"📷 عکس رسید - فایل ID: {message.photo[-1].file_id}"
        receipt_type = "photo"
        await message.answer(texts['receipt_received'])
        
        # عکس را برای ادمین‌ها هم فوروارد می‌کنیم
        await forward_photo_to_admins(message, bot, user_id)
        
        await complete_investment_with_receipt(message, state, bot, receipt_text, receipt_type)
        return
    
    # بررسی اگر کاربر سند/فایل ارسال کرد
    if message.content_type == ContentType.DOCUMENT:
        receipt_text = f"📄 فایل رسید - فایل ID: {message.document.file_id}"
        receipt_type = "document"
        await message.answer(texts['receipt_received'])
        
        # فایل را برای ادمین‌ها هم فوروارد می‌کنیم
        await forward_document_to_admins(message, bot, user_id)
        
        await complete_investment_with_receipt(message, state, bot, receipt_text, receipt_type)
        return
    
    # بررسی اگر متن (هش تراکنش) ارسال کرد
    if message.text:
        receipt_text = message.text
        receipt_type = "text"
        await message.answer(texts['receipt_received'])
        await complete_investment_with_receipt(message, state, bot, receipt_text, receipt_type)
        return
    
    # اگر چیزی ارسال نکرده که قابل پردازش نیست
    await message.answer(texts['invalid_receipt'])

async def complete_investment_with_receipt(message: Message, state: FSMContext, bot: Bot, receipt_text: str, receipt_type: str):
    """تکمیل سرمایه‌گذاری با رسید"""
    user_id = message.from_user.id
    language = db.get_user_language(user_id)
    
    texts = get_investment_texts(language)
    
    # دریافت داده‌ها از state
    data = await state.get_data()
    amount = data.get('amount')
    annual_percentage = data.get('annual_percentage')
    monthly_profit = data.get('monthly_profit')
    monthly_percentage = data.get('monthly_percentage')
    
    # دریافت اطلاعات کاربر
    user = db.get_user(user_id)
    user_name = user[2] if user else "Unknown"
    user_wallet = user[5] if user else "Not set"
    
    # ذخیره سرمایه‌گذاری در دیتابیس (با رسید)
    cursor = db.conn.cursor()
    start_date = datetime.now()
    end_date = start_date + timedelta(days=365*10)  # 10 سال
    
    cursor.execute('''
        INSERT INTO investments (user_id, package, amount, duration, start_date, end_date, status, monthly_profit_percent, annual_profit_percent, transaction_receipt, receipt_type)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        user_id,
        f"{annual_percentage}% Annual",
        amount,
        999,
        start_date.strftime('%Y-%m-%d %H:%M:%S'),
        end_date.strftime('%Y-%m-%d %H:%M:%S'),
        'pending',
        monthly_percentage,  # درصد سود ماهانه
        annual_percentage,   # درصد سود سالانه
        receipt_text,
        receipt_type
    ))
    
    db.conn.commit()
    investment_id = cursor.lastrowid
    
    # ارسال نوتیفیکیشن به ادمین‌ها (با رسید)
    await send_investment_notification_to_admins(
        bot, investment_id, user_name, user_id, amount, 
        annual_percentage, monthly_profit, monthly_percentage, user_wallet,
        receipt_text=receipt_text,
        receipt_type=receipt_type
    )
    
    await state.clear()
    
    investment_submitted_text = texts['investment_submitted'].format(
        investment_id=investment_id,
        amount=amount,
        annual_percentage=annual_percentage,
        monthly_percentage=monthly_percentage,
        monthly_profit=monthly_profit
    )
    
    await message.answer(investment_submitted_text, reply_markup=get_investment_keyboard(language))

async def send_investment_notification_to_admins(bot: Bot, investment_id: int, user_name: str, user_id: int, 
                                                amount: float, annual_percentage: float, monthly_profit: float, 
                                                monthly_percentage: float, user_wallet: str, receipt_text: str = "بدون رسید", 
                                                receipt_type: str = "none"):
    """ارسال نوتیفیکیشن سرمایه‌گذاری جدید به ادمین‌ها (با رسید)"""
    admin_ids_str = os.getenv("ADMIN_IDS", "")
    if not admin_ids_str:
        print("⚠️ ADMIN_IDS not set in environment variables")
        return
    
    admin_ids = [int(id_str.strip()) for id_str in admin_ids_str.split(",") if id_str.strip()]
    
    if not admin_ids:
        print("⚠️ No admin IDs found")
        return
    
    print(f"📢 Attempting to send investment notification to {len(admin_ids)} admins")
    
    for admin_id in admin_ids:
        try:
            # تشخیص زبان ادمین برای نوتیفیکیشن
            admin_data = db.get_user(admin_id)
            admin_lang = admin_data[1] if admin_data else 'fa'
            
            # متن رسید (کوتاه شده اگر طولانی باشد)
            receipt_display = receipt_text
            if receipt_type == "text" and len(receipt_text) > 100:
                receipt_display = f"{receipt_text[:20]}...{receipt_text[-10:]}"
            
            # نماد نوع رسید
            receipt_icon = {
                'none': '❌',
                'text': '📄',
                'photo': '📷',
                'document': '📎'
            }.get(receipt_type, '📄')
            
            # نوع رسید به صورت متن
            receipt_type_text = {
                'none': 'بدون رسید',
                'text': 'هش تراکنش',
                'photo': 'عکس رسید',
                'document': 'فایل رسید'
            }.get(receipt_type, 'نامشخص')
            
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M')
            
            # استفاده از Markdown
            if admin_lang == 'fa':
                notification = (
                    "💰 *درخواست سرمایه‌گذاری جدید*\n\n"
                    f"🆔 *شناسه سرمایه‌گذاری:* #{investment_id}\n"
                    f"👤 *کاربر:* {user_name}\n"
                    f"🆔 *شناسه کاربر:* {user_id}\n"
                    f"💵 *مبلغ:* ${amount:,.2f}\n"
                    f"📈 *نرخ سود سالانه:* {annual_percentage}%\n"
                    f"📊 *نرخ سود ماهانه:* ~{monthly_percentage:.2f}%\n"
                    f"💰 *سود ماهانه:* ${monthly_profit:,.2f}\n"
                    f"🔐 *کیف پول کاربر:* {user_wallet[:10]}...\n\n"
                    f"📋 *رسید تراکنش:*\n"
                    f"📌 *نوع:* {receipt_icon} {receipt_type_text}\n"
                    f"📎 *محتوا:* `{receipt_display}`\n\n"
                    f"📅 *زمان درخواست:* {current_time}\n\n"
                    f"✅ *برای تایید:* /confirm_invest_{investment_id}\n"
                    f"❌ *برای رد:* /reject_invest_{investment_id}\n"
                    f"📋 *مشاهده جزئیات:* /user_{user_id}"
                )
                
                await bot.send_message(
                    admin_id, 
                    notification,
                    parse_mode="Markdown"
                )
                
            elif admin_lang == 'ar':
                # ترجمه عربی برای رسید
                receipt_type_text_ar = {
                    'none': 'بدون إيصال',
                    'text': 'هاش المعاملة',
                    'photo': 'صورة الإيصال',
                    'document': 'ملف الإيصال'
                }.get(receipt_type, 'غير معروف')
                
                notification = (
                    "💰 *طلب استثمار جديد*\n\n"
                    f"🆔 *معرف الاستثمار:* #{investment_id}\n"
                    f"👤 *المستخدم:* {user_name}\n"
                    f"🆔 *معرف المستخدم:* {user_id}\n"
                    f"💵 *المبلغ:* ${amount:,.2f}\n"
                    f"📈 *معدل الربح السنوي:* {annual_percentage}%\n"
                    f"📊 *معدل الربح الشهري:* ~{monthly_percentage:.2f}%\n"
                    f"💰 *الربح الشهري:* ${monthly_profit:,.2f}\n"
                    f"🔐 *محفظة المستخدم:* {user_wallet[:10]}...\n\n"
                    f"📋 *إيصال المعاملة:*\n"
                    f"📌 *النوع:* {receipt_icon} {receipt_type_text_ar}\n"
                    f"📎 *المحتوى:* `{receipt_display}`\n\n"
                    f"📅 *وقت الطلب:* {current_time}\n\n"
                    f"✅ *للتأكيد:* /confirm_invest_{investment_id}\n"
                    f"❌ *للرفض:* /reject_invest_{investment_id}\n"
                    f"📋 *عرض التفاصيل:* /user_{user_id}"
                )
                
                await bot.send_message(
                    admin_id, 
                    notification,
                    parse_mode="Markdown"
                )
                
            else:
                # ترجمه انگلیسی برای رسید
                receipt_type_text_en = {
                    'none': 'No receipt',
                    'text': 'Transaction hash',
                    'photo': 'Receipt photo',
                    'document': 'Receipt file'
                }.get(receipt_type, 'Unknown')
                
                notification = (
                    "💰 *New Investment Request*\n\n"
                    f"🆔 *Investment ID:* #{investment_id}\n"
                    f"👤 *User:* {user_name}\n"
                    f"🆔 *User ID:* {user_id}\n"
                    f"💵 *Amount:* ${amount:,.2f}\n"
                    f"📈 *Annual Profit Rate:* {annual_percentage}%\n"
                    f"📊 *Monthly Profit Rate:* ~{monthly_percentage:.2f}%\n"
                    f"💰 *Monthly Profit:* ${monthly_profit:,.2f}\n"
                    f"🔐 *User Wallet:* {user_wallet[:10]}...\n\n"
                    f"📋 *Transaction Receipt:*\n"
                    f"📌 *Type:* {receipt_icon} {receipt_type_text_en}\n"
                    f"📎 *Content:* `{receipt_display}`\n\n"
                    f"📅 *Request Time:* {current_time}\n\n"
                    f"✅ *To confirm:* /confirm_invest_{investment_id}\n"
                    f"❌ *To reject:* /reject_invest_{investment_id}\n"
                    f"📋 *View Details:* /user_{user_id}"
                )
                
                await bot.send_message(
                    admin_id, 
                    notification,
                    parse_mode="Markdown"
                )
            
            print(f"✅ Investment notification sent to admin {admin_id}")
            
        except Exception as e:
            print(f"❌ Failed to notify admin {admin_id}: {type(e).__name__}: {e}")
            # راه‌حل جایگزین: ارسال بدون فرمت اما با اطلاعات کامل
            try:
                # نمایش نوع رسید
                receipt_type_simple = {
                    'none': '❌ بدون رسید',
                    'text': '📄 هش تراکنش',
                    'photo': '📷 عکس رسید',
                    'document': '📎 فایل رسید'
                }.get(receipt_type, '📄 نامشخص')
                
                simple_message = (
                    f"💰 سرمایه‌گذاری جدید\n\n"
                    f"🆔 شناسه: #{investment_id}\n"
                    f"👤 کاربر: {user_name}\n"
                    f"💵 مبلغ: ${amount:,.2f}\n"
                    f"📈 سود سالانه: {annual_percentage}%\n"
                    f"📊 سود ماهانه: ~{monthly_percentage:.2f}%\n"
                    f"🔐 کیف پول: {user_wallet[:10]}...\n\n"
                    f"📋 رسید: {receipt_type_simple}\n"
                    f"📎 محتوا: {receipt_text[:50]}...\n\n"
                    f"✅ تایید: /confirm_invest_{investment_id}\n"
                    f"❌ رد: /reject_invest_{investment_id}\n"
                    f"👁️ جزئیات: /user_{user_id}"
                )
                await bot.send_message(admin_id, simple_message)
                print(f"✅ Simple notification sent to admin {admin_id}")
            except Exception as e2:
                print(f"❌ Failed to send simple notification too: {e2}")

@router.message(F.text.in_(["📊 سرمایه‌گذاری‌های من", "📊 My Investments", "📊 استثماراتي"]))
async def show_user_investments(message: Message):
    """نمایش سرمایه‌گذاری‌های کاربر"""
    user_id = message.from_user.id
    language = db.get_user_language(user_id)
    
    texts = get_investment_texts(language)
    
    cursor = db.conn.cursor()
    cursor.execute('''
        SELECT investment_id, package, amount, start_date, status, annual_profit_percent, monthly_profit_percent
        FROM investments 
        WHERE user_id = ?
        ORDER BY start_date DESC
        LIMIT 10
    ''', (user_id,))
    
    investments = cursor.fetchall()
    
    if not investments:
        await message.answer(texts['no_investments'])
        return
    
    # ترجمه وضعیت بر اساس زبان
    status_translations = {
        'fa': {
            'pending': '🟡 در انتظار تایید',
            'active': '🟢 فعال',
            'completed': '🔵 تکمیل شده',
            'rejected': '🔴 رد شده'
        },
        'ar': {
            'pending': '🟡 في انتظار التأكيد',
            'active': '🟢 نشط',
            'completed': '🔵 مكتمل',
            'rejected': '🔴 مرفوض'
        },
        'en': {
            'pending': '🟡 Pending',
            'active': '🟢 Active',
            'completed': '🔵 Completed',
            'rejected': '🔴 Rejected'
        }
    }
    
    status_dict = status_translations.get(language, status_translations['en'])
    
    response = texts['investments_title']
    for inv in investments:
        inv_id, package, amount, start_date, status, annual_percent, monthly_percent = inv
        
        # ترجمه وضعیت
        status_text = status_dict.get(status, status)
        
        # محاسبه سود ماهانه (استفاده از monthly_percent یا محاسبه از annual)
        if monthly_percent:
            monthly_profit = (amount * monthly_percent) / 100
        else:
            monthly_profit = (amount * (annual_percent / 12)) / 100
        
        investment_item = texts['investment_item'].format(
            inv_id=inv_id,
            package=package,
            amount=amount,
            annual_percentage=annual_percent or "N/A",
            monthly_profit=monthly_profit,
            status_text=status_text,
            start_date=start_date[:10]
        )
        
        if status == 'active':
            investment_item += texts['active_status']
        
        response += investment_item + "─" * 25 + "\n\n"
    
    # محاسبه مجموع
    cursor.execute('SELECT SUM(amount) FROM investments WHERE user_id = ? AND status = "active"', (user_id,))
    total_active = cursor.fetchone()[0] or 0
    
    response += texts['total_active'].format(total_active=total_active)
    
    await message.answer(response)

@router.message(F.text.in_(["💵 موجودی و سود", "💵 Balance & Profit", "💵 الرصيد والربح"]))
async def show_balance_profit(message: Message):
    """نمایش موجودی و سود کاربر"""
    user_id = message.from_user.id
    language = db.get_user_language(user_id)
    
    texts = get_investment_texts(language)
    
    user = db.get_user(user_id)
    balance = user[6] if user else 0
    
    cursor = db.conn.cursor()
    
    # مجموع سرمایه‌گذاری‌های فعال
    cursor.execute('SELECT SUM(amount) FROM investments WHERE user_id = ? AND status = "active"', (user_id,))
    total_investment = cursor.fetchone()[0] or 0
    
    # مجموع سود ماهانه
    cursor.execute('''
        SELECT SUM(amount * COALESCE(monthly_profit_percent, annual_profit_percent / 12) / 100) 
        FROM investments 
        WHERE user_id = ? AND status = "active"
    ''', (user_id,))
    total_monthly_profit = cursor.fetchone()[0] or 0
    
    # تعداد سرمایه‌گذاری‌های فعال
    cursor.execute('SELECT COUNT(*) FROM investments WHERE user_id = ? AND status = "active"', (user_id,))
    active_count = cursor.fetchone()[0] or 0
    
    # محاسبه سود روزانه
    daily_profit = total_monthly_profit / 30
    
    response = texts['balance_title'] + texts['balance_details'].format(
        balance=balance,
        total_investment=total_investment,
        total_monthly_profit=total_monthly_profit,
        active_count=active_count,
        daily_profit=daily_profit
    )
    
    await message.answer(response)

@router.message(F.text.in_(["🔙 بازگشت", "🔙 Back", "🔙 رجوع"]))
async def back_to_investment_menu(message: Message):
    """بازگشت به منوی سرمایه‌گذاری"""
    user_id = message.from_user.id
    language = db.get_user_language(user_id)
    
    texts = get_investment_texts(language)
    
    await message.answer(texts['back'], reply_markup=get_investment_keyboard(language))
