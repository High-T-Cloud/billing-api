import utils
import os

def lambda_handler(event, context):
    print('--event: ', event)
    conn = utils.get_db_connection(os.environ['DB_ENDPOINT'], os.environ['DB_NAME'], os.environ['SECRET_ARN'])
    cursor = conn.cursor()

    # Required permission: Master
    user_auth = utils.get_user_auth(cursor, event, organization_id=6, account_id=False)
    if user_auth != 3:
        conn.close()
        raise Exception('err-401: user access denied')
    
    # Get data from DB
    # Id = 1 : AWS provider
    cursor.execute('SELECT name, payer_account AS number FROM accounts WHERE payer_account IS NOT NULL AND provider_id = 1')
    payer_accounts = cursor.fetchall()
    

    return payer_accounts