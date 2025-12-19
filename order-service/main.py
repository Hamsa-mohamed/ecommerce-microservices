from fastapi import FastAPI
import uuid

app = FastAPI(title="Order Service")
@app.get("/orders")
def get_orders():
    return [
        {"id": 1, "status": "CREATED"},
        {"id": 2, "status": "PAID"},
        {"id": 3, "status": "SHIPPED"}
    ]


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
