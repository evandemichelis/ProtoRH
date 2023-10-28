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
        "exp": datetime.utcnow() + timedelta(minutes=30)
    }
    jwt_token = jwt.encode(jwt_data, SECRET_KEY, algorithm="HS256")

    return {"access_token": jwt_token, "token_type": "bearer"}


# Endpoint : /users/{user_id}
# Type : GET
# Récupération d'utilisateur
@app.get("/users/{user_id}", response_model=UserResponse)
async def read_user(user_id: int, jwt_token: str):
    try:
        # Vérifiez le jeton JWT et récupérez les réclamations
        jwt_data = jwt.decode(jwt_token, SECRET_KEY, algorithms=["HS256"])
        email = jwt_data.get("email")

        # Recherchez l'utilisateur dans la base de données en utilisant l'e-mail
        user = SessionLocal().query(User).filter(User.email == email).first()

        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        

        user_data = UserResponse(
            email=user.email,
            firstname=user.firstname,
            lastname=user.lastname,
            role=user.role,
            address=user.address if user.role == "admin" else "",
            postalcode=user.postalcode if user.role == "admin" else ""
        )
        return user_data
    except JWSError:
        raise HTTPException(status_code=401, detail="Invalid token")


# Endpoint : /users/update
# Type : PATCH
# Permet de mettre à jour un utilisateur
@app.patch("/users/update", response_model=UserUpdate)
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

        # Construct the SQL query
        query = text(
            "UPDATE users SET email = :email, firstname = :firstname, "
            "lastname = :lastname, birthdaydate = :birthdaydate, "
            "address = :address, postalcode = :postalcode "
            "WHERE id = :user_id RETURNING *"
        )
        values = {
            "user_id": user_id,
            "email": user_update.email,
            "firstname": user_update.firstname,
            "lastname": user_update.lastname,
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
        return UserUpdate(**updated_user)
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
    image_obj = Image.open(image_data)
    if image_obj.width > max_width or image_obj.height > max_height:
        return {"type": "upload_error", "error": "Image size exceeds the limit"}

    # Enregistre l'image dans le répertoire d'images de profil
    picture_name = user.token + "." + file_extension
    picture_path = Path("assets/picture/profiles") / picture_name
    with open(picture_path, "wb") as picture_file:
        picture_file.write(image_data)

    # Met à jour la base de données avec le chemin de l'image
    query = text("UPDATE users SET profile_picture = :picture_filename WHERE id = :user_id")
    values = {"picture_filename": picture_name, "user_id": user_id}

    with engine.begin() as conn:
        conn.execute(query, values)

    return {"image_url": str(picture_path)}  


#################################################
#                                               #
#                                               #
#                  END USERS                    #
#                                               #
#                                               #
#################################################






#################################################
#                                               #
#                                               #
#              START DEPARTMENTS                #
#                                               #
#                                               #
#################################################




oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_current_user(jwt_token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(jwt_token, SECRET_KEY, algorithms=["HS256"])
        email = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Could not validate credentials")
        return email
    except JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

    
# Endpoint : /departements/{id_departement}/users/add
# Type : POST
# Permet d'ajouter des utilisateurs à un département
@app.post("/departements/{id_departement}/users/add", response_model=DepartmentList)
async def add_users_to_department(id_departement: int, users: List[DepartmentCreate], jwt_token: str = Depends(get_current_user)):
    # Vérifiez l'existence du département
    department = SessionLocal().query(Department).filter(Department.id == id_departement).first()
    if department is None:
        raise HTTPException(status_code=404, detail="Department not found")

    # Vérifiez le rôle de l'utilisateur actuel
    user = SessionLocal().query(User).filter(User.email == get_user_email_from_token(jwt_token)).first()
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Only administrators can add users to a department")

    users_added = []

    for user_data in users:
        user_id = user_data.id

        # Vérifiez si l'utilisateur est déjà dans le département
        if user_id in [user.id for user in department.users]:
            continue

        # Ajoutez l'utilisateur au département en utilisant une commande SQL
        query = text("INSERT INTO department (id, name) VALUES (:id, :name)")
        values = {"id": id_departement, "name": user_id}

        with engine.begin() as conn:
            conn.execute(query, values)

        # Ajoutez l'utilisateur à la liste des utilisateurs ajoutés
        user_added = SessionLocal().query(User).filter(User.id == user_id).first()
        users_added.append(user_added)

    # Enregistrez les modifications dans la base de données
    SessionLocal().commit()

    # Renvoyez la liste des utilisateurs ajoutés
    return DepartmentList(departments=users_added)



# Endpoint : /departements/{id_departement}/users/remove
# Type : POST
# Permet de retirer des utilisateurs d'un département
@app.post("/departements/{id_departement}/users/remove", response_model=DepartmentList)
async def remove_users_from_department(id_departement: int, users: List[DepartmentCreate], jwt_token: str = Depends(get_current_user)):
    # Vérifiez l'existence du département
    department = SessionLocal().query(Department).filter(Department.id == id_departement).first()
    if department is None:
        raise HTTPException(status_code=404, detail="Department not found")

    # Vérifiez le rôle de l'utilisateur actuel
    user = SessionLocal().query(User).filter(User.email == get_user_email_from_token(jwt_token)).first()
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Only administrators can remove users from a department")

    users_removed = []

    for user_data in users:
        user_id = user_data.id

        # Vérifiez si l'utilisateur est dans le département
        if user_id not in [user.id for user in department.users]:
            continue

        # Retirez l'utilisateur du département en utilisant une commande SQL
        query = text("DELETE FROM department WHERE id = :id AND name = :name")
        values = {"id": id_departement, "name": user_id}

        with engine.begin() as conn:
            conn.execute(query, values)

        # Ajoutez l'utilisateur à la liste des utilisateurs retirés
        user_removed = SessionLocal().query(User).filter(User.id == user_id).first()
        users_removed.append(user_removed)

    # Enregistrez les modifications dans la base de données
    SessionLocal().commit()

    # Renvoyez la liste des utilisateurs retirés
    return DepartmentList(departments=users_removed)






















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
 