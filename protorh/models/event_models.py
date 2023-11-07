from pydantic import BaseModel, Json, NaiveDatetime
from typing import Dict


class EventCreate(BaseModel):
    Name: str
    Date: NaiveDatetime
    Description: str
    UserID: int
    DepartmentID: int


class EventGet(BaseModel):
    Name: str
    Date: NaiveDatetime
    Description: str
    UserID: int
    DepartmentID: int


class EventRemove(BaseModel):
    Name: str
    Date: NaiveDatetime
    Description: str
    UserID: int
    DepartmentID: int
