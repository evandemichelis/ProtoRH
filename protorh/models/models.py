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
    profile_picture = Column(String) 
    department_id = Column(Integer, ForeignKey('department.id'))
    departments = relationship("Department", secondary="user_department", back_populates="users")

# Modèle Department
class Department(Base):
    __tablename__ = "department"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    users = relationship("User", secondary="user_department", back_populates="departments")


class UserDepartment(Base):
    __tablename__ = "user_department"

    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    department_id = Column(Integer, ForeignKey('department.id'), primary_key=True)



# Modèle RequestRH
class RequestRH(Base):
    __tablename__ = "requestrh"

    id = Column(Integer, primary_key=True, index=True)
    UserID = Column(Integer, ForeignKey("users.id"))
    content = Column(String)
    RegistrationDate = Column(DateTime)
    Visibility = Column(Boolean)
    Close = Column(Boolean)
    LastAction = Column(DateTime)
    delete_date = Column(DateTime)
    ContentHistory = Column(JSON)


# Modèle Event
class Event(Base):
    __tablename__ = "event"

    id = Column(Integer, primary_key=True, index=True)
    Name = Column(String)
    Date = Column(DateTime)
    Description = Column(String)
    UserID = Column(Integer)
    DepartmentsID = Column(Integer)
