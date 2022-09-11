import utils
import os

def lambda_handler(event, context):
    print('--event: ', event)
    conn = utils.get_db_connection(os.environ['DB_ENDPOINT'], os.environ['DB_NAME'], os.environ['SECRET_ARN'])
    cursor = conn.cursor()

    # Auth required: Master
    user_auth = utils.get_user_auth(cursor, event, organization_id=6, account_id=False)
    if user_auth < 3:
        raise Exception('err-401: access denied')
    
    fq = '%' + event['query'] + '%'
    cursor.execute('SELECT id, name FROM organizations WHERE name LIKE %s', fq)
    body = cursor.fetchall()

    return body