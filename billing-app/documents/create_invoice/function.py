import utils
import json
import requests
from os import environ

def lambda_handler(event, context):    
    print('--event: ', event)

    conn = utils.get_db_connection(environ['DB_ENDPOINT'], environ['DB_NAME'], environ['SECRET_ARN'])
    cursor = conn.cursor()

    # Auth required: ***TBD***

    # Get all service connections For Each account owned by this organizations
    statement = 'SELECT accounts.name, services.serial, service_connections.* FROM accounts '
    statement += 'LEFT JOIN service_connections ON account_id = accounts.id LEFT JOIN services ON service_id = services.id '
    statement += 'WHERE service_connections.id IS NOT NULL AND owner_id = %s'

    cursor.execute(statement, (event['organization_id']))
    services = cursor.fetchall()
    

    # TODO: ADD GETTING SERVICE DETAILS FROM CONNECTORS IF NEEDED**

    # Add organization details
    cursor.execute('SELECT morning_id, emails FROM organizations WHERE id = %s', event['organization_id'])
    org_details = cursor.fetchone()
    if org_details['emails']:
        org_details['emails'] = json.loads(org_details['emails'])
    print('--organization data: ', org_details)

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

    # Add Document to DB
    new_doc = {
        'due': event['due'],
        'owner': event['organization_id']
    }

    cursor.execute('INSERT INTO documents (due, owner) VALUES (%s, %s)', tuple(new_doc.values()))
    conn.commit()
    print('--added document to db--')
    conn.close()
 
    return {
        'body': res.json()
    }