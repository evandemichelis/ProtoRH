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
    age: int = 0
    meta: Dict = {}
    token: str = ""  
    role: str = "" 

class UserConnect(BaseModel):
    email: str
    password: str

class UpdatePassword(BaseModel):
    email: str
    old_password: str
    new_password: str
    repeat_new_password: str

class UserResponse(BaseModel):
    email: str
    firstname: str
    lastname: str
    role: str
    address: str = ""
    postalcode: str = ""
