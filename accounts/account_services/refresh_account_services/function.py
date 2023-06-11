import utils
import os
import requests

def get_services_g1(cursor, conn, cntr_endpoint:str, account_number:str, account_id:str, payer_account:str = None) -> list:
    # Get data from the connector
    cntr_headers = utils.get_cntr_auth(os.environ['CNTR_SECRET_ARN'])
    url = f'{os.environ["CNTR_API_URL"]}{cntr_endpoint}/invoices-last?account_id={account_number}&last=1'
    if payer_account is not None:
        url += '&payer_account=' + payer_account
    print('--calling connector api on url: ', url)

    res = requests.get(url, headers=cntr_headers)
    print('--request status code: ', res.status_code)
    invoice = res.json()
    print('--INVOICE: ', invoice)
    invoice = invoice[0]

    # Get the account service for the provider bill
    cursor.execute('SELECT account_services.* FROM account_services LEFT JOIN services ON services.id = service_id WHERE account_id = %s AND data_source = %s', (account_id, 'cntr'))
    account_service = cursor.fetchone()
    print('--service before update: ', account_service)

    # Format the service to match the SQL query
    f_account_service = {
            'account_id': account_id,
            'service_id': account_service['service_id'],
            'description': account_service['description'],
            'value': invoice['amount'],
            'currency': invoice['currency'],
            'margin': account_service['margin'],
            'quantity': account_service['quantity'],
        }
    
    print('--service after update: ', f_account_service)

    return [f_account_service]
    

def get_services_g2(cursor, conn, cntr_endpoint:str, account_number:str, account_id:str) -> list:    
    # Get data from connector
    cntr_headers = cntr_headers = utils.get_cntr_auth(os.environ['CNTR_SECRET_ARN'])
    url = f"{os.environ['CNTR_API_URL']}{cntr_endpoint}/invoice?customer_id={account_number}"
    print('--calling connector api with url: ', url)
    res = requests.get(url, headers=cntr_headers)
    print('--cntr status code: ', res.status_code)
    subs = res.json()

    # Construct accounts services from the google data
    account_services = []
    for sub in subs:
        # Get the releveant service for the subscription
        cursor.execute('SELECT id, description FROM services WHERE serial = %s', sub['serial'])
        service = cursor.fetchone()
        
        account_service = {
            'account_id': account_id,
            'service_id': service['id'],
            'description': service['description'],
            'value': sub['value'],
            'currency': sub['currency'],
            'margin': sub['margin'],
            'quantity': sub['quantity'],
        }
        account_services.append(account_service)

    print('--account services after update: ', account_services)
    return account_services

def lambda_handler(event, context):
    """
    Update the service connections of an account by account id.
    Returns a list of all account's services after the update
    connector groups: The model for handling fetching the data for each connector
    `Group1`: get the most recent invoice for this cloud provider and insert one account service with the full montly bill.
    `Group 2`: Get a list of all servics paid for in the provider and insert an account service for each of them.
    When creating an account_service object the dictionary order MUST be `{account_id, service_id, description, value, currency, quantity, margin}`
    """
    print('--event: ', event)

    # Consts
    CONNECTORS_GROUP1 = ['/vultr', '/do', '/aws']
    CONNECTORS_GROUP2 = ['/gapps']

    # Setup
    conn = utils.get_db_connection(os.environ['DB_ENDPOINT'], os.environ['DB_NAME'], os.environ['SECRET_ARN'])
    cursor = conn.cursor()

    # Permission level required: Master
    user_auth = int(utils.get_user_auth(cursor, event, account_id=False, organization_id=6))
    print('--user auth: ', user_auth)
    if user_auth !=3:
        conn.close()
        raise Exception('err-401: user access denied')


    # Get the provider endpoint
    cursor.execute('SELECT account_number, payer_account, provider_id FROM accounts WHERE id = %s', event['account_id'])
    dbq = cursor.fetchone()
    cursor.execute('SELECT cntr_endpoint FROM providers WHERE id = %s', dbq['provider_id'])
    cntr_endpoint = cursor.fetchone()['cntr_endpoint']
    print('--cntr_endpoint: ', cntr_endpoint)

    # Get accounts services data
    account_services = []
    if cntr_endpoint in CONNECTORS_GROUP1:
        account_services = get_services_g1(cursor, conn, cntr_endpoint, dbq['account_number'], event['account_id'], dbq['payer_account'])
    elif cntr_endpoint in CONNECTORS_GROUP2:
        account_services = get_services_g2(cursor, conn, cntr_endpoint, dbq['account_number'], event['account_id'])        
    
    print('--new account services: ', account_services)

    # Delete all account services with cntr data_source and insert the new ones
    cursor.execute('DELETE account_services FROM account_services LEFT JOIN services ON services.id = account_services.service_id WHERE account_id = %s AND data_source = %s', (event['account_id'], 'cntr'))
    conn.commit()
    print('--deleted old account services')
    
    for service in account_services:
        print('--inserting service: ', service)
        cursor.execute('INSERT INTO account_services (account_id, service_id, description, value, currency, margin, quantity) VALUES (%s, %s, %s, %s, %s, %s, %s)', list(service.values()))
    conn.commit()
    print('--inserted new services--')

    # Return all the servies in the account
    cursor.execute('SELECT * FROM account_services WHERE account_id = %s', event['account_id'])
    output = cursor.fetchall()

    # Serialize datetime values in the response
    for service in output:
        service['last_update'] = service['last_update'].isoformat()

    return output





    



