import boto3
import utils
from os import environ

def lambda_handler(event, context):
    print('--Event: ', event)
    conn = utils.get_db_connection(environ['DB_ENDPOINT'], environ['DB_NAME'], environ['SECRET_ARN'])
    cursor = conn.cursor()
    
    # Auth required: Manager
    user_auth = utils.get_user_auth(cursor, event, account_id=False)
    if user_auth < 2:
        conn.close()
        raise Exception('err-401: user access denied')
        
    group_name = 'org-' + str(event['organization_id'])
    
    cognito = boto3.client('cognito-idp')    
    res = cognito.list_users_in_group(GroupName=group_name, UserPoolId=environ['USER_POOL_ID'])
    group_users = res['Users']
    print('--Group users: ', group_users)

    users = []
    for user in group_users:
        new_user = {
            'username': user['Username'],
            'sub': user['Attributes'][0]['Value'],
            'email': user['Attributes'][2]['Value'],
            'enabled': user['Enabled'],
        }
        users.append(new_user)
    

    conn.close()
    return users
    