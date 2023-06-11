from os import environ
import utils

def lambda_handler(event, context):
    print('--event: ', event)

    # CONSTS
    PAYMENT_SOURCE_OPTIONS = ['manual', 'paypal']

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

    # Create a new account service
    new_service = {'service_id': None, 'account_id': None, 'description': None, 'value': None, 'currency': None, 'quantity': None, 'discount': None, 'margin': None, 'payment_source': None, 'payment_source_id': None}
    for key in event:
        if key in new_service and event[key] != '':
            new_service[key] = event[key] 
  
    print('--new account service: ', new_service)
    
    # TODO: validate currency code

    # Validate given data    
    if new_service['payment_source']:
        if new_service['payment_source'] not in PAYMENT_SOURCE_OPTIONS:
            raise Exception('err-400: invalid payment source')
    if new_service['discount']:
        if int(new_service['discount']) > 100 or int(new_service['discount']) < 0:
            raise Exception('err-400: invalid discount value')
    if new_service['margin']:
        if int(new_service['margin']) > 100 or int(new_service['margin']) < 0:
            raise Exception('err-400: invalid margin value')
    
    print('--passed validation--')
    
    # Insert to DB
    cursor.execute('INSERT INTO account_services (service_id, account_id, description, value, currency, quantity, discount, margin, payment_source, payment_source_id) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)', tuple(new_service.values()))
    conn.commit()
    conn.close()

    return {
        'message': 'account service added'
    }