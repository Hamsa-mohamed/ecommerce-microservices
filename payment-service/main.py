from fastapi import FastAPI

app = FastAPI(title="Payment Service")

@app.get("/health")
def health():
    return {"status": "Payment service is running"}

@app.post("/pay")
def pay(order_id: str, amount: float):
    return {
        "order_id": order_id,
        "amount": amount,
        "status": "PAID",
        "message": "Payment successful"
    }
