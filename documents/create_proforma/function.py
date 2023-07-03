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

    # Create the statement for all account ids
    acc_statement = 'accounts.id = %s' 
    acc_statement += ' OR accounts.id = %s' * (len(event['accounts']) - 1)


    # Get all account services For Each account owned by this organizations
    statement = 'SELECT accounts.name, account_number, services.serial, account_services.* FROM accounts '
    statement += 'LEFT JOIN account_services ON account_id = accounts.id LEFT JOIN services ON service_id = services.id '
    statement += 'WHERE account_services.id IS NOT NULL AND payment_source = %s AND '
    statement += acc_statement

    statement_params = ['manual'] + event['accounts']    

    print('--SQL statement: ', statement)
    print('--SQL statement params: ', statement_params)    

    cursor.execute(statement, statement_params)
    services = cursor.fetchall()        

    print('--services found: ', services)
               

    # Add organization details
    cursor.execute('SELECT morning_id, email FROM organizations WHERE id = %s', event['organization_id'])
    org_details = cursor.fetchone()    
    print('--organization data: ', org_details)

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
    print('--Calling morning API to create a new document--')    
    token = utils.get_morning_token(os.environ['MORNING_SECRET_ARN'])
    url = 'https://sandbox.d.greeninvoice.co.il/api/v1/documents'
    headers = {'Authorization': 'Bearer ' + token}
    res = requests.post(url, headers=headers, data=req_body)
    print('--morning response status code: ', res.status_code)
    if res.status_code < 200 or res.status_code > 299:
        print('morning response: ', res)
        conn.close()
        raise Exception('--err-500: invalid respone from morning api')
    
    res = res.json()

    # --Add document Data to DB--
    
    # Get the proforma actuall data from morning
    print('--Calling morning API to get document data')
    url = url + '/' + res['id']
    res = requests.get(url, headers=headers)
    print('--morning response code: ', res.status_code)
    if res.status_code < 200 or res.status_code > 299:
        print('--morning response: ', res)
        conn.close()
        # TODO: pay attention - severe error!
        raise Exception('--err-500: Error getting document data AFTER creating document, document not created in DB')

    res = res.json()

    # Create document object
    # TODO: add due date
    new_doc = {
        'organization_id': event['organization_id'],
        'type': 'proforma',
        'description': res['description'],
        'value': res['amount'],
        'currency': res['currency'],
        'language': res['lang'],
        'source': res['url']['origin'],
        'morning_id': res['id'],
    }
    print('--new document data: ', new_doc)

    # Add to DB
    print('--adding document to DB--')
    cursor.execute('INSERT INTO documents (organization_id, type, description, value, currency, language, source, morning_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)', list(new_doc.values()))
    conn.commit()        
 
    return new_doc

