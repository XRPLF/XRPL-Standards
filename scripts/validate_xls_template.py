#!/usr/bin/env python3
"""
XLS Validator - Validates XLS specs against templates

This script validates that XLS documents follow the structure defined in:
- XLS_TEMPLATE.md (preamble metadata and basic structure)
- AMENDMENT_TEMPLATE.md (for Amendment category XLS)

Usage:
    # Validate specific files
    python scripts/validate_xls_template.py XLS-0070-credentials/README.md

    # Validate all XLS specs
    python scripts/validate_xls_template.py --all

    # Auto-detect changed files (for CI)
    python scripts/validate_xls_template.py

Validation Rules:
    - All XLS: Checks preamble fields and basic structure
    - Amendment XLS: Additionally validates against AMENDMENT_TEMPLATE.md

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

    # Amendment template section patterns and their required subsections
    AMENDMENT_SECTION_TEMPLATES = {
        r"SType:": {
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
        r"Ledger Entry:": {
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
        r"Transaction:": {
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
        r"Permission:": {
            "required_subsections": {},
            "optional_subsections": {}
        },
        r"RPC:": {
            "required_subsections": {},
            "optional_subsections": {}
        },
    }

    # Placeholder patterns that should not appear in final Amendment specs
    PLACEHOLDER_PATTERNS = [
        r'\[STypeName\]',
        r'\[LedgerEntryName\]',
        r'\[TransactionName\]',
        r'\[PermissionName\]',
        r'\[rpc_method_name\]',
        r'0x\[XXXX\]',
        r'\[field_name\]',
        r'\[FieldName\]',
        r'\[api_method_name\]',
        r'\[CustomField\d+\]',
        r'\[EntryTypeValue\]',
        r'\[TYPE\]',
        r'\[Yes/No(?:/Conditional)?\]',
        r'\[Standard/Custom(?:/None)?\]',
        r'\[Value/N/A\]',
        r'\[r-address\]',
        r'\[example value\]',
        r'_\[Description.*?\]',
        r'_\[Provide.*?\]',
        r'_\[Specify.*?\]',
        r'_\[Describe.*?\]',
        r'_\[List.*?\]',
        r'_\[If .*?\]',
        r'_\[Add more.*?\]',
        r'_\[Remove example.*?\]',
        r'_\[Any explanatory.*?\]',
        r'_\[Detailed explanation.*?\]',
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
        self._validate_section_structure()

        # Additionally validate Amendment template structure
        if doc.category == "Amendment":
            self._validate_amendment_structure()
            self._validate_no_placeholders()

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

        # proposal-from is required for new XLS
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

    def _validate_amendment_structure(self):
        """Validate Amendment-specific template structure."""
        # Get main sections (level 2)
        main_sections = [s for s in self.sections if s.level == 2]

        # Check if at least one template section exists
        has_template_section = False
        for section in main_sections:
            for pattern in self.AMENDMENT_SECTION_TEMPLATES.keys():
                if re.search(pattern, section.title):
                    has_template_section = True
                    break
            if has_template_section:
                break

        if not has_template_section:
            # No template sections found - might be an old spec, skip
            return

        # Validate each template section's subsections
        for section in main_sections:
            for pattern, template in self.AMENDMENT_SECTION_TEMPLATES.items():
                if re.search(pattern, section.title):
                    self._validate_subsections(
                        section,
                        template["required_subsections"],
                        template["optional_subsections"]
                    )

    def _validate_subsections(
        self,
        parent_section: Section,
        required_subsections: dict,
        optional_subsections: dict
    ):
        """Validate that a section has required subsections."""
        # Get all subsections under this parent
        parent_idx = self.sections.index(parent_section)
        subsections = []

        for i in range(parent_idx + 1, len(self.sections)):
            section = self.sections[i]

            # Stop when we hit another section at same or higher level
            if section.level <= parent_section.level:
                break

            # Only collect direct children (one level deeper)
            if section.level == parent_section.level + 1:
                subsections.append(section)

        # Check for required subsections
        for sub_num, sub_title in required_subsections.items():
            # Find this subsection by title, regardless of its actual number
            found = any(
                sub_title in s.title
                for s in subsections
            )

            if not found:
                self.errors.append(ValidationError(
                    str(self.file_path),
                    parent_section.line_number,
                    f"Section '{parent_section.title}' is missing required "
                    f"subsection: {sub_title}"
                ))

    def _validate_no_placeholders(self):
        """Check for template placeholder text in Amendment specs."""
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
        description='Validate XLS specs against templates '
                    '(XLS_TEMPLATE.md and AMENDMENT_TEMPLATE.md)'
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
    amendment_count = 0

    for file_path in files_to_validate:
        print(f"Checking {file_path.parent.name}/README.md...")
        success, errors = validate_file(file_path)

        if errors:
            all_errors.extend(errors)
            validated_count += 1
            # Check if this is an Amendment for stats
            try:
                content = file_path.read_text()
                if 'category: Amendment' in content:
                    amendment_count += 1
            except:
                pass
        elif success:
            # File was validated and passed
            validated_count += 1
            try:
                content = file_path.read_text()
                if 'category: Amendment' in content:
                    amendment_count += 1
            except:
                pass
            print("  ✓ Valid")

    # Print results
    separator = "=" * 70
    print(f"\n{separator}")
    print("Validation complete:")
    print(f"  Validated: {validated_count}")
    if amendment_count > 0:
        print(f"  Amendment specs: {amendment_count}")
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
