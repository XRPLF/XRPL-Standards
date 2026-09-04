---
name: xls-template-conformity
description: Check that an XLS specification conforms to the XRPL-Standards templates. Use when asked to check an XLS against the template, validate a spec's structure or preamble, review a draft's format before opening a PR, or review changes to an XLS-*/README.md file.
---

# XLS template conformity

Check one or more `XLS-NNNN-slug/README.md` documents against `templates/XLS_TEMPLATE.md` and, for Amendment specs, `templates/AMENDMENT_TEMPLATE.md`.

The templates are the source of truth. Read them at run time and compare — never work from a remembered copy of their contents.

## 1. Resolve targets

Use the paths given. If none were given, use the changed specs on this branch:

```bash
git diff --name-only master...HEAD -- 'XLS-*/README.md'
```

## 2. Run the validator first

The repo already machine-checks preamble fields, required sections, Amendment subsection presence, and leftover template placeholders. Run it; do not reimplement it.

```bash
pip install -r scripts/requirements.txt
python scripts/validate_xls_template.py XLS-NNNN-slug/README.md   # or --all
```

Report every error it prints verbatim, as `blocking`. Do not restate those findings in your own words or add a second comment about the same line.

If the validator cannot run (no Python, no network — it does HEAD requests to xrpl.org), say so explicitly and continue with the manual passes.

## 3. Compare against the templates

Read `templates/XLS_TEMPLATE.md`. If the preamble says `category: Amendment`, also read `templates/AMENDMENT_TEMPLATE.md`.

Check that the spec's section structure, ordering, numbering, and per-section content match what the template asks for. The validator only checks that required sections _exist_; you are checking that each one actually does its job, and that optional sections were omitted deliberately rather than forgotten.

## 4. Apply the checks the template and validator cannot express

Read `references/beyond-the-template.md` and work through it. It also lists the exemptions the validator already applies, so you do not re-flag them.

## 5. Report

One table, grouped by severity, most severe first:

| Severity | Location                      | Finding | Suggested fix |
| -------- | ----------------------------- | ------- | ------------- |
| blocking | `XLS-NNNN-slug/README.md:120` | ...     | ...           |

- `blocking` — validator errors, missing required content, an unsafe or unimplementable statement.
- `should-fix` — real defect that does not block merge.
- `nit` — wording or consistency.

Never report anything CI already owns: whitespace, line endings, EOF newlines, markdown table alignment (prettier owns it), or the presence of fields and sections the validator checks.

## 6. Offer to fix

Offer to apply the mechanical fixes (renumbering, missing table columns, JSON/table mismatches). Leave design questions to the author — state the question, do not answer it for them.
