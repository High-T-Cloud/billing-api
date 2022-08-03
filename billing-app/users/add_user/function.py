import json
import utils
from os import environ
import boto3
import pymysql
from pymysql.constants import CLIENT

def lambda_handler(event, context):
    conn = utils.get_db_connection(environ['DB_ENDPOINT'], environ['DB_NAME'], environ['SECRET_ARN'])
    cursor = conn.cursor()
    
    if not utils.check_user_auth(cursor):
        raise Exception('err-401: user access denied')
        
    # Signup the user with cognito
    cognito = boto3.client('cognito-idp')
    try:
        res = cognito.sign_up(ClientId=environ['APP_CLIENT_ID'], Username=event['username'], Password=event['password'], UserAttributes=[{'Name': 'email', 'Value': event['email']}])
    except Exception as e:
        print('--Signup Error : ', e)
        raise Exception('err-400: Signup Error')
        
    print('--Cognito Response: ', res)
    
    user_sub = res['UserSub']
    print('--user sub: ', user_sub)
    
    
    # Add user to organization's group
    organization_group = 'org-' + str(event['organization_id'])
    print('--Adding user to group', organization_group)
    
    res = cognito.admin_add_user_to_group(UserPoolId=environ['USER_POOL_ID'], Username=event['username'], GroupName=organization_group)
    print('--cognito add to group response: ', res)
    
    
    # Add user to organization table in DB
    permission = '2'  # **TEMP**
    
    cursor.execute('SELECT connected_users FROM organizations WHERE id = %s', str(event['organization_id']))
    connected_users = cursor.fetchone()['connected_users']
    connected_users = json.loads(connected_users)
    print('--connected users: ', connected_users)
    
    if user_sub not in connected_users:
        connected_users[user_sub] = permission
    
    users_json = json.dumps(connected_users)
    print('new users json: ', users_json)
    
    cursor.execute('UPDATE organizations SET connected_users = %s WHERE id = %s', (users_json, str(event['organization_id'])))
    conn.commit()
    
    # make return statement
    new_user = {
        'sub': user_sub,
        'username': event['username'],
        'email': event['email']
    }
    
    conn.close()
    
    return {'body': new_user}
    
    
    
