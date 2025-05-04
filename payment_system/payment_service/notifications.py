import logging
import requests
from config import Config

logger = logging.getLogger(__name__)

def send_notification(message: str, payment_id: str = None, status: str = None, reason: str = None):
    try:
        full_message = f"Платеж {payment_id if payment_id else 'N/A'}\n"
        full_message += f"Статус: {status if status else 'N/A'}\n"
        if reason:
            full_message += f"Причина отказа: {reason}\n"
        full_message += f"Детали: {message}"
        
        url = f'https://api.telegram.org/bot{Config.TELEGRAM_TOKEN}/sendMessage'
        data = {
            'chat_id': Config.TELEGRAM_CHAT_ID,
            'text': full_message
        }
        response = requests.post(url, data=data)
        response.raise_for_status()
        logger.info(f"Уведомление отправлено: {full_message}")
    except Exception as e:
        logger.error(f"Ошибка при отправке уведомления: {str(e)}")