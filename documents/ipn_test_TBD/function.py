import json
from urllib.parse import parse_qs

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
        print('--data: ', data)
        print('--data type: ', type(data['subscription_id']))
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
