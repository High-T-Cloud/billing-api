from os import environ
import utils
import json


def create_service_price(event:dict, id:int, cursor, conn ):
    print('--creating price data--')
    if 'percent_from' in event and event['percent_from'] != '':
        print('--in event--')
        # Percent based
        
        # Extract ids of services to take the percent from
        percent_from = json.loads(event['percent_from'])

        # Create service_price for each
        for percent_id in percent_from:

            # Get currency and validate account_service exists
            cursor.execute('SELECT currency, percent_from_id FROM service_prices WHERE account_service_id = %s', percent_id)
            currency = cursor.fetchone()
            print('--currecny: ', currency)
            if not currency:
                #TODO: Severe error! (account service created without service price)
                conn.close()
                raise Exception('err-400: cannot find account service in percent_from')
            if currency['percent_from_id'] != None:
                raise Exception('err-400: cannot use percent based account services')
            currency = currency['currency']

            new_price = {'account_service_id': id, 'currency': currency, 'percent_amount': event['amount'], 'percent_from_id': percent_id}
            print('--service price: ', new_price)

            # Insert to DB
            param_names = ', '.join(new_price.keys())
            param_placeholders = ('%s, ' * len(new_price))[:-2]
            param_values = list(new_price.values())

            cursor.execute(f'INSERT INTO service_prices ({param_names}) VALUES ({param_placeholders})', param_values)
            conn.commit()

    else:
        # Create service price
        new_price = {'amount': None, 'currency': None}

        # Merge with event data
        for key in new_price:
            if key in event and event[key] != '':
                new_price[key] = event[key]
        
        new_price['account_service_id'] = id

        print('--service price: ', new_price)
        
        # Insert to DB
        param_names = ', '.join(new_price.keys())
        param_placeholders = ('%s, ' * len(new_price))[:-2]
        param_values = list(new_price.values())

        cursor.execute(f'INSERT INTO service_prices ({param_names}) VALUES ({param_placeholders})', param_values)
        conn.commit()
        print('--inserted service price to DB--')


def lambda_handler(event, context):
    print('--event: ', event)

    # CONSTS
    PAYMENT_SOURCE_OPTIONS = ['manual', 'paypal']

    conn = utils.get_db_connection(environ['DB_ENDPOINT'], environ['DB_NAME'], environ['SECRET_ARN'])
    cursor = conn.cursor()

    # Permission level required: Master
    user_auth = int(utils.get_user_auth(cursor, event, account_id=False, organization_id=6))
    print('--user auth: ', user_auth)
    if user_auth !=3:
        conn.close()
        raise Exception('err-401: user access denied')    
    
    # Validate service id
    cursor.execute('SELECT id, data_source FROM services WHERE id = %s', event['service_id'])
    service = cursor.fetchone()
    if not service:
        conn.close()
        raise Exception('err-400: invalid service id')
    print('--validated service id--')

    # Validate payment source
    if 'payment_source' in event and event['payment_source'] != '':
        if event['payement_source'] not in PAYMENT_SOURCE_OPTIONS:
            conn.close()
            raise Exception('err-400: invalid payment source')

    # Create a new account service
    # TODO: validate currency code
    service_schema = {
        'service_id': None,
        'account_id': None,
        'description': None,
        'quantity': None,
        'discount': None,
        'margin': None,
        'payment_source': None,
        'payment_source_id': None,
        'vat_included': None,
    }
    new_service = {}
    for key in event:
        if key in service_schema and key in event and event[key] != '':
            new_service[key] = event[key] 
  
    print('--new account service: ', new_service)

    # Insert to DB
    param_names = ', '.join(new_service.keys())
    param_placeholders = ('%s, ' * len(new_service))[:-2]
    param_values = list(new_service.values())

    cursor.execute(f'INSERT INTO account_services ({param_names}) VALUES ({param_placeholders})', param_values)
    conn.commit()

    # Get the id of the newely created account_service
    cursor.execute('SELECT LAST_INSERT_ID() AS id')    
    acc_service_id = cursor.fetchone()['id']
    print('--inserted account service to db--')


    create_service_price(event, acc_service_id, cursor, conn )
        
    return {
        'message': 'account service added'
    }