from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from payments import create_payment, check_payment, refund_payment
from payment_service.db import init_db
import logging
from contextlib import asynccontextmanager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield
    logger.info("Payment system started")

app = FastAPI(title="Payment System API", lifespan=lifespan)

class PaymentCreateRequest(BaseModel):
    amount: dict
    order_id: int
    user_id: str
    is_recurring: bool = False

class PaymentStatusResponse(BaseModel):
    status: str
    is_recurring: bool = False

class RefundCreateRequest(BaseModel):
    payment_id: str
    reason: Optional[str] = None

class RefundResponse(BaseModel):
    refund_id: str
    status: str
    amount: dict
    reason: Optional[str] = None

@app.post("/create-payment", response_model=dict)
async def create_payment_endpoint(request: PaymentCreateRequest):
    """
    Создает новый платеж в системе YooKassa
    
    - **amount**: словарь с суммой и валютой, например: {"value": "100.00", "currency": "RUB"}
    - **order_id**: идентификатор заказа в системе
    - **user_id**: идентификатор пользователя
    - **is_recurring**: флаг рекуррентного платежа
    """
    try:
        payment_url = create_payment(
            amount=request.amount,
            order_id=request.order_id,
            user_id=request.user_id,
            is_recurring=request.is_recurring
        )
        return {"payment_url": payment_url}
    except Exception as e:
        logger.error(f"Ошибка при создании платежа: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Payment creation failed: {str(e)}"
        )

@app.get("/check-payment/{payment_id}", response_model=PaymentStatusResponse)
async def check_payment_status(payment_id: str):
    """
    Проверяет статус платежа по его идентификатору
    
    - **payment_id**: идентификатор платежа в YooKassa
    """
    try:
        status = check_payment(payment_id)
        return {"status": status}
    except Exception as e:
        logger.error(f"Ошибка при проверке платежа: {str(e)}")
        raise HTTPException(
            status_code=404,
            detail=f"Payment check failed: {str(e)}"
        )
    
@app.post("/refund-payment", response_model=RefundResponse)
async def refund_payment_endpoint(request: RefundCreateRequest):
    """
    Оформляет возврат платежа
    
    - **payment_id**: идентификатор исходного платежа
    - **reason**: причина возврата (опционально)
    """
    try:
        refund_data = refund_payment(
            payment_id=request.payment_id,
            reason=request.reason
        )
        return {
            "refund_id": refund_data["id"],
            "status": refund_data["status"],
            "amount": refund_data["amount"],
            "reason": request.reason
        }
    except ValueError as e:
        logger.error(f"Ошибка валидации при возврате платежа: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=str(e))
    except Exception as e:
        logger.error(f"Ошибка при возврате платежа: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)