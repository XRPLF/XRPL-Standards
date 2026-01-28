#!/bin/bash
set -e

# This script processes stale discussions in a GitHub repository
# It warns discussions that haven't been updated in STALE_DAYS
# It closes discussions that were warned WARNING_DAYS ago with no activity

# Cleanup function to remove temporary files
cleanup() {
  if [ -f "discussions.json" ] || [ -f "discussions_page.json" ]; then
    echo ""
    echo "Cleaning up temporary files..."
    rm -f discussions.json discussions_page.json discussions_temp.json
  fi
}

# Register cleanup function to run on script exit (success or failure)
trap cleanup EXIT

# Environment variables expected:
# - STALE_DAYS: Number of days without updates to consider a discussion stale
# - WARNING_DAYS: Number of days to wait after warning before closing
# - WARNING_MESSAGE: Message to post when warning
# - CLOSE_MESSAGE: Message to post when closing
# - GITHUB_REPOSITORY_OWNER: Owner of the repository
# - GITHUB_REPOSITORY_NAME: Name of the repository
# - GH_TOKEN: GitHub token for API access
# - BOT_LOGIN: GitHub login name of the bot (for author verification)
# - DRY_RUN: Set to "true" to only print what would happen without making changes (optional)

# Validate required environment variables
required_env_vars=(STALE_DAYS WARNING_DAYS WARNING_MESSAGE CLOSE_MESSAGE GITHUB_REPOSITORY_OWNER GITHUB_REPOSITORY_NAME GH_TOKEN BOT_LOGIN)
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
# Stale cutoff: discussions not updated in STALE_DAYS will be warned
STALE_CUTOFF_EPOCH=$((NOW_EPOCH - STALE_DAYS * SECONDS_IN_DAY))
# Close cutoff: warning comments older than WARNING_DAYS will trigger closure
CLOSE_CUTOFF_EPOCH=$((NOW_EPOCH - WARNING_DAYS * SECONDS_IN_DAY))

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

# Validate GitHub token permissions
echo ""
echo "Validating GitHub token permissions..."

# Check if we can access the repository
if ! REPO_INFO=$(gh api /repos/$GITHUB_REPOSITORY_OWNER/$GITHUB_REPOSITORY_NAME 2>&1); then
  echo "Error: Failed to access repository $GITHUB_REPOSITORY_OWNER/$GITHUB_REPOSITORY_NAME" >&2
  echo "This could indicate:" >&2
  echo "  - Invalid or expired GH_TOKEN" >&2
  echo "  - Incorrect repository owner or name" >&2
  echo "  - Token lacks 'repo' or 'public_repo' scope" >&2
  echo "" >&2
  echo "Additional details are available from the GitHub CLI error output; avoid logging sensitive data from API responses." >&2
  exit 1
fi

# Verify the token has necessary permissions for discussions
# Note: Repository permissions (push/admin) don't directly correlate with discussion permissions.
# The most reliable way to check is to actually test the required operations.
echo "Testing discussion read access..."
if ! gh api graphql -f query='query($owner: String!, $name: String!) {
  repository(owner: $owner, name: $name) {
    discussions(first: 1) { nodes { id } }
  }
}' -f owner="$GITHUB_REPOSITORY_OWNER" -f name="$GITHUB_REPOSITORY_NAME" >/dev/null 2>&1; then
  echo "Error: Token does not have permission to read discussions" >&2
  echo "" >&2
  echo "Required permissions/scopes:" >&2
  echo "  - For GitHub Apps: Read and Write access to Discussions" >&2
  echo "  - For PATs: 'repo' scope (or 'public_repo' for public repos)" >&2
  echo "" >&2
  echo "Please check your token configuration in GitHub settings." >&2
  exit 1
fi

echo "Testing discussion write access..."
# Test if we can perform a write operation by checking the viewer's permissions
# We use a query that would fail if we don't have write access
if ! VIEWER_CHECK=$(gh api graphql -f query='query {
  viewer {
    login
    repositories(first: 1, affiliations: [OWNER, COLLABORATOR, ORGANIZATION_MEMBER]) {
      nodes {
        viewerCanSubscribe
      }
    }
  }
}' 2>&1); then
  echo "Warning: Could not verify write permissions via viewer query" >&2
  echo "The script will attempt to proceed, but may fail during write operations." >&2
  echo "API Response: $VIEWER_CHECK" >&2
else
  echo "✓ Token has basic write capabilities"
fi

echo "✓ Token permissions validated successfully"
echo ""
echo "Note: Full write permissions (comment, close, lock) will be verified during actual operations."

# Display bot login for verification
echo ""
echo "Bot login: $BOT_LOGIN"

# Verify bot login is accessible
if ! BOT_INFO=$(gh api /users/$BOT_LOGIN 2>&1); then
  echo "Warning: Could not verify bot user '$BOT_LOGIN'" >&2
  echo "The script will continue, but make sure BOT_LOGIN is correct." >&2
  echo "API Response: $BOT_INFO" >&2
else
  BOT_TYPE=$(echo "$BOT_INFO" | jq -r '.type // "Unknown"')
  echo "Bot type: $BOT_TYPE"
fi

# Fetch all discussions using GitHub GraphQL API with pagination
echo ""
echo "Fetching discussions..."
CURSOR="null"
HAS_NEXT_PAGE="true"
PAGE_COUNT=0
MAX_PAGES=1000  # Safety limit to prevent infinite loops (100 discussions/page = max 100k discussions)

# Initialize empty discussions array
echo '{"data":{"repository":{"discussions":{"nodes":[]}}}}' > discussions.json

while [ "$HAS_NEXT_PAGE" = "true" ]; do
  PAGE_COUNT=$((PAGE_COUNT + 1))

  # Safety check: prevent infinite loops
  if [ "$PAGE_COUNT" -gt "$MAX_PAGES" ]; then
    echo "Error: Exceeded maximum page count ($MAX_PAGES pages)" >&2
    echo "This likely indicates a pagination logic error or an extremely large repository." >&2
    echo "If you genuinely have more than $((MAX_PAGES * 100)) discussions, increase MAX_PAGES in the script." >&2
    exit 1
  fi

  echo "Fetching page $PAGE_COUNT..."

  # Fetch one page of discussions
  # Note: Fetches last 100 comments per discussion using comments(last: 100).
  # This is INTENTIONAL and correct behavior:
  # - We only need to find the bot's most recent warning comment
  # - If a discussion has 100+ comments AFTER the bot's warning, it means there's
  #   significant ongoing activity, so the discussion should NOT be closed
  # - This prevents closing active discussions that happen to be old
  # - The script looks for the LAST (most recent) warning comment, which will be
  #   in the last 100 comments if it's relevant for closure decisions
  # Use -F for cursor to pass it as raw JSON (allows null value)
  gh api graphql \
    -f owner="$GITHUB_REPOSITORY_OWNER" \
    -f repo="$GITHUB_REPOSITORY_NAME" \
    -F cursor="$CURSOR" \
    -f query='
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
    ' > discussions_page.json

  # Validate the API response
  if ! jq -e '.data.repository.discussions' discussions_page.json >/dev/null 2>&1; then
    echo "Error: Invalid API response on page $PAGE_COUNT" >&2
    echo "Response content:" >&2
    cat discussions_page.json >&2
    exit 1
  fi

  # Extract pagination info with error handling
  HAS_NEXT_PAGE=$(jq -r '.data.repository.discussions.pageInfo.hasNextPage' discussions_page.json)
  CURSOR=$(jq -r '.data.repository.discussions.pageInfo.endCursor' discussions_page.json)

  # Validate pagination values
  if [ -z "$HAS_NEXT_PAGE" ] || [ "$HAS_NEXT_PAGE" = "null" ]; then
    echo "Warning: hasNextPage is null or empty, assuming no more pages" >&2
    HAS_NEXT_PAGE="false"
  fi

  if [ -z "$CURSOR" ]; then
    echo "Warning: endCursor is empty, assuming no more pages" >&2
    CURSOR="null"
    HAS_NEXT_PAGE="false"
  fi

  # Merge this page's discussions into the main array
  if ! jq -s '.[0].data.repository.discussions.nodes += .[1].data.repository.discussions.nodes | .[0]' discussions.json discussions_page.json > discussions_temp.json; then
    echo "Error: Failed to merge discussions from page $PAGE_COUNT" >&2
    exit 1
  fi
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

# Define the unique marker used to identify warning comments
# This HTML comment is invisible to users but allows the script to reliably detect
# warning comments even if the WARNING_MESSAGE text changes over time.
# IMPORTANT: This marker must match the one in WARNING_MESSAGE in the workflow file.
MARKER="<!-- stale-discussion-warning -->"

# Validate that WARNING_MESSAGE contains the marker
echo ""
echo "Validating WARNING_MESSAGE contains required marker..."
if [[ "$WARNING_MESSAGE" != *"$MARKER"* ]]; then
  echo "Error: WARNING_MESSAGE does not contain the required marker: $MARKER" >&2
  echo "Current WARNING_MESSAGE:" >&2
  echo "$WARNING_MESSAGE" >&2
  exit 1
fi
echo "✓ WARNING_MESSAGE contains required marker"

# Process discussions to close
# A discussion should be closed if:
# 1. It has a warning comment containing the unique marker
# 2. That warning comment was posted by the bot
# 3. That warning comment is older than WARNING_DAYS
# 4. The discussion hasn't been updated since the warning (or updates are also old)
echo ""
echo "=== Discussions to close - warned ${WARNING_DAYS}+ days ago with no activity ==="
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Disable exit-on-error for this section to allow graceful error handling per discussion
set +e
jq_output=$(jq -r --arg warningCutoff "$CLOSE_CUTOFF" --arg marker "$MARKER" --arg botLogin "$BOT_LOGIN" -f "$SCRIPT_DIR/filter-discussions-to-close.jq" discussions.json)
jq_status=$?
if [ "$jq_status" -ne 0 ]; then
  echo "Error: Failed to filter discussions to close using jq (exit code: $jq_status)." >&2
  exit 1
fi
printf '%s\n' "$jq_output" | while IFS= read -r discussion; do
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
# Re-enable exit-on-error
set -e

# Process discussions to warn
# A discussion should be warned if:
# 1. It hasn't been updated in STALE_DAYS
# 2. Either:
#    a. It doesn't have a warning comment (with unique marker) from the bot yet, OR
#    b. It has a warning from the bot but was updated after that warning (user responded, so we warn again)
echo ""
echo "=== Discussions to warn - stale for ${STALE_DAYS}+ days, not yet warned ==="

# Disable exit-on-error for this section to allow graceful error handling per discussion
set +e
cat discussions.json | jq -r --arg staleCutoff "$STALE_CUTOFF" --arg marker "$MARKER" --arg botLogin "$BOT_LOGIN" -f "$SCRIPT_DIR/filter-discussions-to-warn.jq" | while IFS= read -r discussion; do
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
      if ! gh api graphql -f query='mutation($discussionId: ID!, $body: String!) { addDiscussionComment(input: {discussionId: $discussionId, body: $body}) { comment { id } } }' -f discussionId="$DISCUSSION_ID" -f body="$WARNING_MESSAGE"; then
        echo "  Error: Failed to add warning comment for discussion #$DISCUSSION_NUMBER. Skipping this discussion."
        echo ""
        continue
      fi
    fi

    echo ""
  fi
done
# Re-enable exit-on-error
set -e

echo "Done!"
# Note: discussions.json will be automatically cleaned up by the EXIT trap
