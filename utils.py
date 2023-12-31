import os
import boto3
import json

def send_email(email:str,token:str,website:str):
    ses_client = boto3.client('ses',region_name='eu-north-1')
    template_string = '{\"token\":\"%s\",\"website\":\"%s\"}' % (token,website)
    ses_client.send_templated_email(
        Source='noreply@ironpond.net',
        Destination={
            'ToAddresses': [email],
            'CcAddresses': [],
        },
        ReplyToAddresses=['noreply@ironpond.net'],
        Template='FASTAPI_RESET_TOKEN',
        TemplateData='{"token":"%s","website":"%s","email":"%s"}' % (token,website,email)
        )

def one_to_dict(cursor):
    values = list(cursor.fetchone())
    columns = [column[0] for column in cursor.description]
    pointers = {column:value for column,value in zip(columns,values)}
    return pointers

def get_ssm_envs(secret_name):
    ssm_client = boto3.client('secretsmanager',region_name='eu-north-1')
    print(secret_name)
    try:
        response = ssm_client.get_secret_value(SecretId=secret_name)
        return  json.loads(response["SecretString"])
    except Exception as error:
        print(error)


