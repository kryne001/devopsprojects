import requests
import os

OKTA_DOMAIN = os.environ.get("OKTA_DOMAIN")
OKTA_TOKEN = os.environ.get("OKTA_TOKEN")

HEADERS = {
    "Authorization": f"SSWS {OKTA_TOKEN}",
    "Accept": "application/json",
    "Content-Type": "application/json"
}

def create_test_user(first_name, last_name, email):
    url = f"https://{OKTA_DOMAIN}/api/v1/users?activate=true"
    payload = {
        "profile": {
            "firstName": first_name,
            "lastName": last_name,
            "email": email,
            "login": email
        },
        "credentials": {
            "password": {"value": "TempPassword123!"}
        }
    }
    response = requests.post(url, headers=HEADERS, json=payload)
    response.raise_for_status()
    return response.json()

def main():
    for i in range(20, 251):  # create 250 test users to force multiple pages
        first = f"Test{i}"
        last = "User"
        email = f"test.user{i}@example.com"
        try:
            user = create_test_user(first, last, email)
            print(f"Created: {email}")
        except requests.exceptions.RequestException as e:
            print(f"Failed to create {email}: {e}")

if __name__ == "__main__":
    main()