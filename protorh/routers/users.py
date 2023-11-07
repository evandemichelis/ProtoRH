import subprocess, uvicorn
from psycopg2 import Date
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, Depends, status, UploadFile, File
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import DATE, DateTime, JSON, Boolean, create_engine, Column, Integer, String, Float, text, or_
from sqlalchemy.orm import sessionmaker
from jose import JWSError, JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy_utils import database_exists, create_database
from pydantic import BaseModel, Json, NaiveDatetime
from typing import Dict, List
import json
from models.department_models import DepartmentCreate, DepartmentList
from models.models import Base, User, Department
from models.user_models import UserCreate, UserUpdate, UserConnect, UpdatePassword, UserResponse
import hashlib
from pathlib import Path
from PIL import Image
import os
import io
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
#################################################
#                                               #
#                                               #
#                  START USERS                  #
#                                               #
#                                               #
#################################################


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
# Connexion avec un jeton JWT temporaire
@app.post("/connect/", response_model=TokenResponse)
async def connect_user(user_connect: UserConnect):
    # Recherche l'utilisateur dans la base de données en utilisant l'e-mail
    user = SessionLocal().query(User).filter(User.email == user_connect.email).first()

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    # Vérifie si le mot de passe correspond
    if user.password != hashlib.md5((user_connect.password + salt).encode()).hexdigest():
        raise HTTPException(status_code=401, detail="Invalid password")

    # Générez un jeton JWT temporaire
    jwt_data = {
        "email": user.email,
        "exp": datetime.utcnow() + timedelta(minutes=3600)
    }
    jwt_token = jwt.encode(jwt_data, SECRET_KEY, algorithm="HS256")

    return {"access_token": jwt_token, "token_type": "bearer"}


# Endpoint : /users/{user_id}
# Type : GET
# Récupération d'utilisateur
@app.get("/users/{user_id}", response_model=UserResponse)
async def read_user(user_id: int, jwt_token: str):
    try:
        # Verify the JWT token and retrieve claims
        jwt_data = jwt.decode(jwt_token, SECRET_KEY, algorithms=["HS256"])
        email = jwt_data.get("email")

        # Retrieve the user from the database based on user_id
        user = SessionLocal().query(User).filter(User.id == user_id).first()

        if user is None:
            raise HTTPException(status_code=404, detail="User not found")

        # Check the user's role to determine which fields to return
        user_data = UserResponse(
            email=user.email,
            firstname=user.firstname,
            lastname=user.lastname,
            role=user.role,
        )

        # If the user is an admin, return all fields
        if user.role == "admin":
            user_data.address = user.address
            user_data.postalcode = user.postalcode
            user_data.age = user.age
            user_data.birthdaydate = user.birthdaydate
            user_data.meta = user.meta
            user_data.token = user.token

        return user_data
    except JWSError:
        raise HTTPException(status_code=401, detail="Invalid token")


# Endpoint : /users/update
# Type : POST
# Permet de mettre à jour un utilisateur
@app.post("/users/update", response_model=UserUpdate)
async def update_user(user_id: int, user_update: UserUpdate, jwt_token: str):
    try:
        # Verify the JWT token and retrieve claims
        jwt_data = jwt.decode(jwt_token, SECRET_KEY, algorithms=["HS256"])
        email = jwt_data.get("email")

        # Retrieve the user to be updated
        user = SessionLocal().query(User).filter(User.email == email).first()

        if user is None:
            raise HTTPException(status_code=404, detail="User not found")

        # Check if the user is trying to modify restricted fields
        if user_update.firstname != user.firstname and user.role != "admin":
            raise HTTPException(status_code=400, detail="Modifying 'firstname' field is not allowed")

        if user_update.lastname != user.lastname and user.role != "admin":
            raise HTTPException(status_code=400, detail="Modifying 'lastname' field is not allowed")

        if user_update.role != user.role and user.role != "admin":
            raise HTTPException(status_code=400, detail="Modifying 'role' field is not allowed")

        # Construct the SQL query to update user information
        query = text(
            "UPDATE users SET email = :email, birthdaydate = :birthdaydate, address = :address, postalcode = :postalcode "
            "WHERE id = :user_id RETURNING *"
        )
        values = {
            "user_id": user_id,
            "email": user_update.email,
            "birthdaydate": user_update.birthdaydate,
            "address": user_update.address,
            "postalcode": user_update.postalcode,
        }

        # Execute the SQL query and get the updated user
        with engine.begin() as conn:
            result = conn.execute(query, values)
            updated_user = result.fetchone()

        if updated_user is None:
            raise HTTPException(status_code=404, detail="User not found")

        # Return the updated user data
        return UserUpdate(updated_user)
    except JWSError:
        raise HTTPException(status_code=401, detail="Invalid token")



# Endpoint : /users/password
# Type : PATCH
# Update the user's password
@app.patch("/users/password", response_model=UpdatePassword)
async def update_password(jwt_token: str, password_update: UpdatePassword):
    try:
        # Verify the JWT token and retrieve claims
        jwt_data = jwt.decode(jwt_token, SECRET_KEY, algorithms=["HS256"])
        email = jwt_data.get("email")

        # Retrieve the user based on the email
        user = SessionLocal().query(User).filter(User.email == email).first()

        if user is None:
            raise HTTPException(status_code=404, detail="User not found")

        # Check if the provided old password is valid
        if user.password != hashlib.md5((password_update.old_password + salt).encode()).hexdigest():
            raise HTTPException(status_code=400, detail="Invalid old password")

        # Check if the new password and repeat new password match
        if password_update.new_password != password_update.repeat_new_password:
            raise HTTPException(status_code=400, detail="New passwords do not match")

        # Hash the new password
        new_password_salt = password_update.new_password + salt
        new_password_hash = hashlib.md5(new_password_salt.encode()).hexdigest()

        # Use SQL query to update the password
        query = text("UPDATE users SET password = :new_password WHERE email = :email")
        values = {"new_password": new_password_hash, "email": email}

        # Execute the SQL query to update the password
        with engine.begin() as conn:
            conn.execute(query, values)

        # Commit the changes to the database
        SessionLocal().commit()

        return password_update
    except JWSError:
        raise HTTPException(status_code=401, detail="Invalid token")
    




# Endpoint : /upload/picture/user/{user_id}
# Type : POST
# Permet de télécharger une image de profil pour un utilisateur spécifique
@app.post("/upload/picture/user/{user_id}", response_model=str)
async def upload_user_profile_picture(user_id: int, image: UploadFile):
    user = SessionLocal().query(User).filter(User.id == user_id).first()

    if user is None:
        return {"type": "user_error", "error": "User not found"}

    # Vérifie l'extension du fichier
    good_extensions = {'png', 'jpg', 'gif'}
    file_extension = image.filename.split(".")[-1].lower()
    if file_extension not in good_extensions:
        return {"type": "upload_error", "error": "Invalid file format"}

    # Vérifie la taille de l'image
    max_width, max_height = 800, 800
    image_data = await image.read()
    image_obj = Image.open(io.BytesIO(image_data))
    if image_obj.width > max_width or image_obj.height > max_height:
        return {"type": "upload_error", "error": "Image size exceeds the limit"}

    # Enregistre l'image dans le répertoire d'images de profil
    picture_name = user.token + "." + file_extension
    picture_path = os.path.join("assets", "picture", "profiles", picture_name)

    with open(picture_path, "wb") as picture_file:
        picture_file.write(image_data)

    # Met à jour la base de données avec le chemin de l'image
    query = text("UPDATE users SET profile_picture = :picture_filename WHERE id = :user_id")
    values = {"picture_filename": picture_name, "user_id": user_id}

    with engine.begin() as conn:
        conn.execute(query, values)

    return {"image_url": picture_path}



# Endpoint : /picture/user/{user_id}
# Type : POST
# Permet de télécharger une image de profil pour un utilisateur spécifique
@app.get("/picture/user/{user_id}", response_model=str)
async def get_user_profile_picture(user_id: int):
    # Query the database to get the user's profile picture filename
    query = text("SELECT profile_picture FROM users WHERE id = :user_id")
    values = {"user_id": user_id}

    with engine.begin() as conn:
        result = conn.execute(query, values)
        profile_picture = result.scalar()

    if not profile_picture:
        raise HTTPException(status_code=404, detail="Profile picture not found for the user")

    # Construct the path to the profile picture file
    picture_path = Path("assets/picture/profiles") / profile_picture

    # Check if the file exists
    if not picture_path.is_file():
        raise HTTPException(status_code=404, detail="Profile picture file not found on the server")

    return {"image_url": str(picture_path)}

#################################################
#                                               #
#                                               #
#                  END USERS                    #
#                                               #
#                                               #
#################################################

