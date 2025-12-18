from fastapi import FastAPI

app = FastAPI(title="Catalog Service")

@app.get("/health")
def health():
    return {"status": "Catalog service is running"}
