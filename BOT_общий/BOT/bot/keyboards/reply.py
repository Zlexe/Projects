from telegram import ReplyKeyboardMarkup, KeyboardButton

def get_main_menu_keyboard():
    """Главное меню"""
    keyboard = [
        ["📝 Задачи", "🔔 Напоминания"],
        ["📅 Календарь", "📊 Статистика"],
        ["⚙️ Настройки"]
    ]
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=False
    )

def get_admin_menu_keyboard():
    """Админ меню"""
    keyboard = [
        ["📝 Задачи", "🔔 Напоминания"],
        ["📅 Календарь", "📊 Статистика"],
        ["👥 Управление пользователями"],
        ["📢 Рассылка", "⚙️ Настройки"],
        ["🔑 Админ-панель"]
    ]
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=False
    )

def get_tasks_menu_keyboard():
    """Меню задач"""
    keyboard = [
        ["➕ Создать задачу"],
        ["📋 Мои задачи", "✅ Завершённые"],
        ["⏳ В процессе", "🔙 Назад"]
    ]
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=False
    )

def get_reminders_menu_keyboard():
    """Меню напоминаний"""
    keyboard = [
        ["➕ Новое напоминание"],
        ["📋 Мои напоминания"],
        ["🔙 Назад"]
    ]
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=False
    )

def get_confirmation_keyboard():
    """Подтверждение действия"""
    keyboard = [
        ["✅ Да", "❌ Нет"]
    ]
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=True
    )

def get_priority_keyboard():
    """Выбор приоритета"""
    keyboard = [
        ["🔴 Высокий"],
        ["🟡 Средний"],
        ["🟢 Низкий"]
    ]
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=True
    )

def get_cancel_keyboard():
    """Кнопка отмены"""
    keyboard = [
        ["🔙 Отмена"]
    ]
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=True
    )
