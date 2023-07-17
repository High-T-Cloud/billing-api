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
            
    # Get account
    cursor.execute('SELECT * FROM accounts WHERE id=%s', event['account_id'])
    new_account = cursor.fetchone()
    print('--old account: ', new_account)

    if not new_account:
        raise Exception('err-404: could not find account')

    # Reorder to fit sql statement    
    new_account = {
        'name': new_account['name'],
        'account_number': new_account['account_number'],
        'payer_account': new_account['payer_account'],
        'provider_id': new_account['provider_id']
    }
    
    # merge account with event data
    for key in new_account:
        if key in event and event[key] != '':
            new_account[key] = event[key]
    print('--new account: ', new_account)

    # Update in DB
    param_names = ('=%s, '.join(new_account.keys())) + '=%s'
    param_values = list(new_account.values())
    param_values.append(event['account_id'])

    cursor.execute('UPDATE accounts SET ' + param_names + ' WHERE id = %s', param_values)
    conn.commit()
    conn.close()
    

    return {'message': 'account updated'}
    