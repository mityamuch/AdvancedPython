import sqlite3
from config import Config
import logging

logger = logging.getLogger(__name__)

def init_db():
    with sqlite3.connect(Config.DB_FILE) as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id TEXT PRIMARY KEY,
            order_id INTEGER,
            user_id TEXT,
            status TEXT,
            is_recurring BOOLEAN DEFAULT FALSE,
            recurring_interval INTEGER,
            next_payment_date TEXT,
            parent_payment_id TEXT,
            FOREIGN KEY (parent_payment_id) REFERENCES payments(id)
        )
        """)
        
        conn.execute("""
        CREATE TABLE IF NOT EXISTS refunds (
            id TEXT PRIMARY KEY,
            payment_id TEXT,
            status TEXT,
            reason TEXT,
            FOREIGN KEY (payment_id) REFERENCES payments(id)
        )
        """)

def save_payment(payment_id: str, order_id: int, user_id: str, status: str, 
                is_recurring: bool = False, recurring_interval: int = None,
                next_payment_date: str = None, parent_payment_id: str = None):
    with sqlite3.connect(Config.DB_FILE) as conn:
        conn.execute("""
        INSERT INTO payments (id, order_id, user_id, status, is_recurring, 
                            recurring_interval, next_payment_date, parent_payment_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (payment_id, order_id, user_id, status, is_recurring, 
              recurring_interval, next_payment_date, parent_payment_id))

def update_payment_status(payment_id: str, status: str):
    with sqlite3.connect(Config.DB_FILE) as conn:
        conn.execute("""
        UPDATE payments SET status = ? WHERE id = ?
        """, (status, payment_id))

def save_refund(refund_id: str, payment_id: str, status: str, reason: str = None):
    with sqlite3.connect(Config.DB_FILE) as conn:
        conn.execute("""
        INSERT INTO refunds (id, payment_id, status, reason)
        VALUES (?, ?, ?, ?)
        """, (refund_id, payment_id, status, reason))

def get_payment_status(payment_id: str) -> str:
    with sqlite3.connect(Config.DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT status FROM payments WHERE id = ?", (payment_id,))
        result = cursor.fetchone()
        return result[0] if result else None

def get_recurring_payments() -> list:
    with sqlite3.connect(Config.DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, order_id, user_id, recurring_interval 
            FROM payments 
            WHERE is_recurring = TRUE 
            AND status = 'failed'
            AND next_payment_date <= datetime('now')
        """)
        return cursor.fetchall()

def update_next_payment_date(payment_id: str, interval_days: int):
    with sqlite3.connect(Config.DB_FILE) as conn:
        conn.execute("""
            UPDATE payments 
            SET next_payment_date = datetime('now', '+' || ? || ' days')
            WHERE id = ?
        """, (interval_days, payment_id))

def check_refund_exists(payment_id: str) -> bool:
    with sqlite3.connect(Config.DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM refunds WHERE payment_id = ?", (payment_id,))
        return cursor.fetchone() is not None