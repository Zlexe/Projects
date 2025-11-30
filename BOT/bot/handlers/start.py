from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from database.crud import UserCRUD
from database.database import SessionLocal
from bot.keyboards.reply import get_main_menu_keyboard, get_admin_menu_keyboard
from bot.utils.helpers import get_user_summary
import logging

logger = logging.getLogger(__name__)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик /start"""
    db = SessionLocal()
    try:
        user = update.effective_user
        chat_id = update.effective_chat.id
        
        # Создать или получить пользователя
        db_user = UserCRUD.get_or_create(
            db,
            telegram_id=user.id,
            username=user.username,
            full_name=user.first_name
        )
        
        # Выбрать клавиатуру в зависимости от роли
        if UserCRUD.is_admin(db, user.id):
            keyboard = get_admin_menu_keyboard()
            welcome_text = f"👋 Добро пожаловать, администратор <b>{user.first_name}</b>!\n\n"
            welcome_text += "📋 Это бот для управления напоминаниями, задачами и событиями.\n\n"
            welcome_text += "🔑 У вас есть доступ к админ-панели для управления пользователями и рассылки."
        else:
            keyboard = get_main_menu_keyboard()
            welcome_text = f"👋 Добро пожаловать, <b>{user.first_name}</b>!\n\n"
            welcome_text += "📋 Это бот для управления вашими напоминаниями, задачами и событиями.\n\n"
            welcome_text += "Используйте меню ниже для начала работы."
        
        await context.bot.send_message(
            chat_id=chat_id,
            text=welcome_text,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard
        )
        
        logger.info(f"✅ Пользователь {user.id} ({user.username}) запустил бота")
    except Exception as e:
        logger.error(f"❌ Ошибка в start_command: {e}")
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="❌ Произошла ошибка при инициализации. Попробуйте позже."
        )
    finally:
        db.close()

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик /help"""
    help_text = """
🆘 <b>Справка по командам бота</b>

<b>📝 Управление задачами:</b>
/add_task - Создать новую задачу
/my_tasks - Просмотреть активные задачи
/task_stats - Статистика по задачам

<b>🔔 Управление напоминаниями:</b>
/add_reminder - Создать напоминание
/my_reminders - Мои напоминания
/reminder_list - Полный список

<b>📅 Календарь и события:</b>
/calendar - Показать календарь событий
/add_event - Добавить событие
/today_events - События на сегодня

<b>📊 Статистика:</b>
/stats - Моя статистика
/users_stats - Статистика пользователей (админ)

<b>⚙️ Системные команды:</b>
/start - Главное меню
/help - Эта справка
/settings - Настройки аккаунта

<b>👨‍💼 Админ-команды:</b>
/admin - Админ-панель
/broadcast - Массовая рассылка
/grant_admin - Назначить администратора
/user_list - Список пользователей

<b>ℹ️ Формат даты и времени:</b>
ДД.МММ.ГГГГ ЧЧ:МИ (например: 30.11.2025 14:30)

<b>💡 Советы:</b>
• Используйте приоритеты (🔴 высокий, 🟡 средний, 🟢 низкий)
• Напоминания проверяются каждые 5 минут
• События синхронизируются с Google Calendar (если настроено)
"""
    
    await update.message.reply_text(
        help_text,
        parse_mode=ParseMode.HTML
    )
    logger.info(f"✅ Справка отправлена пользователю {update.effective_user.id}")

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отмена текущей операции"""
    await update.message.reply_text("❌ Операция отменена.")
    context.user_data.clear()
