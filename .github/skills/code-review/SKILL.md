---
name: code-review
description: Review a pull request in XRPL-Standards. Use for any PR in this repository, especially one that changes an XLS-*/README.md, the templates, or the validation scripts.
---

# Reviewing a PR in XRPL-Standards

This repository holds prose specifications, not shipping code. A review's job is to find **spec defects**: ambiguity, internal inconsistency, missing normative detail, unsafe design, or a claim that contradicts the implementation.

## Complete the review before commenting

Analyze the complete PR before submitting any comments:

1. Read the PR description and complete diff.
2. Inspect every changed file and the unchanged context needed to validate it.
3. For each changed normative behavior, check the affected field tables, failure conditions, state changes, invariants, formulas, examples, RPCs, parent specification, and amendment patches.
4. Build the complete candidate finding set privately.
5. Verify each candidate, remove duplicates and previously addressed findings, then submit one review for the current HEAD commit.

Do not publish findings incrementally as they are discovered. Do not stop after finding the first valid issue.

## Follow the repository guidelines

Read [`.github/copilot-instructions.md`](../../copilot-instructions.md) — the "Review Guidelines (for AI reviewers)" section is normative for this review. It covers what CI already owns, the process checks, evidence standards, and comment etiquette.

## For any changed `XLS-*/README.md` or nested patch file (`XLS-*/*/*.md`)

Follow [`.agents/skills/xls-template-conformity/SKILL.md`](../../../.agents/skills/xls-template-conformity/SKILL.md), including its `references/beyond-the-template.md`. It is the same procedure human contributors run, and it reads `templates/` at review time, so it cannot drift from them.

## Never flag

Trailing whitespace, line endings, missing EOF newline, markdown or table formatting (prettier owns table alignment — never suggest realigning a table), missing preamble fields, missing required sections, missing Amendment subsections, leftover template placeholders.

Every one of these fails CI on its own. A comment about them is pure noise.

Also suppress spelling, grammar, phrasing, verbosity, naming consistency, field qualification, and optional clarity suggestions unless they create two plausible protocol interpretations or would cause incorrect implementation or client behavior.

Also never flag:

- Predictions that CI will fail. CI reports its own failures.
- Nested amendment patches (`XLS-NNNN-name/NN.N/...`) being outside the top-level site glob or validator. That is intentional.
- A link to a file that a named open PR adds, when the PR states the merge order.
- Byte-level encoding for values serialized with the standard XRPL binary format, or inlined proof constructions when the spec names an external construction.
- Ordering or composition rules between two existing specs that the PR does not change.

## Check current behavior against rippled, not other specs

Older XLS documents can be stale. When a spec disagrees with another XLS, check rippled `develop` before deciding which is wrong. A Draft may lead the implementation on purpose. Do not cite unimplemented proposals (such as XLS-49) as constraints. Amendment-gated operators often reverse between branches; read the gate before calling an operator wrong.

## One defect, one comment

If the same defect appears in several places, or on both the parent spec and its patch, post one comment and list the other lines in it.

## Avoid repeat rounds

Read existing review threads before submitting the review. Do not repeat an issue that was already reported, resolved, answered, or made outdated. Reopen it only if the same defect still exists at the current HEAD, and explain specifically why the earlier response or change did not resolve it.

An author reply of "intended", "out of scope", "separate PR", or a reasoned disagreement answers the thread. Do not reopen it, and do not post the same request on another line with new wording.

## Note on symlinks

`.ai-review/instructions.md` is a committed symlink (git mode `120000`). If your view of the tree does not resolve it, it will look absent or look like a one-line file containing a path. Do not report it as missing or malformed.

The `.claude/skills/<name>/SKILL.md` files are deliberate stubs: `name` and `description` frontmatter, which Claude Code needs to discover the skill, plus one line pointing at `.agents/skills/<name>/SKILL.md`, which holds the procedure. Do not report them as incomplete, and do not propose removing the frontmatter.
