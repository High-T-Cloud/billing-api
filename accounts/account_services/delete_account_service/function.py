from os import environ
import utils

def lambda_handler(event, context):
    print('--event: ', event)

    conn = utils.get_db_connection(environ['DB_ENDPOINT'], environ['DB_NAME'], environ['SECRET_ARN'])
    cursor = conn.cursor()

    # Permission level required: Master
    user_auth = int(utils.get_user_auth(cursor, event, account_id=False, organization_id=6))
    print('--user auth: ', user_auth)
    if user_auth !=3:
        conn.close()
        raise Exception('err-401: user access denied')    

    # Validate account service exists
    cursor.execute('SELECT id FROM account_services WHERE id = %s', event['service_id'])
    service_id = cursor.fetchone()
    if not service_id:
        conn.close()
        raise Exception('err-400: invalid account service id')
    print('--validated sid--')
    
    # Delete account service
    cursor.execute('DELETE FROM account_services WHERE id = %s', event['service_id'])
    conn.commit()
    conn.close()

    return {'message': 'account service deleted'}

