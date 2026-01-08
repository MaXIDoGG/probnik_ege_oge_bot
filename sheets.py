import os
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class GoogleSheets:
    """Класс для работы с Google Sheets"""
    
    def __init__(self):
        self.client = None
        self.spreadsheet = None
        self.worksheet = None
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
                    cols=10
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
                    "Преподаватель"
                ]
                self.worksheet.append_row(headers)
            
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
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),  # Дата записи
            user_data.get("telegram_id", ""),
            user_data.get("telegram_username", ""),
            user_data.get("full_name", ""),
            user_data.get("exam_type", ""),
            user_data.get("day_name", ""),
            user_data.get("time", ""),
            user_data.get("exam_datetime", ""),
            user_data.get("teacher", "")
        ]
        
        # Добавляем строку в таблицу
        self.worksheet.append_row(row)
        logger.info(f"Данные сохранены в Google Sheets: {user_data.get('full_name')}")
    
    def get_upcoming_exams(self):
        """Получение списка предстоящих экзаменов из таблицы"""
        if not self.worksheet:
            raise RuntimeError("Google Sheets не инициализирован")
        
        # Получаем все записи
        records = self.worksheet.get_all_records()
        upcoming_exams = []
        
        now = datetime.now()
        
        for record in records:
            exam_datetime_str = record.get("Дата и время экзамена", "")
            if not exam_datetime_str:
                continue
            
            try:
                exam_datetime = datetime.fromisoformat(exam_datetime_str)
                if exam_datetime > now:
                    upcoming_exams.append({
                        "telegram_id": record.get("Telegram ID", ""),
                        "exam_datetime": exam_datetime,
                        "full_name": record.get("Имя и фамилия", "")
                    })
            except (ValueError, TypeError) as e:
                logger.warning(f"Ошибка парсинга даты: {exam_datetime_str}, {e}")
                continue
        
        return upcoming_exams
