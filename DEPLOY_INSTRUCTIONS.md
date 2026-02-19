# Инструкция по деплою на облачный сервер

## Шаг 1: Закоммитьте и запушьте изменения (на вашем ПК)

```powershell
git add deploy.sh ege-bot.service
git commit -m "Add deploy script and systemd service"
git push origin main
```

## Шаг 2: Подключитесь к серверу по SSH

```powershell
ssh root@147.45.158.75
```

## Шаг 3: На сервере — деплой

Скопируйте и выполните в SSH-сессии:

```bash
# Клонирование репозитория
cd ~
git clone https://github.com/MaXIDoGG/probnik_ege_oge_bot.git EGE_BOT
cd EGE_BOT

# Создание виртуального окружения и установка зависимостей
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Установка systemd сервиса (автозапуск при рестарте)
sudo cp ege-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable ege-bot
```

## Шаг 4: Скопируйте .env и credentials.json на сервер

**В новом окне терминала на вашем ПК** (не выходя из папки EGE_BOT):

```powershell
scp .env root@147.45.158.75:~/EGE_BOT/
scp credentials.json root@147.45.158.75:~/EGE_BOT/
```

## Шаг 5: Запуск бота

Вернитесь в SSH-сессию и выполните:

```bash
sudo systemctl start ege-bot
sudo systemctl status ege-bot
```

Бот запущен и будет автоматически стартовать при каждой перезагрузке сервера.

---

**Полезные команды:**
- `sudo systemctl restart ege-bot` — перезапустить бота
- `sudo journalctl -u ege-bot -f` — смотреть логи в реальном времени
- `sudo systemctl stop ege-bot` — остановить бота
