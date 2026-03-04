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

> **Always read the actual template files before reviewing or writing any XLS specification.** The structure documented below reflects the templates at the time these instructions were written; the files are the authoritative source and may have been updated since.
>
> - `templates/XLS_TEMPLATE.md` — top-level section structure for all XLS types
> - `templates/AMENDMENT_TEMPLATE.md` — Specification section structure for Amendment XLSes

## XLS_TEMPLATE.md — Required Top-Level Sections

```
## 1. Abstract                     ← required
## 2. Motivation                   ← optional
## 3. Specification                ← required; for Amendment use AMENDMENT_TEMPLATE.md
## 4. Rationale                    ← required
## 5. Backwards Compatibility      ← optional (required if incompatibilities exist)
## 6. Test Plan                    ← optional (required for Amendment/System)
## 7. Reference Implementation     ← optional
## 8. Security Considerations      ← required (XLS rejected without it)
# Appendix                         ← optional
```

## AMENDMENT_TEMPLATE.md — Specification Section Structure

For Amendment-category XLSes, `## 3. Specification` contains components as `### 3.N. ComponentType: \`Name\``subsections. Each component has numbered sub-subsections`#### 3.N.M.` and deeper.

### Ledger Entry (`### 3.N. Ledger Entry: \`Name\``)

| Sub | Heading             | Notes                                                                                                                                                                                        |
| --- | ------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| .1  | `Object Identifier` | Optional if entry already on mainnet. **Key Space:** `0x[XXXX]`; **ID Calculation Algorithm:**                                                                                               |
| .2  | `Fields`            | See table schema below. Standard rows always present: `LedgerEntryType`, `Account`, `OwnerNode`, `PreviousTxnID`, `PreviousTxnLgrSeq`. Field detail sub-subsections at `##### 3.N.2.1.` etc. |
| .3  | `Flags`             | Optional if none. Flag names use `lsf` prefix. See Flags table schema.                                                                                                                       |
| .4  | `Ownership`         | Optional if existing. **Owner:**; **Directory Registration:**                                                                                                                                |
| .5  | `Reserves`          | Optional if existing. **Reserve Requirement:** `[Standard/Custom/None]`                                                                                                                      |
| .6  | `Deletion`          | Optional if existing. **Deletion Transactions:**; **Deletion Conditions:** bullet list; **Account Deletion Blocker:** `[Yes/No]`                                                             |
| .7  | `Pseudo-Account`    | Optional. **Uses Pseudo-Account:** `[Yes/No]`; Purpose, AccountID Derivation, Capabilities                                                                                                   |
| .8  | `Freeze/Lock`       | Optional. **Freeze Support:**; **Lock Support:**                                                                                                                                             |
| .9  | `Invariants`        | Bullet list. Use `<object>` for before-state, `<object>'` for after-state                                                                                                                    |
| .10 | `RPC Name`          | Optional if existing. **RPC Type Name:** `snake_case_name`                                                                                                                                   |
| .11 | `Example JSON`      | ` ```json ` block                                                                                                                                                                            |

**Ledger Entry Fields table columns (exact):**

```
| Field Name | Constant | Required | Internal Type | Default Value | Description |
```

### Transaction (`### 3.N. Transaction: \`Name\``)

Naming convention: `<LedgerEntryName><Verb>` (e.g., `VaultCreate`, `VaultDelete`).

| Sub | Heading              | Notes                                                                                                                |
| --- | -------------------- | -------------------------------------------------------------------------------------------------------------------- |
| .1  | `Fields`             | See table schema below. Always includes `TransactionType` row. Field detail sub-subsections at `##### 3.N.1.1.` etc. |
| .2  | `Flags`              | Optional if none. Flag names use `tf` prefix. See Flags table schema.                                                |
| .3  | `Transaction Fee`    | Optional if existing. **Fee Structure:** `[Standard/Custom]`                                                         |
| .4  | `Failure Conditions` | **Two mandatory sub-subsections** (see below)                                                                        |
| .5  | `State Changes`      | **On Success (`tesSUCCESS`):** bold label followed by bullet list                                                    |
| .6  | `Metadata Fields`    | Optional. See table schema below.                                                                                    |
| .7  | `Example JSON`       | ` ```json ` block                                                                                                    |

**Transaction Fields table columns (exact):**

```
| Field Name | Required? | JSON Type | Internal Type | Default Value | Description |
```

**Failure Conditions structure — always two sub-subsections with numbered lists:**

```markdown
##### 3.N.4.1. Data Verification

[All Data Verification failures return a `tem` level error.]

1. [condition description] (`[ERROR_CODE]`)
2. [condition description] (`[ERROR_CODE]`)

##### 3.N.4.2. Protocol-Level Failures

[Protocol-level failures return `tec` codes ...]

1. [condition description] (`[ERROR_CODE]`)
```

### Permission (`### 3.N. Permission: \`Name\``)

Sub-subsections: `.1. Permission Description`, `.2. Transaction Types Affected`, `.3. Permission Value`

### RPC (`### 3.N. RPC: \`method_name\``)

| Sub | Heading              | Notes                                            |
| --- | -------------------- | ------------------------------------------------ |
| .1  | `Request Fields`     | Always includes `command` row. See table schema. |
| .2  | `Response Fields`    | Always includes `status` row. See table schema.  |
| .3  | `Failure Conditions` | Single numbered list (no sub-subsections)        |
| .4  | `Example Request`    | ` ```json ` block                                |
| .5  | `Example Response`   | ` ```json ` block                                |

### Table Schemas (exact column headings)

| Table                | Columns                                                                                 |
| -------------------- | --------------------------------------------------------------------------------------- |
| Ledger Entry Fields  | `Field Name \| Constant \| Required \| Internal Type \| Default Value \| Description`   |
| Transaction Fields   | `Field Name \| Required? \| JSON Type \| Internal Type \| Default Value \| Description` |
| Flags (both)         | `Flag Name \| Flag Value \| Description`                                                |
| RPC Request Fields   | `Field Name \| Required? \| JSON Type \| Description`                                   |
| RPC Response Fields  | `Field Name \| Always Present? \| JSON Type \| Description`                             |
| Transaction Metadata | `Field Name \| Validated \| Always Present? \| Type \| Description`                     |

## Key Rules

- **No unfilled placeholders** — `validate_xls_template.py` rejects patterns like `[FieldName]`, `[example value]`, `_[Describe...]`, `0x[XXXX]`, `[r-address]`, `[Yes/No]`, etc.
- **New draft directories** use `XLS-draft-<short-title>/` — the CI bot assigns the number; editors rename before merge.
- **`scripts/_site/` is gitignored** — never commit build output.
- Always run `python scripts/xls_parser.py` after any preamble change; it validates all docs and exits 1 on error.
