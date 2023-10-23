from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# Modèle User
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    Email = Column(String, unique=True, index=True)
    Password = Column(String)
    Firstname = Column(String)
    Lastname = Column(String)
    BirthdayDate = Column(DateTime)
    Address = Column(String)
    PostalCode = Column(String)
    Age = Column(Integer)
    Meta = Column(JSON)
    RegistrationDate = Column(DateTime)
    Token = Column(String)
    Role = Column(String)

# Modèle Department
class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)

