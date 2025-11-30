import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Основные настройки приложения"""
    
    # Telegram
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    ADMIN_ID = int(os.getenv('ADMIN_ID', 0))
    
    # Database
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./student_tracker.db')
    
    # Google Calendar
    GOOGLE_CREDENTIALS_PATH = os.getenv('GOOGLE_CREDENTIALS_PATH', 'credentials.json')
    GOOGLE_CALENDAR_ID = os.getenv('GOOGLE_CALENDAR_ID')
    
    # Redis
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    # Приложение
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
    TIMEZONE = os.getenv('TIMEZONE', 'Europe/Moscow')
    
    # Логирование
    LOG_LEVEL = 'DEBUG' if DEBUG else 'INFO'
    
    @staticmethod
    def validate():
        """Проверка обязательных переменных"""
        required = ['BOT_TOKEN', 'ADMIN_ID']
        missing = [var for var in required if not os.getenv(var)]
        if missing:
            raise ValueError(f"Отсутствуют переменные окружения: {', '.join(missing)}")

config = Config()
