<pre>
  xls: 64.1
  title: Pseudo-Account under fixCleanup3_3_0
  description: Records the changes the fixCleanup3_3_0 amendment makes to XLS-64
  implementation: https://github.com/XRPLF/rippled/pull/7382
  author: Vito Tumas (@Tapanito)
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/191
  status: Draft
  category: Amendment
  requires: [XLS-64](../README.md)
  created: 2026-09-04
  updated: 2026-09-08
</pre>

# Pseudo-Account under `fixCleanup3_3_0`

## 1. Abstract

This patch of [XLS-64](../README.md) records the changes the `fixCleanup3_3_0` amendment makes to pseudo-accounts. The amendment is not yet live. The consolidated specification is the top-level [README.md](../README.md).

The amendment makes the following changes to XLS-64:

- **Pseudo-Account Freeze Checks** — standardizes the freeze and lock checks for assets transferred into or out of pseudo-accounts.

## 2. Motivation

**Pseudo-Account Freeze Checks.** A pseudo-account holds assets on behalf of an object rather than a person, so it sits between the two parties of a transfer: a deposit is a transfer from the submitter to the pseudo-account, and a withdrawal is a transfer from the pseudo-account to a destination. A freeze check written for a single transfer does not say which of the three accounts it applies to.

The consequences of getting that wrong run in both directions. Omitting the pseudo-account from the checks lets assets move into or out of a frozen holding. Applying a local freeze on the submitter to a self-withdrawal blocks a depositor from recovering their own funds, which a regular freeze is not meant to do. The issuer exemption also needs to be explicit because an issuer can always receive its own asset back.

## 3. Specification

### 3.1 Pseudo-Account Freeze Checks

Throughout this section, an asset is _globally frozen_ when its issuance is frozen or locked, and an account is _locally frozen_ for an asset when it is individually frozen for that asset. A local freeze is a regular freeze; deep freeze is called out explicitly where it applies. For a Multi-Purpose Token, the `lsfMPTLocked` flag on either the `MPTokenIssuance` or the `MPToken` of the holder is equivalent to deep-frozen semantics.

`checkDepositFreeze` and `checkWithdrawFreeze` operate on the asset transferred into or out of the pseudo-account. For `VaultDeposit` and `VaultWithdraw`, callers pass the Vault's underlying asset; the helpers do not perform a separate Vault Share check on their successful path.

This section specifies the common freeze and lock checks performed by those helpers. While `fixCleanup3_3_0` is enabled, these rules take precedence over conflicting freeze or lock rules in a transaction specification that uses the helpers, including XLS-30, XLS-65, and XLS-66. Transaction-specific checks outside the helpers continue to apply and can reject a transaction before or after a helper succeeds; an “allowed” result in this section therefore means that the helper returns `tesSUCCESS`, not that the complete transaction must succeed. The reference implementation gates the helper calls in [`AMMDeposit`](https://github.com/XRPLF/rippled/blob/09e6aa1aa6bf9ac84fd58c0f7cfa9860a60a1997/src/libxrpl/tx/transactors/dex/AMMDeposit.cpp#L258-L282), [`AMMWithdraw`](https://github.com/XRPLF/rippled/blob/09e6aa1aa6bf9ac84fd58c0f7cfa9860a60a1997/src/libxrpl/tx/transactors/dex/AMMWithdraw.cpp#L241-L271), [`VaultDeposit`](https://github.com/XRPLF/rippled/blob/09e6aa1aa6bf9ac84fd58c0f7cfa9860a60a1997/src/libxrpl/tx/transactors/vault/VaultDeposit.cpp#L113-L127), [`VaultWithdraw`](https://github.com/XRPLF/rippled/blob/09e6aa1aa6bf9ac84fd58c0f7cfa9860a60a1997/src/libxrpl/tx/transactors/vault/VaultWithdraw.cpp#L166-L189), [`LoanBrokerCoverDeposit`](https://github.com/XRPLF/rippled/blob/09e6aa1aa6bf9ac84fd58c0f7cfa9860a60a1997/src/libxrpl/tx/transactors/lending/LoanBrokerCoverDeposit.cpp#L83-L95), and [`LoanBrokerCoverWithdraw`](https://github.com/XRPLF/rippled/blob/09e6aa1aa6bf9ac84fd58c0f7cfa9860a60a1997/src/libxrpl/tx/transactors/lending/LoanBrokerCoverWithdraw.cpp#L129-L146).

#### 3.1.1 Deposit Failure Conditions

A deposit into a pseudo-account must be rejected if any of the following holds, evaluated in order:

| Condition                                                                               | Code                      |
| :-------------------------------------------------------------------------------------- | :------------------------ |
| The asset is globally frozen                                                            | `tecFROZEN` / `tecLOCKED` |
| The depositor is locally frozen for the asset, unless the depositor is the asset issuer | `tecFROZEN` / `tecLOCKED` |
| The pseudo-account is locally frozen for the asset                                      | `tecFROZEN` / `tecLOCKED` |

#### 3.1.2 Withdrawal Failure Conditions

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

### 3.2 Pre-Activation Behavior

Before `fixCleanup3_3_0` is enabled, there is no common pseudo-account deposit or withdrawal helper rule. Each transaction continues to use its transaction-specific legacy checks, as shown by the disabled branches linked above. In particular:

- Vault deposits check the depositor's underlying asset and the depositor's Vault Share; Vault withdrawals check the destination's underlying asset and the submitter's Vault Share.
- Loan Broker cover deposits check the depositor for a regular freeze but the broker pseudo-account only for a deep freeze. Cover withdrawals skip freeze checks when the destination is the issuer; otherwise they check the broker pseudo-account for a regular freeze and the destination for a deep freeze.
- AMM deposits and withdrawals retain their inline, per-asset freeze checks.

Those legacy transaction-specific rules, rather than sections 3.1.1 and 3.1.2, govern ledgers before activation and replay of pre-activation ledgers.

## 4. Rationale

**Pseudo-Account Freeze Checks.** The checks are stated as an ordered list of conditions rather than as a single predicate so that each account involved is named exactly once, and so that the code returned for each case is unambiguous.

Naming the two cases where a check is skipped — the issuer as destination, and the submitter as their own destination — was preferred to expressing them as additional freeze conditions. Both are exemptions from an otherwise general rule, and writing them as such keeps the general rule short.

## 6. Test Plan

The reference implementation tests IOU and MPT deposits and withdrawals for AMMs, Vaults, and Loan Brokers with `fixCleanup3_3_0` both enabled and disabled. The cases cover global freeze, regular and deep local freeze, MPT locks, pseudo-account freeze, the issuer-destination exemption, and self-withdrawal.

## 7. Reference Implementation

[XRPLF/rippled#7382](https://github.com/XRPLF/rippled/pull/7382)

## 8. Security Considerations

**Pseudo-Account Freeze Checks.** The pseudo-account must be checked on both paths. Omitting it lets a deposit add to, or a withdrawal draw from, a holding that an issuer has frozen, which defeats the freeze on assets that a protocol holds on behalf of its participants.

The self-withdrawal exemption is deliberately limited to a regular freeze. A deep freeze, and the equivalent lock on an MPT, continue to block a self-withdrawal; an implementation that widened the exemption to cover deep freeze would let a deep-frozen holder exit through a pool.
