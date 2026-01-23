<pre>
  xls: 11
  title: Retiring Amendments
  authors: Wietse Wind (@WietseWind),Scott Schurr <scott@ripple.com>, Rome Reginelli <rome@ripple.com>
  description: This standard proposes an orderly process for retiring legacy XRP Ledger protocol behavior.
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/19
  created: 2020-05-07
  status: Final
  category: Ecosystem
</pre>

# Retiring Amendments

This standard proposes an orderly process for retiring legacy XRP Ledger protocol behavior.

## Background

The XRP Ledger protocol has an [Amendments](https://xrpl.org/amendments.html) system for applying changes to transaction processing logic in an orderly fashion, with the approval of network validators. After an amendment has been enabled, it cannot be disabled. However, XRP Ledger servers still have the implementation for the pre-amendment behavior.

These "legacy code paths" apply when reconstructing older ledger versions from before the amendment became enabled. They may also apply on parallel networks (testnets and similar) that have not enabled the same set of amendments. However, the legacy code will never be used in the processing of new ledgers.

### Replaying Ledgers

One of the benefits of a blockchain system is that anyone can reconstruct the outcome of transactions to verify that everyone has followed the rules of the system and no one gets special treatment. However, any changes to the protocol pose a challenge for reconstructing historical behavior. This includes changes to introduce new functionality or fix transaction processing bugs. We call the process of reconstructing the outcome of a historical set of transactions on a historical ledger version to verify the outcome _replaying a ledger_.

To accurately replay a ledger from a given point in time, a server must have the implementation for all of the transaction processing logic that was in effect at that time. Otherwise, the server may not construct the same resulting ledger from the same parent ledger and set of transactions as the consensus network did at the original time, depending on whether the transactions use the specific legacy transaction processing behavior that changed.

### Time-Based Switches

Prior to the implementation of the Amendments system, the XRP Ledger's developers used time-based switches to coordinate the activation of new transaction-processing logic. These switches enabled new behavior based on the close time of a given ledger. Time-based switches did not involve validator voting or an approval period, and there is no mechanism to enable or disable them individually for software testing. There were at least 7 time-based switches, which activated from December 2015 through March 2017.

Ripple [removed all time-based switches](https://github.com/ripple/rippled/pull/3212/commits) version 1.5.0 of `rippled`, the reference implementation of the XRP Ledger protocol. Thus, `rippled` v1.5.0 can no longer accurately replay ledgers from 2017 or earlier. However, given that `rippled`'s source code is freely available, one can still compile an earlier version of the software to be able to replay ledgers from farther back in time.

## Rationale

The number of amendments in existence keeps growing. At the time of this writing, the complete list contains [27 enabled amendments](https://xrpl.org/known-amendments.html). For each of those amendments, the server has code for executing transactions _with_ and _without_ the amendment. (Exception: the FeeEscalation amendment did not affect transaction processing directly, only which transactions would be proposed for consensus, so it has no impact on ledger replay. It was safely [removed from the code base](https://github.com/ripple/rippled/commit/58f786cbb48a234e5bdaba10b0548357110b3b2e) in October of 2018.)

We could let the list of enabled amendments continue to grow without bound, but there are downsides.

- The list of enabled amendments is stored in the ledger as the [Amendments object](https://xrpl.org/amendments-object.html). This is data that must be replicated to every server in the XRP Ledger network and carried through from ledger to ledger.

- There is complexity every place that the code supports two alternative behaviors. When an amendment is enabled, the code needs to support both the pre- and post-amendment behavior. By removing legacy code for amendments that have been enabled for a long time we can reduce the complexity inside the code.

- There is mental overhead in keeping track of a large number of amendments, most of which are years old. It would be nice to only need to think about the more recent amendments.

- All servers in the network must also track which amendments they know about and have implementations for, so they can participate in Amendment voting and which amendments they have implementations for. These are additional data structures that the servers must keep in memory most or all of the time.

- The results of API methods describing available amendments are also growing in size over time.

None of these are killer concerns. The data structures are measured in kilobytes, not megabytes. However, for the long-term stability of the XRP Ledger it would be nice to have a plan to completely "retire" some enabled amendments, to prevent the list from growing indefinitely. In this proposal, a retired amendment becomes part of the core protocol and does not need to be tracked separately.

## Support Timeline

It can be useful to keep amendment code around for unit tests and for replaying ledgers. Ripple proposes to support all enabled amendments in the XRP Ledger reference implementation (`rippled`) for at least **2 years** after those amendments became enabled. After an amendment has been enabled for 2 years, Ripple plans to "unconditionalize" the amendment so that the XRP Ledger reference implementation no longer has maintained code for the pre-amendment behavior.

The XRP Ledger is an open network, and there is no problem if different servers support different sets of non-enabled Amendments. At any given time, each server in the network only needs to know about and support the protocol rules that are currently in use, so it is possible to maintain an XRP Ledger compatible server that supports enabled amendments for a longer or shorter period of time, and still participate in the XRP Ledger mainnet.

This document proposes a mechanism for "fully retiring" amendments such that they are removed from the list of amendments in the server and on the ledger.

## Proposed Retirement Process

The process of fully "retiring" an amendment makes an amendment a permanent part of the protocol so that neither people nor computers need to know about the amendment to follow the XRP Ledger protocol. Retiring an amendment _does not_ revert to the "pre-amendment" behavior. The process involves the following high-level steps:

1. Set a cutoff date, to retire all (not-yet-retired) amendments that were enabled before that date.

   We call the set of amendments that are to be retired in this way the "retiring amendments."

2. "Unconditionalize" the amendments in the XRP Ledger server code.

   After doing this, the server follows the amended transaction logic for all transactions regardless of the amendments' status as of any given ledger. As a result, the server is no longer guaranteed to produce historically-accurate results when trying to replay ledgers older than the cutoff date. The `rippled` server implementation issues a warning message to the log when trying to replay a ledger outside of its supported range.

3. Use a "roll-up" amendment to remove the amendments from the "enabled amendments" data structures.

   When this amendment becomes enabled through the usual process involving a consensus of validators, the XRP Ledger network removes the retiring amendments from the data structures of enabled amendments in the ledger. The roll-up amendment has no other effect.

   Each server must know which amendments are retiring and MUST NOT propose those amendments again for approval in the consensus process after they have been retired. At this time or later, the server can remove the list of retiring amendments from its internal data structures and API methods. A server should do this only _after_ the amendments have been removed from the ledger, so that the server doesn't become [amendment blocked](https://xrpl.org/amendments.html#amendment-blocked).

After this process has completed, the retiring amendments are no longer listed as available in the latest version of the XRP Ledger reference implementation, nor in the on-ledger data structures. The XRP Ledger protocol can continue to carry on, including all the changes that were originally introduced by those amendments, without needing to keep a list of all of them.

## Current Plans

Ripple expects to unconditionalize amendments approximately once per year, so that there is always a two-year rolling window of amendments supported in the `rippled` software. For historical purposes, Ripple expects to help maintain documentation of _all_ known amendments indefinitely, including those that have been retired or rejected, on xrpl.org.

At this time, Ripple does not see a need to fully retire amendments. We propose the mechanism described in this document in case the need arises in the future. We do not expect to introduce a "roll-up" amendment at this time.

Ripple proposes January 1, 2018 as the cutoff date for the first batch of unconditionalized amendments. Ripple plans to unconditionalize these amendments in version 1.6.0 of `rippled`, which is currently scheduled to release sometime around June or July of 2020.

The complete list of amendments to be unconditionalized in v1.6.0 is as follows:

| Amendment Name    | Date Enabled |
| :---------------- | :----------- |
| MultiSign         | 2016-06-27   |
| TrustSetAuth      | 2016-07-19   |
| Flow              | 2016-10-21   |
| CryptoConditions  | 2017-01-03   |
| TickSize          | 2017-02-21   |
| PayChan           | 2017-03-31   |
| fix1368           | 2017-03-31   |
| Escrow            | 2017-03-31   |
| fix1373           | 2017-07-07   |
| EnforceInvariants | 2017-07-07   |
| SortedDirectories | 2017-11-14   |
| fix1528           | 2017-11-14   |
| fix1523           | 2017-11-14   |
| fix1512           | 2017-11-14   |
| fix1201           | 2017-11-14   |

> **Note:** As mentioned above, the **FeeEscalation** amendment (enabled 2016-05-19), which did not directly affect transaction processing and ledger replay, has been unconditionalized since v1.2.0.
