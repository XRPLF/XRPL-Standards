#!/usr/bin/env python3
"""
XLS Standards Parser - Extracts metadata from XLS markdown documents.

This module provides functionality to parse XLS (XRPL Standards) documents
and extract their metadata for use in documentation systems and validation.
"""

import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List, Optional, Tuple
import sys

from bs4 import BeautifulSoup


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

    def to_dict(self):
        return asdict(self)


def extract_xls_metadata(content: str, folder_name: str) -> Optional[XLSDocument]:
    """Extract metadata from XLS markdown content.

    Args:
        content: The raw markdown content of the XLS document
        folder_name: Name of the folder containing the XLS document

    Returns:
        XLSDocument instance with extracted metadata, or None if parsing fails
    """

    # Initialize metadata with defaults
    metadata = {}

    # Parse HTML pre block for metadata
    pre_regex = r"<pre>(.*?)</pre>"
    match = re.search(pre_regex, content, re.DOTALL)
    if match:
        pre_text = match.group(1)
    else:
        print("ERROR: No <pre> block found in content")
        sys.exit(1)

    # Extract metadata using standardized patterns (headers are now enforced by CI)
    patterns = {
        "title": r"[tT]itle:\s*(.*?)(?:\n|$)",
        "description": r"[dD]escription:\s*(.*?)(?:\n|$)",
        "authors": r"[aA]uthors?:\s*(.*?)(?:\n|$)",
        "status": r"[sS]tatus:\s*(.*?)(?:\n|$)",
        "category": r"[cC]ategory:\s*(.*?)(?:\n|$)",
        "created": r"[cC]reated:\s*(.*?)(?:\n|$)",
        "proposal_from": r"[pP]roposal-from:\s*(.*?)(?:\n|$)",
        "implementation": r"[iI]mplementation:\s*(.*?)(?:\n|$)",
        "requires": r"[rR]equires:\s*(.*?)(?:\n|$)",
        "updated": r"[uU]pdated:\s*(.*?)(?:\n|$)",
        "withdrawal_reason": r"[wW]ithdrawal-reason:\s*(.*?)(?:\n|$)",
    }

    def format_author(author):
        """Format author information into name and link tuple."""
        author = author.strip()
        # Email address
        email_match = re.match(r"^(.*?)\s*<\s*([^>]+)\s*>$", author)
        if email_match:
            name = email_match.group(1).strip()
            email = email_match.group(2).strip()
            return name, f'mailto:{email}'
        # GitHub username in parentheses
        gh_match = re.match(r"^(.*?)\s*\(@([^)]+)\)$", author)
        if gh_match:
            name = gh_match.group(1).strip()
            gh_user = gh_match.group(2).strip()
            return name, f'https://github.com/{gh_user}'
        # Just a name
        return author, ""

    for key, pattern in patterns.items():
        match = re.search(pattern, pre_text, re.IGNORECASE | re.DOTALL)
        if match:
            value = match.group(1).strip()
            # Clean HTML tags from value and process based on field type
            if key == "authors":
                # Process comma-separated authors
                value = [
                    format_author(author)
                    for author in value.split(",")
                ]
            else:
                # Clean HTML tags for other fields
                value = BeautifulSoup(value, "html.parser").get_text().strip()
            metadata[key] = value

    # Extract XLS number from folder name
    xls_match = re.match(r"XLS-(\d+)([d]?)", folder_name)
    if xls_match:
        number = xls_match.group(1)
    else:
        number = "000"

    return XLSDocument(
        number=number,
        title=metadata.get("title", "Unknown Title"),
        description=metadata.get("description", "No description available"),
        authors=metadata.get("authors", [("Unknown Author", "")]),
        folder=folder_name,
        filename="README.md",
        status=metadata.get("status", "Unknown"),
        category=metadata.get("category", "Unknown"),
        created=metadata.get("created", "Unknown"),
        proposal_from=metadata.get("proposal_from"),
        implementation=metadata.get("implementation"),
        requires=metadata.get("requires"),
        updated=metadata.get("updated"),
        withdrawal_reason=metadata.get("withdrawal_reason"),
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
                if doc:
                    xls_docs.append(doc)
                    print(f"Parsed: {folder.name} - {doc.title}")
                else:
                    raise Exception(f"Failed to parse metadata from {folder.name}")

            except Exception as e:
                print(f"Error processing {folder.name}: {e}")
                raise

    return xls_docs


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
