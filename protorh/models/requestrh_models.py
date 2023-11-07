from pydantic import BaseModel, Json
from typing import Dict


class RequestRHCreate(BaseModel):
    UserID: int
    content: str


class RequestRHUpdate(BaseModel):
    UserID: int
    Content: str
    Visibility: str
    Close: str
    LastAction: str
    ContentHistory: str


class RequestRHRemove(BaseModel):
    UserID: int
    Content: str
    Visibility: str
    Close: str
    LastAction: str
    ContentHistory: str


class RequestRHGet(BaseModel):
    UserID: int
    Content: str
    Visibility: str
    Close: str
    LastAction: str
    ContentHistory: str
