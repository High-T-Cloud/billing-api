import boto3
from os import environ
import json
import utils


def lambda_handler(event, context):
    print('--Event: ', event)

    # Auth required - App User
    
    conn = utils.get_db_connection(environ['DB_ENDPOINT'], environ['DB_NAME'], environ['SECRET_ARN'])
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM providers')
    providers = cursor.fetchall()
    
    return {'body': providers}
