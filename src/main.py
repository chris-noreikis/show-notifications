# This is a sample Python script.
import json
import os

import boto3
import tvdb_v4_official


s3 = boto3.resource('s3')
db_ptr = s3.Object('notifications-cn', 'db.json')


def get_secrets():
    secret_name = os.environ['SECRET_KEY_NAME']
    region_name = "us-east-1"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    get_secret_value_response = client.get_secret_value(
        SecretId=secret_name
    )

    # Decrypts secret using the associated KMS key.
    return json.loads(get_secret_value_response['SecretString'])


def get_db():
    return json.loads(
        db_ptr.get()['Body'].read().decode('utf-8')
    )


def save_db(last_aired_db):
    db_ptr.put(Body=json.dumps(last_aired_db))

def send_notification(subscribers, show):
    message = f"""\
    {show['name']}
    Next air date: {show['nextAired']}"""

    ses_client = boto3.client('ses')
    for subscriber in subscribers:
        ses_client.send_email(
            Source='notifications@chrisnoreikis.com',
            Destination={
                'ToAddresses': [subscriber],
            },
            Message={
                'Subject': {
                    'Data': f'New Season Alert: {show["name"]}',
                    'Charset': 'utf-8'
                },
                'Body': {
                    'Text': {
                        'Data': message,
                        'Charset': 'utf-8'
                    }
                }
            }
        )


def process_show_updates(db, secrets):
    tv_client = tvdb_v4_official.TVDB(secrets['API_KEY'], secrets['PIN'])

    for show in db['shows']:
        updated_show = tv_client.get_series_nextAired(show['id'])
        next_aired = updated_show['nextAired']
        if next_aired != "" and next_aired != show['lastAired']:
            show['lastAired'] = next_aired

            send_notification(show['subscribers'], updated_show)

    save_db(db)


def lambda_entrypoint(lambda_event, lambda_ctx):
    process_show_updates(
        get_db(),
        get_secrets()
    )