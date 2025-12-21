# Quick Start & Testing Guide

## Prerequisites

Ensure Python 3.9+ and pip are installed.

---

## Installation & Setup

### 1. Install Dependencies

```bash
# Navigate to workspace
cd f:\assignments\cloud\project\ecommerce-microservices

# Install all packages for all services
pip install fastapi uvicorn python-multipart requests
```

---

## Starting the Services

### Option 1: Individual Terminals (Recommended for Development)

**Terminal 1 - Cart Service (Port 8001)**
```bash
cd cart-service
python -m uvicorn main:app --host 0.0.0.0 --port 8001
# Output: Uvicorn running on http://0.0.0.0:8001
```

**Terminal 2 - Catalog Service (Port 8002)**
```bash
cd catalog-service
python -m uvicorn main:app --host 0.0.0.0 --port 8002
# Output: Uvicorn running on http://0.0.0.0:8002
```

**Terminal 3 - Order Service (Port 8003)**
```bash
cd order-service
python -m uvicorn main:app --host 0.0.0.0 --port 8003
# Output: Uvicorn running on http://0.0.0.0:8003
```

**Terminal 4 - Payment Service (Port 8004)**
```bash
cd payment-service
python -m uvicorn main:app --host 0.0.0.0 --port 8004
# Output: Uvicorn running on http://0.0.0.0:8004
```

### Option 2: With Custom API Key

```bash
export API_KEY="your-custom-key"
python -m uvicorn main:app --port 8001
```

---

## Testing the Services

### API Key Configuration
```bash
API_KEY=secret-key-123  # Default value used throughout examples
```

### 1. Health Checks

```bash
# Test all services health endpoints
curl -X GET http://localhost:8001/health \
  -H "X-API-Key: secret-key-123"

curl -X GET http://localhost:8002/health \
  -H "X-API-Key: secret-key-123"

curl -X GET http://localhost:8003/health \
  -H "X-API-Key: secret-key-123"

curl -X GET http://localhost:8004/health \
  -H "X-API-Key: secret-key-123"

# Expected Response
{
  "status": "... service is running",
  "database": "connected"
}
```

---

### 2. Test Catalog Service

#### Get All Products
```bash
curl -X GET http://localhost:8002/products \
  -H "X-API-Key: secret-key-123"

# Response
[
  {"id": 1, "name": "Laptop", "price": 999.99, "stock": 50},
  {"id": 2, "name": "Mouse", "price": 29.99, "stock": 200},
  {"id": 3, "name": "Keyboard", "price": 79.99, "stock": 150}
]
```

#### Get Specific Product
```bash
curl -X GET http://localhost:8002/products/1 \
  -H "X-API-Key: secret-key-123"

# Response
{
  "id": 1,
  "name": "Laptop",
  "price": 999.99,
  "stock": 50
}
```

---

### 3. Test Cart Service

#### Get Empty Cart
```bash
curl -X GET http://localhost:8001/cart/user1 \
  -H "X-API-Key: secret-key-123"

# Response (first time)
{
  "user_id": "user1",
  "cart": []
}
```

#### Add Item to Cart (Valid Product)
```bash
curl -X POST "http://localhost:8001/cart/user1/add?product_id=1&quantity=2" \
  -H "X-API-Key: secret-key-123"

# Response
{
  "message": "Item added to cart",
  "cart": [
    {"product_id": 1, "quantity": 2}
  ]
}
```

#### Add Item to Cart (Invalid Product)
```bash
curl -X POST "http://localhost:8001/cart/user1/add?product_id=999&quantity=1" \
  -H "X-API-Key: secret-key-123"

# Response (404 Error)
{
  "detail": "Product 999 not found in catalog"
}
```

#### Retrieve Cart After Adding Items
```bash
curl -X GET http://localhost:8001/cart/user1 \
  -H "X-API-Key: secret-key-123"

# Response
{
  "user_id": "user1",
  "cart": [
    {"product_id": 1, "quantity": 2}
  ]
}
```

#### Add Another Item
```bash
curl -X POST "http://localhost:8001/cart/user1/add?product_id=2&quantity=1" \
  -H "X-API-Key: secret-key-123"

# Response
{
  "message": "Item added to cart",
  "cart": [
    {"product_id": 1, "quantity": 2},
    {"product_id": 2, "quantity": 1}
  ]
}
```

#### Clear Cart
```bash
curl -X DELETE http://localhost:8001/cart/user1/clear \
  -H "X-API-Key: secret-key-123"

# Response
{
  "message": "Cart cleared"
}

# Verify
curl -X GET http://localhost:8001/cart/user1 \
  -H "X-API-Key: secret-key-123"
# Response: cart is now empty []
```

---

### 4. Test Order Service

#### Create Order
```bash
curl -X POST "http://localhost:8003/orders?user_id=user1" \
  -H "X-API-Key: secret-key-123" \
  -H "Content-Type: application/json" \
  -d '[{"product_id": 1, "quantity": 1, "price": 999.99}, {"product_id": 2, "quantity": 2, "price": 29.99}]'

# Response (save order_id for next step)
{
  "order_id": "<uuid>",
  "user_id": "user1",
  "items": [...],
  "total_amount": 1059.97,
  "status": "CREATED"
}
```

#### List All Orders
```bash
curl -X GET http://localhost:8003/orders \
  -H "X-API-Key: secret-key-123"

# Response
[
  {
    "id": "<uuid>",
    "user_id": "user1",
    "items": [...],
    "status": "CREATED",
    "total_amount": 1059.97
  }
]
```

#### Get Specific Order
```bash
curl -X GET "http://localhost:8003/orders/<order_id>" \
  -H "X-API-Key: secret-key-123"

# Response
{
  "id": "<order_id>",
  "user_id": "user1",
  "items": [...],
  "status": "CREATED",
  "total_amount": 1059.97
}
```

---

### 5. Test Payment Service & Integration

#### Process Payment (Triggers Order Update)
```bash
# First create an order (see above) and note the order_id

curl -X POST "http://localhost:8004/pay?order_id=<order_id>&amount=1059.97" \
  -H "X-API-Key: secret-key-123"

# Response
{
  "payment_id": "<uuid>",
  "order_id": "<order_id>",
  "amount": 1059.97,
  "status": "PAID",
  "message": "Payment successful and order updated"
}
```

#### Verify Order Status Updated
```bash
curl -X GET "http://localhost:8003/orders/<order_id>" \
  -H "X-API-Key: secret-key-123"

# Response (status should now be "PAID")
{
  "id": "<order_id>",
  "user_id": "user1",
  "items": [...],
  "status": "PAID",  ← Changed from "CREATED"!
  "total_amount": 1059.97
}
```

#### Get Payment History
```bash
curl -X GET "http://localhost:8004/payments/<order_id>" \
  -H "X-API-Key: secret-key-123"

# Response
{
  "payment_id": "<uuid>",
  "order_id": "<order_id>",
  "amount": 1059.97,
  "status": "COMPLETED"
}
```

---

### 6. Test Authentication

#### Request Without API Key
```bash
curl -X GET http://localhost:8001/cart/user1

# Response (401 Error)
{
  "detail": "Invalid API Key"
}
```

#### Request With Wrong API Key
```bash
curl -X GET http://localhost:8001/cart/user1 \
  -H "X-API-Key: wrong-key"

# Response (401 Error)
{
  "detail": "Invalid API Key"
}
```

#### Request With Correct API Key
```bash
curl -X GET http://localhost:8001/cart/user1 \
  -H "X-API-Key: secret-key-123"

# Response (200 OK)
{
  "user_id": "user1",
  "cart": [...]
}
```

---

### 7. Test Data Persistence

#### Step 1: Add Item to Cart
```bash
curl -X POST "http://localhost:8001/cart/user-persist/add?product_id=3&quantity=5" \
  -H "X-API-Key: secret-key-123"

# Response
{
  "message": "Item added to cart",
  "cart": [{"product_id": 3, "quantity": 5}]
}
```

#### Step 2: Stop the Cart Service
```
Press Ctrl+C in the Cart Service terminal
```

#### Step 3: Verify Database File Exists
```bash
# Check in cart-service directory
ls -la carts.db
# File should exist
```

#### Step 4: Restart the Cart Service
```bash
cd cart-service
python -m uvicorn main:app --host 0.0.0.0 --port 8001
```

#### Step 5: Verify Data Persisted
```bash
curl -X GET http://localhost:8001/cart/user-persist \
  -H "X-API-Key: secret-key-123"

# Response (data still exists!)
{
  "user_id": "user-persist",
  "cart": [{"product_id": 3, "quantity": 5}]
}
```

✅ **Data Persistence Verified!**

---

## Complete End-to-End Workflow

### Scenario: Customer Shopping

```bash
# 1. Browse catalog
curl -X GET http://localhost:8002/products \
  -H "X-API-Key: secret-key-123"

# 2. Add items to cart
curl -X POST "http://localhost:8001/cart/john/add?product_id=1&quantity=1" \
  -H "X-API-Key: secret-key-123"

curl -X POST "http://localhost:8001/cart/john/add?product_id=2&quantity=3" \
  -H "X-API-Key: secret-key-123"

# 3. Review cart
curl -X GET http://localhost:8001/cart/john \
  -H "X-API-Key: secret-key-123"

# 4. Checkout (create order)
curl -X POST "http://localhost:8003/orders?user_id=john" \
  -H "X-API-Key: secret-key-123" \
  -H "Content-Type: application/json" \
  -d '[{"product_id":1,"quantity":1,"price":999.99},{"product_id":2,"quantity":3,"price":29.99}]'
  
# Save order_id from response

# 5. Payment
curl -X POST "http://localhost:8004/pay?order_id=<saved_order_id>&amount=1089.96" \
  -H "X-API-Key: secret-key-123"

# 6. Verify order is paid
curl -X GET "http://localhost:8003/orders/<saved_order_id>" \
  -H "X-API-Key: secret-key-123"
  
# Status should now be "PAID"

# 7. Clear cart for next session
curl -X DELETE http://localhost:8001/cart/john/clear \
  -H "X-API-Key: secret-key-123"
```

---

## Troubleshooting

### Service Won't Start
```bash
# Check if port is already in use
netstat -ano | findstr :8001

# Kill process using port
taskkill /PID <PID> /F

# Try again
python -m uvicorn main:app --port 8001
```

### API Key Issues
```bash
# Default API Key: secret-key-123
# Make sure to include in every request header:
-H "X-API-Key: secret-key-123"
```

### Database Issues
```bash
# Check database files exist in service directories
ls -la cart-service/carts.db
ls -la catalog-service/products.db
ls -la order-service/orders.db
ls -la payment-service/payments.db

# To reset (delete all data)
rm *.db
# Services will recreate on next start
```

### Service Communication Issues
```bash
# Verify all services are running
curl http://localhost:8001/health -H "X-API-Key: secret-key-123"
curl http://localhost:8002/health -H "X-API-Key: secret-key-123"
curl http://localhost:8003/health -H "X-API-Key: secret-key-123"
curl http://localhost:8004/health -H "X-API-Key: secret-key-123"

# All should return 200 OK with status messages
```

---

## Performance Testing

### Load Testing with Multiple Users

```bash
# Add carts for multiple users
for user in user1 user2 user3 user4 user5; do
  curl -X POST "http://localhost:8001/cart/$user/add?product_id=1&quantity=1" \
    -H "X-API-Key: secret-key-123"
done

# Create multiple orders
for user in user1 user2 user3 user4 user5; do
  curl -X POST "http://localhost:8003/orders?user_id=$user" \
    -H "X-API-Key: secret-key-123" \
    -H "Content-Type: application/json" \
    -d '[{"product_id":1,"quantity":1,"price":999.99}]'
done
```

---

## Database Inspection (Optional)

### Using SQLite CLI

```bash
# Install sqlite3 if needed
# apt-get install sqlite3

# Inspect carts
sqlite3 cart-service/carts.db
> SELECT * FROM carts;
> .exit

# Inspect products
sqlite3 catalog-service/products.db
> SELECT * FROM products;
> .exit

# Inspect orders
sqlite3 order-service/orders.db
> SELECT * FROM orders;
> .exit

# Inspect payments
sqlite3 payment-service/payments.db
> SELECT * FROM payments;
> .exit
```

---

## Summary

All services are now:
✅ Running with persistent databases
✅ Protected with API key authentication
✅ Communicating with each other
✅ Supporting transactions
✅ Validating data across services
✅ Fully tested and operational

Ready for production deployment! 🚀
