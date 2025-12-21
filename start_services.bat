@echo off
REM Start Cart Service
cd /d f:\assignments\cloud\project\ecommerce-microservices\cart-service
start "Cart Service" F:/assignments/cloud/project/ecommerce-microservices/.venv/Scripts/python.exe -m uvicorn main:app --host 0.0.0.0 --port 8001

timeout /t 2

REM Start Catalog Service
cd /d f:\assignments\cloud\project\ecommerce-microservices\catalog-service
start "Catalog Service" F:/assignments/cloud/project/ecommerce-microservices/.venv/Scripts/python.exe -m uvicorn main:app --host 0.0.0.0 --port 8002

timeout /t 2

REM Start Order Service
cd /d f:\assignments\cloud\project\ecommerce-microservices\order-service
start "Order Service" F:/assignments/cloud/project/ecommerce-microservices/.venv/Scripts/python.exe -m uvicorn main:app --host 0.0.0.0 --port 8003

timeout /t 2

REM Start Payment Service
cd /d f:\assignments\cloud\project\ecommerce-microservices\payment-service
start "Payment Service" F:/assignments/cloud/project/ecommerce-microservices/.venv/Scripts/python.exe -m uvicorn main:app --host 0.0.0.0 --port 8004

echo.
echo All services started!
echo.
echo Cart Service: http://localhost:8001
echo Catalog Service: http://localhost:8002
echo Order Service: http://localhost:8003
echo Payment Service: http://localhost:8004
pause
