import json
from os import environ
import utils

def lambda_handler(event, context):
    print('--event: ', event)
    conn = utils.get_db_connection(environ['DB_ENDPOINT'], environ['DB_NAME'], environ['SECRET_ARN'])
    cursor = conn.cursor()

    # Required permission: Master
    user_auth = utils.get_user_auth(cursor, event, organization_id=6, account_id=False)
    if user_auth != 3:
        conn.close()
        raise Exception('err-401: user access denied')

    cursor.execute('SELECT * FROM organizations')
    query = cursor.fetchall()  
    conn.close()        
        
    return query
