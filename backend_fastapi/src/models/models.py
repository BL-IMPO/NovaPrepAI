# src/models/models.py
from sqlalchemy import Column, Integer, String
from src.database import Base


class Product(Base):
    __tablename__ = "users_product"  # Django's table name

    id = Column(Integer, primary_key=True)
    name = Column(String(100))  # Match Django's max_length=100
    price = Column(Integer)  # Django uses IntegerField, not Numeric

    def __repr__(self):
        return f"<Product(id={self.id}, name='{self.name}', price={self.price})>"