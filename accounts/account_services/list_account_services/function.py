from os import environ
import utils

def lambda_handler(event, context):
    print('--event: ', event)

    conn = utils.get_db_connection(environ['DB_ENDPOINT'], environ['DB_NAME'], environ['SECRET_ARN'])
    cursor = conn.cursor()

    # Permission level required: viewer
    user_auth = int(utils.get_user_auth(cursor, event))
    print('--user auth: ', user_auth)
    if user_auth < 1:
        conn.close()
        raise Exception('err-401: user access denied')

    # if count mode count account services and return the count
    if event['count'] == True:
        cursor.execute('SELECT COUNT(id) AS count FROM account_services WHERE account_id = %s', event['account_id'])
        count = cursor.fetchone()
        count = count['count']
        return count

    cursor.execute('SELECT account_services.*, serial, data_source FROM account_services LEFT JOIN services ON service_id = services.id WHERE account_id = %s', event['account_id'])
    services = cursor.fetchall()   

    # Serialize datetime columns
    for service in services:
        service['last_update'] = service['last_update'].isoformat() 

    conn.close()
    return services