#!/usr/bin/env python3
"""
Amendment Template Validator - Validates Amendment specs against AMENDMENT_TEMPLATE.md

This script validates that Amendment category XLS documents follow the structure
defined in AMENDMENT_TEMPLATE.md. It is designed to run in CI/CD to check only
new or modified specs.

Usage:
    # Validate specific files
    python scripts/validate_amendment_template.py XLS-0070-credentials/README.md

    # Validate all Amendment specs
    python scripts/validate_amendment_template.py --all

    # Auto-detect changed files (for CI)
    python scripts/validate_amendment_template.py

Validation Rules:
    - Only validates specs with category: Amendment
    - Only validates specs that use template section titles
      (Serialized Types, Ledger Entries, Transactions, Permissions, API/RPCs)
    - Checks for required subsections within each template section
    - Detects template placeholder text that should be replaced
    - Skips validation for old specs that don't follow the template

Exit Codes:
    0 - All validations passed
    1 - Validation errors found
"""

import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

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
    number: str  # e.g., "1", "2.1", "2.1.1"
    title: str
    level: int  # 2 for ##, 3 for ###, etc.
    line_number: int
    is_optional: bool = False


class AmendmentTemplateValidator:
    """Validates Amendment specs against the template structure."""

    # Map section titles to their expected subsections
    # Key is the section title, value is dict of subsection numbers to titles
    SECTION_TEMPLATES = {
        "Serialized Types": {
            "required_subsections": {
                "1": "SType Value",
                "2": "JSON Representation",
                "4": "Binary Encoding",
                "5": "Example JSON and Binary Encoding",
            },
            "optional_subsections": {
                "3": "Additional Accepted JSON Inputs",
            }
        },
        "Ledger Entries": {
            "required_subsections": {
                "1": "Object Identifier",
                "2": "Fields",
                "3": "Ownership",
                "4": "Reserves",
                "5": "Deletion",
                "8": "Invariants",
                "9": "RPC Name",
                "10": "Example JSON",
            },
            "optional_subsections": {
                "6": "Pseudo-Account",
                "7": "Freeze/Lock",
            }
        },
        "Transactions": {
            "required_subsections": {
                "1": "Fields",
                "2": "Transaction Fee",
                "3": "Failure Conditions",
                "4": "State Changes",
                "6": "Example JSON",
            },
            "optional_subsections": {
                "5": "Metadata Fields",
            }
        },
        "Permissions": {
            "required_subsections": {},
            "optional_subsections": {}
        },
        "API/RPCs": {
            "required_subsections": {},
            "optional_subsections": {}
        },
    }

    # Placeholder patterns that should not appear in final specs
    PLACEHOLDER_PATTERNS = [
        r'\[STypeName\]',
        r'\[LedgerEntryName\]',
        r'\[TransactionName\]',
        r'\[XXXX\]',
        r'\[field_name\]',
        r'\[api_method_name\]',
        r'\[CustomField\d+\]',
        r'\[EntryTypeValue\]',
        r'\[TYPE\]',
        r'\[Yes/No\]',
        r'\[Value/N/A\]',
        r'\[Description.*?\]',
        r'\[Provide.*?\]',
        r'\[Specify.*?\]',
        r'\[Describe.*?\]',
        r'\[List.*?\]',
        r'\[If.*?\]',
        r'\[Add more.*?\]',
        r'\[Remove example.*?\]',
    ]

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

        # Check if this is an Amendment category spec
        if not self._is_amendment_spec(content):
            # Not an amendment, skip validation
            return True

        # Parse sections
        self._parse_sections()

        # Run validation checks
        self._validate_has_required_sections()
        self._validate_section_structure()
        self._validate_no_placeholders()

        return len(self.errors) == 0

    def _is_amendment_spec(self, content: str) -> bool:
        """Check if the spec is an Amendment category spec."""
        try:
            doc = extract_xls_metadata(content, self.file_path.parent.name)
            return doc and doc.category.lower() == "amendment"
        except Exception:
            # If we can't parse metadata, assume it's not an amendment
            return False

    def _parse_sections(self):
        """Parse all sections from the markdown content."""
        # Match markdown headers: ## 1. Title, ### 1.1. Title, etc.
        header_pattern = (
            r'^(#{2,4})\s+(\d+(?:\.\d+)*)\.\s+(.+?)(?:\s+_\(Optional\)_)?$'
        )

        for line_num, line in enumerate(self.content_lines, start=1):
            match = re.match(header_pattern, line)
            if match:
                hashes, number, title = match.groups()
                level = len(hashes)
                is_optional = '_(Optional)_' in line

                # Clean title
                title = title.strip()
                title = re.sub(r'_\(Optional\)_', '', title).strip()
                title = re.sub(r'`([^`]+)`', r'\1', title)  # Remove backticks

                self.sections.append(Section(
                    number=number,
                    title=title,
                    level=level,
                    line_number=line_num,
                    is_optional=is_optional
                ))

    def _validate_has_required_sections(self):
        """Validate that at least one template section exists."""
        main_sections = [s for s in self.sections if s.level == 2]

        # Get titles of main sections
        section_titles = {s.title for s in main_sections}

        # Check if at least one template section exists
        template_sections = set(self.SECTION_TEMPLATES.keys())
        has_template_section = bool(section_titles & template_sections)

        if not has_template_section:
            # No template sections found - this might be an old spec
            # We'll just skip validation for this file
            return

    def _validate_section_structure(self):
        """Validate the structure and numbering of sections."""
        # Check each main section that matches a template
        for section in self.sections:
            if section.level == 2:
                # Check if this section matches a template
                if section.title in self.SECTION_TEMPLATES:
                    self._validate_subsections(section)

    def _validate_subsections(self, parent_section: Section):
        """Validate subsections for a given parent section."""
        template = self.SECTION_TEMPLATES.get(parent_section.title)
        if not template:
            return

        # Get all direct subsections (level 3) for this parent
        parent_num = parent_section.number
        subsections = [
            s for s in self.sections
            if s.number.startswith(parent_num + ".") and s.level == 3
        ]

        # Group subsections by their first-level parent (e.g., 2.1, 2.2)
        # This handles cases where there are multiple instances
        # (e.g., multiple ledger entries or transactions)
        first_level_groups = {}
        for s in subsections:
            parts = s.number.split('.')
            if len(parts) >= 2:
                first_level = f"{parts[0]}.{parts[1]}"
                if first_level not in first_level_groups:
                    first_level_groups[first_level] = []
                first_level_groups[first_level].append(s)

        # For each first-level group, validate required subsections
        required_subs = template["required_subsections"]

        for first_level in first_level_groups:
            # Check each required subsection
            for sub_num, sub_title in required_subs.items():
                expected_num = f"{first_level}.{sub_num}"

                # Find this subsection in the group
                found = any(
                    s.number == expected_num
                    for s in self.sections
                    if s.level == 4
                )

                if not found:
                    self.errors.append(ValidationError(
                        str(self.file_path), parent_section.line_number,
                        f"Missing required subsection {expected_num} "
                        f"'{sub_title}' under {parent_section.title}"
                    ))

    def _validate_no_placeholders(self):
        """Check for template placeholder text that should be replaced."""
        # Skip metadata block (first <pre> block)
        in_metadata = False
        content_start = 0

        for i, line in enumerate(self.content_lines):
            if '<pre>' in line:
                in_metadata = True
            elif '</pre>' in line and in_metadata:
                in_metadata = False
                content_start = i + 1
                break

        # Check content after metadata
        for line_num, line in enumerate(
            self.content_lines[content_start:], start=content_start + 1
        ):
            for pattern in self.PLACEHOLDER_PATTERNS:
                if re.search(pattern, line):
                    self.errors.append(ValidationError(
                        str(self.file_path), line_num,
                        f"Found template placeholder text: {pattern}"
                    ))
                    break  # Only report one error per line

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
    validator = AmendmentTemplateValidator(file_path)
    success = validator.validate()
    return success, validator.get_errors()


def get_changed_files(repo_root: Path) -> List[Path]:
    """
    Get list of changed XLS files in the current git diff.

    This function is designed to run in CI and detect files changed in a PR.

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
        description='Validate Amendment specs against AMENDMENT_TEMPLATE.md'
    )
    parser.add_argument(
        'files',
        nargs='*',
        help='Specific files to validate (default: auto-detect changed files)'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Validate all Amendment specs, not just changed ones'
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
    skipped_count = 0

    for file_path in files_to_validate:
        print(f"Checking {file_path.parent.name}/README.md...")
        success, errors = validate_file(file_path)

        if errors:
            all_errors.extend(errors)
            validated_count += 1
        elif success:
            # File was validated (is an Amendment) and passed
            validated_count += 1
            print("  ✓ Valid")
        else:
            # File was skipped (not an Amendment)
            skipped_count += 1
            print("  - Skipped (not an Amendment spec)")

    # Print results
    separator = "=" * 70
    print(f"\n{separator}")
    print("Validation complete:")
    print(f"  Validated: {validated_count}")
    print(f"  Skipped: {skipped_count}")
    print(f"  Errors: {len(all_errors)}")

    if all_errors:
        print(f"\n{separator}")
        print("VALIDATION ERRORS:")
        print(f"{separator}\n")
        for error in all_errors:
            print(f"  {error}")
        print()
        return 1

    print("\n✓ All Amendment specs are valid!")
    return 0


if __name__ == '__main__':
    sys.exit(main())
