# Migrating a spec to the current templates

Read `templates/XLS_TEMPLATE.md` and, for an Amendment spec, `templates/AMENDMENT_TEMPLATE.md` at run time. This file gives the procedure, not the template contents.

## Scope

Migrate a spec only if all of these are true:

- `status` is `Draft`, `Final`, or `Living`. Do not touch `Stagnant`, `Withdrawn`, or `Deprecated` specs. Report them as skipped.
- The spec is in this repository's `master`, not only in an open PR.
- No open PR edits the same file, or the user has said to go ahead anyway. Check with `gh pr list --repo XRPLF/XRPL-Standards --state open --search '<XLS number>'` and the changed-file lists of the results.

`Ecosystem`, `System`, and `Meta` specs follow `XLS_TEMPLATE.md` only. Do not add Amendment sections to them.

## Allowed edits

Only these edits are allowed:

1. **Move** a block of text to the section where the template puts it, for example "Introduction" content into "Motivation", or a transaction's failure list into its `Failure Conditions` subsection.
2. **Rename** a heading to the template name, for example `### Flags` under a ledger entry to `#### 3.1.3. Flags`, or `## 2. Introduction` to `## 2. Motivation`.
3. **Renumber** headings to the template order, and update every internal link and anchor that points at a renamed heading. Check the whole repository for links into this file: `grep -rn 'XLS-NNNN-slug/README.md#' --include='*.md' .`.
4. **Split** one section into template subsections, with each sentence kept whole and in its original order.
5. **Add** a required subsection that the spec has no content for, as a heading with one line: `TODO: content pass.` Never write the content.
6. **Mark** a section `_(Optional)_` or remove an empty optional section.
7. **Preamble:** reorder fields to the XLS-1 order, and bump `updated:`. Do not change any other preamble value.

Anything else is a content change. That includes rewording, merging two lists, changing a field table's values, fixing an error you noticed, converting prose into a table, and deleting text that is not an empty heading. Report it under Content changes and leave it for `spec-from-rippled`.

## Where Amendment sections go

`XLS_TEMPLATE.md` puts the Amendment template inside `## 3. Specification`. A ledger entry, transaction, or RPC section is a subsection of Specification, for example `### 3.1. Ledger Entry: \`Loan\``, with its template subsections one level below. Keep the template's order: STypes, ledger entries, transactions, permissions, RPCs.

A spec that documents a transaction or ledger entry that is already on mainnet uses the same template section with only the subsections it changes, and the exemptions in `beyond-the-template.md` apply.

## Long appendices

Equation glossaries, pseudo-code, and implementation references stay where they are. Put them under `# Appendix` with `## Appendix X: <name>` headings if they are not there already. Do not move normative rules out of an appendix into the Specification. Report them as a question for the content pass.

## Nested patches

Apply the same edits to each `x.y/` file. In addition, check the layout against XLS-1 §4.4.4:

- The H1 includes the patch number (`# 66.2 Lending Protocol Impairment Timing`).
- Template sections are numbered (`### 3.1. Transaction: \`LoanManage\``).
- The folder name is `x.y-amendment-slug`. If it is only `x.y`, report it. Do not rename the folder in a migration PR, because open PRs and external links point at the old path. The rename is its own PR, after the open PRs that touch the folder are merged.

## Check the result

1. `python scripts/validate_xls_template.py --strict <files>` passes, or each remaining error is a `TODO` gap you reported.
2. The words did not change. Compare the text with markup and numbering removed:

   ```bash
   strip() { git show "$1" | sed -E 's/^#+ +([0-9]+\.)*[0-9]*\.? *//; s/[`*_]//g' | tr -s '[:space:]' '\n' | sort; }
   diff <(strip "master:$f") <(strip "HEAD:$f")
   ```

   A word that appears only on one side is a heading rename, a `TODO: content pass.` line, or a content change. Explain each one under Moves, Gaps, or Content changes.

3. `pre-commit run --files <files>` passes.
