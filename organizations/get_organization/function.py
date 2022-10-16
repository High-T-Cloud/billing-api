from os import environ
import utils
import json
    
def lambda_handler(event, context):
    
    print('--Event: ', event)
    conn = utils.get_db_connection(environ['DB_ENDPOINT'], environ['DB_NAME'], environ['SECRET_ARN'])
    cursor = conn.cursor()

    # Special Case - get user's organization
    if event['organization_id'] == 'USER':            
        fsub = '%' + event['user_sub'] + '%'

        cursor.execute('SELECT * FROM organizations WHERE connected_users LIKE %s', fsub)        
    else:  # Get organization by id
        # Required permission: Viewer
        user_auth = utils.get_user_auth(cursor, event, account_id=False) 
        print('--auth: ', user_auth)   
        if user_auth < 1:
            conn.close()
            raise Exception('err-401: user access denied')            
        cursor.execute('SELECT * FROM organizations WHERE id = %s', event['organization_id'])        
        
    organization = cursor.fetchone()
    conn.close()
    if not organization:
        raise Exception('err-400: invalid organization id')        

    return organization