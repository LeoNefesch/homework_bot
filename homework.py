import logging
import os
import sys
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()


PRACTICUM_TOKEN = os.getenv('MY_PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('MY_TG_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('MY_TG_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(asctime)s - [%(levelname)s] - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


def check_tokens() -> None:
    """Проверка наличия и доступности переменных окружения."""
    if not all((PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID)):
        logger.critical('Недоступны переменные окружения!')
        raise KeyError('Проблема с наличием переменных окружения')


def send_message(bot: telegram.Bot, message: str) -> None:
    """Отправка сообщения."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logger.debug(f'Сообщение {message} отправлено.')
    except telegram.error.TelegramError as error:
        logger.error(f'Ошибка отправки сообщения: {error}.')


def get_api_answer(timestamp: int) -> dict:
    """Получение ответа от API."""
    payload = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=payload)
    except requests.RequestException as error:
        logger.error(f'{error}, недоступность эндпоинта.')
        raise requests.RequestException.InvalidURL(
            f'Ошибка ответа API: {error}.'
        )
    status = response.status_code
    if status != HTTPStatus.OK:
        logger.error(f'Ответ API: {status}')
        raise requests.RequestException.HTTPError(f'Status_code: {status}')
    return response.json()


def check_response(response: dict) -> dict:
    """Проверка ответа API на соответствие документации."""
    if not isinstance(response, dict):
        raise TypeError('Ответ API не является словарем')
    if 'homeworks' not in response:
        raise KeyError('В ответе API домашки нет ключа `homeworks`')
    if not isinstance(response['homeworks'], list):
        raise TypeError('По ключу `homeworks` данные не в виде списка')
    return response['homeworks'][0]


def parse_status(homework: dict) -> str:
    """Получение из ответа API статуса проверки работы."""
    if (not homework) or ('homework_name' not in homework):
        raise KeyError('Ключ homework_name отсутствует')
    if 'status' not in homework:
        raise KeyError('Ключ status отсутствует')
    homework_name = homework['homework_name']
    homework_status = homework['status']
    if homework_status not in HOMEWORK_VERDICTS:
        raise KeyError(f'{homework_status} '
                       f'отсутствует в словаре HOMEWORK_VERDICTS')
    verdict = HOMEWORK_VERDICTS[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main() -> None:
    """Основная логика работы бота."""
    if check_tokens():
        raise SystemExit(
            'Недоступны переменные окружения. '
            'Выполнение программы принудительно остановлено.'
        )
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = 0
    last_message = ''
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            status = parse_status(homeworks)
            if status != last_message:
                send_message(bot, status)
                last_message = status
        except OSError as error:
            logger.error(f'Сбой в работе программы: {error}')
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
