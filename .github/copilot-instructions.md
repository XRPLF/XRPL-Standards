# Copilot Cloud Agent Instructions — XRPL-Standards

## Repository Purpose

This repository is the canonical home for **XRP Ledger Standards (XLSes)** — specifications and standards that govern the XRP Ledger ecosystem. Each XLS is a living document covering protocol amendments, system-level changes, or community/off-chain conventions. The full process is defined in [XLS-0001](../XLS-0001-xls-process/README.md) and summarized in [CONTRIBUTING.md](../CONTRIBUTING.md).

---

## Repository Layout

```
/
├── XLS-NNNN-slug/          # One folder per XLS spec (4-digit zero-padded number + hyphenated title)
│   └── README.md           # The XLS document itself (required)
├── templates/
│   ├── XLS_TEMPLATE.md     # Preamble + section scaffold for all new XLSes
│   └── AMENDMENT_TEMPLATE.md  # Extra scaffold for Amendment-category XLSes (Section 3 onward)
├── scripts/
│   ├── requirements.txt    # Python deps (install with: pip install -r scripts/requirements.txt)
│   ├── xls_parser.py       # Parses XLS README.md files and validates preamble metadata
│   ├── validate_xls_template.py  # Validates XLS structure against templates (Beta CI)
│   └── build_site.py       # Builds the GitHub Pages static site from XLS docs
├── CONTRIBUTING.md         # How to contribute (summarises XLS-1)
└── .github/
    ├── pull_request_template.md
    ├── workflows/           # CI workflows (see below)
    └── scripts/             # Scripts used by CI (assign_xls_number.py, etc.)
```

---

## XLS Document Format

Every XLS lives at `XLS-NNNN-slug/README.md` and **must** start with an RFC-822-style `<pre>` preamble block:

```
<pre>
  xls: [number]
  title: [max 44 chars, no "XLS" prefix]
  description: [max 140 chars, one sentence]
  author: Name (@github-handle), Other Name <email@example.com>
  category: [Amendment | System | Ecosystem | Meta]
  status: [Draft | Final | Living | Deprecated | Stagnant | Withdrawn]
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/NNN
  created: YYYY-MM-DD
  updated: YYYY-MM-DD          # optional
  implementation: [url]        # optional, for Amendment/System XLSes
  requires: [xls numbers]      # optional
  withdrawal-reason: [reason]  # required only when status is Withdrawn
</pre>
```

**Required sections** (all XLSes): Abstract, Rationale, Security Considerations.
**Amendment XLSes** additionally require the sub-structure from `AMENDMENT_TEMPLATE.md` covering STypes, Ledger Entries, Transactions, Permissions, and RPCs as applicable.

### Categories

| Category | Description |
|----------|-------------|
| `Amendment` | Requires an XRP Ledger amendment (on-chain protocol change via rippled) |
| `System` | Affects XRPL protocol behavior (RPCs, P2P) but no amendment needed |
| `Ecosystem` | Off-chain/community standards (metadata, registries, etc.) |
| `Meta` | Standards about the XLS process itself |

### Statuses

`Idea` → `Proposal` → `Draft` → `Final` or `Living`

Also: `Deprecated` (Final XLS no longer recommended), `Stagnant` (Draft inactive ≥6 months), `Withdrawn` (removed by author — number cannot be reused).

---

## How to Add a New XLS

1. Start in GitHub Discussions (Idea or Proposal stage) — do **not** open a PR until there is community feedback.
2. Create a directory named `XLS-draft-<short-title>/` (agents/authors must NOT self-assign numbers for XLS numbers > 95).
3. Copy `templates/XLS_TEMPLATE.md` to `XLS-draft-<short-title>/README.md` and fill it in.
4. Open a PR. CI will assign the official XLS number automatically after a maintainer with write access approves; the `assign-xls-number.yml` workflow renames the directory and updates the preamble. Authors should not assign their own XLS number.

---

## CI Workflows

| Workflow | Trigger | What it does |
|----------|---------|--------------|
| `validate-xls.yml` | PRs, push to master | Runs `python scripts/xls_parser.py` — validates preamble of **all** XLS docs |
| `validate-xls.yml` (beta job) | PRs | Runs `python scripts/validate_xls_template.py <changed files>` — checks section structure |
| `assign-xls-number.yml` | PRs | Detects `XLS-draft-*` directories and assigns the next available XLS number after write-access approval |
| `pre-commit.yml` | PRs, push to master | Runs pre-commit hooks (trailing whitespace, end-of-file, prettier) |
| `deploy.yml` | Push to master | Builds and deploys the GitHub Pages site |
| `discussions.yml` | Daily schedule | Closes/warns on stale GitHub Discussions (inactive ≥1 year) |
| `close-xls-discussions.yml` | Push to master | Closes the GitHub Discussion linked in `proposal-from` when an XLS is merged |

### Running Validation Locally

```bash
pip install -r scripts/requirements.txt

# Validate all XLS preambles
python scripts/xls_parser.py

# Validate structure of changed files
python scripts/validate_xls_template.py XLS-NNNN-slug/README.md

# Build the static site
python scripts/build_site.py
```

---

## Code Style and Conventions

- **Markdown formatting**: enforced by `prettier` via pre-commit. Run `pre-commit run --all-files` or let CI flag issues.
- **No trailing whitespace**, files must end with a newline (`end-of-file-fixer` hook).
- **Folder naming**: `XLS-NNNN-slug` with a 4-digit zero-padded number and lowercase hyphenated slug.
- **Author format**: either `Name (@github-handle)` or `Name <email@example.com>` — both forms are parsed by `xls_parser.py`. Each author must have a name **and** a link; otherwise validation fails.
- **Dates**: always `YYYY-MM-DD`.
- **Section numbering**: XLS documents use numeric section headings (`## 1. Abstract`, `## 2. Motivation`, etc.).
- **Python scripts** in `scripts/` use Python 3.11 and are run directly (no build step needed beyond `pip install -r scripts/requirements.txt`).
- **Templates are normative**: sections from `XLS_TEMPLATE.md` and `AMENDMENT_TEMPLATE.md` are checked by `validate_xls_template.py`. Do not skip required sections or leave template placeholders (bracketed instructions) in merged XLS documents.

---

## PR Checklist (from `pull_request_template.md`)

- Summarize the change and link any associated GitHub Discussion.
- Check the type of change: New XLS Draft / XLS Update / XLS Status Change / Process/Meta / Infrastructure / Documentation.
- Ensure the preamble is correct and complete.
- Do not self-assign XLS numbers (for numbers > 95); use `XLS-draft-<slug>` naming.

---

## Known Gotchas

- **Duplicate XLS numbers**: `xls_parser.py` fails if two folders resolve to the same number. Always use the `XLS-draft-*` naming convention and let CI assign the number.
- **Self-assigned numbers > 95**: the `assign-xls-number.yml` workflow posts a warning comment and blocks the CI if a PR adds a numbered directory (> XLS-0095) without the `has-xls-number` label.
- **Withdrawn XLSes** must include a `withdrawal-reason` field in the preamble or validation fails.
- **Amendment XLSes cannot reach `Final`** until the corresponding rippled PR is merged; `System` XLSes require a merged implementation too.
- **`proposal-from` is required** for all XLSes in the preamble. Missing it causes `validate_xls_preamble` to fail.
- The `build_site.py` script outputs to `scripts/_site/` — this directory is ephemeral and not committed.
- Pre-commit uses pinned SHAs (not tags) for hook repos — update them in `.pre-commit-config.yaml` if upgrading.
