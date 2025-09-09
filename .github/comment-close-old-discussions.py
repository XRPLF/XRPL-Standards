import os
import requests
from datetime import datetime, UTC

GITHUB_TOKEN = os.environ['GITHUB_TOKEN']
REPO = os.environ['GITHUB_REPOSITORY']
API_URL = f"https://api.github.com/repos/{REPO}/discussions"
HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

STALE_LABEL = "stale"
STALE_COMMENT = "This discussion has been marked as stale due to inactivity for 90 days. If there is no further activity, it will be closed in 14 days."
TIME_TIL_STALE = 90  # days
TIME_TIL_CLOSE = 14  # days


def get_discussions():
    discussions = []
    page = 1
    while True:
        resp = requests.get(f"{API_URL}?per_page=100&page={page}", headers=HEADERS)
        if resp.status_code != 200:
            break
        data = resp.json()
        if not data:
            break
        discussions.extend(data)
        page += 1
    return discussions


def get_comments(discussion_number):
    url = f"{API_URL}/{discussion_number}/comments"
    resp = requests.get(url, headers=HEADERS)
    if resp.status_code != 200:
        return []
    return resp.json()


def safe_post(url, json_data):
    resp = requests.post(url, headers=HEADERS, json=json_data)
    if resp.status_code >= 400:
        print(f"POST {url} failed: {resp.status_code} {resp.text}")
    return resp


def safe_patch(url, json_data):
    resp = requests.patch(url, headers=HEADERS, json=json_data)
    if resp.status_code >= 400:
        print(f"PATCH {url} failed: {resp.status_code} {resp.text}")
    return resp


def add_label(discussion_number, label):
    print(f"Adding label '{label}' to discussion #{discussion_number}")
    url = f"https://api.github.com/repos/{REPO}/issues/{discussion_number}/labels"
    safe_post(url, {"labels": [label]})


def post_comment(discussion_number, body):
    print(f"Posting comment to discussion #{discussion_number}")
    url = f"{API_URL}/{discussion_number}/comments"
    safe_post(url, {"body": body})


def close_and_lock(discussion_number):
    print(f"Closing and locking discussion #{discussion_number}")
    url = f"{API_URL}/{discussion_number}"
    safe_patch(url, {"state": "closed", "locked": True})


def main():
    now = datetime.now(UTC)
    discussions = get_discussions()
    for d in discussions:
        number = d['number']
        labels = [label['name'] for label in d.get('labels', [])]
        last_updated = datetime.strptime(d['updated_at'], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
        comments = get_comments(number)
        stale_comment = next((c for c in comments if STALE_COMMENT in c['body']), None)

        # Mark as stale after 90 days
        if (now - last_updated).days >= TIME_TIL_STALE and STALE_LABEL not in labels:
            add_label(number, STALE_LABEL)
            post_comment(number, STALE_COMMENT)
            continue

        # Close and lock after 14 days of being stale
        if STALE_LABEL in labels and stale_comment:
            stale_time = datetime.strptime(stale_comment['created_at'], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
            if (now - stale_time).days >= TIME_TIL_CLOSE:
                # Check for any comments after stale comment
                recent_comments = [c for c in comments if datetime.strptime(c['created_at'], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC) > stale_time]
                if not recent_comments:
                    close_and_lock(number)


if __name__ == "__main__":
    main()
