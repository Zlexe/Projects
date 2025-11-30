from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from telegram.constants import ParseMode
from database.crud import UserCRUD, ReminderCRUD
from database.database import SessionLocal
from bot.keyboards.reply import get_cancel_keyboard, get_reminders_menu_keyboard
from bot.keyboards.inline import get_reminder_actions_keyboard, get_pagination_keyboard
from bot.utils.helpers import format_reminder_info, format_datetime, paginate_list, parse_datetime_input, is_valid_datetime
from bot.utils.scheduler import reminder_scheduler
import logging

logger = logging.getLogger(__name__)

# States
REMINDER_TITLE, REMINDER_DESC, REMINDER_TIME = range(3)

async def add_reminder_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Начать создание напоминания"""
    await update.message.reply_text(
        "🔔 <b>Создание нового напоминания</b>\n\n"
        "Введите название напоминания:",
        parse_mode=ParseMode.HTML,
        reply_markup=get_cancel_keyboard()
    )
    return REMINDER_TITLE

async def reminder_title_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получить название напоминания"""
    if update.message.text == "🔙 Отмена":
        await update.message.reply_text("❌ Создание напоминания отменено.")
        return ConversationHandler.END
    
    context.user_data['reminder_title'] = update.message.text
    
    await update.message.reply_text(
        "📝 Введите описание (или пропустите /skip):",
        parse_mode=ParseMode.HTML,
        reply_markup=get_cancel_keyboard()
    )
    return REMINDER_DESC

async def reminder_description_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получить описание напоминания"""
    if update.message.text == "🔙 Отмена":
        await update.message.reply_text("❌ Создание напоминания отменено.")
        return ConversationHandler.END
    
    if update.message.text != "/skip":
        context.user_data['reminder_description'] = update.message.text
    
    await update.message.reply_text(
        "⏰ Введите время напоминания (ДД.МММ.ГГГГ ЧЧ:МИ):",
        parse_mode=ParseMode.HTML,
        reply_markup=get_cancel_keyboard()
    )
    return REMINDER_TIME

async def reminder_time_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получить время напоминания"""
    if update.message.text == "🔙 Отмена":
        await update.message.reply_text("❌ Создание напоминания отменено.")
        return ConversationHandler.END
    
    if not is_valid_datetime(update.message.text):
        await update.message.reply_text(
            "❌ Неверный формат. Используйте: ДД.МММ.ГГГГ ЧЧ:МИ"
        )
        return REMINDER_TIME
    
    scheduled_time = parse_datetime_input(update.message.text)
    
    db = SessionLocal()
    try:
        user = UserCRUD.get_by_telegram_id(db, update.effective_user.id)
        
        reminder = ReminderCRUD.create(
            db,
            user_id=user.id,
            title=context.user_data['reminder_title'],
            description=context.user_data.get('reminder_description'),
            scheduled_time=scheduled_time
        )
        
        # Добавить в расписание
        reminder_scheduler.add_reminder_job(reminder.id, scheduled_time)
        
        response_text = "✅ <b>Напоминание создано!</b>\n\n"
        response_text += format_reminder_info(reminder)
        
        await update.message.reply_text(
            response_text,
            parse_mode=ParseMode.HTML,
            reply_markup=get_reminders_menu_keyboard()
        )
        
        logger.info(f"✅ Напоминание {reminder.id} создано")
    except Exception as e:
        logger.error(f"❌ Ошибка при создании напоминания: {e}")
        await update.message.reply_text("❌ Произошла ошибка при создании напоминания.")
    finally:
        db.close()
    
    return ConversationHandler.END

async def my_reminders_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать мои напоминания"""
    db = SessionLocal()
    try:
        user = UserCRUD.get_by_telegram_id(db, update.effective_user.id)
        reminders = ReminderCRUD.get_user_reminders(db, user.id, active_only=False)
        
        if not reminders:
            await update.message.reply_text(
                "📭 У вас нет напоминаний.",
                reply_markup=get_reminders_menu_keyboard()
            )
            return
        
        page_reminders, page, total_pages = paginate_list(reminders, 1, 3)
        
        message_text = f"🔔 <b>Ваши напоминания ({len(reminders)})</b>\n\n"
        
        for reminder in page_reminders:
            message_text += format_reminder_info(reminder)
            message_text += "\n"
        
        keyboard = get_pagination_keyboard(page, total_pages, "reminders") if total_pages > 1 else None
        
        await update.message.reply_text(
            message_text,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard
        )
    except Exception as e:
        logger.error(f"❌ Ошибка в my_reminders_command: {e}")
        await update.message.reply_text("❌ Произошла ошибка.")
    finally:
        db.close()

async def reminder_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик callback для напоминаний"""
    query = update.callback_query
    await query.answer()
    
    db = SessionLocal()
    try:
        data = query.data
        
        if data.startswith("reminder_toggle_"):
            reminder_id = int(data.split("_")[-1])
            reminder = ReminderCRUD.toggle_active(db, reminder_id)
            
            if reminder:
                await query.edit_message_text(
                    text=f"✅ <b>Напоминание обновлено!</b>\n\n{format_reminder_info(reminder)}",
                    parse_mode=ParseMode.HTML,
                    reply_markup=get_reminder_actions_keyboard(reminder_id, reminder.is_active)
                )
        
        elif data.startswith("reminder_delete_"):
            reminder_id = int(data.split("_")[-1])
            ReminderCRUD.delete(db, reminder_id)
            reminder_scheduler.remove_reminder_job(reminder_id)
            
            await query.edit_message_text("🗑️ Напоминание удалено.")
    
    except Exception as e:
        logger.error(f"❌ Ошибка в reminder_callback_handler: {e}")
        await query.edit_message_text("❌ Произошла ошибка.")
    finally:
        db.close()

async def send_reminder(reminder):
    """Отправить напоминание пользователю"""
    from bot.main import bot_instance
    
    try:
        text = f"🔔 <b>Напоминание!</b>\n\n{format_reminder_info(reminder)}"
        
        await bot_instance.send_message(
            chat_id=reminder.user.telegram_id,
            text=text,
            parse_mode=ParseMode.HTML,
            reply_markup=get_reminder_actions_keyboard(reminder.id, reminder.is_active)
        )
        
        logger.info(f"📨 Напоминание {reminder.id} отправлено пользователю {reminder.user.telegram_id}")
    except Exception as e:
        logger.error(f"❌ Ошибка при отправке напоминания: {e}")
