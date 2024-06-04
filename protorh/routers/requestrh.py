from datetime import datetime
from fastapi import FastAPI, HTTPException, Header, APIRouter
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from jose import JWSError, jwt
from sqlalchemy_utils import database_exists, create_database
import json
from models.models import Base, RequestRH, User
from models.requestrh_models import RequestRHCreate, RequestRHUpdate, RequestRHRemove
import os
from dotenv import load_dotenv
from config import salt, SECRET_KEY
import json
from datetime import datetime

from models.user_models import UserCreate



DATABASE_URL = "postgresql://lounes:lehacker147@localhost/proto"
engine = create_engine(DATABASE_URL)
if not database_exists(engine.url):
    create_database(engine.url, template="template0")



SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


Base.metadata.create_all(bind=engine)




requestrh_router = APIRouter()


def datetime_serialization(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError("Type not serializable")


def lastaction():
    return datetime.now()

# Endpoint : /requestrh
# Type : CREATE
# This endpoint adds an RH request
@requestrh_router.post("/rh/msg/add", response_model=RequestRHCreate)
async def create_rh_request(request_data: RequestRHCreate, authorization: str = Header(None)):
    try:
        # Verify if the JWT token is provided in the Authorization header
        if not authorization:
            raise HTTPException(status_code=401, detail="Authorization token is missing")

        # Extract the JWT token from the Authorization header
        jwt_token = authorization.split(' ')[-1]

        # Verify the JWT token and retrieve the claims
        jwt_data = jwt.decode(jwt_token, SECRET_KEY, algorithms=["HS256"])
        email = jwt_data.get("email")

        # Use an SQL query to search for the user based on the email in the JWT token
        query = text("SELECT id FROM users WHERE email = :email")
        result = SessionLocal().execute(query, {"email": email})
        user_id = result.scalar()
        Registrationdate = datetime.now()

        if user_id is None:
            raise HTTPException(status_code=404, detail="User not found")

        # Check if the provided user ID in the request exists
        user_exists_query = text("SELECT id FROM users WHERE id = :user_id")
        user_exists_result = SessionLocal().execute(user_exists_query, {"user_id": request_data.UserID})
        user_exists = user_exists_result.scalar()

        if user_exists is None:
            raise HTTPException(status_code=404, detail="User with the provided ID does not exist")

        # Create an initial content for the RH request
        content_history = [
            {
                "author": request_data.UserID,
                "content": request_data.content,
                "date": Registrationdate
            }
        ]

        # Create the RH request
        requestrh = RequestRH(
            UserID=request_data.UserID,
            content=json.dumps(content_history, default=datetime_serialization),
            RegistrationDate=Registrationdate,
            Visibility=True,
            Close=False,
            LastAction=Registrationdate
        )


        # Start a session and add the RH request
        session = SessionLocal()
        session.add(requestrh)
        session.commit()

        return request_data

    except JWSError:
        raise HTTPException(status_code=401, detail="Invalid token")



# Endpoint : /requestrh
# Type : DELETE
# This endpoint marks a RH request as non-visible and updates delete_date and last_action
@requestrh_router.post("/rh/msg/remove", response_model=RequestRHRemove)
async def remove_requestrh(request_data: RequestRHRemove, authorization: str = Header(None)):
    try:
        # Verify if the JWT token is provided in the Authorization header
        if not authorization:
            raise HTTPException(status_code=401, detail="Authorization token is missing")

        # Extract the JWT token from the Authorization header
        jwt_token = authorization.split(' ')[-1]

        # Verify the JWT token and retrieve the claims
        jwt_data = jwt.decode(jwt_token, SECRET_KEY, algorithms=["HS256"])
        email = jwt_data.get("email")

        # Use an SQL query to search for the user based on the email in the JWT token
        query = text("SELECT id FROM users WHERE email = :email")
        result = SessionLocal().execute(query, {"email": email})
        user_id = result.scalar()
        action_date = datetime.now()
        requestrh_id = request_data.requestrh_id

        if user_id is None:
            raise HTTPException(status_code=404, detail="User not found")

        # Update the RH request to mark it as non-visible and set delete_date and last_action
        query = text("UPDATE requestrh SET visibility = false, delete_date = :action_date, last_action = :action_date WHERE id = :requestrh_id RETURNING *")
        values = {"requestrh_id": requestrh_id, "action_date": action_date}

        with engine.begin() as conn:
            result = conn.execute(query, values)
            updated_requestrh = result.fetchone()

            if not updated_requestrh:
                raise HTTPException(status_code=404, detail="Item not found")

        return updated_requestrh

    except JWSError:
        raise HTTPException(status_code=401, detail="Invalid token")




# Endpoint : /requestrh
# Type : UPDATE
# This endpoint update requestrh
@requestrh_router.post("/rh/msg/update", response_model=RequestRHUpdate)
async def update_requestrh(requestrh: RequestRHUpdate):
    requestrh = SessionLocal().query(RequestRH).filter(RequestRH.id == requestrh_id).first()
    if requestrh is None:
        raise HTTPException(status_code=404, detail="User not found")

    for key, value in requestrh_update.dict().items():
        setattr(requestrh, key, value)

    SessionLocal().commit()

    return requestrh


# Endpoint : /requestrh
# Type : UPDATE
# This endpoint get the requests
@requestrh_router.get("/rh/msg", response_model=RequestRHUpdate)
async def read_requestrh(user_id: int):
    requestrh = SessionLocal().query(RequestRH).filter(RequestRH.id == requesth_id).first()
    if requestrh is None:
        raise HTTPException(status_code=404, detail="Request not found")
    return requestrh
