from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from passlib.context import CryptContext
from dotenv import load_dotenv
import os
import psycopg2

load_dotenv() 
app = FastAPI()
conn = psycopg2.connect(database="wages",
                        host="localhost",
                        user="my_user",
                        password="root",
                        port="5432")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class User(BaseModel):
    username: str
    password: str
    
@app.get("/users/{user_id}")
async def get_user(user_id:int):
   
    try:
        cursor = conn.cursor()
        command = "select user_id,username from wages_users where user_id = %s" %(user_id) 
        cursor.execute(command)
        values = list(cursor.fetchone())
        columns = [column[0] for column in cursor.description]
        user = {column:value for column,value in zip(columns,values)}
        cursor.close()
        conn.close()
        return {"user": user}
    except:
        return JSONResponse(status_code=404,content={"message": "user not found"})

@app.post("/users/")
async def create_user(user: User):
    try:
        cursor = conn.cursor()
        command = "insert into wages_users (username,password) values ('%s','%s')" % (user.username,pwd_context.hash(user.password))
        cursor.execute(command)
        conn.commit()
        return user
    except:
        return JSONResponse(status_code=409,content={"message": "user already exists"})