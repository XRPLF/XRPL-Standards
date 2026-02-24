<pre>
  xls: 98
  title: Institutional DeFi Insurance Protocol for XLS-0065 Vaults
  description: An ecosystem-layer insurance protocol enabling vault depositors to purchase coverage against borrower defaults in XLS-0066 lending vaults.
  author: Will Flores <wflores@wardprotocol.org>
  category: Ecosystem
  status: Draft
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/474
  requires: XLS-0020, XLS-0030, XLS-0065, XLS-0066, XLS-0070, XLS-0080
  created: 2026-02-23
  updated: 2026-02-23
</pre>

# Institutional DeFi Insurance Protocol for XLS-0065 Vaults

## 1. Abstract

Ward Protocol is an ecosystem-layer insurance protocol for the XRP Ledger that enables vault depositors to purchase coverage against borrower defaults in XLS-0066 lending vaults. The protocol uses existing XRPL primitives: XLS-0020 NFTs for policy certificates, XLS-0030 AMM pools for capital aggregation, and native Escrow for claim settlement, without requiring any protocol amendments. The reference implementation is live on XRPL testnet at https://wardprotocol.org.

## 2. Motivation

XLS-0066 introduces fixed-term, fixed-rate lending using pooled liquidity from XLS-0065 single-asset vaults. While XLS-0066 includes First-Loss Capital protection, vault depositors face uninsured tail risk when defaults exceed that protection:

    DefaultAmount  = Principal + Interest
    DefaultCovered = min(FirstLossCapital x LiquidationRate, DefaultAmount)
    VaultLoss      = DefaultAmount - DefaultCovered

Example: A $55,000 default with $1,000 First-Loss coverage leaves depositors absorbing $54,000. This prevents institutional participation because regulated entities require risk transfer before deploying capital at scale.

## 3. Specification

### 3.1 Overview

Ward Protocol operates as an off-chain service with on-ledger settlement. All financial obligations are backed by on-ledger AMM pool reserves. Policy ownership is represented by XLS-0020 NFTs. Claims settle via native XRPL Escrow.

### 3.2 Policy Issuance

A depositor purchases a policy by sending a premium payment to the Ward Protocol operator account. The operator mints an XLS-0020 NFT as the policy certificate with URI metadata:

    {
      "protocol":        "ward-v1",
      "vault_id":        "<XLS-0065 VaultID>",
      "coverage_amount": "<drops>",
      "coverage_ratio":  "<percent>",
      "coverage_start":  "<ISO-8601>",
      "coverage_end":    "<ISO-8601>",
      "pool_id":         "<AMM AccountID>"
    }

### 3.3 Premium Calculation

    epoch_premium   = coverage_amount x base_rate x term_factor x risk_multiplier
    total_premium   = epoch_premium x num_epochs
    base_rate:        1-5% annually (per vault risk tier)
    term_factor:      term_days / 365
    risk_multiplier:  0.5x-2.0x based on vault utilization, First-Loss ratio,
                      LossUnrealized impairment ratio, historical default rate

### 3.4 Claim Validation (9-Step Process)

1. Verify loan has lsfLoanDefault flag set on-ledger
2. Calculate vault loss using XLS-0066 AssetsTotal delta
3. Retrieve policy record linked to submitted NFT TokenID
4. Verify policy status is active
5. Verify default occurred within coverage window
6. Verify defaulted vault matches policy vault_id
7. Calculate payout: min(VaultLoss x CoverageRatio, FaceValue)
8. Verify pool capital adequacy: ReserveBalance >= payout
9. Approve or reject; log result on-chain via Memo field

### 3.5 Claim Settlement

Approved claims settle via native XRPL Escrow with a 48-hour dispute window. Operator creates EscrowCreate with FinishAfter = 48 hours. After window closes, EscrowFinish releases funds.

### 3.6 Capital Pool Solvency Constraint

    TotalActiveCoverage <= ReserveBalance x MaxCoverageRatio / 100

MaxCoverageRatio defaults to 200 (200% minimum reserve). Enforced at policy issuance and pool withdrawal.

### 3.7 XLS-0070 Credential Integration

When a pool requires credentials, the operator validates the depositor holds a valid unexpired XLS-0070 credential before issuing a policy. The credential hash is recorded in the policy NFT URI metadata.

### 3.8 XLS-0080 Permissioned Domain Integration

When a pool sets domain restrictions, the operator validates the depositor is a member of the pool's XLS-0080 Permissioned Domain before issuing a policy.

## 4. Rationale

An ecosystem implementation allows rapid deployment and market validation before requesting protocol changes. XLS-0020 NFTs provide policy transferability and on-ledger metadata. XLS-0030 AMM pools provide transparent reserve verification. Native Escrow provides dispute resolution without smart contracts. If adoption warrants it, a future amendment (XLS-104) could add native InsurancePolicy ledger objects and PolicyClaim transaction types.

## 5. Backwards Compatibility

This proposal introduces no changes to existing ledger objects or transaction types. No backwards incompatibilities exist.

## 6. Test Plan

The reference implementation includes 60 automated tests with 75% code coverage covering policy issuance, premium calculation, 9-step claim validation, escrow flows, XLS-0070/0080 verification, and pool solvency enforcement.

Test suite: https://github.com/wflores9/ward-protocol/tree/main/tests

## 7. Reference Implementation

- Website: https://wardprotocol.org
- API: https://api.wardprotocol.org
- Docs: https://api.wardprotocol.org/docs
- GitHub: https://github.com/wflores9/ward-protocol
- XLS-0080 Domain ID: 0a0fb36bcd46e16b4391d5c0df0d1fbb1841b602b11d13c8d06c6ed5463dc17a

## 8. Security Considerations

**Oracle Risk:** Default detection uses only on-ledger state. No external oracles are used. Multiple monitoring nodes with 3-of-5 consensus prevent single points of failure.

**Capital Adequacy:** 200% minimum reserve enforced at policy issuance. Pool withdrawals violating solvency are rejected.

**Claim Fraud:** All claim inputs are verifiable on-ledger. The 48-hour escrow window provides a dispute period.

**Key Management:** Operator account uses multi-signature (3-of-5) with cold storage for reserve keys.

**No Smart Contracts:** All transactions use native XRPL transaction types only.
