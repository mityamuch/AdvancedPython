from celery import Celery
from yookassa import Payment
from config import Config
from db import update_payment_status
from notifications import send_notification

app = Celery('tasks', broker='redis://localhost:6379/0')

@app.task
def check_payment_task(payment_id):
    payment = Payment.find_one(payment_id)
    
    if payment.status == "succeeded":
        update_payment_status(payment_id, "completed")
        send_notification(f"Платеж {payment_id} успешен")
    elif payment.status == "canceled":
        update_payment_status(payment_id, "failed")
        send_notification(f"Платеж {payment_id} отменен")
        # Повтор через 24 часа
        check_payment_task.apply_async(args=[payment_id], countdown=86400)