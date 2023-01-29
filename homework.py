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


def check_tokens():
    """Проверка наличия и доступности переменных окружения."""
    if not (PRACTICUM_TOKEN and TELEGRAM_TOKEN and TELEGRAM_CHAT_ID):
        logger.critical('Недоступны переменные окружения!')
        raise KeyError('Проблема с наличием переменных окружения')
    return (PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID)


def send_message(bot, message):
    """Отправка сообщения."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logger.debug(f'Сообщение {message} отправлено.')
    except Exception as error:
        logger.error(f'Ошибка отправки сообщения: {error}.')


def get_api_answer(timestamp):
    """Получение ответа от API."""
    payload = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=payload)
    except requests.RequestException as error:
        logger.error(f'{error}, недоступность эндпоинта.')
        raise Exception(f'Ошибка ответа API: {error}.')
    status = response.status_code
    if status != HTTPStatus.OK:
        logger.error(f'Ответ API: {status}')
        raise Exception(f'Status_code: {status}')
    response = response.json()
    return response


def check_response(response):
    """Проверка ответа API на соответствие документации."""
    if not isinstance(response, dict):
        raise TypeError('Ответ API не является словарем')
    if 'homeworks' not in response:
        raise Exception('В ответе API домашки нет ключа `homeworks`')
    if not isinstance(response.get('homeworks'), list):
        raise TypeError('По ключу `homeworks` данные не в виде списка')
    return response['homeworks'][0]


def parse_status(homework):
    """Получение из ответа API статуса проверки работы."""
    if not homework:
        raise Exception('Словарь homeworks пуст')
    if 'homework_name' not in homework:
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


def main():
    """Основная логика работы бота."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = 0
    last_message = ''
    if not check_tokens():
        raise Exception('Недоступны переменные окружения')
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            status = parse_status(homeworks)
            if status != last_message:
                send_message(bot, status)
                last_message = status
        except Exception as error:
            logger.error(f'Сбой в работе программы: {error}')
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
