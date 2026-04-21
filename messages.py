from __future__ import annotations


# --- Общие тексты диалога ---

TEXT_CHOOSE_EXAM_TYPE = "Выберите тип экзамена:"
TEXT_SCHEDULE_LOAD_ERROR = "К сожалению, не удалось загрузить расписание. Попробуйте позже."
TEXT_NO_SLOTS = "На данный момент нет доступных дат для записи. Обратитесь к организаторам."
TEXT_CHOOSE_SLOT = "Выбери дату и время экзамена:"
TEXT_SLOT_UNAVAILABLE = "Выбранный слот недоступен. Начните заново /start"
TEXT_CHOOSE_TEACHER = "Выбери преподавателя:"
TEXT_ENTER_FULL_NAME = "Введи своё имя и фамилию:"
TEXT_INVALID_FULL_NAME = "Пожалуйста, введите корректное имя и фамилию (минимум 3 символа):"
TEXT_SAVE_ERROR = "Произошла ошибка при сохранении данных. Пожалуйста, попробуйте позже."
TEXT_CANCELLED = "Запись отменена."

# --- Массовое уведомление ---

TEXT_NEW_EXAM_ANNOUNCEMENT = (
    "Привет!\n\n"
    "Мы, Анастасия и Василина, приглашаем вас на последний в этом учебном году "
    "пробный экзамен по математике! 🎓\n\n"
    "Это ваша финальная возможность проверить себя перед основным экзаменом, "
    "увидеть свои слабые места и понять, над чем ещё стоит поработать.\n\n"
    "Пробник пройдёт, как обычно, в Zoom. Выбирайте удобный день и время и "
    "записывайтесь! 👇\n\n"
    "Ждём вас!"
)


# --- Ссылки ---

FORMS_LINK = (
    "https://drive.google.com/file/d/1UcgVmYd2pulJ6tAqFGzY3xzY7n6UiJ2r/view?usp=drivesdk"
)

ZOOM_SATURDAY = "https://us06web.zoom.us/j/9709286191"
ZOOM_SUNDAY = "https://us06web.zoom.us/j/5621545595?pwd=EEaV6rb8Dr8UgaaL9AF4wbarlhraNV.1"


def zoom_link_for_day_name(day_name: str) -> str:
    day = (day_name or "").strip().lower()
    return ZOOM_SUNDAY if "воскрес" in day else ZOOM_SATURDAY


# --- Напоминания ---

def reminder_1h_text(zoom_link: str) -> str:
    return (
        "У тебя экзамен через час, ещё раз держи ссылку, на всякий случай "
        f"{zoom_link}\n"
        "Удачи🍀"
    )


TEXT_REMINDER_15M = "Экзамен через 15 минут, подготовь всё что нужно и заходи🌚"


# --- Сообщение после регистрации ---

def support_text(day_name: str, contact: str) -> str:
    day = (day_name or "").strip().lower()
    day_in_text = "в субботу" if "суббот" in day else "в воскресенье"
    return (
        "Твоя поддержка на экзамене: \n"
        f"Во время пробника {day_in_text} с тобой будет находиться дежурный. "
        "Если возникнут любые технические сложности или вопросы по организации, сразу пиши в тг:\n"
        f"📱 {contact} ."
    )


def registration_message_text(
    *,
    date_str: str,
    zoom_link: str,
    contact: str,
    day_name: str,
) -> str:
    return (
        "ПРОБНЫЙ ЭКЗАМЕН\n\n"
        f"🔗 Дата и время: {date_str} \n"
        "☺️ Обязательное условие: Во время всего экзамена у тебя должна быть включена камера.\n\n"
        "Что нужно подготовить:\n"
        "- Черновик (любые листочки или тетрадь).\n"
        "- Бланки для ответов (если удалось распечатать).\n"
        "- Ручка, карандаш и линейка (на всякий случай).\n"
        "- Тихое и удобное место, где тебя никто не побеспокоит.\n"
        f"Бланки можно взять тут 👉  {FORMS_LINK}\n\n"
        f"{support_text(day_name, contact)}\n\n"
        f"Подключайся по этой ссылке: {zoom_link}\n\n"
        "Ты уже знаешь намного больше, желаю показать тебе свой самый лучший результат🔥"
    )

