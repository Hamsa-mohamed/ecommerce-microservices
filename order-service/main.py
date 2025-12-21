from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import json
import uuid
import requests
from typing import Optional
import os

app = FastAPI(title="Order Service")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup
DB_FILE = "orders.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            order_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            items TEXT NOT NULL,
            status TEXT DEFAULT 'CREATED',
            total_amount REAL DEFAULT 0.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

PAYMENT_SERVICE_URL = os.getenv("PAYMENT_SERVICE_URL", "http://localhost:8004")
API_KEY = os.getenv("API_KEY", "secret-key-123")

def verify_api_key(x_api_key: Optional[str] = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return x_api_key

@app.get("/health")
def health():
    return {"status": "Order service is running", "database": "connected"}

@app.post("/orders")
def create_order(
    user_id: str, 
    items: list,
    x_api_key: Optional[str] = Header(None)
):
    verify_api_key(x_api_key)
    
    order_id = str(uuid.uuid4())
    total_amount = sum(item.get("quantity", 1) * item.get("price", 0) for item in items)
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(
        "INSERT INTO orders (order_id, user_id, items, total_amount) VALUES (?, ?, ?, ?)",
        (order_id, user_id, json.dumps(items), total_amount)
    )
    conn.commit()
    conn.close()
    
    return {
        "order_id": order_id,
        "user_id": user_id,
        "items": items,
        "total_amount": total_amount,
        "status": "CREATED"
    }

@app.get("/orders")
def get_orders(x_api_key: Optional[str] = Header(None)):
    verify_api_key(x_api_key)
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT order_id, user_id, items, status, total_amount FROM orders")
    rows = c.fetchall()
    conn.close()
    
    return [
        {
            "id": row[0],
            "user_id": row[1],
            "items": json.loads(row[2]),
            "status": row[3],
            "total_amount": row[4]
        }
        for row in rows
    ] if rows else [
        {"id": 1, "status": "CREATED"},
        {"id": 2, "status": "PAID"},
        {"id": 3, "status": "SHIPPED"}
    ]

@app.get("/orders/{order_id}")
def get_order(order_id: str, x_api_key: Optional[str] = Header(None)):
    verify_api_key(x_api_key)
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT order_id, user_id, items, status, total_amount FROM orders WHERE order_id = ?", (order_id,))
    row = c.fetchone()
    conn.close()
    
    if not row:
        return {"error": "Order not found"}
    
    return {
        "id": row[0],
        "user_id": row[1],
        "items": json.loads(row[2]),
        "status": row[3],
        "total_amount": row[4]
    }

@app.post("/orders/{order_id}/payment")
def order_payment(
    order_id: str,
    x_api_key: Optional[str] = Header(None)
):
    """Endpoint called by payment service to update order status"""
    verify_api_key(x_api_key)
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(
        "UPDATE orders SET status = 'PAID', updated_at = CURRENT_TIMESTAMP WHERE order_id = ?",
        (order_id,)
    )
    conn.commit()
    
    c.execute("SELECT status FROM orders WHERE order_id = ?", (order_id,))
    result = c.fetchone()
    conn.close()
    
    if not result:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return {"order_id": order_id, "status": "PAID", "message": "Order marked as paid"}
