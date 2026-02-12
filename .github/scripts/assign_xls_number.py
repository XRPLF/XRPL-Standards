#!/usr/bin/env python3
"""
Assign XLS numbers to new draft XLS proposals.

This script scans the repository for existing XLS directories,
determines the next available XLS number, and outputs it for use
in GitHub Actions.
"""

import os
import re
import sys
import json
from pathlib import Path
from urllib import error, parse, request


def get_existing_xls_numbers(repo_root: Path) -> set[int]:
    """
    Scan the repository root for existing XLS directories and extract their numbers.

    Returns a set of integers representing all claimed XLS numbers.
    """
    xls_pattern = re.compile(r"^XLS-(\d{4})-")
    numbers = set()

    for item in repo_root.iterdir():
        if item.is_dir():
            match = xls_pattern.match(item.name)
            if match:
                numbers.add(int(match.group(1)))

    return numbers


# Minimum XLS number to assign (to avoid filling old historical gaps)
MIN_XLS_NUMBER = 96


def get_next_xls_number(existing_numbers: set[int]) -> int:
    """
    Determine the next available XLS number.

    Returns the first unused number >= MIN_XLS_NUMBER.
    """
    if not existing_numbers:
        return MIN_XLS_NUMBER

    # Find the first available number starting from MIN_XLS_NUMBER
    max_num = max(existing_numbers)
    for num in range(MIN_XLS_NUMBER, max_num + 2):
        if num not in existing_numbers:
            return num

    return max_num + 1


def find_draft_xls_files(changed_files: list[str]) -> list[str]:
    """
    Filter changed files to find new XLS draft README files.

    Args:
        changed_files: List of file paths that were added in the PR

    Returns:
        List of draft XLS directory names (e.g., ["XLS-draft-my-feature"])
    """
    draft_pattern = re.compile(r"^((XLS|xls)-draft[^/]+)/README\.md$")
    drafts = []

    for file_path in changed_files:
        match = draft_pattern.match(file_path)
        if match:
            drafts.append(match.group(1))

    return list(set(drafts))  # Remove duplicates


def github_api_request(path: str, token: str, params: dict | None = None):
    """Small helper to call the GitHub REST API.

    Returns parsed JSON or an empty list/dict on failure.
    """

    base_url = "https://api.github.com"
    url = f"{base_url}{path}"
    if params:
        query = parse.urlencode(params)
        url = f"{url}?{query}"

    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "xrpl-standards-xls-number-bot",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = request.Request(url, headers=headers)

    try:
        with request.urlopen(req) as resp:
            data = resp.read()
        return json.loads(data.decode("utf-8"))
    except error.HTTPError as e:
        print(f"Warning: GitHub API HTTP error {e.code} for {url}: {e.reason}")
    except error.URLError as e:
        print(f"Warning: GitHub API URL error for {url}: {e.reason}")

    # On any failure, return an empty list so callers can treat it as "no data".
    return []


def extract_xls_number_from_comments(
    owner: str, repo: str, token: str, issue_number: int
) -> int | None:
    """Extract reserved XLS number for an issue/PR from bot comments.

    Looks for a marker of the form: <!-- XLS_NUMBER:0123 --> in comments
    authored by github-actions[bot].
    """

    page = 1
    while True:
        comments = github_api_request(
            f"/repos/{owner}/{repo}/issues/{issue_number}/comments",
            token,
            {"per_page": 100, "page": page},
        )

        if not comments:
            break

        for comment in comments:
            if comment.get("user", {}).get("login") != "github-actions[bot]":
                continue
            body = comment.get("body") or ""
            match = re.search(r"<!--\s*XLS_NUMBER:(\\d+)\s*-->", body)
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    continue

        if len(comments) < 100:
            break
        page += 1

    return None


def get_reserved_xls_numbers_from_prs(
    token: str, repo: str, current_pr_number: int | None
) -> tuple[set[int], int | None]:
    """Find XLS numbers reserved by open PRs with the 'has-xls-number' label.

    Returns a tuple of (set of reserved numbers, number assigned to the current PR
    if any).
    """

    if not token or not repo:
        # Without a token or repo, we cannot query the API; treat as no reservations.
        return set(), None

    if "/" not in repo:
        return set(), None

    owner, repo_name = repo.split("/", 1)

    reserved_numbers: set[int] = set()
    current_pr_assigned: int | None = None

    page = 1
    while True:
        issues = github_api_request(
            f"/repos/{owner}/{repo_name}/issues",
            token,
            {
                "state": "open",
                "labels": "has-xls-number",
                "per_page": 100,
                "page": page,
            },
        )

        if not issues:
            break

        for issue in issues:
            # Filter to PRs only
            if "pull_request" not in issue:
                continue

            issue_number = issue.get("number")
            num = extract_xls_number_from_comments(owner, repo_name, token, issue_number)
            if num is None:
                continue

            reserved_numbers.add(num)

            if current_pr_number is not None and issue_number == current_pr_number:
                current_pr_assigned = num

        if len(issues) < 100:
            break

        page += 1

    return reserved_numbers, current_pr_assigned


def main():
    """Main entry point for the script."""
    # Get repository root (parent of .github directory)
    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parent.parent

    # Get changed files from command line arguments or environment variable
    if len(sys.argv) > 1:
        changed_files = sys.argv[1:]
    else:
        # Try to get from environment variable (set by GitHub Actions)
        changed_files_env = os.environ.get("CHANGED_FILES", "")
        changed_files = changed_files_env.split() if changed_files_env else []

    # Helper to set GitHub output
    def set_github_output(name: str, value: str):
        github_output = os.environ.get("GITHUB_OUTPUT")
        if github_output:
            with open(github_output, "a") as f:
                f.write(f"{name}={value}\n")
        else:
            print(f"  {name}={value}")

    if not changed_files:
        print("No changed files provided.")
        set_github_output("has_drafts", "false")
        return

    # Find draft XLS files
    draft_dirs = find_draft_xls_files(changed_files)

    if not draft_dirs:
        print("No XLS draft files found in changed files.")
        set_github_output("has_drafts", "false")
        return

    # Discover reserved XLS numbers from other open PRs and from this PR (if any)
    github_token = os.environ.get("GITHUB_TOKEN", "")
    github_repo = os.environ.get("GITHUB_REPOSITORY", "")
    current_pr_number = None
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    if event_path and os.path.isfile(event_path):
        try:
            with open(event_path, "r", encoding="utf-8") as f:
                event = json.load(f)
            current_pr_number = event.get("pull_request", {}).get("number")
        except Exception as exc:  # pragma: no cover - defensive
            print(f"Warning: Failed to parse GITHUB_EVENT_PATH: {exc}")

    reserved_numbers, current_pr_assigned = get_reserved_xls_numbers_from_prs(
        github_token,
        github_repo,
        current_pr_number,
    )

    if reserved_numbers:
        print(f"Found {len(reserved_numbers)} XLS numbers reserved by open PRs.")

    # Get existing XLS numbers from the base branch
    existing_numbers = get_existing_xls_numbers(repo_root)
    print(f"Found {len(existing_numbers)} existing XLS numbers in the repository.")
    print(f"Highest existing number: {max(existing_numbers) if existing_numbers else 0}")

    all_numbers = existing_numbers | reserved_numbers

    assignments = []

    if current_pr_assigned is not None:
        print(
            f"Reusing previously reserved XLS number {current_pr_assigned:04d} for this PR."
        )
        next_number = current_pr_assigned
    else:
        next_number = get_next_xls_number(all_numbers)

    for draft_dir in sorted(draft_dirs):
        assigned_number = next_number
        all_numbers.add(assigned_number)
        new_dir_name = re.sub(r"^xls-draft-", f"xls-{assigned_number:04d}-", draft_dir.lower())
        assignments.append({
            "draft": draft_dir,
            "number": assigned_number,
            "new_name": new_dir_name,
        })
        # Calculate the next free number for any additional drafts
        next_number = get_next_xls_number(all_numbers)

    # Output results
    print("\n=== XLS Number Assignments ===")
    for assignment in assignments:
        draft = assignment['draft']
        new_name = assignment['new_name']
        num = assignment['number']
        print(f"  {draft} -> {new_name} (XLS-{num:04d})")

    # Set GitHub Actions outputs
    set_github_output("has_drafts", "true")
    set_github_output("assignments", str(assignments))

    # For single draft case, also output individual values for easy access
    if len(assignments) == 1:
        set_github_output("xls_number", f"{assignments[0]['number']}")
        set_github_output("draft_dir", assignments[0]['draft'])
        set_github_output("new_dir_name", assignments[0]['new_name'])


if __name__ == "__main__":
    main()
