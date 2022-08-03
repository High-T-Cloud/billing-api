import utils
import boto3
from os import environ
from jwt import decode as jwt_decode

def lambda_handler(event, context):
    print('--Event: ', event)
    conn = utils.get_db_connection(environ['DB_ENDPOINT'], environ['DB_NAME'], environ['SECRET_ARN'])
    cursor = conn.cursor()
    
    # Special case: get self details

    # Auth required: Manager
    
    # Get organization id from user's organization
    formatted_sub = '%' + event['user_sub'] + '%'
    cursor.execute('SELECT id FROM organizations WHERE connected_users LIKE %s', formatted_sub)
    user_org_id = cursor.fetchone()
    if not user_org_id:
        conn.close()
        print('--user not found in any organization--')
        raise Exception('err-400: invalid user sub')
    user_org_id = user_org_id['id']
    user_auth = utils.get_user_auth(cursor, event, organization_id=user_org_id, account_id=False)
    if user_auth < 2:
        raise Exception('err-401: user access denied')
    

    # Get all users in the organization's group and filter to find the right sub    
    group_name = 'org-' + user_org_id
    
    cognito = boto3.client('cognito-idp')
    res = cognito.list_users_in_group(UserPoolId = environ['USER_POOL_ID'], GroupName=group_name)
    
    group_users = res['Users']
    print('--Group users: ', group_users)
    
    # Special case - get user sub from jwt token
    if event['user_sub'] == 'USER':
        token_str = event['Authorization'].split('Bearer ')[1]
        token = jwt_decode(token_str, options={'verify_signature': False})
        event['user_sub'] = token['sub']
    
    # search for user sub in group
    my_user = None
    
    for user in group_users:
        if user['Attributes'][0]['Value'] == event['user_sub']:
            print('--Found user sub--')
            my_user = {
                'username': user['Username'],
                'sub': user['Attributes'][0]['Value'],
                'email': user['Attributes'][2]['Value'],
                'enabled': user['Enabled'],
            }
    
    if my_user is None:
        raise Exception('err-400: invalid user sub')
    
    return {'body': my_user}