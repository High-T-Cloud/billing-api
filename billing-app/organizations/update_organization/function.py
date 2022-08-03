import json
from os import environ
import utils

def lambda_handler(event, context):
    print('--Event: ', event)
    conn = utils.get_db_connection(environ['DB_ENDPOINT'], environ['DB_NAME'], environ['SECRET_ARN'])
    cursor = conn.cursor()

    # Required permission: Manager
    user_auth = utils.get_user_auth(cursor, event, organization_id = event['id'])
    if user_auth < 2:
        conn.close()
        raise Exception('err-401: user access denied')
    
    # --Function Logic--
    
    # try to find organization
    cursor.execute('SELECT * FROM organizations WHERE id=%s', event['id'])
    current_organization = cursor.fetchone()    
    print('--current organization: ', current_organization)
        
    # Merge current organization with request organization
    for key in current_organization:
        if key in event:
            current_organization[key] = event[key]
            
    # Format JSON values in organization
    if type(current_organization['emails']) == str:
        current_organization['emails'] = json.loads(current_organization['emails'])
    if type(current_organization['address']) == str:
        current_organization['address'] = json.loads(current_organization['address'])
    if type(current_organization['connected_users']) == str:
        current_organization['connected_users'] = json.loads(current_organization['connected_users'])
        
    print('--New organization: ', current_organization)
    
    # update organization in DB
    cursor.execute('UPDATE organizations SET name=%s, business_id=%s, phone=%s, emails=%s, address=%s, connected_users=%s WHERE id=%s', ( current_organization['name'], current_organization['business_id'], current_organization['phone'], json.dumps(current_organization['emails']), json.dumps(current_organization['address']), json.dumps(current_organization['connected_users']), event['id'] ))
    conn.commit()
    conn.close()
    
    return {
        'body': current_organization
    }
    
    
