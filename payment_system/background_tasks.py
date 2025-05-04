from celery import Celery
from yookassa import Payment
from payment_service.db import update_payment_status, get_recurring_payments
from payment_service.notifications import send_notification
from payment_service.payments import create_payment, _get_payment_status_with_refunds
from config import Config
import logging
import sqlite3

logger = logging.getLogger(__name__)

app = Celery('tasks', broker=Config.REDIS_URL)

def get_pending_payments() -> list:
    with sqlite3.connect(Config.DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id FROM payments 
            WHERE status = 'pending'
        """)
        return cursor.fetchall()

@app.task
def check_payment_task(payment_id: str):
    try:
        payment = Payment.find_one(payment_id)
        status = _get_payment_status_with_refunds(payment)
        update_payment_status(payment_id, status)
        
        if status == "succeeded":
            send_notification(
                message="Платеж успешно выполнен",
                payment_id=payment_id,
                status="completed"
            )
        elif status == "canceled":
            reason = payment.cancellation_details.get("reason", "Неизвестная причина")
            send_notification(
                message="Платеж отменен",
                payment_id=payment_id,
                status="failed",
                reason=reason
            )
            
            if payment.metadata.get("is_recurring"):
                check_payment_task.apply_async(args=[payment_id], countdown=30) # поменять на 86400
    except Exception as e:
        logger.error(f"Ошибка при проверке платежа {payment_id}: {str(e)}")
        raise

@app.task
def process_recurring_payments():
    try:
        recurring_payments = get_recurring_payments()
        
        for payment_id, order_id, user_id, interval in recurring_payments:
            try:
                new_payment = create_payment(
                    amount={"value": "100.00", "currency": "RUB"},
                    order_id=order_id,
                    user_id=user_id,
                    is_recurring=True
                )
                
                send_notification(
                    message="Создан повторный платеж",
                    payment_id=new_payment,
                    status="pending"
                )
                
                check_payment_task.apply_async(args=[new_payment], countdown=10)
                
            except Exception as e:
                logger.error(f"Ошибка при создании повторного платежа {payment_id}: {str(e)}")
                continue
    except Exception as e:
        logger.error(f"Ошибка при обработке рекуррентных платежей: {str(e)}")
        raise

@app.task
def check_pending_payments():
    try:
        pending_payments = get_pending_payments()
        for payment_id in pending_payments:
            check_payment_task.apply_async(args=[payment_id[0]])
    except Exception as e:
        logger.error(f"Ошибка при проверке ожидающих платежей: {str(e)}")
        raise

app.conf.beat_schedule = {
    'process-recurring-payments': {
        'task': 'background_tasks.process_recurring_payments',
        'schedule': 10.0,  # Каждые 10 секунд
    },
    'check-pending-payments': {
        'task': 'background_tasks.check_pending_payments',
        'schedule': 10.0,  # Каждые 10 секунд
    },
}