# src/main.py
from fastapi import FastAPI
from src.database import SessionLocal
from src.models.models import Product

app = FastAPI()

@app.get("/products")
def get_products():
    db = SessionLocal()
    try:
        products = db.query(Product).all()
        return [
            {"id": p.id, "name": p.name, "price": p.price}  # No float conversion needed
            for p in products
        ]
    finally:
        db.close()

# REMOVE THIS LINE: Base.metadata.create_all(bind=engine)

#if __name__ == "__main__":
#    uvicorn.run("main:app", host="0.0.0.0", port=8001)