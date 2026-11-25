---
name: spec-from-rippled
description: Update an XLS specification to match rippled. Use when asked to sync a spec with a rippled PR, commit, branch, or release, update an XLS from the implementation, audit a whole spec against a rippled version, reconcile a spec against rippled code, check whether a spec still matches what was built, or write a nested amendment patch (fix* or feature amendment, x.y / x.y.z files) for an existing XLS.
---

# Update a spec from rippled

Reconcile an `XLS-NNNN-slug/README.md` (and its nested patches) in this repo against rippled, and propose the minimal spec edits that make the two agree.

The implementation is the evidence. Every proposed edit cites a rippled `path:line` at a named ref. Never describe behavior that is not in the code you read.

## 1. Choose the mode and the ref

There are two modes:

- **Diff mode.** Reconcile the spec against one change: a PR, a commit, or `base...head` between two refs.
- **Audit mode.** Reconcile the whole spec against the code at one ref, for example a release tag. Use it when no single diff covers the change, or when the spec has never been checked against the code.

**Always ask the user for the ref.** Do not default to `develop`, `master`, the latest tag, or whatever is checked out. In diff mode, ask for both the base and the head (a PR or commit gives both). In audit mode, ask for one ref. Resolve it to a full commit SHA and use that SHA for every citation:

```bash
git -C <rippled> fetch <remote> --tags
git -C <rippled> rev-parse --verify '<ref>^{commit}'
```

If the ref does not resolve, stop and ask. A caller such as `spec-release-sync` may pass the ref in. Then do not ask again.

### Get the code

Diff mode, from a PR or commit (no checkout needed):

```bash
gh pr diff XRPLF/rippled <number>
gh pr view XRPLF/rippled <number> --json title,body,files,baseRefOid,headRefOid
gh api repos/XRPLF/rippled/commits/<sha> --jq '.files[].filename'
```

Diff mode, from a local checkout:

```bash
git -C <rippled> diff <base>...<head> --stat
git -C <rippled> diff <base>...<head>
```

Audit mode: read files at the ref without changing the user's checkout.

```bash
git -C <rippled> show <sha>:<path>
git -C <rippled> grep -n '<Name>' <sha> -- include src
```

For a large diff, work from `--stat` first and read individual files as needed.

## 2. Identify the target spec

In order of preference: the XLS number given by the user or caller; the XLS number in the PR title or body; the amendment name in `include/xrpl/protocol/detail/features.macro`, matched against this repo; or ask. Do not guess between two candidate specs.

Read the parent `README.md` and every nested patch under it (`XLS-NNNN-slug/*/*.md`). The parent's Amendments subsection lists them.

### Amendments at the ref

List each amendment the spec or its patches describe, and read its entry in `features.macro` at the ref:

| Amendment | In `features.macro` at ref | `Supported` | Spec location |
| --------- | -------------------------- | ----------- | ------------- |

- Specify behavior only for amendments present at the ref.
- An amendment in the spec but absent at the ref is a finding (`spec says X, code does not`). Do not delete its text. The author decides.
- An amendment at the ref with `Supported::no` is still specified, but the report says it is not supported at the ref.
- If the code at the ref is gated by an amendment that came after the target XLS (a `fix*` amendment, or a later feature amendment such as `LendingProtocolV1_1`), the edit is a nested patch under that XLS, not a rewrite of the parent. Read [XLS-1 §4.4.4 Subsequent amendments](../../../XLS-0001-xls-process/README.md#444-subsequent-amendments) and follow it. It is the source of truth for patch layout, numbering, parent updates, and the fix-versus-feature split.
- In audit mode, also check the reverse: text in the parent that describes behavior gated by a later amendment belongs in a patch. Report it as a `move-to-patch` finding. Do not move it unless the user asks.

## 3. Map code to spec sections

Read `references/rippled-map.md`.

rippled's tree moves. Treat every path in that table as a hint and confirm it at the ref before relying on it:

```bash
git -C <rippled> ls-tree -r --name-only <sha> | grep -i '<Name>'
git -C <rippled> grep -n '<TxName>' <sha> -- include src | head -30
```

- **Diff mode:** map each changed file to the spec sections it affects.
- **Audit mode:** go the other way. For each spec section that `rippled-map.md` maps to code (fields, flags, failure conditions, state changes, invariants, RPCs), find that code at the ref. Then find code for the spec's ledger entries and transactions that no section covers.

## 4. Read the spec, then propose edits

For each mapped section:

1. Read the current spec text for that section.
2. Decide whether the spec is correct, wrong, incomplete, or describes behavior the code does not have. Say so for each. "Correct" is a useful result.
3. Propose the smallest edit that fixes it, quoting the rippled `path:line` at the ref that justifies it.

Do not restructure sections the code does not touch. Formatting belongs to `xls-template-conformity`. Do not infer a failure condition, a default value, or an invariant that you did not read in the code.

Each nested patch is a delta. Edit the patch for behavior its amendment gates, and edit the parent only for behavior of the original amendment. Keep the parent's amendment-split text in step with the patch (XLS-1 §4.4.4.7).

## 5. Update the preamble

- Bump `updated:` to today's date in every file you edit.
- `implementation:` names the PR that implemented this XLS's amendment. Add or fix it only if it is missing or wrong. Never set it to a release tag or to the ref you audited against.
- Do not change `status:`. Reaching `Final` is a separate decision.

## 6. Verify

Run the `xls-template-conformity` skill on the edited files, or at minimum:

```bash
python scripts/validate_xls_template.py XLS-NNNN-slug/README.md XLS-NNNN-slug/*/*.md
```

## 7. Report

Report in this shape, so that `spec-release-sync` can collect reports across specs:

```markdown
### XLS-NNNN: <title>

Mode: audit | diff. Ref: <ref as given> (<full sha>).

| Amendment | In features.macro | Supported | Spec location |
| --------- | ----------------- | --------- | ------------- |

| Kind | Spec location | rippled evidence | Change |
| ---- | ------------- | ---------------- | ------ |
```

`Kind` is one of these:

- `edited`: the spec was wrong or incomplete, and you changed it.
- `correct`: the spec matches the code. List each section you checked. Do not list every correct line.
- `spec-only`: the spec says X, and the code at the ref does not. Not edited. The author decides.
- `code-only`: the code does X, and no section covers it. Not edited unless the section exists and is incomplete.
- `move-to-patch`: parent text that a later amendment gates.
- `unmapped`: a changed rippled file (diff mode) or a code path (audit mode) you could not tie to a section, with a one-line reason. Some are spec-invisible (refactors, build files, logging). Others mean the spec is missing a section. That call belongs to the author.
- `question`: a design or intent question for the author. State it. Do not answer it.
