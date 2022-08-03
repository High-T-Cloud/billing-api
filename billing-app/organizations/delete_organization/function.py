from os import environ
import utils

def lambda_handler(event, context):
    print('--event: ', event)
    conn = utils.get_db_connection(environ['DB_ENDPOINT'], environ['DB_NAME'], environ['SECRET_ARN'])
    cursor = conn.cursor()

    # Permission required: Master
    user_auth = utils.get_user_auth(cursor, event, organization_id=6)
    if user_auth != 3:
        conn.close()
        raise Exception('err-401: user access denied')  
        
    
    # try to find organization
    cursor.execute('SELECT * FROM organizations WHERE id=%s', event['id'])

    query = cursor.fetchone()
    print('--Query: ', query)
    
    if not query:
        conn.close()
        raise Exception('err-400: invalid organization id')
    
    # found organization
    cursor.execute('DELETE FROM organizations WHERE id=%s', event['id'])
    conn.commit()
    conn.close()
        
    return {'message': 'organization deleted'}
