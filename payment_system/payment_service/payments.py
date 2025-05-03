import uuid
from yookassa import Payment, Configuration, Refund
from config import Config
from db import save_payment, save_refund, update_payment_status
from notifications import send_notification

Configuration.account_id = Config.YOOKASSA_SHOP_ID
Configuration.secret_key = Config.YOOKASSA_SECRET

def create_payment(amount: dict, order_id: int, user_id: str) -> str:
    payment_id = str(uuid.uuid4())
    
    payment = Payment.create({
        "amount": amount,
        "confirmation": {
            "type": "redirect",
            "return_url": f"{Config.RETURN_URL}/{payment_id}"
        },
        "description": f"Order #{order_id}",
        "capture": True
    }, payment_id)
    
    save_payment(
        payment_id=payment.id,
        order_id=order_id,
        user_id=user_id,
        status="pending"
    )
    
    return payment.confirmation.confirmation_url

def check_payment(payment_id: str) -> str:
    payment = Payment.find_one(payment_id)
    update_payment_status(payment_id, payment.status)
    return payment.status

def refund_payment(payment_id: str) -> dict:
    payment = Payment.find_one(payment_id)
    
    if payment.status != "succeeded":
        raise ValueError("Cannot refund payment that is not succeeded")
    
    refund = Refund.create({
        "payment_id": payment_id,
        "amount": payment.amount
    })
    
    save_refund(
        refund_id=refund.id,
        payment_id=payment_id,
        status=refund.status
    )
    
    update_payment_status(payment_id, "refunded")
    send_notification(f"Refund created for payment {payment_id}")
    
    return {
        "id": refund.id,
        "status": refund.status,
        "amount": {
            "value": refund.amount.value,
            "currency": refund.amount.currency
        }
    }