from telegram import Update, ParseMode
from telegram.ext import ContextTypes, ConversationHandler
from telegram.constants import ParseMode
from database.crud import UserCRUD, TaskCRUD, StatisticCRUD
from database.database import SessionLocal
from database.models import TaskStatus
from bot.keyboards.reply import get_cancel_keyboard, get_priority_keyboard, get_tasks_menu_keyboard
from bot.keyboards.inline import get_task_actions_keyboard, get_status_keyboard, get_pagination_keyboard
from bot.utils.helpers import (
    format_task_info, get_priority_emoji, format_datetime, 
    paginate_list, parse_datetime_input, is_valid_datetime
)
import logging

logger = logging.getLogger(__name__)

# States для ConversationHandler
TASK_TITLE, TASK_DESC, TASK_PRIORITY, TASK_DUE_DATE = range(4)

async def add_task_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Начать создание задачи"""
    await update.message.reply_text(
        "📝 <b>Создание новой задачи</b>\n\n"
        "Введите название задачи:",
        parse_mode=ParseMode.HTML,
        reply_markup=get_cancel_keyboard()
    )
    return TASK_TITLE

async def task_title_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получить название задачи"""
    if update.message.text == "🔙 Отмена":
        await update.message.reply_text("❌ Создание задачи отменено.")
        return ConversationHandler.END
    
    context.user_data['task_title'] = update.message.text
    
    await update.message.reply_text(
        "📝 Введите описание задачи (или пропустите, отправив /skip):",
        parse_mode=ParseMode.HTML,
        reply_markup=get_cancel_keyboard()
    )
    return TASK_DESC

async def task_description_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получить описание задачи"""
    if update.message.text == "🔙 Отмена":
        await update.message.reply_text("❌ Создание задачи отменено.")
        return ConversationHandler.END
    
    if update.message.text != "/skip":
        context.user_data['task_description'] = update.message.text
    else:
        context.user_data['task_description'] = None
    
    await update.message.reply_text(
        "⚠️ <b>Выберите приоритет:</b>",
        parse_mode=ParseMode.HTML,
        reply_markup=get_priority_keyboard()
    )
    return TASK_PRIORITY

async def task_priority_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получить приоритет задачи"""
    if update.message.text == "🔙 Отмена":
        await update.message.reply_text("❌ Создание задачи отменено.")
        return ConversationHandler.END
    
    priority_map = {
        "🔴 Высокий": 1,
        "🟡 Средний": 2,
        "🟢 Низкий": 3
    }
    
    priority = priority_map.get(update.message.text, 3)
    context.user_data['task_priority'] = priority
    
    await update.message.reply_text(
        "📅 Введите срок выполнения в формате ДД.МММ.ГГГГ ЧЧ:МИ\n"
        "(или пропустите, отправив /skip):",
        parse_mode=ParseMode.HTML,
        reply_markup=get_cancel_keyboard()
    )
    return TASK_DUE_DATE

async def task_due_date_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получить срок задачи"""
    if update.message.text == "🔙 Отмена":
        await update.message.reply_text("❌ Создание задачи отменено.")
        return ConversationHandler.END
    
    due_date = None
    if update.message.text != "/skip":
        if not is_valid_datetime(update.message.text):
            await update.message.reply_text(
                "❌ Неверный формат даты. Используйте: ДД.МММ.ГГГГ ЧЧ:МИ"
            )
            return TASK_DUE_DATE
        due_date = parse_datetime_input(update.message.text)
    
    context.user_data['task_due_date'] = due_date
    
    # Создать задачу
    db = SessionLocal()
    try:
        user = UserCRUD.get_by_telegram_id(db, update.effective_user.id)
        
        task = TaskCRUD.create(
            db,
            user_id=user.id,
            title=context.user_data['task_title'],
            description=context.user_data.get('task_description'),
            priority=context.user_data['task_priority'],
            due_date=due_date
        )
        
        # Обновить статистику
        StatisticCRUD.update_stats(db, user.id)
        
        response_text = "✅ <b>Задача создана успешно!</b>\n\n"
        response_text += format_task_info(task)
        
        await update.message.reply_text(
            response_text,
            parse_mode=ParseMode.HTML,
            reply_markup=get_tasks_menu_keyboard()
        )
        
        logger.info(f"✅ Задача {task.id} создана пользователем {update.effective_user.id}")
    except Exception as e:
        logger.error(f"❌ Ошибка при создании задачи: {e}")
        await update.message.reply_text("❌ Произошла ошибка при создании задачи.")
    finally:
        db.close()
    
    return ConversationHandler.END

async def my_tasks_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать мои задачи"""
    db = SessionLocal()
    try:
        user = UserCRUD.get_by_telegram_id(db, update.effective_user.id)
        tasks = TaskCRUD.get_user_tasks(db, user.id)
        
        if not tasks:
            await update.message.reply_text(
                "📭 У вас нет задач. Создайте первую!",
                reply_markup=get_tasks_menu_keyboard()
            )
            return
        
        # Пагинация
        page_tasks, page, total_pages = paginate_list(tasks, 1, 3)
        
        message_text = f"📋 <b>Ваши задачи ({len(tasks)} всего)</b>\n\n"
        
        for task in page_tasks:
            message_text += format_task_info(task)
            message_text += "\n"
        
        keyboard = get_pagination_keyboard(page, total_pages, "tasks") if total_pages > 1 else None
        
        await update.message.reply_text(
            message_text,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"❌ Ошибка в my_tasks_command: {e}")
        await update.message.reply_text("❌ Произошла ошибка при получении задач.")
    finally:
        db.close()

async def task_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик callback для задач"""
    query = update.callback_query
    await query.answer()
    
    db = SessionLocal()
    try:
        data = query.data
        
        if data.startswith("task_complete_"):
            task_id = int(data.split("_")[-1])
            task = TaskCRUD.update_status(db, task_id, TaskStatus.COMPLETED.value)
            
            if task:
                await query.edit_message_text(
                    text=f"✅ <b>Задача завершена!</b>\n\n{format_task_info(task)}",
                    parse_mode=ParseMode.HTML
                )
                logger.info(f"✅ Задача {task_id} завершена")
        
        elif data.startswith("task_delete_"):
            task_id = int(data.split("_")[-1])
            TaskCRUD.delete(db, task_id)
            
            await query.edit_message_text(
                text="🗑️ Задача удалена."
            )
            logger.info(f"🗑️ Задача {task_id} удалена")
        
        elif data.startswith("status_"):
            parts = data.split("_")
            status = parts[1]
            task_id = int(parts[2])
            
            task = TaskCRUD.update_status(db, task_id, status)
            
            if task:
                await query.edit_message_text(
                    text=f"✅ <b>Статус обновлён!</b>\n\n{format_task_info(task)}",
                    parse_mode=ParseMode.HTML,
                    reply_markup=get_task_actions_keyboard(task_id)
                )
    
    except Exception as e:
        logger.error(f"❌ Ошибка в task_callback_handler: {e}")
        await query.edit_message_text("❌ Произошла ошибка.")
    finally:
        db.close()
