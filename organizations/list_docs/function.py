import utils
import os

def lambda_handler(event, context):
    """
    get a list of documents releated to this organization
    """
    print('--event: ', event)
    conn = utils.get_db_connection(os.environ['DB_ENDPOINT'], os.environ['DB_NAME'], os.environ['SECRET_ARN'])
    cursor = conn.cursor()

    # Auth required: Master
    user_auth = utils.get_user_auth(cursor, event, organization_id=6, account_id=False)
    if user_auth < 3:
        conn.close()
        raise Exception('err-401: access denied')
    
    # Get docs
    cursor.execute('SELECT * FROM documents WHERE organization_id = %s', event['id'])
    docs = cursor.fetchall()

    # Format datetime data
    for doc in docs:
        if doc['due_date'] is not None:
            doc['due_date'] = doc['due_date'].isoformat()
        if doc['created_at'] is not None:
            doc['created_at'] = doc['created_at'].isoformat()

    conn.close()
    return docs
    
