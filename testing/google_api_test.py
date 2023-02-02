import os.path
import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.cloud import channel
from google.type.date_pb2 import Date


# If modifying these scopes, delete the file token.json.
os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'
SCOPES = ['https://www.googleapis.com/auth/apps.reports.usage.readonly']
SCOPES = ['https://www.googleapis.com/auth/apps.order']
SCOPES = ['https://www.googleapis.com/auth/apps.order', 'https://www.googleapis.com/auth/apps.reports.usage.readonly']
ACCOUNT_ID = 'C049ub8g4'  # reseller ID
CUSTOMER_ID = 'Ssnqm5FosgU043' # benisho customer id
REPORT_NAME = 'accounts/C049ub8g4/reports/27105fz1'

OP_NAME = 'operations/7d4e0069-236e-4ebf-bfab-0b0153f1f241'
JOB_NAME = 'accounts/C049ub8g4/reportJobs/7d4e0069-236e-4ebf-bfab-0b0153f1f241'




def get_creds():
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token-tomer.json'):
        creds = Credentials.from_authorized_user_file('token-tomer.json', SCOPES)
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


def get_service(creds):
    service = build('reseller', 'v1', credentials=creds)
    print('--created service--')
    return service


def get_channel(creds):
    # client = channel.CloudChannelServiceClient(credentials=creds)
    rclient = channel.CloudChannelReportsServiceClient(credentials=creds)

    # Test the client
        
    # res = rclient.run_report_job(channel.RunReportJobRequest(name=REPORT_NAME, date_range=channel.DateRange(invoice_start_date=Date(year=2022, month=11, day=10), invoice_end_date=Date(year=2022, month=11, day=12))))
    # print(res)    
    # result = res.result()
    # op = res.operation
    # print('--operation--')
    # print(op)
    # print('--res--')
    # print(result)
    # print('--triyng--')
    # print(result.response)

    res = rclient.fetch_report_results(channel.FetchReportResultsRequest(report_job=JOB_NAME))
    print(res)


# service = get_service()

# Call the Admin SDK Reseller API
creds = get_creds()
service = get_channel(creds)

# res = service.subscriptions().list(maxResults=10, customerId='C012m17qd').execute()
# print(res)
# print(type(res))
