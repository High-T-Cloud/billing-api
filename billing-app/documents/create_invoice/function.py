import utils
import json
import requests
from os import environ

def lambda_handler(event, context):
    print('--event: ', event)

    conn = utils.get_db_connection(environ['DB_ENDPOINT'], environ['DB_NAME'], environ['SECRET_ARN'])
    cursor = conn.cursor()

    # Auth required: TBD***

    # Get all service connections For Each account owned by this organizations
    statement = 'SELECT accounts.name, services.serial, service_connections.* FROM accounts '
    statement += 'LEFT JOIN service_connections ON account_id = accounts.id LEFT JOIN services ON service_id = services.id '
    statement += 'WHERE service_connections.id IS NOT NULL AND owner_id = %s'

    cursor.execute(statement, (event['organization_id']))
    services = cursor.fetchall()
    # print('--organization services: ', services)

    # TODO: ADD GETTING SERVICE DETAILS FROM CONNECTORS IF NEEDED**


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
        'client': {'id': 'ff1fb256-0d4e-4aa3-a4ff-0aeaecad23b0', 'emails': ['69dagod69@gmail.com']}, # **TBD**
        'income': income
    }
    print('--request body: ', req_body)

    req_body = json.dumps(req_body)
    print('--finished converting to json')    

    # Make morning api call
    TOKEN = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.VUZndHRzQzN6Ym4vVG1YL2JFWEVjUkFDMXpyMkx3U3VNN1o5Qm9EV0tMZTgycTlzdjJlS1VJczFiUndIQkZoaEhNUW1zRWorV1BuU0w1Y3Z1MUxHaWdyQys1OHB1QXdYc1hReFIvbWtOdDZUN2RpYTJISGhyQTFmZWtLWmVubHphTDhqSlk1ZHBjWHloRUQ3Z3FZWE55VklUK0lmZlZ3VFhmT2RCa3BHZ1hBNDE3cS9YTjFDZlZPUFgxVGlEZDVFQkVrcmpuQzZCSkdKZlN6L3RLaVZlSlUrdy9UWkFxcUVpU0NabHNmRU5vSmVuNmFYTDRPYkFhTWhHMjRTeVQ5aDRzL1RvblZYL0czZU1NWktSN28vdHlRTXVFVXZ5SDNkVXlOaE1nUGJ0SUhoWDZlZlVLK2J2R1AwOWM4dDZBOEovRFlaYlJENTJQYVpjaWdKNXprUGFBPT0.ZzA_Tqv8blXnj6kFsWTDvso2s7uMKshObdqZUMGPmJc'
    url = 'https://sandbox.d.greeninvoice.co.il/api/v1/documents'
    headers = {'Authorization': 'Bearer ' + TOKEN}
    res = requests.post(url, headers=headers, data=req_body)

    return res.content


    
