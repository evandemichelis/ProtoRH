import subprocess, uvicorn
from psycopg2 import Date
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import DATE, DateTime, JSON, Boolean, create_engine, Column, Integer, String, Float, text, or_
from sqlalchemy.orm import sessionmaker
from jose import JWSError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy_utils import database_exists, create_database
from pydantic import BaseModel, Json, NaiveDatetime
from typing import Dict, List
import json
from models.models import Base, User, Department
from models.user_models import UserCreate, UserUpdate, UserConnect
from config import *
import hashlib


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

# Endpoint pour récupérer la liste des utilisateurs
@app.get("/users/", response_model=List[UserUpdate])
async def read_users():
    users = SessionLocal().query(User).all()
    return users


# Endpoint pour récupérer un utilisateur par ID
@app.get("/users/{user_id}", response_model=UserUpdate)
async def read_user(user_id: int):
    user = SessionLocal().query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user
def hash_djb2(s):                                                                                                                                
    hash = 5381
    for x in s:
        hash = (( hash << 5) + hash) + ord(x)
    return hash & 0xFFFFFFFF

def calculate_age(birthdate):
    today = datetime.now()
    age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))
    return age

# Endpoint : /users
# Type : POST
# Permet de créer un nouvel utilisateur
@app.post("/users/create", response_model=UserCreate)
async def create_user(user: UserCreate):
    

    if user.Password_repeat != user.Password:
        raise HTTPException(status_code=404, detail="Password invalid!")
    password_salt = user.Password + salt
    password_hash = hashlib.md5(password_salt).hexdigest()

    age = calculate_age(user.BirthdayDate)
    token_hash = hash_djb2(user.Email + user.Firstname + user.Lastname + salt)
    query = text("INSERT INTO users (\"Email\", \"Password\", \"Firstname\", \"Lastname\", \"BirthdayDate\", \"Address\", \"PostalCode\", \"Age\", \"Meta\", \"RegistrationDate\", \"Token\", \"Role\") VALUES (:Email, :Password, :Firstname, :Lastname, :BirthdayDate, :Address, :PostalCode, :Age, :Meta, :RegistrationDate, :Token, :Role) RETURNING *")
    values = {
        "Email" : user.Email,
        "Password" : password_hash,
        "Firstname" : user.Firstname,
        "Lastname" : user.Lastname,
        "BirthdayDate" : user.BirthdayDate,
        "Address" : user.Address,
        "PostalCode" : user.PostalCode,
        "Age" : age,
        "Meta" : json.dumps({}),
        "RegistrationDate" : user.RegistrationDate,
        "Token" : token_hash,
        "Role" : "user"
    }
    with engine.begin() as conn:
        result = conn.execute(query, values)
        return result.fetchone()


# Endpoint : /connect 
# Type : POST
# Connexion avec un jeton JWT
@app.post("/connect/", response_model=UserConnect):
async def connect_user(user_id: int, user_connect: UserConnect):
    if user_connect.Email != UserCreate.Email:
        raise HTTPException(status_code=404, detail="Password invalid!")






# Endpoint : /users
# Type : PUT
# Permet de mettre a jour un utilisateur
@app.patch("/users/{user_id}", response_model=UserUpdate)
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
