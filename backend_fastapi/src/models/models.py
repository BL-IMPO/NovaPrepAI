# src/models/models.py
from sqlalchemy import Column, Integer, String
from src.database import Base


#class Product(Base):
#    __tablename__ = "users_product"
#
#    id = Column(Integer, primary_key=True)
#    name = Column(String(100))
#    price = Column(Integer)
#
#    def __repr__(self):
#        return f"<Product(id={self.id}, name='{self.name}', price={self.price})>"