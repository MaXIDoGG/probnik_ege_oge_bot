import logging
import os
from datetime import datetime, timedelta
import pytz
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    ConversationHandler,
    filters
)
from dotenv import load_dotenv
from sheets import GoogleSheets
from scheduler import ReminderScheduler

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Состояния диалога
EXAM_TYPE, DAY, TIME, TEACHER, NAME = range(5)

# Инициализация Google Sheets
sheets = GoogleSheets()
scheduler = ReminderScheduler()

# Данные пользователей (временное хранилище)
user_data = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Начало диалога - выбор типа экзамена"""
    user_id = update.effective_user.id
    user_data[user_id] = {}
    
    keyboard = [
        [InlineKeyboardButton("ОГЭ", callback_data="exam_oge")],
        [InlineKeyboardButton("ЕГЭ Проф", callback_data="exam_ege_prof")],
        [InlineKeyboardButton("ЕГЭ База", callback_data="exam_ege_base")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "Выберите тип экзамена:",
        reply_markup=reply_markup
    )
    
    return EXAM_TYPE


async def exam_type_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка выбора типа экзамена"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    exam_type = query.data.replace("exam_", "")
    
    # Маппинг для читаемости
    exam_types = {
        "oge": "ОГЭ",
        "ege_prof": "ЕГЭ Проф",
        "ege_base": "ЕГЭ База"
    }
    
    user_data[user_id]["exam_type"] = exam_types.get(exam_type, exam_type)
    
    keyboard = [
        [InlineKeyboardButton("Суббота", callback_data="day_saturday")],
        [InlineKeyboardButton("Воскресенье", callback_data="day_sunday")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "Выбери день:",
        reply_markup=reply_markup
    )
    
    return DAY


async def day_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка выбора дня"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    day = query.data.replace("day_", "")
    
    user_data[user_id]["day"] = day
    
    # Определяем время в зависимости от дня
    if day == "saturday":
        times = ["11:00", "15:00"]
        day_name = "Суббота"
    else:  # sunday
        times = ["10:00", "14:00"]
        day_name = "Воскресенье"
    
    user_data[user_id]["day_name"] = day_name
    
    keyboard = [[InlineKeyboardButton(time, callback_data=f"time_{time}")] for time in times]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "Выбери время:",
        reply_markup=reply_markup
    )
    
    return TIME


async def time_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка выбора времени"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    time = query.data.replace("time_", "")
    
    user_data[user_id]["time"] = time
    
    keyboard = [
        [InlineKeyboardButton("Анастасия", callback_data="teacher_anastasia")],
        [InlineKeyboardButton("Василина", callback_data="teacher_vasilina")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "Выбери преподавателя:",
        reply_markup=reply_markup
    )
    
    return TEACHER


async def teacher_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка выбора преподавателя"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    teacher = query.data.replace("teacher_", "")
    
    # Маппинг для читаемости
    teachers = {
        "anastasia": "Анастасия",
        "vasilina": "Василина"
    }
    
    user_data[user_id]["teacher"] = teachers.get(teacher, teacher)
    
    await query.edit_message_text(
        "Введи своё имя и фамилию:"
    )
    
    return NAME


async def name_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка ввода имени и фамилии"""
    user_id = update.effective_user.id
    full_name = update.message.text.strip()
    
    if not full_name or len(full_name) < 3:
        await update.message.reply_text(
            "Пожалуйста, введите корректное имя и фамилию (минимум 3 символа):"
        )
        return NAME
    
    user_data[user_id]["full_name"] = full_name
    user_data[user_id]["telegram_id"] = user_id
    user_data[user_id]["telegram_username"] = update.effective_user.username or ""
    
    # Вычисляем дату экзамена
    today = datetime.now()
    day_name = user_data[user_id]["day_name"]
    
    # Находим ближайшую субботу или воскресенье
    days_ahead = 0
    if day_name == "Суббота":
        days_ahead = (5 - today.weekday()) % 7
        if days_ahead == 0 and today.weekday() != 5:
            days_ahead = 7
    else:  # Воскресенье
        days_ahead = (6 - today.weekday()) % 7
        if days_ahead == 0 and today.weekday() != 6:
            days_ahead = 7
    
    exam_date = today + timedelta(days=days_ahead)
    exam_time = user_data[user_id]["time"]
    
    # Создаем полную дату и время экзамена
    timezone = pytz.timezone("Europe/Moscow")
    exam_datetime = datetime.combine(exam_date.date(), datetime.strptime(exam_time, "%H:%M").time())
    exam_datetime = timezone.localize(exam_datetime)
    user_data[user_id]["exam_datetime"] = exam_datetime.isoformat()
    
    # Сохраняем в Google Sheets
    try:
        sheets.save_registration(user_data[user_id])
        logger.info(f"Данные пользователя {user_id} сохранены в Google Sheets")
    except Exception as e:
        logger.error(f"Ошибка при сохранении в Google Sheets: {e}")
        await update.message.reply_text(
            "Произошла ошибка при сохранении данных. Пожалуйста, попробуйте позже."
        )
        return ConversationHandler.END
    
    # Настраиваем напоминания
    try:
        scheduler.schedule_reminders(user_id, exam_datetime, context.bot)
        logger.info(f"Напоминания для пользователя {user_id} настроены")
    except Exception as e:
        logger.error(f"Ошибка при настройке напоминаний: {e}")
    
    # Отправляем ссылку на бланки
    forms_link = os.getenv("FORMS_LINK", "https://example.com/forms")
    
    await update.message.reply_text(
        f"Вот ссылка на бланки для заполнения: {forms_link}\n\n"
        f"Ваша запись:\n"
        f"Тип экзамена: {user_data[user_id]['exam_type']}\n"
        f"День: {day_name}\n"
        f"Время: {exam_time}\n"
        f"Преподаватель: {user_data[user_id]['teacher']}\n"
        f"Имя: {full_name}"
    )
    
    # Очищаем временные данные
    del user_data[user_id]
    
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отмена диалога"""
    user_id = update.effective_user.id
    if user_id in user_data:
        del user_data[user_id]
    
    await update.message.reply_text("Запись отменена.")
    return ConversationHandler.END


def main():
    """Запуск бота"""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN не установлен в переменных окружения")
    
    # Создаем приложение
    application = Application.builder().token(token).build()
    
    # Создаем ConversationHandler для диалога
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            EXAM_TYPE: [CallbackQueryHandler(exam_type_callback, pattern="^exam_")],
            DAY: [CallbackQueryHandler(day_callback, pattern="^day_")],
            TIME: [CallbackQueryHandler(time_callback, pattern="^time_")],
            TEACHER: [CallbackQueryHandler(teacher_callback, pattern="^teacher_")],
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, name_input)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    
    # Добавляем обработчики
    application.add_handler(conv_handler)
    
    # Инициализируем Google Sheets
    try:
        sheets.initialize()
        logger.info("Google Sheets инициализирован")
    except Exception as e:
        logger.error(f"Ошибка инициализации Google Sheets: {e}")
    
    # Функция для загрузки напоминаний после инициализации бота
    async def post_init(app: Application) -> None:
        """Загрузка напоминаний после инициализации бота"""
        try:
            await scheduler.load_reminders_from_sheets(sheets, app.bot)
        except Exception as e:
            logger.error(f"Ошибка при загрузке напоминаний: {e}")
    
    application.post_init = post_init
    
    # Запускаем бота
    logger.info("Бот запущен")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
