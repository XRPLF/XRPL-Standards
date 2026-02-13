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
from pathlib import Path


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

    # Get existing XLS numbers
    existing_numbers = get_existing_xls_numbers(repo_root)
    print(f"Found {len(existing_numbers)} existing XLS numbers.")
    print(f"Highest existing number: {max(existing_numbers) if existing_numbers else 0}")

    # Assign numbers to each draft
    next_number = get_next_xls_number(existing_numbers)
    assignments = []

    for draft_dir in sorted(draft_dirs):
        assigned_number = next_number
        new_dir_name = re.sub(r"^xls-draft-", f"xls-{assigned_number:04d}-", draft_dir.lower())
        assignments.append({
            "draft": draft_dir,
            "number": assigned_number,
            "new_name": new_dir_name,
        })
        next_number += 1

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
