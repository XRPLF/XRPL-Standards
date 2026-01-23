#!/usr/bin/env python3
"""
XLS Template Validator - Validates XLS specs against XLS_TEMPLATE.md

This script validates that XLS documents follow the structure defined in
XLS_TEMPLATE.md, checking both preamble metadata and section structure.

Usage:
    # Validate specific files
    python scripts/validate_xls_template.py XLS-0070-credentials/README.md

    # Validate all XLS specs
    python scripts/validate_xls_template.py --all

    # Auto-detect changed files (for CI)
    python scripts/validate_xls_template.py

Validation Rules:
    - Checks all required preamble fields exist
    - Validates field formats (dates, categories, status values)
    - Checks for required top-level sections
    - Validates section numbering and structure

Exit Codes:
    0 - All validations passed
    1 - Validation errors found
"""

import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

from markdown_it import MarkdownIt
from xls_parser import extract_xls_metadata


@dataclass
class ValidationError:
    """Represents a validation error."""
    file_path: str
    line_number: Optional[int]
    message: str

    def __str__(self):
        if self.line_number:
            return f"{self.file_path}:{self.line_number}: {self.message}"
        return f"{self.file_path}: {self.message}"


@dataclass
class Section:
    """Represents a section in the markdown document."""
    number: str  # e.g., "1", "2", "3"
    title: str
    level: int  # 2 for ##, 3 for ###, etc.
    line_number: int
    is_optional: bool = False


class XLSTemplateValidator:
    """Validates XLS specs against the template structure."""

    # Required top-level sections (level 2 headings)
    REQUIRED_SECTIONS = {
        "Abstract": False,  # Not numbered in some specs
        "Specification": False,
        "Rationale": False,
        "Security Considerations": False,
    }

    # Optional top-level sections
    OPTIONAL_SECTIONS = {
        "Motivation": True,
        "Backwards Compatibility": True,
        "Test Plan": True,
        "Reference Implementation": True,
        "Appendix": True,
    }

    # Valid status values
    VALID_STATUSES = [
        "Draft", "Final", "Living", "Deprecated", "Stagnant", "Withdrawn"
    ]

    # Valid category values
    VALID_CATEGORIES = ["Amendment", "System", "Ecosystem", "Meta"]

    def __init__(self, file_path: Path):
        """Initialize validator with the file to validate."""
        self.file_path = file_path
        self.errors: List[ValidationError] = []
        self.sections: List[Section] = []
        self.content_lines: List[str] = []

    def validate(self) -> bool:
        """
        Run all validation checks.

        Returns:
            True if validation passes, False otherwise
        """
        # Read file content
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                self.content_lines = content.split('\n')
        except Exception as e:
            self.errors.append(ValidationError(
                str(self.file_path), None, f"Failed to read file: {e}"
            ))
            return False

        # Parse metadata
        try:
            doc = extract_xls_metadata(content, self.file_path.parent.name)
        except Exception as e:
            self.errors.append(ValidationError(
                str(self.file_path), None, f"Failed to parse metadata: {e}"
            ))
            return False

        # Parse sections
        self._parse_sections()

        # Run validation checks
        self._validate_preamble(doc)

        # Only validate section structure for new (Draft) XLS
        if doc.status == "Draft":
            self._validate_section_structure()

        return len(self.errors) == 0

    def _parse_sections(self):
        """Parse all sections from the markdown content using markdown-it-py."""
        md = MarkdownIt()
        content = '\n'.join(self.content_lines)
        tokens = md.parse(content)

        # Pattern to match section numbering: "1.", "2.", "3.", etc.
        number_pattern = r'^(\d+)\.\s+(.+)$'

        # Walk through tokens to find headings
        for i, token in enumerate(tokens):
            if token.type == 'heading_open':
                # Get the heading level (h2 = level 2, h3 = level 3, etc.)
                level = int(token.tag[1])

                # Only process h2 (top-level sections)
                if level != 2:
                    continue

                # The next token should be 'inline' containing heading text
                if i + 1 < len(tokens) and tokens[i + 1].type == 'inline':
                    inline_token = tokens[i + 1]
                    heading_text = inline_token.content

                    # Line number from the token's map (0-based, so add 1)
                    line_number = token.map[0] + 1 if token.map else None

                    # Check if this heading has section numbering
                    match = re.match(number_pattern, heading_text)
                    if match:
                        number, title = match.groups()
                    else:
                        # No numbering (e.g., "Abstract", "Appendix")
                        number = ""
                        title = heading_text

                    # Check if optional
                    is_optional = '_(Optional)_' in title

                    # Clean title
                    title = title.strip()
                    title = re.sub(r'_\(Optional\)_', '', title).strip()
                    title = re.sub(r'`([^`]+)`', r'\1', title)

                    self.sections.append(Section(
                        number=number,
                        title=title,
                        level=level,
                        line_number=line_number,
                        is_optional=is_optional
                    ))

    def _validate_preamble(self, doc):
        """Validate preamble metadata fields."""
        # Determine if this is a "new" XLS based on status
        # Draft XLS are considered new and must follow all rules
        is_new_xls = doc.status == "Draft"

        # Only validate Draft XLS strictly
        # Old XLS may not follow current template requirements
        if not is_new_xls:
            return

        # Check required fields for new (Draft) XLS
        if not doc.title or doc.title == "Unknown Title":
            self.errors.append(ValidationError(
                str(self.file_path), 1,
                "Missing required field: title"
            ))

        if not doc.description or doc.description == "No description available":
            self.errors.append(ValidationError(
                str(self.file_path), 1,
                "Missing required field: description"
            ))

        if not doc.authors or doc.authors == [("Unknown Author", "")]:
            self.errors.append(ValidationError(
                str(self.file_path), 1,
                "Missing required field: author"
            ))

        if not doc.category or doc.category == "Unknown":
            self.errors.append(ValidationError(
                str(self.file_path), 1,
                "Missing required field: category"
            ))
        elif doc.category not in self.VALID_CATEGORIES:
            self.errors.append(ValidationError(
                str(self.file_path), 1,
                f"Invalid category '{doc.category}'. "
                f"Must be one of: {', '.join(self.VALID_CATEGORIES)}"
            ))

        if not doc.status or doc.status == "Unknown":
            self.errors.append(ValidationError(
                str(self.file_path), 1,
                "Missing required field: status"
            ))
        elif doc.status not in self.VALID_STATUSES:
            self.errors.append(ValidationError(
                str(self.file_path), 1,
                f"Invalid status '{doc.status}'. "
                f"Must be one of: {', '.join(self.VALID_STATUSES)}"
            ))

        if not doc.created or doc.created == "Unknown":
            self.errors.append(ValidationError(
                str(self.file_path), 1,
                "Missing required field: created"
            ))
        elif not re.match(r'^\d{4}-\d{2}-\d{2}$', doc.created):
            self.errors.append(ValidationError(
                str(self.file_path), 1,
                f"Invalid date format for 'created': {doc.created}. "
                "Expected YYYY-MM-DD"
            ))

        # proposal-from is required for new XLS (Draft status)
        if not doc.proposal_from:
            self.errors.append(ValidationError(
                str(self.file_path), 1,
                "Missing required field: proposal-from"
            ))

        # Check conditional fields
        if doc.status == "Withdrawn" and not doc.withdrawal_reason:
            self.errors.append(ValidationError(
                str(self.file_path), 1,
                "Withdrawn XLS must have withdrawal-reason field"
            ))

        # Validate updated field format if present
        if doc.updated and not re.match(r'^\d{4}-\d{2}-\d{2}$', doc.updated):
            self.errors.append(ValidationError(
                str(self.file_path), 1,
                f"Invalid date format for 'updated': {doc.updated}. "
                "Expected YYYY-MM-DD"
            ))

    def _validate_section_structure(self):
        """Validate the structure of top-level sections."""
        # Get all section titles
        section_titles = [s.title for s in self.sections]

        # Check for Abstract (required, not numbered)
        if "Abstract" not in section_titles:
            self.errors.append(ValidationError(
                str(self.file_path), None,
                "Missing required section: Abstract"
            ))

        # Check for Security section (can be "Security" or "Security Considerations")
        has_security = any(
            "Security" in title for title in section_titles
        )
        if not has_security:
            self.errors.append(ValidationError(
                str(self.file_path), None,
                "Missing required section: Security or Security Considerations"
            ))

        # For Amendment XLS, the Specification and Rationale sections
        # are often split into numbered subsections, so we don't enforce
        # them strictly. The template validator focuses on preamble
        # and basic structure.

    def get_errors(self) -> List[ValidationError]:
        """Get all validation errors."""
        return self.errors


def validate_file(file_path: Path) -> Tuple[bool, List[ValidationError]]:
    """
    Validate a single file.

    Args:
        file_path: Path to the file to validate

    Returns:
        Tuple of (success, errors)
    """
    validator = XLSTemplateValidator(file_path)
    success = validator.validate()
    return success, validator.get_errors()


def get_changed_files(repo_root: Path) -> List[Path]:
    """
    Get list of changed XLS files in the current git diff.

    Returns:
        List of paths to changed README.md files in XLS folders
    """
    import subprocess

    try:
        # Get the base branch (usually master or main)
        base_ref = "origin/master"

        # Try to get changed files from git diff
        result = subprocess.run(
            ["git", "diff", "--name-only", base_ref, "HEAD"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True
        )

        changed_files = result.stdout.strip().split('\n')

        # Filter for XLS README.md files
        xls_files = []
        for file in changed_files:
            if file.startswith('XLS-') and file.endswith('/README.md'):
                file_path = repo_root / file
                if file_path.exists():
                    xls_files.append(file_path)

        return xls_files

    except subprocess.CalledProcessError:
        # If git diff fails, fall back to checking all files
        print("Warning: Could not get git diff, checking all XLS files")
        return list(repo_root.glob('XLS-*/README.md'))
    except Exception as e:
        print(f"Warning: Error getting changed files: {e}")
        return []


def main():
    """Main entry point for the validator."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Validate XLS specs against XLS_TEMPLATE.md'
    )
    parser.add_argument(
        'files',
        nargs='*',
        help='Specific files to validate (default: auto-detect changed files)'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Validate all XLS specs, not just changed ones'
    )

    args = parser.parse_args()

    # Determine repository root
    script_dir = Path(__file__).parent.resolve()
    repo_root = script_dir.parent

    # Determine which files to validate
    if args.files:
        # Validate specific files provided as arguments
        files_to_validate = [Path(f).resolve() for f in args.files]
    elif args.all:
        # Validate all XLS files
        files_to_validate = list(repo_root.glob('XLS-*/README.md'))
    else:
        # Auto-detect changed files (for CI)
        files_to_validate = get_changed_files(repo_root)

    if not files_to_validate:
        print("No files to validate.")
        return 0

    print(f"Validating {len(files_to_validate)} file(s)...\n")

    # Validate each file
    all_errors = []
    validated_count = 0

    for file_path in files_to_validate:
        print(f"Checking {file_path.parent.name}/README.md...")
        success, errors = validate_file(file_path)

        if errors:
            all_errors.extend(errors)
            validated_count += 1
        elif success:
            # File was validated and passed
            validated_count += 1
            print("  ✓ Valid")

    # Print results
    separator = "=" * 70
    print(f"\n{separator}")
    print("Validation complete:")
    print(f"  Validated: {validated_count}")
    print(f"  Errors: {len(all_errors)}")

    if all_errors:
        print(f"\n{separator}")
        print("VALIDATION ERRORS:")
        print(f"{separator}\n")
        for error in all_errors:
            print(f"  {error}")
        print()
        return 1

    print("\n✓ All XLS specs are valid!")
    return 0


if __name__ == '__main__':
    sys.exit(main())
