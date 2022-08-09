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
    cursor.execute('SELECT * FROM services WHERE id = %s', event['service_id'])
    new_service = cursor.fetchone()
    print('--fetched service: ', new_service)
    if not new_service:
        conn.close()
        raise Exception('err-400: invalid service id')
    
    for key in new_service:        
        if key in event and event[key] is not None:
            new_service[key] = event[key]
    
    # update service
    cursor.execute('UPDATE services SET serial=%s, description=%s, value=%s, unit=%s WHERE id = %s', 
        (new_service['serial'], new_service['description'], new_service['value'], new_service['unit'], new_service['id']))
    
    conn.commit()
    conn.close()
    
    return {'message': 'service updated', 'body': new_service}