import os
import psycopg2
import models
from pydantic import BaseModel
from dotenv import dotenv_values
from passlib.context import CryptContext
import utils

print(os.environ)
db_envs = utils.get_ssm_envs(os.environ.get("DB_SECRET"))
""" envs=dict(dotenv_values(".env"))  """
conn=psycopg2.connect(database=db_envs["dbname"],
                        host=db_envs["host"],
                        user=db_envs["username"],
                        password=db_envs["password"],
                        port=db_envs["port"]) 

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
    cursor = conn.cursor()
    command = "insert into wages_users (email,password) values ('%s','%s')" % (user.email,pwd_context.hash(user.password))
    cursor.execute(command)
    conn.commit()

def init_tables():
    conn.set_session(autocommit=True)
    cursor = conn.cursor()
    check_command = "SELECT EXISTS (SELECT FROM pg_tables WHERE tablename  = 'wages_users')"
    cursor.execute(check_command)
    table_exists = cursor.fetchone()[0]
    if not table_exists: 
        seq_command = "CREATE sequence if not exists wages_users_user_id_sequence"
        cursor.execute(seq_command)
        table_command ="create table if not exists wages_users(\
            user_id integer not null default nextval('wages_users_user_id_sequence') primary key,\
            email varchar unique not null,\
            password varchar not null,\
            created TIMESTAMP DEFAULT NOW())"
        cursor.execute(table_command)
        alter_seq_command = "ALTER SEQUENCE wages_users_user_id_sequence RESTART WITH 101"
        cursor.execute(alter_seq_command)
    conn.commit()

