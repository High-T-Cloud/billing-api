import utils
from os import environ

def lambda_handler(event, context):
    conn = utils.get_db_connection(environ['DB_ENDPOINT'], environ['DB_NAME'], environ['SECRET_ARN'])
    cursor = conn.cursor()

    # TODO: Add Auth**

    # Create SQL statement
    formatted_query = '%' + event['query'] + '%'
    statement = 'SELECT documents.*, organizations.name AS organization FROM documents LEFT JOIN organizations ON organizations.id = owner '
    statement += 'WHERE name LIKE %s OR serial LIKE %s'
        
    print('--statement: ', statement)

    cursor.execute(statement, (formatted_query, formatted_query))
    docs = cursor.fetchall()

    conn.close()
    return {
        'body': docs
    }

