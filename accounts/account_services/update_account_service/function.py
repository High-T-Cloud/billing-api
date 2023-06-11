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
    
    # Fetch the service connection
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
        if int(service['margin']) > 100 or int(service['margin']) < 0:
            raise Exception('err-400: invalid margin value')
            
    # Save changes in DB
    new_service_params = (service['description'], service['value'], service['currency'], service['quantity'],service['discount'], service['margin'], service['payment_source'], service['payment_source_id'],service['id'])
    cursor.execute('UPDATE account_services SET description=%s, value=%s, currency=%s, quantity=%s, discount=%s, margin=%s, payment_source=%s, payment_source_id=%s WHERE id = %s', new_service_params)    
    conn.commit()
    conn.close()

    # Serialize datetime column for output
    service['last_update'] = service['last_update'].isoformat()
    
    return service
