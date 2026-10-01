<pre>
  xls: 65.4
  title: Vault Donation
  description: Adds the tfVaultDonate flag to VaultDeposit so the Vault owner can add assets to a Vault without minting shares
  author: Vytautas Vito Tumas <vtumas@ripple.com>
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/192
  status: Draft
  category: Amendment
  requires: [XLS-65.1.4](../65.1/65.1.4-closed-ended-vault.md), [XLS-65.2](../65.2/README.md)
  implementation: https://github.com/XRPLF/rippled/pull/6383
  created: 2026-10-01
  updated: 2026-10-01
</pre>

# Vault Donation

## 1. Abstract

Under `LendingProtocolV1_2`, `VaultDeposit` accepts a new flag, `tfVaultDonate`. A donation moves assets from the Vault Owner into the Vault and mints no shares. `Vault.AssetsTotal` and `Vault.AssetsAvailable` rise, so every outstanding share is worth more. Only the Owner may donate, and only to a Vault that has outstanding shares. A donation is allowed in every phase of a closed-ended Vault.

## 2. Motivation

A Vault can lend out its whole balance and then have the Loan default. The Vault is left with shares and no assets. An ordinary deposit into that Vault mints shares at par, so the new depositor is diluted by the existing shares, which are worth nothing.

The Owner needs a way to restore backing for the existing shareholders. A deposit that mints no shares does this: it raises the value of every share and gives the Owner no claim on the Vault in return. Today the only way to add assets to a Vault is an ordinary `VaultDeposit`, which always mints shares.

## 3. Specification

This patch changes the parent [XLS-65](../README.md) sections named below. All other parent behavior is unchanged. Everything in this patch is gated by `LendingProtocolV1_2`, defined in [XLS-65.3](../65.3/README.md) §3.21.

A `VaultDeposit` with `tfVaultDonate` set is a **donation**. `tfVaultDonate` has no effect unless `LendingProtocolV1_2` is enabled.

### 3.1 Transaction: `VaultDeposit`

#### 3.1.1 Flags

Add to parent [§3.5](../README.md#35-transaction-vaultdeposit):

| Flag Name       | Flag Value   | Description                                                                        |
| --------------- | ------------ | ---------------------------------------------------------------------------------- |
| `tfVaultDonate` | `0x00010000` | Add `Amount` to the Vault without minting shares. Only the Vault Owner may set it. |

The flag value is per transaction type. It equals the value of `tfVaultPrivate` on `VaultCreate`, and the two do not collide. Before `LendingProtocolV1_2` is enabled, the `VaultDeposit` flag mask includes `tfVaultDonate` as an invalid bit. After it is enabled, the bit is valid.

#### 3.1.2 Failure Conditions

##### 3.1.2.1 Data Verification

Append to parent [§3.5.2.1](../README.md#3521-data-verification):

3. - `LendingProtocolV1_2` disabled: `tfVaultDonate` is set. (`temINVALID_FLAG`)
   - `LendingProtocolV1_2` enabled: The check does not apply.

##### 3.1.2.2 Protocol-Level Failures

Append to parent [§3.5.2.2](../README.md#3522-protocol-level-failures). These apply only when `tfVaultDonate` is set:

16. The transaction `Account` is not `Vault.Owner`. (`tecNO_PERMISSION`)
17. `MPTokenIssuance(Vault.ShareMPTID).OutstandingAmount` is zero, so the Vault has no shares to receive the donation. (`tecNO_PERMISSION`)

Items 16 and 17 are numbered for reference only. They are evaluated in `preclaim`, in that order, after the Vault and its share issuance are read and before the share-lock check (parent item 5).

Change these existing conditions for a donation:

- The `LendingProtocolV1_1` phase check, which fails a deposit to a closed-ended Vault outside `Subscription` or `NoPhase` ([XLS-65.1.4](../65.1/65.1.4-closed-ended-vault.md) §3.4.1), is skipped. A donation succeeds in the `Subscription`, `Investment` and `Redemption` phases.
- No shares are computed, so the "computed number of shares is zero" check (item 11) does not apply.

All other conditions apply to a donation unchanged, including the asset, freeze, lock, authorization, balance and `Vault.AssetsMaximum` checks. A donation that would take `Vault.AssetsTotal` above a non-zero `Vault.AssetsMaximum` fails with `tecLIMIT_EXCEEDED`. On a private Vault the Owner is always authorized, so the permissioned-domain check never fails a donation.

#### 3.1.3 State Changes

Replace the share computation and transfer of parent [§3.5.3](../README.md#353-state-changes) for a donation:

1. With `fixCleanup3_2_0` enabled, `Amount` is first rounded down to the Vault's `AssetsTotal` scale, as for an ordinary deposit. $\Delta_{asset}$ starts as that amount. It is not derived from a share count, so there is no share-to-asset round trip.
2. With `fixCleanup3_4_0` enabled, $\Delta_{asset}$ is rounded down to the posterior `Vault.AssetsTotal` scale, and the transaction fails with `tecPRECISION_LOSS` if the depositor's balance would round to zero, exactly as for an ordinary deposit ([XLS-65.2](../65.2/README.md) §3.1.2.3).
3. $\Delta_{asset}$ is debited from the Owner and credited to the Vault. `Vault.AssetsTotal` and `Vault.AssetsAvailable` increase by $\Delta_{asset}$ (parent §3.5.3 items 4 to 7).
4. No shares are minted or transferred, so parent §3.5.3 items 1 to 3 do not apply. `MPTokenIssuance(Vault.ShareMPTID).OutstandingAmount` is unchanged.

Because the assets rise and the share count does not, the asset value of each share increases by $\Delta_{asset}$ divided by the outstanding shares.

#### 3.1.4 Invariants

Change the `VaultDeposit` invariants of parent [§3.5.4](../README.md#354-invariants) for a donation:

- Items 3 and 4 (depositor shares increase, `OutstandingAmount` increases by the same amount) are replaced by the checks below.
- Item 7 (the phase restriction) does not apply. A donation may be applied in any phase.
- A donation is the only `VaultDeposit` that may succeed without changing any share balance.

Replacement checks. A failed check makes the invariant fail the transaction (`tecINVARIANT_FAILED`, or `tefINVARIANT_FAILED` on retry):

1. `Vault.Owner` equals the transaction `Account`.
2. `MPTokenIssuance(Vault.ShareMPTID).OutstandingAmount` is non-zero. The issuance is not modified by a donation, so an implementation must read it from the ledger view rather than from the modified entries.
3. The shares held by the transaction `Account` do not change.
4. The shares held by the Vault pseudo-account do not change.

Items 1, 2 and 5 of parent §3.5.4 apply to a donation unchanged. Item 6 also applies, so `Vault.AssetsMaximum` is enforced both by the transactor and by the invariant.

### 3.2 RPC: `server_definitions`

`server_definitions` lists `tfVaultDonate` among the `VaultDeposit` transaction flags. The reference implementation adds the flag to the transaction flag macro in `TxFlags.h`, and `server_definitions` is generated from that macro. No other change to the RPC is made.

## 4. Rationale

**Why a flag on `VaultDeposit`.** A donation is a deposit with a different share rule. The asset-side checks, the rounding guards and the authorization checks are the same, so a flag reuses them and keeps the Vault's asset movement in one transactor. A separate transaction type would duplicate that logic and the invariant wiring for one difference.

**Why not a plain `Payment` to the pseudo-account.** The pseudo-account cannot receive payments, and a transfer outside the Vault's own transactors would not update `AssetsTotal` and `AssetsAvailable`, which the share exchange rate depends on.

**Why Owner only.** A donation gives the donor nothing back. Letting anyone donate would let a third party change a Vault's exchange rate at will. Restricting it to the Owner keeps the operation a recapitalisation tool.

**Why outstanding shares are required.** With no shares outstanding, a donation would credit assets that no share claims. The next depositor would mint at par and receive a claim on the whole donation.

**Why donations ignore the phase.** The phase gates of [XLS-65.1.4](../65.1/65.1.4-closed-ended-vault.md) protect shareholders from changes in share supply. A donation does not change the share supply, and recapitalisation is most needed after a default, which happens in the Investment and Redemption phases.

**Why `AssetsMaximum` still applies.** The cap bounds `Vault.AssetsTotal`, not the number of shares, so a donation counts against it.

## 5. Backwards Compatibility

The amendment adds a flag that was previously invalid. Before activation, a `VaultDeposit` with `tfVaultDonate` fails with `temINVALID_FLAG`. `VaultDeposit` transactions without the flag behave as before. `tfVaultPrivate` on `VaultCreate` shares the numeric value `0x00010000` and is unaffected.

## 6. Test Plan

The reference implementation tests a donation with the amendment disabled (`temINVALID_FLAG`); to an empty Vault and by a non-owner (`tecNO_PERMISSION`); above `AssetsMaximum` (`tecLIMIT_EXCEEDED`); and for XRP, IOU and MPT Vaults, including an IOU debit that rounds to zero (`tecPRECISION_LOSS`) and a locked MPT (`tecLOCKED`). It checks that a donation leaves the share supply unchanged and raises `AssetsTotal` and `AssetsAvailable`, including at a non-1:1 share ratio and over repeated donations. It runs a donation in the `Investment` and `Redemption` phases of a closed-ended Vault, where an ordinary deposit fails with `tecEXPIRED`. It checks that `VaultCreate` with `tfVaultPrivate` is unaffected under the amendment, and that the invariant rejects a donation that changes share balances, or comes from a non-owner. A manual rounding suite covers a donation to an IOU Vault whose `LossUnrealized` equals `AssetsTotal - AssetsAvailable`.

## 7. Reference Implementation

[XRPLF/rippled#6383](https://github.com/XRPLF/rippled/pull/6383)

## 8. Security Considerations

A donation is irreversible. The Owner cannot reclaim donated assets except by redeeming shares like any other holder, and a donation benefits every shareholder pro rata, including any shares the Owner holds.

A donation raises the exchange rate of the shares without minting any. A non-owner cannot use this, because the Owner check fails with `tecNO_PERMISSION`. An Owner can move the rate, but only in the direction of the shareholders, and at its own cost.

The Owner check and the outstanding-shares check are enforced twice, in `preclaim` and in the `ValidVault` invariant, so an implementation error in the transactor cannot create a donation that credits assets to a Vault with no shareholders, or one made by someone other than the Owner.

On an `IOU` Vault, `LossUnrealized`, `AssetsTotal` and `AssetsAvailable` are quantised independently. When `LossUnrealized == AssetsTotal - AssetsAvailable`, a donation can round `AssetsTotal` and `AssetsAvailable` in opposite directions and shrink that difference by one unit, which would trip the loss invariant. With `fixCleanup3_4_0` enabled, the one-unit tolerance of [XLS-65.2](../65.2/README.md) §3.1.2.1 absorbs this. Without it, the invariant has no tolerance for that residue.
