# Проект python telegram bot
### О чём проект?
Перед Вами Telegram-бот, который обращается к API сервиса Практикум.Домашка и узнаёт статус проверки вашей домашней работы.

##### Функционал:
- раз в 10 минут обращаться к API сервиса Практикум.Домашка и проверять статус работы;
- при обновлении статуса отправлять вам в чат Telegram соответствующее сообщение;
- логировать свою работу и сообщать вам о важных проблемах сообщением в Telegram.

**Стэк технологий:**
- Python 3.9
- python-dotenv 0.19.0
- python-telegram-bot 13.7
- requests 2.26.0

### Как запустить проект:

Клонировать репозиторий и перейти в него в командной строке:

```
git clone git@github.com:LeoNefesch/homework_bot.git
```

```
cd homework_bot
```

Cоздать и активировать виртуальное окружение:

```
python3 -m venv venv
```

```
source v env/bin/activate
```

Установить зависимости из файла requirements.txt:

```
python3 -m pip install --upgrade pip
```

```
pip install -r requirements.txt
```

Запустить файл homework.py:

```
python3 homework.py
```
