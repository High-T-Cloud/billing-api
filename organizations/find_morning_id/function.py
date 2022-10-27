import requests
from os import environ
import utils

def lambda_handler(event, context):
    print('--event: ', event)
    conn = utils.get_db_connection(environ['DB_ENDPOINT'], environ['DB_NAME'], environ['SECRET_ARN'])
    cursor = conn.cursor()

    # Required permission: Master
    user_auth = utils.get_user_auth(cursor, event, organization_id=6, account_id=False)
    if user_auth != 3:
        conn.close()
        raise Exception('err-401: user access denied')

    token = utils.get_morning_token(environ['MORNING_SECRET_ARN'])
    url = 'https://sandbox.d.greeninvoice.co.il/api/v1/clients/search'
    headers = {'Authorization': 'Bearer ' + token}
    req_body = {
        'page': 1,
        'pageSize': 10,
        'name': event['query']
    }
    if event['active'] is True or event['active'] == 'true':
        req_body['active'] = True
        
    res = requests.post(url, headers=headers, data=req_body)    
    print('--morning res status code: ', res.status_code)
    res = res.json()
    print('--morning res: ', res)
        
    # Format the response
    clients = []
    for client in res['items']:                
        clients.append({'id': client['id'], 'name': client['name'], 'active': client['active']})
    
    return clients
        

    
    
    
    