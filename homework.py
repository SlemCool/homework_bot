import http
import logging
import os
import sys
import time

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()


logging.basicConfig(
    handlers=[logging.FileHandler(filename='main.log', encoding='utf-8')],
    format='%(asctime)s  %(name)s, %(levelname)s, %(message)s',
    datefmt="%F %A %T",
    level=logging.DEBUG,
)
logger = logging.getLogger(__name__)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(
    logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
)
logger.addHandler(handler)

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
    """Проверка предзаполненных переменных окружения."""
    return all((PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID))


def send_message(bot, message):
    """Отправка сообщения пользователю бота."""
    logger.debug('Начало отправки сообщения в Telegram')
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.debug(f'Сообщение отправлено: {message}')
    except Exception as error:
        logger.error(f'Упс сообщение не получилось отправить: {error}')


def get_api_answer(timestamp):
    """Запрос к эндпоинту API-сервиса."""
    logger.debug(
        f'Посылаем запрос к API: {ENDPOINT} с меткой времени: {timestamp}'
    )
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=timestamp)
        if response.status_code != http.HTTPStatus.OK:
            logger.error('API не отвечает')
            raise http.exceptions.HTTPError()
        logger.debug('Запрос к API выполнен успешно')
        return response.json()
    except requests.exceptions.RequestException as request_error:
        logger.error(f'Ошибка запроса к API: {request_error}')


def check_response(response):
    """Проверяет ответ API на соответствие документации."""
    logger.debug('Проверяем response и возвращаем список работ')
    if not isinstance(response, dict):
        raise TypeError(f'response должен быть dict, а не: {type(response)}')
    homeworks = response.get('homeworks')
    if 'homeworks' not in response:
        raise KeyError('Ключ homeworks отсутствует в response')
    if 'current_date' not in response:
        raise KeyError('Ключ current_date отсутствует в response')
    if not isinstance(homeworks, list):
        raise TypeError(f'homework должен быть list а не: {type(homeworks)}')
    logger.debug(f'response прошёл проверку и возвращает: {homeworks}')
    return homeworks


def parse_status(homework):
    """Извлекает статус работы."""
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if 'homework_name' not in homework:
        raise KeyError('Ключ homework_name отсутствует в homework')
    if 'status' not in homework:
        raise KeyError('Ключ status отсутствует в homework')
    if homework_status not in HOMEWORK_VERDICTS:
        raise KeyError(f'Неожиданный статус проверки {homework_status}')
    verdict = HOMEWORK_VERDICTS[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    logger.info('Бот приступает к патрулированию')
    if not check_tokens():
        logger.critical('Отсутствует хотя бы одна переменная окружения')
        raise ValueError('Отсутствует хотя бы одна переменная окружения!')
    logger.debug('Переменные прошли проверку')
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    while True:
        try:
            response = get_api_answer({'from_date': timestamp})
            timestamp = response['current_date']
            logger.debug(f'Обновляем метку времени на: {timestamp}')
            homeworks = check_response(response)
            if homeworks:
                message = parse_status(homeworks[0])
                send_message(bot, message)
            else:
                logger.debug('Статус проверки не поменялся.')
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
            logger.error(message)
        finally:
            logger.debug(f'Засыпаю на - {RETRY_PERIOD} сек')
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
