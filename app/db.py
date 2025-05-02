import sqlite3
from config import Config

def init_db():
    with sqlite3.connect(Config.DB_FILE) as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id TEXT PRIMARY KEY,
            order_id INTEGER,
            user_id TEXT,
            status TEXT
        )
        """)
        
        conn.execute("""
        CREATE TABLE IF NOT EXISTS refunds (
            id TEXT PRIMARY KEY,
            payment_id TEXT,
            status TEXT
        )
        """)

def save_payment(payment_id: str, order_id: int, user_id: str, status: str):
    with sqlite3.connect(Config.DB_FILE) as conn:
        conn.execute("""
        INSERT INTO payments (id, order_id, user_id, status)
        VALUES (?, ?, ?, ?)
        """, (payment_id, order_id, user_id, status))

def update_payment_status(payment_id: str, status: str):
    with sqlite3.connect(Config.DB_FILE) as conn:
        conn.execute("""
        UPDATE payments SET status = ? WHERE id = ?
        """, (status, payment_id))

def save_refund(refund_id: str, payment_id: str, status: str):
    with sqlite3.connect(Config.DB_FILE) as conn:
        conn.execute("""
        INSERT INTO refunds (id, payment_id, status)
        VALUES (?, ?, ?)
        """, (refund_id, payment_id, status))

def get_payment_status(payment_id: str) -> str:
    with sqlite3.connect(Config.DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT status FROM payments WHERE id = ?", (payment_id,))
        result = cursor.fetchone()
        return result[0] if result else None

def check_refund_exists(payment_id: str) -> bool:
    with sqlite3.connect(Config.DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM refunds WHERE payment_id = ?", (payment_id,))
        return cursor.fetchone() is not None