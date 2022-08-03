from os import environ
import utils

def lambda_handler(event, context):
    print('--Event: ', event)
    
    conn = utils.get_db_connection(environ['DB_ENDPOINT'], environ['DB_NAME'], environ['SECRET_ARN'])
    cursor = conn.cursor()

    # Permission required: Master
    user_auth = utils.get_user_auth(cursor, event, organization_id=6)
    if user_auth != 3:
        conn.close()
        raise Exception('err-401: user access denied')        
    
    # build empty organization
    new_organization = {'name': None, 'business_id': None, 'phone': None, 'emails': None, 'address': None}

    # merge empty organization with event organization
    for key in new_organization:
        if key in event:
            new_organization[key] = event[key]
            
            
    print('--New Organization: ', new_organization)    

    cursor.execute('INSERT INTO organizations (name, business_id, phone, emails, address) VALUES (%s, %s, %s, %s, %s)', tuple(new_organization.values()))
    conn.commit()
    conn.close()
    
    return {'message': 'organization added'}