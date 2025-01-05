from sqlalchemy import Column,Integer,String,TIMESTAMP, Text, DATE,func
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

class admin(Base):
    __tablename__ = 'admin_table'

    id = Column(Integer,primary_key=True)
    created =  Column(DATE, default=func.current_date())
    email = Column(String(150),unique=True)
    username = Column(String(100),unique=True)
    password = Column(String(500))
    token = Column(Text)
    expiry = Column(TIMESTAMP)

class CompanyDetails(Base):
    __tablename__ = 'details'

    id = Column(Integer, primary_key=True, autoincrement=True)
    location = Column(String(100), default="")
    companyName = Column(String(100))  # String with a max length of 100
    designation = Column(String(100))  # String with a max length of 100
    description = Column(Text)  # VARCHAR(255) for MySQL
    image = Column(String(255))  # String with a max length of 255 (for image URLs or file names)
    created =  Column(DATE, default=func.current_date())  # Defaults to current date
    deadline = Column(DATE)  # This can be NULL
    applicationLink = Column(String(150))  # String with a max length of 150
    salary = Column(String(20))  # String with a max length of 20
    batch = Column(String(25))  # String with a max length of 25


