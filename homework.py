import logging
import os
import time

import requests
from telegram import Bot, ReplyKeyboardMarkup
from telegram.ext import CommandHandler, Updater

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    handlers=[
        logging.FileHandler(
            filename='main.log', encoding='utf-8'
        )
    ],
    format='%(asctime)s,  %(name)s, %(levelname)s, %(message)s',
    datefmt="%F %A %T",
    level=logging.INFO,
)

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.',
}

status = ''


def check_tokens():
    if not PRACTICUM_TOKEN or not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        logging.error(f'Отсутствует хотя бы одна переменная окружения')
        raise ValueError(f'Отсутствует хотя бы одна переменная окружения!')


def send_message(bot, message):
    bot.send_message(TELEGRAM_CHAT_ID, message)


def get_api_answer(timestamp):
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=timestamp)
    except Exception as error:
        logging.error(f'Ошибка при запросе к основному API: {error}')

    homework = response.json().get('homeworks')[0]
    return parse_status(homework)


def check_response(response):
    ...


def parse_status(homework):
    global status
    if homework['status'] != status:
        status = homework['status']
        homework_name = homework['homework_name']
        verdict = HOMEWORK_VERDICTS[status]
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    check_tokens()

    bot = Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    message = get_api_answer({'from_date': 0})
    send_message(bot, message)
    # ...

    # while True:
    #     try:

    #         ...

    #     except Exception as error:
    #         message = f'Сбой в работе программы: {error}'
    #         ...
    #     ...


if __name__ == '__main__':
    main()
