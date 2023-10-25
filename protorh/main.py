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
from models.user_models import UserCreate, UserUpdate, UserConnect, UpdatePassword
import hashlib
import os
from dotenv import load_dotenv

env_file_path = os.path.join(os.path.dirname(__file__), 'protorh.env')

if os.path.exists(env_file_path):
    load_dotenv(dotenv_path=env_file_path)



salt = os.getenv('salt')
SECRET_KEY = os.getenv('SECRET_KEY')
DATABASE_HOST = os.getenv('DATABASE_HOST')
DATABASE_PORT = os.getenv('DATABASE_PORT')
DATABASE_NAME = os.getenv('DATABASE_NAME')
DATABASE_USER = os.getenv('DATABASE_USER')
DATABASE_PASSWORD = os.getenv('DATABASE_PASSWORD')






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



def hash_djb2(s):                                                                                                                                
    hash = 5381
    for x in s:
        hash = (( hash << 5) + hash) + ord(x)
    return hash & 0xFFFFFFFF

def calculate_age(birthdate):
    today = datetime.now()
    age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))
    return age


# Endpoint : /add/user/
# Type : POST
# This endpoint add user and return "Okay".
@app.post("/users/create", response_model=dict)
async def create_user(user: UserCreate):
    
    
    password_salt = user.password + salt
    password_hash = hashlib.md5(password_salt.encode()).hexdigest()
    registration = datetime.now()
        
    age = calculate_age(user.birthdaydate)
    token_hash = hash_djb2(user.email + user.firstname + user.lastname + salt)
    query = text(
        "INSERT INTO users (email,password,firstname,lastname,birthdaydate,address,postalcode, age, meta, registrationdate, token, role) VALUES (:email, :password, :firstname, :lastname, :birthdaydate, :address, :postalcode, :age, :meta, :registrationdate, :token, :role) RETURNING *"
    )
    values = {
        "email" : user.email,
        "password" : password_hash,
        "firstname" : user.firstname,
        "lastname" : user.lastname,
        "birthdaydate" : user.birthdaydate,
        "address" : user.address,
        "postalcode" : user.postalcode,
        "age": age,
        "meta" : json.dumps(user.meta),
        "registrationdate" : registration,
        "token" : token_hash,
        "role" : user.role
    }
    with engine.begin() as conn :
        result = conn.execute(query, values)
    return {'message' : 'Okay'}


def create_jwt_token(data):
    token = jwt.encode(data, SECRET_KEY, algorithm="HS256")
    return token

class TokenResponse(BaseModel):
    access_token: str
    token_type: str

# Endpoint : /connect
# Type : POST
# Connexion avec un jeton JWT
@app.post("/connect/", response_model=TokenResponse)
async def connect_user(user_connect: UserConnect):
    # Recherchez l'utilisateur dans la base de données en utilisant l'e-mail
    user = SessionLocal().query(User).filter(User.email == user_connect.email).first()

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    # Vérifiez si le mot de passe correspond
    if user.password != hashlib.md5((user_connect.password + salt).encode()).hexdigest():
        raise HTTPException(status_code=401, detail="Invalid password")

    # Authentification réussie, générez le jeton JWT
    jwt_data = {"sub": user.email}  # Vous pouvez ajouter d'autres informations au jeton
    jwt_token = create_jwt_token(jwt_data)

    return {"access_token": jwt_token, "token_type": "bearer"}


# Endpoint pour récupérer un utilisateur par ID
@app.get("/users/{user_id}", response_model=UserUpdate)
async def read_user(user_id: int):
    user = SessionLocal().query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# Endpoint : /users
# Type : PUT
# Permet de mettre a jour un utilisateur
@app.patch("/users/update", response_model=UserUpdate)
async def update_user(user_id: int, user_update: UserUpdate):
    # Récupére l'utilisateur existant en fonction de l'ID
    user = SessionLocal().query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    # Met à jour les champs de l'utilisateur avec les données de user_update
    for key, value in user_update.dict().items():
        setattr(user, key, value)

    # Enregistre les modifications dans la base de données
    SessionLocal().commit()

    return user

# Endpoint : /users/password
# Type : POST
# Permet de mettre a jour password
@app.post("/users/password", response_model=UpdatePassword)
async def update_password(jwt_token: int, password_update: UpdatePassword):
    # Récupére l'utilisateur existant en fonction de l'ID
    user = SessionLocal().query(User).filter(User.token == jwt_token).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.password != hashlib.md5((password_update.old_password + salt).encode()).hexdigest():
        raise HTTPException(status_code=400, detail="Ancien mot de passe invalid")
    
    if password_update.new_password != password_update.repeat_new_password:
        raise HTTPException(status_code=400, detail="New password do not match")
    
    new_password_salt = password_update.new_password + salt
    new_password_hash = hashlib.md5(new_password_salt.encode()).hexdigest()
    user.password = new_password_hash

    # ON ENREGISTRE
    SessionLocal().commit()

    return password_update
        
    

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
