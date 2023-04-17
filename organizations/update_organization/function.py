import json
from os import environ
import utils

def lambda_handler(event, context):
    print('--Event: ', event)
    conn = utils.get_db_connection(environ['DB_ENDPOINT'], environ['DB_NAME'], environ['SECRET_ARN'])
    cursor = conn.cursor()

    # Required permission: Master
    user_auth = utils.get_user_auth(cursor, event, account_id=False, organization_id=6)
    if user_auth < 3:
        conn.close()
        raise Exception('err-401: user access denied')
    
    # --Function Logic--
    
    # try to find organization
    cursor.execute('SELECT * FROM organizations WHERE id=%s', event['organization_id'])
    current_organization = cursor.fetchone()    
    print('--current organization: ', current_organization)
        
    # Merge current organization with request organization
    new_organization = {
        'business_id': current_organization['business_id'],
        'phone': current_organization['phone'],
        'email': current_organization['email'],
        'country': current_organization['country'],
        'city': current_organization['city'],
        'address_line': current_organization['address_line'],
        'morning_id': current_organization['morning_id'],
        'gapps_id': current_organization['gapps_id'],
        'id': current_organization['id']
    }
    for key in current_organization:
        if key in event:
            new_organization[key] = event[key]                    
        
    print('--New organization: ', new_organization)
    
    # update organization in DB
    cursor.execute('UPDATE organizations SET business_id=%s, phone=%s, email=%s, country=%s, city=%s, address_line=%s, morning_id=%s, gapps_id=%s WHERE id = %s', tuple(new_organization.values()))
    conn.commit()
    conn.close()
    
    return {'message': 'organization updated'}
    
    
