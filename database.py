from dotenv import load_dotenv
load_dotenv()
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from db_models import admin, CompanyDetails

uri = os.getenv("db_dev")

engine = create_engine(uri)

SessionLocal = sessionmaker(autocommit=False,autoflush=False,bind=engine)


Base = declarative_base()

def create_tables():
    try:
        # Create specific tables
        Base.metadata.create_all(bind=engine, tables=[admin.__table__, CompanyDetails.__table__])
        print("Tables created or already exist.")

        Session = sessionmaker(bind=engine)
        session = Session()

        # Check if the admin table already has an entry
        existing_admin = session.query(admin).first()
        if not existing_admin:
            # Insert default admin if not already present
            default_admin = admin(
                username="admin",  # Default username
                password="scrypt:32768:8:1$mzEI0w2XKp2p611j$ab2d3d3173f03569915634d172389247b70f9f2520ab4cf7c8c187c6d3085fc9b71f5ad3c278d6c9a0d8b13759b85cf0dbf573a3a67021d38a21ec1f8008e20f",  # You should hash the password
            )

            session.add(default_admin)
            session.commit()
            print("Default admin user added.")

        # Close the session after the operation
        session.close()

    except Exception as e:
        print(e)
