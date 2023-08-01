from boto3 import client
from json import loads, dumps
from pymysql import connect
from pymysql.cursors import DictCursor
from os.path import join, isfile
from datetime import datetime


def get_db_connection(db_endpoint:str, db_name:str, secret_arn:str):
    # Get secret values

    # check if secret is stored in the temp directory
    file_path = join('/tmp', 'db_secrets.json')
    if isfile(file_path):
        with open(file_path, 'r') as f:
            secrets_dict = loads(f.read())
        print('--retrieved secrets from file--')
    else:
        sm_client = client('secretsmanager')
        sm_res = sm_client.get_secret_value(SecretId=secret_arn)
        secrets_dict = loads(sm_res['SecretString'])
        print('--Retrieved secrets--')
        # write data to temp file
        with open(file_path, 'w') as f:
            f.write(dumps(secrets_dict))
        print('--wrote data to file--')
                
    # Connect to RDS
    conn = connect(host=db_endpoint, user=secrets_dict['db_username'], password=secrets_dict['db_password'], database=db_name, cursorclass=DictCursor)    
    print('--Connected to db--')
    return conn


def get_user_auth(cursor, event:dict = None, organization_id=None, account_id=None, user_sub:str = None)->int:
    """
    Returns user's permission level in it's organization (Based on 1to1 user-organization approach)
    event mode: if event is passed and other params were not explicitly passed, all params will be taken from event, pass False for the param to be ignored in the event.
    Account mode: if account id is present, organization id will be ignored and the organization id will be that of the acocunt's owner
    """        

    # Check for event mode
    if event is not None:
        if organization_id is None and 'organization_id' in event: organization_id = event['organization_id']
        if account_id is None and 'account_id' in event: account_id = event['account_id']
        if user_sub is None and 'user_sub' in event: user_sub = event['user_sub']
    
    # Validate that all required variables exist
    if not user_sub or (not organization_id and not account_id):
        print('--invalid params in get auth--')
        return -2    

    # Account mode
    if account_id:
        print('--using acocunt owner id--')
        # Get the account's organization owner
        cursor.execute('SELECT connected_users FROM organizations WHERE id = (SELECT organization_id FROM accounts WHERE id = %s)', account_id)
    else:  # Organization mode
        cursor.execute('SELECT connected_users FROM organizations WHERE id = %s', organization_id)
    
    # get organization's user permissions
    org_users = cursor.fetchone()
    if not org_users:
        print('--did not find org users--')
        return -2
    org_users = loads(org_users['connected_users'])
    print('--org users: ', org_users)

    # find user's sub in organization
    for sub in org_users:
        if sub == user_sub:
            print('--user auth found--')
            return int(org_users[sub])

    # user not found
    print('--user not in organization--')
    return -1


def get_morning_token(secret_arn:str)->str:
    from requests import post

    sm = client('secretsmanager')

    # Search secret values in temp folder    
    file_path = join('/tmp', 'morning_secrets.json')

    if isfile(file_path):        
        with open(file_path, 'r') as f:
            secret = loads(f.read())
        print('--retrieved morning secrets from file--')
    else:
        # Get current token
        res = sm.get_secret_value(SecretId=secret_arn)
        secret = res['SecretString']
        secret = loads(secret)
        print('--retrieved morning secret--')

    # Check if token is valid
    token_expiration = datetime.fromtimestamp(int(secret['expires']))
    if token_expiration > datetime.today():
        print('--token is valid--')
        return secret['token']

    # If token is invalid get a new token
    print('--creating new token--')
    url = 'https://sandbox.d.greeninvoice.co.il/api/v1/account/token'
    req_body = {
        'id': secret['api_key'],
        'secret': secret['api_secret']
    }
    res = post(url, data=dumps(req_body), headers={'Content-Type': 'application/json'})
    print('--Morning token status code: ', res.status_code)
    res = res.text
    res = loads(res)

    # Update secret values in secrets manager
    secret['expires'] = res['expires']
    secret['token'] = res['token']

    res = sm.update_secret(SecretId=secret_arn, SecretString=dumps(secret))

    # Write secret data to new file    
    print('--writing morning secret data to file--')
    with open(file_path, 'w') as f:
        f.write(dumps(secret))    

    print('--retrieved morning api token--')
    return secret['token']


def get_cntr_auth(secret_arn:str)->dict:
    import hmac
    from hashlib import sha256

    # Get Secrets
    sm = client('secretsmanager')
    res = sm.get_secret_value(SecretId=secret_arn)

    secrets_dict = loads(res['SecretString'])
    print('--retrieved cntr secrets--')

    # Build Hmac
    timestamp = datetime.now().timestamp()
    hash_str = f'{secrets_dict["version"]}:{timestamp}'

    mac = hmac.new(key=secrets_dict['signature_secret'].encode(), msg=hash_str.encode(), digestmod=sha256)
    mac_digest = mac.hexdigest()

    headers = {
        'x-api-key': secrets_dict['api_key'],
        'x-billing-signature': mac_digest,
        'x-billing-timestamp': str(timestamp)
    }
    print('--got cntr credentials--')

    return headers


# Helper functions
def get_insert_statement(item, table=None):
    param_names = ', '.join(item.keys())
    param_placeholders = ('%s, ' * len(item))[:-2]
    param_values = list(item.values())

    if table:
        statement = f'INSERT INTO {table} ({param_names}) VALUES ({param_placeholders})'
        return statement, param_values, param_names, param_placeholders

    return param_values, param_names, param_placeholders