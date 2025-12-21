from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import json
import requests
from typing import Optional
import os

app = FastAPI(title="Cart Service")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup
DB_FILE = "carts.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS carts (
            user_id TEXT PRIMARY KEY,
            items TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

CALOG_SERVICE_URL = os.getenv("CATALOG_SERVICE_URL", "http://localhost:8002")
API_KEY = os.getenv("API_KEY", "secret-key-123")

def verify_api_key(x_api_key: Optional[str] = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return x_api_key

def validate_product(product_id: int) -> bool:
    """Validate product exists in catalog service"""
    try:
        response = requests.get(
            f"{CATALOG_SERVICE_URL}/products",
            headers={"X-API-Key": API_KEY},
            timeout=5
        )
        if response.status_code == 200:
            products = response.json()
            return any(p["id"] == product_id for p in products)
    except Exception as e:
        print(f"Error validating product: {e}")
        # Fail open: allow if catalog service is down
        return True
    return False

@app.get("/health")
def health():
    return {"status": "Cart service is running", "database": "connected"}

@app.post("/cart/{user_id}/add")
def add_to_cart(
    user_id: str, 
    product_id: int, 
    quantity: int = 1,
    x_api_key: Optional[str] = Header(None)
):
    verify_api_key(x_api_key)
    
    # Validate product exists in catalog
    if not validate_product(product_id):
        raise HTTPException(status_code=404, detail=f"Product {product_id} not found in catalog")
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Get existing cart
    c.execute("SELECT items FROM carts WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    
    if row:
        items = json.loads(row[0])
    else:
        items = []
    
    # Add item
    items.append({
        "product_id": product_id,
        "quantity": quantity
    })
    
    # Save to database
    c.execute(
        "INSERT OR REPLACE INTO carts (user_id, items, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)",
        (user_id, json.dumps(items))
    )
    conn.commit()
    conn.close()
    
    return {"message": "Item added to cart", "cart": items}

@app.get("/cart/{user_id}")
def get_cart(user_id: str, x_api_key: Optional[str] = Header(None)):
    verify_api_key(x_api_key)
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT items FROM carts WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    
    items = json.loads(row[0]) if row else []
    return {"user_id": user_id, "cart": items}

@app.delete("/cart/{user_id}/clear")
def clear_cart(user_id: str, x_api_key: Optional[str] = Header(None)):
    verify_api_key(x_api_key)
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM carts WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
    
    return {"message": "Cart cleared"}
