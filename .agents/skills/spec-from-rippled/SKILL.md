---
name: spec-from-rippled
description: Update an XLS specification to match changes made in rippled. Use when asked to sync a spec with a rippled PR or commit, update an XLS from the implementation, reconcile a spec against rippled code, or check whether a spec still matches what was built.
---

# Update a spec from rippled changes

Reconcile an `XLS-NNNN-slug/README.md` in this repo against a change in rippled, and propose the minimal spec edits that make the two agree.

The implementation is the evidence. Every proposed edit cites a rippled `path:line`. Never describe behavior that is not in the code you read.

## 1. Get the diff

**From a PR or commit URL** (no checkout needed):

```bash
gh pr diff XRPLF/rippled <number>
gh pr view XRPLF/rippled <number> --json title,body,files
# or, for a commit:
gh api repos/XRPLF/rippled/commits/<sha> --jq '.files[].filename'
```

**From a local checkout** (e.g. `~/Documents/rippled-all/develop`):

```bash
git -C <rippled> diff develop...<branch> --stat
git -C <rippled> diff develop...<branch>
```

Ask which one to use if the request is ambiguous. For a large diff, work from `--stat` first and read individual files as needed.

## 2. Identify the target spec

In order of preference: the XLS number in the PR title or body; the amendment name added to `include/xrpl/protocol/detail/features.macro`, matched against this repo; or ask. Do not guess between two candidate specs.

## 3. Map changed files to spec sections

Read `references/rippled-map.md`.

rippled's tree moves — transactors and invariants were recently relocated under `src/libxrpl/tx/`. Treat every path in that table as a hint and confirm it before relying on it:

```bash
git -C <rippled> ls-files '*transactors*' | head
git -C <rippled> grep -n "TxName" -- include src | head -30
```

## 4. Read the spec, then propose edits

For each mapped change:

1. Read the current spec text for that section.
2. Decide whether the spec is wrong, incomplete, or already correct. Say so for each — "already correct" is a useful result.
3. Propose the smallest edit that fixes it, quoting the rippled `path:line` that justifies it.

Do not restructure sections the diff does not touch. Do not infer a failure condition, a default value, or an invariant that you did not read in the code.

## 5. Update the preamble

- Bump `updated:` to today's date.
- Add or refresh `implementation:` if this PR is the reference implementation.
- Do not change `status:` — an Amendment or System XLS reaching `Final` is a separate decision, and needs the rippled PR merged first.

## 6. Verify

Run the `xls-template-conformity` skill on the edited spec, or at minimum:

```bash
python scripts/validate_xls_template.py XLS-NNNN-slug/README.md
```

## 7. Report what did not map

List every changed rippled file you could not tie to a spec section, with a one-line reason. Some are genuinely spec-invisible (refactors, build files, logging); others mean the spec is missing a section. That call belongs to the author, so surface it rather than deciding it.
