import utils
from os import environ

def lambda_handler(event, context):
    print('--event: ', event)

    conn = utils.get_db_connection(environ['DB_ENDPOINT'], environ['DB_NAME'], environ['SECRET_ARN'])
    cursor = conn.cursor()
    
    # Role required: Master    
    user_role = utils.get_user_auth(cursor, event, account_id=False, organization_id=6)
    if int(user_role) != 3:
        conn.close()
        raise Exception('err-401: user access denied')
        
    
    # find the requested service
    cursor.execute('SELECT * FROM services WHERE id = %s', event['id'])
    new_service = cursor.fetchone()
    if not new_service:
        conn.close()
        raise Exception('err-400: invalid service id')
    
    # Reorder to fit sql statement
    new_service = {
        'serial': new_service['serial'],
        'description': new_service['description'],
        'amount': new_service['amount'],
        'currency': new_service['currency'],
        'data_source': new_service['data_source'],        
    }
    print('--old service: ', new_service)    
    
    # Merge with new data
    for key in new_service:        
        if key in event and event[key] != '':
            new_service[key] = event[key]
    
    # --Cntr data source--
    if new_service['data_source'] == 'cntr':
        new_service['amount'] = None
        new_service['currency'] = None  # Currency will be determined according to cntr data when creating invoice
    print('--updated service: ', new_service)
    
    # update in db
    param_names = ('=%s, '.join(new_service.keys())) + '=%s'
    param_values = list(new_service.values())
    param_values.append(event['id'])
    
    print(param_names)
    cursor.execute('UPDATE services SET ' + param_names + 'WHERE id = %s', param_values)
    
    conn.commit()
    conn.close()
    
    return new_service