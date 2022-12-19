import json
from urllib.parse import parse_qs
import utils
from os import environ
import requests


def create_tax_invoice(service: dict, organization: dict, invoice_description: str) -> dict:
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
        'price': service['price'],
        'currency': service['unit'],
        # TODO: Add tax options
        'vatType': 1
    }]

    payment = [{
    'date': '2022-12-19',  # TODO: Add dynamic dates
    'type': 5, # '5': Paypal
    'price': service['price'],
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

    # Make the morning API call
    token = utils.get_morning_token(environ['MORNING_SECRET_ARN'])
    url = 'https://sandbox.d.greeninvoice.co.il/api/v1/documents'
    headers = {'Authorization': 'Bearer ' + token}
    res = requests.post(url, headers=headers, data=payload)
    print('--morning response status code: ', res.status_code)
    res = res.json()


def lambda_handler(event, context):
    print('-------event------')
    print(event)
    print('--Event body: ', event['body-json'])
    body = parse_qs(event['body-json'])
    print('--ps: ', body)
    print('--type of body: ', type(body))

    # Extract data from the payload
    data = {}
    if 'txn_type' in body:
        data['txn_type'] = body['txn_type'][0]
    print('data: ', data)
    print('data type: ', type(data['txn_type']))

    if data['txn_type'] == 'recurring_payment':
        print('--Recurring payment--')
        data['subscription_id'] = body['recurring_payment_id'][0]
        # connect to db and search for service connection with the subcription id
        conn = utils.get_db_connection(
            environ['DB_ENDPOINT'], environ['DB_NAME'], environ['SECRET_ARN'])
        cursor = conn.cursor()
        cursor.execute(
            'SELECT * FROM service_connections WHERE connection_id = %s', (data['subscription_id']))
        services = cursor.fetchall()
        print('--services found: ', services)

    else:
        print('--txn_type is not subscription')

    return {
        'statusCode': 200,
        'body': json.dumps(
            {
                'test': 'testing'
            }
        )
    }
