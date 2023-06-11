import utils
import json
import requests
import os

def lambda_handler(event, context):    
    print('--event: ', event)

    cntr_headers = None
    conn = utils.get_db_connection(os.environ['DB_ENDPOINT'], os.environ['DB_NAME'], os.environ['SECRET_ARN'])
    cursor = conn.cursor()

    # Permission level required: Master
    user_auth = int(utils.get_user_auth(cursor, event, account_id=False, organization_id=6))
    print('--user auth: ', user_auth)
    if user_auth !=3:
        conn.close()
        raise Exception('err-401: user access denied')   

    # Get all service connections For Each account owned by this organizations
    statement = 'SELECT accounts.name, account_number, services.serial, account_services.* FROM accounts '
    statement += 'LEFT JOIN account_services ON account_id = accounts.id LEFT JOIN services ON service_id = services.id '
    statement += 'WHERE account_services.id IS NOT NULL AND payment_source = %s AND owner_id = %s'

    cursor.execute(statement, ('manual' ,event['organization_id']))
    services = cursor.fetchall()

    print('--services found: ', services)
               

    # Add organization details
    cursor.execute('SELECT morning_id, email FROM organizations WHERE id = %s', event['organization_id'])
    org_details = cursor.fetchone()    
    print('--organization data: ', org_details)

    conn.close()

    # --MORNING PART--    

    # Format sql service data to match morning api
    income = []
    for s in services:        
        item = {
            'catalogNum': s['serial'],
            'description': s['description'],
            'price': float(s['value']),
            'currency': s['currency'],
            'quantity': s['quantity']
        }        
        income.append(item)
    print('--income: ', income)       
    
    req_body = {
        'description': event['description'],
        'type': 300,
        'lang': event['language'],
        'currency': event['currency'],
        'vatType': 0,        
        'client': {'id': org_details['morning_id'], 'emails': [org_details['email']]},
        'income': income
    }
    print('--request body: ', req_body)

    req_body = json.dumps(req_body)    

    # Make morning api call
    token = utils.get_morning_token(os.environ['MORNING_SECRET_ARN'])
    url = 'https://sandbox.d.greeninvoice.co.il/api/v1/documents'
    headers = {'Authorization': 'Bearer ' + token}
    res = requests.post(url, headers=headers, data=req_body)
    print('--morning response status code: ', res.status_code)
    res = res.json()
    
 
    return res

