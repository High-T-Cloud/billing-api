import utils
from os import environ

def lambda_handler(event, context):
    print('--Event: ', event)
    
    conn = utils.get_db_connection(environ['DB_ENDPOINT'], environ['DB_NAME'], environ['SECRET_ARN'])
    cursor = conn.cursor()
    
    # Role required: Master
    user_role = utils.get_user_auth(cursor, event, account_id=False, organization_id=6)
    if int(user_role) != 3:
        conn.close()
        raise Exception('err-401: user access denied')
    
    # function logic
    cursor.execute('SELECT * FROM services')
    services = cursor.fetchall()
    
    return {
        'body': services
    }
        
