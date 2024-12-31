from dotenv import load_dotenv
load_dotenv()
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from db_models import admin, CompanyDetails

uri = os.getenv("db")

engine = create_engine(uri)

SessionLocal = sessionmaker(autocommit=False,autoflush=False,bind=engine)


def create_tables():
    Base.metadata.create_all(bind=engine)
    print("Tables created or already exist.")

Base = declarative_base()

if __name__ == "__main__":
    create_tables()