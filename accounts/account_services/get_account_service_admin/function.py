from os import environ
import utils

def lambda_handler(event, context):
    print('--event: ', event)

    conn = utils.get_db_connection(environ['DB_ENDPOINT'], environ['DB_NAME'], environ['SECRET_ARN'])
    cursor = conn.cursor()

    # Permission level required: Master
    user_auth = int(utils.get_user_auth(cursor, event, account_id=False, organization_id=6))
    print('--user auth: ', user_auth)
    if user_auth != 3:
        conn.close()
        raise Exception('err-401: user access denied')

    cursor.execute('SELECT account_services.*, serial, data_source FROM account_services LEFT JOIN services ON service_id = services.id WHERE account_services.id = %s', event['service_id'])
    service = cursor.fetchone()

    conn.close()
    return service