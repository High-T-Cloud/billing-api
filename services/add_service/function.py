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
        
    
    # Crate the new service
    new_service = {'serial': None, 'description': None, 'amount': None, 'currency': None, 'data_source': None}

    for key in new_service:
        if key in event and event[key] != '':
            new_service[key] = event[key]
    
    # cntr data source
    if new_service['data_source'] == 'cntr':
        new_service['amount'] = None
        new_service['currency'] = None  # Currency will be determined according to cntr data when creating invoice
    
    # Insert to DB
    params_placeholder = ("%s, " * len(new_service))[:-2]
    param_names = ', '.join(new_service.keys())
    param_values = list(new_service.values())        
    statement = 'INSERT INTO services (' + param_names + ') VALUES (' + params_placeholder + ')'    
    cursor.execute(statement, param_values)
    conn.commit()
    conn.close()
    
    return {'message': 'service created'}
    
    