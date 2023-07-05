import hmac
import hashlib
import requests
import os
import utils
import boto3
import json


def authenticate(body, signature):
    """
    Use hmac to validate webhook message legitimacy.
    """
    print('--verifying message authenticity-- ')
    # Get the hmac secret key from secretsmanager
    sm_client = boto3.client('secretsmanager')
    res = sm_client.get_secret_value(SecretId=os.environ['MORNING_SECRET_ARN'])
    secret_value = json.loads(res['SecretString'])
    
    hmac_secret = secret_value['webhook_secret']
    print('--retrieved secret valuest--')
    
    digest = hmac.new(key=hmac_secret.encode('utf-8'), msg=body.encode('utf-8'), digestmod=hashlib.sha256).hexdigest()
    verified = hmac.compare_digest(digest, signature)
    print('--verified to: ', verified)
    return verified
    

# TODO: implement
def handle_non_invoice():
    print('--document type is not relevant, ending function--')
    return 0

# TODO: implement
def handle_multiple_proformas():
    print('--MULTIPLE PROFORMAS--')
    return 0

def lambda_handler(event, context):
    """
    proccess messages coming from morning webhook (validation and auth is done before this step)
    """
    
    print('--event: ', event)
    
    # TODO: Altert on false message!
    if not authenticate(event['body'], event['headers']['X-Webhook-Signature']):
        print('--FOUND NON LEGITIMATE MESSAGE--')
        raise Exception('err-403: Message was not found as legitimate')
    
    INVOICE_TYPES = [320]  # documents types that need to be handeled
    PROFORMA_TYPE = 300
    
    body = json.loads(event['body'])

    # Check the document type
    if int(body['type']) not in INVOICE_TYPES:
        return handle_non_invoice()

    # --Document is relevant--

    # Call morning api to get linked documents
    print('--calling morning api to get linked documents--')
    url = f'{os.environ["MORNING_URL"]}/{body["id"]}/linked'
    token = utils.get_morning_token(os.environ['MORNING_SECRET_ARN'])
    headers = {'Authorization': 'Bearer ' + token}

    res = requests.get(url, headers=headers)
    print('--response status code: ', res.status_code)
    if res.status_code < 200 or res.status_code > 299:
        # TODO: pay attention - severe error!
        print('--morning response: ', res)
        raise Exception('err-500: unable to get linked documents')        

    linked_docs = res.json()
    print('--linked docs: ', linked_docs)
    
    # Get all proformas
    proforma_doc = []
    for doc in linked_docs:
        if int(doc['type']) == PROFORMA_TYPE:
            proforma_doc.append(doc)
    
    # Check if there is more then one linked proforma
    if len(proforma_doc) > 1:
        return handle_multiple_proformas()
    proforma_doc = proforma_doc[0]
    
    # Find the proforma in the DB
    print('--getting proforma from DB--')
    conn = utils.get_db_connection(os.environ['DB_ENDPOINT'], os.environ['DB_NAME'], os.environ['SECRET_ARN'])
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM documents WHERE morning_id = %s', proforma_doc['id'])
    proforma_db = cursor.fetchone()

    # Proforma not found in DB
    if not proforma_db:
        # TODO: pay attention - severe error!
        conn.close()        
        raise Exception('err-400: proforma not found in db')

    print('--proforma found in db: ', proforma_db)

    # TODO: validate profroma from db is same as from morning
    # TODO: handle mixed currencies between invoice and proforma

    # Update the amount and delete the document if needed
    new_proforma_amount = proforma_db['value'] - float(body['total'])
    print('--new amount from profroma: ', new_proforma_amount)
    if new_proforma_amount <= 0:
        print('--removing proforma from DB--')
        cursor.execute('DELETE FROM documents WHERE id = %s', proforma_db['id'])
    else:
        print('--updating profroma amount--')
        cursor.execute('UPDATE documents SET amount = %s WHERE id = %s', (new_proforma_amount, proforma_db['id']))
    
    conn.commit()

    return 0