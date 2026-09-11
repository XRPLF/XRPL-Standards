# rippled artifact → XLS section map

Section numbers refer to `templates/AMENDMENT_TEMPLATE.md`.

Paths are **hints, not constants** — rippled reorganizes its tree periodically. Confirm each with `git -C <rippled> ls-files` or `git grep` before relying on it. The paths below were current as of the post-rearchitecture `develop` layout (transactors and invariants under `src/libxrpl/tx/`, RPC handlers under `src/xrpld/rpc/handlers/`).

## Protocol definitions

| rippled artifact                                                      | Spec section                        | What to extract                                                                |
| --------------------------------------------------------------------- | ----------------------------------- | ------------------------------------------------------------------------------ |
| `include/xrpl/protocol/detail/features.macro`                         | preamble, §1 Abstract               | amendment name, `Supported::yes/no`, `VoteBehavior`                            |
| `include/xrpl/protocol/detail/sfields.macro`                          | §2.2 / §3.1 Fields                  | field name, internal type (`UINT32`, `AMOUNT`, `ACCOUNT`, …), `SField` code    |
| `include/xrpl/protocol/detail/ledger_entries.macro`                   | §2 Ledger Entry, §2.10 RPC Name     | entry type name and value, `snake_case` RPC name, required/optional field list |
| `include/xrpl/protocol/detail/transactions.macro`                     | §3 Transaction                      | transaction type name and value, required/optional field list                  |
| `include/xrpl/protocol/detail/permissions.macro`                      | §4 Permission                       | granular permission name and value                                             |
| `include/xrpl/protocol/TxFlags.h`                                     | §3.2 Flags                          | `tf` values; confirm powers of two and no collision                            |
| `include/xrpl/protocol/LedgerFormats.h`                               | §2.3 Flags                          | `lsf` values                                                                   |
| `include/xrpl/protocol/Indexes.h`, `src/libxrpl/protocol/Indexes.cpp` | §2.1 Object Identifier              | keylet function, key space value, hashed inputs                                |
| `include/xrpl/protocol/TER.h`                                         | §3.4 Failure Conditions             | `tem`/`tec`/`ter`/`tef`/`tel` codes, including newly added ones                |
| `include/xrpl/protocol/ErrorCodes.h`                                  | §5.3 RPC Failure Conditions         | RPC error codes                                                                |
| `include/xrpl/protocol/InnerObjectFormats.h`                          | §2.2 / §3.1 Fields                  | shape of any new inner object / array element                                  |
| `include/xrpl/protocol/Fees.h`, `Protocol.h`                          | §2.5 Reserves, §3.3 Transaction Fee | reserve increments, non-standard fee logic                                     |

## Transaction behavior

| rippled artifact                                                              | Spec section                   | What to extract                                                                |
| ----------------------------------------------------------------------------- | ------------------------------ | ------------------------------------------------------------------------------ |
| `src/libxrpl/tx/transactors/<TxName>.cpp` — `preflight`                       | §3.4.1 Data Verification       | every `tem` return: the malformed-input conditions, in order                   |
| same — `preclaim`                                                             | §3.4.2 Protocol-Level Failures | every `tec`/`ter` return that needs ledger state                               |
| same — `doApply`                                                              | §3.5 State Changes, §3.4.2     | entries created/modified/deleted, owner count changes, remaining `tec` returns |
| same — `calculateBaseFee`                                                     | §3.3 Transaction Fee           | any non-standard fee                                                           |
| same — `makeTxConsequences`                                                   | §3.5 State Changes             | consequences declared for queueing                                             |
| `src/libxrpl/tx/invariants/InvariantCheck.cpp`, `include/xrpl/tx/invariants/` | §2.9 Invariants                | new or extended invariant checks                                               |
| `src/libxrpl/tx/applySteps.cpp`                                               | §3 Transaction                 | transactor registration, privilege / delegation wiring                         |
| account-deletion blocker lists (grep `deleteAccount`, `AccountDelete`)        | §2.6 Deletion                  | whether the new entry blocks account deletion                                  |
| `adjustOwnerCount` call sites                                                 | §2.5 Reserves                  | whether the entry consumes an owner reserve                                    |

## API surface

| rippled artifact                                                         | Spec section                   | What to extract                                |
| ------------------------------------------------------------------------ | ------------------------------ | ---------------------------------------------- |
| `src/xrpld/rpc/handlers/<Name>.cpp`                                      | §5 RPC                         | request fields, response fields, error returns |
| `include/xrpl/protocol/ApiVersion.h`, `API-CHANGELOG.md`                 | §5, §5 Backwards Compatibility | API version gating of any new field            |
| transaction metadata emission (grep the new `sf` names in metadata code) | §3.6 Metadata Fields           | new metadata fields and when they appear       |

## Tests

| rippled artifact                  | Spec section | What to extract                                                                              |
| --------------------------------- | ------------ | -------------------------------------------------------------------------------------------- |
| `src/test/app/<Feature>_test.cpp` | §6 Test Plan | scenarios covered; useful for confirming failure conditions you inferred from the transactor |
| `src/test/rpc/<Name>_test.cpp`    | §5.3, §6     | RPC error cases                                                                              |

## Changes that are usually spec-invisible

Build files, `CMakeLists.txt`, conan deps, logging, `#include` churn, formatting, unit-test refactors that add no new scenario, and internal helper renames that do not change a wire-visible name. Still list them in the "did not map" report rather than dropping them silently.
