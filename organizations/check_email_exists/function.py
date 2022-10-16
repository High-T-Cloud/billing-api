from os import environ
import boto3
import utils

def lambda_handler(event, context):
    print('--Event: ', event)
    
    conn = utils.get_db_connection(environ['DB_ENDPOINT'], environ['DB_NAME'], environ['SECRET_ARN'])
    cursor = conn.cursor()

    # Permission required: Master
    user_auth = utils.get_user_auth(cursor, event, organization_id=6, account_id=False)
    if user_auth != 3:
        conn.close()
        raise Exception('err-401: user access denied')        

    email_exists = False    
    my_email = event['email']

    cursor.execute('SELECT email FROM organizations')
    all_emails = cursor.fetchall()
    print('--emails: ', all_emails)

    for item in all_emails:
        if item['email'] == my_email:
            email_exists = True

    
    return email_exists
    