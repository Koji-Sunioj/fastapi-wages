import boto3

ses_client = boto3.client('ses')

def ses_init(host:str):
    templates = ses_client.list_templates(
        MaxItems=10
    )
    template_strings = [template["Name"] for template in templates["TemplatesMetadata"]] if len(templates["TemplatesMetadata"]) > 0 else []
    if "FASTAPI_RESET_TOKEN" not in template_strings:
        link = '<p>please follow this <a href=http://%s>link</a> to reset your password.</p>' % (host)
        template = ses.create_template(
        Template = {
            'TemplateName' : 'FASTAPI_RESET_TOKEN',
            'SubjectPart'  : 'Reset your password',
            'TextPart'     : 'Hello you son of a bitch',
            'HtmlPart'     : link
        })

def send_email(email:str):
    ses_client.send_templated_email(
        Source='noreply@ironpond.net',
        Destination={
            'ToAddresses': [email],
            'CcAddresses': [],
        },
        ReplyToAddresses=['noreply@ironpond.net'],
        Template='FASTAPI_RESET_TOKEN',
        TemplateData="{}"
    )