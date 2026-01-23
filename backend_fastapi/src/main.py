from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.database import SessionLocal
from src.models.models import Product

app = FastAPI()

# ------- CORS ---------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ----------------------

@app.get("/products")
def get_products():
    db = SessionLocal()
    try:
        products = db.query(Product).all()
        return [
            {"id": p.id, "name": p.name, "price": p.price}
            for p in products
        ]
    finally:
        db.close()

#if __name__ == "__main__":
#    uvicorn.run("main:app", host="0.0.0.0", port=8001)