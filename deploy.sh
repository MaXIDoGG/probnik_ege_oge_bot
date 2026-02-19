#!/bin/bash
# Скрипт деплоя бота на сервер
# Запускать на сервере (в SSH сессии)

set -e

APP_DIR="$HOME/EGE_BOT"
REPO_URL="https://github.com/MaXIDoGG/probnik_ege_oge_bot.git"

echo "=== Деплой EGE_BOT ==="

# Обновление или клонирование репозитория
if [ -d "$APP_DIR" ]; then
    echo "Обновление кода..."
    cd "$APP_DIR"
    git pull origin main 2>/dev/null || git pull origin master 2>/dev/null || true
else
    echo "Клонирование репозитория..."
    git clone "$REPO_URL" "$APP_DIR"
    cd "$APP_DIR"
fi

# Создание виртуального окружения
if [ ! -d "venv" ]; then
    echo "Создание виртуального окружения..."
    python3 -m venv venv
fi

echo "Активация venv и установка зависимостей..."
source venv/bin/activate
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Проверка наличия .env и credentials.json
if [ ! -f ".env" ]; then
    echo ""
    echo "ВНИМАНИЕ: Файл .env не найден!"
    echo "С вашего ПК выполните: scp .env root@147.45.158.75:$APP_DIR/"
    echo ""
fi

if [ ! -f "credentials.json" ]; then
    echo "ВНИМАНИЕ: Файл credentials.json не найден!"
    echo "С вашего ПК выполните: scp credentials.json root@147.45.158.75:$APP_DIR/"
    echo ""
fi

echo "=== Деплой завершён ==="
echo ""
echo "Для установки автозапуска выполните:"
echo "  sudo cp $APP_DIR/ege-bot.service /etc/systemd/system/"
echo "  sudo systemctl daemon-reload"
echo "  sudo systemctl enable ege-bot"
echo "  sudo systemctl start ege-bot"
echo ""
echo "Проверка статуса: sudo systemctl status ege-bot"
