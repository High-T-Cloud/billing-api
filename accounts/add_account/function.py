from os import environ
import utils


def lambda_handler(event, context):

    print('--Event: ', event)
    conn = utils.get_db_connection(
        environ['DB_ENDPOINT'], environ['DB_NAME'], environ['SECRET_ARN'])
    cursor = conn.cursor()

    # Auth requied: Master
    user_auth = utils.get_user_auth(cursor, event=event, account_id=False, organization_id=6)
    if user_auth != 3:
        conn.close()
        raise Exception('err-401: user access denied')

    # Validate provider exists
    cursor.execute('SELECT id FROM providers WHERE id=%s',
                   event['provider_id'])
    if not cursor.fetchone():
        conn.close()
        raise Exception('err-400: invalid provider id')

    print('--Finished validation--')

    # Create a new acocunt
    new_account = {
        'name': None,
        'account_number': None,
        'payer_account': None,
        'provider_id': None,
        'organization_id': event['organization_id'],                
    }

    # Merge event data
    for key in new_account:
        if key in event:
            new_account[key] = event[key]        

    # Set payer account's default to account number
    if new_account['payer_account'] == '':
        new_account['payer_account'] = new_account['account_number']
    
    print('--new acocunt: ', new_account)

    # Insert to DB
    param_names = ', '.join(new_account.keys())
    param_values = list(new_account.values())
    param_placeholders = ('%s, ' * len(new_account))[:-2]    
    cursor.execute(f'INSERT INTO accounts ({param_names}) VALUES ({param_placeholders})', param_values)
    conn.commit()
    conn.close()
    return {'message': 'account added'}
