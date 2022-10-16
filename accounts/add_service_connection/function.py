from os import environ
import utils

def lambda_handler(event, context):
    print('--event: ', event)

    conn = utils.get_db_connection(environ['DB_ENDPOINT'], environ['DB_NAME'], environ['SECRET_ARN'])
    cursor = conn.cursor()

    # Permission level required: Master
    user_auth = int(utils.get_user_auth(cursor, event, account_id=False, organization_id=6))
    print('--user auth: ', user_auth)
    if user_auth !=3:
        conn.close()
        raise Exception('err-401: user access denied')    
    
    # Validate service id
    cursor.execute('SELECT id, data_source FROM services WHERE id = %s', event['service_id'])
    service = cursor.fetchone()
    if not service:
        conn.close()
        raise Exception('err-400: invalid service id')
    print('--validated service id--')

    # Create a new service connection
    new_service = {'service_id': None, 'account_id': None, 'description': None, 'value': None, 'unit': None, 'quantity': 1}    
    for key in event:
        if key in new_service and event[key] != '':
            new_service[key] = event[key] 
  
    # TODO: validate currency code (unit)
    # TODO: other data sources

    print('--new service connection: ', new_service.keys())

    

    cursor.execute('INSERT INTO service_connections (service_id, account_id, description, value, unit, quantity) VALUES (%s,%s,%s,%s,%s,%s)', tuple(new_service.values()))
    conn.commit()
    conn.close()

    return {
        'message': 'service connection added'
    }