import requests
import json
import gauth
import time

def get_auth_headers(token:dict)->dict:
    """
    return headers with access token
    `token`: dict containing the access token
    """

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token["access_token"]}'
    }
    print('--got token--')
    return headers


def do_report(auth):
    report_name = 'accounts/C049ub8g4/reports/27105fz1'
    url = 'https://cloudchannel.googleapis.com/v1/' + report_name + ':run'
    date_range = {
        'invoiceStartDate': {'year': 2023, 'month': 2, 'day': 1},
        'invoiceEndDate': {'year': 2023, 'month': 2, 'day': 28}
    }
    data = {
        'dateRange': date_range
    }
    res = requests.post(url, headers=auth, data=json.dumps(data))
    print(res.status_code)
    res = res.json()
    return res


def get_operation(auth, operation_name):    
    url = 'https://cloudchannel.googleapis.com/v1/' + operation_name
    res = requests.get(url, headers=auth)
    print(res.status_code)
    res = res.json()
    return res


def fetch_result(auth, job_name):    
    url = f'https://cloudchannel.googleapis.com/v1/{job_name}:fetchReportResults'
    res = requests.post(url, headers=auth)
    print(res.status_code)
    res = res.json()
    return res


def format_report(report, mode='json'):
    """
    format a report result `from fetch_result` into json or csv format
    report structure: response -> rows(list) -> values [ 'business_entity', 'business_entity_display_name', customer', 'customer_org_display_name', 'customer_domain', 'customer_cost']
    -> stringValue / moneyValue
    moneyValue structure: {currencyCode, units(str), nanos(int)}
    return: dict / string in csv mode
    """
    output = None

    if mode == 'csv':
        output = 'customer_id,customer_name,domain,entity,currency_code,cost\n'
        for row in report['rows']:
            # Format money cost to 2 decimal float
            if 'nanos' not in row['values'][5]['moneyValue']:
                cost = int(row['values'][5]['moneyValue']['units'])
            else:
                cost = int(row['values'][5]['moneyValue']['units']) + (row['values'][5]['moneyValue']['nanos'] / 1000000000)
            customer_name = row['values'][3]['stringValue'].replace('"', '""')
            customer_name = f'"{customer_name}"'
            new_line = f"{row['values'][2]['stringValue']},{customer_name},{row['values'][4]['stringValue']},{row['values'][0]['stringValue']},{row['values'][5]['moneyValue']['currencyCode']},"            
            new_line += str(cost)
            output += new_line
            output += '\n'
    else:
        output = []
        for row in report['rows']:            
            new_row = {
                'customer_id': row['values'][2]['stringValue'],
                'customer_name': row['values'][3]['stringValue'],
                'domain': row['values'][4]['stringValue'],
                'entity': row['values'][0]['stringValue'],
                'currency_code': row['values'][5]['moneyValue']['currencyCode']
            }
            # format the money cost to 2 decimal float
            if 'nanos' not in row['values'][5]['moneyValue']:
                new_row['cost'] = int(row['values'][5]['moneyValue']['units'])
            else:
                new_row['cost'] = int(row['values'][5]['moneyValue']['units']) + (row['values'][5]['moneyValue']['nanos'] / 1000000000)
                        
            output.append(new_row)

    return output



token = gauth.get_token_from_file('./assets/token.json')
headers = get_auth_headers(token)

res = do_report(headers)
rep_name = res['name']
time.sleep(2)
res = get_operation(headers, rep_name)
job_name = res['response']['reportJob']['name']
print(job_name)
res = fetch_result(headers, job_name)
out = format_report(res, 'csv')

print(out)
with open('assets/test_invoice.csv', 'w', encoding='utf-16') as f:
    f.write(out)
print('-----done-------')
