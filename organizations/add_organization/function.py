from os import environ
import boto3
import utils

def lambda_handler(event, context):
    print('--Event: ', event)
    
    conn = utils.get_db_connection(environ['DB_ENDPOINT'], environ['DB_NAME'], environ['SECRET_ARN'])
    cursor = conn.cursor()

    # Permission required: Master
    user_auth = utils.get_user_auth(cursor, event, organization_id=6, account_id=False)
    if user_auth != 3:
        conn.close()
        raise Exception('err-401: user access denied')        
    
    # build empty organization
    new_organization = {'name': None, 'business_id': None, 'phone': None, 'email': None,'morning_id': None, 'gapps_id': None, 'country': None, 'city': None, 'address_line': None}

    # merge empty organization with event organization
    for key in new_organization:
        if key in event and event[key] != '':
            new_organization[key] = event[key]                        
    print('--New Organization: ', new_organization)        

    cursor.execute('INSERT INTO organizations (name, business_id, phone, email, morning_id, gapps_id, country, city, address_line) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)', tuple(new_organization.values()))
    conn.commit()    

    # -- Create a new cognito group for the organizations --

    # find the ID of the new organizations
    cursor.execute('SELECT id FROM organizations WHERE name = %s', new_organization['name'])
    org_id = cursor.fetchone()['id']
    conn.close()
    print('--new org id: ', org_id)

    # Create cognito group
    cognito = boto3.client('cognito-idp')
    print('--created cognito client--')
    res = cognito.create_group(
        GroupName = 'org-' + str(org_id),
        UserPoolId = environ['USER_POOL_ID'],
        Description = 'User group for organization ' + new_organization['name']
    )

    print('--cognito response: ', res)
    
    return {'message': 'organization added'}