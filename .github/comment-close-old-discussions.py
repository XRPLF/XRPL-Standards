import os
import requests
from datetime import datetime, UTC

GITHUB_TOKEN = os.environ['GITHUB_TOKEN']
REPO = os.environ['GITHUB_REPOSITORY']
OWNER, NAME = REPO.split('/')
API_URL = "https://api.github.com/graphql"
HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

STALE_LABEL = "stale"
STALE_COMMENT = "This discussion has been marked as stale due to inactivity for 90 days. If there is no further activity, it will be closed in 14 days."
TIME_TIL_STALE = 90  # days
TIME_TIL_CLOSE = 14  # days


def graphql(query, variables=None):
    resp = requests.post(API_URL, headers=HEADERS, json={"query": query, "variables": variables or {}})
    if resp.status_code != 200 or 'errors' in resp.json():
        print(f"GraphQL error: {resp.text}")
        return None
    return resp.json()['data']


def get_discussions():
    discussions = []
    cursor = None
    while True:
        query = """
        query($owner: String!, $name: String!, $cursor: String) {
          repository(owner: $owner, name: $name) {
            discussions(first: 50, after: $cursor) {
              pageInfo { hasNextPage endCursor }
              nodes {
                number
                updatedAt
                labels(first: 10) { nodes { name } }
              }
            }
          }
        }
        """
        variables = {"owner": OWNER, "name": NAME, "cursor": cursor}
        data = graphql(query, variables)
        if not data:
            break
        nodes = data['repository']['discussions']['nodes']
        discussions.extend(nodes)
        page_info = data['repository']['discussions']['pageInfo']
        if not page_info['hasNextPage']:
            break
        cursor = page_info['endCursor']
    return discussions


def get_comments(discussion_number):
    query = """
    query($owner: String!, $name: String!, $number: Int!) {
      repository(owner: $owner, name: $name) {
        discussion(number: $number) {
          comments(first: 100) {
            nodes {
              body
              createdAt
            }
          }
        }
      }
    }
    """
    variables = {"owner": OWNER, "name": NAME, "number": discussion_number}
    data = graphql(query, variables)
    if not data:
        return []
    return data['repository']['discussion']['comments']['nodes']


# GitHub Discussions do not support adding labels via API for GitHub Apps/integrations.
def add_label(discussion_number, label):
    print(f"Skipping label '{label}' for discussion #{discussion_number} (not supported by API)")
    return


def get_discussion_node_id(discussion_number):
    query = """
    query($owner: String!, $name: String!, $number: Int!) {
      repository(owner: $owner, name: $name) {
        discussion(number: $number) { id }
      }
    }
    """
    variables = {"owner": OWNER, "name": NAME, "number": discussion_number}
    data = graphql(query, variables)
    if not data:
        return None
    return data['repository']['discussion']['id']


def get_label_node_id(label_name):
    query = """
    query($owner: String!, $name: String!, $label: String!) {
      repository(owner: $owner, name: $name) {
        label(name: $label) { id }
      }
    }
    """
    variables = {"owner": OWNER, "name": NAME, "label": label_name}
    data = graphql(query, variables)
    if not data or not data['repository']['label']:
        return None
    return data['repository']['label']['id']


def post_comment(discussion_number, body):
    print(f"Posting comment to discussion #{discussion_number}")
    query = """
    mutation($input: AddDiscussionCommentInput!) {
      addDiscussionComment(input: $input) {
        clientMutationId
      }
    }
    """
    node_id = get_discussion_node_id(discussion_number)
    if not node_id:
        print("Could not get node ID for discussion.")
        return
    variables = {"input": {"discussionId": node_id, "body": body}}
    graphql(query, variables)


def close_and_lock(discussion_number):
    print(f"Closing and locking discussion #{discussion_number}")
    query = """
    mutation($input: UpdateDiscussionInput!) {
      updateDiscussion(input: $input) {
        clientMutationId
      }
    }
    """
    node_id = get_discussion_node_id(discussion_number)
    if not node_id:
        print("Could not get node ID for discussion.")
        return
    variables = {"input": {"discussionId": node_id, "locked": True, "state": "CLOSED"}}
    graphql(query, variables)


def main():
    now = datetime.now(UTC)
    discussions = get_discussions()
    for d in discussions:
        number = d['number']
        labels = [label['name'] for label in d.get('labels', {}).get('nodes', [])]
        last_updated = datetime.strptime(d['updatedAt'], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
        comments = get_comments(number)
        stale_comment = next((c for c in comments if STALE_COMMENT in c['body']), None)

        # Mark as stale after 90 days
        if (now - last_updated).days >= TIME_TIL_STALE and STALE_LABEL not in labels:
            add_label(number, STALE_LABEL)
            post_comment(number, STALE_COMMENT)
            continue

        # Close and lock after 14 days of being stale
        if stale_comment:
            stale_time = datetime.strptime(stale_comment['createdAt'], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
            if (now - stale_time).days >= TIME_TIL_CLOSE:
                # Check for any comments after stale comment
                recent_comments = [c for c in comments if datetime.strptime(c['createdAt'], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC) > stale_time]
                if not recent_comments:
                    close_and_lock(number)
