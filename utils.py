import boto3

def send_email(email:str,token:str,website:str):
    ses_client = boto3.client('ses')
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