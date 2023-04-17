import requests
import json
from datetime import datetime, timedelta


def get_creds_from_file(file_path:str) -> dict:
    """
    get credentials (client_id and client_secret) from json file
    """
    creds = None
    with open(file_path, 'r') as f:
        creds = f.read()
    creds = json.loads(creds)
    
    if 'installed' in creds:
        creds = creds['installed']
    elif 'web' in creds:
        creds = creds['web']
    return creds


def get_token_from_file(file_path:str) -> dict:
    """
    get a token dict from json file
    """
    token = None
    with open(file_path, 'r') as f:
        token = f.read()
    
    try:
        token = json.loads(token)
    except Exception as e:
        print('--could not parse file data to dict, error: ', e)

    return token


def make_new_token(creds, file_path:str=None, logs:bool=True) -> dict:
    """
    Create a new token using Oauth2 flow (Manually)
    `creds`: if string - path to the credentials.json file containing the client id and secret. if dict: dict object containig the creds info
    `file_path`: if not None the token data will be written to file in this path.
    """

    SCOPES = ['https://www.googleapis.com/auth/apps.order', 'https://www.googleapis.com/auth/apps.reports.usage.readonly']

    # if required read creds data from file
    if type(creds) is str:
        try:
            with open(creds, 'r') as f:
                creds = f.read()
            # Format the file data
            creds = json.loads(creds)

            if 'installed' in creds:
                creds = creds['installed']
            elif 'web' in creds:
                creds = creds['web']
        except Exception as e:
            print('--error reading creds file location: ', e)

    print('--creds: ', creds)
    # Request an authorization code
    auth_url = 'https://accounts.google.com/o/oauth2/v2/auth'
    auth_params = {
        'response_type': 'code',
        'client_id': creds['client_id'],
        'redirect_uri': creds['redirect_uris'][0],
        'scope': ' '.join(SCOPES),
        'access_type': 'offline',
        'prompt': 'consent'
    }

    # Start manual flow
    print('Go to the following URL and grant permission:')
    print(f'{auth_url}?{requests.compat.urlencode(auth_params)}')

    # Get the authorization code from the user
    auth_code = input('Enter the authorization code: ')

    # Exchange the authorization code for an access token
    token_url = 'https://oauth2.googleapis.com/token'
    token_data = {
        'code': auth_code,
        'client_id': creds['client_id'],
        'client_secret': creds['client_secret'],
        'redirect_uri': creds['redirect_uris'][0],
        'grant_type': 'authorization_code'
    }

    response = requests.post(token_url, data=token_data)

    # Check if the request was successful
    if response.status_code == 200:
        token_data = response.json()        
        # Save the access token for later use  
        if logs:
            print('--got token data--')
    else:
        # Handle the error
        error_message = response.json().get('error_description', '')
        print(f'Request failed with error: {error_message}')
        raise Exception('--could not get access token--')
    
    # Format the token data
    token_data['scopes'] = token_data['scope'].split(' ')
    token_data.pop('scope')    
    token_data['expiry'] = (datetime.now() - timedelta(seconds=int(token_data['expires_in'] + 60))).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    token_data.pop('expires_in')
    token_data['client_id'] = creds['client_id']
    token_data['client_secret'] = creds['client_secret']

    # Write data to file
    if file_path is not None:
        token_json = json.dumps(token_data)
        with open(file_path, 'w') as f:
            f.write(token_json)
        if logs:
            print('--written token data to file at ', file_path)

    return token_data


def refresh_token(token:dict, file_path:str=None, logs:bool=True) -> dict:
    """
    Use the refresh token to recieve a new access token
    return a copy of `token` with 'access_token' and 'expires_in' updated
    `token`: path to json file containing the refresh token and expired access token.
    `file_path`: if not none the updated token data will be saved to json file with this path.
    """
    # construct the request
    url = 'https://oauth2.googleapis.com/token'
    data = {
        'grant_type': 'refresh_token',
        'refresh_token': token['refresh_token'],
        'client_id': token['client_id'],
        'client_secret': token['client_secret']
    }

    response = requests.post(url, data=data)

    # Check if the request was successful
    if response.status_code == 200:
        token_data = response.json()
        
        # Update the old token with a new access token and expiry date
        new_token = token.copy()
        new_token['access_token'] = token_data['access_token']
        new_token['expiry'] = (datetime.now() - timedelta(seconds=int(token_data['expires_in'] + 60))).strftime('%Y-%m-%dT%H:%M:%S.%fZ')

        # Save to file
        if file_path is not None:
            token_json = json.dumps(new_token)
            with open(file_path, 'w') as f:
                f.write(token_json)
        if logs:
            print('--wrote token data to file--')

        return new_token
        

    else:
        # Handle the error
        error_message = response.json().get('error_description', '')
        print(f'Request failed with error: {error_message}')    
        raise Exception('--could not recieve refresh token--')