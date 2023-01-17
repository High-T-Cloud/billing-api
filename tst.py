import requests
import json


client = {
    'id': '37b520d5-a53b-4197-b351-6d35e409bd3e',
    'name': 'Abu musa',
    'emails': ['tomerzx@gmail.com']
}

income = [{
    # 'catalogNum': 'tst1',
    'description': 'paypal test',
    'quantity': 1,
    'price': 200,
    'currency': 'USD',
    'vatType': 1 # Check if can remove
}]

payment = [{
    'date': '2022-12-19',
    'type': 5,
    'price': 200,
    'currency': 'USD',
}]

req_body = {
    'type': 320,
    'description': 'test description',
    'lang': 'en',
    'currency': 'USD',
    'vatType': 1, # Check if can remove
    'client': client,
    'income': income,
    'payment': payment
}

# Morning consts
print('--getting morning token--')
token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.VUZndHRzQzN6Ym4vVG1YL2JFWEVjU2M3U2lYVEdveWJRVzQ4U0puQU5ac2ZBLzhZSERhVkpnS1FhMVNPTEZoMVBvSTF3ZXBPc2ZRckxZMUN3OWdURDJiWmtjOUYxVGFPZyttZW5vOGQ4d0Nid0g0Q1RZNHNFektUaWR3bFhDTnlHRFRCWTFjS3ZFRklsSzR1MVVCcndOWFlKUW4xMEkrRkpmd0pXd3Jsd3hTZE5nZjlQM1JwTHBLSUN2U3VWVmxEc25BQ2I3QmdiTktXaHk2R1FsdkZyRGwzS216bmpQcklNOVc4K1FTdloyS2ZmL2oxYUd1MVlEWUxUWjJqeEE5ajBPZmhUVnpJc20rNWJWS3A3R0dqSGIrTnR6VVZ5TXpZMWxucDNjVUFFSnJiWTh6MHoyMkNJTXNqVGpBRnJzUHFXbDlBTEMrNkJIK1A0WUFSWmtCVFNRPT0.x3JbKbCWhpQ8RTk2aaKOxMgD_E7gFiHObYO8W_toQGE'
url = 'https://sandbox.d.greeninvoice.co.il/api/v1/documents'
headers = {'Authorization': 'Bearer ' + token}
res = requests.post(url, headers=headers, data=json.dumps(req_body))
print('--res code: ', res.status_code)
print('--res content: ', res.content)
res = res.json()
print('--res: ', res)