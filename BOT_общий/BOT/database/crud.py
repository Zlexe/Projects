from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from datetime import datetime, timedelta
from database.models import User, Reminder, Task, Event, Statistic, TaskStatus

# ============= USER OPERATIONS =============

class UserCRUD:
    @staticmethod
    def get_or_create(db: Session, telegram_id: int, username: str = None, full_name: str = None):
        """Получить или создать пользователя"""
        user = db.query(User).filter(User.telegram_id == telegram_id).first()
        if not user:
            user = User(
                telegram_id=telegram_id,
                username=username,
                full_name=full_name,
                role='STUDENT'
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        return user
    
    @staticmethod
    def get_by_telegram_id(db: Session, telegram_id: int):
        """Получить пользователя по telegram_id"""
        return db.query(User).filter(User.telegram_id == telegram_id).first()
    
    @staticmethod
    def get_by_id(db: Session, user_id: int):
        """Получить пользователя по ID"""
        return db.query(User).filter(User.id == user_id).first()
    
    @staticmethod
    def get_all_admins(db: Session):
        """Получить всех администраторов"""
        return db.query(User).filter(User.role.in_(['ADMIN', 'SUPERADMIN'])).all()
    
    @staticmethod
    def set_admin(db: Session, telegram_id: int, role: str = 'ADMIN'):
        """Назначить администратора"""
        user = db.query(User).filter(User.telegram_id == telegram_id).first()
        if user:
            user.role = role
            db.commit()
            db.refresh(user)
        return user
    
    @staticmethod
    def is_admin(db: Session, telegram_id: int):
        """Проверить, является ли пользователь администратором"""
        user = db.query(User).filter(User.telegram_id == telegram_id).first()
        return user and user.role in ['ADMIN', 'SUPERADMIN']
    
    @staticmethod
    def update_profile(db: Session, telegram_id: int, username: str = None, full_name: str = None):
        """Обновить профиль пользователя"""
        user = db.query(User).filter(User.telegram_id == telegram_id).first()
        if user:
            if username:
                user.username = username
            if full_name:
                user.full_name = full_name
            db.commit()
            db.refresh(user)
        return user


# ============= REMINDER OPERATIONS =============

class ReminderCRUD:
    @staticmethod
    def create(db: Session, user_id: int, title: str, description: str = None, scheduled_time: datetime = None):
        """Создать напоминание"""
        reminder = Reminder(
            user_id=user_id,
            title=title,
            description=description,
            scheduled_time=scheduled_time or datetime.utcnow()
        )
        db.add(reminder)
        db.commit()
        db.refresh(reminder)
        return reminder
    
    @staticmethod
    def get_user_reminders(db: Session, user_id: int, active_only: bool = True):
        """Получить напоминания пользователя"""
        query = db.query(Reminder).filter(Reminder.user_id == user_id)
        if active_only:
            query = query.filter(Reminder.is_active == True)
        return query.order_by(desc(Reminder.scheduled_time)).all()
    
    @staticmethod
    def get_upcoming_reminders(db: Session, minutes: int = 5):
        """Получить напоминания на ближайшие N минут"""
        now = datetime.utcnow()
        soon = now + timedelta(minutes=minutes)
        return db.query(Reminder).filter(
            and_(
                Reminder.scheduled_time >= now,
                Reminder.scheduled_time <= soon,
                Reminder.is_active == True
            )
        ).all()
    
    @staticmethod
    def get_by_id(db: Session, reminder_id: int):
        """Получить напоминание по ID"""
        return db.query(Reminder).filter(Reminder.id == reminder_id).first()
    
    @staticmethod
    def delete(db: Session, reminder_id: int):
        """Удалить напоминание"""
        reminder = db.query(Reminder).filter(Reminder.id == reminder_id).first()
        if reminder:
            db.delete(reminder)
            db.commit()
            return True
        return False
    
    @staticmethod
    def toggle_active(db: Session, reminder_id: int):
        """Переключить статус напоминания"""
        reminder = db.query(Reminder).filter(Reminder.id == reminder_id).first()
        if reminder:
            reminder.is_active = not reminder.is_active
            db.commit()
            db.refresh(reminder)
        return reminder


# ============= TASK OPERATIONS =============

class TaskCRUD:
    @staticmethod
    def create(db: Session, user_id: int, title: str, description: str = None, 
               priority: int = 3, due_date: datetime = None):
        """Создать задачу"""
        task = Task(
            user_id=user_id,
            title=title,
            description=description,
            priority=priority,
            due_date=due_date,
            status=TaskStatus.TODO.value
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        return task
    
    @staticmethod
    def get_user_tasks(db: Session, user_id: int, status: str = None):
        """Получить задачи пользователя"""
        query = db.query(Task).filter(Task.user_id == user_id)
        if status:
            query = query.filter(Task.status == status)
        return query.order_by(Task.priority, desc(Task.created_at)).all()
    
    @staticmethod
    def get_by_id(db: Session, task_id: int):
        """Получить задачу по ID"""
        return db.query(Task).filter(Task.id == task_id).first()
    
    @staticmethod
    def update_status(db: Session, task_id: int, status: str):
        """Обновить статус задачи"""
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = status
            if status == TaskStatus.COMPLETED.value:
                task.completed_at = datetime.utcnow()
            db.commit()
            db.refresh(task)
        return task
    
    @staticmethod
    def delete(db: Session, task_id: int):
        """Удалить задачу"""
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            db.delete(task)
            db.commit()
            return True
        return False
    
    @staticmethod
    def update(db: Session, task_id: int, title: str = None, description: str = None, 
               priority: int = None, due_date: datetime = None):
        """Обновить задачу"""
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            if title:
                task.title = title
            if description is not None:
                task.description = description
            if priority:
                task.priority = priority
            if due_date:
                task.due_date = due_date
            db.commit()
            db.refresh(task)
        return task


# ============= EVENT OPERATIONS =============

class EventCRUD:
    @staticmethod
    def create(db: Session, user_id: int, title: str, start_time: datetime, end_time: datetime,
               description: str = None, location: str = None, event_type: str = 'FACULTY'):
        """Создать событие"""
        event = Event(
            user_id=user_id,
            title=title,
            start_time=start_time,
            end_time=end_time,
            description=description,
            location=location,
            event_type=event_type
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        return event
    
    @staticmethod
    def get_user_events(db: Session, user_id: int, days_ahead: int = 7):
        """Получить события пользователя на N дней вперед"""
        now = datetime.utcnow()
        future = now + timedelta(days=days_ahead)
        return db.query(Event).filter(
            and_(
                Event.user_id == user_id,
                Event.start_time >= now,
                Event.start_time <= future
            )
        ).order_by(Event.start_time).all()
    
    @staticmethod
    def get_by_id(db: Session, event_id: int):
        """Получить событие по ID"""
        return db.query(Event).filter(Event.id == event_id).first()
    
    @staticmethod
    def delete(db: Session, event_id: int):
        """Удалить событие"""
        event = db.query(Event).filter(Event.id == event_id).first()
        if event:
            db.delete(event)
            db.commit()
            return True
        return False
    
    @staticmethod
    def get_today_events(db: Session, user_id: int):
        """Получить события на сегодня"""
        now = datetime.utcnow()
        today_end = now.replace(hour=23, minute=59, second=59)
        return db.query(Event).filter(
            and_(
                Event.user_id == user_id,
                Event.start_time >= now,
                Event.start_time <= today_end
            )
        ).order_by(Event.start_time).all()


# ============= STATISTIC OPERATIONS =============

class StatisticCRUD:
    @staticmethod
    def get_or_create(db: Session, user_id: int):
        """Получить или создать статистику"""
        stat = db.query(Statistic).filter(Statistic.user_id == user_id).first()
        if not stat:
            stat = Statistic(user_id=user_id)
            db.add(stat)
            db.commit()
            db.refresh(stat)
        return stat
    
    @staticmethod
    def update_stats(db: Session, user_id: int):
        """Обновить статистику пользователя"""
        stat = StatisticCRUD.get_or_create(db, user_id)
        
        # Подсчёт завершённых задач
        completed_tasks = db.query(Task).filter(
            and_(Task.user_id == user_id, Task.status == TaskStatus.COMPLETED.value)
        ).count()
        
        total_tasks = db.query(Task).filter(Task.user_id == user_id).count()
        total_reminders = db.query(Reminder).filter(Reminder.user_id == user_id).count()
        total_events = db.query(Event).filter(Event.user_id == user_id).count()
        
        stat.completed_tasks = completed_tasks
        stat.total_tasks = total_tasks
        stat.total_reminders = total_reminders
        stat.total_events = total_events
        stat.last_activity = datetime.utcnow()
        
        db.commit()
        db.refresh(stat)
        return stat
    
    @staticmethod
    def get_stats(db: Session, user_id: int):
        """Получить статистику"""
        return StatisticCRUD.get_or_create(db, user_id)
