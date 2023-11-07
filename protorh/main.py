import subprocess, uvicorn
from psycopg2 import Date
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, Depends, status, UploadFile, File, Header
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
from models.department_models import DepartmentBase, DepartmentCreate, DepartmentCreateResponse, DepartmentList
from models.models import Base, User, Department
from models.user_models import UserCreate, UserUpdate, UserConnect, UpdatePassword, UserResponse
import hashlib
from pathlib import Path
from PIL import Image
import os
import io
from dotenv import load_dotenv





DATABASE_URL = "postgresql://lounes:lehacker147@localhost/proto"
engine = create_engine(DATABASE_URL)
if not database_exists(engine.url):
    create_database(engine.url, template="template0")



SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


Base.metadata.create_all(bind=engine)

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
        "exp": datetime.utcnow() + timedelta(minutes=3600),
        "role": user.role
    }

    jwt_token = jwt.encode(jwt_data, SECRET_KEY, algorithm="HS256")

    return {"access_token": jwt_token, "token_type": "bearer"}




from fastapi import HTTPException

@app.get("/users/{user_id}", response_model=UserResponse)
async def read_user(user_id: int, authorization: str = Header(None)):
    try:
        # Vérifiez si le jeton JWT est fourni dans l'en-tête d'autorisation
        if not authorization:
            raise HTTPException(status_code=401, detail="Authorization token is missing")

        # Extrait le jeton JWT de l'en-tête d'autorisation
        jwt_token = authorization.split(' ')[-1]

        # Vérifiez le jeton JWT et récupérez les revendications
        jwt_data = jwt.decode(jwt_token, SECRET_KEY, algorithms=["HS256"])
        email = jwt_data.get("email")

        # Récupérez l'utilisateur depuis la base de données en fonction de user_id
        user = SessionLocal().query(User).filter(User.id == user_id).first()

        if user is None:
            raise HTTPException(status_code=404, detail="User not found")

        # Vérifiez le rôle de l'utilisateur pour déterminer les champs à renvoyer
        user_data = UserResponse(
            email=user.email,
            firstname=user.firstname,
            lastname=user.lastname,
            role=user.role,
            age=user.age,
            birthdaydate=user.birthdaydate,
            password=user.password,
            address=user.address,
            postalcode=user.postalcode
        )

        # Si l'utilisateur est un administrateur, renvoyez tous les champs
        if user.role == "admin":
            user_data.meta = user.meta
            user_data.token = user.token

        return user_data
    except JWSError:
        raise HTTPException(status_code=401, detail="Invalid token")



from fastapi import HTTPException

# ...

# Endpoint : /users/update
# Type : POST
# Permet de mettre à jour un utilisateur
@app.patch("/users/update/{user_id}", response_model=dict)
async def update_user(user_id: int, user_update: UserUpdate, authorization: str = Header(None)):
    try:
        # Vérifiez si le jeton JWT est fourni dans l'en-tête d'autorisation
        if not authorization:
            raise HTTPException(status_code=401, detail="Authorization token is missing")

        # Extrait le jeton JWT de l'en-tête d'autorisation
        jwt_token = authorization.split(' ')[-1]

        # Vérifiez le jeton JWT et récupérez les revendications
        jwt_data = jwt.decode(jwt_token, SECRET_KEY, algorithms=["HS256"])
        email = jwt_data.get("email")
        # Rechercher l'utilisateur en fonction de user_id
        user = SessionLocal().query(User).filter(User.id == user_id).first()

        if user is None:
            raise HTTPException(status_code=404, detail="User not found")

        # Si l'utilisateur n'est pas un administrateur et tente de modifier des champs interdits, renvoyer une erreur
        if user.role != "admin":
            raise HTTPException(status_code=403, detail="Only administrators can modify user fields")

        # Construction de la requête SQL pour mettre à jour les informations de l'utilisateur
        query = text("UPDATE users SET email = :email, birthdaydate = :birthdaydate, address = :address, postalcode = :postalcode WHERE id = :user_id RETURNING *")

        values = {
            "user_id": user_id,
            "email": user_update.email,
            "birthdaydate": user_update.birthdaydate,
            "address": user_update.address,
            "postalcode": user_update.postalcode,
        }

        # Exécution de la requête SQL pour mettre à jour les informations de l'utilisateur
        with engine.begin() as conn:
            result = conn.execute(query, values)
            updated_user = result.fetchone()

        if updated_user is None:
            raise HTTPException(status_code=404, detail="User not found")

        return {"message": "User updated"}

    except JWSError:
        raise HTTPException(status_code=401, detail="Invalid token")





# Endpoint : /users/password
# Type : PATCH
# Update the user's password
@app.patch("/users/password", response_model=UpdatePassword)
async def update_password(password_update: UpdatePassword, authorization: str = Header(None)):
    try:
        # Vérifiez si le jeton JWT est fourni dans l'en-tête d'autorisation
        if not authorization:
            raise HTTPException(status_code=401, detail="Authorization token is missing")

        # Extrait le jeton JWT de l'en-tête d'autorisation
        jwt_token = authorization.split(' ')[-1]

        # Vérifiez le jeton JWT et récupérez les revendications
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






#################################################
#                                               #
#                                               #
#              START DEPARTMENTS                #
#                                               #
#                                               #
#################################################


# Endpoint : /departments/create
# Type : POST
# This endpoint creates a new department
@app.post("/departments/create", response_model=DepartmentCreateResponse)
async def create_department(department: DepartmentCreate, authorization: str = Header(None)):
    try:

        existing_department = SessionLocal().query(Department).filter(Department.name == department.name).first()
        if existing_department:
            return DepartmentCreateResponse(message='Department already exists')

               # Vérifiez si le jeton JWT est fourni dans l'en-tête d'autorisation
        if not authorization:
            raise HTTPException(status_code=401, detail="Authorization token is missing")

        # Extrait le jeton JWT de l'en-tête d'autorisation
        jwt_token = authorization.split(' ')[-1]

        # Vérifiez le jeton JWT et récupérez les revendications
        jwt_data = jwt.decode(jwt_token, SECRET_KEY, algorithms=["HS256"])
        email = jwt_data.get("email")
        user = SessionLocal().query(User).filter(User.email == email).first()
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        if user.role != "admin":
            raise HTTPException(status_code=403, detail="Only administrators can perform this action")


        query = text(
            "INSERT INTO department (name) VALUES (:name) RETURNING *"
        )
        values = {
            "name": department.name
        }
        with engine.begin() as conn:
            result = conn.execute(query, values)
        return DepartmentCreateResponse(message='Department create !')

    except JWSError:
        raise HTTPException(status_code=401, detail="Invalid token")




    
# Endpoint: /departements/{id_departement}/users/add
# Type: POST
# Allows adding users to a department
@app.post("/departements/{id_departement}/users/add", response_model=List[int])
async def add_users_to_department(id_departement: int, users: List[int], authorization: str = Header(None)):
    try:
        # Create a session
        session = SessionLocal()

        # Vérifiez si le jeton JWT est fourni dans l'en-tête d'autorisation
        if not authorization:
            raise HTTPException(status_code=401, detail="Authorization token is missing")

        # Extrait le jeton JWT de l'en-tête d'autorisation
        jwt_token = authorization.split(' ')[-1]

        # Vérifiez le jeton JWT et récupérez les revendications
        jwt_data = jwt.decode(jwt_token, SECRET_KEY, algorithms=["HS256"])
        email = jwt_data.get("email")
        user = session.query(User).filter(User.email == email).first()

        # Verify if the user is an administrator
        if user.role != "admin":
            raise HTTPException(status_code=403, detail="Only administrators can add users to a department")

        department = session.query(Department).filter(Department.id == id_departement).first()
        if department is None:
            raise HTTPException(status_code=404, detail="Department not found")

        users_added = []

        for user_id in users:
            existing_user = session.query(User).filter(User.id == user_id).first()
            if existing_user is None:
                raise HTTPException(status_code=404, detail=f"User {user_id} not found")

            # Check if the user is already in the department
            if existing_user not in department.users:
                # Update the user's department_id field with the department's ID
                existing_user.department_id = id_departement
                users_added.append(user_id)

        session.commit()
        return users_added

    except JWSError:
        raise HTTPException(status_code=401, detail="Invalid token")


# Endpoint : /departements/{id_departement}/users/{user_id}
# Type : GET
# Récupération d'un utilisateur d'un département spécifique
@app.get("/departements/{id_departement}/users/{user_id}", response_model=UserResponse)
async def get_user_in_department(id_departement: int, user_id: int, authorization: str = Header(None)):
    try:
        # Créez une session pour interagir avec la base de données
        db = SessionLocal()

        # Vérifiez si le jeton JWT est fourni dans l'en-tête d'autorisation
        if not authorization:
            raise HTTPException(status_code=401, detail="Authorization token is missing")

        # Extrait le jeton JWT de l'en-tête d'autorisation
        jwt_token = authorization.split(' ')[-1]

        # Vérifiez le jeton JWT et récupérez les revendications
        jwt_data = jwt.decode(jwt_token, SECRET_KEY, algorithms=["HS256"])
        email = jwt_data.get("email")
        user = db.query(User).filter(User.email == email).first()

        # Vérifiez si le département existe
        department = db.query(Department).filter(Department.id == id_departement).first()
        if department is None:
            raise HTTPException(status_code=404, detail="Department not found")

        # Récupérez le rôle de l'utilisateur
        user_role = user.role if user else None

        # Construisez la requête SQL en fonction du rôle de l'utilisateur avec la jointure appropriée
        if user_role == "admin":
            # Si l'utilisateur est administrateur, récupérez tous les champs
            user = db.query(User).join(User.departments).filter(Department.id == id_departement, User.id == user_id).first()
        else:
            # Si l'utilisateur n'est pas administrateur, récupérez uniquement les champs nécessaires
            user = db.query(User.id, User.email, User.firstname, User.lastname, User.role, User.age, User.department_id).join(User.departments).filter(Department.id == id_departement, User.id == user_id).first()

        if user is None:
            raise HTTPException(status_code=404, detail="User not found in the department")

        return user

    except JWSError:
        raise HTTPException(status_code=401, detail="Invalid token")



# Endpoint : /departements/{id_departement}/users/remove
# Type : POST
# Permet de retirer des utilisateurs d'un département
@app.delete("/departements/{id_departement}/users/remove", response_model=List[int])
async def remove_users_from_department(id_departement: int, users: List[int], authorization: str = Header(None)):
    try:
        # Vérifiez si le jeton JWT est fourni dans l'en-tête d'autorisation
        if not authorization:
            raise HTTPException(status_code=401, detail="Authorization token is missing")

        # Extrait le jeton JWT de l'en-tête d'autorisation
        jwt_token = authorization.split(' ')[-1]

        # Vérifiez le jeton JWT et récupérez les revendications
        jwt_data = jwt.decode(jwt_token, SECRET_KEY, algorithms=["HS256"])
        email = jwt_data.get("email")

        # Récupérez l'utilisateur pour vérifier son rôle
        user = SessionLocal().query(User).filter(User.email == email).first()
        if user is None:
            raise HTTPException(status_code=404, detail="Utilisateur non trouvé")

        # Vérifiez si l'utilisateur est un administrateur
        if user.role != "admin":
            raise HTTPException(status_code=403, detail="Seuls les administrateurs peuvent retirer des utilisateurs d'un département")

       # Vérifiez l'existence du département
        department = SessionLocal().query(Department).filter(Department.id == id_departement).first()
        if department is None:
            raise HTTPException(status_code=404, detail="Department not found")

        # Vérifiez si l'utilisateur est dans le département
        user = SessionLocal().query(User).filter(User.id == user.id, User.department_id == id_departement).first()
        if user is None:
            raise HTTPException(status_code=404, detail="User not found in the department")

        # Retirez l'utilisateur du département en mettant à jour la base de données
        user.department_id = None
        SessionLocal().commit()

        # Renvoyez un entier (1) pour indiquer le succès
        return [1]

    except JWSError:
        raise HTTPException(status_code=401, detail="Invalid token")




















from fastapi import HTTPException

@app.delete("/users/{user_id}", response_model=UserCreate)
async def delete_user(user_id: int, authorization: str = Header(None)):
    try:
        # Vérifiez si le jeton JWT est fourni dans l'en-tête d'autorisation
        if not authorization:
            raise HTTPException(status_code=401, detail="Authorization token is missing")

        # Extrait le jeton JWT de l'en-tête d'autorisation
        jwt_token = authorization.split(' ')[-1]

        # Vérifiez le jeton JWT et récupérez les revendications
        jwt_data = jwt.decode(jwt_token, SECRET_KEY, algorithms=["HS256"])
        email = jwt_data.get("email")

        # Create a new session for this request
        db = SessionLocal()

        # Search for the user to delete based on user_id
        user = db.query(User).filter(User.id == user_id).first()

        if user is None:
            db.close()
            raise HTTPException(status_code=404, detail="User not found")

        # Delete the user from the database
        db.delete(user)
        db.commit()

        # Close the session
        db.close()

        return user

    except JWSError:
        raise HTTPException(status_code=401, detail="Invalid token")
