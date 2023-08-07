import utils
import os
import requests


def update_cntr_services_g1(cursor, conn, services: list, account: dict) -> list:
    """
    get amount from invoice and update the account service data
    There should only be one cntr based service for this group
    """

    print('--getting connector data--')
    # Get data from the connector
    cntr_headers = utils.get_cntr_auth(os.environ['CNTR_SECRET_ARN'])
    url = f'{os.environ["CNTR_API_URL"]}{account["cntr_endpoint"]}/invoices-last?account_id={account["account_number"]}&last=1'
    if account['payer_account'] is not None:
        url += '&payer_account=' + account['payer_account']
    print('--calling connector api on url: ', url)

    res = requests.get(url, headers=cntr_headers)
    print('--request status code: ', res.status_code)
    invoice = res.json()
    print('--INVOICE: ', invoice)
    invoice = invoice[0]

    # Get the account service for the provider bill
    account_service = services[0]

    # Update value
    amount = invoice['amount']
    currency = invoice['currency']

    # Update in DB
    cursor.execute('UPDATE account_services SET amount = %s, currency = %s WHERE id = %s', (amount, currency, account_service['id']))
    conn.commit()


def update_cntr_services_g2(cursor, conn, services: list, account: dict) -> list:
    # Get data from connector
    cntr_headers = cntr_headers = utils.get_cntr_auth(
        os.environ['CNTR_SECRET_ARN'])
    url = f"{os.environ['CNTR_API_URL']}{account['cntr_endpoint']}/invoice?customer_id={account['account_number']}"
    print('--calling connector api with url: ', url)
    res = requests.get(url, headers=cntr_headers)
    print('--cntr status code: ', res.status_code)
    subs = res.json()
    print('--cntr res: ', subs)

    # Construct accounts services from the google data
    new_account_services = []
    for sub in subs:
        # Get the releveant service for the subscription
        cursor.execute(
            'SELECT id, description FROM services WHERE serial = %s', sub['serial'])
        service = cursor.fetchone()

        account_service = {
            'account_id': account['id'],
            'service_id': service['id'],
            'description': service['description'],
            'amount': sub['value'],
            'currency': sub['currency'],
            # 'margin': sub['margin'],  # TODO: Check margin meanings
            'quantity': sub['quantity'],
        }
        new_account_services.append(account_service)        

    print('--fetched account services: ', new_account_services)

    # Match existing services by serial and update values
    for new_service in new_account_services:
        found = False 

        for service in services:
            if new_service['service_id'] == service['service_id']:
                # Update values in DB
                cursor.execute('UPDATE account_services SET amount = %s, currency = %s, quantity = %s WHERE id = %s', (
                    new_service['amount'], new_service['currency'], new_service['quantity'], service['id']))
                conn.commit()
                found = True
                break
        if not found:
            # New service
            print('--creating new account service--')
            statement, values, _, _ = utils.get_insert_statement(service, 'account_services')
            cursor.execute(statement, values)
            conn.commit()


def update_percent_services(cursor, conn, services: list):
    print('--updating percent services--')
    for service in services:
        # Get percent_from service
        cursor.execute('SELECT amount, margin, discount FROM account_services WHERE id = %s', service['percent_from'])
        percent_from = cursor.fetchone()
        # Calc amount
        amount = percent_from['amount']
        if percent_from['margin'] is not None:
            amount *= (percent_from['margin'] / 100 + 1)
        if percent_from['discount'] is not None:
            amount *= (percent_from['discount'] / 100 + 1)
        amount *= service['percent_amount']

        # Update in DB
        cursor.execute('UPDATE account_services SET amount = %s WHERE id = %s', (amount, service['id']))
        conn.commit()


def lambda_handler(event, context):
    """
    Update the service connections of an account by account id.    
    connector groups: The model for handling fetching the data for each connector
    `Group1`: get the most recent invoice for this cloud provider and insert one account service with the full montly bill.
    `Group 2`: Get a list of all servics paid for in the provider and insert an account service for each of them.
    Returns a success message.
    """
    print('--event: ', event)

    # Consts
    CONNECTOR_GROUP_1 = ['/vultr', '/do', '/aws']
    CONNECTOR_GROUP_2 = ['/gapps']

    # Setup
    conn = utils.get_db_connection(
        os.environ['DB_ENDPOINT'], os.environ['DB_NAME'], os.environ['SECRET_ARN'])
    cursor = conn.cursor()

    # Auth
    user_auth = int(utils.get_user_auth(
        cursor, event, account_id=False, organization_id=6))
    print('--user auth: ', user_auth)
    if user_auth != 3:
        conn.close()
        raise Exception('err-401: user access denied')

    # --Main--

    # Get account details
    cursor.execute(
        'SELECT accounts.id, account_number, payer_account, provider_id, cntr_endpoint FROM accounts LEFT JOIN providers ON providers.id = provider_id WHERE accounts.id = %s', event['account_id'])
    account = cursor.fetchone()
    print('--account: ', account)

    # Get all current account services
    cursor.execute(
        'SELECT account_services.*, data_source FROM account_services LEFT JOIN services on services.id = service_id WHERE account_id = %s', event['account_id'])
    account_services = cursor.fetchall()
    print('--current account services: ', account_services)

    # split services by data source
    percent_based_services = []
    cntr_based_services = []
    manual_services = []

    for service in account_services:
        if service['data_source'] == 'cntr':
            cntr_based_services.append(service)
        elif service['data_source'] == 'percent':
            percent_based_services.append(service)
        elif service['data_source'] == 'manual':
            manual_services.append(service)

    # Update cntr services
    if account['cntr_endpoint'] in CONNECTOR_GROUP_1:
        if len(cntr_based_services) > 0:
            update_cntr_services_g1(cursor, conn, cntr_based_services, account)
    elif account['cntr_endpoint'] in CONNECTOR_GROUP_2:
        update_cntr_services_g2(cursor, conn, cntr_based_services, account)    

    if len(percent_based_services) > 0:
        update_percent_services(cursor, conn, percent_based_services)

    return {
        'message': 'refresh succesful'
    }
