import json
from urllib.parse import parse_qs
import utils
from os import environ

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
        conn = utils.get_db_connection(environ['DB_ENDPOINT'], environ['DB_NAME'], environ['SECRET_ARN'])
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM service_connections WHERE connection_id = %s', (data['subscription_id']))
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
