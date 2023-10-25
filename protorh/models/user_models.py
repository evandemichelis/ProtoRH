# user_models.py

from pydantic import BaseModel, Json, NaiveDatetime
from typing import Dict

class UserCreate(BaseModel):
    email: str
    password: str
    firstname: str
    lastname: str
    birthdaydate: NaiveDatetime
    address: str
    postalcode: str
    age: int = 0
    meta: Dict = {}
    token: str = ""  
    role: str = ""  


class UserUpdate(BaseModel):
    email: str
    firstname: str
    lastname: str
    birthdaydate: NaiveDatetime
    address: str
    postalcode: str
    age: int
    meta: Dict
    token: str
    role: str

class UserConnect(BaseModel):
    Email: str
    Password: str
