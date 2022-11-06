from os import environ
import utils

def lambda_handler(event, context):
    print('--Event: ', event)  
    
    conn = utils.get_db_connection(db_endpoint=environ['DB_ENDPOINT'], db_name=environ['DB_NAME'], secret_arn=environ['SECRET_ARN'])
    cursor = conn.cursor()
    
    # Permission required: Viewer
    user_auth = utils.get_user_auth(cursor, event, account_id=False)
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
        statement = 'SELECT * FROM accounts WHERE owner_id = %s'
    else:
        statement = 'SELECT accounts.*, providers.name AS provider_name, providers.image_path FROM accounts LEFT JOIN providers ON accounts.provider_id = providers.id WHERE owner_id = %s'
    params = (event['organization_id'])
        
    cursor.execute(statement, params)
    accounts = cursor.fetchall()
    
    conn.close()
    return accounts
    