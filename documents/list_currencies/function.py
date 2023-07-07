import requests
import os

def lambda_handler(event, context):
    print('--event: ', event)
    url = os.environ['MORNING_URL']

    res = requests.get(url)
    print('--request status code: ', res.status_code)

    if res.status_code > 299 or res.status_code < 200:
        print('error: ', res)
        raise Exception('--err-500: could not retrieve currencies from morning servers ')
    
    res = res.json()
    print('--res: ', res)
    currencies = [curr['code'] for curr in res]
    return currencies