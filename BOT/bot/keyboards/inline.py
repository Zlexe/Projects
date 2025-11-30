from telegram import InlineKeyboardMarkup, InlineKeyboardButton

def get_task_actions_keyboard(task_id: int):
    """Кнопки действий для задачи"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Завершить", callback_data=f"task_complete_{task_id}"),
            InlineKeyboardButton("✏️ Редактировать", callback_data=f"task_edit_{task_id}")
        ],
        [
            InlineKeyboardButton("❌ Отменить", callback_data=f"task_cancel_{task_id}"),
            InlineKeyboardButton("🗑️ Удалить", callback_data=f"task_delete_{task_id}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_reminder_actions_keyboard(reminder_id: int, is_active: bool):
    """Кнопки действий для напоминания"""
    toggle_text = "⏸️ Отключить" if is_active else "▶️ Включить"
    keyboard = [
        [
            InlineKeyboardButton(toggle_text, callback_data=f"reminder_toggle_{reminder_id}"),
            InlineKeyboardButton("✏️ Редактировать", callback_data=f"reminder_edit_{reminder_id}")
        ],
        [
            InlineKeyboardButton("🗑️ Удалить", callback_data=f"reminder_delete_{reminder_id}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_event_actions_keyboard(event_id: int):
    """Кнопки действий для события"""
    keyboard = [
        [
            InlineKeyboardButton("✏️ Редактировать", callback_data=f"event_edit_{event_id}"),
            InlineKeyboardButton("🗑️ Удалить", callback_data=f"event_delete_{event_id}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_pagination_keyboard(page: int, total_pages: int, prefix: str):
    """Пагинация"""
    keyboard = []
    
    buttons = []
    if page > 1:
        buttons.append(InlineKeyboardButton("◀️ Назад", callback_data=f"{prefix}_page_{page-1}"))
    
    buttons.append(InlineKeyboardButton(f"{page}/{total_pages}", callback_data="noop"))
    
    if page < total_pages:
        buttons.append(InlineKeyboardButton("Вперёд ▶️", callback_data=f"{prefix}_page_{page+1}"))
    
    keyboard.append(buttons)
    
    return InlineKeyboardMarkup(keyboard)

def get_status_keyboard(task_id: int):
    """Выбор статуса задачи"""
    keyboard = [
        [
            InlineKeyboardButton("📝 TODO", callback_data=f"status_TODO_{task_id}"),
            InlineKeyboardButton("⏳ В процессе", callback_data=f"status_IN_PROGRESS_{task_id}"),
        ],
        [
            InlineKeyboardButton("✅ Завершено", callback_data=f"status_COMPLETED_{task_id}"),
            InlineKeyboardButton("❌ Отменено", callback_data=f"status_CANCELLED_{task_id}"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_yes_no_keyboard(action: str, data_id: int):
    """Подтверждение действия"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Да", callback_data=f"{action}_yes_{data_id}"),
            InlineKeyboardButton("❌ Нет", callback_data=f"{action}_no_{data_id}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_event_type_keyboard(event_id: int = None):
    """Выбор типа события"""
    keyboard = [
        [
            InlineKeyboardButton("🎓 Факультет", callback_data=f"event_type_FACULTY_{event_id or 'new'}"),
            InlineKeyboardButton("👤 Личное", callback_data=f"event_type_PERSONAL_{event_id or 'new'}")
        ],
        [
            InlineKeyboardButton("📝 Экзамен", callback_data=f"event_type_EXAM_{event_id or 'new'}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)
