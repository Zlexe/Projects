from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from database.crud import UserCRUD, StatisticCRUD, TaskCRUD
from database.database import SessionLocal
from database.models import TaskStatus
import logging

logger = logging.getLogger(__name__)

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Моя статистика"""
    db = SessionLocal()
    try:
        user = UserCRUD.get_by_telegram_id(db, update.effective_user.id)
        stat = StatisticCRUD.update_stats(db, user.id)
        
        tasks = TaskCRUD.get_user_tasks(db, user.id)
        completed = sum(1 for t in tasks if t.status == TaskStatus.COMPLETED.value)
        in_progress = sum(1 for t in tasks if t.status == TaskStatus.IN_PROGRESS.value)
        
        message_text = f"📊 <b>Ваша статистика</b>\n\n"
        message_text += f"👤 <b>Пользователь:</b> {user.full_name or 'Unknown'}\n\n"
        message_text += f"📝 <b>Задачи:</b>\n"
        message_text += f"  • Всего: {stat.total_tasks}\n"
        message_text += f"  • ✅ Завершено: {stat.completed_tasks}\n"
        message_text += f"  • ⏳ В процессе: {in_progress}\n"
        message_text += f"  • 📋 Осталось: {stat.total_tasks - stat.completed_tasks}\n\n"
        
        message_text += f"🔔 <b>Напоминания:</b>\n"
        message_text += f"  • Всего: {stat.total_reminders}\n"
        message_text += f"  • 📨 Отправлено: {stat.triggered_reminders}\n\n"
        
        message_text += f"📅 <b>События:</b>\n"
        message_text += f"  • Всего: {stat.total_events}\n\n"
        
        message_text += f"🕐 <b>Последняя активность:</b> {stat.last_activity.strftime('%d.%m.%Y %H:%M')}\n"
        
        if stat.total_tasks > 0:
            completion_percent = (stat.completed_tasks / stat.total_tasks) * 100
            message_text += f"\n📈 <b>Процент выполнения:</b> {completion_percent:.1f}%\n"
        
        await update.message.reply_text(
            message_text,
            parse_mode=ParseMode.HTML
        )
        
        logger.info(f"📊 Статистика пользователя {user.telegram_id} отправлена")
    except Exception as e:
        logger.error(f"❌ Ошибка в stats_command: {e}")
        await update.message.reply_text("❌ Произошла ошибка при получении статистики.")
    finally:
        db.close()
