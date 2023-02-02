import json
from urllib.parse import parse_qs
import utils
from os import environ
import requests


def create_tax_invoice(services: list, organization: dict, invoice_description: str) -> dict:
    """
    Given a service_connection object and a organization object, call the morning API and create a tax invoice
    """
    print('--creating tax invoice--')

    print('--services in create_tax_invoice: ', services)  # **TBD**

    # Add the client data based on organization
    client = {
        'id': organization['morning_id'],
        'name': organization['name'],
        'emails': [organization['email']]
    }
    # Add the payment and income data based on the service_connection

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
    token = utils.get_morning_token(environ['MORNING_SECRET_ARN'])
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


def handle_recurring_payment(data):
    print('--parsed data: ', data)

    # Connect to DB
    conn = utils.get_db_connection(
        environ['DB_ENDPOINT'], environ['DB_NAME'], environ['SECRET_ARN'])
    cursor = conn.cursor()

    # Extract the relevant service data
    cursor.execute(
        'SELECT service_connections.*, serial FROM service_connections LEFT JOIN services ON services.id = service_id WHERE connection_id = %s', (data['subscription_id']))
    services = cursor.fetchall()
    print('--services found: ', services)

    # no services found
    if len(services) < 1:
        conn.close()
        raise Exception(
            'err-400: no services matching the paypal subscription id found in db')

    # Extract organization data (*use the id of the first service in the list since they must all belong to the same organization)
    cursor.execute(
        'SELECT id, name, phone, email, morning_id, country, city, address_line FROM organizations WHERE id = (SELECT owner_id FROM accounts WHERE id = %s)', services[0]['account_id'])
    organization = cursor.fetchone()
    print('--organization found: ', organization)

    # No organization found
    if not organization:
        conn.close()
        raise Exception('err-400: no organization found in db')

    try:
        # TODO: Update description somehow
        invoice = create_tax_invoice(
            services, organization, 'TEST DESCRIPTION')
    except Exception as e:
        print('--exception in creating tax invoice--')
        print('--exception: ', e)
        return {'statusCode': 400}
    print('--invoice: ', invoice)


def handle_failure(data):
    print('--reucurring payment failed--')


def lambda_handler(event, context):
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
    paypal_verify_url = 'https://ipnpb.sandbox.paypal.com/cgi-bin/webscr'
    headers = {'content-type': 'application/x-www-form-urlencoded'}
    params_data = '?' + event['body-json'] + '&cmd=_notify-validate'

    print('--verifying against paypal servers--')
    res = requests.post(paypal_verify_url+params_data, headers=headers)
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
        # data['subscription_id'] = body['recurring_payment_id'][0]  # **Comment this line if testing locally
        handle_recurring_payment(data)
    elif data['txn_type'] == 'recurring_payment_failed':
        print('--IPN event: subscription failure')
        # data['subscription_id'] = body['recurring_payment_id'][0]  # **Comment this line if testing locally
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


{'body-json': 'mc_gross=1000.00&outstanding_balance=0.00&period_type=+Regular&next_payment_date=02%3A00%3A00+Jan+31%2C+2023+PST&protection_eligibility=Eligible&payment_cycle=Daily&address_status=confirmed&tax=0.00&payer_id=72CM8GPAN5KVN&address_street=%E9%F9%F8%E0%EC%E9%F1+5+%E3%E9%F8%E4+4&payment_date=23%3A27%3A05+Jan+29%2C+2023+PST&payment_status=Completed&product_name=Cloud+Platinum&charset=windows-1255&recurring_payment_id=I-CBMFG4GJDMF0&address_zip=61014&first_name=Nadav&mc_fee=35.20&address_country_code=IL&address_name=Nadav+Dagon&notify_version=3.9&amount_per_cycle=1000.00&payer_status=verified&currency_code=ILS&business=tomer%40high-t.cloud&address_country=Israel&address_city=%FA%EC-%E0%E1%E9%E1&verify_sign=A-8sxAsepLwVCTE9rkoV7Fc5m-kFAJerCEUwFC3f2pHrnaPfbu8ztjR-&payer_email=69dagod69%40gmail.com&initial_payment_amount=0.00&profile_status=Active&amount=1000.00&txn_id=48X50886Y1043502C&payment_type=instant&last_name=Dagon&address_state=&receiver_email=tomer%40high-t.cloud&payment_fee=&receiver_id=N5NH53T46TSYS&txn_type=recurring_payment&mc_currency=ILS&residence_country=IL&test_ipn=1&transaction_subject=Cloud+Platinum&payment_gross=&shipping=0.00&product_type=1&time_created=23%3A27%3A05+Jan+29%2C+2023+PST&ipn_track_id=700156eae6786',
    'params': {'path': {}, 'querystring': {}, 'header': {'Accept': 'text/plain, application/json, application/*+json, */*', 'Accept-Encoding': 'gzip,deflate', 'Content-Type': 'application/x-www-form-urlencoded', 'Host': '1buvn89ho4.execute-api.eu-west-1.amazonaws.com', 'User-Agent': 'PayPal IPN ( https://www.paypal.com/ipn )', 'X-Amzn-Trace-Id': 'Root=1-63d77273-1fcf4ac3413aa3a409b18610', 'X-Forwarded-For': '173.0.80.116', 'X-Forwarded-Port': '443', 'X-Forwarded-Proto': 'https'}}, 'stage-variables': {}, 'context': {'account-id': '', 'api-id': '1buvn89ho4', 'api-key': '', 'authorizer-principal-id': '', 'caller': '', 'cognito-authentication-provider': '', 'cognito-authentication-type': '', 'cognito-identity-id': '', 'cognito-identity-pool-id': '', 'http-method': 'POST', 'stage': 'dev1', 'source-ip': '173.0.80.116', 'user': '', 'user-agent': 'PayPal IPN ( https://www.paypal.com/ipn )', 'user-arn': '', 'request-id': '943f12c4-8ff6-46ee-961b-51c8d52fa5a4', 'resource-id': 'a0si17', 'resource-path': '/documents/paypal'}}
