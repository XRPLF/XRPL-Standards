<pre>
  xls: 65.3
  title: LendingProtocolV1_2 Vault Changes
  description: Index of Vault changes introduced by the LendingProtocolV1_2 amendment
  author: Vytautas Vito Tumas <vtumas@ripple.com>
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/192
  status: Draft
  category: Amendment
  created: 2026-11-25
  updated: 2026-11-25
</pre>

# 65.3 LendingProtocolV1_2 Vault Changes

## 1. Abstract

This index groups the Vault changes introduced by the `LendingProtocolV1_2` amendment. The amendment's changes to the Lending Protocol are specified under [XLS-66.3](../../XLS-0066-lending-protocol/66.3-lending-protocol-v1_2/README.md).

## 2. Specifications

These specifications are introduced by the `LendingProtocolV1_2` amendment:

| Spec                                                                          | Description                                                                                                                                          |
| ----------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| [65.3.1 Fixed Precision Vault](./65.3.1-fixed-precision.md)                   | Fixes one precision grid per new Vault, adds `AssetsDeployed` and `YieldUnrealized`, derives `AssetsTotal`, and bounds optional inflows by capacity. |
| [65.3.2 Vault Transactions in Batch](./65.3.2-vault-transactions-in-batch.md) | Allows the Vault transactions as `Batch` inner transactions.                                                                                         |

## 3. Rationale

The amendment changes both the Vault and the Lending Protocol. Each parent records its own deltas, and this index records the Vault side.

## 4. Security Considerations

This index introduces no additional protocol behavior. The security considerations for each change are documented in its linked specification.
