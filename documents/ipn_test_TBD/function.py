import json
from urllib.parse import parse_qs
import utils
from os import environ
import requests


def create_tax_invoice(service: dict, organization: dict, invoice_description: str) -> dict:
    print('--creating tax invoice--')
    """
    Given a service_connection object and a organization object, call the morning API and create a tax invoice
    """
    # Add the client data based on organization
    client = {
        'id': organization['morning_id'],
        'name': organization['name'],
        'emails': [organization['email']]
    }
    # Add the payment and income data based on the service_connection
    income = [{
        'catalogNum': service['serial'],
        'description': service['description'],
        'quantity': service['quantity'],
        'price': service['value'],
        'currency': service['unit'],
        # TODO: Add tax options
        'vatType': 1
    }]

    payment = [{
    'date': '2022-12-19',  # TODO: Add dynamic dates
    'type': 5, # '5': Paypal
    'price': service['value'],
    'currency': service['unit'],
}]

    # Create payload
    payload = {
        'type': 320,
        'description': invoice_description,
        # TODO: Change temp default settings
        'currency': 'ILS',
        'lang': 'he',
        'vatType': 1,
        'client': client,
        'income': income,
        'payment': payment
    }
    print('--morning payload: ', payload)

    # Make the morning API call
    token = utils.get_morning_token(environ['MORNING_SECRET_ARN'])
    url = 'https://sandbox.d.greeninvoice.co.il/api/v1/documents'
    headers = {'Authorization': 'Bearer ' + token}
    res = requests.post(url, headers=headers, data=json.dumps(payload))
    print('--morning response status code: ', res.status_code)
    res = res.json()
    if res.status_code < 200 or res.status_code > 299:
        raise Exception(json.dumps(res))

    return res


def lambda_handler(event, context):
    print('-------event------')
    print(event)

    # # *** MOCK - TBD ***
    # data = {}
    # data['subscription_id'] = event['recurring_payment_id']
    # data['txn_type'] = event['txn_type']

    
    # Parse event from x-www-form-urlencoded data to dict
    body = parse_qs(event['body-json'])
    print('--ps: ', body)    
    # Extract data from the payload
    data = {}
    if 'txn_type' in body:
        data['txn_type'] = body['txn_type'][0]
        print('--txn type: ', data['txn_type'])

    # Check if the paypal IPN event type is recurring payment
    if data['txn_type'] == 'recurring_payment':
        print('--IPN event: recurring payment--')
        
        data['subscription_id'] = body['recurring_payment_id'][0]        
        print('--parsed data: ', data)

        # Connect to DB
        conn = utils.get_db_connection(environ['DB_ENDPOINT'], environ['DB_NAME'], environ['SECRET_ARN'])
        cursor = conn.cursor()
        
        # Extract the relevant service data
        cursor.execute('SELECT service_connections.*, serial FROM service_connections LEFT JOIN services ON services.id = service_id WHERE connection_id = %s', (data['subscription_id']))
        service = cursor.fetchone()
        print('--service found: ', service)

        # no services found
        if not service:
            conn.close()
            raise Exception('err-400: no services found in db')

        # Extract organization data
        cursor.execute('SELECT id, name, phone, email, morning_id, country, city, address_line FROM organizations WHERE id = (SELECT owner_id FROM accounts WHERE id = %s)', service['account_id'])
        organization = cursor.fetchone()
        print('--organization found: ', organization)

        # No organization found
        if not organization:
            conn.close()
            raise Exception('err-400: no organization found in db')
        
        try:
            invoice = create_tax_invoice(service, organization, 'TEST DESCRIPTION')
        except Exception as e:
            print('--exception in creating tax invoice--')
            print('--exception: ', e)
            return {'statusCode': 400}            
        print('--invoice: ', invoice)


    # IPN event is not recurring payment
    else:
        print('--txn_type is not subscription--')
        return {
            'statusCode': 200,
            'body': json.dumps(
                {'message': 'Irrelevant IPN event'}
            )
        }

    return {
        'statusCode': 200,
        'body': json.dumps(
            {
                'test': 'testing'
            }
        )
    }
