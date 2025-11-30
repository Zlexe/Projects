from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum

Base = declarative_base()

class User(Base):
    """Модель пользователя"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, index=True, nullable=False)
    username = Column(String(100), nullable=True)
    full_name = Column(String(255), nullable=True)
    role = Column(String(20), default='STUDENT')  # STUDENT, ADMIN, SUPERADMIN
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связи
    reminders = relationship("Reminder", back_populates="user", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="user", cascade="all, delete-orphan")
    events = relationship("Event", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, telegram_id={self.telegram_id}, username={self.username}, role={self.role})>"


class Reminder(Base):
    """Модель напоминания"""
    __tablename__ = "reminders"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    scheduled_time = Column(DateTime, nullable=False, index=True)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связи
    user = relationship("User", back_populates="reminders")
    
    def __repr__(self):
        return f"<Reminder(id={self.id}, user_id={self.user_id}, title={self.title}, scheduled_time={self.scheduled_time})>"


class TaskStatus(str, enum.Enum):
    """Статусы задач"""
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class Task(Base):
    """Модель задачи"""
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    priority = Column(Integer, default=3)  # 1 - высокий, 3 - низкий
    status = Column(String(20), default=TaskStatus.TODO.value)
    due_date = Column(DateTime, nullable=True, index=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Связи
    user = relationship("User", back_populates="tasks")
    
    def __repr__(self):
        return f"<Task(id={self.id}, user_id={self.user_id}, title={self.title}, status={self.status})>"


class Event(Base):
    """Модель события для календаря"""
    __tablename__ = "events"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    start_time = Column(DateTime, nullable=False, index=True)
    end_time = Column(DateTime, nullable=False)
    location = Column(String(255), nullable=True)
    event_type = Column(String(50), default='FACULTY')  # FACULTY, PERSONAL, EXAM
    google_event_id = Column(String(255), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связи
    user = relationship("User", back_populates="events")
    
    def __repr__(self):
        return f"<Event(id={self.id}, user_id={self.user_id}, title={self.title}, start_time={self.start_time})>"


class Statistic(Base):
    """Модель статистики пользователя"""
    __tablename__ = "statistics"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, unique=True, index=True)
    total_tasks = Column(Integer, default=0)
    completed_tasks = Column(Integer, default=0)
    total_reminders = Column(Integer, default=0)
    triggered_reminders = Column(Integer, default=0)
    total_events = Column(Integer, default=0)
    
    last_activity = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Statistic(user_id={self.user_id}, completed_tasks={self.completed_tasks}/{self.total_tasks})>"
