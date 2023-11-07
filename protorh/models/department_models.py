from pydantic import BaseModel
from typing import List

class DepartmentBase(BaseModel):
    name: str


class DepartmentCreate(DepartmentBase):
    pass

class Department(DepartmentBase):
    id: int

    
class DepartmentList(BaseModel):
    departments: List[Department]

class DepartmentCreateResponse(BaseModel):
    message: str