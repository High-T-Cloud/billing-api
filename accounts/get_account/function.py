from os import environ
import utils

def lambda_handler(event, context):
    print('--Event: ', event)
    
    conn = utils.get_db_connection(environ['DB_ENDPOINT'], environ['DB_NAME'], environ['SECRET_ARN'])
    cursor = conn.cursor()
    
    # Permission Required: Viewer
    user_auth = utils.get_user_auth(cursor, event)
    if user_auth < 1:
        conn.close()
        raise Exception('err-401: user access denied')
    
    # check if need to add provider info of not
    provider_info = False
    if 'provider_info' in event and event['provider_info']:
            print('--find check--')
            if event['provider_info'] == 'true' or type(event['provider_info']) == bool:
                provider_info = True
                print('--Adding provider info--')
    
    if not provider_info:
        statement = 'SELECT * FROM accounts WHERE id = %s'
    else:
        statement = 'SELECT accounts.*, providers.name AS provider_name, providers.image_path FROM accounts LEFT JOIN providers ON accounts.provider_id = providers.id WHERE accounts.id = %s'
    params = (event['account_id'])
    
    cursor.execute(statement, params)
    account = cursor.fetchone()
    
    if not account:
        conn.close()
        raise Exception('err-400: inalid account id')

    conn.close()
    return account
    