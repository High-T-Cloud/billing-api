import os.path
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.cloud import channel
from google.type.date_pb2 import Date


# If modifying these scopes, delete the file token.json.
# os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'  # **UNCOMMENT THIS IF MAKING A NEW TOKEN WITH NEW SCOPES**

SCOPES = ['https://www.googleapis.com/auth/apps.order',
          'https://www.googleapis.com/auth/apps.reports.usage.readonly']
ACCOUNT_ID = 'C049ub8g4'  # reseller ID
# Report name for invoice by customer
REPORT_NAME = 'accounts/C049ub8g4/reports/27105fz1'

JOB_NAME = 'accounts/C049ub8g4/reportJobs/60db1cb4-95bf-49a0-bde2-36aa9c3214e5'


def get_creds():
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token-tomer.json'):
        creds = Credentials.from_authorized_user_file(
            'token-tomer.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print('--refreshing token--')
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'creds.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token-tomer.json', 'w') as token:
            token.write(creds.to_json())
        print('--created new token file--')
    if creds == None:
        raise Exception('--failed to create credentails--')

    print('--got creds--')
    return creds


def list_subscriptions(creds):
    service = build('reseller', 'v1', credentials=creds)
    print('--created service--')

    res = service.subscriptions().list(maxResults=10, customerId='C012m17qd').execute()
    print(res)


def run_report(client):
    # client = channel.CloudChannelServiceClient(credentials=creds)
    # client = channel.CloudChannelReportsServiceClient(credentials=creds)

    # Test the client

    res = client.run_report_job(channel.RunReportJobRequest(name=REPORT_NAME, date_range=channel.DateRange(
        invoice_start_date=Date(year=2022, month=10, day=1), invoice_end_date=Date(year=2022, month=10, day=31))))
    # return res
    print('--operation result: ', res.result())
    print('--operation name: ', res.operation.name)
    print('--operation done: ', res.operation.done)


def get_report(client):
    """
    get a result from a finished report
    """
    res = client.fetch_report_results(
        channel.FetchReportResultsRequest(report_job=JOB_NAME))
    return res


def do_report(client, date_range):
    """
    run a report and return it's result after fetching it
    """
    # Run the report
    res = client.run_report_job(channel.RunReportJobRequest(
        name=REPORT_NAME, date_range=date_range))
    job_res = res.result()
    report_job = job_res.report_job
    job_name = report_job.name
    op_name = res.operation.name
    print('--operation done: ', res.operation.done)
    # Fetch report result
    print('--fetching report result for report job ', job_name)
    res = client.fetch_report_results(channel.FetchReportResultsRequest(report_job=job_name))    
    return res    


def format_report(report_result, mode='json'):
    """
    report result hiarchy
    response -> __iter__ -> values [
        'business_entity', 'business_entity_display_name', customer', 'customer_org_display_name', 'customer_domain', 'customer_cost'
    ] -> string_value / money_value
    """    

    if mode == 'csv':
        data = 'customer_id,customer_name,domain,entity,currency_code,cost\n'
        for row in report_result:
            # Format money cost to 2 decimal float
            cost = row.values[5].money_value.units + (row.values[5].money_value.nanos / 1000000000)
            customer_name = row.values[3].string_value.replace('"', '""')
            customer_name = f'"{customer_name}"'
            new_line = f'{row.values[2].string_value},{customer_name},{row.values[4].string_value},{row.values[0].string_value},{row.values[5].money_value.currency_code},'            
            new_line += str(cost)
            data += new_line
            data += '\n'
    else:
        data = []
        for row in report_result:
            print('---row values--\n', row.values)
            row_data = {
                'customer_id': row.values[2].string_value,
                'customer_name': row.values[3].string_value,
                'domain': row.values[4].string_value,
                'entity': row.values[0].string_value,
                'currency_code': row.values[5].money_value.currency_code
            }
            # format the money cost to 2 decimal float
            row_data['cost'] = row.values[5].money_value.units + (row.values[5].money_value.nanos / 1000000000)
            data.append(row_data)
    return data


creds = get_creds()
# client = channel.CloudChannelReportsServiceClient(credentials=creds)

# # start_date = Date(year=2022, month=12, day=1)
# # end_date = Date(year=2022, month=12, day=31)
# # date_range = channel.DateRange(invoice_start_date=start_date, invoice_end_date=end_date)

# # client = channel.CloudChannelServiceClient(credentials=creds)
# report = get_report(client)
# report_data = format_report(report, mode='csv')

# with open('rep.csv', 'w', encoding='utf-16') as f:
#     f.write(report_data)
# print('-done-')

