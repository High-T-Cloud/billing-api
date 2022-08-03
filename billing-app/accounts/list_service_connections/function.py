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
        raise Exception('err-401: user access denied')
    
    # check organization access to account
    cursor.execute('SELECT owner_id FROM accounts WHERE ID = %s', str(event['id']))
    account_owner = cursor.fetchone()
    if not account_owner:
        raise Exception('err-400: invalid account id')
    account_owner = account_owner['owner_id']
    if str(account_owner) != str(event['organization_id']):
        raise Exception('err-401a: user access to account denied')

    cursor.execute('SELECT * FROM service_connections WHERE account_id = %s', str(event['id']))
    services = cursor.fetchall()
    if not services:
        raise Exception('err-400: invalid account id')      

    return {'body': services}