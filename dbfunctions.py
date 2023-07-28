import os
import psycopg2
import models
from pydantic import BaseModel
from dotenv import dotenv_values
from passlib.context import CryptContext
import utils

db_envs = utils.get_db_envs('wages_secrets')
print(db_envs)
conn=psycopg2.connect(database=db_envs["DB_NAME"],
                        host=db_envs["DB_HOST"],
                        user=db_envs["USER"],
                        password=db_envs["PWD"],
                        port=db_envs["PORT"]) 

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def select_one_user(email:str,retrieve_pwd=False):
    cursor = conn.cursor()
    parameter = "password,created" if retrieve_pwd else "created"
    command = "select email,%s from wages_users where email='%s'" % (parameter,email)
    cursor.execute(command)
    existing_user = utils.one_to_dict(cursor)
    return existing_user

def update_user_password(user:models.User):
    cursor = conn.cursor()
    command = "update wages_users set password ='%s' where email='%s'" % (pwd_context.hash(user.password),user.email)
    cursor.execute(command)
    conn.commit()

def insert_user(user:models.User):
    conn.autocommit = True
    cursor = conn.cursor()
    command = "insert into wages_users (email,password) values ('%s','%s')" % (user.email,pwd_context.hash(user.password))
    cursor.execute(command)
    conn.commit()
