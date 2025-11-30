"""
Скрипт для инициализации базы данных
Используется: python init_db.py
"""

import os
from database.database import init_db
from bot.config import config

def main():
    print("🔄 Инициализация базы данных...")
    print(f"📍 Используется база: {config.DATABASE_URL}")
    
    try:
        init_db()
        print("✅ База данных успешно инициализирована!")
        print("📋 Все таблицы созданы.")
    except Exception as e:
        print(f"❌ Ошибка при инициализации БД: {e}")
        exit(1)

if __name__ == "__main__":
    main()
