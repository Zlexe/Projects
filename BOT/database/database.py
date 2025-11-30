from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from bot.config import config
from database.models import Base

# Создание engine
if config.DATABASE_URL.startswith('sqlite'):
    engine = create_engine(
        config.DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=config.DEBUG
    )
else:
    engine = create_engine(
        config.DATABASE_URL,
        echo=config.DEBUG,
        pool_pre_ping=True
    )

# Создание SessionLocal
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Session:
    """Dependency для получения сессии БД"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Инициализация базы данных"""
    Base.metadata.create_all(bind=engine)
    print("✅ База данных инициализирована")

async def get_db_async() -> Session:
    """Асинхронное получение сессии"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
