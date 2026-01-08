import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
import pytz

logger = logging.getLogger(__name__)


class ReminderScheduler:
    """Класс для управления напоминаниями"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.scheduler.start()
        self.timezone = pytz.timezone("Europe/Moscow")  # Московское время
    
    def schedule_reminders(self, user_id: int, exam_datetime: datetime, bot):
        """Настройка напоминаний для пользователя"""
        # Убеждаемся, что дата в правильном часовом поясе
        if exam_datetime.tzinfo is None:
            exam_datetime = self.timezone.localize(exam_datetime)
        
        # Напоминание за час до экзамена
        reminder_1h = exam_datetime - timedelta(hours=1)
        if reminder_1h > datetime.now(self.timezone):
            self.scheduler.add_job(
                self.send_reminder,
                DateTrigger(run_date=reminder_1h),
                args=[bot, user_id, "Напоминание: экзамен начнется через час"],
                id=f"reminder_1h_{user_id}_{exam_datetime.timestamp()}",
                replace_existing=True
            )
            logger.info(f"Напоминание за час настроено для пользователя {user_id} на {reminder_1h}")
        
        # Напоминание за 15 минут до экзамена
        reminder_15m = exam_datetime - timedelta(minutes=15)
        if reminder_15m > datetime.now(self.timezone):
            self.scheduler.add_job(
                self.send_reminder,
                DateTrigger(run_date=reminder_15m),
                args=[bot, user_id, "Напоминание: экзамен начнется через 15 минут"],
                id=f"reminder_15m_{user_id}_{exam_datetime.timestamp()}",
                replace_existing=True
            )
            logger.info(f"Напоминание за 15 минут настроено для пользователя {user_id} на {reminder_15m}")
    
    async def send_reminder(self, bot, user_id: int, message: str):
        """Отправка напоминания пользователю"""
        try:
            await bot.send_message(chat_id=user_id, text=message)
            logger.info(f"Напоминание отправлено пользователю {user_id}")
        except Exception as e:
            logger.error(f"Ошибка при отправке напоминания пользователю {user_id}: {e}")
    
    async def load_reminders_from_sheets(self, sheets, bot):
        """Загрузка напоминаний из Google Sheets при запуске бота"""
        try:
            upcoming_exams = sheets.get_upcoming_exams()
            for exam in upcoming_exams:
                telegram_id = exam.get("telegram_id")
                exam_datetime_str = exam.get("exam_datetime")
                
                if not telegram_id or not exam_datetime_str:
                    continue
                
                try:
                    if isinstance(exam_datetime_str, str):
                        exam_datetime = datetime.fromisoformat(exam_datetime_str)
                    else:
                        exam_datetime = exam_datetime_str
                    
                    if exam_datetime.tzinfo is None:
                        exam_datetime = self.timezone.localize(exam_datetime)
                    
                    self.schedule_reminders(int(telegram_id), exam_datetime, bot)
                except (ValueError, TypeError) as e:
                    logger.warning(f"Ошибка при загрузке напоминания: {e}")
                    continue
            
            logger.info(f"Загружено {len(upcoming_exams)} напоминаний из Google Sheets")
        except Exception as e:
            logger.error(f"Ошибка при загрузке напоминаний из Google Sheets: {e}")
