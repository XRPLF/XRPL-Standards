<pre>
  xls: 64.1
  title: Pseudo-Account Freeze Checks
  description: Defines the freeze and lock conditions a deposit into, or withdrawal from, a pseudo-account must evaluate
  author: Vito Tumas (@Tapanito)
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/191
  status: Draft
  category: Amendment
  requires: [XLS-64](../README.md)
  created: 2026-09-04
  updated: 2026-09-04
</pre>

# Pseudo-Account Freeze Checks

## 1. Abstract

This patch of [XLS-64](../README.md) records the changes the `fixCleanup3_4_0` amendment makes to the freeze handling of a pseudo-account. It states the conditions a deposit into a pseudo-account and a withdrawal out of one must evaluate, distinguishes a global freeze from a local freeze, and defines where the exemption for the issuer of an asset applies.

The consolidated specification is the top-level [README.md](../README.md).

## 2. Motivation

A pseudo-account holds assets on behalf of an object rather than a person, so it sits between the two parties of a transfer: a deposit is a transfer from the submitter to the pseudo-account, and a withdrawal is a transfer from the pseudo-account to a destination. A freeze check written for a single transfer does not say which of the three accounts it applies to.

The consequences of getting that wrong run in both directions. Omitting the pseudo-account from the checks lets assets move into or out of a frozen holding. Applying a local freeze on the submitter to a self-withdrawal blocks a depositor from recovering their own funds, which a regular freeze is not meant to do. Two further cases need stating: a Vault share carries the freeze state of its underlying asset, and the issuer of an asset can always receive it back.

## 3. Specification

Throughout this section, an asset is _globally frozen_ when its issuance is frozen or locked, and an account is _locally frozen_ for an asset when it is individually frozen for that asset. A local freeze is a regular freeze; deep freeze is called out explicitly where it applies. For a Multi-Purpose Token, the `lsfMPTLocked` flag on either the `MPTokenIssuance` or the `MPToken` of the holder is equivalent to deep-frozen semantics.

For an MPT that is a Vault Share, _locally frozen_ also covers the Vault Share condition below: the underlying asset of the share must not be frozen or locked for the Vault pseudo-account or for the account itself. An implementation that performs the global and the local check separately, rather than through one combined freeze check, must still perform the Vault pseudo-account check for MPT shares.

### 3.1 Deposit Failure Conditions

A deposit into a pseudo-account must be rejected if any of the following holds, evaluated in order:

| Condition                                                                               | Code                      |
| :-------------------------------------------------------------------------------------- | :------------------------ |
| The asset is globally frozen                                                            | `tecFROZEN` / `tecLOCKED` |
| If the asset is a Vault Share, the underlying asset of the share is frozen or locked     | `tecLOCKED`               |
| The depositor is locally frozen for the asset, unless the depositor is the asset issuer  | `tecFROZEN` / `tecLOCKED` |
| The pseudo-account is locally frozen for the asset                                      | `tecFROZEN` / `tecLOCKED` |

### 3.2 Withdrawal Failure Conditions

If the destination is the issuer of the asset, the withdrawal is allowed and none of the conditions below are evaluated: the issuer can always receive its own token. This applies to MPTs in the same way as to IOUs, so a withdrawal to the issuer bypasses the lock checks as well.

Otherwise, a withdrawal must be rejected if any of the following holds, evaluated in order:

| Condition                                                                                  | Code                      |
| :----------------------------------------------------------------------------------------- | :------------------------ |
| The asset is globally frozen                                                               | `tecFROZEN` / `tecLOCKED` |
| If the asset is a Vault Share, the underlying asset of the share is frozen or locked        | `tecLOCKED`               |
| The pseudo-account, as the source, is locally frozen for the asset                         | `tecFROZEN` / `tecLOCKED` |
| The submitter is locally frozen for the asset **and** the submitter is not the destination  | `tecFROZEN` / `tecLOCKED` |
| The destination is deep frozen for the asset                                               | `tecFROZEN` / `tecLOCKED` |

The submitter check is skipped when the submitter and the destination are the same account, that is on a self-withdrawal, because a regular freeze must not stop an account from recovering its own funds from a pool. For an MPT this exemption has no practical effect: a locked holder is always blocked, because locked and deep frozen are the same state.

The destination is checked for a deep freeze rather than a regular freeze, because a regular freeze on the destination does not prevent it from receiving.

## 4. Rationale

The checks are stated as an ordered list of conditions rather than as a single predicate so that each account involved is named exactly once, and so that the code returned for each case is unambiguous.

Naming the two cases where a check is skipped — the issuer as destination, and the submitter as their own destination — was preferred to expressing them as additional freeze conditions. Both are exemptions from an otherwise general rule, and writing them as such keeps the general rule short.

## 5. Security Considerations

The pseudo-account must be checked on both paths. Omitting it lets a deposit add to, or a withdrawal draw from, a holding that an issuer has frozen, which defeats the freeze on assets that a protocol holds on behalf of its participants.

The self-withdrawal exemption is deliberately limited to a regular freeze. A deep freeze, and the equivalent lock on an MPT, continue to block a self-withdrawal; an implementation that widened the exemption to cover deep freeze would let a deep-frozen holder exit through a pool.
