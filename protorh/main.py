from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import database_exists, create_database
from models.models import Base
import os
from dotenv import load_dotenv
from routers.users import user_router
from routers.departments import department_router
from routers.requestrh import requestrh_router
from routers.event import event_router




DATABASE_URL = "postgresql://lounes:lehacker147@localhost/proto"
engine = create_engine(DATABASE_URL)
if not database_exists(engine.url):
    create_database(engine.url, template="template0")



SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


Base.metadata.create_all(bind=engine)

env_file_path = os.path.join(os.path.dirname(__file__), 'protorh.env')

if os.path.exists(env_file_path):
    load_dotenv(dotenv_path=env_file_path)



salt = os.getenv('salt')
SECRET_KEY = os.getenv('SECRET_KEY')
DATABASE_HOST = os.getenv('DATABASE_HOST')
DATABASE_PORT = os.getenv('DATABASE_PORT')
DATABASE_NAME = os.getenv('DATABASE_NAME')
DATABASE_USER = os.getenv('DATABASE_USER')
DATABASE_PASSWORD = os.getenv('DATABASE_PASSWORD')



app = FastAPI()

app.include_router(user_router)

app.include_router(department_router)

app.include_router(requestrh_router)

app.include_router(event_router)
