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
# - DRY_RUN: Set to "true" to only print what would happen without making changes (optional)

# Validate required environment variables
required_env_vars=(STALE_DAYS WARNING_DAYS WARNING_MESSAGE CLOSE_MESSAGE GITHUB_REPOSITORY_OWNER GITHUB_REPOSITORY_NAME GH_TOKEN)
for var in "${required_env_vars[@]}"; do
  if [ -z "${!var}" ]; then
    echo "Error: required environment variable ${var} is not set or empty." >&2
    exit 1
  fi
done

# Calculate cutoff dates
SECONDS_IN_DAY=86400

# Use epoch seconds and support both GNU date (-d) and BSD/macOS date (-r)
NOW_EPOCH=$(date -u +%s)
STALE_CUTOFF_EPOCH=$((NOW_EPOCH - STALE_DAYS * SECONDS_IN_DAY))
CLOSE_CUTOFF_EPOCH=$((NOW_EPOCH - (STALE_DAYS + WARNING_DAYS) * SECONDS_IN_DAY))

if date -u -d "@0" '+%Y-%m-%dT%H:%M:%SZ' >/dev/null 2>&1; then
  # GNU date
  STALE_CUTOFF=$(date -u -d "@$STALE_CUTOFF_EPOCH" '+%Y-%m-%dT%H:%M:%SZ')
  CLOSE_CUTOFF=$(date -u -d "@$CLOSE_CUTOFF_EPOCH" '+%Y-%m-%dT%H:%M:%SZ')
elif date -u -r 0 '+%Y-%m-%dT%H:%M:%SZ' >/dev/null 2>&1; then
  # BSD/macOS date
  STALE_CUTOFF=$(date -u -r "$STALE_CUTOFF_EPOCH" '+%Y-%m-%dT%H:%M:%SZ')
  CLOSE_CUTOFF=$(date -u -r "$CLOSE_CUTOFF_EPOCH" '+%Y-%m-%dT%H:%M:%SZ')
else
  echo "Error: unsupported 'date' implementation; cannot compute cutoff dates." >&2
  exit 1
fi
echo "Stale cutoff (for warnings): $STALE_CUTOFF"
echo "Close cutoff (for closing): $CLOSE_CUTOFF"

if [ "$DRY_RUN" = "true" ]; then
  echo ""
  echo "*** DRY RUN MODE - No actual changes will be made ***"
fi

# Debug: Check token permissions
echo ""
echo "Checking GitHub token permissions..."
gh api /repos/$GITHUB_REPOSITORY_OWNER/$GITHUB_REPOSITORY_NAME --jq '.permissions' || echo "Could not fetch repo permissions"

# Get the bot's login name for author verification
echo ""
echo "Fetching bot login name..."
BOT_LOGIN=$(gh api /user --jq '.login')
if [ -z "$BOT_LOGIN" ]; then
  echo "Error: Could not fetch bot login name." >&2
  exit 1
fi
echo "Bot login: $BOT_LOGIN"

# Fetch all discussions using GitHub GraphQL API with pagination
echo ""
echo "Fetching discussions..."
CURSOR="null"
HAS_NEXT_PAGE="true"
PAGE_COUNT=0

# Initialize empty discussions array
echo '{"data":{"repository":{"discussions":{"nodes":[]}}}}' > discussions.json

while [ "$HAS_NEXT_PAGE" = "true" ]; do
  PAGE_COUNT=$((PAGE_COUNT + 1))
  echo "Fetching page $PAGE_COUNT..."

  # Fetch one page of discussions
  # Note: Fetches last 100 comments per discussion, which is sufficient since
  # bot warning comments are recent and we only need to find the last one.
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
            comments(last: 100) {
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
  ' -f owner="$GITHUB_REPOSITORY_OWNER" -f repo="$GITHUB_REPOSITORY_NAME" -f cursor="$CURSOR" > discussions_page.json

  # Extract pagination info
  HAS_NEXT_PAGE=$(jq -r '.data.repository.discussions.pageInfo.hasNextPage' discussions_page.json)
  CURSOR=$(jq -r '.data.repository.discussions.pageInfo.endCursor' discussions_page.json)

  # Merge this page's discussions into the main array
  jq -s '.[0].data.repository.discussions.nodes += .[1].data.repository.discussions.nodes | .[0]' discussions.json discussions_page.json > discussions_temp.json
  mv discussions_temp.json discussions.json

  # If cursor is null, we've reached the end
  if [ "$CURSOR" = "null" ]; then
    HAS_NEXT_PAGE="false"
  fi
done

# Clean up temporary file
rm -f discussions_page.json

TOTAL_DISCUSSIONS=$(jq '.data.repository.discussions.nodes | length' discussions.json)
echo "Fetched $TOTAL_DISCUSSIONS discussions across $PAGE_COUNT page(s)"

# Process discussions to close
# A discussion should be closed if:
# 1. It has a warning comment containing the configured WARNING_MESSAGE
# 2. That warning comment was posted by the bot
# 3. That warning comment is older than WARNING_DAYS
# 4. The discussion hasn't been updated since the warning (or updates are also old)
echo ""
echo "=== Discussions to close - warned ${WARNING_DAYS}+ days ago with no activity ==="
cat discussions.json | jq -r --arg warningCutoff "$CLOSE_CUTOFF" --arg warningMessage "$WARNING_MESSAGE" --arg botLogin "$BOT_LOGIN" '.data.repository.discussions.nodes[] | select(.closed == false) | . as $discussion | ((.comments.nodes // []) | map(select(.body | contains($warningMessage)) | select(.author.login == $botLogin)) | last) as $warningComment | select($warningComment != null) | select($warningComment.createdAt < $warningCutoff) | select($discussion.updatedAt <= $warningComment.createdAt) | @json' | while IFS= read -r discussion; do
  if [ -n "$discussion" ]; then
    DISCUSSION_ID=$(echo "$discussion" | jq -r '.id')
    DISCUSSION_NUMBER=$(echo "$discussion" | jq -r '.number')
    DISCUSSION_TITLE=$(echo "$discussion" | jq -r '.title')
    DISCUSSION_URL=$(echo "$discussion" | jq -r '.url')
    DISCUSSION_UPDATED=$(echo "$discussion" | jq -r '.updatedAt')

    echo "Discussion #$DISCUSSION_NUMBER: $DISCUSSION_TITLE"
    echo "  URL: $DISCUSSION_URL"
    echo "  Last updated: $DISCUSSION_UPDATED"
    if [ "$DRY_RUN" = "true" ]; then
      echo "  Action: Would close and lock (DRY RUN)"
    else
      echo "  Action: Closing and locking"

      # Step 1: Add a closing comment explaining why the discussion was closed
      echo "  Adding close comment..."
      if ! gh api graphql -f query='mutation($discussionId: ID!, $body: String!) { addDiscussionComment(input: {discussionId: $discussionId, body: $body}) { comment { id } } }' -f discussionId="$DISCUSSION_ID" -f body="$CLOSE_MESSAGE"; then
        echo "  Error: Failed to add close comment for discussion #$DISCUSSION_NUMBER. Skipping close/lock for this discussion."
        echo ""
        continue
      fi

      # Step 2: Close the discussion
      echo "  Closing discussion..."
      if ! gh api graphql -f query='mutation($discussionId: ID!) { closeDiscussion(input: {discussionId: $discussionId}) { discussion { id } } }' -f discussionId="$DISCUSSION_ID"; then
        echo "  Error: Failed to close discussion #$DISCUSSION_NUMBER after adding close comment. Skipping lock for this discussion."
        echo ""
        continue
      fi

      # Step 3: Lock the discussion to prevent further comments
      echo "  Locking discussion..."
      if ! gh api graphql -f query='mutation($discussionId: ID!) { lockLockable(input: {lockableId: $discussionId}) { lockedRecord { locked } } }' -f discussionId="$DISCUSSION_ID"; then
        echo "  Warning: Failed to lock discussion #$DISCUSSION_NUMBER after closing it. Discussion remains closed but unlocked."
      fi
    fi

    echo ""
  fi
done

# Process discussions to warn
# A discussion should be warned if:
# 1. It hasn't been updated in STALE_DAYS
# 2. Either:
#    a. It doesn't have a warning comment from the bot yet, OR
#    b. It has a warning from the bot but was updated after that warning (user responded, so we warn again)
echo ""
echo "=== Discussions to warn - stale for ${STALE_DAYS}+ days, not yet warned ==="
cat discussions.json | jq -r --arg staleCutoff "$STALE_CUTOFF" --arg warningMessage "$WARNING_MESSAGE" --arg botLogin "$BOT_LOGIN" '.data.repository.discussions.nodes[] | select(.closed == false) | select(.updatedAt < $staleCutoff) | . as $discussion | ((.comments.nodes // []) | map(select(.body | contains($warningMessage)) | select(.author.login == $botLogin)) | last) as $warningComment | select($warningComment == null or $discussion.updatedAt > $warningComment.createdAt) | @json' | while IFS= read -r discussion; do
  if [ -n "$discussion" ]; then
    DISCUSSION_ID=$(echo "$discussion" | jq -r '.id')
    DISCUSSION_NUMBER=$(echo "$discussion" | jq -r '.number')
    DISCUSSION_TITLE=$(echo "$discussion" | jq -r '.title')
    DISCUSSION_URL=$(echo "$discussion" | jq -r '.url')
    DISCUSSION_UPDATED=$(echo "$discussion" | jq -r '.updatedAt')

    echo "Discussion #$DISCUSSION_NUMBER: $DISCUSSION_TITLE"
    echo "  URL: $DISCUSSION_URL"
    echo "  Last updated: $DISCUSSION_UPDATED"
    if [ "$DRY_RUN" = "true" ]; then
      echo "  Action: Would add warning comment (DRY RUN)"
    else
      echo "  Action: Adding warning comment"

      # Add a warning comment to the discussion
      echo "  Adding warning comment..."
      gh api graphql -f query='mutation($discussionId: ID!, $body: String!) { addDiscussionComment(input: {discussionId: $discussionId, body: $body}) { comment { id } } }' -f discussionId="$DISCUSSION_ID" -f body="$WARNING_MESSAGE"
    fi

    echo ""
  fi
done

echo "Done!"
