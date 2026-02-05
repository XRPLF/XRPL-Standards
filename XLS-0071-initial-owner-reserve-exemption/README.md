<pre>
  xls: 71
  title: Initial Owner Reserve Exemption
  description: The first two account `objects` that are counted towards the `OwnerCount` shall not increase the `Owner Reserve`
  author: Vet (@xVet)
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/204
  created: 2024-07-01
  status: Stagnant
  category: Amendment
</pre>

## Terminology

The reserve requirement has two parts:

The `Base Reserve` is a minimum amount of XRP that is required for each address in the ledger.
The `Owner Reserve` is an increase to the reserve requirement for each object that the address owns in the ledger. The cost per item is also called the incremental reserve.

## Abstract

This proposal introduces the general initial owner reserve exemption.

The first two account `objects` that are counted towards the `OwnerCount` shall not increase the `Owner Reserve`. We enforce the increase of the `Owner Reserve` , if `OwnerCount > 2` , else zero (Free) - For all objects that can be owned by an account e.g Offers, DID, NFTs, Trustlines, Oracles etc.

## Motivation

1. We do this to allow new created accounts by users / enterprises to be immediately able to use the XRP Ledger without the need initial XRP for reserves to accept an NFT, Loyalty points, Stablecoin, a RWA etc thus signficantly reduces the initial pain point of using the XRP Ledger without compromising the logic behind reserves, if accounts wish to own more objects then the XRPL will enforce just normally the reserve requierments.

Owning an object on the XRP Ledger is a powerful feature that should be allowed up to the threshold of 2, to be free for any account.

2. In order to reduce the `base` and `owner` reserve long term, this step is a good middle ground. Typically, the concern around `account deletion fee` is associated with this topic. With this proposal we can keep this fee stable, as it is the owner reserve, reduce the base reserve long term but also get around the initial pain point of owner reserve funding

3. Xahau has the import feature, whereby if you import an activated XRPL account to Xahau, you get also 5 object slots for free. This seems to work well, where the `account deletion fee` on the XRPL is enough friction to prevent spam.

4. We already have this owner reserve exemption in a single case, for trustlines or more specific the `SetTrust` transaction, which helped trustlines to be a very popular and poweful feature on the XRPL for any new user.

## Implementation example

    XRPAmount const reserveCreate(
        (uOwnerCount < 2) ? XRPAmount(beast::zero)
                          : view().fees().accountReserve(uOwnerCount + 1));

Enforcing increase of owner reserve if OwnerCount > 2 in the `SetTrust`transaction

## FAQ

### A: Can this allow spam attacks ?

I don't see any attack vector that scales due to only the first two account object threshold, evidence in regards to Trustlines suggests that this is not a concern yet. Worst case, validators increase owner reserves in case spamming is observed, but the account deletion fee should be enough to prevent this.

### A: How to roll this exemption out and which transactors should have it ?

It makes sense to include this exemption over time to as many object creation transaction as possible in case of adoption, while closely monitoring the network.
