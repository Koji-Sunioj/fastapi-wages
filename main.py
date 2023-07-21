from fastapi import FastAPI
from datetime import datetime, timedelta
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from passlib.context import CryptContext
from dotenv import dotenv_values
from jose import JWTError, jwt
import os
import psycopg2


app=FastAPI()
envs=dict(dotenv_values(".env"))
conn= psycopg2.connect(database=envs["DB_NAME"],
                        host=envs["HOST"],
                        user=envs["USER"],
                        password=envs["PWD"],
                        port=envs["PORT"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class User(BaseModel):
    username: str
    password: str

def one_to_dict(cursor):
    values = list(cursor.fetchone())
    columns = [column[0] for column in cursor.description]
    pointers = {column:value for column,value in zip(columns,values)}
    return pointers

@app.post("/sign-in/")
async def get_token(user: User):           
    cursor = conn.cursor()
    command = "select username,password from wages_users where username='%s'" % (user.username)
    cursor.execute(command)
    existing_user = one_to_dict(cursor)
    verified = pwd_context.verify(user.password, existing_user["password"])
    if verified:
        now = datetime.utcnow()
        expires = now + timedelta(minutes=60)
        jwt_payload = {"sub":existing_user["username"],"iat":now,"exp":expires}
        token = jwt.encode(jwt_payload,envs["SECRET"])
        return {"token":token}
    else:
        return JSONResponse(status_code=403,content={"message": "invalid credentials"})

    
@app.get("/users/{user_id}")
async def get_user(user_id:int):
    try:
        cursor = conn.cursor()
        command = "select user_id,username from wages_users where user_id=%s;" %(user_id) 
        cursor.execute(command)
        user = one_to_dict(cursor)
        return {"user": user}
    except Exception as error:
        print(error)
        return JSONResponse(status_code=404,content={"message": "user not found"})

@app.post("/users/")
async def create_user(user: User):
    try:
        cursor = conn.cursor()
        command = "insert into wages_users (username,password) values ('%s','%s')" % (user.username,pwd_context.hash(user.password))
        cursor.execute(command)
        conn.commit()
        return JSONResponse(status_code=200,content={"message": "successfully created user"})
    except Exception as error:
        print(error)
        return JSONResponse(status_code=409,content={"message": "user already exists"})