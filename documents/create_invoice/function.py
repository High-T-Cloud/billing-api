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
    statement = 'SELECT accounts.name, account_number, services.serial, services.data_source, account_services.* FROM accounts '
    statement += 'LEFT JOIN account_services ON account_id = accounts.id LEFT JOIN services ON service_id = services.id '
    statement += 'WHERE account_services.id IS NOT NULL AND owner_id = %s'

    cursor.execute(statement, (event['organization_id']))
    services = cursor.fetchall()
    
    # Add connector data to services - ** DEPRECATED AND MOVED TO DIFFERENT FUNCTION **
    # for service in services:
    #     if service['data_source'] == 'cntr':
    #         if cntr_headers is None:
    #             cntr_headers = utils.get_cntr_auth(os.environ['CNTR_SECRET_ARN'])
    #         # Get the cntr endpoint
    #         cursor.execute('SELECT cntr_endpoint FROM providers WHERE id = (SELECT provider_id FROM accounts WHERE id = %s)', service['account_id'])
    #         cntr_endpoint = cursor.fetchone()['cntr_endpoint']                        
    #         # Call the connector to get the data
    #         url = f'{os.environ["CNTR_API_URL"]}{cntr_endpoint}/invoices-last?account_id={service["account_number"]}&last=1'
    #         print('--cntr url: ', url)
    #         r = requests.get(url, headers=cntr_headers)
    #         print('--cntr res status: ', r.status_code)
    #         res = r.json()[0]
    #         service['value'] = res['amount']
    #         service['unit'] = res['currency']
    #         print('--service after cntr: ', service)
            

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

