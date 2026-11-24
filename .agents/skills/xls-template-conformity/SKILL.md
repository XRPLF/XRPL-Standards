---
name: xls-template-conformity
description: Check that an XLS specification conforms to the XRPL-Standards templates, or migrate a legacy spec to them. Use when asked to check an XLS against the template, validate a spec's structure or preamble, review a draft's format before opening a PR, review changes to an XLS-*/README.md or nested patch file, or reformat an existing spec to the current template.
---

# XLS template conformity

Check one or more `XLS-NNNN-slug/README.md` documents, and the nested amendment patches under them (`XLS-NNNN-slug/*/*.md`, XLS-1 §4.4.4), against `templates/XLS_TEMPLATE.md` and, for Amendment specs, `templates/AMENDMENT_TEMPLATE.md`.

There are two modes:

- **Check** (default). Report what does not conform. Use it for reviews and drafts.
- **Migrate**. Restructure an existing spec to the current templates without changing what it specifies. Use it when the user or `spec-release-sync` asks to reformat a spec. See §7.

The templates are the source of truth. Read them at run time and compare — never work from a remembered copy of their contents.

## 1. Resolve targets

Use the paths given. If none were given, use the changed specs on this branch:

```bash
git diff --name-only master...HEAD -- 'XLS-*/README.md' 'XLS-*/*/*.md'
```

A target that is a parent `README.md` includes its nested patches. Check them in the same pass.

## 2. Run the validator first

The repo already machine-checks preamble fields, required sections, Amendment subsection presence, and leftover template placeholders. Run it; do not reimplement it.

```bash
pip install -r scripts/requirements.txt
python scripts/validate_xls_template.py XLS-NNNN-slug/README.md XLS-NNNN-slug/*/*.md   # or --all
```

In migrate mode, also run with `--strict`. Strict mode does not exempt legacy specs, and it finds template sections nested under `## 3. Specification`, where `XLS_TEMPLATE.md` puts them. A migrated Amendment spec must pass `--strict`. In check mode, report `--strict` errors only for specs that already use the template sections.

Report every error it prints verbatim, as `blocking`. Do not restate those findings in your own words or add a second comment about the same line.

If the validator cannot run (no Python, no network — it does HEAD requests to xrpl.org), say so explicitly and continue with the manual passes.

## 3. Compare against the templates

Read `templates/XLS_TEMPLATE.md`. If the preamble says `category: Amendment`, also read `templates/AMENDMENT_TEMPLATE.md`.

Check that the spec's section structure, ordering, numbering, and per-section content match what the template asks for. The validator only checks that required sections _exist_; you are checking that each one actually does its job, and that optional sections were omitted deliberately rather than forgotten.

## 4. Apply the checks the template and validator cannot express

Read `references/beyond-the-template.md` and work through it. It also lists the exemptions the validator already applies, so you do not re-flag them.

## 5. Report

Finish every validator, template, and beyond-the-template pass before reporting. Build the complete finding set, verify it, and remove duplicates. Do not report findings incrementally or stop after the first defect.

For an interactive conformity check, use one table grouped by severity, most severe first:

| Severity | Location                      | Finding | Suggested fix |
| -------- | ----------------------------- | ------- | ------------- |
| blocking | `XLS-NNNN-slug/README.md:120` | ...     | ...           |

- `blocking` — validator errors, missing required content, an unsafe or unimplementable statement.
- `should-fix` — a concrete defect that can cause divergent implementation or incorrect client behavior.

Do not report nits. Suppress spelling, grammar, phrasing, verbosity, naming consistency, field qualification, and optional clarity suggestions unless they meet one of the two severity thresholds above.

Never report anything CI already owns: whitespace, line endings, EOF newlines, markdown table alignment (prettier owns it), or the presence of fields and sections the validator checks.

## 6. Offer to fix

Offer to apply the mechanical fixes (renumbering, missing table columns, JSON/table mismatches). Leave design questions to the author — state the question, do not answer it for them.

## 7. Migrate mode

Migrate mode restructures a spec so that it passes `--strict` and matches the templates. The change is mechanical: feature owners do not review it, so it must not change what the spec specifies. Read `references/migration.md` and follow it.

Apply the edits, then run §2 to §4 on the result. Report in the §5 table, plus:

- **Moves.** One line for each block of text you moved or renamed, from heading to heading.
- **Gaps.** Each required subsection that the spec does not have the content for. You add the heading with a `TODO` line, not invented content.
- **Content changes.** Everything that is not a pure move, rename, or renumber. This list must be empty. If an edit cannot be made without changing meaning, do not make it. Report it here and leave it for the content pass.
