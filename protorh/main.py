import subprocess, uvicorn
from psycopg2 import Date
from fastapi import FastAPI, HTTPException
from sqlalchemy import DATE, DateTime, JSON, Boolean, create_engine, Column, Integer, String, Float, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy_utils import database_exists, create_database
from pydantic import BaseModel, Json, NaiveDatetime
from typing import Dict
import json
from models import Base, User, Department
from user_models import UserCreate, UserUpdate



DATABASE_URL = "postgresql://lounes:lehacker147@localhost/proto"
engine = create_engine(DATABASE_URL)
if not database_exists(engine.url):
    create_database(engine.url, template="template0")



SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


Base.metadata.create_all(bind=engine)



app = FastAPI()

@app.get("/")
async def read_root():
    return {"message":  "Hello, World"}

@app.get("/exit")
async def stop_server():
    subprocess.call(["pkill", "uvicorn"])
    return {"message" : "Server Stopped"}


# Endpoint : /users
# Type : POST
# Permet de créer un nouvel utilisateur
@app.post("/users/", response_model=UserCreate)
async def create_user(user: UserCreate):
    query = text("INSERT INTO users (\"Email\", \"Password\", \"Firstname\", \"Lastname\", \"BirthdayDate\", \"Address\", \"PostalCode\", \"Age\", \"Meta\", \"RegistrationDate\", \"Token\", \"Role\") VALUES (:Email, :Password, :Firstname, :Lastname, :BirthdayDate, :Address, :PostalCode, :Age, :Meta, :RegistrationDate, :Token, :Role) RETURNING *")
    values = {
        "Email" : user.Email,
        "Password" : user.Password,
        "Firstname" : user.Firstname,
        "Lastname" : user.Lastname,
        "BirthdayDate" : user.BirthdayDate,
        "Address" : user.Address,
        "PostalCode" : user.PostalCode,
        "Age" : user.Age,
        "Meta" : json.dumps(user.Meta),
        "RegistrationDate" : user.RegistrationDate,
        "Token" : user.Token,
        "Role" : user.Role
    }
    with engine.begin() as conn:
        result = conn.execute(query, values)
        return result.fetchone()



# Endpoint : /users
# Type : PUT
# Permet de mettre a jour un utilisateur
@app.put("/users/{user_id}", response_model=User)
async def update_user(user_id: int, user_update: UserUpdate):
    # Récupérez l'utilisateur existant en fonction de l'ID
    user = SessionLocal().query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    # Mettez à jour les champs de l'utilisateur avec les données de user_update
    for key, value in user_update.dict().items():
        setattr(user, key, value)

    # Enregistrez les modifications dans la base de données
    SessionLocal().commit()

    return user



# Endpoint : /users
# Type : DELETE
# this endpoint return à json string containing "Hello Link!"
@app.delete("/users/{user_id}", response_model=UserCreate)
async def delete_user(user_id : int):
    query = text("DELETE FROM users WHERE id = :user_id RETURNING *")
    values = {"user_id": user_id}
    with engine.begin() as conn:
        result = conn.execute(query, values)
        deleted_user = result.fetchone()
        if not deleted_user:
            raise HTTPException(status_code=404, detail ="User not found")
        return deleted_user
