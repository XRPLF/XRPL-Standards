#!/usr/bin/env python3
"""
Check and assign XLS numbers for a pull request.

Run by .github/workflows/assign-xls-number.yml in two modes:

  inspect  Read the PR's added files. Set the outputs `has_drafts` and
           `has_self_assigned`. If the PR adds a numbered XLS directory above
           LAST_MANUAL_XLS_NUMBER without the reservation label, write a
           warning comment body to $RUNNER_TEMP/self-assigned-comment.md.

  assign   Pick the next free XLS number for each added draft directory, while
           it skips numbers that other open PRs reserved. Write the comment body
           to $RUNNER_TEMP/assignment-comment.md.

The assign mode reads reservations first and the base branch's directories
second, both from the API. A PR that merges between the two reads is then in
one of them, so its number is never handed out again.

The script uses only the standard library. It reads the PR from
GITHUB_EVENT_PATH and calls the GitHub REST API with GITHUB_TOKEN. File names
come from the API, never from the shell, so a crafted path cannot run code.
"""

import json
import os
import re
import sys
from collections.abc import Iterable
from pathlib import Path
from urllib import parse, request

# Numbers up to this value were assigned by hand before CI assigned numbers.
LAST_MANUAL_XLS_NUMBER = 95
MIN_XLS_NUMBER = LAST_MANUAL_XLS_NUMBER + 1

# Label that marks a PR whose XLS number is reserved. Must match the label in
# the repository and in assign-xls-number.yml.
RESERVED_LABEL = "has XLS number"

BOT_LOGIN = "github-actions[bot]"

# Directory names are restricted to safe characters so that they can go into
# Markdown and GITHUB_OUTPUT without escaping.
_NAME = r"[A-Za-z0-9._-]+"
DRAFT_README = re.compile(rf"^((?:XLS|xls)-draft-{_NAME})/README\.md$")
NUMBERED_README = re.compile(rf"^((?:XLS|xls)-(\d{{4}})-{_NAME})/README\.md$")
EXISTING_DIR = re.compile(r"^XLS-(\d{4})-")
NUMBER_MARKER = re.compile(r"<!--\s*XLS_NUMBER:(\d+)\s*-->")


class GitHubError(RuntimeError):
    pass


def github_get(path: str, token: str, params: dict | None = None):
    """GET a GitHub REST API path and return the parsed JSON.

    Raises GitHubError on any failure. A failed lookup must stop the run: if it
    returned empty data, the script could hand out a number that is reserved.
    """
    url = f"https://api.github.com{path}"
    if params:
        url = f"{url}?{parse.urlencode(params)}"
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "xrpl-standards-xls-number-bot",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        with request.urlopen(request.Request(url, headers=headers), timeout=30) as r:
            return json.load(r)
    except Exception as exc:
        raise GitHubError(f"GET {url} failed: {exc}") from exc


def github_get_all(path: str, token: str, params: dict | None = None) -> list:
    """GET every page of a list endpoint."""
    items: list = []
    page = 1
    while True:
        batch = github_get(path, token, {**(params or {}), "per_page": 100, "page": page})
        items.extend(batch)
        if len(batch) < 100:
            return items
        page += 1


def existing_xls_numbers(entries: Iterable[dict]) -> set[int]:
    """Return the numbers of the XLS-NNNN-* directories in a contents listing."""
    numbers = set()
    for entry in entries:
        match = EXISTING_DIR.match(entry.get("name") or "")
        if match and entry.get("type") == "dir":
            numbers.add(int(match.group(1)))
    return numbers


def get_existing_xls_numbers(repo: str, token: str, ref: str) -> set[int]:
    """Return the XLS numbers in the root of `ref`, read now from the API."""
    return existing_xls_numbers(github_get(f"/repos/{repo}/contents/", token, {"ref": ref}))


def get_next_xls_number(used: set[int]) -> int:
    """Return the lowest unused number that is at least MIN_XLS_NUMBER."""
    num = MIN_XLS_NUMBER
    while num in used:
        num += 1
    return num


def find_draft_dirs(added_files: list[str]) -> list[str]:
    """Return the sorted draft directories whose README.md was added."""
    return sorted({m.group(1) for f in added_files if (m := DRAFT_README.match(f))})


def find_numbered_dirs(added_files: list[str]) -> list[tuple[str, int]]:
    """Return (directory, number) for added numbered XLSes above the manual range.

    These are either self-assigned or drafts that were already renamed.
    """
    found = set()
    for f in added_files:
        m = NUMBERED_README.match(f)
        if m and int(m.group(2)) > LAST_MANUAL_XLS_NUMBER:
            found.add((m.group(1), int(m.group(2))))
    return sorted(found)


def numbered_dir_name(draft_dir: str, number: int) -> str:
    """XLS-draft-my-feature -> XLS-0123-my-feature."""
    return re.sub(r"^(?:XLS|xls)-draft-", f"XLS-{number:04d}-", draft_dir)


def numbers_in_comments(comments: list[dict]) -> set[int]:
    """Return the XLS numbers in the bot's reservation markers."""
    numbers = set()
    for c in comments:
        if (c.get("user") or {}).get("login") == BOT_LOGIN:
            numbers.update(int(n) for n in NUMBER_MARKER.findall(c.get("body") or ""))
    return numbers


def get_reserved_numbers(repo: str, token: str, current_pr: int) -> tuple[set[int], set[int]]:
    """Return (numbers reserved by other open PRs, numbers reserved by this PR)."""
    others: set[int] = set()
    mine: set[int] = set()
    issues = github_get_all(
        f"/repos/{repo}/issues", token, {"state": "open", "labels": RESERVED_LABEL}
    )
    for issue in issues:
        if "pull_request" not in issue:
            continue
        comments = github_get_all(f"/repos/{repo}/issues/{issue['number']}/comments", token)
        nums = numbers_in_comments(comments)
        (mine if issue["number"] == current_pr else others).update(nums)
    # This PR can also have a reservation comment before it has the label.
    if not mine:
        mine = numbers_in_comments(
            github_get_all(f"/repos/{repo}/issues/{current_pr}/comments", token)
        )
    return others, mine


def plan_assignments(
    drafts: list[str], used: set[int], mine: set[int]
) -> list[tuple[str, int, str]]:
    """Return (draft, number, new name) per draft.

    The PR keeps its own earlier reservations first, in order, then takes new
    free numbers.
    """
    used = set(used)
    reuse = sorted(mine)
    result = []
    for draft in drafts:
        number = reuse.pop(0) if reuse else get_next_xls_number(used)
        used.add(number)
        result.append((draft, number, numbered_dir_name(draft, number)))
    return result


def self_assigned_comment(entries: list[tuple[str, int]]) -> str:
    rows = "\n".join(f"| `{d}` | {n} |" for d, n in entries)
    return f"""## ⚠️ Self-Assigned XLS Number Warning

This PR adds a new XLS directory with a **self-assigned number**. XLS numbers should be assigned by CI using the `XLS-draft-*` naming convention.

| Directory | Self-Assigned Number |
|-----------|----------------------|
{rows}

### What to do

Rename your directory to use the draft convention instead (for example, `XLS-draft-my-feature`). CI assigns an XLS number after a maintainer approves the PR.

---
*This warning was automatically generated.*
"""


def assignment_comment(
    assignments: list[tuple[str, int, str]], renamed: list[tuple[str, int]] = ()
) -> str:
    """Comment body for new assignments.

    `renamed` holds directories that this PR already renamed to a number it
    reserved. They keep their markers so the reservation stays until merge.
    """
    rows = "\n".join(
        [f"| `{d}` | **XLS-{n}** | `{new}` |" for d, n, new in assignments]
        + [f"| (renamed) | **XLS-{n}** | `{d}` |" for d, n in renamed]
    )
    reserved = sorted({n for _, n, _ in assignments} | {n for _, n in renamed})
    markers = "\n".join(f"<!-- XLS_NUMBER:{n} -->" for n in reserved)
    numbers = ", ".join(str(n) for _, n, _ in assignments)
    return f"""## 🎫 XLS Number Assignment

This PR adds a new XLS draft. CI reserved the next available XLS number, based on the existing XLS directories and the numbers that other open PRs reserved:

| Draft Directory | Assigned Number | New Directory Name |
|-----------------|-----------------|--------------------|
{rows}

### Next Steps for XLS Editors

Before merging this PR:

1. **Rename the directory** to the new name in the table.
2. **Update the preamble** in the README.md:
   - Set `xls:` to the assigned number ({numbers})
   - Set `status:` to `Draft`

---
*This comment was automatically generated.*

{markers}
"""


def set_output(name: str, value: str) -> None:
    path = os.environ.get("GITHUB_OUTPUT")
    if path:
        with open(path, "a", encoding="utf-8") as f:
            f.write(f"{name}={value}\n")
    print(f"output {name}={value}")


def write_body(filename: str, body: str) -> None:
    path = Path(os.environ.get("RUNNER_TEMP", ".")) / filename
    path.write_text(body, encoding="utf-8")
    print(f"Wrote {path}")


def main(argv: list[str]) -> int:
    if len(argv) != 2 or argv[1] not in ("inspect", "assign"):
        print("usage: assign_xls_number.py inspect|assign", file=sys.stderr)
        return 2
    mode = argv[1]

    token = os.environ.get("GITHUB_TOKEN", "")
    repo = os.environ["GITHUB_REPOSITORY"]
    with open(os.environ["GITHUB_EVENT_PATH"], encoding="utf-8") as f:
        pr = json.load(f)["pull_request"]

    files = github_get_all(f"/repos/{repo}/pulls/{pr['number']}/files", token)
    added = [f["filename"] for f in files if f.get("status") == "added"]
    drafts = find_draft_dirs(added)

    if mode == "inspect":
        set_output("has_drafts", "true" if drafts else "false")
        labels = {label["name"] for label in pr.get("labels", [])}
        self_assigned = [] if RESERVED_LABEL in labels else find_numbered_dirs(added)
        set_output("has_self_assigned", "true" if self_assigned else "false")
        if self_assigned:
            write_body("self-assigned-comment.md", self_assigned_comment(self_assigned))
        return 0

    if not drafts:
        print("No XLS draft directories added.")
        return 0
    if not token:
        print("GITHUB_TOKEN is required to read reserved numbers.", file=sys.stderr)
        return 1

    # Order matters: reservations first, then the base branch. See the
    # module docstring.
    others, mine = get_reserved_numbers(repo, token, pr["number"])
    existing = get_existing_xls_numbers(repo, token, pr["base"]["ref"])
    # Numbered directories that this PR adds, for example a draft that an
    # editor already renamed. Their numbers are taken.
    numbered = find_numbered_dirs(added)
    taken_here = {n for _, n in numbered}
    renamed = [(d, n) for d, n in numbered if n in mine]
    print(f"Existing numbers: {len(existing)}, highest {max(existing, default=0)}")
    print(f"Reserved by other open PRs: {sorted(others)}")
    print(f"Reserved by this PR: {sorted(mine)}")
    print(f"Numbered directories added by this PR: {numbered}")

    used = existing | others | taken_here
    assignments = plan_assignments(drafts, used, mine - used)
    for draft, number, new in assignments:
        print(f"  {draft} -> {new} (XLS-{number:04d})")
    write_body("assignment-comment.md", assignment_comment(assignments, renamed))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
