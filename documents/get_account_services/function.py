import utils
import os
import requests

def lambda_handler(event, context):
    # Get account number
    print('--event: ', event)
    conn = utils.get_db_connection(os.environ['DB_ENDPOINT'], os.environ['DB_NAME'], os.environ['SECRET_ARN'])
    cursor = conn.cursor()

    cursor.execute('SELECT account_number FROM accounts WHERE id = %s', event['account_id'])
    customer_id = cursor.fetchone()['account_number']
    print('--customer id: ', customer_id)

    # Get gapps data for this account
    cntr_headers = cntr_headers = utils.get_cntr_auth(os.environ['CNTR_SECRET_ARN'])
    url = os.environ['CNTR_API_URL'] + '/gapps/invoice'
    url += '?customer_id=' + customer_id
    res = requests.get(url, headers=cntr_headers)
    print('--cntr status code: ', res.status_code)
    subs = res.json()
    

    # **TEMP - LOCAL TESTING**
    # subs = [{"name": "accounts/C049ub8g4/customers/Sp6yGGpkwsOOpI/entitlements/SVlop37e0VOXCR", "quantity": 6, "serial": "UM8oR33G7oGVqB", "margin": 0, "unit": "USD", "value": 6.0}, {"name": "accounts/C049ub8g4/customers/Sp6yGGpkwsOOpI/entitlements/SVzh457QPqLcOj", "quantity": 102, "serial": "SRRpRk3rG7zvB3", "margin": 0.2, "unit": "USD", "value": 4.8}, {"name": "accounts/C049ub8g4/customers/Sp6yGGpkwsOOpI/entitlements/SqCVDe93rtExOL", "quantity": 2, "serial": "UR6wZ33Nj7REKw", "margin": 0, "unit": "USD", "value": 14.0}]

    # Construct accounts services from the google data
    account_services = []

    for sub in subs:
        # Get the releveant service for the subscription
        cursor.execute('SELECT id, description FROM services WHERE serial = %s', sub['serial'])
        service = cursor.fetchone()
        
        service_connection = {
            'account_id': event['account_id'],
            'service_id': service['id'],
            'description': service['description'],
            'value': sub['value'],
            'unit': sub['unit'],
            'quantity': sub['quantity'],
            'margin': sub['margin'],
        }
        s = service_connection.values()
        print('--New service connections: ', service_connection)
        # Insert the new account service into the DB
        cursor.execute('INSERT INTO service_connections (account_id, service_id, description, value, unit, quantity, margin) VALUES (%s, %s, %s, %s, %s, %s, %s)', list(service_connection.values()))

    conn.commit()
    print('--commited changes--')
    return 0



