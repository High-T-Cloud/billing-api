import json
from urllib.parse import parse_qs
import utils
import os
import requests

# Paypal IPN Txn types:
# 'recurring_payment_profile_cancel' - Subscription cancled by client
# I-E918601SMY45

def create_tax_invoice(services: list, organization: dict, invoice_description: str) -> dict:
    """
    Given an `account_service` object and an `organization` object, call the morning API and create a tax invoice
    """
    print('--creating tax invoice--')

    print('--services in create_tax_invoice: ', services)  # **TBD**

    # Add the client data based on organization
    client = {
        'id': organization['morning_id'],
        'name': organization['name'],
        'emails': [organization['email']]
    }
    # Add the payment and income data based on the account_service

    # Format each service in the services list to match morning api
    # Calculate the sum of values for all the services and add it to the payment part in the payload
    # *** TEMPORARILY CALCULATE THE SUM AS IF ALL THE SERVICES HAVE THE SAME UNIT AND SET THE UNIT IN THE PAYMENT ACCORDINGLY ***
    income = []
    income_sum = 0
    for service in services:
        formatted_service = {
            'catalogNum': service['serial'],
            'description': service['description'],
            'quantity': service['quantity'],
            'price': service['value'],
            'currency': service['unit'],
            # TODO: Add tax options
            'vatType': 1
        }
        income.append(formatted_service)
        income_sum += formatted_service['price']
    print('--income payload: ', income)

    payment = [{
        'date': '2022-12-19',  # TODO: Add dynamic dates
        'type': 5,  # '5': Paypal
        'price': income_sum,
        'currency': services[0]['unit']
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
    token = utils.get_morning_token(os.environ['MORNING_SECRET_ARN'])
    url = 'https://sandbox.d.greeninvoice.co.il/api/v1/documents'
    headers = {'Authorization': 'Bearer ' + token}
    res = requests.post(url, headers=headers, data=json.dumps(payload))
    print('--morning response status code: ', res.status_code)
    print('--morning res content: ', res.content)
    if res.status_code < 200 or res.status_code > 299:
        raise Exception(res.content)

    res = res.json()
    print('--res json: ', res)
    return res


def handle_recurring_payment(recurring_payment_id):
    print('--handling recurring payment with id: ', recurring_payment_id)

    # Connect to DB
    conn = utils.get_db_connection(os.environ['DB_ENDPOINT'], os.environ['DB_NAME'], os.environ['SECRET_ARN'])
    cursor = conn.cursor()

    # Extract the relevant service data
    cursor.execute('SELECT account_services.*, serial FROM account_services LEFT JOIN services ON services.id = service_id WHERE connection_id = %s', (recurring_payment_id))
    services = cursor.fetchall()
    print('--services found: ', services)

    # no services found
    if len(services) < 1:
        conn.close()
        raise Exception('err-400: no services matching the paypal subscription id found in db')

    # Extract organization data (*use the id of the first service in the list since they must all belong to the same organization)
    cursor.execute('SELECT id, name, phone, email, morning_id, country, city, address_line FROM organizations WHERE id = (SELECT owner_id FROM accounts WHERE id = %s)', services[0]['account_id'])
    organization = cursor.fetchone()
    print('--organization found: ', organization)

    # No organization found
    if not organization:
        conn.close()
        raise Exception('err-400: no organization found in db')

    try:
        # TODO: Update description somehow
        invoice = create_tax_invoice(services, organization, 'TEST DESCRIPTION')
    except Exception as e:
        print('--exception in creating tax invoice--')
        print('--exception: ', e)
        return {'statusCode': 400}
    print('--invoice: ', invoice)


def handle_failure(data):
    print('--reucurring payment failed--')


def legacy_main(event, context):
    """
    the main function's job is to parse the data, verify the ipn message and then check the txn_type and call the handler function accordingly
    """

    print('---event---', event)

    # *** MOCK - When testing locally ****
    # data = {}
    # data['subscription_id'] = event['recurring_payment_id']
    # data['txn_type'] = event['txn_type']

    # Parse event from x-www-form-urlencoded data to dict (**comment all of this if testing locally**)
    body = parse_qs(event['body-json'])
    print('--ps: ', body)
    # Extract data from the payload
    data = {}
    if 'txn_type' in body:
        data['txn_type'] = body['txn_type'][0]
        print('--txn type: ', data['txn_type'])

    # Verify IPN message is legitimate against paypal servers
    headers = {'content-type': 'application/x-www-form-urlencoded'}
    params_data = '?' + event['body-json'] + '&cmd=_notify-validate'

    print('--verifying against paypal servers--')
    res = requests.post(
        os.environ["PAYPAL_VERIFY_URL"]+params_data, headers=headers)
    if res.status_code < 200 or res.status_code > 299:
        print('--res status code: ', res.status_code)
        print('--res content: ', res.content)
        raise Exception('err-500: paypal verification failed')
    print('--paypal verification: ', res.text)
    if res.text != 'VERIFIED':
        raise Exception('err-500: paypal verification failed')

    # Check the type of IPN message
    if data['txn_type'] == 'recurring_payment':
        print('--IPN event: recurring payment--')
        data['subscription_id'] = body['recurring_payment_id'][0]
        handle_recurring_payment(data)
    elif data['txn_type'] == 'recurring_payment_failed':
        print('--IPN event: subscription failure')
        data['subscription_id'] = body['recurring_payment_id'][0]
        handle_failure(data)
    else:
        print('--IPN event is not subscription--')
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Irrelevant IPN event'})
        }

    # Success
    return {
        'statusCode': 200,
        'body': json.dumps(
            {
                'test': 'testing'
            }
        )
    }


def lambda_handler(event, context):
    # print('--event: ', event)

    records = event['Records']
    print('--number of messages: ', len(records))

    for record in records:
        body = parse_qs(record['body'])
        print('--body: ', body)

        # Verify IPN message is legitimate against paypal servers
        print('--verifying against paypal servers--')
        headers = {'content-type': 'application/x-www-form-urlencoded'}
        params_data = '?' + record['body'] + '&cmd=_notify-validate'
        res = requests.post(os.environ["PAYPAL_VERIFY_URL"]+params_data, headers=headers)
        if res.status_code < 200 or res.status_code > 299:
            print('--res status code: ', res.status_code)
            print('--res content: ', res.content)
            raise Exception('err-500: paypal verification failed')
        print('--paypal verification: ', res.text)
        if res.text != 'VERIFIED':
            raise Exception('err-500: paypal verification failed')
        
        # Check the message type
        if 'txn_type' not in body:
            raise Exception('err-500: txn_type not found in message')
        print('--message type: ', body['txn_type'])

        if body['txn_type'][0] == 'recurring_payment':
            try:
                handle_recurring_payment(body['recurring_payment_id'][0])
            except Exception as e:
                raise e

    return 0
