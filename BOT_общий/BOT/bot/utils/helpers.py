from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from database.crud import UserCRUD, TaskCRUD, ReminderCRUD, EventCRUD, StatisticCRUD
from database.models import TaskStatus
import logging

logger = logging.getLogger(__name__)

def format_datetime(dt: datetime) -> str:
    """Форматировать дату и время"""
    if not dt:
        return "Не указано"
    return dt.strftime("%d.%m.%Y %H:%M")

def format_date(dt: datetime) -> str:
    """Форматировать дату"""
    if not dt:
        return "Не указано"
    return dt.strftime("%d.%m.%Y")

def get_priority_emoji(priority: int) -> str:
    """Получить эмодзи приоритета"""
    if priority == 1:
        return "🔴"  # Высокий
    elif priority == 2:
        return "🟡"  # Средний
    else:
        return "🟢"  # Низкий

def get_status_emoji(status: str) -> str:
    """Получить эмодзи статуса"""
    if status == TaskStatus.COMPLETED.value:
        return "✅"
    elif status == TaskStatus.IN_PROGRESS.value:
        return "⏳"
    elif status == TaskStatus.CANCELLED.value:
        return "❌"
    else:
        return "📝"

def format_task_info(task) -> str:
    """Форматировать информацию о задаче"""
    text = f"{get_status_emoji(task.status)} <b>{task.title}</b>\n"
    text += f"Приоритет: {get_priority_emoji(task.priority)}\n"
    text += f"Статус: {task.status}\n"
    
    if task.description:
        text += f"Описание: <i>{task.description}</i>\n"
    
    if task.due_date:
        text += f"Срок: {format_datetime(task.due_date)}\n"
    
    return text

def format_reminder_info(reminder) -> str:
    """Форматировать информацию о напоминании"""
    status = "✅ Активно" if reminder.is_active else "❌ Отключено"
    text = f"<b>{reminder.title}</b>\n"
    text += f"Статус: {status}\n"
    text += f"Время: {format_datetime(reminder.scheduled_time)}\n"
    
    if reminder.description:
        text += f"Описание: <i>{reminder.description}</i>\n"
    
    return text

def format_event_info(event) -> str:
    """Форматировать информацию о событии"""
    text = f"📅 <b>{event.title}</b>\n"
    text += f"Тип: {event.event_type}\n"
    text += f"Начало: {format_datetime(event.start_time)}\n"
    text += f"Конец: {format_datetime(event.end_time)}\n"
    
    if event.location:
        text += f"Место: {event.location}\n"
    
    if event.description:
        text += f"Описание: <i>{event.description}</i>\n"
    
    return text

def get_user_summary(db: Session, user_id: int) -> str:
    """Получить краткую информацию о пользователе"""
    tasks = TaskCRUD.get_user_tasks(db, user_id)
    reminders = ReminderCRUD.get_user_reminders(db, user_id)
    events = EventCRUD.get_user_events(db, user_id, days_ahead=7)
    
    completed_tasks = sum(1 for t in tasks if t.status == TaskStatus.COMPLETED.value)
    active_reminders = sum(1 for r in reminders if r.is_active)
    
    text = "📊 <b>Ваша статистика:</b>\n\n"
    text += f"📝 Задачи: {completed_tasks}/{len(tasks)} выполнено\n"
    text += f"🔔 Напоминания: {active_reminders} активных из {len(reminders)}\n"
    text += f"📅 События: {len(events)} на неделю\n"
    
    return text

def parse_datetime_input(text: str) -> datetime:
    """Парсить дату и время из текста (DD.MM.YYYY HH:MM)"""
    try:
        return datetime.strptime(text.strip(), "%d.%m.%Y %H:%M")
    except ValueError:
        return None

def is_valid_datetime(text: str) -> bool:
    """Проверить валидность формата даты и времени"""
    return parse_datetime_input(text) is not None

def get_time_until(dt: datetime) -> str:
    """Получить время до события"""
    now = datetime.utcnow()
    diff = dt - now
    
    if diff.total_seconds() < 0:
        return "Истекло"
    
    hours = diff.total_seconds() // 3600
    minutes = (diff.total_seconds() % 3600) // 60
    
    if hours > 0:
        return f"через {int(hours)}ч {int(minutes)}м"
    else:
        return f"через {int(minutes)}м"

def safe_get_user_info(user) -> dict:
    """Безопасно получить информацию о пользователе"""
    return {
        'id': user.id,
        'telegram_id': user.telegram_id,
        'username': user.username or "не указано",
        'full_name': user.full_name or "не указано",
        'role': user.role,
        'created_at': format_datetime(user.created_at)
    }

def paginate_list(items: list, page: int = 1, items_per_page: int = 5) -> tuple:
    """Пагинировать список"""
    total_pages = (len(items) + items_per_page - 1) // items_per_page
    page = max(1, min(page, total_pages))
    
    start = (page - 1) * items_per_page
    end = start + items_per_page
    
    page_items = items[start:end]
    return page_items, page, total_pages
