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
        raise Exception('err-401: user access denied')

    # check organization access to account
    cursor.execute('SELECT owner_id FROM accounts WHERE ID = %s', str(event['id']))
    account_owner = cursor.fetchone()
    if not account_owner:
        raise Exception('err-400: invalid account id')
    account_owner = account_owner['owner_id']
    if str(account_owner) != str(event['organization_id']):
        raise Exception('err-401a: user access to account denied')

    # Validate service connection
    cursor.execute('SELECT id FROM service_connections WHERE id = %s', event['sid'])
    service_id = cursor.fetchone()
    if not service_id:
        raise Exception('err-400a: invalid service connection id')
    print('--validated sid--')
    
    # Delete service connection
    cursor.execute('DELETE FROM service_connections WHERE id = %s', event['sid'])
    conn.commit()
    conn.close()

    return {'message': 'service connection deleted'}

