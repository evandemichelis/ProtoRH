import subprocess, uvicorn
from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine, Column, Integer, String, Float, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy_utils import database_exists, create_database
from pydantic import BaseModel

DATABASE_URL = "postgresql://lounes:lehacker147@localhost/proto"
engine = create_engine(DATABASE_URL)
if not database_exists(engine.url):
    create_database(engine.url, template="template0")



SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    price = Column(Float)
    quantity = Column(Integer)


class ItemCreate (BaseModel):
    name : str
    price : float
    quantity : int

class ItemUpdate (BaseModel):
    name : str
    price : float
    quantity : int


Base.metadata.create_all(bind=engine)



app = FastAPI()

@app.get("/")
async def read_root():
    return {"message":  "Hello, World"}

@app.get("/exit")
async def stop_server():
    subprocess.call(["pkill", "uvicorn"])
    return {"message" : "Server Stopped"}

@app.post("/items/", response_model=ItemCreate)
async def create_item(item: ItemCreate):
    query = text("INSERT INTO items (name, price, quantity) VALUES (:name, :price, :quantity) RETURNING *")
    values = {
        "name" : item.name,
        "price" : item.price,
        "quantity" : item.quantity
    }
    with engine.begin() as conn:
        result = conn.execute(query, values)
        return result.fetchone()

@app.delete("/items/{item_id}", response_model=ItemCreate)
async def delete_item(item_id : int):
    query = text("DELETE FROM items WHERE id = :item_id RETURNING *")
    values = {"item_id": item_id}
    with engine.begin() as conn:
        result = conn.execute(query, values)
        deleted_item = result.fetchone()
        if not deleted_item:
            raise HTTPException(status_code=404, detail ="Item not found")
        return deleted_item