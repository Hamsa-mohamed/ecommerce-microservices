from fastapi import FastAPI
import uuid

app = FastAPI(title="Order Service")

orders = {}

@app.get("/health")
def health():
    return {"status": "Order service is running"}

@app.post("/orders")
def create_order(user_id: str, items: list):
    order_id = str(uuid.uuid4())
    orders[order_id] = {
        "order_id": order_id,
        "user_id": user_id,
        "items": items,
        "status": "CREATED"
    }
    return orders[order_id]

@app.get("/orders/{order_id}")
def get_order(order_id: str):
    return orders.get(order_id, {"error": "Order not found"})
