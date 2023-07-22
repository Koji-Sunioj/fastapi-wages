import models
import dbfunctions
from typing import Union
from jose import JWTError, jwt
from pydantic import BaseModel
from dotenv import dotenv_values
from fastapi import FastAPI,Header
from typing_extensions import Annotated
from passlib.context import CryptContext
from datetime import datetime, timedelta
from fastapi.responses import JSONResponse

app=FastAPI()
envs=dict(dotenv_values(".env"))
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@app.post("/users/")
async def create_user(user: models.User):
    try:
        dbfunctions.insert_user(user)
        return JSONResponse(status_code=200,content={"message": "successfully created user"})
    except Exception as error:
        print(error)
        return JSONResponse(status_code=409,content={"message": "user already exists"})    

@app.post("/sign-in/")
async def get_token(user: models.User):           
    existing_user = dbfunctions.select_one_user(user.username,retrieve_pwd=True)
    verified = pwd_context.verify(user.password, existing_user["password"])
    if verified:
        now = datetime.utcnow()
        expires = now + timedelta(minutes=180)
        jwt_payload = {"sub":existing_user["username"],"iat":now,"exp":expires}
        token = jwt.encode(jwt_payload,envs["SECRET"])
        return {"token":token}
    else:
        return JSONResponse(status_code=403,content={"message": "invalid credentials"})

    
@app.get("/users/{username}")
async def get_user(username:str,authorization: Annotated[Union[str, None], Header()] = None):
    try:
        decodable = jwt.decode(authorization.split()[1],key=envs["SECRET"])
        if decodable["sub"] == username:
            existing_user = dbfunctions.select_one_user(username)
            return {"user": existing_user}
        else: 
            raise Exception({"message":"user not found","code":404})
    except Exception as error:
        parsed_error = error.args[0]
        error = {"code":403,"message":"invalid credentials"} if isinstance(parsed_error, str) else parsed_error
        return JSONResponse(status_code=error["code"],content={"message": error["message"]})

@app.get("/check-session")
async def check_token(token:str):
    try:
        decodable = jwt.decode(token,key=envs["SECRET"])
        is_expired = datetime.utcnow() > datetime.utcfromtimestamp(decodable["exp"])
        if is_expired:
            raise Exception("expired token")
        return {"message":"valid token"}
    except Exception as error:
        return JSONResponse(status_code=403,content={"message": "invalid credentials"})

@app.patch("/users/{username}/reset-password")
async def reset_password(user:models.User,username:str,authorization: Annotated[Union[str, None], Header()] = None):
    try:
        decodable = jwt.decode(authorization.split()[1],key=envs["SECRET"])
        existing_user = dbfunctions.select_one_user(username,retrieve_pwd=True)
        valid_request = [value == decodable["sub"] for value in [existing_user["username"],user.username]] 
        if all(valid_request):
            dbfunctions.update_user_password(user)
            return {"message":"successfully updated password"}
        else:
            raise Exception("user mismatch")
    except Exception as error:
        print(error)
        return JSONResponse(status_code=403,content={"message": "invalid credentials"})
    

