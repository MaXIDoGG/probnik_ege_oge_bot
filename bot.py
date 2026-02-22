import logging
import os
from datetime import datetime
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
EXAM_TYPE, EXAM_SLOT, TEACHER, NAME = range(4)

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
    
    # Получаем доступные слоты из таблицы
    try:
        slots = sheets.get_exam_slots()
    except Exception as e:
        logger.error(f"Ошибка получения слотов: {e}")
        await query.edit_message_text(
            "К сожалению, не удалось загрузить расписание. Попробуйте позже."
        )
        return ConversationHandler.END
    
    if not slots:
        await query.edit_message_text(
            "На данный момент нет доступных дат для записи. Обратитесь к организаторам."
        )
        return ConversationHandler.END
    
    keyboard = [
        [InlineKeyboardButton(slot["display"], callback_data=f"slot_{slot['index']}")]
        for slot in slots
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    user_data[user_id]["_slots"] = slots
    
    await query.edit_message_text(
        "Выбери дату и время экзамена:",
        reply_markup=reply_markup
    )
    
    return EXAM_SLOT


async def slot_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка выбора слота (дата и время)"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    slot_index = int(query.data.replace("slot_", ""))
    
    slots = user_data[user_id].get("_slots", [])
    slot = next((s for s in slots if s["index"] == slot_index), None)
    
    if not slot:
        await query.edit_message_text("Выбранный слот недоступен. Начните заново /start")
        return ConversationHandler.END
    
    user_data[user_id]["slot"] = slot
    user_data[user_id]["day_name"] = slot["day_name"]
    user_data[user_id]["time"] = slot["time"]
    user_data[user_id]["exam_datetime"] = slot["datetime_str"]
    user_data[user_id]["zoom"] = slot["zoom"]
    user_data[user_id]["contact"] = slot["contact"]
    
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
    
    # Дата и время берутся из выбранного слота (уже сохранены в user_data)
    
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
    
    # Формируем сообщение после регистрации
    slot = user_data[user_id].get("slot", {})
    date_str = slot.get("display", user_data[user_id].get("exam_datetime", ""))
    zoom_link = user_data[user_id].get("zoom", "https://us06web.zoom.us/j/9709286191")
    contact = user_data[user_id].get("contact", "@vasilina45")
    day_name = user_data[user_id].get("day_name", "")
    
    forms_link = "https://drive.google.com/file/d/1UcgVmYd2pulJ6tAqFGzY3xzY7n6UiJ2r/view?usp=drivesdk"
    day_in_text = "в субботу" if "суббот" in day_name.lower() else "в воскресенье"
    support_msg = (
        "Твоя поддержка на экзамене: \n"
        f"Во время пробника {day_in_text} с тобой будет находиться дежурный. "
        "Если возникнут любые технические сложности или вопросы по организации, сразу пиши в тг:\n"
        f"📱 {contact} ."
    )
    
    registration_message = (
        "ПРОБНЫЙ ЭКЗАМЕН\n\n"
        f"🔗 Дата и время: {date_str} \n"
        "☺️ Обязательное условие: Во время всего экзамена у тебя должна быть включена камера.\n\n"
        "Что нужно подготовить:\n"
        "- Черновик (любые листочки или тетрадь).\n"
        "- Бланки для ответов (если удалось распечатать).\n"
        "- Ручка, карандаш и линейка (на всякий случай).\n"
        "- Тихое и удобное место, где тебя никто не побеспокоит.\n"
        f"Бланки можно взять тут 👉  {forms_link}\n\n"
        f"{support_msg}\n\n"
        f"Подключайся по этой ссылке: {zoom_link}\n\n"
        "Ты уже знаешь намного больше, желаю показать тебе свой самый лучший результат🔥"
    )
    
    await update.message.reply_text(registration_message)
    
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
            EXAM_SLOT: [CallbackQueryHandler(slot_callback, pattern="^slot_")],
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
    
    # Функция для инициализации напоминаний после запуска бота
    async def post_init(app: Application) -> None:
        """Инициализация scheduler после запуска бота"""
        try:
            scheduler.initialize(sheets, app.bot)
            # Настраиваем периодическую проверку напоминаний каждую минуту
            job_queue = app.job_queue
            if job_queue:
                # Создаем обертку-функцию для job_queue
                async def check_reminders_callback(context: ContextTypes.DEFAULT_TYPE):
                    await scheduler.check_and_send_reminders(context)
                
                job_queue.run_repeating(
                    check_reminders_callback,
                    interval=60,  # Каждую минуту
                    first=10,  # Начинаем через 10 секунд после запуска
                    name="check_reminders"
                )
                logger.info("Периодическая проверка напоминаний настроена (каждую минуту)")
        except Exception as e:
            logger.error(f"Ошибка при инициализации напоминаний: {e}", exc_info=True)
    
    application.post_init = post_init
    
    # Запускаем бота
    logger.info("Бот запущен")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
