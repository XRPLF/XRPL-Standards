# Contributing to XRPL Standards

> [!NOTE]
> This document summarizes how to contribute new XRP Ledger Standards (XLSes). The authoritative, detailed definition of the process is **[XLS-1: XLS Process and Guidelines](./XLS-0001-xls-process/README.md)**. If anything here conflicts with XLS-1, XLS-1 wins.

The work of the [XRP Ledger](https://xrpl.org) community is open, collaborative, and welcoming of all contributors participating in good faith. Part of that effort involves standardization, and this document outlines how anyone can contribute to that process.

## 1. Licensing

Any XRPL Standards document can be referred to interchangeably as an "XLS", "XRPL Standard", or "document". Copyright on all content is subject to the terms of this [license](LICENSE), and all contributors grant everyone a royalty-free license to use their contributions, including the following grants:

- **Copyright**: a royalty-free license to anyone to use any contributions submitted to this repository.
- **Patent**: a commitment to license on a royalty-free basis any essential patent claims relating to any contributions in this repository.

## 2. Overview of the XLS process (per XLS-1)

XLS-1 defines both **categories** of XLSes and their **lifecycle statuses**.

- **Categories** (`category` field in the XLS preamble):
  - `Amendment`: changes that require an XRP Ledger amendment.
  - `System`: changes that affect XRPL protocol behavior (RPCs, P2P, etc.) but do not require an amendment.
  - `Ecosystem`: off-chain or community standards (metadata, registries, etc.).
  - `Meta`: standards about the XLS process itself (like XLS-1).

- **Statuses** (`status` field in the XLS preamble):
  - `Idea`: pre-draft, typically discussed only in GitHub Discussions.
  - `Proposal`: a fairly fleshed-out proposal, still only in Discussions.
  - `Draft`: the first formally tracked stage in this repo; XLS numbers are assigned here by XLS Editors.
  - `Final`: the final, stable form of the XLS. Only errata and non-normative clarifications may be added.
  - `Living`: a spec intended to be continuously updated (for example, XLS-1 itself).
  - `Deprecated`: a `Final` XLS that is no longer recommended.
  - `Stagnant`: a `Draft` that has seen no activity for a long period.
  - `Withdrawn`: withdrawn by the author(s); cannot be resurrected under the same XLS number.

The sections below explain how to move through these stages. For all edge cases and full definitions, see [XLS-1 §4: XLS Process](./XLS-0001-xls-process/README.md#4-xls-process).

## 3. Start with a GitHub Discussion (Idea / Proposal)

Before opening a PR with any kind of formal proposal, **start with a GitHub Discussion**.

1. Go to the [XRPL-Standards Discussions](https://github.com/XRPLF/XRPL-Standards/discussions).
2. Choose a category that matches your intended XLS `category`:
   - `Amendment`, `System`, `Ecosystem`, or `Meta`.
3. Use the **status** in your title to indicate maturity:
   - For early concepts, treat them as **Ideas**.
   - Once the concept is fairly fleshed out, treat it as a **Proposal**.

#### 3.1. Discussion titles

To make Discussions easier to scan, we recommend titles of the form:

```text
[<Category> <Idea|Proposal>: <Short descriptive title>]
```

For example:

- `[Amendment Idea: In-ledger governance tokens]`
- `[Ecosystem Proposal: Extended validator TOML metadata]`

This keeps the Discussion aligned with the `category` and `status` terminology from XLS-1.

#### 3.2. Gather feedback and iterate

Discussions are the right place for early work-in-progress: ask questions, propose alternatives, and make sweeping changes. Collecting such feedback is required before moving forward in the specification process.

When your idea has converged into a coherent design and has community interest, you are ready to move toward a **Draft XLS** via a PR.

#### 3.3. Closing or archiving Discussions

XLS-1 defines rules for stale proposals and ideas (see [§4.5](./XLS-0001-xls-process/README.md#45-stale-proposalsideas)). In short:

- Discussions are checked for staleness after 90 days.
- If there is no activity for another 30 days, they may be closed and locked.
- Authors can ask maintainers to reopen stale Discussions later.

When you open a PR for a Draft XLS, you should:

- Close the original Discussion (if it's still open).
- Link the PR from the original Discussion (for traceability).
- Optionally, add a final comment pointing to the PR so others know where to continue the conversation.

## 4. Creating a Draft XLS (Pull Request)

Once there is a clear Proposal with community interest, you can open a PR to add a **Draft** XLS to this repository.

At a high level this looks like:

1. **Create a new directory for your draft.**
   - Use a temporary name such as `XLS-draft-<short-title>` while the number is being assigned.
2. **Copy the template.**
   - Base your document on [XLS_TEMPLATE.md](./templates/XLS_TEMPLATE.md).
3. **Fill out the required sections.**
   - Follow [XLS-1 §4.3: Format: Drafts and Onward](./XLS-0001-xls-process/README.md#43-format-drafts-and-onward), especially the required preamble and sections.
   - Before you open the PR, check your draft against the templates. Run the validator, and use the `xls-template-conformity` skill if your editor supports Agent Skills (see [§8](#8-ai-agents-and-review-bots)):

     ```bash
     pip install -r scripts/requirements.txt
     python scripts/validate_xls_template.py XLS-draft-<short-title>/README.md
     ```

4. **Open a pull request.**
   - Link the associated Discussion in the PR description.
   - Make it clear which `category` you are targeting and that this is intended to be a `Draft`.
5. **Work with XLS Editors.**
   - Editors review for completeness, formatting, and clarity (see [XLS-1 §7](./XLS-0001-xls-process/README.md#7-xls-editors)).
   - Editors assign the official XLS number and update the directory name to `XLS-<NNNN>-<short-title>`.
   - The `xls` and `status` fields in the preamble are updated to reflect the assigned number and `Draft` status before merge.

After the PR is merged, your XLS is an officially tracked **Draft** in this repository.

## 5. Moving from Draft to Final (or Living)

Promotion from `Draft` to `Final` (or `Living`) is governed by XLS-1 (see [§4](./XLS-0001-xls-process/README.md#4-xls-process)). In summary:

- A `Final` XLS is considered the canonical form of the standard.
  - Only errata and non-normative clarifications should be added afterward.
- For **Amendment** and **System** XLSes, an XLS cannot be `Final` until the corresponding implementation (for example, in `rippled`) has been merged.
- For **Ecosystem** and **Meta** XLSes, there should be at least one complete implementation or clear adoption before moving to `Final`.
- Some documents (including XLS-1) are explicitly marked `Living` and are expected to evolve over time instead of reaching `Final`.

Requests to move a `Draft` to `Final` (or `Living`) should be made via a PR that updates the `status` field in the preamble and, if applicable, links to implementations.

## 6. Stagnant, Withdrawn, and Deprecated XLSes

XLS-1 defines additional statuses that describe the long-term state of a spec:

- **Stagnant**: a `Draft` that has had no activity for at least 6 months.
- **Withdrawn**: an XLS that the author(s) have actively withdrawn; this state has finality and the number should not be reused.
- **Deprecated**: a `Final` XLS that is no longer recommended. This is typically chosen when a better alternative exists or when the functionality is being phased out.

The precise rules for these transitions, and how they are recorded, are described in [XLS-1 §4](./XLS-0001-xls-process/README.md#4-xls-process).

## 7. Ownership and Editors

The roles and responsibilities around XLS authorship and editing are defined in [XLS-1 §6–7](./XLS-0001-xls-process/README.md#6-xls-ownership).

- **Authors** own and champion their XLSes, shepherding them through the process and building community consensus.
- **XLS Editors** (maintainers of this repository):
  - Help ensure proposals are complete, well-structured, and follow the required format.
  - Assign XLS numbers and merge PRs once they meet the bar.
  - Do **not** decide which technical direction is “correct” when there are competing proposals; their role is editorial and administrative.

If you are unsure how to proceed at any step, open a Discussion or PR and explicitly ask for help from the XLS Editors; they will guide you according to XLS-1.

## 8. AI agents and review bots

This repository ships shared instructions and [Agent Skills](https://agentskills.io) so that AI assistants help with XLS work in a consistent way. Using them is optional; contributions are judged on the spec, not on the tooling that produced it.

### 8.1. Automated review

Two bots may comment on your PR:

- **GitHub Copilot code review**, which reads [`.github/copilot-instructions.md`](./.github/copilot-instructions.md) and [`.github/skills/code-review/SKILL.md`](./.github/skills/code-review/SKILL.md).
- **Ripple's `@ai-review` bot** (internal; triggered by an `@ai-review` or `/ai-review` comment), which reads the same guidance through [`.ai-review/instructions.md`](./.ai-review/instructions.md).

Both are advisory. A human XLS Editor still reviews and merges. If a bot is wrong, say so on the thread and move on — and if it is wrong in a way that will recur, fix the guidance rather than arguing with it case by case.

### 8.2. Skills

Two skills live under `.agents/skills/`:

| Skill                     | What it does                                                                                               |
| ------------------------- | ---------------------------------------------------------------------------------------------------------- |
| `xls-template-conformity` | Checks an XLS against `templates/` and the validation scripts, and reports what needs fixing.              |
| `spec-from-rippled`       | Updates a spec to match a rippled PR, commit, or local branch, citing the implementation for every change. |

Cursor, Codex CLI, Gemini CLI, and Augment discover `.agents/skills/` directly. Claude Code reads them through symlinks in `.claude/skills/`.

### 8.3. Keep the guidance in sync

Agent instructions are duplicated across paths because each tool looks in a different place. **If your PR changes one of these files, check the others in the same PR** — a stale copy teaches a reviewer the wrong rule, which is worse than no copy at all.

[`.github/copilot-instructions.md` § Maintaining the AI instruction surface](./.github/copilot-instructions.md#maintaining-the-ai-instruction-surface) lists every file, which tool reads it, and which ones are symlinks. Start there. In short:

- Add a skill under `.agents/skills/<name>/`, and add the matching `.claude/skills/<name>` symlink.
- Put review rules in the Review Guidelines section, not scattered across skills.
- Skills read `templates/` and run `scripts/validate_xls_template.py` at run time rather than restating them, so that changing a template does not require changing a skill. Keep it that way.

The same applies in reverse: a PR that changes `templates/`, the validation scripts, or the XLS process should check whether the AI guidance still describes them correctly.
