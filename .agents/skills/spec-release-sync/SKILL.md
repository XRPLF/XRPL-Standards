---
name: spec-release-sync
description: Bring many XLS specifications in line with a rippled release, one PR per XLS. Use when asked to update all specs (or a list of specs) for a rippled release, run the per-release spec sync, mass-update or migrate XLSes to the current template and to rippled, or do a dry run of that process on a few specs.
---

# Sync specs with a rippled release

Run `xls-template-conformity` and `spec-from-rippled` over a set of specs for one rippled release, and open one PR per XLS for its feature owners to review.

This skill only orchestrates. It does not check format or read rippled itself. Each spec still goes through the other two skills, in full.

## 1. Inputs

Ask the user for each of these. Do not guess any of them:

1. **Release ref.** The rippled tag or commit to sync to, for example `3.5.0`. Resolve it to a full SHA (`git -C <rippled> rev-parse --verify '<ref>^{commit}'`). If it does not resolve, stop.
2. **Previous release ref**, or "none". With a previous ref, the run is diff-driven. With "none", every spec in scope gets a full audit. Use "none" for the first run.
3. **Scope.** "All", or a list of XLS numbers, for example `64, 65, 66` for a dry run.
4. **Mode.** `full` (format and content, the default), or `format-only` (§4.1 only, for a one-time migration that lands before content review starts).
5. **rippled checkout.** A local path, so that `git show <sha>:<path>` works. Do not check out the ref in it. Read through `git show` and `git grep <sha>`.

Then record the run settings at the top of the run log (§6), and pass the resolved SHAs to `spec-from-rippled` so that it does not ask again.

## 2. Select specs

Start from the scope. Drop and report each spec that:

- has `status` `Stagnant`, `Withdrawn`, or `Deprecated`, or
- has category `Ecosystem` or `Meta`. The content pass does not apply to them. In `format-only` mode, keep them.

Then, with a previous release ref:

```bash
git -C <rippled> diff --stat <prev-sha> <sha> -- include src
git -C <rippled> diff <prev-sha> <sha> -- include/xrpl/protocol/detail/features.macro
```

Keep a spec if an amendment it describes changed in `features.macro`, or if the diff touches a file that `spec-from-rippled`'s `references/rippled-map.md` maps to one of its sections. Report every spec you drop with the reason "no change between refs". Report every changed rippled file that maps to no spec in scope. A file that maps to no spec in the scope can be a missing spec, which is a finding for the user.

Without a previous ref, keep every spec that is still in scope.

## 3. Order

Process specs in dependency order: an XLS after every XLS it names in `requires:`, and a parent before its own patches. A content change to a parent can change what a dependent spec must say, for example XLS-66 depends on the XLS-65 Vault phases.

Before you start, list open PRs that touch each spec:

```bash
gh pr list --repo XRPLF/XRPL-Standards --state open --json number,title,files \
  --jq '.[] | select(any(.files[]; .path | startswith("XLS-NNNN-"))) | "\(.number) \(.title)"'
```

If a spec has an open PR, ask the user whether to skip it, wait, or go ahead. A sync PR that conflicts with an author's open PR costs the author more than it saves.

## 4. Per spec

Work on one branch per XLS, from an up-to-date `master`. Name it with the user's branch prefix, if they have one, and `xls-NNNN-sync-<release>`.

### 4.1. Format commit

Run `xls-template-conformity` in migrate mode on the parent and its nested patches. Commit the result alone:

```
docs(XLS-NNNN): reformat to current template
```

The migration report must have no content changes (see that skill's `references/migration.md`). If it has some, stop for that spec and ask the user. If the spec already conforms, there is no commit. Report "format: no change".

### 4.2. Content commit

Skip in `format-only` mode.

Run `spec-from-rippled`:

- With a previous ref: diff mode, `<prev-sha>...<sha>`.
- Without one: audit mode at `<sha>`.

Commit the edits alone:

```
docs(XLS-NNNN): sync with rippled <release>
```

If the report has no `edited` rows, there is no commit. Report "content: no change".

Keeping the two commits separate lets an owner review the content commit only, and lets an Editor merge a format-only PR without the owners.

### 4.3. Verify

```bash
python scripts/validate_xls_template.py --strict XLS-NNNN-slug/README.md XLS-NNNN-slug/*/*.md
pre-commit run --files <changed files>
```

### 4.4. Open the PR

Ask the user before you push or open any PR. Show the list of PRs that the run will open, with titles, branches, and reviewers, and wait for approval. One approval may cover the whole list.

Use `.github/pull_request_template.md`. Fill in each section:

- **High Level Overview of Change:** one or two sentences.
- **Context of Change:** the release ref and SHA, the mode, and the previous ref if any. Paste the `spec-from-rippled` report. List the `spec-only`, `code-only`, `move-to-patch`, and `question` rows first, because they need the owner's decision.
- **Type of Change:** `XLS Update`.
- State the review deadline from §5.

Request review from the owners (§5). Open the PR as a draft if the content report has a `question` row.

## 5. Owners and the review window

The owners of an XLS are the people in its `author:` preamble field. Find their GitHub handles from the commit history of the spec (`git log --format='%an %ae' -- XLS-NNNN-slug/ | sort | uniq -c`) or ask the user. If the user gives an override list (for example, for authors who have left), use it instead. Record the handle you used for each owner in the run log. Never guess a handle.

The review window is 2 weeks from the day the PR is opened. Write the deadline date in the PR body. After the deadline, the user decides what to do with a PR that has no owner review. This skill does not merge, approve, or change any PR after it opens it.

## 6. Run log

Keep one Markdown table for the run, in a file the user names (default `release-sync-<release>.md` in the repository root, not committed):

| XLS | Format | Content | Open questions | PR  | Owners | Opened | Deadline | State |
| --- | ------ | ------- | -------------- | --- | ------ | ------ | -------- | ----- |

- `Format` and `Content` are `changed`, `no change`, `skipped (<reason>)`, or `blocked (<reason>)`.
- `Open questions` is the number of `spec-only`, `code-only`, `move-to-patch`, and `question` rows.
- `State` is `open`, `approved`, `changes requested`, `merged`, or `past deadline`.

To update an existing run, read the log, then refresh each PR's state:

```bash
gh pr view <number> --repo XRPLF/XRPL-Standards --json state,reviewDecision,reviews
```

At the end of a run, give the user the table and the list of dropped specs and unmapped rippled files from §2.

## 7. Dry run

For a dry run, use a small scope with one dependency chain (for example `64, 65, 66`), and stop before §4.4. Give the user the run log, both commits per spec, and the reports. List each step of this skill that was wrong, unclear, or needed a manual fix, so that the skill can be fixed before the full run.
