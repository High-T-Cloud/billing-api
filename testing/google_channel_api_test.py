from google.cloud import channel
from google.oauth2 import service_account
import os

def main():
  # Set up credentials with user impersonation
  json_key_file = os.environ['GOOGLE_APPLICATION_CREDENTIALS']
  reseller_admin_user = os.environ['GOOGLE_RESELLER_ADMIN_USER']

  credentials = service_account.Credentials.from_service_account_file(
      json_key_file, scopes=["https://www.googleapis.com/auth/apps.order"])
  credentials_delegated = credentials.with_subject(reseller_admin_user)

  # Create the API client
  client = channel.CloudChannelServiceClient(credentials=credentials_delegated)

  # Test the client
  account_id = os.environ['GOOGLE_RESELLER_ACCOUNT_ID']
  request = channel.CheckCloudIdentityAccountsExistRequest(
      parent="accounts/" + account_id, domain="example.com")
  response = client.check_cloud_identity_accounts_exist(request)
  print("The API call worked!")

if __name__ == "__main__":
  main()