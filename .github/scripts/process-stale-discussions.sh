#!/bin/bash
set -e

# This script processes stale discussions in a GitHub repository
# It warns discussions that haven't been updated in STALE_DAYS
# It closes discussions that were warned WARNING_DAYS ago with no activity

# Environment variables expected:
# - STALE_DAYS: Number of days without updates to consider a discussion stale
# - WARNING_DAYS: Number of days to wait after warning before closing
# - WARNING_MESSAGE: Message to post when warning
# - CLOSE_MESSAGE: Message to post when closing
# - GITHUB_REPOSITORY_OWNER: Owner of the repository
# - GITHUB_REPOSITORY_NAME: Name of the repository
# - GH_TOKEN: GitHub token for API access

# Calculate cutoff dates
SECONDS_IN_DAY=86400
STALE_CUTOFF=$(date -u -d "@$(($(date +%s) - STALE_DAYS * SECONDS_IN_DAY))" '+%Y-%m-%dT%H:%M:%SZ')
CLOSE_CUTOFF=$(date -u -d "@$(($(date +%s) - (STALE_DAYS + WARNING_DAYS) * SECONDS_IN_DAY))" '+%Y-%m-%dT%H:%M:%SZ')

echo "Stale cutoff (for warnings): $STALE_CUTOFF"
echo "Close cutoff (for closing): $CLOSE_CUTOFF"

# Debug: Check token permissions
echo ""
echo "Checking GitHub token permissions..."
gh api /repos/$GITHUB_REPOSITORY_OWNER/$GITHUB_REPOSITORY_NAME --jq '.permissions' || echo "Could not fetch repo permissions"

# Fetch discussions using GitHub GraphQL API
gh api graphql -f query='
  query($owner: String!, $repo: String!, $cursor: String) {
    repository(owner: $owner, name: $repo) {
      discussions(first: 100, after: $cursor, orderBy: {field: UPDATED_AT, direction: ASC}) {
        pageInfo {
          hasNextPage
          endCursor
        }
        nodes {
          id
          number
          title
          url
          createdAt
          updatedAt
          closed
          locked
          comments(last: 10) {
            nodes {
              body
              createdAt
              author {
                login
              }
            }
          }
        }
      }
    }
  }
' -f owner="$GITHUB_REPOSITORY_OWNER" -f repo="$GITHUB_REPOSITORY_NAME" > discussions.json

# Process discussions to close
# A discussion should be closed if:
# 1. It has a warning comment containing "will be closed in 30 days"
# 2. That warning comment is older than WARNING_DAYS
# 3. The discussion hasn't been updated since the warning (or updates are also old)
echo ""
echo "=== Discussions to close - warned ${WARNING_DAYS}+ days ago with no activity ==="
cat discussions.json | jq -r --arg warningCutoff "$CLOSE_CUTOFF" '.data.repository.discussions.nodes[] | select(.closed == false) | . as $discussion | ((.comments.nodes // []) | map(select(.body | contains("will be closed in 30 days"))) | last) as $warningComment | select($warningComment != null) | select($warningComment.createdAt < $warningCutoff) | select($discussion.updatedAt <= $warningComment.createdAt or $discussion.updatedAt < $warningCutoff) | @json' | while IFS= read -r discussion; do
  if [ -n "$discussion" ]; then
    DISCUSSION_ID=$(echo "$discussion" | jq -r '.id')
    DISCUSSION_NUMBER=$(echo "$discussion" | jq -r '.number')
    DISCUSSION_TITLE=$(echo "$discussion" | jq -r '.title')
    DISCUSSION_URL=$(echo "$discussion" | jq -r '.url')
    DISCUSSION_UPDATED=$(echo "$discussion" | jq -r '.updatedAt')

    echo "Discussion #$DISCUSSION_NUMBER: $DISCUSSION_TITLE"
    echo "  URL: $DISCUSSION_URL"
    echo "  Last updated: $DISCUSSION_UPDATED"
    echo "  Action: Closing and locking"

    # Step 1: Add a closing comment explaining why the discussion was closed
    echo "  Adding close comment..."
    gh api graphql -f query='mutation($discussionId: ID!, $body: String!) { addDiscussionComment(input: {discussionId: $discussionId, body: $body}) { comment { id } } }' -f discussionId="$DISCUSSION_ID" -f body="$CLOSE_MESSAGE"

    # Step 2: Close the discussion
    echo "  Closing discussion..."
    gh api graphql -f query='mutation($discussionId: ID!) { closeDiscussion(input: {discussionId: $discussionId}) { discussion { id } } }' -f discussionId="$DISCUSSION_ID"

    # Step 3: Lock the discussion to prevent further comments
    echo "  Locking discussion..."
    gh api graphql -f query='mutation($discussionId: ID!) { lockLockable(input: {lockableId: $discussionId}) { lockedRecord { locked } } }' -f discussionId="$DISCUSSION_ID"

    echo ""
  fi
done

# Process discussions to warn
# A discussion should be warned if:
# 1. It hasn't been updated in STALE_DAYS
# 2. Either:
#    a. It doesn't have a warning comment yet, OR
#    b. It has a warning but was updated after that warning (user responded, so we warn again)
echo ""
echo "=== Discussions to warn - stale for ${STALE_DAYS}+ days, not yet warned ==="
cat discussions.json | jq -r --arg staleCutoff "$STALE_CUTOFF" '.data.repository.discussions.nodes[] | select(.closed == false) | select(.updatedAt < $staleCutoff) | . as $discussion | ((.comments.nodes // []) | map(select(.body | contains("will be closed in 30 days"))) | last) as $warningComment | select($warningComment == null or $discussion.updatedAt > $warningComment.createdAt) | @json' | while IFS= read -r discussion; do
  if [ -n "$discussion" ]; then
    DISCUSSION_ID=$(echo "$discussion" | jq -r '.id')
    DISCUSSION_NUMBER=$(echo "$discussion" | jq -r '.number')
    DISCUSSION_TITLE=$(echo "$discussion" | jq -r '.title')
    DISCUSSION_URL=$(echo "$discussion" | jq -r '.url')
    DISCUSSION_UPDATED=$(echo "$discussion" | jq -r '.updatedAt')

    echo "Discussion #$DISCUSSION_NUMBER: $DISCUSSION_TITLE"
    echo "  URL: $DISCUSSION_URL"
    echo "  Last updated: $DISCUSSION_UPDATED"
    echo "  Action: Adding warning comment"

    # Add a warning comment to the discussion
    echo "  Adding warning comment..."
    gh api graphql -f query='mutation($discussionId: ID!, $body: String!) { addDiscussionComment(input: {discussionId: $discussionId, body: $body}) { comment { id } } }' -f discussionId="$DISCUSSION_ID" -f body="$WARNING_MESSAGE"

    echo ""
  fi
done

echo "Done!"
