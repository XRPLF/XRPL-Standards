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

# Process discussions to close (warned WARNING_DAYS+ days ago with no activity)
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
    echo "  Action: Would close and lock"

    # COMMENTED OUT FOR TESTING
    # echo "  Adding close comment..."
    # gh api graphql -f query='mutation($discussionId: ID!, $body: String!) { addDiscussionComment(input: {discussionId: $discussionId, body: $body}) { comment { id } } }' -f discussionId="$DISCUSSION_ID" -f body="$CLOSE_MESSAGE"

    # echo "  Closing discussion..."
    # gh api graphql -f query='mutation($discussionId: ID!) { closeDiscussion(input: {discussionId: $discussionId}) { discussion { id } } }' -f discussionId="$DISCUSSION_ID"

    # echo "  Locking discussion..."
    # gh api graphql -f query='mutation($discussionId: ID!) { lockLockable(input: {lockableId: $discussionId}) { lockedRecord { locked } } }' -f discussionId="$DISCUSSION_ID"

    echo ""
  fi
done

# Process discussions to warn (stale but not yet warned)
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
    echo "  Action: Would add warning comment"

    # COMMENTED OUT FOR TESTING
    # echo "  Adding warning comment..."
    # gh api graphql -f query='mutation($discussionId: ID!, $body: String!) { addDiscussionComment(input: {discussionId: $discussionId, body: $body}) { comment { id } } }' -f discussionId="$DISCUSSION_ID" -f body="$WARNING_MESSAGE"

    echo ""
  fi
done

echo "Done!"
