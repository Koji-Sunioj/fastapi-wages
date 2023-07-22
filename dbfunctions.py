import os
import psycopg2
import models
from pydantic import BaseModel
from dotenv import dotenv_values
from passlib.context import CryptContext

envs=dict(dotenv_values(".env"))
conn= psycopg2.connect(database=envs["DB_NAME"],
                        host=envs["HOST"],
                        user=envs["USER"],
                        password=envs["PWD"],
                        port=envs["PORT"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def one_to_dict(cursor):
    values = list(cursor.fetchone())
    columns = [column[0] for column in cursor.description]
    pointers = {column:value for column,value in zip(columns,values)}
    return pointers

def select_one_user(username:str,retrieve_pwd=False):
    cursor = conn.cursor()
    parameter = "password" if retrieve_pwd else "created"
    command = "select username,%s from wages_users where username='%s'" % (parameter,username)
    cursor.execute(command)
    existing_user = one_to_dict(cursor)
    return existing_user

def update_user_password(user:models.User):
    cursor = conn.cursor()
    command = "update wages_users set password ='%s' where username='%s'" % (pwd_context.hash(user.password),user.username)
    cursor.execute(command)
    conn.commit()

def insert_user(user:models.User):
    cursor = conn.cursor()
    command = "insert into wages_users (username,password) values ('%s','%s')" % (user.username,pwd_context.hash(user.password))
    cursor.execute(command)
    conn.commit()
