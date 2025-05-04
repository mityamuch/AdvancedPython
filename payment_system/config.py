import os

class Config:
    YOOKASSA_SHOP_ID = os.getenv("YOOKASSA_SHOP_ID")
    YOOKASSA_SECRET = os.getenv("YOOKASSA_SECRET")
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
    RETURN_URL = os.getenv('RETURN_URL')
    DB_FILE = "payments.db"
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')