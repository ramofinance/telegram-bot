# handlers/tickets.py
from aiogram import F, Router, Bot
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime
import os

from database import Database

router = Router()
db = Database()

class TicketStates(StatesGroup):
    waiting_for_subject = State()
    waiting_for_message = State()

def is_admin(user_id: int) -> bool:
    """بررسی اینکه کاربر ادمین هست یا نه"""
    admin_ids_str = os.getenv("ADMIN_IDS", "")
    if admin_ids_str:
        admin_ids = [int(id_str.strip()) for id_str in admin_ids_str.split(",") if id_str.strip()]
        return user_id in admin_ids
    return False

def get_ticket_keyboard(language='fa'):
    """منوی تیکت"""
    if language == 'fa':
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🎫 ارسال تیکت جدید")],
                [KeyboardButton(text="📋 تیکت‌های من")],
                [KeyboardButton(text="🔙 بازگشت")]
            ],
            resize_keyboard=True
        )
    else:
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🎫 New Ticket")],
                [KeyboardButton(text="📋 My Tickets")],
                [KeyboardButton(text="🔙 Back")]
            ],
            resize_keyboard=True
        )

@router.message(F.text.in_(["🆘 Support", "🆘 پشتیبانی"]))
async def support_menu(message: Message):
    """منوی پشتیبانی (تیکت)"""
    user_id = message.from_user.id
    language = db.get_user_language(user_id)
    
    if language == 'fa':
        await message.answer(
            "🆘 **سیستم پشتیبانی**\n\n"
            "✅ می‌توانید از طریق تیکت با پشتیبانی در ارتباط باشید.\n"
            "⏰ زمان پاسخگویی: ۲۴ ساعته\n"
            "📥 تیکت‌های شما محرمانه باقی می‌مانند.",
            reply_markup=get_ticket_keyboard(language)
        )
    else:
        await message.answer(
            "🆘 **Support System**\n\n"
            "✅ You can contact support through tickets.\n"
            "⏰ Response time: 24/7\n"
            "📥 Your tickets remain confidential.",
            reply_markup=get_ticket_keyboard(language)
        )

@router.message(F.text.in_(["🎫 ارسال تیکت جدید", "🎫 New Ticket"]))
async def start_new_ticket(message: Message, state: FSMContext):
    """شروع ایجاد تیکت جدید"""
    user_id = message.from_user.id
    language = db.get_user_language(user_id)
    
    if language == 'fa':
        await message.answer(
            "🎫 **تیکت جدید**\n\n"
            "لطفاً موضوع تیکت خود را وارد کنید (حداکثر ۵۰ کاراکتر):",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="🔙 بازگشت")]],
                resize_keyboard=True
            )
        )
    else:
        await message.answer(
            "🎫 **New Ticket**\n\n"
            "Please enter your ticket subject (max 50 characters):",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="🔙 Back")]],
                resize_keyboard=True
            )
        )
    
    await state.set_state(TicketStates.waiting_for_subject)

@router.message(TicketStates.waiting_for_subject)
async def process_ticket_subject(message: Message, state: FSMContext):
    """دریافت موضوع تیکت"""
    if message.text in ["🔙 بازگشت", "🔙 Back"]:
        await state.clear()
        user_id = message.from_user.id
        language = db.get_user_language(user_id)
        await message.answer("❌ ایجاد تیکت لغو شد.", reply_markup=get_ticket_keyboard(language))
        return
    
    if len(message.text) > 50:
        language = db.get_user_language(message.from_user.id)
        if language == 'fa':
            await message.answer("⚠️ موضوع نباید بیشتر از ۵۰ کاراکتر باشد. لطفاً مجدداً وارد کنید:")
        else:
            await message.answer("⚠️ Subject must be less than 50 characters. Please enter again:")
        return
    
    await state.update_data(subject=message.text)
    
    language = db.get_user_language(message.from_user.id)
    if language == 'fa':
        await message.answer(
            "📝 **پیام خود را وارد کنید:**\n\n"
            "• می‌توانید متن، عکس یا فایل ارسال کنید\n"
            "• پس از ارسال، تیکت شما ثبت می‌شود\n"
            "• پشتیبانی در اسرع وقت پاسخ خواهد داد"
        )
    else:
        await message.answer(
            "📝 **Enter your message:**\n\n"
            "• You can send text, photo or file\n"
            "• After sending, your ticket will be created\n"
            "• Support will respond as soon as possible"
        )
    
    await state.set_state(TicketStates.waiting_for_message)

@router.message(TicketStates.waiting_for_message)
async def process_ticket_message(message: Message, state: FSMContext, bot: Bot):
    """دریافت پیام تیکت و ثبت آن"""
    user_id = message.from_user.id
    language = db.get_user_language(user_id)
    user_data = db.get_user(user_id)
    user_name = user_data[2] if user_data else "Unknown"
    
    data = await state.get_data()
    subject = data.get('subject', 'No Subject')
    
    # ذخیره تیکت در دیتابیس
    ticket_message = message.text if message.text else "📎 فایل/عکس ارسال شده"
    ticket_id = db.create_ticket(user_id, subject, ticket_message)
    
    # ارسال نوتیفیکیشن به ادمین‌ها
    admin_ids_str = os.getenv("ADMIN_IDS", "")
    if admin_ids_str:
        admin_ids = [int(id_str.strip()) for id_str in admin_ids_str.split(",") if id_str.strip()]
        
        for admin_id in admin_ids:
            try:
                notification = (
                    "🎫 **تیکت جدید**\n\n"
                    f"🆔 **شماره تیکت:** #{ticket_id}\n"
                    f"👤 **کاربر:** {user_name}\n"
                    f"🆔 **شناسه کاربر:** {user_id}\n"
                    f"📌 **موضوع:** {subject}\n"
                    f"📝 **پیام:** {ticket_message[:100]}...\n"
                    f"📅 **زمان:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
                    f"💬 **برای پاسخ:** /reply_{ticket_id}"
                )
                
                await bot.send_message(admin_id, notification)
                
            except Exception as e:
                print(f"❌ Failed to notify admin {admin_id}: {e}")
    
    await state.clear()
    
    if language == 'fa':
        await message.answer(
            f"✅ **تیکت شما ثبت شد!**\n\n"
            f"🎫 **شماره تیکت:** #{ticket_id}\n"
            f"📌 **موضوع:** {subject}\n"
            f"📝 **پیام شما:** {ticket_message[:100]}...\n\n"
            f"⏳ **وضعیت:** در انتظار پاسخ\n"
            f"📞 **پیگیری:** از منوی 'تیکت‌های من'\n\n"
            f"پشتیبانی در اسرع وقت پاسخ خواهد داد.",
            reply_markup=get_ticket_keyboard(language)
        )
    else:
        await message.answer(
            f"✅ **Your ticket has been created!**\n\n"
            f"🎫 **Ticket ID:** #{ticket_id}\n"
            f"📌 **Subject:** {subject}\n"
            f"📝 **Your Message:** {ticket_message[:100]}...\n\n"
            f"⏳ **Status:** Waiting for response\n"
            f"📞 **Follow up:** From 'My Tickets' menu\n\n"
            f"Support will respond as soon as possible.",
            reply_markup=get_ticket_keyboard(language)
        )

@router.message(F.text.in_(["📋 تیکت‌های من", "📋 My Tickets"]))
async def show_user_tickets(message: Message):
    """نمایش تیکت‌های کاربر"""
    user_id = message.from_user.id
    language = db.get_user_language(user_id)
    
    tickets = db.get_user_tickets(user_id)
    
    if not tickets:
        if language == 'fa':
            await message.answer("📭 **هیچ تیکتی ندارید.**")
        else:
            await message.answer("📭 **You have no tickets.**")
        return
    
    if language == 'fa':
        response = "📋 **تیکت‌های شما**\n\n"
        for ticket in tickets:
            ticket_id, subject, status, created_at, admin_response, responded_at = ticket
            
            # ترجمه وضعیت
            status_text = {
                'open': '🔴 باز',
                'answered': '🟢 پاسخ داده شده',
                'closed': '⚫ بسته'
            }.get(status, status)
            
            response += f"🎫 **تیکت #{ticket_id}**\n"
            response += f"📌 **موضوع:** {subject}\n"
            response += f"📅 **تاریخ:** {created_at[:10]}\n"
            response += f"📊 **وضعیت:** {status_text}\n"
            
            if admin_response:
                response += f"📨 **پاسخ:** {admin_response[:50]}...\n"
            
            response += f"👁️ **مشاهده:** /viewticket_{ticket_id}\n"
            response += "─" * 25 + "\n\n"
    else:
        response = "📋 **Your Tickets**\n\n"
        for ticket in tickets:
            ticket_id, subject, status, created_at, admin_response, responded_at = ticket
            
            status_text = {
                'open': '🔴 Open',
                'answered': '🟢 Answered',
                'closed': '⚫ Closed'
            }.get(status, status)
            
            response += f"🎫 **Ticket #{ticket_id}**\n"
            response += f"📌 **Subject:** {subject}\n"
            response += f"📅 **Date:** {created_at[:10]}\n"
            response += f"📊 **Status:** {status_text}\n"
            
            if admin_response:
                response += f"📨 **Response:** {admin_response[:50]}...\n"
            
            response += f"👁️ **View:** /viewticket_{ticket_id}\n"
            response += "─" * 25 + "\n\n"
    
    await message.answer(response, parse_mode="Markdown")

# هندلر مشاهده یک تیکت خاص
@router.message(F.text.regexp(r'^/viewticket_\d+$'))
async def view_single_ticket(message: Message):
    """مشاهده یک تیکت خاص"""
    user_id = message.from_user.id
    
    try:
        ticket_id = int(message.text.split('_')[1])
        ticket = db.get_ticket(ticket_id)
        
        if not ticket:
            await message.answer("❌ تیکت یافت نشد.")
            return
        
        # بررسی اینکه کاربر صاحب تیکت است یا ادمین
        if ticket[1] != user_id and not is_admin(user_id):
            await message.answer("⛔ دسترسی denied.")
            return
        
        ticket_id, ticket_user_id, subject, ticket_message, status, created_at, admin_response, responded_at, full_name, email = ticket
        
        language = db.get_user_language(user_id)
        
        if language == 'fa':
            status_text = {
                'open': '🔴 باز',
                'answered': '🟢 پاسخ داده شده',
                'closed': '⚫ بسته'
            }.get(status, status)
            
            response = (
                f"🎫 تیکت #{ticket_id}\n\n"
                f"📌 موضوع: {subject}\n"
                f"📅 تاریخ ایجاد: {created_at}\n"
                f"📊 وضعیت: {status_text}\n\n"
                f"📝 پیام شما:\n{ticket_message}\n\n"
            )
            
            if admin_response:
                response += f"📨 پاسخ پشتیبانی:\n{admin_response}\n"
                if responded_at:
                    response += f"⏰ زمان پاسخ: {responded_at}\n"
            
            response += f"\n👤 فرستنده: {full_name}"
            
        else:
            status_text = {
                'open': '🔴 Open',
                'answered': '🟢 Answered',
                'closed': '⚫ Closed'
            }.get(status, status)
            
            response = (
                f"🎫 Ticket #{ticket_id}\n\n"
                f"📌 Subject: {subject}\n"
                f"📅 Created at: {created_at}\n"
                f"📊 Status: {status_text}\n\n"
                f"📝 Your Message:\n{ticket_message}\n\n"
            )
            
            if admin_response:
                response += f"📨 Support Response:\n{admin_response}\n"
                if responded_at:
                    response += f"⏰ Response time: {responded_at}\n"
            
            response += f"\n👤 Sender: {full_name}"
        
        await message.answer(response)
        
    except Exception as e:
        await message.answer(f"❌ خطا: {str(e)}")

# هندلر بازگشت
@router.message(F.text.in_(["🔙 بازگشت", "🔙 Back"]))
async def back_to_support_menu(message: Message):
    """بازگشت به منوی پشتیبانی"""
    user_id = message.from_user.id
    language = db.get_user_language(user_id)
    
    await message.answer("🔙 بازگشت به منوی پشتیبانی", reply_markup=get_ticket_keyboard(language))