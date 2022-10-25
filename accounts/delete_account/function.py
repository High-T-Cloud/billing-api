from os import environ
import utils

def lambda_handler(event, context):
    print('--Event: ', event)
    conn = utils.get_db_connection(environ['DB_ENDPOINT'], environ['DB_NAME'], environ['SECRET_ARN'])
    cursor = conn.cursor()
    
    # Permission required: Master
    user_auth = int(utils.get_user_auth(cursor, event, account_id=False, organization_id=6))
    print('--user auth: ', user_auth)
    if user_auth !=3:
        conn.close()
        raise Exception('err-401: user access denied')
    

    # Delete the account
    cursor.execute('DELETE FROM accounts WHERE id=%s', event['account_id'])
    print('--deleted account from db--')
    # Cascading - delete related account services
    cursor.execute('DELETE FROM service_connections WHERE account_id = %s', event['account_id'])
    print('--deleted account services--')
    conn.commit()
    conn.close()
    
    return {'message': 'account deleted'}