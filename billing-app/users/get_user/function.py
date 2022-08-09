import utils
from os import environ
from boto3 import client

def lambda_handler(event, context):
    print('--Event: ', event)
    conn = utils.get_db_connection(environ['DB_ENDPOINT'], environ['DB_NAME'], environ['SECRET_ARN'])
    cursor = conn.cursor()

    user_sub = event['user_sub']
    # Special case: get user's self details
    if user_sub == 'USER':
        user_sub = event['cognito_user']
    else:
        # Auth required: Manager
        
        # Find the user's organization from db
        fsub = '%' + user_sub + '%'
        cursor.execute('SELECT id FROM organizations WHERE connected_users LIKE %s', fsub)
        user_org = cursor.fetchone()
        if not user_org:
            print('--user not found in db')
            conn.close()
            raise Exception('err-400: invalid user sub')
        user_org = user_org['id']
        # Check user's auth
        user_auth = utils.get_user_auth(cursor, event, organization_id=user_org, account_id=False)
        if user_auth < 2:
            conn.close()
            raise Exception('err-401: user access denied')
        
        # Fetch the user

        # Get all users in the organization's group and filter to find the right sub    
        group_name = 'org-' + str(user_org)
        
        cognito = client('cognito-idp')
        res = cognito.list_users_in_group(UserPoolId = environ['USER_POOL_ID'], GroupName=group_name)
        
        group_users = res['Users']
        print('--Group users: ', group_users)

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
            conn.close()
            raise Exception('err-400a: invalid user sub')
        
        conn.close()
        return {'body': my_user}

