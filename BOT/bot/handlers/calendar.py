from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from telegram.constants import ParseMode
from datetime import datetime, timedelta
from database.crud import UserCRUD, EventCRUD
from database.database import SessionLocal
from bot.keyboards.reply import get_cancel_keyboard
from bot.keyboards.inline import get_event_actions_keyboard, get_event_type_keyboard
from bot.utils.helpers import format_event_info, format_datetime, parse_datetime_input, is_valid_datetime
from bot.utils.google_cal import google_calendar
import logging

logger = logging.getLogger(__name__)

# States
EVENT_TITLE, EVENT_START, EVENT_END, EVENT_DESC, EVENT_LOCATION, EVENT_TYPE = range(6)

async def add_event_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Начать создание события"""
    await update.message.reply_text(
        "📅 <b>Создание нового события</b>\n\n"
        "Введите название события:",
        parse_mode=ParseMode.HTML,
        reply_markup=get_cancel_keyboard()
    )
    return EVENT_TITLE

async def event_title_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получить название события"""
    if update.message.text == "🔙 Отмена":
        await update.message.reply_text("❌ Создание события отменено.")
        return ConversationHandler.END
    
    context.user_data['event_title'] = update.message.text
    
    await update.message.reply_text(
        "⏰ Введите время начала (ДД.МММ.ГГГГ ЧЧ:МИ):",
        parse_mode=ParseMode.HTML,
        reply_markup=get_cancel_keyboard()
    )
    return EVENT_START

async def event_start_time_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получить время начала события"""
    if update.message.text == "🔙 Отмена":
        await update.message.reply_text("❌ Создание события отменено.")
        return ConversationHandler.END
    
    if not is_valid_datetime(update.message.text):
        await update.message.reply_text(
            "❌ Неверный формат. Используйте: ДД.МММ.ГГГГ ЧЧ:МИ"
        )
        return EVENT_START
    
    context.user_data['event_start'] = parse_datetime_input(update.message.text)
    
    await update.message.reply_text(
        "⏰ Введите время окончания (ДД.МММ.ГГГГ ЧЧ:МИ):",
        parse_mode=ParseMode.HTML,
        reply_markup=get_cancel_keyboard()
    )
    return EVENT_END

async def event_end_time_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получить время окончания события"""
    if update.message.text == "🔙 Отмена":
        await update.message.reply_text("❌ Создание события отменено.")
        return ConversationHandler.END
    
    if not is_valid_datetime(update.message.text):
        await update.message.reply_text(
            "❌ Неверный формат. Используйте: ДД.МММ.ГГГГ ЧЧ:МИ"
        )
        return EVENT_END
    
    end_time = parse_datetime_input(update.message.text)
    
    if end_time <= context.user_data['event_start']:
        await update.message.reply_text(
            "❌ Время окончания должно быть позже времени начала."
        )
        return EVENT_END
    
    context.user_data['event_end'] = end_time
    
    await update.message.reply_text(
        "📝 Введите описание события (или пропустите /skip):",
        parse_mode=ParseMode.HTML,
        reply_markup=get_cancel_keyboard()
    )
    return EVENT_DESC

async def event_description_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получить описание события"""
    if update.message.text == "🔙 Отмена":
        await update.message.reply_text("❌ Создание события отменено.")
        return ConversationHandler.END
    
    if update.message.text != "/skip":
        context.user_data['event_description'] = update.message.text
    
    await update.message.reply_text(
        "📍 Введите место проведения (или пропустите /skip):",
        parse_mode=ParseMode.HTML,
        reply_markup=get_cancel_keyboard()
    )
    return EVENT_LOCATION

async def event_location_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получить место события"""
    if update.message.text == "🔙 Отмена":
        await update.message.reply_text("❌ Создание события отменено.")
        return ConversationHandler.END
    
    if update.message.text != "/skip":
        context.user_data['event_location'] = update.message.text
    
    await update.message.reply_text(
        "🏷️ <b>Выберите тип события:</b>",
        parse_mode=ParseMode.HTML,
        reply_markup=get_event_type_keyboard()
    )
    return EVENT_TYPE

async def event_type_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Выбрать тип события"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    event_type = data.split("_")[2]
    
    db = SessionLocal()
    try:
        user = UserCRUD.get_by_telegram_id(db, update.effective_user.id)
        
        event = EventCRUD.create(
            db,
            user_id=user.id,
            title=context.user_data['event_title'],
            start_time=context.user_data['event_start'],
            end_time=context.user_data['event_end'],
            description=context.user_data.get('event_description'),
            location=context.user_data.get('event_location'),
            event_type=event_type
        )
        
        # Попытаться добавить в Google Calendar
        google_event_id = google_calendar.create_event(
            title=event.title,
            start_time=event.start_time,
            end_time=event.end_time,
            description=event.description,
            location=event.location
        )
        
        if google_event_id:
            event.google_event_id = google_event_id
            db.commit()
        
        response_text = "✅ <b>Событие создано!</b>\n\n"
        response_text += format_event_info(event)
        
        await query.edit_message_text(
            text=response_text,
            parse_mode=ParseMode.HTML,
            reply_markup=get_event_actions_keyboard(event.id)
        )
        
        logger.info(f"✅ Событие {event.id} создано")
    except Exception as e:
        logger.error(f"❌ Ошибка при создании события: {e}")
        await query.edit_message_text("❌ Произошла ошибка при создании события.")
    finally:
        db.close()
    
    return ConversationHandler.END

async def calendar_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать календарь на неделю"""
    db = SessionLocal()
    try:
        user = UserCRUD.get_by_telegram_id(db, update.effective_user.id)
        events = EventCRUD.get_user_events(db, user.id, days_ahead=7)
        
        if not events:
            await update.message.reply_text(
                "📭 У вас нет запланированных событий на следующую неделю."
            )
            return
        
        message_text = "📅 <b>Ваши события на неделю:</b>\n\n"
        
        for event in events:
            message_text += format_event_info(event)
            message_text += f"<i>ID: {event.id}</i>\n\n"
        
        await update.message.reply_text(
            message_text,
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        logger.error(f"❌ Ошибка в calendar_command: {e}")
        await update.message.reply_text("❌ Произошла ошибка.")
    finally:
        db.close()

async def today_events_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать события на сегодня"""
    db = SessionLocal()
    try:
        user = UserCRUD.get_by_telegram_id(db, update.effective_user.id)
        events = EventCRUD.get_today_events(db, user.id)
        
        if not events:
            await update.message.reply_text(
                "📭 У вас нет событий на сегодня."
            )
            return
        
        message_text = "📅 <b>События на сегодня:</b>\n\n"
        
        for event in events:
            message_text += format_event_info(event)
            message_text += "\n"
        
        await update.message.reply_text(
            message_text,
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        logger.error(f"❌ Ошибка в today_events_command: {e}")
        await update.message.reply_text("❌ Произошла ошибка.")
    finally:
        db.close()

async def event_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик callback для событий"""
    query = update.callback_query
    await query.answer()
    
    db = SessionLocal()
    try:
        data = query.data
        
        if data.startswith("event_delete_"):
            event_id = int(data.split("_")[-1])
            event = EventCRUD.get_by_id(db, event_id)
            
            if event and event.google_event_id:
                google_calendar.delete_event(event.google_event_id)
            
            EventCRUD.delete(db, event_id)
            
            await query.edit_message_text("🗑️ Событие удалено.")
    
    except Exception as e:
        logger.error(f"❌ Ошибка в event_callback_handler: {e}")
        await query.edit_message_text("❌ Произошла ошибка.")
    finally:
        db.close()
