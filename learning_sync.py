#!/usr/bin/env python

from dotenv import load_dotenv
import os
import requests
from sqlalchemy import create_engine
from sqlalchemy.sql import text

load_dotenv()

it_assets_auth = (
    os.environ["IT_ASSETS_USER"],
    os.environ["IT_ASSETS_USER_PW"],
)

print("Querying IT Assets database for user data")
resp = requests.get(os.environ["IT_ASSETS_API_URL"], auth=it_assets_auth)
resp.raise_for_status()
users_json = resp.json()
users = {user["email"].lower(): user for user in users_json}

print("Querying LMS database for user data")
database_url = os.environ["DATABASE_URL"]
engine = create_engine(database_url)
conn = engine.connect()
moodle_data = conn.execute(
    'SELECT id, email, idnumber, institution, department, city, country FROM mdl_user WHERE auth="oidc";'
)
moodle_map = {x[1].lower(): (x[0], x[2], x[3], x[4], x[5], x[6]) for x in moodle_data}

for email, (dbid, dbempl, dbinstit, dbdepart, dbcity, dbcountry) in moodle_map.items():
    if email in users:
        if users[email]["employee_id"] and dbempl != users[email]["employee_id"]:
            print(
                "Updating Moodle: set {} employee ID to {}".format(
                    email, users[email]["employee_id"]
                )
            )
            statement = text(
                "UPDATE mdl_user SET idnumber = :employee_id WHERE id = :row_id"
            )
            conn.execute(
                statement, employee_id=users[email]["employee_id"], row_id=dbid
            )
        if "org_data" in users[email] and "units" in users[email]["org_data"]:
            department = next(
                (
                    x["name"]
                    for x in reversed(users[email]["org_data"]["units"])
                    if x["unit_type"].startswith("Department")
                ),
                None,
            )
            institution = next(
                (
                    x["name"]
                    for x in reversed(users[email]["org_data"]["units"])
                    if x["unit_type"].startswith("Division")
                ),
                None,
            )
            city = next(
                (
                    x["location__name"]
                    for x in reversed(users[email]["org_data"]["units"])
                    if x["unit_type"].startswith("Division")
                ),
                None,
            )
            if institution is not None and institution != dbinstit:
                print(
                    "Updating Moodle: set {} institution from {} to {}".format(
                        email, dbinstit, institution
                    )
                )
                statement = text(
                    "UPDATE mdl_user SET institution = :institution WHERE id = :row_id"
                )
                conn.execute(statement, institution=institution, row_id=dbid)
            if city is not None and city != dbcity:
                print(
                    "Updating Moodle: set {} city from {} to {}".format(
                        email, dbcity, city
                    )
                )
                statement = text("UPDATE mdl_user SET city = :city WHERE id = :row_id")
                conn.execute(statement, city=city, row_id=dbid)
            if department is not None and department != dbdepart:
                print(
                    "Updating Moodle: set {} department from {} to {}".format(
                        email, dbdepart, department
                    )
                )
                statement = text(
                    "UPDATE mdl_user SET department = :department WHERE id = :row_id"
                )
                conn.execute(statement, department=department, row_id=dbid)
            if dbcountry is None or dbcountry != "AU":
                country = "AU"
                print(
                    "Updating Moodle: set {} country from {} to {}".format(
                        email, dbcountry, country
                    )
                )
                statement = text(
                    "UPDATE mdl_user SET country = :country WHERE id = :row_id"
                )
                conn.execute(statement, country=country, row_id=dbid)

conn.close()
print("Sync completed")
