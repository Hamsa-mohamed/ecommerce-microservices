from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import json
import requests
from typing import Optional
import os

app = FastAPI(title="Payment Service")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup
DB_FILE = "payments.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS payments (
            payment_id TEXT PRIMARY KEY,
            order_id TEXT NOT NULL,
            amount REAL NOT NULL,
            status TEXT DEFAULT 'PENDING',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

ORDER_SERVICE_URL = os.getenv("ORDER_SERVICE_URL", "http://localhost:8003")
API_KEY = os.getenv("API_KEY", "secret-key-123")

def verify_api_key(x_api_key: Optional[str] = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return x_api_key

@app.get("/health")
def health():
    return {"status": "Payment service is running", "database": "connected"}

@app.post("/pay")
def pay(
    order_id: str, 
    amount: float,
    x_api_key: Optional[str] = Header(None)
):
    verify_api_key(x_api_key)
    
    import uuid
    payment_id = str(uuid.uuid4())
    
    # Save payment to database
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(
        "INSERT INTO payments (payment_id, order_id, amount, status) VALUES (?, ?, ?, 'COMPLETED')",
        (payment_id, order_id, amount)
    )
    conn.commit()
    conn.close()
    
    # Notify order service to update order status
    try:
        response = requests.post(
            f"{ORDER_SERVICE_URL}/orders/{order_id}/payment",
            headers={"X-API-Key": API_KEY},
            timeout=5
        )
        if response.status_code == 200:
            print(f"Order {order_id} marked as PAID")
    except Exception as e:
        print(f"Error notifying order service: {e}")
        # Log error but don't fail the payment
    
    return {
        "payment_id": payment_id,
        "order_id": order_id,
        "amount": amount,
        "status": "PAID",
        "message": "Payment successful and order updated"
    }

@app.get("/payments/{order_id}")
def get_payment(order_id: str, x_api_key: Optional[str] = Header(None)):
    verify_api_key(x_api_key)
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT payment_id, order_id, amount, status FROM payments WHERE order_id = ?", (order_id,))
    row = c.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    return {
        "payment_id": row[0],
        "order_id": row[1],
        "amount": row[2],
        "status": row[3]
    }
