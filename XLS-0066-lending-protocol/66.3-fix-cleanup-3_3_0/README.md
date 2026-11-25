<pre>
  xls: 66.3
  title: Lending Protocol Cleanup 3.3.0
  description: Lending Protocol changes of the fixCleanup3_3_0 amendment to the freeze checks of first-loss capital deposits and withdrawals
  author: Vytautas Vito Tumas <vtumas@ripple.com>
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/190
  status: Final
  category: Amendment
  created: 2026-11-25
  updated: 2026-11-25
</pre>

# 66.3 Lending Protocol Cleanup 3.3.0

## 1. Abstract

Under the `fixCleanup3_3_0` amendment, `LoanBrokerCoverDeposit` and `LoanBrokerCoverWithdraw` use the same freeze rules as other deposits to and withdrawals from a _pseudo-account_. A deposit is rejected if the broker _pseudo-account_ is frozen, not only deep frozen. A withdrawal to the issuer is always allowed by the freeze checks, and a submitter that is frozen cannot withdraw to a third party.

## 2. Motivation

Before the amendment, a deposit could reach a broker _pseudo-account_ under a regular freeze, and the funds could then not be withdrawn. A frozen submitter could withdraw cover to a third party, and a withdrawal to the issuer failed if the _pseudo-account_ balance was frozen.

## 3. Specification

No fields are added or removed. In the checks below, a frozen account returns `tecFROZEN` for an IOU and `tecLOCKED` for an MPT.

### 3.1 Transaction: `LoanBrokerCoverDeposit`

#### 3.1.1 Failure Conditions

When the amendment is enabled, parent §3.5.3.2 checks 5 and 6 are replaced, in this order, by:

1. The asset is globally frozen or locked.
2. The submitter is not the issuer and is individually frozen for the asset.
3. The broker _pseudo-account_ is individually frozen for the asset.

When the amendment is not enabled, parent checks 5 and 6 apply: the submitter is frozen, or the broker _pseudo-account_ is deep frozen.

### 3.2 Transaction: `LoanBrokerCoverWithdraw`

#### 3.2.1 Failure Conditions

When the amendment is enabled, parent §3.6.3.2 checks 10 and 11 are replaced by the following. If the destination is the issuer of the asset, none of them apply. Otherwise, in this order:

1. The asset is globally frozen or locked.
2. The broker _pseudo-account_ is individually frozen for the asset.
3. The submitter is not the destination and is individually frozen for the asset.
4. The destination is deep frozen for the asset.

When the destination is the issuer, parent check 14 counts the _pseudo-account_ balance even if it is frozen.

When the amendment is not enabled, parent checks 10 and 11 apply, and parent check 14 counts a frozen balance as zero.

## 4. Rationale

A _pseudo-account_ cannot act on its own, so funds deposited under a regular freeze would be stuck. Sending to the issuer only reduces the issuer's obligations, so a freeze does not block it. A regular freeze stops an account from sending, so a frozen submitter cannot direct cover to another account, but may still withdraw to itself.

## 5. Security Considerations

The amendment rejects deposits to a broker _pseudo-account_ under a regular freeze and withdrawals to a third party by a frozen submitter. It allows a withdrawal to the issuer even when the _pseudo-account_ balance is frozen, which returns funds to the issuer and cannot move them to another holder.
