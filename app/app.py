from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from payments import create_payment, check_payment, refund_payment
from db import init_db
from config import Config
import logging

app = FastAPI(title="Payment System API")

@app.on_event("startup")
async def startup_event():
    init_db()
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.info("Payment system started")

class PaymentCreateRequest(BaseModel):
    amount: dict
    order_id: int
    user_id: str

class PaymentStatusResponse(BaseModel):
    status: str

class RefundCreateRequest(BaseModel):
    payment_id: str

class RefundResponse(BaseModel):
    refund_id: str
    status: str
    amount: dict

@app.post("/create-payment", response_model=dict)
async def create_payment_endpoint(request: PaymentCreateRequest):
    """
    Создает новый платеж в системе YooKassa
    
    - **amount**: словарь с суммой и валютой, например: {"value": "100.00", "currency": "RUB"}
    - **order_id**: идентификатор заказа в системе
    - **user_id**: идентификатор пользователя
    """
    try:
        payment_url = create_payment(
            amount=request.amount,
            order_id=request.order_id,
            user_id=request.user_id
        )
        return {"payment_url": payment_url}
    except Exception as e:
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
        raise HTTPException(
            status_code=404,
            detail=f"Payment check failed: {str(e)}"
        )
    
@app.post("/refund-payment", response_model=RefundResponse)
async def refund_payment_endpoint(request: RefundCreateRequest):
    """
    Оформляет возврат платежа
    
    - **payment_id**: идентификатор исходного платежа
    """
    try:
        refund_data = refund_payment(
            payment_id=request.payment_id
        )
        return {
            "refund_id": refund_data["id"],
            "status": refund_data["status"],
            "amount": refund_data["amount"]
        }
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)