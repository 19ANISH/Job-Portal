from functools import wraps
from typing import Annotated, Optional
from datetime import datetime, timedelta, date
import jwt

from fastapi import FastAPI, HTTPException, Depends, status
from sqlalchemy.orm import Session
from werkzeug.security import check_password_hash, generate_password_hash

import db_models
from database import SessionLocal, create_tables
from models.login_model import login_data, detailing, DataSetOut
import uvicorn
import os
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
load_dotenv()

from starlette.middleware.cors import CORSMiddleware


app = FastAPI()
create_tables()
SECRET_KEY = os.getenv("secret_key")  # Change this to a strong secret key
ALGORITHM = os.getenv("algorithm")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("access_token_expiry"))
origins = [
    "http://localhost:5173",  # your frontend's URL
    "https://job-portal-ui-qifg.onrender.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Can be set to ["*"] for all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods
    allow_headers=["*"],  # Allows all headers
)

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

# JWT utility functions
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=7)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None

def check_authentication(db: Session, creds: login_data):
    admin_creds = db.query(db_models.admin).filter(db_models.admin.username == creds.username).first()
    if admin_creds is None or not check_password_hash(admin_creds.password, creds.password):
        raise HTTPException(status_code=401, detail="Unauthorized")
    return admin_creds

def requires_authentication():
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            token = kwargs.get('token')
            if token is None or verify_token(token) is None:
                raise HTTPException(status_code=401, detail="Unauthorized")
            return await func(*args, **kwargs)
        return wrapper
    return decorator

#isactive or inactive function
def is_active(company: db_models.CompanyDetails) -> bool:
    # If deadline is None or it is in the future, it's still active
    if company.deadline is None or company.deadline >= date.today():
        return True
    return False

@app.post("/")
async def home(db: Session = Depends(get_db)):
    try:
        # Query all company details from the database
        company_details = db.query(db_models.CompanyDetails).all()

        # Filter active companies using the is_active function
        active_companies = [company for company in company_details if is_active(company)]

        # Convert the active result into a list of dictionaries (or any other serializable format)
        result = [{"id": company.id, "companyName": company.companyName, "designation": company.designation,"location": company.location,
                   "description": company.description, "image": company.image,"salary":company.salary,"deadline":company.deadline,"batch":company.batch,"applicationLink": company.applicationLink} for company in active_companies]

        return DataSetOut(statuscode=200,data=result,message=None,error=None)
    except Exception as e:
        raise HTTPException(status_code=500,detail=str(e))
@app.post("/add_admin")
@requires_authentication()
async def admin_addition(token: str,data: login_data, db: db_dependency):
    try:
        hashed_password = generate_password_hash(data.password)
        data.password = hashed_password
        db_admin = db_models.admin(**data.dict())
        db.add(db_admin)
        db.commit()
        return {status.HTTP_200_OK: f"{data.username} created"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# from sqlalchemy.orm import Session
# from sqlalchemy import update


@app.post("/auth")
async def login(creds: login_data, db: db_dependency):
    # Authenticate the user
    admin_creds = check_authentication(db, creds)

    if admin_creds:
        access_token = create_access_token(data={"sub": admin_creds.username})

        # Update the existing token and expiry in the database
        try:
            db.query(db_models.admin).filter(db_models.admin.username == admin_creds.username).update(
                {
                    db_models.admin.token: access_token,
                    db_models.admin.expiry: datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
                }
            )
            db.commit()
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

        return DataSetOut(statuscode=200, message="Login successful", data=access_token,error=None)

    raise HTTPException(status_code=403, detail="Wrong password")

@app.get('/{company_id}')
async def get_details(company_id : int, db: Session = Depends(get_db)):
    try:
        company_data = db.query(db_models.CompanyDetails).filter(db_models.CompanyDetails.id == company_id).first()
        if not company_data:
            raise HTTPException(status_code=404,detail="Company not found")
        data = {
                "companyName": company_data.companyName,
                "designation": company_data.designation,
                "description": company_data.description,
                "image": company_data.image,
                "created": company_data.created,
                "deadline": company_data.deadline,
                "applicationLink": company_data.applicationLink,
                "salary": company_data.salary,
                "batch": company_data.batch,
                "location": company_data.location

            }
        return DataSetOut(statuscode=200,data=data,message='Successfully fetched the job', error=None)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/update/{company_id}")
@requires_authentication()
async def update_details(company_id: int, token: str,company_data: detailing, db: Session = Depends(get_db)):
    try:
            # Get the company record by ID
            company = db.query(db_models.CompanyDetails).filter(db_models.CompanyDetails.id == company_id).first()
            # print("company")
            # print(company)
            if not company:
                raise HTTPException(status_code=404, detail="Company not found")

            # Update fields from company_data (no need to manually extract them)
            # deadline = required_detail.deadline or (date.today() + timedelta(days=10))
            company.companyName = company_data.companyName
            company.designation = company_data.designation
            company.description = company_data.description
            company.image = company_data.image
            company.created = company_data.created
            company.deadline = company_data.deadline or (date.today() + timedelta(days=10))
            company.applicationLink = company_data.applicationLink
            company.salary = company_data.salary or ("NA")
            company.batch = company_data.batch
            company.location = company_data.location

            # Commit the changes
            db.commit()

            data = {
                "companyName": company_data.companyName,
                "designation": company_data.designation,
                "description": company_data.description,
                "image": company_data.image,
                "created": company_data.created,
                "deadline": company.deadline,
                "applicationLink": company_data.applicationLink,
                "salary": company.salary,
                "batch": company_data.batch,
                "location": company_data.location

            }

            # Return the updated company details as response
            return DataSetOut(statuscode=200,data=data,message=None,error=None)

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
@app.post("/details")
@requires_authentication()
async def upload_details(required_detail: detailing, db: db_dependency,token: str):
    try:
        deadline = required_detail.deadline or (date.today() + timedelta(days=10))
        salary = required_detail.salary or ("NA")
        # Create the db model object
        required_detail.deadline = deadline
        db_details = db_models.CompanyDetails(**required_detail.dict())

        # Add to the database
        db.add(db_details)
        db.commit()

        # Prepare the response data
        data = {
            "companyName": required_detail.companyName,
            "designation": required_detail.designation,
            "description": required_detail.description,
            "image": required_detail.image,
            "created": date.today(),
            "deadline": deadline,
            "applicationLink": required_detail.applicationLink,
            "salary": salary,
            "batch": required_detail.batch,
            "location": required_detail.location
        }

        # Return the response with status code 200
        return DataSetOut(statuscode=200, data=data,message=None,error=None)

    except Exception as e:
        print(e)
        raise HTTPException(status_code=403, detail=str(e))
if __name__ == '__main__':
    # app.run(host='0.0.0.0', port=5000)
    uvicorn.run(app="main:app", host="0.0.0.0", port=int(os.getenv("PORT")), reload=True)
