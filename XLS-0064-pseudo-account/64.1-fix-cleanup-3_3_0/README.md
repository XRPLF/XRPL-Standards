<pre>
  xls: 64.1
  title: Pseudo-Account Freeze Checks
  description: Introduces common freeze and lock checks for assets transferred into or out of pseudo-accounts
  implementation: https://github.com/XRPLF/rippled/pull/7382
  author: Vytautas Vito Tumas <vtumas@ripple.com>
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/191
  status: Draft
  category: Amendment
  created: 2026-09-04
  updated: 2026-09-08
</pre>

# Pseudo-Account Freeze Checks

## 1. Abstract

Under the `fixCleanup3_3_0` amendment, every transaction that moves an asset into or out of a pseudo-account applies the same freeze and lock checks, instead of the transaction-specific checks each protocol defines for itself. A deposit is rejected when the asset is globally frozen, when the depositor is locally frozen for it and is not its issuer, or when the pseudo-account is locally frozen for it. A withdrawal is rejected when the asset is globally frozen, when the pseudo-account is locally frozen for it, when the submitter is locally frozen for it and is not the destination, or when the destination is deep frozen for it; a withdrawal to the issuer of the asset is always allowed.

Stating the checks this way names each of the three accounts involved in a transfer — the submitter, the pseudo-account, and the destination — exactly once, so that a freeze on the pseudo-account blocks the transfer in both directions while a regular freeze does not stop an account from recovering its own funds.

## 2. Motivation

A pseudo-account holds assets on behalf of an object rather than a person, so it sits between the two parties of a transfer: a deposit is a transfer from the submitter to the pseudo-account, and a withdrawal is a transfer from the pseudo-account to a destination. A freeze check written for a single transfer does not say which of the three accounts it applies to.

The consequences of getting that wrong run in both directions. Omitting the pseudo-account from the checks lets assets move into or out of a frozen holding. Applying a local freeze on the submitter to a self-withdrawal blocks a depositor from recovering their own funds, which a regular freeze is not meant to do. The issuer exemption also needs to be explicit because an issuer can always receive its own asset back.

## 3. Specification

Throughout this section, an asset is _globally frozen_ when its issuance is frozen or locked, and an account is _locally frozen_ for an asset when it is individually frozen for that asset. A local freeze is a regular freeze; deep freeze is called out explicitly where it applies. For a Multi-Purpose Token, `lsfMPTLocked` on the `MPTokenIssuance` is a global freeze/lock of the issuance. `lsfMPTLocked` on the holder's `MPToken` satisfies both a local-freeze check and a deep-freeze check for that holder, so the “locally frozen” rows in the tables below include a locked MPT holder and return `tecLOCKED`.

The checks operate on the asset transferred into or out of the pseudo-account. For `VaultDeposit` and `VaultWithdraw`, that asset is the Vault's underlying asset. Those transactions still apply their own Vault Share freeze and lock checks from XLS-65.

When the amendment is enabled, these rules take precedence over conflicting freeze or lock rules in a transaction specification that moves an asset into or out of a pseudo-account, including XLS-30, XLS-65, and XLS-66. Transaction-specific checks continue to apply and can reject a transaction before or after these checks pass; an “allowed” result in this section therefore means that these checks pass, not that the complete transaction must succeed. When the amendment is not enabled, the pre-amendment, transaction-specific checks recorded in the parent specification continue to apply.

### 3.1 Deposit Failure Conditions

A deposit into a pseudo-account must be rejected if any of the following holds, evaluated in order:

| Condition                                                                               | Code                      |
| :-------------------------------------------------------------------------------------- | :------------------------ |
| The asset is globally frozen                                                            | `tecFROZEN` / `tecLOCKED` |
| The depositor is locally frozen for the asset, unless the depositor is the asset issuer | `tecFROZEN` / `tecLOCKED` |
| The pseudo-account is locally frozen for the asset                                      | `tecFROZEN` / `tecLOCKED` |

### 3.2 Withdrawal Failure Conditions

If the destination is the issuer of the asset, the withdrawal is allowed and none of the conditions below are evaluated: the issuer can always receive its own token. This applies to MPTs in the same way as to IOUs, so a withdrawal to the issuer bypasses the lock checks as well.

Otherwise, a withdrawal must be rejected if any of the following holds, evaluated in order:

| Condition                                                                                  | Code                      |
| :----------------------------------------------------------------------------------------- | :------------------------ |
| The asset is globally frozen                                                               | `tecFROZEN` / `tecLOCKED` |
| The pseudo-account, as the source, is locally frozen for the asset                         | `tecFROZEN` / `tecLOCKED` |
| The submitter is locally frozen for the asset **and** the submitter is not the destination | `tecFROZEN` / `tecLOCKED` |
| The destination is deep frozen for the asset                                               | `tecFROZEN` / `tecLOCKED` |

The submitter check is skipped when the submitter and the destination are the same account, that is on a self-withdrawal, because a regular freeze must not stop an account from recovering its own funds from a pool. For an MPT this exemption has no practical effect: a locked holder is always blocked, because locked and deep frozen are the same state.

The destination is checked for a deep freeze rather than a regular freeze, because a regular freeze on the destination does not prevent it from receiving.

## 4. Rationale

The checks are stated as an ordered list of conditions rather than as a single predicate so that each account involved is named exactly once, and so that the code returned for each case is unambiguous.

Naming the two cases where a check is skipped — the issuer as destination, and the submitter as their own destination — was preferred to expressing them as additional freeze conditions. Both are exemptions from an otherwise general rule, and writing them as such keeps the general rule short.

## 5. Backwards Compatibility

When the amendment is not enabled, the transaction-specific freeze and lock checks in the parent specification continue to apply. In particular, a regularly frozen Loan Broker _pseudo-account_ still accepts cover deposits. After activation, the common deposit rule rejects that transfer because the pseudo-account is locally frozen. Implementations that replay pre-activation ledgers, or that run on a network without the amendment, must use the parent checks.

## 6. Test Plan

The reference implementation tests IOU and MPT deposits and withdrawals for AMMs, Vaults, and Loan Brokers with the amendment both enabled and disabled. The cases cover global freeze, regular and deep local freeze, MPT locks, pseudo-account freeze, the issuer-destination exemption, and self-withdrawal.

## 7. Reference Implementation

[XRPLF/rippled#7382](https://github.com/XRPLF/rippled/pull/7382)

## 8. Security Considerations

The pseudo-account must be checked on both paths. Omitting it lets a deposit add to, or a withdrawal draw from, a holding that an issuer has frozen, which defeats the freeze on assets that a protocol holds on behalf of its participants.

The self-withdrawal exemption is deliberately limited to a regular freeze. A deep freeze, and the equivalent lock on an MPT, continue to block a self-withdrawal; an implementation that widened the exemption to cover deep freeze would let a deep-frozen holder exit through a pool.
