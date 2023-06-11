import utils
import os
import pymysql

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
    cursor.execute('SELECT payer_account FROM accounts WHERE payer_account IS NOT NULL')
    payer_accounts = cursor.fetchall()

    # Format data
    payer_accounts = [item['payer_account'] for item in payer_accounts]

    return payer_accounts