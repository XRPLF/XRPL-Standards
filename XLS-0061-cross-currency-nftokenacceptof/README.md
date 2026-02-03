<pre>
  xls: 61
  title: CrossCurrency NFTokenAcceptOffer
  description: Allow cross-currency NFToken transactions using multiple currencies
  author: tequ (@tequdev)
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/183
  created: 2024-02-26
  status: Stagnant
  category: Amendment
</pre>

# Abstract

XRPL's NFToken functionality, currently implemented as XLS-20, only allows the use of a single currency for transactions.

This proposal allows cross-currency NFToken transactions using multiple currencies.

Creators and marketplaces will be able to sell NFTs without being tied to a currency, and users will be able to buy NFTs without being tied to a currency.

This will increase revenue opportunities for creators and marketplaces and create significant tokenomics.

# Specification

## `NFTokenAcceptOffer` Transaction

Add the following field:

| Field Name | Required? |      JSON Type       | Internal Type |
| ---------- | :-------: | :------------------: | :-----------: |
| `Amount`   |           | `object` or `string` |   `AMOUNT`    |

### `Amount` Field

When accepting an NFTokenOffer with the tfSellOffer flag set, the `Amount` field acts like the `SendMax` field, and when accepting an NFTokenOffer without tfSellOffer set, the `DeliverMin` field acts like the `Amount` field.

It doesn't have to match the `Amount` of the Offeror specified in `NFTokenSellOffer` or `NFTokenBuyOffer`.

In broker mode, the `Amount` field must not be present.

### `NFTokenBrokerFee` Field

The existing `NFTokenBrokerFee` field can be any currency amount.

### CrossCurrency Accept

The currency of `Amount` can be different from the currency of the BuyOffer / SellOffer.
The currency of `NFTokenBrokerFee` can be different from the currency of the BuyOffer / SellOffer.

Buyer must specify a sufficient amount that can be transferred to Seller, nftoken issuer(nftoken transfer fee), broker(broker fee), token issuer(token transfer fee).

NFToken transfer fees are sent in the buyer's currency.
NFToken with the tfOnlyXRP flag set will be paid in XRP.

If there was insufficient amount or liquidity, the transaction will fail.

## `NFTokenCreateOffer` Transaction

No change in fields.

Change to only check if the NFToken issuer has a trustline for the currenfy of `Amount` field when creating a BuyOffer for an NFToken with royalties.

## The `NFTokenPage` Object

No changes.

## The `NFTokenOffer` Object

No changes.

# Cases

## `Amount` Field not specified in `NFTokenAcceptOffer` Transaction

According to XLS-20 specifications. Except for NFTs with royalties, issuer's trust line [must be checked](https://github.com/XRPLF/rippled/issues/4925).

## `Amount` Field specified and equal to `Amount` in `NFTokenOffer`

DEX liquidity will not be used and existing transfer processing will be used.
If the quantity in the `Amount` cannot be sent to the seller, the transaction will fail.

## `Amount` Field specified and not same as `Amount` in `NFTokenOffer`

DEX liquidity will be used and other transfer processing (used in Payment/CheckCash) will be used.
If the quantity in `Amount` cannot be sent to the seller, the transaction will fail.

If the buyer's `Amount` can send more than the specified amount of the seller's `Amount`, the amount will be sent up to the maximum amount of the buyer's `Amount`.

## `NFTokenBrokerFee` Field specified

Convert and send the amount from the buyer's `Amount` to satisfy the `NFTokenBrokerFee`.

## Accept NFToken with TransferFee

Paid in the same currency as the buyer's `Amount`.
If no trustline is set, the transaction will fail.

## Accept NFToken with TransferFee, `tfOnlyXRP`, `Amount` Field specified, `NFTokenBrokerFee` Field specified

Up to 3 times currency will be converted and up to 3 times token transfer fees will be charged.

1. From Buyer to Broker (`NFTokenBrokerFee` currency, Buyer's `Amount` currency fee)
1. From Buyer to Issuer (`TransferFee` currency or XRP, Buyer's `Amount` currency fee)
1. From Buyer to Seller (`Amount` currency, Buyer's `Amount` currency fee)

# Concern

## Transaction load

Processing load is expected to increase due to up to three cross-currency remittance processes (flows) within a single transaction.

However, instead of merely being concerned about the increased load of a single transaction, it should be noted that in the current, similar processing would have to be spread over two or more transactions, NFTokenAccept and CrossCurrency Payment.

## Royalty for NFToken with tfOnlyFlag

The royalty is sent by converting a portion of the buyer's Amount (TransferFee %) into XRP, so if there is not enough liquidity, the royalty might be almost zero.

# Note

The process used by Payment is used for currency conversion and remittance processing.
Path cannot be specified, and only direct AAA->BBB pairs are used at this time.

If auto-bridge is enabled by default by [XLS-60](../XLS-0060-default-autobridge/README.md), the auto-bridge path will also be used for the currency conversion process in this proposal.
