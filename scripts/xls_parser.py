#!/usr/bin/env python3
"""
XLS Standards Parser - Extracts metadata from XLS markdown documents.

This module provides functionality to parse XLS (XRPL Standards) documents
and extract their metadata for use in documentation systems and validation.
"""

import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
import sys
from typing import List, Optional, Tuple


# Valid status values for XLS documents
VALID_STATUSES = [
    "Draft", "Final", "Living", "Deprecated", "Stagnant", "Withdrawn"
]

# Valid category values for XLS documents
VALID_CATEGORIES = ["Amendment", "System", "Ecosystem", "Meta"]


@dataclass
class XLSDocument:
    """Represents an XLS document with metadata."""

    number: str
    raw_number: int
    title: str
    description: str
    authors: List[Tuple[str, str]]  # Tuple of (author_name, author_link)
    folder: str
    filename: str
    status: str  # draft, final, stagnant, withdrawn, etc.
    category: str  # amendment, ecosystem, system, etc.
    created: str  # YYYY-MM-DD format
    proposal_from: Optional[str] = None  # Link to proposal discussion
    implementation: Optional[str] = None  # Link to implementation PR
    requires: Optional[str] = None  # XLS number(s) this depends on
    updated: Optional[str] = None  # YYYY-MM-DD format
    withdrawal_reason: Optional[str] = None  # Reason for withdrawal
    # Nested amendment patches (XLS-1 §4.4.4). For a patch, `xls` is its
    # dotted number (for example "65.1.2") and `source` its repo-relative path.
    xls: str = ""
    source: str = ""
    patches: List["XLSDocument"] = field(default_factory=list)
    amendment: str = ""  # Amendment name for a patch, e.g. "fixCleanup3_4_0"

    @property
    def is_patch(self) -> bool:
        return "." in self.xls

    @property
    def label(self) -> str:
        return f"XLS-{self.xls}" if self.is_patch else f"XLS-{self.number}"

    def to_dict(self):
        return asdict(self)


def patch_sort_key(doc: XLSDocument) -> Tuple[int, ...]:
    return tuple(int(part) for part in doc.xls.split(".") if part.isdigit())


_PREAMBLE_RE = re.compile(r"<pre>(.*?)</pre>", re.DOTALL)
_AUTHOR_EMAIL_RE = re.compile(r"^(.*?)\s*<\s*([^>]+?)\s*>$")
_AUTHOR_GITHUB_RE = re.compile(r"^(.*?)\s*\(@([^)]+)\)$")


def parse_preamble(content: str) -> dict:
    """Return the `key: value` pairs of the first <pre> block, keys lowercased.

    Raises:
        ValueError: If the content has no <pre> block.
    """
    match = _PREAMBLE_RE.search(content)
    if not match:
        raise ValueError("No <pre> preamble block found")
    fields = {}
    for line in match.group(1).splitlines():
        key, sep, value = line.partition(":")
        key = key.strip().lower()
        if sep and key and " " not in key and key not in fields:
            fields[key] = value.strip()
    return fields


def parse_author(author: str) -> Tuple[str, str]:
    """Split `Name <email>` or `Name (@handle)` into (name, link)."""
    author = author.strip()
    if match := _AUTHOR_EMAIL_RE.match(author):
        return match.group(1).strip(), f"mailto:{match.group(2)}"
    if match := _AUTHOR_GITHUB_RE.match(author):
        return match.group(1).strip(), f"https://github.com/{match.group(2).strip()}"
    return author, ""


def extract_xls_metadata(content: str, folder_name: str) -> XLSDocument:
    """Extract metadata from XLS markdown content.

    Args:
        content: The raw markdown content of the XLS document
        folder_name: Name of the folder containing the XLS document

    Raises:
        ValueError: If the content has no <pre> preamble block.
    """
    fields = parse_preamble(content)
    authors = fields.get("author") or fields.get("authors")

    xls_match = re.match(r"XLS-(\d+)", folder_name)
    number = xls_match.group(1) if xls_match else "000"

    return XLSDocument(
        number=number,
        raw_number=int(number),
        title=fields.get("title") or "Unknown Title",
        description=fields.get("description") or "No description available",
        authors=(
            [parse_author(a) for a in authors.split(",")]
            if authors
            else [("Unknown Author", "")]
        ),
        folder=folder_name,
        filename="README.md",
        status=fields.get("status") or "Unknown",
        category=fields.get("category") or "Unknown",
        created=fields.get("created") or "Unknown",
        proposal_from=fields.get("proposal-from") or None,
        implementation=fields.get("implementation") or None,
        requires=fields.get("requires") or None,
        updated=fields.get("updated") or None,
        withdrawal_reason=fields.get("withdrawal-reason") or None,
        xls=fields.get("xls", ""),
    )


def find_xls_documents(root_dir: Path) -> List[XLSDocument]:
    """Find and parse all XLS documents in the given directory.

    Args:
        root_dir: Root directory to search for XLS folders

    Returns:
        List of XLSDocument instances for all found documents

    Raises:
        Exception: If parsing fails for any document
    """
    xls_docs = []
    xls_folders = [
        d for d in root_dir.iterdir() if d.is_dir() and d.name.startswith("XLS-")
    ]

    for folder in xls_folders:
        readme_path = folder / "README.md"
        if readme_path.exists():
            try:
                with open(readme_path, "r", encoding="utf-8") as f:
                    content = f.read()

                doc = extract_xls_metadata(content, folder.name)
                doc.source = f"{folder.name}/README.md"
                doc.patches = find_patches(root_dir, folder.name)
                xls_docs.append(doc)
                print(f"Parsed: {folder.name} - {doc.title}")

            except Exception as e:
                print(f"Error processing {folder.name}: {e}")
                raise

    return xls_docs


def find_patches(root_dir: Path, folder: str) -> List[XLSDocument]:
    """Return the nested amendment patches under an XLS folder, in number order.

    Patches live one folder down (`XLS-0065-.../65.1/65.1.2-...md`), the same
    files `validate_xls_template.py --all` checks.
    """
    patches = []
    for path in sorted((root_dir / folder).glob("*/*.md")):
        doc = extract_xls_metadata(path.read_text(encoding="utf-8"), folder)
        doc.source = path.relative_to(root_dir).as_posix()
        patches.append(doc)
    return sorted(patches, key=patch_sort_key)


def validate_xls_preamble(doc: XLSDocument) -> List[str]:
    """Validate preamble metadata fields for a single XLS document.

    Args:
        doc: The XLSDocument to validate

    Returns:
        List of error messages (empty if validation passes)
    """
    errors = []

    # Required fields
    if not doc.title or doc.title == "Unknown Title":
        errors.append(f"{doc.folder}: Missing required field: title")

    if not doc.description or doc.description == "No description available":
        errors.append(f"{doc.folder}: Missing required field: description")

    if not doc.authors or doc.authors == [("Unknown Author", "")]:
        errors.append(f"{doc.folder}: Missing required field: author")
    elif any(not name for name, _ in doc.authors):
        errors.append(f"{doc.folder}: Author with missing name")
    elif any(link == "" for _, link in doc.authors):
        errors.append(f"{doc.folder}: Author with missing link")

    # Category validation
    if not doc.category or doc.category == "Unknown":
        errors.append(f"{doc.folder}: Missing required field: category")
    elif doc.category not in VALID_CATEGORIES:
        errors.append(
            f"{doc.folder}: Invalid category '{doc.category}'. "
            f"Must be one of: {', '.join(VALID_CATEGORIES)}"
        )

    # Status validation
    if not doc.status or doc.status == "Unknown":
        errors.append(f"{doc.folder}: Missing required field: status")
    elif doc.status not in VALID_STATUSES:
        errors.append(
            f"{doc.folder}: Invalid status '{doc.status}'. "
            f"Must be one of: {', '.join(VALID_STATUSES)}"
        )

    # Created date validation
    if not doc.created or doc.created == "Unknown":
        errors.append(f"{doc.folder}: Missing required field: created")
    elif not re.match(r'^\d{4}-\d{2}-\d{2}$', doc.created):
        errors.append(
            f"{doc.folder}: Invalid date format for 'created': {doc.created}. "
            "Expected YYYY-MM-DD"
        )

    # proposal-from is required
    if not doc.proposal_from:
        errors.append(f"{doc.folder}: Missing required field: proposal-from")

    # Conditional fields
    if doc.status == "Withdrawn" and not doc.withdrawal_reason:
        errors.append(
            f"{doc.folder}: Withdrawn XLS must have withdrawal-reason field"
        )

    # Validate updated field format if present
    if doc.updated and not re.match(r'^\d{4}-\d{2}-\d{2}$', doc.updated):
        errors.append(
            f"{doc.folder}: Invalid date format for 'updated': {doc.updated}. "
            "Expected YYYY-MM-DD"
        )

    return errors


def validate_xls_documents(root_dir: Path) -> bool:
    """Validate that all XLS documents can be parsed correctly.

    Args:
        root_dir: Root directory containing XLS folders

    Returns:
        True if all documents parse successfully, False otherwise
    """
    try:
        docs = find_xls_documents(root_dir)

        # Basic validation checks
        if not docs:
            print("Warning: No XLS documents found")
            return False

        # Check for duplicate numbers
        numbers = [doc.number for doc in docs]
        if len(numbers) != len(set(numbers)):
            duplicates = [num for num in set(numbers) if numbers.count(num) > 1]
            print(f"Error: Duplicate XLS numbers found: {duplicates}")
            return False

        # Validate each document's preamble
        validation_errors = []
        for doc in docs:
            validation_errors.extend(validate_xls_preamble(doc))

        if validation_errors:
            print("\n")
            for error in validation_errors:
                print(f"Error: {error}")
            print(
                f"\nValidation failed: {len(validation_errors)} error(s) found"
            )
            return False

        print(f"\nSuccessfully validated {len(docs)} XLS documents")
        return True

    except Exception as e:
        print(f"Validation failed: {e}")
        return False


if __name__ == "__main__":
    """Run validation when script is executed directly."""
    root_dir = Path(".")
    success = validate_xls_documents(root_dir)
    sys.exit(0 if success else 1)
