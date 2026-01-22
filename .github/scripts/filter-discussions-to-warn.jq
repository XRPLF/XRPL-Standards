# Filter discussions that should receive a warning
# A discussion should be warned if:
# 1. It hasn't been updated in STALE_DAYS
# 2. Either:
#    a. It doesn't have a warning comment (with unique marker) from the bot yet, OR
#    b. It has a warning from the bot but was updated after that warning (user responded, so we warn again)
#
# Input: GraphQL response with discussions data
# Arguments:
#   $staleCutoff - ISO 8601 timestamp for staleness threshold
#   $marker - Unique marker string to identify warning comments
#   $botLogin - GitHub login of the bot user
# Output: JSON objects (one per line) for discussions that should be warned

.data.repository.discussions.nodes[]

# Only process open discussions
| select(.closed == false)

# Only process discussions that are stale (not updated recently)
| select(.updatedAt < $staleCutoff)

# Store the discussion for later reference
| . as $discussion

# Find the most recent warning comment from the bot
| (
    (.comments.nodes // [])
    | map(
        select(.body | contains($marker))
        | select(.author.login == $botLogin)
      )
    | last
  ) as $warningComment

# Only proceed if:
# - No warning comment exists yet, OR
# - Discussion was updated after the last warning (user responded)
| select(
    $warningComment == null
    or $discussion.updatedAt > $warningComment.createdAt
  )

# Output as JSON
| @json
