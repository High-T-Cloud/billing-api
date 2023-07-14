from os import environ
import utils
    
def lambda_handler(event, context):
    
    print('--Event: ', event)
    
    conn = utils.get_db_connection(environ['DB_ENDPOINT'], environ['DB_NAME'], environ['SECRET_ARN'])
    cursor = conn.cursor()
    
    # Required Auth: Master
    user_auth = int(utils.get_user_auth(cursor, event, account_id=False, organization_id=6))
    print('--user auth: ', user_auth)
    if user_auth !=3:
        conn.close()
        raise Exception('err-401: user access denied')
    
    # Validate provider exists
    if 'provider_id' in event and event['provider_id'] != '':
        cursor.execute('SELECT id FROM providers WHERE id=%s', event['provider_id'])
        if not cursor.fetchone():
            conn.close()
            raise Exception('err-400: invalid provider id')
            
    # Update Account
    cursor.execute('SELECT * FROM accounts WHERE id=%s', event['account_id'])
    account = cursor.fetchone()
    #Serialize datetime data
    account['last_update'] = account['last_update'].isoformat()
    
    # merge account with event data
    for key in account:
        if key in event and event[key] != '':
            account[key] = event[key]
    cursor.execute('UPDATE accounts SET name=%s, account_number=%s, provider_id=%s, payer_account=%s WHERE id=%s', (account['name'], account['account_number'], account['provider_id'], account['payer_account'], event['account_id']))
    
    conn.commit()
    conn.close()
    
    return account
    