from os import environ
import utils
import json
    
def lambda_handler(event, context):
    
    print('--Event: ', event)
    conn = utils.get_db_connection(environ['DB_ENDPOINT'], environ['DB_NAME'], environ['SECRET_ARN'])
    cursor = conn.cursor()
              
    # Required permission: Master
    user_auth = utils.get_user_auth(cursor, event, account_id=False, organization_id=6) 
    print('--auth: ', user_auth)   
    if user_auth != 3:
        conn.close()
        raise Exception('err-401: user access denied')            

    # Query organization        
    cursor.execute('SELECT * FROM organizations WHERE id = %s', event['organization_id'])        
    organization = cursor.fetchone()
    conn.close()
    if not organization:
        raise Exception('err-400: invalid organization id')        

    return organization