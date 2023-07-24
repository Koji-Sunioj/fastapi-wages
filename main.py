import boto3
import models
import dbfunctions
import ses
from typing import Union
from jose import JWTError, jwt
from pydantic import BaseModel
from dotenv import dotenv_values
from fastapi import FastAPI,Header
from typing_extensions import Annotated
from passlib.context import CryptContext
from datetime import datetime, timedelta
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

origins = ["http://localhost:3000"]
app=FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


envs=dict(dotenv_values(".env"))
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@app.post("/users/")
async def create_user(user: models.User):
    try:
        dbfunctions.insert_user(user)
        return JSONResponse(status_code=200,content={"message": "successfully created user. please sign in with your new password."})
    except Exception as error:
        print(error)
        return JSONResponse(status_code=409,content={"message": "user already exists"})    

@app.post("/sign-in/")
async def get_token(user: models.User):
    print(user)
    try:           
        existing_user = dbfunctions.select_one_user(user.email,retrieve_pwd=True)
        verified = pwd_context.verify(user.password, existing_user["password"])
        if verified:
            now = datetime.utcnow()
            expires = now + timedelta(minutes=180)
            jwt_payload = {"sub":existing_user["email"],"iat":now,"exp":expires,"created":str(existing_user["created"])}
            token = jwt.encode(jwt_payload,envs["SECRET"])
            jwt_payload.update({"token":token})
            return jwt_payload
        else:
            return JSONResponse(status_code=403,content={"message": "invalid credentials"})
    except Exception as error:
        print(error)
        return JSONResponse(status_code=400,content={"message": "invalid credentials"})
    
@app.get("/users/{email}")
async def get_user(email:str,authorization: Annotated[Union[str, None], Header()] = None):
    try:
        decodable = jwt.decode(authorization.split()[1],key=envs["SECRET"])
        if decodable["sub"] == email:
            existing_user = dbfunctions.select_one_user(email)
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
        jwt_payload = jwt.decode(token,key=envs["SECRET"])
        is_expired = datetime.utcnow() > datetime.utcfromtimestamp(decodable["exp"])
        if is_expired:
            raise Exception("expired token") 
        jwt_payload.update({"token":token})     
        return jwt_payload
    except Exception as error:
        return JSONResponse(status_code=403,content={"message": "invalid credentials"})

@app.patch("/users/{email}/reset-password")
async def reset_password(user:models.User,email:str,authorization: Annotated[Union[str, None], Header()] = None):
    try:
        print(authorization)
        decodable = jwt.decode(authorization.split()[1],key=envs["SECRET"])
        existing_user = dbfunctions.select_one_user(email,retrieve_pwd=True)
        valid_request = [value == decodable["sub"] for value in [existing_user["email"],user.email]] 
        if all(valid_request):
            dbfunctions.update_user_password(user)
            return {"message":"successfully updated password"}
        else:
            raise Exception("user mismatch")
    except Exception as error:
        print(error)
        return JSONResponse(status_code=403,content={"message": "invalid credentials"})
    

@app.post("/users/{email}/forgot-password")
async def forgot_password(email:str):
    try:
        now = datetime.utcnow()
        expires = now + timedelta(minutes=180)
        jwt_payload = {"task":"reset-password","iat":now,"exp":expires}
        token = jwt.encode(jwt_payload,envs["SECRET"])
        ses.send_email(email,token,envs["FE_HOST"])
        return {"message":"password reset link sent"}
    except Exception as error:
        print(error)
        return JSONResponse(status_code=403,content={"message": "invalid credentials"})
