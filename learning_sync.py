#!/usr/bin/env python

from dotenv import load_dotenv
import os
import requests
from sqlalchemy import create_engine
from sqlalchemy.sql import text

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

moodle_data = conn.execute('SELECT id, email, idnumber, institution FROM mdl_user WHERE auth="oidc";')
moodle_map = {x[1].lower(): (x[0], x[2], x[3]) for x in moodle_data}


for email, (dbid, dbempl, dbinstit) in moodle_map.items():
    if email in users:
        if users[email]['employee_id'] and dbempl != users[email]['employee_id']:
            print('Updating Moodle: set {} employee ID to {}'.format(email, users[email]['employee_id']))
            statement = text('UPDATE mdl_user SET idnumber = :employee_id WHERE id = :row_id')
            conn.execute(statement, employee_id=users[email]['employee_id'], row_id=dbid)
        if 'org_data' in users[email] and 'units' in users[email]['org_data']:
            institution = next( (x['name'] for x in reversed( users[email]['org_data']['units'] ) if x['unit_type'].startswith('Division')), None )
            if institution is not None and institution != dbinstit:
                print('Updating Moodle: set {} institution from {} to {}'.format(email, dbinstit, institution))
                statement = text('UPDATE mdl_user SET institution = :institution WHERE id = :row_id')
                conn.execute(statement, institution=institution, row_id=dbid)


conn.close()
