import requests
import argparse
import json
import os
from datetime import datetime, timedelta, UTC

OKTA_DOMAIN = os.environ.get("OKTA_DOMAIN")  # e.g. "dev-12345.okta.com"
OKTA_TOKEN = os.environ.get("OKTA_API_TOKEN")  # never hardcode this

HEADERS = {
    "Authorization": f"SSWS {OKTA_TOKEN}",
    "Accept": "application/json"
}

def get_all_users():
    all_users = []
    url = f"https://{OKTA_DOMAIN}/api/v1/users"
    while url is not None:    
        response = requests.get(url, headers=HEADERS)
        all_users.extend(response.json())
        response.raise_for_status()
        if "next" in response.links:
            url = response.links["next"]["url"]
        else:
            url = None
    return response.json()

def get_user_app_links(user_id):
    url = f"https://{OKTA_DOMAIN}/api/v1/users/{user_id}/appLinks"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json()

def find_stale_active_users(users, inactive_days=90):
    flagged = []
    cutoff = datetime.now(UTC) - timedelta(days=inactive_days)

    for user in users:
        last_login = user.get("lastLogin")
        status = user.get("status")

        if status == "ACTIVE":
            if last_login is None:
                # Never logged in but active — arguably worse than stale
                flagged.append({
                    "user": user["profile"]["login"],
                    "last_login": None,
                    "reason": "active_never_logged_in"
                })
            else:
                last_login_date = datetime.strptime(last_login, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=UTC)
                if last_login_date < cutoff:
                    app_links = get_user_app_links(user["id"])
                    flagged.append({
                        "user": user["profile"]["login"],
                        "last_login": last_login,
                        "app_count": len(app_links),
                        "reason": f"inactive_{inactive_days}_days_with_active_apps"
                    })
    return flagged

def main():
    parser = argparse.ArgumentParser(description="Audit Okta users for stale access")
    parser.add_argument("--inactive-days", type=int, default=90, help="Days of inactivity to flag")
    parser.add_argument("--output", help="Optional path to write JSON results")
    parser.add_argument("--verbose", action="store_true", help="Print status of all users, not just flagged ones")
    args = parser.parse_args()

    if args.verbose:
        for user in users:
            print(user["profile"]["login"], user.get("status"), user.get("lastLogin"))

    if not OKTA_DOMAIN or not OKTA_TOKEN:
        print("Error: set OKTA_DOMAIN and OKTA_API_TOKEN environment variables")
        return

    try:
        users = get_all_users()
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to Okta: {e}")
        return

    flagged = find_stale_active_users(users, args.inactive_days)

    print(f"\n--- Flagged Users ({len(flagged)}) ---")
    for item in flagged:
        print(item)


    if args.output:
        with open(args.output, "w") as f:
            json.dump(flagged, f, indent=2)
        print(f"\nResults written to {args.output}")

if __name__ == "__main__":
    main()