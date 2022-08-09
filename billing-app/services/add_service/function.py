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
    new_service = {'serial': None, 'description': None, 'value': None, 'unit': None}
    
    # create the new secrive
    for key in new_service:
        if key in event and event[key] is not None:
            new_service[key] = event[key]
    
    cursor.execute('INSERT INTO services (serial, description, value, unit) VALUES (%s,%s,%s,%s)',
        (new_service['serial'], new_service['description'], new_service['value'], new_service['unit']))
    conn.commit()
    conn.close()
    
    return {'message': 'service created'}
    
    