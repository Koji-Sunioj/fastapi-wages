import models
import dbfunctions
import utils
import uvicorn
from typing import Union
from jose import jwt
from dotenv import dotenv_values
from fastapi import FastAPI,Header
from typing_extensions import Annotated
from passlib.context import CryptContext
from datetime import datetime, timedelta
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
import fastapi.exceptions

origins = ["http://localhost:3000"]
app=FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


frontend_envs=utils.get_db_envs("wages_frontend")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    errors = vars(exc)["_errors"]
    message = "missing %s" %  (", ".join([item["loc"][1] for item in errors]))
    return JSONResponse({"detail":message}, status_code=422)
 

@app.post("/users/")
async def create_user(user: models.User):
    try:
        dbfunctions.insert_user(user)
        return JSONResponse(status_code=200,content={"detail": "successfully created user. please sign in with your new password."})
    except Exception as error:
        return JSONResponse(status_code=400,content={"detail": "user already exists"})    

@app.post("/sign-in/")
async def get_token(user: models.User):
    try:           
        existing_user = dbfunctions.select_one_user(user.email,retrieve_pwd=True)
        verified = pwd_context.verify(user.password, existing_user["password"])
        if verified:
            now = datetime.utcnow()
            expires = now + timedelta(minutes=180)
            jwt_payload = {"sub":existing_user["email"],"iat":now,"exp":expires,"created":str(existing_user["created"])}
            token = jwt.encode(jwt_payload,frontend_envs["SECRET"])
            jwt_payload.update({"token":token})
            return jwt_payload
        else:
            return JSONResponse(status_code=403,content={"detail": "invalid credentials"})
    except Exception as error:
        return JSONResponse(status_code=400,content={"detail": "invalid credentials"})
    
@app.get("/users/{email}")
async def get_user(email:str,authorization: Annotated[Union[str, None], Header()] = None):
    try:
        decodable = jwt.decode(authorization.split()[1],key=frontend_envs["SECRET"])
        if decodable["sub"] == email:
            existing_user = dbfunctions.select_one_user(email)
            return {"user": existing_user}
        else: 
            raise Exception({"detail":"user not found","code":404})
    except Exception as error:
        parsed_error = error.args[0]
        error = {"code":403,"detail":"invalid credentials"} if isinstance(parsed_error, str) else parsed_error
        return JSONResponse(status_code=error["code"],content={"detail": error["message"]})

@app.get("/check-session")
async def check_token(token:str):
    try:
        jwt_payload = jwt.decode(token,key=frontend_envs["SECRET"])
        is_expired = datetime.utcnow() > datetime.utcfromtimestamp(jwt_payload["exp"])
        if is_expired:
            raise Exception("expired token") 
        jwt_payload.update({"token":token})    
        return jwt_payload
    except Exception as error:
        print(error)
        return JSONResponse(status_code=403,content={"detail": "invalid credentials"})

@app.patch("/users/{email}/reset-password")
async def reset_password(user:models.User,email:str,authorization: Annotated[Union[str, None], Header()] = None):
    try:
        decodable = jwt.decode(authorization.split()[1],key=frontend_envs["SECRET"])
        existing_user = dbfunctions.select_one_user(email,retrieve_pwd=True)
        valid_request = [value == decodable["sub"] for value in [existing_user["email"],user.email]] 
        if all(valid_request):
            dbfunctions.update_user_password(user)
            return {"detail":"successfully updated password"}
        else:
            raise Exception("user mismatch")
    except Exception as error:
        print(error)
        return JSONResponse(status_code=403,content={"detail": "invalid credentials"})
    

@app.post("/users/{email}/forgot-password")
async def forgot_password(email:str):
    try:
        now = datetime.utcnow()
        expires = now + timedelta(minutes=180)
        jwt_payload = {"task":"reset-password","iat":now,"exp":expires,"sub":email}
        token = jwt.encode(jwt_payload,frontend_envs["SECRET"])
        utils.send_email(email,token,frontend_envs["FE_HOST"])
        return {"detail":"password reset link sent"}
    except Exception as error:
        print(error)
        return JSONResponse(status_code=403,content={"detail": "invalid credentials"})
