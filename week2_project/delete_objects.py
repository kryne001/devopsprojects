import requests
import os

OKTA_DOMAIN = os.environ.get("OKTA_DOMAIN")
OKTA_TOKEN = os.environ.get("OKTA_TOKEN")

HEADERS = {
    "Authorization": f"SSWS {OKTA_TOKEN}",
    "Accept": "application/json",
    "Content-Type": "application/json"
}

def remove_objects(okta_id):
    url = f"https://{OKTA_DOMAIN}/api/v1/users/{okta_id}"
    response = requests.delete(url, headers=HEADERS)
    response.raise_for_status()

def main():

