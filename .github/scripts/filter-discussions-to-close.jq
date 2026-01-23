# Filter discussions that should be closed
# A discussion should be closed if:
# 1. It has a warning comment containing the unique marker
# 2. That warning comment was posted by the bot
# 3. That warning comment is older than WARNING_DAYS
# 4. The discussion hasn't been updated since the warning (or updates are also old)
#
# Input: GraphQL response with discussions data
# Arguments:
#   $warningCutoff - ISO 8601 timestamp for warning age threshold
#   $marker - Unique marker string to identify warning comments
#   $botLogin - GitHub login of the bot user
# Output: JSON objects (one per line) for discussions that should be closed

.data.repository.discussions.nodes[]

# Only process open discussions
| select(.closed == false)

# Store the discussion for later reference
| . as $discussion

# Find the most recent warning comment from the bot
# Note: We only look at the last 100 comments (fetched by the shell script).
# This is intentional - if there are 100+ comments after a warning, the discussion
# is clearly active and should not be closed.
| (
    (.comments.nodes // [])
    | map(
        select(.body | contains($marker))
        | select(.author.login == $botLogin)
      )
    | last
  ) as $warningComment

# Only proceed if a warning comment exists
| select($warningComment != null)

# Only proceed if the warning comment is old enough
| select($warningComment.createdAt <= $warningCutoff)

# Only proceed if the discussion hasn't been updated since the warning
| select($discussion.updatedAt < $warningComment.createdAt)

# Output as JSON
| @json
