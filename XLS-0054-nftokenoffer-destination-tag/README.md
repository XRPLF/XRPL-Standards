<pre>
  xls: 54
  title: NFTokenOffer Destination Tag
  description: Add DestinationTag to NFTokenCreateOffer transaction and NFTokenOffer object
  author: Florent (@florent-uzio)
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/152
  created: 2023-11-27
  status: Stagnant
  category: Amendment
</pre>

# Challenge Overview

My team is working with multiple partners who build on the XRP Ledger.
The majority of those partners mention the cost associated with the XRP reserves (base + owner) which can quickly become high.
Some projects use NFTs and they need to create hundred, thousand... of accounts. Those projects custody the key for their end users.

As an example, in 2023 an NFT project needed to create 4000 accounts requiring approximately 60,000 XRP for it (10 base + ~5 to cover transaction fees and owner reserves).

# 1. Proposed solution

To streamline this process and minimize costs, we propose a technical solution by modifying one ledger object and one transaction:

1. [NFTokenOffer](https://xrpl.org/nftokenoffer.html#nftokenoffer) ledger object
2. [NFTokenCreateOffer](https://xrpl.org/nftokencreateoffer.html#nftokencreateoffer) transaction

Those changes will require an amendment.

# 2. `NFTokenOffer` ledger object

One new field is added to the object: `DestinationTag`.

## 2.1. Fields

As a reference, the `NFTokenOffer` object has the current fields (in addition to the [common fields](https://xrpl.org/transaction-common-fields.html)):

| Name              | JSON Type       | Internal Type | Required |
| ----------------- | --------------- | ------------- | -------- |
| Amount            | Currency Amount | AMOUNT        | Yes      |
| Destination       | string          | AccountID     | No       |
| Expiration        | number          | UInt32        | No       |
| LedgerEntryType   | string          | UInt16        | Yes      |
| NFTokenID         | string          | Hash256       | Yes      |
| NFTokenOfferNode  | string          | UInt64        | No       |
| Owner             | string          | AccountID     | Yes      |
| OwnerNode         | string          | UInt64        | No       |
| PreviousTxnID     | string          | Hash256       | Yes      |
| PreviousTxnLgrSeq | number          | UInt32        | Yes      |

`DestinationTag` would be added to that object with the following specifications:

| Name           | JSON Type | Internal Type | Required |
| -------------- | --------- | ------------- | -------- |
| DestinationTag | Number    | UInt32        | No       |

# 3. `NFTokenCreateOffer` transaction

This transaction already exists and one field would be added to it: `DestinationTag`.

## 3.1. Fields

The current fields of that transaction are:

| Field       | JSON Type       | Internal Type | Required           |
| ----------- | --------------- | ------------- | ------------------ |
| Owner       | String          | AccountID     | Yes if `buy` offer |
| NFTokenID   | String          | Hash256       | Yes                |
| Amount      | Currency Amount | Amount        | Yes                |
| Expiration  | Number          | UInt32        | No                 |
| Destination | String          | AccountID     | No                 |

`DestinationTag` would be added to that transaction with the following specifications:

| Name           | JSON Type | Internal Type | Required |
| -------------- | --------- | ------------- | -------- |
| DestinationTag | Number    | UInt32        | No       |

## 3.2. Usage

Once the transaction is submitted and validated by the XRPL, the `DestinationTag` is stored in the `NFTokenOffer` object and will then be used by the NFT project backend to give ownership of a specific NFT to one of their user.

## 4. Flow, how would you use such `DestinationTag` for NFTs?

Let’s start this explanation by analyzing first a payment flow with an exchange like Coinbase for example.

We will then see how it can be expanded to NFTs.

Let’s say we have three people:

- Alice has a 2,000 XRP balance with Coinbase (so Alice has a destination tag),
- Bob has a 1,000 XRP balance with Coinbase (so Bob also has a destination tag).
- Doug has his own regular XRP address with a 1,500 XRP balance (no destination tag required for him).

![image](https://github.com/XRPLF/XRPL-Standards/assets/36513774/7901d35f-4899-4eb2-b805-acb35e4309dd)

If Alice wants to send Doug 500 XRP, Alice logs on to Coinbase, enters Doug's `r...` address & the amount, and clicks send. Coinbase's balance decreases, Doug's increases. A Payment transaction is sent on the XRPL. No problem.

If Doug wants to send Bob 500 XRP, first Doug needs to find Bob's destination tag for Coinbase. Bob logs on, finds the number, gives it to Doug, and Doug sends a transaction where the destination is Coinbase's r... address, and the destination tag is the number Bob gave Doug.
Doug's balance decreases, and Coinbase's balance increases. But there's an extra step - Coinbase has to examine that transaction, extract the destination tag, look it up in their own database, and then credit Bob with the XRP.

Now what if Bob wants to send Alice 750 XRP? If Coinbase submits a payment transaction from their own r... address with Bob's SenderTag to their own r... address with Alice's DestinationTag, the transaction will fail as malformed (`temREDUNDANT`)!

There's no point in having such a transaction on the ledger. Coinbase simply needs to update their own records to move the balance from Bob to Alice - there's no point in involving the XRPL.

**Now let's expand this example to include NFTs.**

An NFT project, such as the one mentioned at the top of the page that wants to create 4,000 wallets, might envision, for each NFT, to do the following:

1. Fund a "custodied" wallet with 15 XRP (Payment).
2. Mint the NFT ([NFTokenMint](https://xrpl.org/nftokenmint.html)).
3. Offer the NFT to the "custodied" account (create a sell [NFTokenCreateOffer](https://xrpl.org/nftokencreateoffer.html#nftokencreateoffer) with amount of 0 (the amount can vary, it’s just an example here) and `destination` set to the new wallet.
4. Have the new "custodied" wallet accept the NFT offer ([NFTokenAcceptOffer](https://xrpl.org/nftokenacceptoffer.html))

Step 4, though, implies that they control the secret key of the "custodied" wallet and submit transactions on its behalf.
Technically the NFT project buys and sells NFTs among their customers

**Now they're starting to sound like Coinbase.**

Using the exchange-like approach, the process for each NFT would be:

1. Mint the NFT ([NFTokenMint](https://xrpl.org/nftokenmint.html))
2. Internally assign ownership of the NFT to a customer,

Now, whenever one of their internal customers wants to buy or sell the NFT to another internal customer, there is no point in involving the XRPL, just like Bob paying Alice on Coinbase.

If an external wallet wants to buy one of the NFTs, they create an offer for it. They don't even necessarily have to know the destination tag of who owns it - but the NFT project doesn't submit an automated [NFTokenAcceptOffer](https://xrpl.org/nftokenacceptoffer.html) transaction until the current internal owner accepts it manually.

If one of the NFT Project users wants to buy an external NFT, _that_ is when `DestinationTag` comes in.

The NFT project submits a buy [NFTokenCreateOffer](https://xrpl.org/nftokencreateoffer.html#nftokencreateoffer) which includes the user's destination tag.
When the offer is accepted, the NFT project looks at the `NFTokenAcceptOffer` transaction metadata, which includes the offer being deleted (in the `DeletedNode` object), gets the `DestinationTag` from there, and credits ownership of the NFT to that account.

Now if an external wallet would like to sell an NFT to a specific user of that NFT project, that specific user will give his destination tag to the seller.
The seller submits a sell [NFTokenCreateOffer](https://xrpl.org/nftokencreateoffer.html#nftokencreateoffer) with the NFT project’s `r…` address as the destination, and the user's destination tag. Similarly as the buy scenario above, once the sell [NFTokenCreateOffer](https://xrpl.org/nftokencreateoffer.html#nftokencreateoffer) is accepted, the NFT project will credit ownership of the NFT to that specific user.

## 5. Additional Notes

1. The destination tag is NOT added to the [NFToken](https://xrpl.org/nftoken.html#nftoken) object itself. There's no need for it. It's the project's responsibility to internally update ownership of an NFT just like it's Coinbase's responsibility to update their customer's account balance when receiving a payment.

2. This proposal would interact with the `lsfRequireDestTag` flag on an `AccountRoot`. The `NFTokenCreateOffer` and `NFTokenAcceptOffer` transactors should enforce the behavior of that flag.

## 6. Benefits

- Cost Reduction: Minimizes XRP reserve requirements, lowering the financial burden on NFT projects. With `DestinationTag`, the NFT Project mentioned at the top of the page would only need one account (~200 XRP including base + [NFT reserves](https://xrpl.org/nft-reserve-requirements.html#nft-reserve-requirements)) instead of 4000 accounts (~60,000 XRP).
- Efficiency: Simplifies the process by internalizing ownership transactions, reducing the need for extensive ledger involvement.
- Enhanced User Experience: Streamlines the NFT creation and exchange process, making it more user-friendly for both project creators and consumers.
