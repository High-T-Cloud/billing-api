import utils
from os import environ

def lambda_handler(event, context):
    print('--event: ', event)
    
    conn = utils.get_db_connection(environ['DB_ENDPOINT'], environ['DB_NAME'], environ['SECRET_ARN'])
    cursor = conn.cursor()
    
    # Auth
    user_auth = int(utils.get_user_auth(cursor, event, account_id=False, organization_id=6))
    print('--user auth: ', user_auth)
    if user_auth != 3:
        conn.close()
        raise Exception('err-401: user access denied')
    
    
    # Validate service id
    cursor.execute('SELECT id FROM services WHERE id = %s', str(event['service_id']))
    service_id = cursor.fetchone()
    if not service_id:
        conn.close()
        raise Exception('err-400: invalid service id')
    service_id = service_id['id']

    # Cascade - Delete account services connected to this service
    cursor.execute('DELETE FROM account_services WHERE service_id = %s', event['service_id'])
    
    cursor.execute('DELETE FROM services WHERE id = %s', service_id)
    print('--Deleted service--')

    cursor.execute('DELETE FROM account_services WHERE service_id = %s', service_id)
    print('--deleted account services--')
    conn.commit()
    conn.close()
    
    return {'message': 'service deleted'}   