from os import environ
import utils

def lambda_handler(event, context):
    print('--event: ', event)

    conn = utils.get_db_connection(environ['DB_ENDPOINT'], environ['DB_NAME'], environ['SECRET_ARN'])
    cursor = conn.cursor()

    # Auth required: Manager
    user_auth = utils.get_user_auth(cursor, event)
    if user_auth < 2:
        conn.close()
        raise Exception('err-401: user access denied')
    
    # Fetch the service connection
    cursor.execute('SELECT * FROM service_connections WHERE id = %s', event['service_id'])
    service = cursor.fetchone()
    if not service:
        conn.close()
        raise Exception('err-400: invalid service connection id')
    print('--old service: ', service)

    # Merge service with event data
    for key in service:
        if key in event and event[key] is not None:
            service[key] = event[key]
    print('--New service: ', service)
            
    params = (service['description'], service['value'], service['unit'], service['id'])
    cursor.execute('UPDATE service_connections SET description=%s, value=%s, unit=%s WHERE id = %s', params)
    
    conn.commit()
    conn.close()
    return {'body': service}
