from os import environ
import utils

def lambda_handler(event, context):
    # Consts
    PAYMENT_SOURCE_OPTIONS = ['manual', 'paypal']

    print('--event: ', event)

    conn = utils.get_db_connection(environ['DB_ENDPOINT'], environ['DB_NAME'], environ['SECRET_ARN'])
    cursor = conn.cursor()

    # Auth required: Master
    user_auth = int(utils.get_user_auth(cursor, event, account_id=False, organization_id=6))
    print('--user auth: ', user_auth)
    if user_auth !=3:
        conn.close()
        raise Exception('err-401: user access denied')
    
    # Fetch the account service
    cursor.execute('SELECT * FROM account_services WHERE id = %s', event['service_id'])
    service = cursor.fetchone()
    if not service:
        conn.close()
        raise Exception('err-400: invalid account service id')
    print('--old service: ', service)

    # Merge service with event data
    for key in service:
        if key in event and event[key] != '':
            service[key] = event[key]
    print('--New service: ', service)   

    # Validate given data    
    if service['payment_source']:
        if service['payment_source'] not in PAYMENT_SOURCE_OPTIONS:
            raise Exception('err-400: invalid payment source')
    if service['discount']:
        if int(service['discount']) > 100 or int(service['discount']) < 0:
            raise Exception('err-400: invalid discount value')
    if service['margin']:
        if int(service['margin']) < 0:
            raise Exception('err-400: invalid margin value')
    
    # Validate given percent_from id
    if service['percent_from'] is not None:
        print('--percent based--')
        cursor.execute('SELECT currency FROM account_services WHERE id = %s', service['percent_from'])
        currency = cursor.fetchone()
        if not currency:
            raise Exception('err-400: invalid percent from id')
        service['currency'] = currency['currency']

    # Remove non updating columns from data
    service.pop('id')
    service.pop('last_update')
            
    # Save changes in DB
    param_names = ('=%s, '.join(service.keys())) + '=%s'
    param_values = list(service.values())
    param_values.append(event['service_id'])
        
    cursor.execute('UPDATE account_services SET ' + param_names + ' WHERE id = %s', param_values)
    conn.commit()
    conn.close()
    
    return {'message': 'Service updated'}
