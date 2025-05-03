from logging import log
import requests
from config import Config

def send_notification(message):
    log.debug(f"Отправляю сообщение в ТГ бота: {message}")
    url = f'https://api.telegram.org/bot{Config.TELEGRAM_BOT_TOKEN}/sendMessage'
    data = {
        'chat_id': Config.TELEGRAM_CHAT_ID,
        'text': message
    }
    requests.post(url, data=data)