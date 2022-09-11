import utils
import json
import requests
from os import environ

def lambda_handler(event, context):    
    print('--event: ', event)

    # headers = utils.get_cntr_auth('arn:aws:secretsmanager:eu-west-1:754084371841:secret:cntr-credentials-sEq9AZ')
    # url = 'https://db96mdr7ui.execute-api.eu-west-1.amazonaws.com/dev1/do/get-balance?accountId=test_id'
    # r = requests.get(url, headers=headers)
    # print(r.status_code)
    # return r.json()

    conn = utils.get_db_connection(environ['DB_ENDPOINT'], environ['DB_NAME'], environ['SECRET_ARN'])
    cursor = conn.cursor()

    # Auth required: ***TBD***

    # Get all service connections For Each account owned by this organizations
    statement = 'SELECT accounts.name, services.serial, service_connections.* FROM accounts '
    statement += 'LEFT JOIN service_connections ON account_id = accounts.id LEFT JOIN services ON service_id = services.id '
    statement += 'WHERE service_connections.id IS NOT NULL AND owner_id = %s'

    cursor.execute(statement, (event['organization_id']))
    services = cursor.fetchall()
    

    # Get data from connector if needed


    # Add organization details
    cursor.execute('SELECT morning_id, emails FROM organizations WHERE id = %s', event['organization_id'])
    org_details = cursor.fetchone()
    if org_details['emails']:
        org_details['emails'] = json.loads(org_details['emails'])
    print('--organization data: ', org_details)

    conn.close()
    # --MORNING PART--    

    # Translate sql service data to match morning api
    income = []
    for s in services:        
        item = {
            'catalogNum': s['serial'],
            'description': s['description'],
            'price': float(s['value']),
            'currency': s['unit'],
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
        'client': {'id': org_details['morning_id'], 'emails': org_details['emails']},
        'income': income
    }
    print('--request body: ', req_body)

    req_body = json.dumps(req_body)    

    # Make morning api call
    token = utils.get_morning_token(environ['MORNING_SECRET_ARN'])
    url = 'https://sandbox.d.greeninvoice.co.il/api/v1/documents'
    headers = {'Authorization': 'Bearer ' + token}
    res = requests.post(url, headers=headers, data=req_body)

    
 
    return {
        'body': res.json()
    }

