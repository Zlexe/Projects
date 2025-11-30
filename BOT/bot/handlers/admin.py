from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from database.crud import UserCRUD, StatisticCRUD
from database.database import SessionLocal
from bot.keyboards.reply import get_admin_menu_keyboard
from bot.keyboards.inline import get_yes_no_keyboard
import logging

logger = logging.getLogger(__name__)

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Админ-панель"""
    db = SessionLocal()
    try:
        if not UserCRUD.is_admin(db, update.effective_user.id):
            await update.message.reply_text("❌ У вас нет доступа к админ-панели.")
            return
        
        admin_text = """
🔑 <b>Админ-панель</b>

Доступные команды:
/grant_admin - Назначить администратора
/user_list - Список пользователей
/broadcast - Отправить сообщение всем пользователям
/users_stats - Статистика по пользователям
/system_info - Информация о системе
"""
        
        await update.message.reply_text(
            admin_text,
            parse_mode=ParseMode.HTML,
            reply_markup=get_admin_menu_keyboard()
        )
    finally:
        db.close()

async def grant_admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Назначить администратора"""
    db = SessionLocal()
    try:
        if not UserCRUD.is_admin(db, update.effective_user.id):
            await update.message.reply_text("❌ Только администраторы могут назначать админов.")
            return
        
        if not context.args:
            await update.message.reply_text(
                "Использование: /grant_admin <telegram_id>"
            )
            return
        
        try:
            target_id = int(context.args[0])
        except ValueError:
            await update.message.reply_text("❌ Неверный telegram_id")
            return
        
        user = UserCRUD.set_admin(db, target_id, 'ADMIN')
        
        if user:
            await update.message.reply_text(
                f"✅ Пользователь {user.username} ({user.telegram_id}) назначен администратором."
            )
            logger.info(f"✅ Пользователь {target_id} назначен администратором")
        else:
            await update.message.reply_text("❌ Пользователь не найден.")
    finally:
        db.close()

async def user_list_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Список всех пользователей"""
    db = SessionLocal()
    try:
        if not UserCRUD.is_admin(db, update.effective_user.id):
            await update.message.reply_text("❌ Только администраторы могут просматривать список пользователей.")
            return
        
        from database.models import User
        users = db.query(User).all()
        
        if not users:
            await update.message.reply_text("📭 Нет пользователей в системе.")
            return
        
        message_text = f"👥 <b>Список пользователей ({len(users)})</b>\n\n"
        
        for user in users:
            message_text += f"<b>{user.full_name or 'Unknown'}</b>\n"
            message_text += f"ID: {user.telegram_id}\n"
            message_text += f"Username: @{user.username or 'N/A'}\n"
            message_text += f"Роль: {user.role}\n"
            message_text += f"Создан: {user.created_at.strftime('%d.%m.%Y')}\n\n"
        
        await update.message.reply_text(
            message_text,
            parse_mode=ParseMode.HTML
        )
    finally:
        db.close()

async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Начать массовую рассылку"""
    db = SessionLocal()
    try:
        if not UserCRUD.is_admin(db, update.effective_user.id):
            await update.message.reply_text("❌ Только администраторы могут отправлять рассылки.")
            return
        
        context.user_data['is_broadcasting'] = True
        
        await update.message.reply_text(
            "📢 Введите текст для рассылки всем пользователям:\n\n"
            "(Поддерживает HTML разметку)"
        )
    finally:
        db.close()

async def broadcast_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик текста для рассылки"""
    if not context.user_data.get('is_broadcasting'):
        return
    
    db = SessionLocal()
    try:
        if not UserCRUD.is_admin(db, update.effective_user.id):
            return
        
        from database.models import User
        from bot.main import bot_instance
        
        message_text = update.message.text
        users = db.query(User).all()
        
        success_count = 0
        for user in users:
            try:
                await bot_instance.send_message(
                    chat_id=user.telegram_id,
                    text=message_text,
                    parse_mode=ParseMode.HTML
                )
                success_count += 1
            except Exception as e:
                logger.warning(f"⚠️ Не удалось отправить сообщение пользователю {user.telegram_id}: {e}")
        
        await update.message.reply_text(
            f"✅ Рассылка завершена.\n"
            f"Успешно отправлено: {success_count}/{len(users)}"
        )
        
        context.user_data['is_broadcasting'] = False
        logger.info(f"📢 Рассылка отправлена {success_count} пользователям")
    except Exception as e:
        logger.error(f"❌ Ошибка при рассылке: {e}")
        await update.message.reply_text("❌ Произошла ошибка при отправке рассылки.")
    finally:
        db.close()

async def users_stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Статистика по пользователям"""
    db = SessionLocal()
    try:
        if not UserCRUD.is_admin(db, update.effective_user.id):
            await update.message.reply_text("❌ Только администраторы могут просматривать статистику.")
            return
        
        from database.models import User, Statistic
        
        total_users = db.query(User).count()
        total_admins = db.query(User).filter(User.role.in_(['ADMIN', 'SUPERADMIN'])).count()
        
        stats = db.query(Statistic).all()
        
        total_tasks = sum(s.total_tasks for s in stats)
        completed_tasks = sum(s.completed_tasks for s in stats)
        total_reminders = sum(s.total_reminders for s in stats)
        total_events = sum(s.total_events for s in stats)
        
        message_text = "📊 <b>Статистика системы</b>\n\n"
        message_text += f"👥 Всего пользователей: {total_users}\n"
        message_text += f"🔑 Администраторов: {total_admins}\n\n"
        message_text += f"📝 Всего задач: {total_tasks}\n"
        message_text += f"✅ Завершено задач: {completed_tasks}\n"
        message_text += f"🔔 Всего напоминаний: {total_reminders}\n"
        message_text += f"📅 Всего событий: {total_events}\n"
        
        await update.message.reply_text(
            message_text,
            parse_mode=ParseMode.HTML
        )
    finally:
        db.close()

async def system_info_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Информация о системе"""
    db = SessionLocal()
    try:
        if not UserCRUD.is_admin(db, update.effective_user.id):
            await update.message.reply_text("❌ Только администраторы могут просматривать информацию о системе.")
            return
        
        from bot.config import config
        import platform
        
        info_text = "⚙️ <b>Информация о системе</b>\n\n"
        info_text += f"🐍 Python: {platform.python_version()}\n"
        info_text += f"📝 ОС: {platform.system()} {platform.release()}\n"
        info_text += f"🌍 Часовой пояс: {config.TIMEZONE}\n"
        info_text += f"🔧 Режим отладки: {'Включен' if config.DEBUG else 'Отключен'}\n"
        
        await update.message.reply_text(
            info_text,
            parse_mode=ParseMode.HTML
        )
    finally:
        db.close()
