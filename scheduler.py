import logging
from datetime import datetime, timedelta
import pytz

logger = logging.getLogger(__name__)


class ReminderScheduler:
    """Класс для управления напоминаниями через периодическую проверку Google Sheets"""
    
    def __init__(self):
        self.timezone = pytz.timezone("Europe/Moscow")  # Московское время
        self.sheets = None
        self.bot = None
    
    def initialize(self, sheets, bot):
        """Инициализация с Google Sheets и ботом"""
        self.sheets = sheets
        self.bot = bot
        logger.info("ReminderScheduler инициализирован")
    
    async def check_and_send_reminders(self, context=None):
        """Проверка и отправка напоминаний (вызывается каждую минуту)"""
        if not self.sheets:
            logger.warning("ReminderScheduler не инициализирован (нет sheets)")
            return
        
        # Используем bot из context, если передан, иначе из self.bot
        bot = context.bot if context and hasattr(context, 'bot') else self.bot
        if not bot:
            logger.warning("ReminderScheduler не инициализирован (нет bot)")
            return
        
        try:
            # Получаем все экзамены из таблицы
            exams = self.sheets.get_all_exams_for_reminders()
            
            now = datetime.now()
            sent_count = 0
            
            for exam in exams:
                exam_datetime = exam["exam_datetime"]
                telegram_id = exam.get("telegram_id", "")
                
                if not telegram_id:
                    continue
                
                try:
                    telegram_id = int(telegram_id)
                except (ValueError, TypeError):
                    logger.warning(f"Некорректный Telegram ID: {telegram_id}")
                    continue
                
                # Проверяем напоминание за час
                reminder_1h_time = exam_datetime - timedelta(hours=1)
                if not exam["reminder_1h_sent"]:
                    # Проверяем, нужно ли отправить сейчас (с допуском в 1 минуту)
                    time_diff = (reminder_1h_time - now).total_seconds()
                    if 0 <= time_diff <= 60:  # В пределах 1 минуты
                        try:
                            await bot.send_message(
                                chat_id=telegram_id,
                                text="Напоминание: экзамен начнется через час"
                            )
                            # Отмечаем как отправленное в таблице
                            self.sheets.mark_reminder_sent(exam["row_number"], "1h")
                            sent_count += 1
                            logger.info(f"Напоминание за час отправлено пользователю {telegram_id} ({exam.get('full_name', '')})")
                        except Exception as e:
                            logger.error(f"Ошибка при отправке напоминания за час пользователю {telegram_id}: {e}")
                
                # Проверяем напоминание за 15 минут
                reminder_15m_time = exam_datetime - timedelta(minutes=15)
                if not exam["reminder_15m_sent"]:
                    # Проверяем, нужно ли отправить сейчас (с допуском в 1 минуту)
                    time_diff = (reminder_15m_time - now).total_seconds()
                    if 0 <= time_diff <= 60:  # В пределах 1 минуты
                        try:
                            await bot.send_message(
                                chat_id=telegram_id,
                                text="Напоминание: экзамен начнется через 15 минут"
                            )
                            # Отмечаем как отправленное в таблице
                            self.sheets.mark_reminder_sent(exam["row_number"], "15m")
                            sent_count += 1
                            logger.info(f"Напоминание за 15 минут отправлено пользователю {telegram_id} ({exam.get('full_name', '')})")
                        except Exception as e:
                            logger.error(f"Ошибка при отправке напоминания за 15 минут пользователю {telegram_id}: {e}")
            
            if sent_count > 0:
                logger.info(f"Отправлено {sent_count} напоминаний")
                
        except Exception as e:
            logger.error(f"Ошибка при проверке напоминаний: {e}", exc_info=True)
