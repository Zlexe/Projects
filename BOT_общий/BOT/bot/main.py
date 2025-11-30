import logging
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler, 
    ConversationHandler, filters
)
from telegram.constants import ParseMode
from bot.config import config
from database.database import init_db
from bot.utils.scheduler import reminder_scheduler
from bot.handlers import (
    start_command, help_command, cancel_command,
    add_task_command, task_title_input, task_description_input, 
    task_priority_input, task_due_date_input, my_tasks_command, task_callback_handler,
    add_reminder_command, reminder_title_input, reminder_description_input,
    reminder_time_input, my_reminders_command, reminder_callback_handler, send_reminder,
    add_event_command, event_title_input, event_start_time_input, event_end_time_input,
    event_description_input, event_location_input, event_type_selection,
    calendar_command, today_events_command, event_callback_handler,
    admin_command, grant_admin_command, user_list_command, broadcast_command,
    broadcast_message_handler, users_stats_command, system_info_command,
    stats_command,
    TASK_TITLE, TASK_DESC, TASK_PRIORITY, TASK_DUE_DATE,
    REMINDER_TITLE, REMINDER_DESC, REMINDER_TIME,
    EVENT_TITLE, EVENT_START, EVENT_END, EVENT_DESC, EVENT_LOCATION, EVENT_TYPE
)

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=getattr(logging, config.LOG_LEVEL)
)
logger = logging.getLogger(__name__)

# Глобальный экземпляр бота
bot_instance = None

async def error_handler(update, context):
    """Обработчик ошибок"""
    logger.error(msg="Произошла ошибка при обработке обновления:", exc_info=context.error)

async def post_init(application):
    """Инициализация после запуска приложения"""
    global bot_instance
    bot_instance = application.bot
    
    # Инициализировать БД
    init_db()
    
    # Запустить планировщик напоминаний
    reminder_scheduler.set_callback(send_reminder)
    reminder_scheduler.start()
    reminder_scheduler.reschedule_all_reminders()
    
    logger.info("✅ Бот инициализирован")

async def post_shutdown(application):
    """Очистка при остановке"""
    reminder_scheduler.stop()
    logger.info("⏹️ Бот остановлен")

def main():
    """Запуск бота"""
    config.validate()
    
    # Создание приложения
    application = Application.builder().token(config.BOT_TOKEN).build()
    
    # Обработчик /start
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    
    # Conversation Handler для задач
    task_conversation = ConversationHandler(
        entry_points=[CommandHandler("add_task", add_task_command), MessageHandler(filters.Regex("^➕ Создать задачу$"), add_task_command)],
        states={
            TASK_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, task_title_input)],
            TASK_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, task_description_input)],
            TASK_PRIORITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, task_priority_input)],
            TASK_DUE_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, task_due_date_input)],
        },
        fallbacks=[CommandHandler("cancel", cancel_command), MessageHandler(filters.Regex("^🔙 Отмена$"), cancel_command)],
    )
    
    # Conversation Handler для напоминаний
    reminder_conversation = ConversationHandler(
        entry_points=[CommandHandler("add_reminder", add_reminder_command), MessageHandler(filters.Regex("^➕ Новое напоминание$"), add_reminder_command)],
        states={
            REMINDER_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, reminder_title_input)],
            REMINDER_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, reminder_description_input)],
            REMINDER_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, reminder_time_input)],
        },
        fallbacks=[CommandHandler("cancel", cancel_command), MessageHandler(filters.Regex("^🔙 Отмена$"), cancel_command)],
    )
    
    # Conversation Handler для событий
    event_conversation = ConversationHandler(
        entry_points=[CommandHandler("add_event", add_event_command), MessageHandler(filters.Regex("^➕ Добавить событие$"), add_event_command)],
        states={
            EVENT_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, event_title_input)],
            EVENT_START: [MessageHandler(filters.TEXT & ~filters.COMMAND, event_start_time_input)],
            EVENT_END: [MessageHandler(filters.TEXT & ~filters.COMMAND, event_end_time_input)],
            EVENT_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, event_description_input)],
            EVENT_LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, event_location_input)],
            EVENT_TYPE: [CallbackQueryHandler(event_type_selection)],
        },
        fallbacks=[CommandHandler("cancel", cancel_command), MessageHandler(filters.Regex("^🔙 Отмена$"), cancel_command)],
    )
    
    # Добавление Conversation Handlers
    application.add_handler(task_conversation)
    application.add_handler(reminder_conversation)
    application.add_handler(event_conversation)
    
    # Обработчики команд
    application.add_handler(CommandHandler("my_tasks", my_tasks_command))
    application.add_handler(MessageHandler(filters.Regex("^📋 Мои задачи$"), my_tasks_command))
    application.add_handler(CommandHandler("my_reminders", my_reminders_command))
    application.add_handler(MessageHandler(filters.Regex("^📋 Мои напоминания$"), my_reminders_command))
    application.add_handler(CommandHandler("calendar", calendar_command))
    application.add_handler(MessageHandler(filters.Regex("^📅 Календарь$"), calendar_command))
    application.add_handler(CommandHandler("today_events", today_events_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(MessageHandler(filters.Regex("^📊 Статистика$"), stats_command))
    
    # Админ команды
    application.add_handler(CommandHandler("admin", admin_command))
    application.add_handler(MessageHandler(filters.Regex("^🔑 Админ-панель$"), admin_command))
    application.add_handler(CommandHandler("grant_admin", grant_admin_command))
    application.add_handler(CommandHandler("user_list", user_list_command))
    application.add_handler(MessageHandler(filters.Regex("^👥 Управление пользователями$"), user_list_command))
    application.add_handler(CommandHandler("broadcast", broadcast_command))
    application.add_handler(MessageHandler(filters.Regex("^📢 Рассылка$"), broadcast_command))
    application.add_handler(CommandHandler("users_stats", users_stats_command))
    application.add_handler(CommandHandler("system_info", system_info_command))
    
    # Обработчик рассылки
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.User(user_id=config.ADMIN_ID), broadcast_message_handler))
    
    # Callback обработчики
    application.add_handler(CallbackQueryHandler(task_callback_handler, pattern="^task_"))
    application.add_handler(CallbackQueryHandler(reminder_callback_handler, pattern="^reminder_"))
    application.add_handler(CallbackQueryHandler(event_callback_handler, pattern="^event_"))
    
    # Обработчик ошибок
    application.add_error_handler(error_handler)
    
    # Callbacks для жизненного цикла
    application.post_init = post_init
    application.post_shutdown = post_shutdown
    
    # Запуск бота
    logger.info("🚀 Запуск бота...")
    application.run_polling(allowed_updates=["message", "callback_query"])

if __name__ == "__main__":
    main()
