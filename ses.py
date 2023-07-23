import boto3

ses_client = boto3.client('ses')

def send_email(email:str,token:str,website:str):
    template_string = '{\"token\":\"%s\",\"website\":\"%s\"}' % (token,website)
    print(template_string)
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