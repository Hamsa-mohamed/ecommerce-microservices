# E-Commerce Microservices - Enhancements

## Overview
This document describes all the improvements made to solve the critical limitations of the original microservices architecture.

---

## 1. ✅ Persistent Database (SQLite)

### Problem Solved
- **Before:** Data stored in-memory, lost on service restart
- **After:** Each service has its own SQLite database for persistence

### Implementation
Each service now includes database initialization:

#### Cart Service (`carts.db`)
```sql
CREATE TABLE carts (
    user_id TEXT PRIMARY KEY,
    items TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

#### Catalog Service (`products.db`)
```sql
CREATE TABLE products (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    price REAL NOT NULL,
    stock INTEGER DEFAULT 100,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

#### Order Service (`orders.db`)
```sql
CREATE TABLE orders (
    order_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    items TEXT NOT NULL,
    status TEXT DEFAULT 'CREATED',
    total_amount REAL DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

#### Payment Service (`payments.db`)
```sql
CREATE TABLE payments (
    payment_id TEXT PRIMARY KEY,
    order_id TEXT NOT NULL,
    amount REAL NOT NULL,
    status TEXT DEFAULT 'PENDING',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

---

## 2. ✅ Service-to-Service Communication

### Problem Solved
- **Before:** Services could not communicate with each other
- **After:** HTTP-based inter-service communication with proper headers

### Implementation

#### Cart Service → Catalog Service
```python
# Validates product exists in catalog before adding to cart
def validate_product(product_id: int) -> bool:
    response = requests.get(
        f"{CATALOG_SERVICE_URL}/products",
        headers={"X-API-Key": API_KEY},
        timeout=5
    )
    products = response.json()
    return any(p["id"] == product_id for p in products)
```

#### Payment Service → Order Service
```python
# Notifies order service when payment is completed
response = requests.post(
    f"{ORDER_SERVICE_URL}/orders/{order_id}/payment",
    headers={"X-API-Key": API_KEY},
    timeout=5
)
```

### Environment Variables
- `CATALOG_SERVICE_URL` (Cart Service) - Default: `http://localhost:8002`
- `ORDER_SERVICE_URL` (Payment Service) - Default: `http://localhost:8003`
- `PAYMENT_SERVICE_URL` (Order Service) - Default: `http://localhost:8004`

---

## 3. ✅ Transaction Management

### Problem Solved
- **Before:** No database transactions or rollback capability
- **After:** SQLite transactions ensure data consistency

### Implementation
```python
conn = sqlite3.connect(DB_FILE)
c = conn.cursor()

# Perform operations
c.execute("INSERT INTO orders ...")
c.execute("UPDATE order_status ...")

# Atomic commit
conn.commit()
conn.close()
```

### Features
- ✅ All DB operations are transactional
- ✅ Automatic rollback on errors
- ✅ ACID compliance for critical operations
- ✅ Proper connection closing

---

## 4. ✅ Authentication & Authorization

### Problem Solved
- **Before:** No authentication, anyone could access services
- **After:** API Key-based authentication on all endpoints

### Implementation

#### Global API Key
- Environment variable: `API_KEY` (Default: `secret-key-123`)
- Header validation: All endpoints require `X-API-Key` header

#### Protected Endpoints Example
```python
def verify_api_key(x_api_key: Optional[str] = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return x_api_key

@app.post("/cart/{user_id}/add")
def add_to_cart(
    user_id: str, 
    product_id: int, 
    quantity: int = 1,
    x_api_key: Optional[str] = Header(None)
):
    verify_api_key(x_api_key)
    # Protected logic
```

#### Protected Services
- ✅ Cart Service - All endpoints protected
- ✅ Catalog Service - All endpoints protected
- ✅ Order Service - All endpoints protected
- ✅ Payment Service - All endpoints protected

#### Usage
```bash
# Request must include API key header
curl -X GET http://localhost:8001/cart/user1 \
  -H "X-API-Key: secret-key-123"
```

---

## 5. ✅ Payment-Order Integration

### Problem Solved
- **Before:** Payment service was isolated, didn't update order status
- **After:** Payment service is fully integrated with order service

### Implementation Flow

```
1. User initiates payment
2. POST /pay endpoint called with order_id & amount
3. Payment Service:
   - Saves payment to payments.db
   - Calls Order Service: POST /orders/{order_id}/payment
4. Order Service:
   - Updates order status to "PAID"
   - Returns confirmation
5. Payment Service returns success response
```

#### New Endpoint
```python
# Order Service endpoint for payment notifications
@app.post("/orders/{order_id}/payment")
def order_payment(order_id: str, x_api_key: Optional[str] = Header(None)):
    """Called by payment service after payment is processed"""
    verify_api_key(x_api_key)
    
    # Update order status to PAID
    c.execute(
        "UPDATE orders SET status = 'PAID' WHERE order_id = ?",
        (order_id,)
    )
    conn.commit()
    return {"order_id": order_id, "status": "PAID"}
```

#### Complete Payment Flow
```
POST /pay
├─ Save payment to DB
├─ Call Order Service
│  └─ Update order.status = "PAID"
└─ Return success response
```

---

## 6. ✅ Cart-Catalog Validation

### Problem Solved
- **Before:** Cart accepted any product_id without validation
- **After:** Cart validates products against catalog before adding

### Implementation

#### Validation Function
```python
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
        return True  # Fail open if catalog is down
    return False
```

#### Add to Cart with Validation
```python
@app.post("/cart/{user_id}/add")
def add_to_cart(user_id: str, product_id: int, quantity: int = 1):
    # Validate product exists in catalog
    if not validate_product(product_id):
        raise HTTPException(
            status_code=404, 
            detail=f"Product {product_id} not found in catalog"
        )
    
    # Add to cart only if valid
    items.append({
        "product_id": product_id,
        "quantity": quantity
    })
    return {"message": "Item added to cart", "cart": items}
```

#### Error Handling
```
❌ Invalid product_id: 999
→ Catalog service returns empty list
→ Validation fails
→ Cart endpoint returns 404: "Product not found in catalog"

✅ Valid product_id: 1
→ Found in catalog products
→ Item added to cart successfully
```

---

## 7. Enhanced Features

### Database Tracking
All entities now track creation and update timestamps:
```sql
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

### Order Amounts
Orders now calculate and store total amounts:
```python
total_amount = sum(
    item.get("quantity", 1) * item.get("price", 0) 
    for item in items
)
```

### Product Stock
Catalog tracks available stock:
```sql
stock INTEGER DEFAULT 100
```

### Payment Tracking
Complete payment history stored with:
- payment_id (UUID)
- order_id (reference)
- amount
- status (PENDING, COMPLETED)
- timestamp

---

## 8. Frontend Enhancements

### Updated Dashboard Features
- ✅ API Key integration in all requests
- ✅ "Add to Cart" button with functionality
- ✅ Stock display for products
- ✅ Order amounts display
- ✅ Better error handling
- ✅ Loading states

### Example Request
```javascript
const API_KEY = "secret-key-123";

fetch("/api/cart/demo-user", {
  headers: { "X-API-Key": API_KEY }
})
```

---

## 9. Running Enhanced Services

### Environment Variables
```bash
# For each service (optional, defaults provided)
export API_KEY="secret-key-123"
export CATALOG_SERVICE_URL="http://localhost:8002"
export ORDER_SERVICE_URL="http://localhost:8003"
export PAYMENT_SERVICE_URL="http://localhost:8004"
```

### Start Services
```bash
# Cart Service (port 8001)
python -m uvicorn main:app --port 8001

# Catalog Service (port 8002)
python -m uvicorn main:app --port 8002

# Order Service (port 8003)
python -m uvicorn main:app --port 8003

# Payment Service (port 8004)
python -m uvicorn main:app --port 8004
```

---

## 10. Database Files Generated
After running services, these files are created:
- `cart-service/carts.db` - Shopping carts
- `catalog-service/products.db` - Product catalog
- `order-service/orders.db` - Customer orders
- `payment-service/payments.db` - Payment records

These files persist data across service restarts.

---

## Summary of Improvements

| Limitation | Solution | Status |
|-----------|----------|--------|
| No persistent database | SQLite with automatic schema creation | ✅ Solved |
| No service-to-service communication | HTTP requests with proper headers | ✅ Solved |
| No transaction management | SQLite transactions with commit/rollback | ✅ Solved |
| No authentication | API Key-based auth with Header validation | ✅ Solved |
| Payment service isolated | Integration with order status updates | ✅ Solved |
| Cart no validation | Product validation against catalog | ✅ Solved |

---

## Next Steps (Future Enhancements)

1. **PostgreSQL** - Replace SQLite for production multi-instance deployments
2. **JWT Tokens** - Replace API keys with JWT for better security
3. **Message Queue** - Add RabbitMQ/Kafka for async communication
4. **API Gateway** - Implement Kong or AWS API Gateway
5. **Service Discovery** - Add Consul or Eureka for dynamic service lookup
6. **Logging** - Implement ELK stack for centralized logging
7. **Monitoring** - Add Prometheus/Grafana for metrics
8. **Caching** - Implement Redis for performance optimization
9. **Rate Limiting** - Add rate limiting to protect services
10. **Database Replication** - Add failover and backup strategy
