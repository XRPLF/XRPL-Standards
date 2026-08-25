# Checks the templates and the validator cannot express

`templates/XLS_TEMPLATE.md` and `templates/AMENDMENT_TEMPLATE.md` define the required structure, and `scripts/validate_xls_template.py` checks that structure mechanically. This file holds only what neither of them can check: agreement _between_ parts of a spec, and whether the prose actually says something.

Nothing here duplicates a template section list. If a check below ever becomes expressible in the template or the validator, delete it from this file.

## Cross-artifact agreement

- **Example JSON vs. field table.** Every field marked required in the Fields table appears in the Example JSON. Every field in the Example JSON appears in the table. Values are of the declared JSON type. This applies to ledger entries (§2.2 vs §2.11), transactions (§3.1 vs §3.7), and RPCs (§5.1/§5.2 vs §5.4/§5.5).
- **Field names.** Spelled identically in the table, the prose, the failure conditions, and the JSON. `MPTokenIssuanceID` in one place and `MPTIssuanceID` in another is a defect, not a style choice.
- **Internal type vs. JSON type.** A `UINT64` rendered in JSON as a string, an `AMOUNT` as an object or string, an `ACCOUNT` as an r-address — the pair has to be coherent.
- **Failure conditions vs. fields.** Every conditionally-required field has a failure condition covering its absence, and every failure condition names a field or state that exists in the spec.
- **State changes vs. ledger entries.** Everything §3.5 says the transaction creates, modifies, or deletes is a ledger entry the spec defines, or an existing one it names.

## Values that have to be checked against reality

Do not assert any of these from memory. Check rippled or xrpl.org and cite what you checked.

- **Flag values** are distinct powers of two, and do not collide with existing values for the same object or transaction type. Existing values: `include/xrpl/protocol/TxFlags.h` and `include/xrpl/protocol/LedgerFormats.h` in rippled.
- **Error codes** referenced in Failure Conditions exist in `include/xrpl/protocol/TER.h` (transactions) or `include/xrpl/protocol/ErrorCodes.h` (RPCs). A spec that proposes a _new_ code has to say why the existing codes are insufficient — flag it if it does not.
- **`tem` vs `tec`.** Data-verification failures (malformed input, checkable without ledger state) are `tem` and belong in §3.4.1. Failures that need ledger state are `tec`/`ter`/`tef`/`tel` and belong in §3.4.2. A `tem` that requires reading the ledger, or a `tec` for a purely malformed field, is misplaced.
- **Key space value** (§2.1) is not already taken by another entry type — see `include/xrpl/protocol/Indexes.h` and any pending XLS in this repo.
- **`requires:` preamble field** names XLS numbers that exist in this repo and that the spec genuinely depends on.
- **Referenced XLS numbers** in prose exist. Relative links and internal anchors resolve.

## Substance, not presence

The validator confirms a section exists. These need a reader:

- **Security Considerations** is specific to this proposal — threats, failure modes, what an adversary gains. A generic paragraph about "users should be careful" is a `blocking` finding: XLS-1 forbids `Final` without a sufficient one.
- **Rationale** explains _why_ this design over the alternatives, and names the alternatives.
- **Abstract** is readable standalone and matches what the spec actually does.
- **Invariants** (§2.9) are stated over before/after state and are actually checkable, not restatements of the field table.
- **Amendment activation.** Where behavior differs before and after activation, the spec says so. Silence about pre-activation behavior on a change to an existing transaction or entry is a `should-fix`.
- **Backwards compatibility.** If the change breaks an existing client, the section exists and says how.
- **RFC 2119.** If the spec declares RFC 2119 / RFC 8174, normative statements use MUST / SHOULD / MAY, not "will" or "should probably". If it does not declare them, do not demand them.

## Naming

- Transaction names follow `<LedgerEntryName><Verb>`, e.g. `VaultSet`, `VaultDelete`.
- RPC method names are `snake_case`; the §2.10 RPC Name (for `account_objects` / `ledger_data` filtering) is `snake_case` too.
- Ledger entry and field names are `PascalCase`.
- `title` is at most 44 characters and carries no "XLS" prefix or number.
- `description` is one short sentence, at most 140 characters.

## Exemptions — do not flag these

The validator already applies these, and so should you:

- For a **ledger entry type already live on XRPL mainnet**, these subsections are optional: Object Identifier (2.1), Ownership (2.4), Reserves (2.5), Deletion (2.6), RPC Name (2.10). Only require them if the spec changes that aspect.
- For a **transaction type already live on mainnet**, Transaction Fee (3.3) is optional.
- A spec that predates the Amendment template and uses no `Ledger Entry:` / `Transaction:` / `RPC:` sections at all is treated as legacy — the validator skips Amendment structure checks. Do not demand a wholesale restructure of a legacy spec in a PR that only touches a few lines; say it is out of scope for the diff.

## Owned by CI — never report

Trailing whitespace, line endings, missing EOF newline, markdown or table formatting and alignment (prettier owns tables — never propose realigning one), missing preamble fields, missing required sections, missing Amendment subsections, leftover template placeholders. These all fail CI on their own.
