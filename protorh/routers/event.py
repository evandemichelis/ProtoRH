import subprocess, uvicorn
from psycopg2 import Date
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, Depends, status, UploadFile, File, APIRouter
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import database_exists, create_database
from models.models import Base, Event
from models.event_models import EventCreate, EventGet, EventRemove
import os
from dotenv import load_dotenv

event_router = APIRouter()

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

# Endpoint : /event
# Type : CREATE
# This endpoint add event
@app.post("/event/add", response_model=EventCreate)
async def create_event(event: EventCreate):
    query = text("INSERT INTO event (Name, Date, Description, UserID, DepartmentID) VALUES (:Name, :Date, :Description, :UserID, :DepartmentID) RETURNING *")
    values = {
        "Name": event.Name,
        "Date": event.Date,
        "Description": event.Description,
        "UserID": event.UserID,
        "DepartmentID": event.DepartmentID
    }
    with engine.begin() as conn:
        result = conn.execute(query, values)
        return result.fetchone()

# # Endpoint : /event
# # Type : UPDATE
# # This endpoint update event
# @app.get("/event", response_model=EventGet)
# async def get_event(event: EventGet):
#     event = SessionLocal().query(Event).filter(Event.id == event_id).first()
#     if event is None:
#         raise HTTPException(status_code=404, detail="Event not found")
#     return event


# Endpoint : /event
# Type : DELETE
# This endpoint remove event
@app.get("/event/remove",response_model=EventRemove)
async def delete_event(event:EventRemove):
    query = text("DELETE FROM event WHERE id = :event_id RETURNING *")
    values = {"event_id": event}
    with engine.begin() as conn:
        result = conn.execute(query, **values)
        deleted_event = result.fetchone()
        if not deleted_event:
            raise HTTPException(status_code=404, detail="Item not found")
        return deleted_event
