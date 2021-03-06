import requests
import os
import json
import sys
import logging
import csv
import time

users = []
rows = {}
sources = []
my_sources = {}
page = 1
per_page = 100

DAYS_BACK = 7
start = time.time() - (86400*DAYS_BACK)

header = ["Sevco ID","Timestamp","Names","Emails","Password Change","Groups"]

if not os.environ.get("JWT"):
    raise Exception("Need API key in JWT environment variable.")
if not os.environ.get("ORG"):
    raise Exception("Need target org id in ORG environment variable.")

org = os.environ['ORG']
token = os.environ['JWT']

# Grab all available sources to create header
r = requests.get("https://dev.api.sevcolabs.com/v1/integration/source",
                 headers={ 'Authorization': token, 'X-Sevco-Target-Org': org})
r.raise_for_status()
sources = r.json()

# Grab all the integrations configured for an Org
r = requests.get("https://dev.api.sevcolabs.com/v1/integration/source/config",
                 headers={ 'Authorization': token, 'X-Sevco-Target-Org': org})
r.raise_for_status()
integrations = r.json()

# Build a dictionary to dynamically produce headers and pull each sources unique identifier
for integration in integrations:
    for source in sources:
        if source["id"] == integration["source_id"]:
            my_sources[source["display_name"]] = source["source_type"]

# Pull all the user information into a JSON structure
while True:
    r = requests.get("https://dev.api.sevcolabs.com/v1/asset/user",
                     headers={'Authorization': token, 'X-Sevco-Target-Org': org},
                     params={'start': start, 'per_page': per_page, 'page': page})

    r.raise_for_status()
    data = r.json()
    if len(data['items']) == 0: break

    users.extend(data['items'])
    page += 1

# Add all the customer sources to the header
header = header + list(my_sources.keys())

# Parse the user JSON file and populate the CSV
with open ('users.csv', 'w', newline='') as csvfile:
    fieldnames = header
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

    for user in users:
        row = []
        row.append(user['id'])
        row.append(user['timestamp'])

        if 'names' in user['attributes'].keys():
          row.append(user['attributes']['names']['value'])
        else:
            row.append("")

        if 'emails' in user['attributes'].keys():
            row.append(user['attributes']['emails']['value'])
        else:
            row.append("")

        if 'password_change_timestamp' in user['attributes'].keys():
            row.append(user['attributes']['password_change_timestamp']['value'])
        else:
            row.append("")
    
        if 'groups' in user['attributes'].keys():
            row.append(user['attributes']['groups']['value'])
        else:
            row.append("")

        for src in my_sources.values():
            if src in user['metadata']:
                row.append(list(user['metadata'][src].keys()))
            else:
                row.append("")

        for i, column in enumerate(header):
            rows[column] = str(row[i]).replace(", ","\n").replace("'","").replace("[","").replace("]","")

        writer.writerow(rows)
