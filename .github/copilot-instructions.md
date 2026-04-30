# GitHub Copilot Instructions for XRPL-Standards

## Repository Summary

**Documentation-only** repository for XRP Ledger Standards (XLSes) — Markdown specification documents plus Python validation/site-generation scripts and GitHub Actions CI. No application code to compile. Trust these instructions; only search if something here is incomplete or in error.

## Project Layout

| Path                                 | Purpose                                                               |
| ------------------------------------ | --------------------------------------------------------------------- |
| `XLS-NNNN-short-title/README.md`     | One specification per standard (74 total)                             |
| `templates/XLS_TEMPLATE.md`          | Base template for all new XLS specs                                   |
| `templates/AMENDMENT_TEMPLATE.md`    | Specification section structure for Amendment XLSes                   |
| `scripts/xls_parser.py`              | Parses and validates preambles of all XLS docs (main CI)              |
| `scripts/validate_xls_template.py`   | Validates structure of changed files (Beta CI)                        |
| `scripts/requirements.txt`           | Python deps: markdown, jinja2, beautifulsoup4, pyyaml, markdown-it-py |
| `.github/workflows/lint.yml`         | prettier@3.6.2 check — **required on every PR**                       |
| `.github/workflows/validate-xls.yml` | xls_parser + template validator — **required on every PR**            |
| `.pre-commit-config.yaml`            | prettier@3.6.2 + trailing-whitespace, end-of-file-fixer               |

## XLS Preamble Format

Every `README.md` must open with a `<pre>` block (the `xls_parser.py` CI reads it):

```
<pre>
  xls: [number]
  title: [max 44 chars, no "XLS" prefix or number]
  description: [one full sentence]
  author: [Name <email@example.com>, Name2 (@github-handle)]
  category: [Amendment | System | Ecosystem | Meta]
  status: [Draft | Final | Living | Deprecated | Stagnant | Withdrawn]
  proposal-from: [URL to GitHub Discussions thread]
  created: YYYY-MM-DD
  updated: YYYY-MM-DD          ← optional
  implementation: [URL]        ← optional; required for Final Amendment/System
  requires: XLS-N, XLS-M      ← optional
  withdrawal-reason: [text]    ← required if status is Withdrawn
</pre>
```

Every author **must** have a link — `Name <email>` or `Name (@github-handle)`; a bare name fails CI.

## Template Compliance

> **Always read the actual template files before reviewing or writing any XLS specification.** The templates are the single source of truth for section structure, sub-section ordering, table column headings, and naming conventions. Do not rely on summaries — open the files directly.
>
> - `templates/XLS_TEMPLATE.md` — top-level section structure for all XLS types
> - `templates/AMENDMENT_TEMPLATE.md` — Specification section structure for Amendment XLSes (Ledger Entries, Transactions, Permissions, RPCs, and their required table schemas)
>
> When reviewing or authoring a spec, diff the document against the relevant template to catch missing sections, wrong table columns, or incorrect heading numbering.

## Key Rules

- **No unfilled placeholders** — `validate_xls_template.py` rejects patterns like `[FieldName]`, `[example value]`, `_[Describe...]`, `0x[XXXX]`, `[r-address]`, `[Yes/No]`, etc.
- **New draft directories** use `XLS-draft-<short-title>/` — the CI bot assigns the number; editors rename before merge.
- **`scripts/_site/` is gitignored** — never commit build output.
- Always run `python scripts/xls_parser.py` after any preamble change; it validates all docs and exits 1 on error.
