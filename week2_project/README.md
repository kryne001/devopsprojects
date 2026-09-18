# Okta Stale Access Audit

Command line tool to review status of sOkta users and flag accounts that are currently in the staged phase, never signed in

## What it does

The script connects to the Okta API, pulls the full user list (handling pagination), and flags accounts that represent access risk:

- **Stale active users** — accounts with `ACTIVE` status whose last login is older than a configurable threshold (default: 90 days)
- **Active, never logged in** — accounts with `ACTIVE` status that have *never* logged in at all. This is a real edge case discovered during development: Okta's status field alone doesn't distinguish "went stale" from "was never actually used," and the two represent different risk profiles worth flagging separately.

The script also can activate test accounts and remove test accounts

- **Activate Accounts** - returns accounts that are set to `DEACTIVATED` then sets them to active and sets arbitrary password to make them active, called by --remove-staged
- **Remove Staged** - removes any accounts returned from running base call first, called by --remove-staged

Notes: **Activate Accounts** and **Remove Staged** are primarily used for testing purposes

## Setup

### Requirements
- Python 3.9+
- An Okta org with API access 
- An Okta API token 

### Install

```
python3 -m venv venv
source venv/bin/activate
python3 -m pip install requests python-dotenv
```


### Configure credentials

Create a `.env` file in the project root:

```
OKTA_DOMAIN=your-org.okta.com
OKTA_TOKEN=your-api-token-here
```

Notes:
- `OKTA_DOMAIN` is the bare API domain — no `https://`, no trailing slash, and no `-admin` suffix (that's only for the admin console UI, not the API).
- **`.env` is gitignored** and should never be committed. Treat the token like a password — if it's ever exposed (committed, pasted somewhere public), revoke and regenerate it immediately in the Okta admin console.

## Usage

```
bash
python3 okta_api.py
```

### Flags

| Flag | Description |
|---|---|
| `--inactive-days N` | Days of inactivity before an active user is flagged as stale (default: 90) |
| `--output FILE` | Write flagged results to a JSON file |
| `--verbose` | Print status and last-login info for every user, not just flagged ones |
| `--activate AMOUNT` | Activate set amount of profiles
| `--remove-staged` | deactivates and deletes staged accounts

### Example

```
bash
python3 okta_api.py --inactive-days 60 --output results.json --verbose
```

## Known limitations

Documented honestly rather than glossed over:

- **Pagination is implemented but not fully exercised.** The script uses Okta's cursor-based pagination (`Link` header, `rel="next"`), looping until no further page exists. However, the free Okta Integrator sandbox caps out at 10 active users — well under a single page — so the multi-page code path could not be validated against real data at scale. The logic was verified by code review and by reasoning through Okta's documented pagination behavior; a production Okta org with hundreds or thousands of users would be the real test.
- **Deprovisioned users are excluded from `/api/v1/users` by default.** This is an Okta API behavior, not a script bug: the default users list silently omits `DEPROVISIONED` accounts. A full offboarding audit would need a separate call with an explicit `filter=status eq "DEPROVISIONED"` query to include them — worth knowing, since a naive audit could otherwise miss deprovisioned-but-not-deleted accounts entirely.
- **Okta's user lifecycle has real state-transition rules that affect tooling design.** A few discovered during development:
  - Deleting a user via the API requires **two sequential DELETE calls** — the first deactivates (moves to `DEPROVISIONED`), the second actually purges the record.
  - A deactivated user's profile becomes locked for edits (including credential changes) while in that state — attempts return `403 E0000038`.
  - Setting a password directly is only accepted in certain lifecycle states (e.g., `PROVISIONED`), not others (e.g., `DEPROVISIONED`) — sequencing matters.

These are the kinds of non-obvious, API-specific behaviors that only surface through hands-on testing, not just reading the happy-path documentation.

## Why this matters

Stale or unused active accounts are a common, real access-control risk — they represent standing access that isn't being monitored or justified by actual use, and are a frequent finding in real security/compliance audits. This script demonstrates the kind of lightweight, repeatable automation that turns a manual access review into something that can run on a schedule.
