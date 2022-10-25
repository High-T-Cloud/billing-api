from os import environ
import utils

def lambda_handler(event, context):
    print('--Event: ', event)  
    
    conn = utils.get_db_connection(db_endpoint=environ['DB_ENDPOINT'], db_name=environ['DB_NAME'], secret_arn=environ['SECRET_ARN'])
    cursor = conn.cursor()
    
    # Permission required: Master
    user_auth = utils.get_user_auth(cursor, event, account_id=False, organization_id=6)
    if user_auth != 3:
        conn.close()
        raise Exception('err-401: user access denied')
    
    # Get organization details
    cursor.execute('SELECT name FROM organizations WHERE id = %s', event['id'])
    org_name = cursor.fetchone()
    if not org_name:
        conn.close()
        raise Exception('err-400: invalid organization id')        
    org_name = org_name['name']
    print('--org name: ', org_name)
    # Create the description based on event
    status = 'inactive'
    if event['status'] is True or event['status'] == 'true':
        status = 'active'        
    description = 'Updated status to ' + status
    print('--log description: ', description)

    # Update org status
    cursor.execute('UPDATE organizations SET status = %s WHERE id = %s', (status, event['id']))
    print('--Updated org status--')

    # Create log
    cursor.execute('INSERT INTO logs (object_id, object_name, description) VALUES (%s, %s, %s)', (event['id'], org_name, description))
    print('--created log--')
    conn.commit()
    conn.close()

    return {'message': 'Status updated'}
    

