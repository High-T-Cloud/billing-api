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
    
    # function logic
    new_service = {'serial': None, 'description': None, 'value': None, 'currency': None, 'data_source': None}
    
    # create the new secrvice
    for key in new_service:
        if key in event and event[key] != '':
            new_service[key] = event[key]
    
    # --Cntr data source--
    if new_service['data_source'] == 'cntr':
        new_service['value'] = None
        new_service['currency'] = None  # Currency will be determined according to cntr data when creating invoice
    
    cursor.execute('INSERT INTO services (serial, description, value, currency, data_source) VALUES (%s,%s,%s,%s, %s)',
        (new_service['serial'], new_service['description'], new_service['value'], new_service['currency'], new_service['data_source']))
    conn.commit()
    conn.close()
    
    return {'message': 'service created'}
    
    