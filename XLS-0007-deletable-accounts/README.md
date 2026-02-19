<pre>
  xls: 7
  title: Deletable Accounts
  description: A feature for completely removing accounts from the ledger and recovering the reserve from those accounts
  author: Scott Schurr <scott@ripple.com>, Nik Bougalis <nikb@bougalis.net>
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/8
  status: Final
  category: Amendment
  created: 2019-10-01
</pre>

# Abstract

One desirable feature for the XRP Ledger would be for it to be possible to completely remove an account from the ledger and recover the reserve from that account. We call this a _deletable account_.

There are three primary concerns with deleting accounts:

1. If an account has obligations to other accounts on the ledger the account should not be deletable.
1. Once an account is deleted, if that account were to be recreated it should not be possible to replay old transactions on the newly created account.
1. Abuse should be discouraged. We'd like to avoid a situation, say, where someone creates thousands of accounts and later recovers all of the funds that were tied up in the account reserves.

## Account Obligations

What are the sorts of obligations that can occur between accounts on the XRP ledger? There are quite a few. But let's start with the classic: a [trust line](https://xrpl.org/trust-lines-and-issuing.html). A trust line, in part, tracks the balance of an [issued currency](https://xrpl.org/issued-currencies-overview.html) between two accounts in the XRP Ledger. Whenever that balance is anything other than zero, that means one of the two accounts owes that much of the currency to the other account.

### What Is Desirable

Conservatively, if one account owes currency to another account both of those accounts must be retained on the ledger until the debt is resolved.

Here's a list of all the ledger objects that represent obligations, both debts and other sorts, between accounts:

- [`Check`](https://xrpl.org/check.html),
- [`Escrow`](https://xrpl.org/escrow-object.html),
- [`PayChannel`](https://xrpl.org/paychannel.html), and
- [`RippleState`](https://xrpl.org/ripplestate.html) (the in-ledger representation of a TrustLine)

Clearly an account that holds any of these types of ledger objects should not be deleted from the ledger.

`Escrow` is worth expanding on. An `Escrow` is often between two accounts. But an `Escrow` may be from one account to the same account. Note that an `Escrow` from an account to itself is still an obligation between accounts; it's an obligation from that account to all of the other accounts on the ledger. That `Escrow` says, in effect, the escrowing account will retain ownership of the escrowed XRP (i.e., not spend that XRP) until the `Escrow` expires.

There are a few ledger types that an account can hold _without_ any obligations to other accounts. Those are:

- [`DepositPreauth`](https://xrpl.org/depositpreauth-object.html),
- [`DirectoryNode`](https://xrpl.org/directorynode.html),
- [`Offer`](https://xrpl.org/offer.html),
- [`SignerList`](https://xrpl.org/signerlist.html), and
- `Ticket` (not yet in the XRP Ledger Documentation Portal).

And, finally, there are transactions that don't (directly) add or remove any of the account's directory entries:

- [`AccountSet`](https://xrpl.org/accountset.html),
- [`Payment`](https://xrpl.org/payment.html), and
- [`SetRegularKey`](https://xrpl.org/setregularkey.html).

So, at least by the guidelines we've set out so far, an account should be deletable if it holds none of the following ledger types:

- [`Check`](https://xrpl.org/check.html),
- [`Escrow`](https://xrpl.org/escrow-object.html),
- [`PayChannel`](https://xrpl.org/paychannel.html), or
- [`RippleState`](https://xrpl.org/ripplestate.html) (the in-ledger representation of a TrustLine).

### What Is Achievable

However there's a fly in this ointment. It is not uniformly easy to tell when an account is associated with one of these obligations. Generally an obligation leaves a link behind in the directories of accounts the obligation is associated with. For example when a `RippleState` is added to the ledger, the two accounts associated with that `RippleState` each have a link added from their directory to the new `RippleState`. Those links make it relatively easy to see that the accounts are related to the `RippleState`. You just have to walk the account's directory entries.

`Check`s also have links similar to the ones that are added for `RippleState`. And `Escrow`s created since November 14 2017 (when [fix1523](https://xrpl.org/known-amendments.html#fix1523) was enabled) also have similar links.

But older `Escrow`s (none of which are on the production XRP Ledger) and all current `PayChannel` objects only have one link: a link to the owner.

We'll call these obligations that lack a back link from their destination accounts _legacy obligations_.

The lack of a link from the destination to a legacy obligation means we can't currently prevent deletion of an account that is the destination of a legacy obligation.

What to do?

- Add an amendment so new `PayChannel`s have links from their destination as well as from their owner. That way new `PayChannel`s will have the desired behavior. The amendment will affect the `PaymentChannelCreate` transaction and the `account_channels` and `account_objects` RPC commands.
- An account that is the destination of a legacy obligation _can_ be deleted. There is not enough information available to prevent it.
- Add rules for handling `Escrow` and `PaymentChannel` transactions where the destination account is missing from the ledger. More on that in the next section.

The upshot is that, as long as legacy `PayChannel` or `Escrow` objects are in the ledger, a person deleting an account needs to be careful. But if an account goes missing, then transactions operating on legacy obligations will have reasonable behavior.

### Obligations Where the Destination Disappeared

It's worth thinking hard about the behavior an `Escrow` and a `PayChannel` should exhibit if their destination account goes missing. When thinking about this it is worthwhile to consider two related issues:

1. Once deleted, an account can be resurrected (see section below). To a `PayChannel` and an `Escrow`, a destination account that has been deleted and resurrected is indistinguishable from an account that was never deleted. Since that's the case, how many special conditions do we want for the case where the destination account is missing (and might be resurrected later)?

   My personal take is that we should minimize the number of special conditions that we handle when a destination is absent since that destination may very well be resurrected in the future.

1. Whatever rules we choose should be minimal and unsurprising. We actually never expect to see these rules applied to `Escrow`s on the production ledger. There are currently no escrows in the production ledger that meet the conditions where these rules would apply. However we do expect these rules may be applied to some number of `PayChannel`s.

#### `PayChannel` With a Missing Destination

There are three transactions that affect `PayChannel` objects. They are:

**`PaymentChannelCreate`** is unaffected. The destination must be present for this transaction to succeed.

**`PaymentChannelFund`** should fail if the destination is not in the ledger. However the `PayChannel` itself should be otherwise unaffected.

**`PaymentChannelClaim`** can exhibit a lot of different behaviors (see [PaymentChannelClaim](https://xrpl.org/paymentchannelclaim.html)) depending on its arguments. Here are the different scenarios:

- The **source** address of a channel can:
  - Send XRP from the channel to the destination.

    _If the destination account is missing from the ledger this should fail and leave the channel otherwise unaffected._

  - Set the channel to expire as soon as the channel's SettleDelay has passed.

    _This should succeed._

  - Clear a pending Expiration time.

    _This should succeed._

  - Close a channel immediately if the channel has no XRP remaining.

    _This should succeed._

- The **destination** address of a channel can do nothing in any of these cases; the destination account is missing from the ledger.

- **Any address** sending this transaction can:
  - Cause a channel to be closed if its Expiration or CancelAfter time is older than the previous ledger's close time. Any validly-formed `PaymentChannelClaim` transaction has this effect regardless of the contents of the transaction.

    _This should succeed._

#### `Escrow` With a Missing Destination

There are three transactions that affect `Escrow` objects. They are:

**`EscrowCreate`** is unaffected. The destination must be present for this transaction to succeed.

**`EscrowFinish`** should fail with an error if the destination is missing. An `EscrowFinish` cannot be used to create (or resurrect) an account. However the `Escrow` object itself is otherwise unaffected and remains in the ledger.

**`EscrowCancel`** should be unaffected other than that the destination cannot be the account that does the cancel, since the destination account is missing from the ledger.

## Preventing Replay

A very important part of the XRP Ledger's security model is that any given transaction can be applied at most once. So we should not only be concerned with accounts being deleted. We also need to be concerned with old transactions if that deleted account is ever recreated in the ledger.

### Resurrecting An Account

But first, how could an account be recreated after it has been deleted?

Turns out that's pretty easy. All it takes is a single payment of XRP to the account ID of the deleted account and the account springs back to life. The XRP payment must be sufficient to meet the base reserve. That's it!

The resurrected account has no recollection of its previous life. In effect, it has the same name -- the same _identity_ -- as the earlier account. But that's all it has in common.

Why is it so easy to resurrect an account? Because once an account is deleted it's _gone_. The current ledger has no idea that the account ever existed. So, as far as the ledger is concerned, the resurrected account is actually a brand new account.

If a deleted account is ever resurrected in this way we want to be sure that old transactions from that identity cannot be re-applied against the resurrected account.

### Preventing Replay on a Resurrected Account

The standard mechanism for preventing transaction replay on a given account is the `Sequence` number. An `AccountRoot` carries a 32-bit integral `Sequence` value. Any successful transaction must carry the matching `Sequence` number or else the transaction is rejected. Certain kinds of failing transactions (the _nearly_ successful ones, coded `tec`) also must carry the matching `Sequence` number.

Once the transaction succeeds (or fails with a `tec`) the `AccountRoot`'s `Sequence` is incremented. This increment prevents that `AccountRoot` from accepting that previous `Sequence` number in a transaction ever again.

We can leverage this behavior to make resurrected accounts never accept old transactions. Here's how:

1. Only allow an account to be deleted if its `AccountRoot`'s `Sequence` number is at least 256 less than the current `LedgerSequence` number of the ledger the transaction is applied to. This should be an easy requirement for most accounts to meet. There are two ways to fail to meet the requirement.
   1. In order to fail that requirement an account would need to, on average, put one or more transactions into every validated ledger. Such accounts do, indeed, exist. But they are rare. See Appendix D.

   1. Another way to fail that requirement is for the account in question to have been created within the last 20 minutes or so.

   In either case, simply letting an account (that hasn't been extraordinarily busy) sit quietly for a little while will let the `LedgerSequence` get far enough past the `AccountRoot`'s `Sequence` that the account can be deleted.

1. Change the rule for the starting value of the `AccountRoot`'s `Sequence` number on a new account. Historically the `Sequence` number has always started at 1. Now we will start the `AccountRoot`'s `Sequence` at the value of the current `LedgerSequence` of the ledger the transaction is applied to. That will be much greater than 1.

Now, when a new account is created, any valid transactions from a previously existing account with the same account ID cannot be replayed on the resurrected account. The sequence numbers of any old transactions are in the past. Every one of those old transactions will fail with a `tefPAST_SEQ` error code.

Requiring the `AccountRoot`'s `Sequence` be at least 256 less than the current `LedgerSequence` is the result of an abundance of caution. It would probably be adequate for the `AccountRoot`'s `Sequence` to be one less than the current `LedgerSequence`. One less should be sufficient to prevent problems if an account is deleted and resurrected in the same ledger. But a difference of 256 gives us some breathing room (to account for things like the TxQ and transaction retries). The particular choice of 256 versus other numbers matches the occurrence rate of flag ledgers. This means there are slightly fewer arbitrary numbers for XRP Ledger users to remember.

### Consequences of Using the `LedgerSequence` as the First `Sequence`

Having the initial `Sequence` number of an account root be the current `LedgerSequence` rather than one will complicate the lives of folks who do air gapped account setup.

What is air gapped account setup?

For some folks, setting up a new account on the XRP Ledger is a multi-step process. They want to create the account, yes. But they also want to set certain flags on the `AccountRoot`. They may also want to set up a `RegularKey` or, possibly, give the account multisigning capability by adding a `SignerList`. Getting it all done takes multiple transactions. That is account setup.

_Air gapped_ account setup is when you want to write all of the setup transactions in one shot on an air gapped computer. The air gapping keeps the private key used to sign all of those transactions more secure. Then you (manually) carry all of those signed transactions over to a computer that is connected to the web and submit them to the Ledger.

Historically air gapped account setup has been pretty easy because the newly created account always had `Sequence` one. However if the `Sequence` value of a newly created account varies depending on when the account is created the problem gets harder.

There is at least one work around. But the work around is complicated enough that the description is given in Appendix C. Not here.

## Avoiding Abuse

The XRP Ledger doesn't have very many levers to discourage abusive behaviors. Pretty much all it can do is make abusive behaviors more expensive.

So, at least for the initial release, deleting an account will not return _all_ of the XRP. To accomplish this a transaction that deletes an account has a minimum fee that is equal to the [owner reserve](https://xrpl.org/reserves.html#owner-reserves). At the time of this writing (September 2019) that owner reserve is 5 XRP. So if someone creates an account with 20 XRP, they can get 20 XRP minus 5 XRP equals 15 XRP back.

Once we understand the actual uses of account deletion it will be possible to lower that fee with an amendment. But having a high fee allows us to start with a conservative approach.

One other possible form of abuse would be deleting an account with a huge number of directory entries. If a single transaction affects too many ledger nodes then the transaction can't complete because it produces too much metadata. Producing too much metadata helps no one. All of the nodes on the network execute the transaction which fails and then the transaction's fee is burned.

So rather than allow deleting an account to fail with a `tecOVERFLOW` we set a limit of 1000 directory entries that will be deleted along with the account. This is a high enough number for any reasonable deletable account. And it's also low enough that there shouldn't be any issue with an account delete producing a `tecOVERFLOW` result. So if an account has more than 1000 directory entries, attempting to delete that account will give a `tefTOO_BIG` result.

## How To Delete An Account

We expect deleting an account to be an unusual enough circumstance that it deserves its own, brand new, transaction. We'll call it `AccountDelete`.

What are the upsides?

- We can give the new transaction exactly the behavior that we want, rather than relying on some pre-existing transaction being pretty close to what we want.

- It will be easier to find account deletion in the ledger history.

- We can return better error messages if we're certain that the user's intent is to delete the account.

- An `AccountDelete` transaction can do extra work, like deleting `DepositPreauth`s or `Ticket`s from the account.

- We can give the `AccountDelete` transaction a `Destination` without an `Amount`. The `Destination` receives whatever XRP is left when the transaction completes.

What are the downsides? Simply that we're adding a new transaction type.

## Summary

### Changes That Affect All Newly Created Accounts

- Once the DeletableAccounts amendment passes, _all_ newly created accounts will have their `AccountRoot`'s `Sequence` field initialized to the the current `LedgerSequence` value, not to one.

### Account Deletion

- An account is deleted with an `AccountDelete` transaction.
- The `AccountDelete` carries a `Destination`. XRP left over after the account is deleted goes to the `Destination`.
- An account can be deleted if it meets three requirements:
  - The `AccountRoot`'s `Sequence` number must be at least 256 less than the current value of the `LedgerSequence`.
  - The account has none of the following ledger types in its directory:
    - [`Check`](https://xrpl.org/check.html),
    - [`Escrow`](https://xrpl.org/escrow-object.html),
    - [`PayChannel`](https://xrpl.org/paychannel.html), or
    - [`RippleState`](https://xrpl.org/ripplestate.html).
  - An account with more than 1000 directory entries is not deletable until the number of directory entries is reduced to 1000 or less.
- A _legacy obligation_ is an obligation ledger type that does not have a back link from its destination account to the obligation. An account that is the destination of a legacy obligation _can_ be deleted. There is not enough information available to prevent it. Caveat emptor.
- The following transaction types are adjusted so they handle a missing destination account as well as possible:
  - [`EscrowFinish`](https://xrpl.org/escrowfinish.html),
  - [`PaymentChannelClaim`](https://xrpl.org/paymentchannelclaim.html), and
  - [`PaymentChannelFund`](https://xrpl.org/paymentchannelfund.html).
- The `AccountDelete` transaction automatically removes the following ledger types from the account and, if appropriate, recovers their reserve:
  - [`DepositPreauth`](https://xrpl.org/depositpreauth-object.html),
  - [`DirectoryNode`](https://xrpl.org/directorynode.html),
  - [`Offer`](https://xrpl.org/offer.html),
  - [`SignerList`](https://xrpl.org/signerlist.html), and
  - `Ticket` (not yet in the XRP Ledger Documentation Portal).
- It is possible to "resurrect" a deleted account by sending sufficient XRP to the deleted account ID. But the resurrected account shares only its _identity_ with the deleted account. All other characteristics are lost. So the resurrected account is neither a zombie nor a clone; it has a duplicate of the deleted account's social security number.
- An `AccountDelete` transaction has a minimum fee equal to the [owner reserve](https://xrpl.org/reserves.html#owner-reserves). This minimum fee is the same regardless of whether the transaction is multisigned or not.

## Appendix A: Design Decisions

---

**Q:** Do the suggested rules miss any conditions that should prevent an account from being deleted?

**A:** We don't think so. Of course, the proposed rule changes and the implementation should be very carefully reviewed.

---

**Q:** Are there preferable approaches besides using a new `AccountDelete` transaction to delete accounts?

**A:** Using a standard `Payment` transaction instead of `AccountDelete` was discussed as a possibility. The feeling was that a transaction specifically designed for deleting an account was a better choice.

- An explicit `AccountDelete` improves clarity in the transaction itself and in history for what was intended to be accomplished.
- An explicit `AccountDelete` transaction makes it sensible to perform helpful operations, like destroying an account's leftover `Ticket`s. The additional work makes no sense within the context of a `Payment` transaction.
- An explicit `AccountDelete` with no `Amount` field removes a scenario where a partial payment might be deployed.

---

**Q:** Is the proposed `AccountDelete` doing too much work? Should we force people to manually remove any excess `SignerList`, `DepositPreauth`, or `Ticket` objects in their directory?

**A:** We don't think so. The work it does is beneficial in three ways:

1. If a user wants to delete an account, the work it does makes it easier for that account to be removed from the ledger. In this way it benefits the owner of the account.
1. It saves the user fees that would be associated with manually removing each of those items from the ledger. This also is a benefit for the owner of the account.
1. It removes unwanted entries from the ledger. That benefits all users of the XRP Ledger.

---

**Q:** Should `AccountDelete` support an optional `DeliverMin` field?

**A:** No. If you want to delete the account, you just want it gone. As long as the XRP is recovered you've accomplished your goal. If we discover a reason in the future why a `DeliverMin` is desirable then we can add it later.

---

**Q:** Should we allow the `Destination` of an `AccountDelete` to be the same as the `Account`? Such a transaction would destroy and resurrect the account in a single step.

**A:** No. This is a conservative choice. If two different transactions are required to delete and then to recreate an account, then the ledger history will actually show the account being deleted and then recreated as two separate events. If they happen in the same transaction then the metadata record shows an `AccountRoot` modification, which is not actually what happened.

This is also the kind of capability that could be added later if a crying need shows up.

---

**Q:** Is it fair to require the `Destination` of an `AccountDelete` to already exist?

**A:** Yes. This too is the conservative choice. It allows `AccountDelete` to not know about account creation, which currently only Payment knows. Simpler code runs faster and has fewer bugs.

This too is a capability that could be added later if there is a crying need.

---

**Q:** This account resurrection thing seems like it could be dangerous. Is there a way to prevent that?

**A:** Yes, it could be prevented, but at a fairly high cost.

In order to prevent a deleted account from being resurrected, the ledger would need to keep a record of each deleted account. Consider, if account deletion becomes popular, there may eventually be millions of deleted accounts. So any record of deleted accounts needs to be compact, scalable, and support efficient lookup. And, at least with the current design, there would be no cost to ledger users for adding more deleted account records. So users would not be motivated to try to limit the number of deleted accounts that they create.

Therefore, rather than deal with the problem of unbounded in-ledger deleted account record storage, we're choosing to live with the peculiarities of account resurrection.

---

**Q:** Should there be a flag that prevents a `Payment` from accidentally resurrecting an account?

**A:** This was considered and rejected. In hindsight it would have been great to require a Payment to set a flag if it was creating an account. Or, even better, have a distinct transaction to create an account. Neither of those are in place today.

What we could do today is add a flag to the `Payment` transaction that would prevent account creation. The general belief is that even if such a flag were added the actual adoption of the flag would be minimal. The added complexity would not be worth the payoff.

---

## Appendix B: Specification

### Affected Ledger Type: `AccountRoot`

Although this change does not show in the structure of the `AccountRoot` an `AccountRoot` can now be deleted from the ledger, which has never before been possible.

Additionally, once the amendment passes, the starting value of the `Sequence` number of the `AccountRoot` is affected.

- Prior to the amendment, the `Sequence` field starts at `1`.
- After the amendment passes the `Sequence` field inherits the value of the current `LedgerSequence` as the starting value.

### Affected Transactions

#### New Transaction: `AccountDelete`

**Parameters**

| Field            | Style    | Description                                                      |
| ---------------- | -------- | ---------------------------------------------------------------- |
| `Account`        | Required | Account that is being deleted                                    |
| `Destination`    | Required | Account that receives remaining XRP from deleted Account         |
| `DestinationTag` | Optional | Destination tag that receives remaining XRP from deleted Account |

The following example is an `AccountDelete` transaction that deletes account "a" and sends the remaining XRP to another account, [`rrrrrrrrrrrrrrrrrrrrrhoLvTp`](https://xrpl.org/accounts.html#special-addresses).

```
{
    "Account" : "rnUy2SHTrB9DubsPmkJZUXTf5FcNDGrYEA",
    "Destination" : "rrrrrrrrrrrrrrrrrrrrrhoLvTp",
    "Fee" : "12",
    "Flags" : 2147483648,
    "Sequence" : 5143,
    "SigningPubKey" : "029A80E85C9...81CC071B7D0C",
    "TransactionType" : "AccountDelete",
    "TxnSignature" : "3045022100F...C64162FA0630"
}
```

Reasons why an `AccountDelete` transaction might fail:

- The `AccountDelete` transaction does not specify a large enough `Fee`.
- `Account` does not have sufficient XRP to pay the fee.
- `Account`'s `AccountRoot`'s `Sequence` number is not at least 256 less than the current `LedgerSequence` value.
- `Account` and `Destination` are the same.
- `Destination` is not present in the ledger.
- `Destination` requires deposit preauthorization which is not granted.
- `Account` has at least one of the following ledger types anywhere in its directory:
  - [`Check`](https://xrpl.org/check.html),
  - [`Escrow`](https://xrpl.org/escrow-object.html),
  - [`PayChannel`](https://xrpl.org/paychannel.html), or
  - [`RippleState`](https://xrpl.org/ripplestate.html).
- `Account` has more than 1000 directory entries at the time of the `AccountDelete` transaction.

If successful, the `AccountDelete`:

- Removes from the ledger any of the following ledger types that were owned by `Account`:
  - [`DepositPreauth`](https://xrpl.org/depositpreauth-object.html),
  - [`DirectoryNode`](https://xrpl.org/directorynode.html),
  - [`Offer`](https://xrpl.org/offer.html),
  - [`SignerList`](https://xrpl.org/signerlist.html), and
  - `Ticket` (not yet in the XRP Ledger Documentation Portal).
- Transfers any XRP left over from `Account` into `Destination`'s balance.
- Removes `Account`'s `AccountRoot` from the ledger.
- An `AccountDelete` transaction has a minimum fee equal to the [owner reserve](https://xrpl.org/reserves.html#owner-reserves). This minimum fee is the same regardless of whether the transaction is multisigned or not.
- If an `AccountDelete` transaction goes into the TxQ, it is considered a blocker. It is handled the same way `SetRegularKey` and `SetSignerList` transactions are handled by the Txq.

#### Modified Transaction: `EscrowFinish`

An `EscrowFinish` transaction fails if the destination account is missing from the ledger. However the `Escrow` object in the ledger is otherwise unaffected.

#### Modified Transaction: `PaymentChannelClaim`

A `PaymentChannelClaim` that sends XRP from the channel to the destination should fail if the destination is missing from the ledger. However the `PayChannel` object in the ledger is otherwise unaffected.

#### Modified Transaction: `PaymentChannelFund`

A `PaymentChannelFund` transaction where the destination account is missing from the ledger fails. However the `PayChannel` object in the ledger is otherwise unaffected.

#### Hardening Transaction Processing

All transactions should be audited to make sure they handle a missing `AccountRoot` as well as possible.

### Affected RPC Commands

It will be useful to modify `account_objects` to return all of those objects that represent obligations. That will help users identify what needs to be explicitly removed before an account can be deleted. So the `account_objects` RPC command will accept a new `type` argument. Calling `account_objects` with `"type" : "blocks_deletion"` will cause `account_objects` to return only those objects that will prevent account deletion.

### Other Things Affected

#### Error Codes

There are likely to be some number of `tef` and `tec` error codes added as a result of this effort. The specific error codes have not been identified yet.

#### Amendments

##### `featureDeletableAccounts`

There are two coordinated changes which hinge on a single new `featureDeletableAccounts` amendment. Once that amendment passes two changes occur:

- The starting `Sequence` number of all newly created `AccountRoot` objects is the current `LedgerSequence` of the creation ledger. Previously created `AccountRoot` objects are unaffected.
- It is possible to delete an `AccountRoot` from the ledger using the `AccountDelete` transaction.

##### `fixPayChanRecipientOwnerDir`

After this amendment passes then newly created `PayChannel`s will install back links from both the owner's and the destination's directories to the `PayChannel`. `PayChannel` objects created before the amendment passes are unaffected. Accounts that are the destination of these newer `PayChannel`s will not be deletable.

#### Invariant Checks

The preexisting **AccountRootsNotDeleted** check will be modified so it does not fire when the transaction is an `AccountDelete`. It also will verify that exactly one account root is deleted by a successful `AccountDelete` transaction. Otherwise an account root is never deleted.

A new invariant check will verify that at most one account root is created in one transaction. If an account root is created then the transaction must be a Payment. It also verifies that the newly created account root has the correct Sequence value.

## Appendix C: A Process for Air Gapped Account Setup

As noted in the **Consequences of Using the `LedgerSequence` as the First `Sequence`** section, air gapped account setup becomes more difficult once the `LedgerSequence` is the first `Sequence` of a brand new `AccountRoot`. Previously a person could build their setup transactions and use them seconds, months, or years later. That will no longer be possible.

Three accommodations are required:

1. The person building the transactions must guess approximately the `LedgerSequence` that will be active when their new account is created. We'll call this the first possible ledger sequence.

1. Additionally, the person must decide how much variability they want to allow for when their new account is created. In 2019 so far ledgers are closing about once every 3.7 seconds. So if you want variability of 60 seconds, that's about 17 ledgers. If you want variability of 10 minutes (600 seconds) that's about 165 ledgers. By adding the number of ledgers of variability to the first possible ledger sequence, then you get what we'll call the last possible ledger sequence.

1. Finally, the person must monitor the network using the `ledger` RPC command to identify an appropriate time to apply the transactions.

Once the first and last possible ledger sequences are known the transactions can be constructed. Here is the process.

1. Construct the transaction that will fund the new account. Set the `LastLedgerSequence` field of the transaction to the value of the last possible ledger sequence. This will prevent the transaction from succeeding in case the buffer is entirely missed.

1. Construct a set of [no-op transactions](https://xrpl.org/cancel-or-skip-a-transaction.html). The first no-op transaction uses as its `Sequence` the first possible ledger sequence. Then build as many additional no-op transactions as are needed to allow for the desired variability. Each no-op transaction uses the next sequence value for its `Sequence`. So, for 60 seconds of variability it would take about 17 no-op transactions total. The last no-op transaction has the last possible ledger sequence as its `Sequence`.

1. The no-op transactions supply the buffer. Now create the additional (non-no-op) transactions that should be applied to the account in question. These transactions use `Sequence` numbers starting one after the last possible ledger sequence and increment from there.

1. Move all of the (signed) transactions from the air gapped machine over to the machine attached to the network.

1. Using the `ledger` RPC command, monitor the main network for the first possible ledger sequence.

1. When the `"open"` ledger shows a `"seqNum"` equal to or greater than the first possible ledger sequence then submit all of the transactions to the network.

1. Depending on the number of transactions in the account setup, how busy the server you submit the transactions to is, and how busy the network is, it is possible that not all of the transactions will be processed or queued. Assuming all the transactions are properly signed and well formed, if the server is busy one or more of the transactions may return the error response "slowDown", "tooBusy", or "telCAN_NOT_QUEUE". If this occurs consider dividing your transactions into smaller batches and submit the batches to consecutive ledgers. However, once the new account is successfully created you don't have to hurry to get the transactions into the ledger (except for transactions where the `LastLedgerSequence` field is filled in).

The "buffer" works by providing transactions that no one cares if they fail. If the account's first `Sequence` number is several past the first possible ledger sequence, then those no-op transactions simply fail with a `tefPAST_SEQ` error code and are dropped from the network. The remaining no-op transactions are applied to the account, but have no negative consequences other than the fee they burn.

## Appendix D: Main Net Accounts With `Sequence` Greater Than `LedgerSequence`

The Ripple Data team examined a recent ledger and found a total of three accounts on the Main Net where the `AccountRoot` `Sequence` field got ahead of the `LedgerSequence`. Here are the transactions where the differences were largest for those three accounts. Note that the table is wide and you need to scroll left and right to see all the contents.

| Account                            |                                                 Transaction Hash | Tx Sequence | Ledger Index |   Ahead By |
| :--------------------------------- | ---------------------------------------------------------------: | ----------: | -----------: | ---------: |
| rBxy23n7ZFbUpS699rFVj1V9ZVhAq6EGwC | D739D41D5C899E1FC9EC59B92B29F2B6FBD4C4259EA3395CBBA31511121EFE4A |  52,235,732 |   47,915,816 |  4,319,916 |
| rEr3hxu5aim5tDWwH7H8BK47K91tR8c7FM | F077665E0BE74A22F8E098561B83DDAD7AD9B83E95257CCEFF69741F14DFBCA1 |  80,387,155 |   43,829,273 | 36,557,882 |
| rH3uSRUJYoJhK4kL9x1mzUhDimKE2n3oT6 | 2607AEE01EFE10CAF698E1576FD3430A6FD35B86BF78EA49D2BFB03E8D918D75 |  47,797,501 |   43,830,353 |  3,967,148 |
