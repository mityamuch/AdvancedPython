import uuid
from datetime import datetime, timedelta
from yookassa import Payment, Configuration, Refund
from config import Config
from payment_service.db import save_payment, save_refund, update_payment_status, update_next_payment_date
from payment_service.notifications import send_notification
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

Configuration.account_id = Config.YOOKASSA_SHOP_ID
Configuration.secret_key = Config.YOOKASSA_SECRET

def _handle_payment_status(payment_id: str, status: str, reason: Optional[str] = None) -> None:
    status_messages = {
        "succeeded": "Платеж успешно выполнен",
        "canceled": "Платеж отменен",
        "refunded": "Платеж возвращен"
    }
    
    message = status_messages.get(status, f"Статус платежа: {status}")
    send_notification(
        message=message,
        payment_id=payment_id,
        status=status,
        reason=reason
    )

def _get_payment_status_with_refunds(payment) -> str:
    if payment.status != "succeeded":
        return payment.status
        
    try:
        refunds = Refund.list({"payment_id": payment.id})
        if not refunds.items:
            return payment.status
            
        last_refund = refunds.items[-1]
        return "refunded" if last_refund.status == "succeeded" else payment.status
    except Exception as e:
        logger.error(f"Ошибка при проверке возвратов платежа: {str(e)}")
        return payment.status

def create_payment(amount: Dict[str, str], order_id: int, user_id: str, is_recurring: bool = False) -> str:
    try:
        payment_id = str(uuid.uuid4())
        
        payment = Payment.create({
            "amount": amount,
            "confirmation": {
                "type": "redirect",
                "return_url": f"{Config.RETURN_URL}/{payment_id}"
            },
            "description": f"Order #{order_id}",
            "capture": True,
            "metadata": {
                "order_id": order_id,
                "user_id": user_id,
                "is_recurring": is_recurring
            }
        }, payment_id)
        
        next_payment_date = (datetime.now() + timedelta(days=1)).isoformat() if is_recurring else None
        
        save_payment(
            payment_id=payment.id,
            order_id=order_id,
            user_id=user_id,
            status="pending",
            is_recurring=is_recurring,
            recurring_interval=1 if is_recurring else None,
            next_payment_date=next_payment_date
        )
        
        _handle_payment_status(payment.id, "pending")
        
        return payment.confirmation.confirmation_url
    except Exception as e:
        logger.error(f"Ошибка при создании платежа: {str(e)}")
        raise

def check_payment(payment_id: str) -> str:
    try:
        payment = Payment.find_one(payment_id)
        status = _get_payment_status_with_refunds(payment)
        update_payment_status(payment_id, status)
        
        reason = None
        if status == "canceled":
            reason = payment.cancellation_details.get("reason", "Неизвестная причина")
            
        _handle_payment_status(payment_id, status, reason)
        
        if status == "canceled" and payment.metadata.get("is_recurring"):
            update_next_payment_date(payment_id, 1)
        
        return status
    except Exception as e:
        logger.error(f"Ошибка при проверке платежа {payment_id}: {str(e)}")
        raise

def refund_payment(payment_id: str, reason: Optional[str] = None) -> Dict:
    try:
        payment = Payment.find_one(payment_id)
        
        if payment.status != "succeeded":
            raise ValueError("Cannot refund payment that is not succeeded")
        
        refund = Refund.create({
            "payment_id": payment_id,
            "amount": payment.amount,
            "description": reason
        })
        
        save_refund(
            refund_id=refund.id,
            payment_id=payment_id,
            status=refund.status,
            reason=reason
        )
        
        update_payment_status(payment_id, "refunded")
        _handle_payment_status(payment_id, "refunded", reason)
        
        return {
            "id": refund.id,
            "status": refund.status,
            "amount": {
                "value": refund.amount.value,
                "currency": refund.amount.currency
            }
        }
    except Exception as e:
        logger.error(f"Ошибка при возврате платежа {payment_id}: {str(e)}")
        raise