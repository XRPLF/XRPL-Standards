#!/usr/bin/env python3
"""
Close XLS Discussions - Closes and locks discussions linked in proposal-from fields.

This script is designed to run as part of a GitHub Action after an XLS is merged
into master, or manually via workflow_dispatch to scan all XLS folders.
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

# Add scripts directory to path for xls_parser import
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from xls_parser import extract_xls_metadata, find_xls_documents


def run_gh_command(args: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run a GitHub CLI command."""
    result = subprocess.run(["gh"] + args, capture_output=True, text=True, check=False)
    if check and result.returncode != 0:
        print(f"Error running gh command: {' '.join(args)}")
        print(f"stderr: {result.stderr}")
        raise subprocess.CalledProcessError(
            result.returncode, args, result.stdout, result.stderr
        )
    return result


def run_graphql_query(query: str, variables: dict) -> dict:
    """Run a GraphQL query using the GitHub CLI."""
    args = ["api", "graphql", "-f", f"query={query}"]
    for key, value in variables.items():
        args.extend(["-f", f"{key}={value}"])

    result = run_gh_command(args)
    return json.loads(result.stdout)


def extract_discussion_number(url: str) -> int | None:
    """Extract discussion number from a GitHub discussions URL."""
    # Match URLs like https://github.com/XRPLF/XRPL-Standards/discussions/123
    match = re.search(r"/discussions/(\d+)", url)
    if match:
        return int(match.group(1))
    return None


def get_discussion_info(owner: str, repo: str, number: int) -> dict | None:
    """Get discussion info by number."""
    query = """
    query($owner: String!, $repo: String!, $number: Int!) {
      repository(owner: $owner, name: $repo) {
        discussion(number: $number) {
          id
          title
          closed
          locked
          url
        }
      }
    }
    """
    try:
        result = run_graphql_query(
            query, {"owner": owner, "repo": repo, "number": str(number)}
        )
        return result.get("data", {}).get("repository", {}).get("discussion")
    except subprocess.CalledProcessError:
        return None


def close_and_lock_discussion(
    discussion_id: str,
    close_message: str,
    xls_folder: str,
    dry_run: bool = False,
) -> bool:
    """Close and lock a discussion with a comment."""
    # Customize message with XLS reference
    message = f"{close_message}\n\nSee: [{xls_folder}](/{xls_folder}/README.md)"

    if dry_run:
        print("  [DRY RUN] Would add comment, close, and lock discussion")
        return True

    # Add comment
    print("  Adding close comment...")
    comment_query = """
    mutation($discussionId: ID!, $body: String!) {
      addDiscussionComment(input: {discussionId: $discussionId, body: $body}) {
        comment { id }
      }
    }
    """
    try:
        run_graphql_query(
            comment_query, {"discussionId": discussion_id, "body": message}
        )
    except subprocess.CalledProcessError as e:
        print(f"  Error adding comment: {e}")
        return False

    # Close discussion
    print("  Closing discussion...")
    close_query = """
    mutation($discussionId: ID!) {
      closeDiscussion(input: {discussionId: $discussionId}) {
        discussion { id }
      }
    }
    """
    try:
        run_graphql_query(close_query, {"discussionId": discussion_id})
    except subprocess.CalledProcessError as e:
        print(f"  Error closing discussion: {e}")
        return False

    # Lock discussion
    print("  Locking discussion...")
    lock_query = """
    mutation($discussionId: ID!) {
      lockLockable(input: {lockableId: $discussionId}) {
        lockedRecord { locked }
      }
    }
    """
    try:
        run_graphql_query(lock_query, {"discussionId": discussion_id})
    except subprocess.CalledProcessError as e:
        print(f"  Warning: Failed to lock discussion: {e}")
        # Don't return False - closing succeeded

    return True


def get_xls_folders_from_changed_files(changed_files: str) -> list[str]:
    """Extract XLS folder names from a space-separated list of changed files."""
    if not changed_files:
        return []

    xls_folders = set()
    for file_path in changed_files.split():
        # Match full XLS folder names such as XLS-0001-xls-process/README.md
        match = re.match(r"(XLS-\d+[d]?-[^/]+)/README\.md", file_path)
        if match:
            xls_folders.add(match.group(1))

    return list(xls_folders)


def main():
    """Main entry point."""
    # Get environment variables
    owner = os.environ.get("GITHUB_REPOSITORY_OWNER", "")
    repo = os.environ.get("GITHUB_REPOSITORY_NAME", "")
    close_message = os.environ.get(
        "CLOSE_MESSAGE", "This discussion has been merged into an XLS."
    )
    scan_all = os.environ.get("SCAN_ALL", "false").lower() == "true"
    dry_run = os.environ.get("DRY_RUN", "false").lower() == "true"
    changed_files = os.environ.get("CHANGED_FILES", "")

    if not owner or not repo:
        print(
            "Error: GITHUB_REPOSITORY_OWNER and " "GITHUB_REPOSITORY_NAME must be set"
        )
        sys.exit(1)

    print(f"Repository: {owner}/{repo}")
    print(f"Scan all: {scan_all}")
    print(f"Dry run: {dry_run}")
    print()

    root_dir = Path(".")

    # Determine which XLS folders to process
    if scan_all:
        print("Scanning all XLS folders...")
        docs = find_xls_documents(root_dir)
    else:
        print("Scanning changed XLS folders...")
        changed_folders = get_xls_folders_from_changed_files(changed_files)
        print(f"Changed folders: {changed_folders}")

        if not changed_folders:
            print("No XLS folders changed. Nothing to do.")
            return

        docs = []
        for folder_name in changed_folders:
            readme_path = root_dir / folder_name / "README.md"
            if readme_path.exists():
                with open(readme_path, "r", encoding="utf-8") as f:
                    content = f.read()
                doc = extract_xls_metadata(content, folder_name)
                if doc:
                    docs.append(doc)

    if not docs:
        print("No XLS documents found.")
        return

    print(f"\nFound {len(docs)} XLS document(s) to process")
    print()

    # Process each document
    closed_count = 0
    skipped_count = 0
    error_count = 0

    for doc in docs:
        if not doc.proposal_from:
            print(f"{doc.folder}: No proposal-from field, skipping")
            skipped_count += 1
            continue

        discussion_number = extract_discussion_number(doc.proposal_from)
        if not discussion_number:
            print(
                f"{doc.folder}: Could not extract discussion number "
                f"from '{doc.proposal_from}', skipping"
            )
            skipped_count += 1
            continue

        print(f"{doc.folder}: Processing discussion #{discussion_number}")

        # Get discussion info
        discussion = get_discussion_info(owner, repo, discussion_number)
        if not discussion:
            print(f"  Warning: Could not find discussion #{discussion_number}")
            error_count += 1
            continue

        print(f"  Title: {discussion['title']}")
        print(f"  URL: {discussion['url']}")

        if discussion["closed"]:
            print("  Already closed, skipping")
            skipped_count += 1
            continue

        # Close and lock
        if close_and_lock_discussion(
            discussion["id"], close_message, doc.folder, dry_run=dry_run
        ):
            print("  ✓ Successfully closed and locked")
            closed_count += 1
        else:
            print("  ✗ Failed to close/lock")
            error_count += 1

        print()

    # Summary
    print("=" * 50)
    print("Summary:")
    print(f"  Closed: {closed_count}")
    print(f"  Skipped: {skipped_count}")
    print(f"  Errors: {error_count}")

    if error_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
