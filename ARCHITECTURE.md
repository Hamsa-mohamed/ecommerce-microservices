# Enhanced Architecture Overview

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     FRONTEND DASHBOARD                           │
│                   (Nginx + HTML/JS/CSS)                          │
│              API Key: secret-key-123 (configurable)              │
└──────────┬──────────┬──────────┬──────────────────────────────────┘
           │          │          │
    /api/orders /api/cart /api/catalog
           │          │          │
           │    (with API Key)   │
           │          │          │
┌──────────┴──────────┴──────────┴────────────────────────────────┐
│                    NGINX REVERSE PROXY                           │
│           Routes with API Key validation                         │
└──────────┬──────────┬──────────┬────────────────┬────────────────┘
           │          │          │                │
       Port 8003  Port 8001  Port 8002         Port 8004
           │          │          │                │
      ┌────▼──┐   ┌────▼──┐  ┌────▼──┐      ┌────▼────┐
      │ ORDER │   │ CART  │  │CATALOG│      │ PAYMENT │
      │ SVC   │   │ SVC   │  │ SVC   │      │ SVC     │
      └───┬───┘   └───┬───┘  └───┬───┘      └────┬────┘
          │           │          │              │
          │ (calls)   │ (calls)  │ (calls)      │
          │           │          │              │
          │           ▼          │              │
          │   ┌─────────────────────┐           │
          │   │  CATALOG SERVICE    │           │
          │   │   (Validation)      │           │
          │   └─────────────────────┘           │
          │                                    │
          ├────────────────────────────────────┘
          │
          ▼
    ┌──────────────────┐
    │ ORDER SERVICE    │
    │ (Status Update)  │
    └──────────────────┘
           ▲
           │ (webhook)
           │
      ┌────┴────────────┐
      │ PAYMENT SERVICE │
      │ (Notification)  │
      └─────────────────┘


┌─────────────────────────────────────────────────────────────────┐
│                      DATABASE LAYER                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐      │
│  │  carts.db    │  │ products.db  │  │   orders.db      │      │
│  │              │  │              │  │                  │      │
│  │ - user_id    │  │ - id         │  │ - order_id       │      │
│  │ - items[]    │  │ - name       │  │ - user_id        │      │
│  │ - timestamps │  │ - price      │  │ - items[]        │      │
│  │              │  │ - stock      │  │ - status         │      │
│  │              │  │ - timestamps │  │ - total_amount   │      │
│  │              │  │              │  │ - timestamps     │      │
│  └──────────────┘  └──────────────┘  └──────────────────┘      │
│                                                                   │
│                      ┌──────────────┐                            │
│                      │payments.db   │                            │
│                      │              │                            │
│                      │ - payment_id │                            │
│                      │ - order_id   │                            │
│                      │ - amount     │                            │
│                      │ - status     │                            │
│                      │ - timestamp  │                            │
│                      └──────────────┘                            │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Service Communication Flow

### Flow 1: Adding Product to Cart with Validation

```
1. User clicks "Add to Cart" (product_id=1)
   │
   ├─→ Frontend: POST /api/cart/demo-user/add?product_id=1&quantity=1
   │            Header: X-API-Key: secret-key-123
   │
   ├─→ NGINX → Routes to Cart Service (8001)
   │
   ├─→ Cart Service: add_to_cart()
   │   │
   │   ├─→ verify_api_key() → ✅ Valid
   │   │
   │   ├─→ validate_product(1)
   │   │   │
   │   │   └─→ HTTP GET http://localhost:8002/products
   │   │       Header: X-API-Key: secret-key-123
   │   │       │
   │   │       └─→ Catalog Service returns:
   │   │           [{id:1, name:"Laptop", price:999.99, stock:50}, ...]
   │   │
   │   │   ✅ Product 1 found → return True
   │   │
   │   ├─→ Connect to carts.db
   │   │
   │   ├─→ BEGIN TRANSACTION
   │   │   │
   │   │   ├─→ SELECT items FROM carts WHERE user_id = 'demo-user'
   │   │   │   (returns existing items or empty)
   │   │   │
   │   │   ├─→ Append new item: {product_id: 1, quantity: 1}
   │   │   │
   │   │   ├─→ INSERT/UPDATE carts with new items
   │   │   │
   │   │   └─→ COMMIT
   │   │
   │   └─→ Return: {message: "Item added", cart: [...]}
   │
   ├─→ Frontend receives response
   │
   └─→ Display: "Item added to cart!"
```

---

### Flow 2: Processing Payment and Updating Order

```
1. User clicks "Checkout"
   │
   ├─→ Frontend: POST /api/pay?order_id=<uuid>&amount=999.99
   │            Header: X-API-Key: secret-key-123
   │
   ├─→ NGINX → Routes to Payment Service (8004)
   │
   ├─→ Payment Service: pay()
   │   │
   │   ├─→ verify_api_key() → ✅ Valid
   │   │
   │   ├─→ Generate payment_id (UUID)
   │   │
   │   ├─→ Connect to payments.db
   │   │
   │   ├─→ BEGIN TRANSACTION
   │   │   │
   │   │   ├─→ INSERT INTO payments (payment_id, order_id, amount, status)
   │   │   │   VALUES (<uuid>, <order_uuid>, 999.99, 'COMPLETED')
   │   │   │
   │   │   └─→ COMMIT
   │   │
   │   ├─→ HTTP POST http://localhost:8003/orders/<order_id>/payment
   │   │       Header: X-API-Key: secret-key-123
   │   │       │
   │   │       └─→ Order Service: order_payment()
   │   │           │
   │   │           ├─→ verify_api_key() → ✅ Valid
   │   │           │
   │   │           ├─→ Connect to orders.db
   │   │           │
   │   │           ├─→ BEGIN TRANSACTION
   │   │           │   │
   │   │           │   ├─→ UPDATE orders
   │   │           │   │   SET status = 'PAID', updated_at = NOW()
   │   │           │   │   WHERE order_id = '<order_id>'
   │   │           │   │
   │   │           │   └─→ COMMIT
   │   │           │
   │   │           └─→ Return: {order_id, status: 'PAID'}
   │   │
   │   ├─→ Payment Service receives confirmation
   │   │
   │   └─→ Return: {payment_id, order_id, status: 'PAID', message: "Payment successful and order updated"}
   │
   ├─→ Frontend receives response
   │
   └─→ Display: "Payment successful! Order #<id> is now paid."
```

---

### Flow 3: Cart Product Validation with Error Handling

```
Scenario A: Valid Product
─────────────────────────────────────────

1. User adds product_id=1 (Laptop)
2. Cart validates: GET /products from Catalog
3. Response: [{id:1, ...}, {id:2, ...}, {id:3, ...}]
4. Validation: any(p["id"] == 1) → ✅ True
5. Item added to cart
6. Response: 200 OK


Scenario B: Invalid Product
─────────────────────────────────────────

1. User adds product_id=999 (doesn't exist)
2. Cart validates: GET /products from Catalog
3. Response: [{id:1, ...}, {id:2, ...}, {id:3, ...}]
4. Validation: any(p["id"] == 999) → ❌ False
5. Item NOT added to cart
6. Response: 404 "Product 999 not found in catalog"


Scenario C: Catalog Service Down
─────────────────────────────────────────

1. User adds product_id=1
2. Cart validates: GET /products from Catalog
3. Connection timeout (5 seconds)
4. Exception caught
5. Fail-open strategy: return True (allow operation)
6. Item added to cart
7. Response: 200 OK (operation allowed despite service unavailability)
```

---

## Authentication & Authorization Flow

```
Request with API Key
────────────────────

1. Client prepares request:
   GET /cart/user1
   Header: X-API-Key: secret-key-123

2. Request reaches service endpoint

3. FastAPI extracts header: x_api_key = "secret-key-123"

4. Call verify_api_key(x_api_key)
   │
   ├─→ if x_api_key != "secret-key-123":
   │   │
   │   └─→ raise HTTPException(401, "Invalid API Key")
   │       │
   │       └─→ Return 401 Unauthorized
   │
   └─→ else:
       │
       └─→ return x_api_key (validation passed)

5. Execute protected endpoint logic

6. Return response with status 200

Response Scenarios:
──────────────────

✅ Correct API Key:
   Status: 200 OK
   Body: Data returned

❌ Missing API Key:
   Status: 401 Unauthorized
   Body: {"detail": "Invalid API Key"}

❌ Wrong API Key:
   Status: 401 Unauthorized
   Body: {"detail": "Invalid API Key"}

✅ Health Check (no API key):
   Status: 200 OK
   Body: {"status": "..."}
```

---

## Transaction & Database Operations

### Transaction Example: Order Creation

```
POST /orders?user_id=user1
Body: [{"product_id": 1, "quantity": 1, "price": 999.99}]

Order Service Processing:
──────────────────────────

1. verify_api_key() → ✅

2. Generate order_id = UUID()

3. Calculate: total_amount = 999.99 * 1 = 999.99

4. conn = sqlite3.connect("orders.db")

5. c = conn.cursor()

6. BEGIN TRANSACTION (implicit in SQLite)
   │
   ├─→ c.execute(
   │   "INSERT INTO orders (order_id, user_id, items, total_amount)",
   │   (<uuid>, 'user1', '[{"product_id":1...}]', 999.99)
   │   )
   │
   ├─→ conn.commit()  ← Writes to disk atomically
   │
   └─→ If exception: conn.rollback()  ← Reverses all changes

7. conn.close()

8. return {order_id, status: "CREATED"}

Database State After:
──────────────────────
orders table:
┌─────────┬────────┬───────┬─────────┬──────────────┐
│order_id │user_id │items  │ status  │total_amount  │
├─────────┼────────┼───────┼─────────┼──────────────┤
│<uuid>   │user1   │[...]  │CREATED  │999.99        │
└─────────┴────────┴───────┴─────────┴──────────────┘
```

---

## Database Persistence Example

```
Scenario: Service Restart with Data Persistence
────────────────────────────────────────────────

STEP 1: Initial State
┌─────────────────────┐
│ Cart Service (8001) │
│                     │
│ In Memory:          │
│ carts = {}          │
│                     │
│ On Disk:            │
│ carts.db (empty)    │
└─────────────────────┘

STEP 2: Add Item to Cart
POST /cart/user1/add?product_id=1&quantity=2

┌─────────────────────┐
│ Cart Service (8001) │
│                     │
│ In Memory:          │
│ carts = {           │
│  "user1": [{...}]   │ ← temporary copy
│ }                   │
│                     │
│ On Disk:            │
│ carts.db:           │
│ ├─ user_id: user1   │
│ ├─ items: [...]     │ ← PERSISTED
│ └─ timestamp: ...   │
└─────────────────────┘

STEP 3: Service Stops / Restarts
❌ Restart (Process dies)

┌─────────────────────┐
│ Cart Service (8001) │
│                     │
│ In Memory: EMPTY    │
│ carts = {}          │
│                     │
│ On Disk:            │
│ carts.db:           │
│ ├─ user1: [{...}]   │ ← Data still exists!
│ └─ timestamp: ...   │
└─────────────────────┘

STEP 4: Init DB on Startup
def init_db():
    conn = sqlite3.connect("carts.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS carts (...)
    """)
    conn.commit()

STEP 5: Retrieve Cart
GET /cart/user1

┌──────────────────────────┐
│ SELECT items FROM carts  │
│ WHERE user_id = 'user1'  │
└────────────┬─────────────┘
             │
             ▼
        ✅ Found!
    [{product_id: 1, quantity: 2}]
             │
             ▼
    Return to client

Result: Data survives restart! ✅
```

---

## Security Model

```
API Key Authentication
──────────────────────

Environment:
┌──────────────────────────────┐
│ API_KEY = "secret-key-123"   │
└──────────────────────────────┘

Service Configuration:
┌──────────────────────────┐
│ Cart Service (8001)      │
│ api_key = "secret-key-123" │
├──────────────────────────┤
│ All endpoints:           │
│ ├─ POST /cart/add        │
│ ├─ GET /cart/{id}        │
│ ├─ DELETE /cart/clear    │
│ └─ GET /health           │
└──────────────────────────┘

Request Flow:
┌──────────────┐
│ Client       │
└──────┬───────┘
       │
       ├─ Prepare: GET /cart/user1
       │          Header: X-API-Key: secret-key-123
       │
       ▼
┌──────────────────────┐
│ Service Endpoint     │
│ verify_api_key()     │ ← Middleware/Decorator
└──────────┬───────────┘
           │
           ├─ Extract header: x_api_key
           │
           ├─ Compare: x_api_key == env.API_KEY
           │
           ├─ ✅ Match → Allow request
           │  or
           │  ❌ No match → Return 401
           │
           ▼
       Execute logic

Response:
┌─────────────┐
│ 200 OK      │ (request allowed)
├─────────────┤
│ 401 Unauth  │ (request rejected)
└─────────────┘
```

---

## Error Handling & Resilience

```
Service-to-Service Communication Error Handling
────────────────────────────────────────────────

Scenario 1: Catalog Service Returns Product
─────────────────────────────────────────

try:
    response = requests.get(
        "http://localhost:8002/products",
        headers={"X-API-Key": API_KEY},
        timeout=5
    )
    if response.status_code == 200:
        products = response.json()
        return any(p["id"] == product_id for p in products)
    else:
        return True  # Fail open
except requests.Timeout:
    return True  # Fail open on timeout
except requests.ConnectionError:
    return True  # Fail open on connection error
except Exception:
    return True  # Fail open on any error


Scenario 2: Catalog Service Unavailable
────────────────────────────────────────

User: POST /cart/user1/add?product_id=1
│
├─→ Cart tries to validate product
│
├─→ requests.get("http://localhost:8002/products")
│  └─→ ❌ ConnectionError (service down)
│
├─→ Caught by except block
│
├─→ return True (fail-open)
│
├─→ Product validation passes
│
├─→ Item added to cart anyway
│
└─→ Return: 200 OK

Result: Cart service remains operational even when Catalog is down ✅


Scenario 3: Invalid Product ID
──────────────────────────────

User: POST /cart/user1/add?product_id=999
│
├─→ Catalog returns: [{id:1,...}, {id:2,...}, {id:3,...}]
│
├─→ any(p["id"] == 999 for p in products) → ❌ False
│
├─→ Product validation FAILS
│
├─→ raise HTTPException(404, "Product 999 not found in catalog")
│
└─→ Return: 404 Not Found

Result: Invalid products prevented from cart ✅
```

---

## Summary of Enhancements

| Aspect | Before | After |
|--------|--------|-------|
| **Storage** | In-memory (lost on restart) | SQLite (persistent) |
| **Communication** | Isolated services | HTTP-based inter-service calls |
| **Transactions** | None | SQLite ACID transactions |
| **Auth** | None | API Key authentication |
| **Integration** | Payment isolated | Payment updates order status |
| **Validation** | No checks | Cart validates products |
| **Error Handling** | Basic | Comprehensive with fail-open |
| **Reliability** | Data loss on crash | Automatic recovery from DB |
| **Auditability** | No timestamps | Timestamps on all entities |

