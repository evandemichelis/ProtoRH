# user_models.py

from pydantic import BaseModel, Json, NaiveDatetime
from typing import Dict

class UserCreate(BaseModel):
    Email: str
    Password: str
    Firstname: str
    Lastname: str
    BirthdayDate: NaiveDatetime
    Address: str
    PostalCode: str
    Age: int
    Meta: Dict
    RegistrationDate: NaiveDatetime
    Token: str
    Role: str

class UserUpdate(BaseModel):
    Email: str
    Firstname: str
    Lastname: str
    BirthdayDate: NaiveDatetime
    Address: str
    PostalCode: str
    Age: int
    Meta: Dict
    Token: str
    Role: str
