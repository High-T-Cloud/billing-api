import utils
from os import environ

def lambda_handler(event, context):
    print('--Event: ', event)
    
    conn = utils.get_db_connection(environ['DB_ENDPOINT'], environ['DB_NAME'], environ['SECRET_ARN'])
    cursor = conn.cursor()

    # Role required - App User
    
    # function logic
    cursor.execute('SELECT * FROM services')
    services = cursor.fetchall()
    
    return services
        
