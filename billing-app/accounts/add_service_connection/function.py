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

    # Create a new service connection
    new_service = {'service_id': None, 'id': None, 'description': None, 'value': None, 'unit': None}
    for key in new_service:
        if key in event:
            new_service[key] = event[key]
    print('--new service connection: ', new_service.keys())

    cursor.execute('INSERT INTO service_connections (service_id, account_id, description, value, unit) VALUES (%s,%s,%s,%s,%s)', tuple(new_service.values()))
    conn.commit()
    conn.close()

    return {
        'message': 'service connection added'
    }