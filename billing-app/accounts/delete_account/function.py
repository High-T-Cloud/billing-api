from os import environ
import utils

def lambda_handler(event, context):
    print('--Event: ', event)
    conn = utils.get_db_connection(environ['DB_ENDPOINT'], environ['DB_NAME'], environ['SECRET_ARN'])
    cursor = conn.cursor()
    
    # Permission required: Manager
    user_auth = utils.get_user_auth(cursor, event)
    if user_auth < 2:
        conn.close()
        raise Exception('err-401: user access denied')

    # Delete the account
    cursor.execute('DELETE FROM accounts WHERE id=%s', event['account_id'])
    conn.commit()
    conn.close()
    return {'message': 'account deleted'}