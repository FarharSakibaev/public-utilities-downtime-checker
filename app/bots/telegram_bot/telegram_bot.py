import time
from datetime import datetime

import loguru
import requests
import telebot
from bs4 import BeautifulSoup
from telebot.types import Message

from app.config.config import TELEGRAM_BOT_TOKEN, DISTRICT, STREET, UTILITIES

telegram_bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)


def is_same_date(item):
    date_string = item.find_all('time')[0].get('datetime')
    source_date = datetime.strptime(date_string, '%Y-%m-%dT%H:%M:%S%z')
    current_date = datetime.now()
    return current_date.year == source_date.year \
        and current_date.month == source_date.month and current_date.day == source_date.day


def get_message_to_send(message_text):
    return message_text.replace('<b>', '').replace('</b>', '').replace(
        '<br/>', '\n').replace('<div class="tgme_widget_message_text js-message_text" dir="auto">',
                               '').replace('</div>', '')


def get_data(already_checked: list):
    response = requests.get('https://t.me/s/ArmeniaBlackouts')
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        for item in soup.find_all('div', {'class', 'tgme_widget_message'}):
            if is_same_date(item):
                send_response = False
                matching = ''
                message_text = str(item.find_next('div', {'class', 'tgme_widget_message_text'}))
                if 'ереван' in message_text.lower():
                    if 'арабкир' in message_text.lower():
                        matching = 'DISTRICT ARABKIR IS MATCHED\n\n'
                        matching += get_match_by_address_checking(message_text, True)
                        send_response = True

                    elif 'комитас' in message_text.lower():
                        matching = 'STREET KOMITAS IS MATCHED\n\n'
                        matching += get_match_by_address_checking(message_text)
                        send_response = True

                    if send_response:
                        if message_text in already_checked:
                            loguru.logger.info('SKIPPED: ' + message_text)
                            continue
                        already_checked.append(message_text)
                        utility = get_utility(message_text)
                        telegram_bot.send_message(332016792,
                                                  matching + utility + '\n\n' + get_message_to_send(message_text))
                        loguru.logger.info('Notification sent')
    return already_checked


def get_match_by_address_checking(message: str, check_street: bool = False) -> str:
    matching = ''
    # if 'ереван' in message.lower():
    #     matching += 'CITY IS MATCHED\n\n'
    # else:
    #     matching += 'CITY IS NOT MATCHED\n\n'
    if check_street:
        if 'комитас' in message.lower():
            matching += 'STREET KOMITAS IS MATCHED\n\n'
        else:
            matching += 'STREET KOMITAS IS NOT MATCHED\n\n'
    return matching


def get_utility(message: str) -> str:
    utility = ''
    for utility_item in UTILITIES:
        pass
    if 'вода' in message.lower() or 'водоснабжение' in message.lower():
        utility += 'WATER DOWNTIME\n\n'
    elif 'свет' in message.lower() or 'электр' in message.lower():
        utility += 'ELECTRICITY DOWNTIME\n\n'
    elif 'газ' in message.lower():
        utility += 'GAS DOWNTIME\n\n'

    return utility


@telegram_bot.message_handler(content_types=['text'])
def check_downtime(message: Message) -> None:
    send_response = False
    matching = ''

    if DISTRICT.lower() in message.text.lower():
        matching = f'DISTRICT {DISTRICT.upper()} IS MATCHED\n\n'
        matching += get_match_by_address_checking(message.text, True)
        send_response = True

    elif STREET.lower() in message.text.lower():
        matching = f'STREET {STREET.upper()} IS MATCHED\n\n'
        matching += get_match_by_address_checking(message.text)
        send_response = True

    if send_response:
        utility = get_utility(message.text)
        chat_id = message.chat.id
        telegram_bot.send_message(chat_id, matching + utility + '\n\n' + message.text)


def run_check():
    already_checked = []
    while True:
        loguru.logger.info('Start checking')
        already_checked = get_data(already_checked)
        loguru.logger.info('Finnish checking')
        time.sleep(60 * 30)
