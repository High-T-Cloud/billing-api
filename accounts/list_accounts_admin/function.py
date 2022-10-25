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
          
    statement = 'SELECT accounts.*, providers.name AS provider_name, providers.image_path, COUNT(account_id) AS services FROM accounts '
    statement += 'LEFT JOIN providers ON accounts.provider_id = providers.id LEFT JOIN service_connections ON account_id = accounts.id '
    statement += 'WHERE owner_id = %s GROUP BY accounts.id'
    
    cursor.execute(statement, event['organization_id'])
    accounts = cursor.fetchall()
    conn.close()
    return accounts
    