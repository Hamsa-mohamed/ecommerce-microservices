from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import json
from typing import Optional
import os

app = FastAPI(title="Catalog Service")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup
DB_FILE = "products.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            stock INTEGER DEFAULT 100,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insert sample data if table is empty
    c.execute("SELECT COUNT(*) FROM products")
    if c.fetchone()[0] == 0:
        products = [
            (1, "Laptop", 999.99, 50),
            (2, "Mouse", 29.99, 200),
            (3, "Keyboard", 79.99, 150)
        ]
        c.executemany(
            "INSERT INTO products (id, name, price, stock) VALUES (?, ?, ?, ?)",
            products
        )
    
    conn.commit()
    conn.close()

init_db()

API_KEY = os.getenv("API_KEY", "secret-key-123")

def verify_api_key(x_api_key: Optional[str] = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return x_api_key

@app.get("/health")
def health():
    return {"status": "Catalog service is running", "database": "connected"}

@app.get("/products")
def get_products(x_api_key: Optional[str] = Header(None)):
    verify_api_key(x_api_key)
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, name, price, stock FROM products")
    rows = c.fetchall()
    conn.close()
    
    return [
        {"id": row[0], "name": row[1], "price": row[2], "stock": row[3]}
        for row in rows
    ]

@app.get("/products/{product_id}")
def get_product(product_id: int, x_api_key: Optional[str] = Header(None)):
    verify_api_key(x_api_key)
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, name, price, stock FROM products WHERE id = ?", (product_id,))
    row = c.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return {"id": row[0], "name": row[1], "price": row[2], "stock": row[3]}
