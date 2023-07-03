import utils
import os

def lambda_handler(event, context):
    """
    get a list of organization's balaces grouped by currency by summing documents with organiztion's id
    """
    print('--event: ', event)
    conn = utils.get_db_connection(os.environ['DB_ENDPOINT'], os.environ['DB_NAME'], os.environ['SECRET_ARN'])
    cursor = conn.cursor()

    # Auth required: Master
    user_auth = utils.get_user_auth(cursor, event, organization_id=6, account_id=False)
    if user_auth < 3:
        conn.close()
        raise Exception('err-401: access denied')
    
    # Get balances list
    cursor.execute('SELECT currency, ROUND(SUM(value),2) AS value FROM documents WHERE organization_id=%s GROUP BY currency', event['id'])
    balance = cursor.fetchall()

    conn.close()
    return balance
    
