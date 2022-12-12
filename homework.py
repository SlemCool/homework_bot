import logging
import os
import time

import requests
from dotenv import load_dotenv
from telegram import Bot, ReplyKeyboardMarkup
from telegram.ext import CommandHandler, Updater

load_dotenv()

logging.basicConfig(
    handlers=[logging.FileHandler(filename='main.log', encoding='utf-8')],
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


def check_tokens():
    """Проверка предзаполненых переменных окружения."""
    if not PRACTICUM_TOKEN or not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        logging.critical(f'Отсутствует хотя бы одна переменная окружения')
        raise ValueError(f'Отсутствует хотя бы одна переменная окружения!')


def send_message(bot, message):
    """Отправка собщения пользователю бота."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.debug(f'Сообщение отправлено: {message}')
    except Exception as error:
        logging.error(f'Упс сообщение не получилось отправить: {error}')


def get_api_answer(timestamp):
    """Запрос к эндпоинту API-сервиса."""
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=timestamp)
    except Exception as error:
        logging.error(f'Ошибка при запросе к основному API: {error}')
    return response.json()


def check_response(response):
    """Проверяет ответ API на соответствие документации."""
    try:
        homework = response[0]
        return homework
    except Exception as error:
        logging.error(f'Ошибка при проверке запроса от API: {error}')


def parse_status(homework):
    """Извлекает статус работы."""
    # if homework['status'] in HOMEWORK_VERDICTS:
    try:
        homework_name = homework['homework_name']
        verdict = HOMEWORK_VERDICTS[homework['status']]
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'
    except Exception as error:
        logging.error(f'Статус не в запросе не соответствует словарю - {error}')


def main():
    """Основная логика работы бота."""
    check_tokens()
    bot = Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    status = ''
    while True:
        try:
            response = get_api_answer({'from_date': timestamp})
            timestamp = response['current_date']
            homework = check_response(response['homeworks'])
            if homework and status != homework['status']:
                status = homework['status']
                message = parse_status(homework)
                send_message(bot, message)
                logging.debug(f'Сообщение отправленно со статусом - "{status}"')
            print(f'Уже должно быть заполнено - {status}')
            time.sleep(10)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
            raise ValueError(f'хз что но что-то не так!')
        ...


if __name__ == '__main__':
    main()
