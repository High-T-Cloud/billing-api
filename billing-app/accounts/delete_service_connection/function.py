from os import environ
import utils

def lambda_handler(event, context):
    print('--event: ', event)

    conn = utils.get_db_connection(environ['DB_ENDPOINT'], environ['DB_NAME'], environ['SECRET_ARN'])
    cursor = conn.cursor()

    # Permission level required: Manager
    user_auth = int(utils.get_user_auth(cursor, event))
    print('--user auth: ', user_auth)
    if user_auth < 2:
        conn.close()
        raise Exception('err-401: user access denied')    

    # Validate service connection
    cursor.execute('SELECT id FROM service_connections WHERE id = %s', event['service_id'])
    service_id = cursor.fetchone()
    if not service_id:
        conn.close()
        raise Exception('err-400: invalid service connection id')
    print('--validated sid--')
    
    # Delete service connection
    cursor.execute('DELETE FROM service_connections WHERE id = %s', event['service_id'])
    conn.commit()
    conn.close()

    return {'message': 'service connection deleted'}

