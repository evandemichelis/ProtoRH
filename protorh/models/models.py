from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# Modèle User
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    firstname = Column(String)
    lastname = Column(String)
    birthdaydate = Column(DateTime)
    address = Column(String)
    postalcode = Column(String)
    age = Column(Integer)
    meta = Column(JSON)
    registrationdate = Column(DateTime)
    token = Column(String)
    role = Column(String)

# Modèle Department
class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)

