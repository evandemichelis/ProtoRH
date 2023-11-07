from fastapi import FastAPI, HTTPException, Header, APIRouter
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from jose import JWSError, jwt
from sqlalchemy_utils import database_exists, create_database
from typing import List
from models.department_models import DepartmentCreate, DepartmentCreateResponse
from models.models import Base, User, Department
from models.user_models import UserResponse
import os
from dotenv import load_dotenv
from config import salt, SECRET_KEY

DATABASE_URL = "postgresql://lounes:lehacker147@localhost/proto"
engine = create_engine(DATABASE_URL)
if not database_exists(engine.url):
    create_database(engine.url, template="template0")



SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


Base.metadata.create_all(bind=engine)





department_router = APIRouter()


# Endpoint : /departments/create
# Type : POST
# This endpoint creates a new department
@department_router.post("/departments/create", response_model=DepartmentCreateResponse)
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
@department_router.post("/departements/{id_departement}/users/add", response_model=List[int])
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
                users_added.department_routerend(user_id)

        session.commit()
        return users_added

    except JWSError:
        raise HTTPException(status_code=401, detail="Invalid token")


# Endpoint : /departements/{id_departement}/users/{user_id}
# Type : GET
# Récupération d'un utilisateur d'un département spécifique
@department_router.get("/departements/{id_departement}/users/{user_id}", response_model=UserResponse)
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

        # Construisez la requête SQL en fonction du rôle de l'utilisateur avec la jointure department_routerropriée
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
@department_router.delete("/departements/{id_departement}/users/remove", response_model=List[int])
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