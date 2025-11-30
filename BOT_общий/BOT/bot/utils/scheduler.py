from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from database.database import SessionLocal
from database.crud import ReminderCRUD
from bot.config import config
import logging

logger = logging.getLogger(__name__)

class ReminderScheduler:
    """Класс для управления расписанием напоминаний"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler(timezone=config.TIMEZONE)
        self.callback = None
    
    def start(self):
        """Запустить планировщик"""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("✅ Scheduler запущен")
    
    def stop(self):
        """Остановить планировщик"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("⏹️ Scheduler остановлен")
    
    def set_callback(self, callback):
        """Установить callback для напоминаний"""
        self.callback = callback
    
    def add_reminder_job(self, reminder_id: int, scheduled_time: datetime):
        """Добавить задачу для напоминания"""
        job_id = f"reminder_{reminder_id}"
        
        # Удалить старую задачу если существует
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)
        
        # Добавить новую задачу
        self.scheduler.add_job(
            self._trigger_reminder,
            args=(reminder_id,),
            trigger='date',
            run_date=scheduled_time,
            id=job_id,
            replace_existing=True
        )
        logger.info(f"➕ Напоминание {reminder_id} запланировано на {scheduled_time}")
    
    def remove_reminder_job(self, reminder_id: int):
        """Удалить задачу напоминания"""
        job_id = f"reminder_{reminder_id}"
        job = self.scheduler.get_job(job_id)
        if job:
            job.remove()
            logger.info(f"➖ Напоминание {reminder_id} удалено из расписания")
    
    async def _trigger_reminder(self, reminder_id: int):
        """Триггер напоминания"""
        try:
            db = SessionLocal()
            reminder = ReminderCRUD.get_by_id(db, reminder_id)
            
            if reminder and self.callback:
                await self.callback(reminder)
                logger.info(f"🔔 Напоминание {reminder_id} отправлено")
            
            db.close()
        except Exception as e:
            logger.error(f"❌ Ошибка при запуске напоминания {reminder_id}: {e}")
    
    def reschedule_all_reminders(self):
        """Переспланировать все активные напоминания"""
        try:
            db = SessionLocal()
            now = datetime.utcnow()
            
            # Получить все активные напоминания на будущее
            upcoming = db.query(ReminderCRUD.__class__.__bases__[0]).filter(
                ReminderCRUD.scheduled_time >= now,
                ReminderCRUD.is_active == True
            ).all()
            
            for reminder in upcoming:
                self.add_reminder_job(reminder.id, reminder.scheduled_time)
            
            logger.info(f"🔄 Переспланировано {len(upcoming)} напоминаний")
            db.close()
        except Exception as e:
            logger.error(f"❌ Ошибка при перепланировании напоминаний: {e}")

# Глобальный экземпляр планировщика
reminder_scheduler = ReminderScheduler()
