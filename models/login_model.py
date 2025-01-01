from pydantic import BaseModel
from typing import  Union
from datetime import date

class login_data(BaseModel):
    username: str
    email: Union[str,None]
    password: str

class detailing(BaseModel):
    location: Union[str,None]
    companyName: str
    designation: str
    description: str
    image: str
    created: Union[None,date]
    deadline: Union[None,date]
    applicationLink: str
    salary: Union[None,str]
    batch: Union[None,str]

class DataSetOut(BaseModel):
    statuscode: int
    data: Union[str,dict,list]
    error: Union[str,None]
    message: Union[str,None]