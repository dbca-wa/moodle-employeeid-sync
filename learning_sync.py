from dotenv import load_dotenv
import os
import requests
from sqlalchemy import create_engine

load_dotenv()

it_assets_auth = (
    os.environ['IT_ASSETS_USER_EMAIL'],
    os.environ['IT_ASSETS_USER_PW'],
)

users_json = requests.get(os.environ['IT_ASSETS_API_URL'], auth=it_assets_auth).json()
users = {x['email'].lower(): x for x in users_json['objects']}

database_url = os.environ['DATABASE_URL']
engine = create_engine(database_url)
conn = engine.connect()
moodle_data = conn.execute('SELECT id, email, idnumber FROM mdl_user WHERE auth="oidc";')
moodle_map = {x[1].lower(): (x[0], x[2]) for x in moodle_data}

for email, (dbid, dbempl) in moodle_map.items():
    if email in users and users[email]['employee_id'] and dbempl != users[email]['employee_id']:
        print('Updating Moodle: set {} employee ID to {}'.format(email, users[email]['employee_id']))
        conn.execute('UPDATE mdl_user SET idnumber="{}" WHERE id={};'.format(users[email]['employee_id'], dbid))

conn.close()
