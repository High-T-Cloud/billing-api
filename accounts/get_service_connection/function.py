from os import environ
import utils

def lambda_handler(event, context):
    print('--event: ', event)

    conn = utils.get_db_connection(environ['DB_ENDPOINT'], environ['DB_NAME'], environ['SECRET_ARN'])
    cursor = conn.cursor()

    # Permission level required: Viewer
    user_auth = int(utils.get_user_auth(cursor, event))
    print('--user auth: ', user_auth)
    if user_auth < 1:
        conn.close()
        raise Exception('err-401: user access denied')

    cursor.execute('SELECT service_connections.*, serial, data_source FROM service_connections LEFT JOIN services ON service_id = services.id WHERE service_connections.id = %s', event['service_id'])
    service = cursor.fetchone()

    conn.close()
    return service