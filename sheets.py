import os
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class GoogleSheets:
    """Класс для работы с Google Sheets"""
    
    def __init__(self):
        self.client = None
        self.spreadsheet = None
        self.worksheet = None
        self.schedule_worksheet = None
        self.sheet_id = os.getenv("GOOGLE_SHEET_ID")
        self.credentials_path = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")
    
    def initialize(self):
        """Инициализация подключения к Google Sheets"""
        try:
            # Определяем область доступа
            scope = [
                "https://spreadsheets.google.com/feeds",
                "https://www.googleapis.com/auth/drive"
            ]
            
            # Загружаем учетные данные
            creds = Credentials.from_service_account_file(
                self.credentials_path,
                scopes=scope
            )
            
            # Создаем клиент
            self.client = gspread.authorize(creds)
            
            # Открываем таблицу
            if not self.sheet_id:
                raise ValueError("GOOGLE_SHEET_ID не установлен")
            
            self.spreadsheet = self.client.open_by_key(self.sheet_id)
            
            # Получаем или создаем лист
            try:
                self.worksheet = self.spreadsheet.worksheet("Записи")
            except gspread.exceptions.WorksheetNotFound:
                # Создаем новый лист, если его нет
                self.worksheet = self.spreadsheet.add_worksheet(
                    title="Записи",
                    rows=1000,
                    cols=11
                )
                # Добавляем заголовки
                headers = [
                    "Дата записи",
                    "Telegram ID",
                    "Имя пользователя",
                    "Имя и фамилия",
                    "Тип экзамена",
                    "День",
                    "Время",
                    "Дата и время экзамена",
                    "Преподаватель",
                    "Напоминание за час отправлено",
                    "Напоминание за 15 минут отправлено"
                ]
                self.worksheet.append_row(headers)
            
            # Получаем или создаём лист "Даты экзаменов" с расписанием
            try:
                self.schedule_worksheet = self.spreadsheet.worksheet("Даты экзаменов")
                logger.info("Лист 'Даты экзаменов' найден")
            except gspread.exceptions.WorksheetNotFound:
                self.schedule_worksheet = self.spreadsheet.add_worksheet(
                    title="Даты экзаменов",
                    rows=100,
                    cols=5
                )
                # Заголовки: Дата, Время, Zoom, Контакт
                headers = ["Дата", "Время", "Zoom", "Контакт"]
                self.schedule_worksheet.append_row(headers)
                # Пример данных для заполнения (суббота 28.02, воскресенье 01.03)
                example_rows = [
                    ["28.02.2026", "11:00", "https://us06web.zoom.us/j/9709286191", "@vasilina45"],
                    ["28.02.2026", "15:00", "https://us06web.zoom.us/j/9709286191", "@vasilina45"],
                    ["01.03.2026", "10:00", "https://us06web.zoom.us/j/5621545595?pwd=EEaV6rb8Dr8UgaaL9AF4wbarlhraNV.1", "@dkvnastya"],
                    ["01.03.2026", "14:00", "https://us06web.zoom.us/j/5621545595?pwd=EEaV6rb8Dr8UgaaL9AF4wbarlhraNV.1", "@dkvnastya"],
                ]
                for row in example_rows:
                    self.schedule_worksheet.append_row(row)
                logger.info("Создан лист 'Даты экзаменов' с примером расписания")
            
            logger.info("Google Sheets успешно инициализирован")
            
        except Exception as e:
            logger.error(f"Ошибка инициализации Google Sheets: {e}")
            raise
    
    def save_registration(self, user_data: dict):
        """Сохранение данных регистрации в таблицу"""
        if not self.worksheet:
            raise RuntimeError("Google Sheets не инициализирован")
        
        # Подготавливаем данные для записи
        row = [
            datetime.now().strftime("%d.%m.%Y %H:%M:%S"),  # Дата записи в удобном формате
            user_data.get("telegram_id", ""),
            user_data.get("telegram_username", ""),
            user_data.get("full_name", ""),
            user_data.get("exam_type", ""),
            user_data.get("day_name", ""),
            user_data.get("time", ""),
            user_data.get("exam_datetime", ""),  # Формат: DD.MM.YYYY HH:MM
            user_data.get("teacher", ""),
            "Нет",  # Напоминание за час отправлено
            "Нет"   # Напоминание за 15 минут отправлено
        ]
        
        # Добавляем строку в таблицу
        self.worksheet.append_row(row)
        logger.info(f"Данные сохранены в Google Sheets: {user_data.get('full_name')}")
    
    def get_exam_slots(self):
        """
        Получение списка доступных слотов экзаменов из листа "Даты экзаменов".
        Возвращает список словарей: [{date, time, datetime_str, zoom, contact, day_name}, ...]
        Только слоты в будущем.
        """
        if not self.schedule_worksheet:
            raise RuntimeError("Google Sheets не инициализирован")
        
        records = self.schedule_worksheet.get_all_records()
        slots = []
        now = datetime.now()
        months_ru = ["", "января", "февраля", "марта", "апреля", "мая", "июня",
                     "июля", "августа", "сентября", "октября", "ноября", "декабря"]
        days_ru = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
        
        for idx, record in enumerate(records):
            date_str = str(record.get("Дата", "")).strip()
            time_str = str(record.get("Время", "")).strip()
            zoom = str(record.get("Zoom", "")).strip()
            contact = str(record.get("Контакт", "")).strip()
            
            if not date_str or not time_str:
                continue
            
            try:
                exam_date = datetime.strptime(date_str, "%d.%m.%Y")
                exam_time = datetime.strptime(time_str, "%H:%M").time()
                exam_datetime = datetime.combine(exam_date.date(), exam_time)
                
                if exam_datetime < now:
                    continue
                
                day_name = days_ru[exam_date.weekday()]
                display_date = f"{day_name}, {exam_date.day} {months_ru[exam_date.month]} {time_str}"
                datetime_str = exam_datetime.strftime("%d.%m.%Y %H:%M")
                
                slots.append({
                    "index": idx,
                    "date": date_str,
                    "time": time_str,
                    "datetime_str": datetime_str,
                    "exam_datetime": exam_datetime,
                    "zoom": zoom or "https://us06web.zoom.us/j/9709286191",
                    "contact": contact or "@vasilina45",
                    "day_name": day_name,
                    "display": display_date
                })
            except (ValueError, TypeError) as e:
                logger.warning(f"Ошибка парсинга слота: {date_str} {time_str}, {e}")
                continue
        
        return slots
    
    def get_all_exams_for_reminders(self):
        """Получение всех экзаменов для проверки напоминаний"""
        if not self.worksheet:
            raise RuntimeError("Google Sheets не инициализирован")
        
        # Получаем все записи
        records = self.worksheet.get_all_records()
        exams = []
        
        now = datetime.now()
        
        for idx, record in enumerate(records, start=2):  # Начинаем с 2, так как строка 1 - заголовки
            exam_datetime_str = record.get("Дата и время экзамена", "")
            if not exam_datetime_str:
                continue
            
            try:
                # Парсим формат DD.MM.YYYY HH:MM
                exam_datetime = datetime.strptime(exam_datetime_str, "%d.%m.%Y %H:%M")
                
                # Проверяем, что экзамен еще не прошел (с небольшим запасом в 15 минут после окончания)
                if exam_datetime >= now - timedelta(minutes=15):
                    reminder_1h_sent = record.get("Напоминание за час отправлено", "Нет").strip().lower()
                    reminder_15m_sent = record.get("Напоминание за 15 минут отправлено", "Нет").strip().lower()
                    
                    exams.append({
                        "row_number": idx,  # Номер строки для обновления
                        "telegram_id": record.get("Telegram ID", ""),
                        "exam_datetime": exam_datetime,
                        "full_name": record.get("Имя и фамилия", ""),
                        "day_name": record.get("День", ""),  # Суббота или Воскресенье
                        "reminder_1h_sent": reminder_1h_sent in ("да", "yes", "1", "true", "✓"),
                        "reminder_15m_sent": reminder_15m_sent in ("да", "yes", "1", "true", "✓")
                    })
            except ValueError as e:
                # Пробуем альтернативные форматы
                try:
                    # Формат ISO
                    exam_datetime = datetime.fromisoformat(exam_datetime_str.replace("Z", "+00:00"))
                    if exam_datetime.tzinfo:
                        exam_datetime = exam_datetime.replace(tzinfo=None)
                    
                    if exam_datetime >= now - timedelta(minutes=15):
                        reminder_1h_sent = record.get("Напоминание за час отправлено", "Нет").strip().lower()
                        reminder_15m_sent = record.get("Напоминание за 15 минут отправлено", "Нет").strip().lower()
                        
                        exams.append({
                            "row_number": idx,
                            "telegram_id": record.get("Telegram ID", ""),
                            "exam_datetime": exam_datetime,
                            "full_name": record.get("Имя и фамилия", ""),
                            "day_name": record.get("День", ""),
                            "reminder_1h_sent": reminder_1h_sent in ("да", "yes", "1", "true", "✓"),
                            "reminder_15m_sent": reminder_15m_sent in ("да", "yes", "1", "true", "✓")
                        })
                except (ValueError, TypeError) as e2:
                    logger.warning(f"Ошибка парсинга даты: {exam_datetime_str}, {e}, {e2}")
                    continue
            except (ValueError, TypeError) as e:
                logger.warning(f"Ошибка парсинга даты: {exam_datetime_str}, {e}")
                continue
        
        return exams
    
    def mark_reminder_sent(self, row_number: int, reminder_type: str):
        """Отметить напоминание как отправленное"""
        if not self.worksheet:
            raise RuntimeError("Google Sheets не инициализирован")
        
        # Определяем номер колонки (1-based)
        if reminder_type == "1h":
            col_number = 10  # "Напоминание за час отправлено"
        elif reminder_type == "15m":
            col_number = 11  # "Напоминание за 15 минут отправлено"
        else:
            raise ValueError(f"Неизвестный тип напоминания: {reminder_type}")
        
        try:
            # Обновляем ячейку
            self.worksheet.update_cell(row_number, col_number, "Да")
            logger.info(f"Напоминание {reminder_type} отмечено как отправленное для строки {row_number}")
        except Exception as e:
            logger.error(f"Ошибка при обновлении ячейки: {e}")
            raise
