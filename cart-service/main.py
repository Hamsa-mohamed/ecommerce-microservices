from fastapi import FastAPI

app = FastAPI(title="Cart Service")

# In-memory cart storage
# مثال: { "user1": [{"product_id": 1, "quantity": 2}] }
carts = {}

@app.get("/health")
def health():
    return {"status": "Cart service is running"}

@app.post("/cart/{user_id}/add")
def add_to_cart(user_id: str, product_id: int, quantity: int = 1):
    if user_id not in carts:
        carts[user_id] = []

    carts[user_id].append({
        "product_id": product_id,
        "quantity": quantity
    })
    return {"message": "Item added to cart", "cart": carts[user_id]}

@app.get("/cart/{user_id}")
def get_cart(user_id: str):
    return {"user_id": user_id, "cart": carts.get(user_id, [])}

@app.delete("/cart/{user_id}/clear")
def clear_cart(user_id: str):
    carts[user_id] = []
    return {"message": "Cart cleared"}
