from os import environ
import utils
   
def lambda_handler(event, context):
    
    print('--Event: ', event)        
    conn = utils.get_db_connection(environ['DB_ENDPOINT'], environ['DB_NAME'], environ['SECRET_ARN'])
    cursor = conn.cursor()
    
    # Auth requied: Manager
    user_auth = utils.get_user_auth(cursor, event=event, account_id=False)
    if user_auth < 2:
        conn.close()
        raise Exception('err-401: user access denied') 
        
    # Validate provider exists
    cursor.execute('SELECT id FROM providers WHERE id=%s', event['provider_id'])
    if not cursor.fetchone():
        conn.close()
        raise Exception('err-400: invalid provider id')  

    print('--Finished validation--')   

    # Create a new acocunt
    new_account = {
        'name': None,
        'account_number': None,
        'provider_id': None,               
    } 
    # Merge new account with event data
    for key in new_account:
        if key in event and event[key] is not None:
            new_account[key] = event[key]
    new_account['owner_id'] = event['organization_id']
    print('--new acocunt: ', new_account)
    
    # Insert Account
    cursor.execute('INSERT INTO accounts (name, account_number, provider_id, owner_id) VALUES (%s,%s,%s,%s)', (new_account['name'], new_account['account_number'], new_account['provider_id'], new_account['owner_id']))
    conn.commit()
    conn.close()
    return {'message': 'account added'}