# users.py

from fastapi import FastAPI, HTTPException, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy.sql import text
from models.user_models import UserCreate, UserResponse
from models.department_models import DepartmentList, DepartmentBase
from main import get_db

app = FastAPI()

# Endpoint pour ajouter des utilisateurs à un département
@app.post("/departements/{id_departement}/users/add", response_model=DepartmentList)
async def add_users_to_department(id_departement: int, users: List[UserCreate], db: Session = Depends(get_db)):
    # Vérifier si le département existe
    department = db.execute(text("SELECT id FROM department WHERE id = :id_departement"), id_departement)
    if department is None:
        raise HTTPException(status_code=404, detail="Department not found")

    users_added = []
    for user in users:
        # Vérifier si l'utilisateur existe
        existing_user = db.execute(text("SELECT id FROM users WHERE id = :user_id"), user.id)
        if existing_user is None:
            raise HTTPException(status_code=404, detail="User not found")

        # Vérifier si l'utilisateur n'est pas déjà dans le département
        user_in_department = db.execute(text("SELECT user_id FROM department_users WHERE department_id = :id_departement AND user_id = :user_id"), id_departement, user.id)
        if user_in_department is None:
            db.execute(text("INSERT INTO department_users (department_id, user_id) VALUES (:id_departement, :user_id)"), id_departement, user.id)
            db.commit()
            users_added.append(user)

    return {"departments": users_added}

# Endpoint pour retirer des utilisateurs d'un département
@app.post("/departements/{id_departement}/users/remove", response_model=DepartmentList)
async def remove_users_from_department(id_departement: int, users: List[UserCreate], db: Session = Depends(get_db)):
    # Vérifier si le département existe
    department = db.execute(text("SELECT id FROM department WHERE id = :id_departement"), id_departement)
    if department is None:
        raise HTTPException(status_code=404, detail="Department not found")

    users_removed = []
    for user in users:
        # Vérifier si l'utilisateur existe
        existing_user = db.execute(text("SELECT id FROM users WHERE id = :user_id"), user.id)
        if existing_user is None:
            raise HTTPException(status_code=404, detail="User not found")

        # Vérifier si l'utilisateur est dans le département
        user_in_department = db.execute(text("SELECT user_id FROM department_users WHERE department_id = :id_departement AND user_id = :user_id"), id_departement, user.id)
        if user_in_department:
            db.execute(text("DELETE FROM department_users WHERE department_id = :id_departement AND user_id = :user_id"), id_departement, user.id)
            db.commit()
            users_removed.append(user)

    return {"departments": users_removed}

# Endpoint pour récupérer les utilisateurs d'un département
@app.get("/departements/{id_departement}/users", response_model=DepartmentList)
async def get_department_users(id_departement: int, current_user: UserResponse = Depends(get_current_user), db: Session = Depends(get_db)):
    # Vérifier si le département existe
    department = db.execute(text("SELECT id FROM department WHERE id = :id_departement"), id_departement)
    if department is None:
        raise HTTPException(status_code=404, detail="Department not found")

    user_data = DepartmentBase(name=department.name)
    
    if current_user.role == "admin":
        # Si l'utilisateur est un administrateur, récupérer tous les utilisateurs du département
        users = db.execute(text("SELECT users.id, users.email, users.firstname, users.lastname, users.role FROM users JOIN department_users ON users.id = department_users.user_id WHERE department_users.department_id = :id_departement"), id_departement)
        user_data.users = users
    else:
        # Si l'utilisateur n'est pas un administrateur, récupérer uniquement son propre utilisateur du département
        user = db.execute(text("SELECT users.id, users.email, users.firstname, users.lastname, users.role FROM users JOIN department_users ON users.id = department_users.user_id WHERE department_users.department_id = :id_departement AND users.id = :user_id"), id_departement, current_user.id)
        user_data.users = [user]

    return user_data
