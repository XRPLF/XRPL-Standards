<pre>
xls: 103
title: Nested Multi-Sign
description: Hierarchical multi-signature validation allowing signer lists to recursively delegate signing authority
author: Richard Holland, Niq Dudfield
status: Draft
category: Standards
created: 2026-02-13
</pre>

# Nested Multi-Sign

## Abstract

This standard specifies an extension to the XRP Ledger multi-signature mechanism that supports **hierarchical (nested) signing**. A signer on an account's signer list may satisfy its weight requirement by presenting signatures from its own signer list, rather than signing directly. This nesting may recurse up to four levels deep, enabling organizational governance structures such as `Company → Departments → Teams → Individuals`. The standard also defines cycle detection and quorum relaxation semantics to prevent permanent fund lockout when circular signer-list dependencies exist.

This standard requires a consensus amendment to implement.

## 1. Motivation

The current multi-signature system is flat: every signer on a signer list must produce a direct cryptographic signature. This limits the expressiveness of on-chain governance in several ways.

**Organizational hierarchy.** A company may wish to require sign-off from two of three departments, where each department in turn requires sign-off from a quorum of its members. Today this requires either listing every individual signer on the top-level account (losing the departmental structure entirely) or assigning a single shared key per department, which is a security risk.

**Key rotation without re-configuration.** If a department replaces a team member, it only needs to update its own signer list. The parent account's signer list remains unchanged, reducing operational overhead and the risk of configuration errors.

**Auditability.** Nested signatures are fully on-chain. Every leaf signer's key and signature is visible in the transaction blob, providing a complete audit trail of who actually authorised a transaction.

## 2. Specification

### 2.1 Scope

This standard defines the transaction structure, validation semantics, and error handling for nested multi-signatures on the XRP Ledger. It does not introduce new ledger objects or transaction types. The existing `SignerList` object and `SignerListSet` transaction are unchanged; only the transaction signing and validation pipeline is extended.

When the implementing amendment is not enabled, nested signer arrays are rejected during transaction serialization with `temMALFORMED`, preserving existing behaviour.

### 2.2 Transaction Structure

A signer entry may contain either a direct signature **or** a nested `Signers` array, but never both. A direct (leaf) signer entry contains `SigningPubKey` and `TxnSignature` as today. A nested signer entry omits both fields and instead includes an `sfSigners` array whose entries follow the same recursive structure.

```json
{
  "Account": "rCompany...",
  "TransactionType": "Payment",
  "Signers": [
    {
      "Signer": {
        "Account": "rDeptA...",
        "Signers": [
          {
            "Signer": {
              "Account": "rAlice...",
              "SigningPubKey": "ED...",
              "TxnSignature": "3045..."
            }
          },
          {
            "Signer": {
              "Account": "rBob...",
              "SigningPubKey": "ED...",
              "TxnSignature": "3045..."
            }
          }
        ]
      }
    },
    {
      "Signer": {
        "Account": "rDeptB...",
        "Signers": [
          {
            "Signer": {
              "Account": "rCharlie...",
              "SigningPubKey": "ED...",
              "TxnSignature": "3045..."
            }
          }
        ]
      }
    }
  ]
}
```

### 2.3 Validation Rules

The following rules apply.

1. **Maximum nesting depth: 4 levels.** The root account's signer list is depth 0. Signers that themselves delegate form depth 1, and so on. Any signer entry beyond depth 4 MUST be rejected.

2. **Mutual exclusion.** A signer entry MUST contain either (`SigningPubKey` + `TxnSignature`) or a nested `Signers` array, never both and never neither. Violation → `tefBAD_SIGNATURE`.

3. **Ordering.** Signer entries at every level MUST be sorted in strict ascending order by `Account` (canonical account ID comparison), consistent with the existing consensus requirement for flat multi-sign.

4. **Signer list existence.** A nested signer's `Account` MUST have a `SignerList` object on the ledger. If not → `tefNOT_MULTI_SIGNING`.

5. **Leaf signer validity.** Leaf signers are validated exactly as in flat multi-sign: the `SigningPubKey` must correspond to the leaf account's master key (or regular key), the master key must not be disabled, and the `TxnSignature` must be valid over the canonical transaction hash.

6. **Quorum accumulation.** At each level, signer weights accumulate only when the signer's own quorum (or relaxed quorum — see §2.4) is met. A nested signer whose sub-signers fail to meet quorum contributes zero weight to its parent.

7. **Maximum leaf signers: 64.** The total number of leaf (direct) signers across the entire nested structure MUST NOT exceed 64. This bounds the worst-case signature verification cost. Exceeding this limit → `temMALFORMED`.

### 2.4 Cycle Detection and Quorum Relaxation

Circular signer-list dependencies (e.g., A lists B, B lists A) can arise from independent `SignerListSet` transactions and could permanently lock funds if not handled.

**Detection.** During recursive validation, an *ancestors set* MUST be maintained. Before descending into a nested signer, the validator checks whether the signer's account already appears in the ancestors set. If it does, the signer is **cyclic** and MUST be skipped (contributes zero weight).

**Quorum relaxation.** After identifying cyclic signers at a given level, the *effective quorum* is reduced from the configured quorum to: `min(configuredQuorum, totalNonCyclicWeight)`, where `totalNonCyclicWeight` is the sum of weights of all non-cyclic signers on that list. This prevents a situation where unreachable cyclic signers make it impossible to ever meet quorum.

If `totalNonCyclicWeight` is zero (all signers are cyclic), the effective quorum is zero and validation MUST fail with `tefBAD_QUORUM`, since no valid signing path exists.

### 2.5 Fee Calculation

The base transaction fee MUST be multiplied by (1 + total leaf signers) to account for the additional signature verification cost, consistent with how flat multi-sign fees scale today. The fee calculation walks the nested structure to count all leaf signers before applying the multiplier.

## 3. Error Codes

Conforming implementations return the following error codes under the specified conditions.

| Code | Condition |
|---|---|
| `temMALFORMED` | Nesting depth exceeded; leaf signer count > 64; amendment not enabled and nested array present |
| `tefBAD_SIGNATURE` | Malformed signer entry (both or neither of signature fields and nested array); invalid leaf signature; depth limit exceeded at validation layer |
| `tefBAD_QUORUM` | Accumulated weight insufficient to meet (relaxed) quorum; all signers cyclic |
| `tefNOT_MULTI_SIGNING` | Nested signer account has no `SignerList` on the ledger |
| `tefMASTER_DISABLED` | Leaf signer's master key is disabled and no regular key is configured |

## 4. Security Considerations

**Verification cost.** The 64-leaf-signer cap and 4-level depth limit together bound the maximum computational cost of validating a single transaction. Without these limits, an attacker could construct deeply nested structures requiring excessive CPU time during consensus.

**Cycle-induced lockout.** The quorum relaxation mechanism is designed to be conservative: it only relaxes quorum to the maximum weight that can actually be achieved, never to zero (which would allow unsigned transactions). Accounts where all paths are cyclic correctly fail.

**Authorisation checks before cycle skipping.** When a cyclic signer is encountered, the validator MUST first check whether the signer is authorised on the parent's signer list. Unauthorised entries are rejected with `tefBAD_SIGNATURE` rather than silently skipped, preventing an attacker from injecting arbitrary accounts into the ancestors set.

## 5. Backward Compatibility

This standard introduces no changes to existing ledger objects or transaction types. The `SignerList` ledger object and `SignerListSet` transaction are unchanged.

When the implementing amendment is **not enabled**, the presence of nested `Signers` arrays in a transaction causes rejection with `temMALFORMED` during serialization, identical to current behaviour for malformed transactions. No existing valid transactions are affected.

Tooling and client libraries that construct or parse multi-signed transactions will need updates to support the nested `Signers` structure. Existing flat multi-signed transactions remain valid and are processed identically.

## 6. Reference Implementation

A reference implementation of this standard exists as the `featureNestedMultiSign` amendment, available on both chains:

- **Xahau:** [Xahau/xahaud#675](https://github.com/Xahau/xahaud/pull/675)
- **XRPL:** [XRPLF/rippled#6368](https://github.com/XRPLF/rippled/pull/6368)
