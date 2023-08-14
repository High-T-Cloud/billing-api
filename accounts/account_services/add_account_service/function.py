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

    # Validate payment source
    if 'payment_source' in event and event['payment_source'] != '':
        if event['payment_source'] not in PAYMENT_SOURCE_OPTIONS:
            conn.close()
            raise Exception('err-400: invalid payment source')

    # Create a new account service
    service_schema = {
        'service_id': None,
        'account_id': None,
        'description': None,
        'amount': None,
        'currency': None,
        'percent_from': None,
        'percent_amount': None,
        'quantity': None,
        'discount': None,
        'margin': None,
        'hidden': None,
        'payment_source': None,
        'payment_source_id': None,
    }
    new_service = {}
    for key in event:
        if key in service_schema and key in event and event[key] != '':
            new_service[key] = event[key] 
  
    print('--new account service: ', new_service)

    # Validate percent from
    if 'percent_from' in new_service:
        print('--percent based--')
        cursor.execute('SELECT currency, percent_from FROM account_services WHERE id = %s', new_service['percent_from'])
        currency = cursor.fetchone()
        print('--currency found: ', currency)
        if not currency:
            conn.close()
            raise Exception('err-400: Could not find percent based data')            
        if currency['percent_from'] is not None:
            conn.close()
            raise Exception('err-400: Cannot use percent based services')
        new_service['currency'] = currency['currency']


    # Insert to DB
    statement, vals, _, _ = utils.get_insert_statement(new_service, 'account_services')

    cursor.execute(statement, vals)
    conn.commit()
        
    return {
        'message': 'account service added'
    }