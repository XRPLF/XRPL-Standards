#!/usr/bin/env python3
"""
XLS Validator - Validates XLS specs against templates

This script validates that XLS documents follow the structure defined in:
- XLS_TEMPLATE.md (preamble metadata and basic structure)
- AMENDMENT_TEMPLATE.md (for Amendment category XLS)

Usage:
    # Validate specific files
    python scripts/validate_xls_template.py XLS-0070-credentials/README.md

    # Validate multiple files
    python scripts/validate_xls_template.py XLS-0070-credentials/README.md XLS-0035-uritoken/README.md

    # Validate all XLS specs
    python scripts/validate_xls_template.py --all

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
import urllib.request
import urllib.error

from markdown_it import MarkdownIt
from xls_parser import extract_xls_metadata, validate_xls_preamble


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
    title: str
    level: int  # 2 for ##, 3 for ###, etc.
    line_number: int


class XLSTemplateValidator:
    """Validates XLS specs against the template structure."""

    # Required top-level sections (checked by substring match in section titles)
    REQUIRED_SECTIONS = [
        "Abstract",
        "Rationale",
        "Security",  # Matches "Security" or "Security Considerations"
    ]

    # Amendment template section patterns and their required subsections
    AMENDMENT_SECTION_TEMPLATES = {
        r"SType:": {
            "required": [
                "SType Value",
                "JSON Representation",
                "Binary Encoding",
                "Example JSON and Binary Encoding",
            ],
        },
        r"Ledger Entry:": {
            "required": [
                "Object Identifier",
                "Fields",
                "Ownership",
                "Reserves",
                "Deletion",
                "Invariants",
                "RPC Name",
                "Example JSON",
            ],
        },
        r"Transaction:": {
            "required": [
                "Fields",
                "Transaction Fee",
                "Failure Conditions",
                "State Changes",
                "Example JSON",
            ],
        },
        r"Permission:": {
            "required": [],
        },
        r"RPC:": {
            "required": [
                "Request Fields",
                "Response Fields",
                "Failure Conditions",
                "Example Request",
                "Example Response",
            ],
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

    # Timeout in seconds for HTTP requests to xrpl.org
    HTTP_TIMEOUT = 5

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
        except OSError as e:
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
        number_pattern = r'^\d+\.\s+(.+)$'

        # Walk through tokens to find headings
        for i, token in enumerate(tokens):
            if token.type == 'heading_open':
                # Get the heading level (h1 = level 1, h2 = level 2, etc.)
                level = int(token.tag[1])

                # Skip h1 (document title); process h2+ for structure
                if level < 2:
                    continue

                # The next token should be 'inline' containing heading text
                if i + 1 < len(tokens) and tokens[i + 1].type == 'inline':
                    inline_token = tokens[i + 1]
                    heading_text = inline_token.content

                    # Line number from the token's map (0-based, so add 1)
                    line_number = token.map[0] + 1 if token.map else None

                    # Strip section numbering if present
                    match = re.match(number_pattern, heading_text)
                    title = match.group(1) if match else heading_text

                    # Clean title: remove optional markers and backticks
                    title = title.strip()
                    title = re.sub(r'_\(Optional\)_', '', title).strip()
                    title = re.sub(r'`([^`]+)`', r'\1', title)

                    self.sections.append(Section(
                        title=title,
                        level=level,
                        line_number=line_number,
                    ))

    def _validate_preamble(self, doc):
        """Validate preamble metadata fields using the parser's validation."""
        preamble_errors = validate_xls_preamble(doc)
        for error_msg in preamble_errors:
            # Strip the folder prefix since we use file_path
            # Error format is "folder: message", extract just the message
            if ": " in error_msg:
                message = error_msg.split(": ", 1)[1]
            else:
                message = error_msg
            self.errors.append(ValidationError(
                str(self.file_path), 1, message
            ))

    def _validate_section_structure(self):
        """Validate the structure of top-level sections."""
        # Get all section titles
        section_titles = [s.title for s in self.sections]

        # Check for each required section (using substring match)
        for required in self.REQUIRED_SECTIONS:
            has_section = any(required in title for title in section_titles)
            if not has_section:
                self.errors.append(ValidationError(
                    str(self.file_path), None,
                    f"Missing required section: {required}"
                ))

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
            # No explicit template sections found. Before we assume this is an
            # old spec and skip all Amendment-structure validation, check
            # whether the document clearly describes existing XRPL primitives
            # (transactions, ledger entries, RPCs) using non-template headings
            # like "CheckCash Transaction", "AccountRoot Ledger Entry", or
            # "book_offers RPC". If so, fail validation so authors are
            # prompted to restructure the spec to use AMENDMENT_TEMPLATE.md.

            ledger_like_sections = self._find_existing_ledger_entry_like_headings()
            if ledger_like_sections:
                for section in ledger_like_sections:
                    self.errors.append(ValidationError(
                        str(self.file_path),
                        section.line_number,
                        (
                            "Amendment describes an existing XRPL ledger entry "
                            "type in section "
                            f"'{section.title}' but does not use the standard "
                            "Amendment template Ledger Entry sections (for "
                            "example, '## 2. Ledger Entry: `EntryName`'). "
                            "Please restructure this specification to use "
                            "AMENDMENT_TEMPLATE.md when documenting ledger "
                            "entries it modifies."
                        ),
                    ))

            transaction_like_sections = (
                self._find_existing_transaction_like_headings()
            )
            if transaction_like_sections:
                for section in transaction_like_sections:
                    self.errors.append(ValidationError(
                        str(self.file_path),
                        section.line_number,
                        (
                            "Amendment describes an existing XRPL transaction in "
                            f"section '{section.title}' but does "
                            "not use the standard Amendment template Transaction "
                            "sections (for example, '## 3. Transaction: `TxName`'). "
                            "Please restructure this specification to use "
                            "AMENDMENT_TEMPLATE.md when documenting transactions "
                            "it modifies."
                        ),
                    ))

            # Whether or not we found any heuristic issues, there are no
            # template sections to validate, so treat this as a legacy spec and
            # stop here.
            return

        # Validate each template section's subsections
        for section in main_sections:
            for pattern, template in self.AMENDMENT_SECTION_TEMPLATES.items():
                if re.search(pattern, section.title):
                    # Check if this is a Ledger Entry section for an
                    # existing ledger entry type
                    is_existing_ledger_entry = False
                    if pattern == r"Ledger Entry:":
                        is_existing_ledger_entry = (
                            self._is_existing_ledger_entry(section.title)
                        )

                    # Check if this is a Transaction section for an
                    # existing transaction type
                    is_existing_transaction = False
                    if pattern == r"Transaction:":
                        is_existing_transaction = (
                            self._is_existing_transaction(section.title)
                        )

                    self._validate_subsections(
                        section,
                        template["required"],
                        is_existing_ledger_entry,
                        is_existing_transaction,
                    )

    def _is_existing_ledger_entry(self, section_title: str) -> bool:
        """Check if a Ledger Entry section is for an existing ledger entry.

        Extracts the ledger entry name from the section title and checks if
        the ledger entry exists on xrpl.org by fetching the URL:

        https://xrpl.org/docs/references/protocol/ledger-data/ledger-entry-types/[lowercase]
        """
        # Extract ledger entry name from title like "Ledger Entry: `Foo`" or
        # "2. Ledger Entry: `Foo`".
        match = re.search(r"Ledger Entry:\s*`?([A-Za-z]+)`?", section_title)
        if not match:
            return False

        entry_name = match.group(1)
        return self._is_existing_ledger_entry_name(entry_name)

    def _url_exists(self, url: str, safe_on_error: bool = True) -> bool:
        """Check if a URL exists by making a HEAD request.

        Args:
            url: The URL to check
            safe_on_error: If True, return True on network errors (assume
                resource exists to avoid false positives). If False, return
                False on network errors (used for heuristic checks where
                false positives are worse than false negatives).

        Returns:
            True if the URL returns 200, False if 404 or on error when
            safe_on_error is False.
        """
        try:
            req = urllib.request.Request(url, method="HEAD")
            with urllib.request.urlopen(req, timeout=self.HTTP_TIMEOUT) as resp:
                return resp.status == 200
        except urllib.error.HTTPError as e:
            # 404 means the resource doesn't exist
            if e.code == 404:
                return False
            # Other errors (500, etc.)
            print(f"Warning: unexpected error checking {url}: {e}")
            return safe_on_error
        except (urllib.error.URLError, TimeoutError) as e:
            # Network error
            print(f"Warning: network error checking {url}: {e}")
            return safe_on_error

    def _is_existing_ledger_entry_name(
        self, entry_name: str, safe_on_error: bool = True
    ) -> bool:
        """Check if the given ledger entry name exists on xrpl.org."""
        url = (
            "https://xrpl.org/docs/references/protocol/"
            f"ledger-data/ledger-entry-types/{entry_name.lower()}"
        )
        return self._url_exists(url, safe_on_error)

    def _is_existing_transaction(self, section_title: str) -> bool:
        """Check if a Transaction section is for an existing transaction.

        Extracts the transaction name from the section title and checks if
        the transaction exists on xrpl.org.
        """
        match = re.search(r"Transaction:\s*`?([A-Za-z]+)`?", section_title)
        if not match:
            return False
        return self._is_existing_transaction_name(match.group(1))

    def _is_existing_transaction_name(
        self, transaction_name: str, safe_on_error: bool = True
    ) -> bool:
        """Check if the given transaction name exists on xrpl.org."""
        url = (
            "https://xrpl.org/docs/references/protocol/transactions/types/"
            f"{transaction_name.lower()}"
        )
        return self._url_exists(url, safe_on_error)

    def _find_existing_transaction_like_headings(self) -> List[Section]:
        """Find headings that look like "`SomeTransaction` Transaction".

        This is used as a heuristic to detect specs like XLS-0082 that
        clearly document behaviour for specific XRPL transactions but do not
        use the "Transaction: `Name`" Amendment template sections.

        Returns a list of matching sections; the list may be empty if no such
        headings are found or none of the candidate names resolve to known
        XRPL transaction types.
        """
        # Matches things like "3.3. CheckCash Transaction" or
        # "CheckCash Transaction". The section parser has already stripped
        # backticks from titles, so we only need to handle plain words here.
        pattern = re.compile(r"\b([A-Za-z]+)\s+Transaction\b")

        matches: List[Section] = []
        for section in self.sections:
            # Skip top-level template-style Transaction sections, if any exist
            if section.level == 2 and "Transaction:" in section.title:
                continue

            match = pattern.search(section.title)
            if not match:
                continue

            candidate_name = match.group(1)

            # Only treat this as a signal if the candidate resolves to a
            # known XRPL transaction type. Use safe_on_error=False to avoid
            # false positives on network errors (better to miss a warning
            # than to incorrectly fail validation).
            if self._is_existing_transaction_name(candidate_name, False):
                matches.append(section)

        return matches

    def _find_existing_ledger_entry_like_headings(self) -> List[Section]:
        """Find headings that look like "`SomeEntry` Ledger Entry".

        This is used as a heuristic to detect specs that clearly document
        behaviour for specific XRPL ledger entry types but do not use the
        "Ledger Entry: `Name`" Amendment template sections.
        """
        # Matches things like "2. AccountRoot Ledger Entry" or
        # "AccountRoot Ledger Entry". The section parser has already
        # stripped backticks from titles, so we only need to handle plain
        # words here.
        pattern = re.compile(
            r"\b([A-Za-z]+)\s+(Ledger Entry|On-Ledger Object)\b"
        )

        matches: List[Section] = []
        for section in self.sections:
            # Skip top-level template-style Ledger Entry sections, if any exist
            if section.level == 2 and (
                "Ledger Entry:" in section.title
                or "On-Ledger Object:" in section.title
            ):
                continue

            match = pattern.search(section.title)
            if not match:
                continue

            candidate_name = match.group(1)

            # Only treat this as a signal if the candidate resolves to a
            # known XRPL ledger entry type. Use safe_on_error=False to avoid
            # false positives on network errors.
            if self._is_existing_ledger_entry_name(candidate_name, False):
                matches.append(section)

        return matches

    def _validate_subsections(
        self,
        parent_section: Section,
        required_subsections: List[str],
        is_existing_ledger_entry: bool = False,
        is_existing_transaction: bool = False
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

        # For existing ledger entries, make certain subsections optional
        exempted_subsections: set[str] = set()
        if is_existing_ledger_entry:
            exempted_subsections = {
                "Object Identifier",
                "Ownership",
                "Reserves",
                "Deletion",
                "RPC Name",
            }

        # For existing transactions, make Transaction Fee optional
        if is_existing_transaction:
            exempted_subsections.add("Transaction Fee")

        # Check for required subsections
        for sub_title in required_subsections:
            # Skip if this subsection is exempted
            if sub_title in exempted_subsections:
                continue

            # Find this subsection by title
            found = any(sub_title in s.title for s in subsections)

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
    return success, validator.errors


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
        help='XLS files to validate (e.g., XLS-0070-credentials/README.md)'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Validate all XLS specs'
    )

    args = parser.parse_args()

    # Determine repository root
    script_dir = Path(__file__).parent.resolve()
    repo_root = script_dir.parent

    # Determine which files to validate
    if args.all:
        # Validate all XLS files
        files_to_validate = list(repo_root.glob('XLS-*/README.md'))
    elif args.files:
        # Validate specific files provided as arguments
        files_to_validate = [Path(f).resolve() for f in args.files]
    else:
        # No files specified
        parser.print_help()
        print("\nError: Please specify files to validate or use --all")
        return 1

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
        validated_count += 1

        # Check if this is an Amendment for stats
        try:
            content = file_path.read_text()
            if 'category: Amendment' in content:
                amendment_count += 1
        except OSError:
            pass

        if errors:
            all_errors.extend(errors)
        elif success:
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
