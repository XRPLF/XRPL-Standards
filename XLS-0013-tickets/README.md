<pre>
    xls: 13
    title: Tickets & Ticket Batching
    description: Tickets allow selected transactions on a single account to be processed out of order, which could benefit some multisigning situations.
    author: Nik Bougalis (@nbougalis)
    proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/18
    created: 2020-09-01
    status: Final
    category: Amendment
</pre>

# Tickets

Tickets are a proposed change to the XRP Ledger protocol. They would allow selected transactions on a single account to be processed out of order, which could benefit some multisigning situations. This document outlines the use model and describes the current implementation.

## The Problem Statement

Multisigning on the XRP Ledger. Cool, huh? And it's actually getting used. In March of 2018 approximately 4.4% of all payment transactions on the XRP ledger were multisigned. That's over 33,000 payments in that single month. That's not a large percentage, but when you consider the total number of multisigned payments, it's significant.

As long as multisigning is being used in automated situations, it's great. But for non-automated situations there's at least one downside.

### Sequence Numbers

The trick is that in the XRP Ledger...

- Every account has an incrementing sequence number.
- Every transaction on that account must contain that sequence number.
- Transactions on that account must be applied to the ledger in order by sequence number.

For example, somebody just created an account for Zoe by sending her some XRP. Zoe's brand new account has a starting sequence number. The very first transaction that Zoe applies to her new account must contain that sequence number. If her first transaction omits the sequence number then the transaction fails. If her first transaction uses a sequence number other than the one in her account, then the transaction fails.

Once Zoe submits that first successful transaction then the sequence number on the account increments. So Zoe's next transaction must contain a sequence number one greater than the sequence number in her previous transaction. The story proceeds from there.

What does this have to do with multisigning? It impacts two possible multisigning scenarios.

### Multiple Independent Signers on One Account

With multisigning, it's possible to have multiple independent signers on a single account. Suppose Bonnie and Claudine meet at a Mixed Martial Arts club and decide to start a business together: C-Body Guards. They create an account for the business and set it up for multisigning. Bonnie and Claudine trust each other a great deal. They set up the account multisigning so Claudine can sign or Bonnie can sign for any transaction. (For the detail oriented, Bonnie has a signer weight of 1, Claudine has a signer weight of 1, and the signer list has a quorum of 1.)

Everything was going along just fine until one day when Claudine and Bonnie created independent transactions at about the same time. They both looked at the business account at about the same time and saw the same sequence number. They independently used that same sequence number to create two independent transactions. They submitted their transactions at about the same time. Just by chance Bonnie's transaction made it into the ledger first, so Claudine's transaction failed with `tefPAST_SEQ`. Claudine was puzzled by the error but re-submitted her transaction, with an updated sequence number, and the second one went through just fine.

Eventually Bonnie and Claudine figured out what had happened.

If Bonnie and Claudine started creating transactions frequently, then the rate of collisions would go up. Eventually it would become a problem.

### Multiple Required Human Signers

Prince, Elvis, and Moby decide to go into business together selling tree house kits. However Prince, Elvis, and Moby don't trust each other very much. So when they create their business account they decide that all three of them must sign for any transaction. (For the detail oriented, Prince, Elvis, and Moby each have a signer weight of 1, and the signer list has a quorum of 3).

Elvis decides to throw a party in honor of creating the business and creates a transaction to buy supplies for 2000 peanut butter, banana, and bacon sandwiches. Elvis signs the transaction, using the current account sequence number, and then sends it to Prince and Moby to sign. Moby sits on the transaction because he's not convinced that peanut butter, banana, and bacon sandwiches are the best party food.

In the mean time Prince decides that they should get down to business and buy some lumber for their tree house kits. But Prince has a conundrum. If he creates his transaction with the sequence number one greater than the account sequence, then he must wait until Moby has signed Elvis's transaction and Elvis's transaction has been submitted to and validated by the network. If Prince creates his transaction with the current account sequence number, and if it is validated by the network before Elvis's transaction, then Elvis's transaction could never be validated since it would have a sequence number that is already used. As a consequence Moby and Elvis might need to renegotiate; that would be a pain.

It would be great if there were a way to create transactions so acceptance of a later transaction would not be blocked by acceptance of an earlier transaction.

### Enter Tickets

The proposed solution to this problem (one transaction blocking another due to sequence number ordering) is a new ledger type called a Ticket. Fundamentally, a Ticket can be created on an account, then later that Ticket may be used in place of a sequence number. The order in which Tickets are used is not constrained by sequence number ordering.

So Bonnie, Claudine, Prince, Elvis, and Moby could all solve their problems by creating a bunch of Tickets on their accounts first. Those Tickets would then be assigned to individuals. The individuals can then create their transactions, using Tickets instead of sequence numbers, without having to worry about the sequence number ordering of their own, or anybody else's, transactions.

Now that you understand the point of Tickets, you may want to read about the details, which follow. If you just want the summary, and not the details, you can skip to the [_**Summary**_](#Summary) and the [_**FAQ**_](#FAQ) sections toward the bottom of this document.

## Discussion of the Details

Creating a replacement for something as fundamental as sequence numbers in transactions is delicate work. The following design is as simple as possible. But even with that, there are a lot of details to attend to.

### Why Sequence Numbers?

We need to start by understanding why each account has a sequence number in the first place.

The most important role of the `Sequence` number is that it makes each transaction on an account unique. Consider if Zoe created a transaction to pay 10,000 XRP to Brent. Once that transaction is validated in the ledger what prevents that transaction from being arbitrarily replayed time and again? All of the data in the transaction is correct and the transaction is correctly signed. Otherwise the transaction would not have been validated in the first place. If a transaction is valid, what is it that makes that transaction only valid one time?

The rule that a `Sequence` number may not be re-used in two or more transactions is what keeps Zoe's transaction from being reused. So, because of that `Sequence` number, Zoe can have confidence that her transaction will only be validated once.

Additionally, the `Sequence` number plays a role in guaranteeing that each validated transaction in the ledger has a unique hash. The uniqueness of the hash of each validated transaction is important because all transactions are located in the ledger by their hashes. The ledger is not set up to handle hash collisions because hash collisions are not expected to ever occur. The hash of each transaction is, in part, guaranteed to be unique because the serialized data in each transaction (which includes the `Sequence` number) is guaranteed to be unique.

What matters for both of these considerations is that the `Sequence` number must be unique for each transaction on the account. They don't really need to be sequential. But there's a lot of complexity that is reduced by requiring each `Sequence` number to be consecutive. If they are consecutive then they will automatically be unique (until the integer overflows). And consecutively produced and consumed `Sequence` numbers are easy to think about and compute.

So whatever we do with `Ticket`s needs to carefully:

- reproduce the uniqueness that `Sequence` numbers provide while
- removing the requirement for consecutiveness.

### Creating `Ticket`s

#### Creating One `Ticket`

In order to use a `Ticket` on an account, that `Ticket` must first be created. That takes a transaction.

A successful `TicketCreate` transaction adds a `Ticket` in the directory of the owning account. That `Ticket` contains a `TicketSequence` which is now available to be used by a future transaction on that account. When the `Ticket` is created it computes a new `TicketSequence` number based on the `Sequence` of the account root. That `TicketSequence` number will play an important role when it is time to consume the `Ticket`.

A unique `Ticket` can be identified in the ledger with only two pieces of information: the ID of the account that owns the `Ticket` and the `TicketSequence` number of that `Ticket`.

Once created, a `Ticket` lives in the owning account's directory. Therefore, adding that `Ticket` to the account takes one standard XRP reserve increment on that account (5 XRP in January of 2020). The more `Ticket`s held by the account, proportionally more reserve is required on the account. The reserve is returned to the account when the `Ticket` is consumed (which removes the `Ticket` from both the account directory and from the ledger).

##### The `TicketSequence` Value

What is the integer value of the `TicketSequence` associated with each `Ticket`? Uniqueness is an important consideration here. So how do we compute the value of a `TicketSequence`? There's really one rule, but exactly how that rule is applied depends on how the `Ticket` is created.

> **Rule:** Each created `Ticket` uses as its `TicketSequence` the next value that would be appropriate for the account root's `Sequence` field. It then modifies the account root `Sequence` field to be one greater than the largest created `TicketSequence`.

That rule may not be very clear simply from reading the description. Let's look at the two ways of creating `Ticket`s.

##### Creating a `Ticket` with a `Sequence`

If a `TicketCreate` transaction uses a `Sequence` number then the `TicketSequence` of the created `Ticket` is one greater than the transaction's `Sequence` number.

Say Alice sends a `TicketCreate` transaction with `Sequence` 7. If that transaction is successful, then the `Ticket` it creates will have `TicketSequence` 8. That's because the successful transaction's `Sequence`, by design, equals Alice's account root `Sequence`. Since Alice's account root `Sequence` is 7, and we're using up `Sequence` 7 with the current transaction, then the next viable `Sequence` is 8. And, since the largest `TicketSequence` created was 8, then the account root `Sequence` moves to 9.

By moving Alice's account root `Sequence` to 9, we make sure that Alice will not have any valid transactions where the `Sequence` and the `TicketSequence` values are the same. Later we'll see why that's useful (see [_**Offers with Ticket**_](#Offers-with-Ticket)).

It's worth noting, however, that Alice's account root `Sequence` just jumped from 7 to 9. So if Alice tries to send a transaction with `Sequence` 8 she'll get a `tefPAST_SEQ` error.

One valid way to think of this is that creating a `Ticket` reserves the corresponding `Sequence` number value so it can be used later. We'll be using it out of order, so we're calling it a `TicketSequence`, but the value is reserved.

##### Creating a `Ticket` with a `TicketSequence`

We're getting a bit ahead of ourselves, but once a `Ticket` has been created, that `Ticket` can be used to create another `Ticket`. The calculation for the `TicketSequence` value of the new `Ticket` works a bit differently than with a `Sequence`. Here's the rule:

If a `TicketCreate` transaction uses a `TicketSequence` number, then the `TicketSequence` of the newly created `Ticket` is the account root's `Sequence` number.

Let's pick up from where Alice left off. Alice has a `Ticket` with `TicketSequence` 8. Alice's account root `Sequence` is 9. Alice now does a `TicketCreate` with `TicketSequence` 8. Since Alice's account root `Sequence` is 9, and the `TicketCreate` is _not_ using `Sequence` 9, then the new Ticket gets `TicketSequence` 9. Alice's account root `Sequence` moves to 10.

Even though the steps are a little different, we again see that creating the `Ticket` tucks away the next available unused and unreserved account root `Sequence` so Alice can use it later.

#### Creating Lots of `Ticket`s

There are problems with creating only one `Ticket` at a time on an account with multiple required human signers. For example, it doubles the work. You must create a transaction to create a `Ticket`. Then you must create the originally intended transaction and apply the `Ticket`. And all of those transactions must be signed by all of the required signers.

In effect `Ticket`s have doubled the amount of work we must do. If that were the state of the art, then `Ticket`s would not be worth the effort.

So we allow one `TicketCreate` transaction to create a whole bunch of `Ticket`s in one fell swoop. There is still the hassle of making a transaction and getting it signed by all of the multisigners. But only one transaction needs to be signed and submitted to create up to 250 Tickets. This seriously reduces, but does not eliminate, the hassle factor.

The XRP Ledger sets a limit on the amount of metadata one transaction is allowed to create. The question came up, how close is a transaction that creates 250 Tickets to that limit? Given an initial implementation of `Ticket`s, it was found that 5,041 Tickets could be created in a single transaction without excessive metadata. So setting the limit at 250 leaves us over an order of magnitude away from the boundary. That seems like enough safety margin.

##### Batch `TicketSequence` Assignment

So when a batch of `Ticket`s is created, how are the `TicketSequence` values assigned?

All of the `Ticket`s created in the same batch have contiguous integral values. The first value is determined as described in [_**Creating One `Ticket`**_](#Creating-One-Ticket). Once the value of that first `Ticket` is determined then each subsequent `Ticket` in the batch increments that starting value.

So, returning to Alice, Alice's account root `Sequence` is now at 10. She's tired of making just one `Ticket` at a time, and she has enough XRP that she can afford the reserve for an additional 100 `Ticket`s. So she sends a `TicketCreate` transaction with a `TicketCount` of 100 and `Sequence` 10. That will create a batch of `Ticket`s for her account that have `TicketSequence` values 11 through 110. Alice's account root `Sequence` will have the value 111 when the transaction completes.

### Using a `Ticket`

`Sequence` numbers are heavily used throughout the XRP Ledger for several different purposes. So it's worth thinking hard about how using a `TicketSequence` in place of a `Sequence` number will effect transactions and the ledger.

There are four primary ways in which `Sequence` numbers affect the ledger and transaction processing:

1. All transactions use the `Sequence` number to verify that the transaction is unique in the ledger and that the hash of the validated transaction is unique.
1. Some transactions use the `Sequence` number as a persistent identifier in a ledger object. This happens both...
   1. Explicitly (`Offer`s and `Check`s) and
   1. Implicitly (`Escrow` and `PayChan`).
1. The `Sequence` number of a transaction is used to sort transactions. This is important because
   1. Transactions are actually applied to a final ledger one-at-a-time in that sorted order and
   1. The Transaction Queue (`TxQ`) stores queued transactions in that order.
1. The account ID and `Sequence` number of a transaction can be used to identify all of the validated transactions associated with an account, as well as the order of those transactions.

All of these behaviors will be affected by the presence of `Ticket`s in transactions.

#### Transaction Validity With Tickets

##### Unique Transaction Hash

An important purpose that `Sequence` numbers fill is guaranteeing the uniqueness of the hash of validated transactions. How is that requirement met by `Ticket`s?

First let's compare a simple transaction using a `Sequence` number to the same transaction using a `Ticket`. With a `Sequence` number we see:

```
{
    "Account" : "rDg53Haik2475DJx8bjMDSDPj4VX7htaMd",
    "Fee" : "40",
    "Flags" : 2147483648,
    "Sequence" : 12,
    "SetFlag" : 4,
    "Signers" : [
      {
        "Signer" : {
           "Account" : "rwSqb8mM4hd7oKTiNWVzvjArgUnF2qYuhW",
           "SigningPubKey" : "EDD5DCA7954DAB...49225E107A15781",
           "TxnSignature" : "E4E23FC9FE7E7D8...B849B250651EB05"
        }
      }
    ],
   "SigningPubKey" : "",
   "TransactionType" : "AccountSet"
}
```

Now, for contrast, suppose instead that we'd created a `Ticket` using `TicketSequence` number 12. We'll now use that `Ticket`.

```
{
    "Account" : "rDg53Haik2475DJx8bjMDSDPj4VX7htaMd",
    "Fee" : "40",
    "Flags" : 2147483648,
    "Sequence" : 0,
    "SetFlag" : 4,
    "Signers" : [
      {
        "Signer" : {
           "Account" : "rwSqb8mM4hd7oKTiNWVzvjArgUnF2qYuhW",
           "SigningPubKey" : "EDD5DCA7954DAB...49225E107A15781",
           "TxnSignature" : "E4E23FC9FE7E7D8...B849B250651EB05"
        }
      }
    ],
    "SigningPubKey" : "",
    "TicketSequence" : 12,
    "TransactionType" : "AccountSet"
}
```

By examining the differences between these two transactions you can see that they will generate different hashes:

1. The `Sequence` field is present in both transactions, but in one transaction it's non-zero, in the other it's zero.
1. The `TicketSequence` field is new in the transaction that uses the `Ticket`.

The `Sequence` field is always required, but if a `TicketSequence` is present the `Sequence` field must be zero. If the `Sequence` field is ever omitted then the transaction is malformed. Correspondingly, a transaction that includes both a non-zero `Sequence` number and a `TicketSequence` field is treated as malformed and returns a `tem` code.

##### Testing for Transaction Validity and Uniqueness

One of the phases of transaction validity and uniqueness testing is `Sequence` validation. Usually the `Sequence` in the transaction is compared to the `Sequence` in the account root of the transaction's `Account`. If they are equal then that part of the validity check is good.

But here we have a `Sequence` of zero. First it's worth noting that when an account root is created it always gets a `Sequence` greater than zero. Since the account root `Sequence` field is incremented, it can never validly have a value of zero. Therefore there should never be any confusion about a transaction with a `Sequence` of zero. If the `Sequence` is zero in a transaction, then there had better be a `TicketSequence`. (`Sequence` field rollover could be a possibility a few years out from now. Before it becomes an issue there will be a different ledger feature to prevent `Sequence` rollover from happening before the Sun goes Red Giant.)

If the `Sequence` is zero then, in order to be a valid transaction, the presence of the `Ticket` in the ledger must be verified during the preclaim phase of transaction validation. If the `Ticket` is not found in the local ledger then the transaction is not forwarded to the network. Instead, the transaction is queued locally to be retried on the next ledger. The transaction will not be forwarded to the network until the appropriate `Ticket` is found in the local ledger.

#### Ledger Artifacts

Every transaction that operates on an `Account` today leaves some kind of artifact in the ledger. (We're ignoring pseudo transactions, since they don't operate on actual `Accounts`). Today, at a minimum, every transaction on an `Account` causes the `Sequence` of that account root to increment. With `Ticket`s we lose that guarantee of the `Sequence` increment. But there are still guaranteed changes to the ledger, including to the account root.

- Every time a `Ticket` is used, then the consumed `Ticket` is removed from the ledger. So the `Ticket` itself will be removed from the ledger.
- The account's directory will have the `Ticket` removed, so the directory will change as well.
- The `PreviousTxnID` field in the account root will be modified to contain the hash of the transaction that consumed the `Ticket`.
- Typically the `OwnerCount` field in the account root will decrease, but that is not required. If the transaction adds one entry to the account's directory, then the removed `Ticket` will be counter-balanced by the added directory entry (say an `Offer`) which could cause the `OwnerCount` field to be left unchanged.
- Also typically the account root `Balance` field would change due to the fee, but this too is not required. If the transaction does not require a fee (for example, a [Key Reset Transaction](https://xrpl.org/transaction-cost.html#key-reset-transaction)) then no fee will be consumed. Or, say with a `CheckCash` transaction, the transaction could bring just enough XRP into the account to counterbalance the fee. If this were to occur, then the `Balance` would not change.

##### Ledger Artifacts With Explicit `Sequence` Numbers

Some transactions produce ledger artifacts that explicitly include the sequence number of the transaction. Specifically, those are `Offer` and `Check`.

###### `Offer`s with `Ticket`

`Offer`s are the classic ledger type that incorporates a `Sequence` field. The `Sequence` of the transaction is also used to build the index of the `Offer` in the ledger.

If we create an `Offer` using a `Ticket` instead of a `Sequence` what are the consequences? Well, we certainly can't use the `Sequence` to build the `Offer`; the `Sequence` is zero. We'll need to use the `TicketSequence` number.

If we do this will we need to be concerned about creating `Offer`s in the ledger with duplicate ledger indexes? Fortunately no. If you read the earlier description for how `TicketSequence` values are computed you'll see that there is no overlap between valid `Sequence` values and valid `TicketSequence` values for a given account.

Is there any way that an XRP Ledger user can receive an advantage by creating an `Offer` with a `Sequence` number that is earlier than an `Offer` they created before? First, how could that happen?

1. Anne creates a `Ticket` with `TicketSequence` 3.
1. Anne creates an `Offer` with `Sequence` 4.
1. Anne creates an `Offer` using the `Ticket` she previously created. That `Ticket` has `TicketSequence` 3. So this newest `Offer` has a `Sequence` of 3, which came from the `Ticket`.

In this example Anne's most recently created `Offer` has a `Sequence` of 3, which precedes an older `Offer` with `Sequence` 4.

Now that we understand how it can happen, is there any advantage to be gained from it? As far as I can tell, no. An `Offer` has value based on where it is located in its Book. Each Book for a currency pair is separated into sections. Each section of that Book contains `Offer`s of exactly the same quality. When a new `Offer` is added to the Book, that `Offer` is appended to the other `Offer`s in that section. So, even though the `Offer` has an earlier `Sequence` number, the position of the `Offer` in the Book is unaffected.

###### `Check`s with `Ticket`

The same thought process we followed for `Offer`s with `Ticket`s applies to `Check`s with `Ticket`s. Building a `Check` using a `TicketSequence` number in place of a `Sequence` number cannot lead to duplicate ledger indices for `Check`s. And there is absolutely no advantage to be gained by creating `Check`s out of `Sequence` order.

##### Ledger Artifacts With Implicit `Sequence` Numbers

There are also two ledger artifacts that use the `Sequence` when constructing their ledger indices, but they do not store the `Sequence` number in the ledger object. Those two ledger objects are `Escrow` and `PayChan`. These two ledger types have the same concerns as `Offer`s in terms of uniqueness. The answer to uniqueness concerns is also the same as for `Offer`s. Since there is no overlap between an account's `Sequence` and `TicketSequence` values, the transaction's `TicketSequence` could not have been used to previously create an `Escrow` or a `PayChan`. So using the `TicketSequence` number in place of the `Sequence` for the `Escrow` or `PayChan` cannot lead to duplicate ledger indices.

#### Transaction Ordering

There are two places where unfinished transactions are sorted. They are:

1. **Transaction processing.** When transactions are applied to a final ledger they are applied in a canonical order. Every node on the network must use this same ordering so the nodes agree on the ledgers they construct. If someone can game that ordering there's the potential for someone to make money by gaming the system. We should avoid situations where people can game the system.
1. **Transaction queuing.** Independent of transaction processing, if a transaction does not make it into the ledger on its first attempt, that transaction is queued. The transaction queue (`TxQ`) sorts its queued transactions in order based on a number of considerations. Those considerations include the transaction fee, the account number, and the `Sequence` number of the transaction.

The ordering of transactions might be a place where someone gains advantage by moving one transaction in front of another. So we'll need to think about the rules for sequencing transactions that contain `TicketSequence`s interspersed with transactions that contain `Sequence` numbers.

##### Application to the Ledger

Currently transactions are applied to the ledger in a sorted order (for the detail oriented, the `CanonicalTxSet` does this sorting). This sort order is applied before transactions are actually accepted into the ledger. So the sorting must allow for the possibility of two transactions having the same `Sequence` number or the same `TicketSequence`. If that occurs then only one transaction with a given `Sequence` number or `TicketSequence` is actually accepted into the ledger. But since we are dealing with transactions that are not yet validated, we must be ready for these kinds of things to occur.

The sort order is currently determined by comparing two transactions this way:

1. The smaller account ID goes in front. If the account IDs are equal, then...
1. The smaller `Sequence` number goes in front. If the `Sequence` numbers are equal, then...
1. The smaller transaction ID goes in front. There should never be equal transaction IDs.

This comparison methodology is insufficient once we can submit a transaction using a `Ticket`. For one thing, since the `Sequence` for a transaction with a `Ticket` is zero, transactions with `Ticket`s would always be sorted to the front and then sorted by transaction ID.

There are a variety of sort orders which take `TicketSequence` into account that could be used. The one we ended up with sorts transactions with `Tickets` _behind_ all transactions with `Sequence` numbers for a given account. How we ended up with this sort order is mostly a historical accident. But it's an easy sort order to understand and it is working well. So there's no motivation to change the sort order at this point.

Here's the transaction sorting order with `TicketSequences` taken into account:

1. The smaller account ID goes in front. If the account IDs are equal, then...
1. The smaller non-zero `Sequence` number goes in front. Zero `Sequence` numbers go to the back. If the `Sequence` numbers are equal, then...
1. If both transactions have `TicketSequence`s then the `TicketSequence` with the smaller number goes to the front. If either transaction
   has no `TicketSequence` or if the `TicketSequence` numbers are the same, then...
1. The smaller transaction ID goes in front. There should never be equal transaction IDs.

##### `TxQ` Transaction Ordering

The `TxQ` also keeps ordered lists of transactions. Actually, it keeps two distinct kinds of lists. One list is of all transactions by `FeeLevel`. (`FeeLevel` is similar to the ratio of the actual fee paid to the minimum fee that would allow the transaction into a non-busy ledger.) This particular list ignores account IDs and `Sequence` numbers. So `Ticket`s will have very little impact in this list.

However the `TxQ` keeps another kind of list as well. For every `AccountID` stored in the `TxQ` there's a sorted list of the transactions queued for that account. These lists are currently sorted by `Sequence`. So with `Ticket`s these lists need the same sort order as the `CanonicalTxSet`.

##### Possible Ordering Consequences

Both of these sort orders (`TxQ` and `CanonicalTxSet`) leave open the possibility that games could be played by doing a late insertion of a transaction in front of a transaction that was already posted (but is not yet in a validated ledger).

Here are two different ways this reordering could happen:

1. Inserting in front by selective use of `Ticket`s:
   1. Abril creates a wad of `Ticket`s on her account.
   1. She submits a transaction using a high numbered `TicketSequence`.
   1. She submits a second transaction with a lower numbered `TicketSequence`.
   1. As long as neither transaction has been validated, the second transaction she submitted will be sorted in front of the earlier transaction.
1. Inserting in front by selective use of `Sequence` numbers and `Ticket`s:
   1. Vita creates a few `Ticket`s on her account.
   1. She submits a transaction using a `TicketSequence`.
   1. She submits a second transaction using a (plain) `Sequence` number.
   1. As long as neither transaction has been validated, the second transaction she submitted (the one with the `Sequence` number) will be sorted in front of the earlier transaction (with the `TicketSequence`).

I'm not convinced that we need to worry about this kind of reordering.

- Any reordering that does happen is limited to the account that owns the `Ticket`(s).
- The `TxQ` already allows the account owner to replace one transaction with another by re-issuing a transaction with the same sequence but a higher fee. To the best of our current knowledge this is not being used to manipulate the ledger.

Someone who's more clever with possible ledger manipulations may have ideas for how this kind of reordering could be abused. If so I'm all ears.

##### Identifying Transactions That Can Never Complete

Both of these queuing mechanisms, the `TxQ` and `CanonicalTxSet`, want to solve the problem of identifying transactions that can never succeed. Any transaction that can never succeed should simply be thrown out rather than re-queued. Is there any way to accomplish this with `Tickets`?

Fortunately, yes. By looking at the `Sequence` field of the account root we can determine if a transaction with a `Ticket` can never succeed. `Ticket`s are created in `Sequence` order, but with potential gaps. This means that:

1. If a transaction uses a `Ticket` and
1. The transaction's account root `Sequence` is past the `TicketSequence` number, and
1. The `Ticket` is not in the ledger, then
   1. The `Ticket` was created and already consumed or
   1. The `Ticket` never was (and can never be) created.
1. At any rate, that `Ticket` can never become available for this transaction, so the transaction can never succeed.

So the rule is just a bit more complicated than the rule we currently have with `Sequence` numbers.

Similarly, if a transaction uses a `TicketSequence` with a number that is equal to or higher than the account root `Sequence` field, then it is a transaction from the future. We can retry that transaction a few times (on upcoming ledgers) to see if that `Ticket` ever gets created. But the retry will be local to the machine where the transaction was submitted. The transaction will not be forwarded to the network unless the `Ticket` is actually seen in the local ledger.

#### `Ticket`s and `tec` Errors

A transaction that consumes a `Ticket` has some interesting new behaviors if the validated transaction generates a `tec` error code.

Usually a transaction that generates a `tec` has small but important interactions with the ledger:

- The transaction's fee is removed from the account root.
- The account root's `Sequence` number is advanced by 1.

There is one `tec` code (`tecOVERSIZE`) that has more impact on the ledger; it also removes a collection of unfunded and expired offers. But, under ordinary circumstances, a transaction that generates a `tec` code does not change the ledger very much.

Note that one of the things a `tec` code always does is advance the account root `Sequence` number. However, if the transaction generating the `tec` is also consuming a `Ticket` we can't follow that path. Instead we remove the `Ticket` that was in the transaction from the ledger. The account root `Sequence` does not change.

This is not a big change, but it's worth drawing people's attention to the change so they can think about it.

#### `Ticket`s and the `AccountTxnID` Field

The `AccountTxnID` field allows you to chain your transactions together as documented here: https://xrpl.org/transaction-common-fields.html#accounttxnid. A transaction that specifies an `AccountTxnID` field is only valid if the specified transaction ID matches the transaction that was last sent by the account.

`Ticket`s on the other hand are intended to remove restrictions on transaction ordering.

Combining these two features makes it very difficult for the TxQ to predict whether a transaction is likely to succeed.

Therefore the initial implementation for `Ticket`s does not allow a transaction that uses a `TicketSequence` to also include an `AccountTxnID` field. Such a transaction is rejected with `temINVALID`. If we find a crying need for such a feature in the future, then we can figure out how to implement it well.

#### The Transaction Database and Indices

One of the SQLite databases that rippled keeps is called the Transaction database. As you might expect, that database stores transactions in a table. It also keeps several indices that make it easier to locate transactions in that database. The Transaction database looks like this:

```
    TABLE Transactions (
        TransID CHARACTER(64) PRIMARY KEY,
        TransType CHARACTER(24),
        FromAcct CHARACTER(35),
        FromSeq BIGINT UNSIGNED,
        LedgerSeq BIGINT UNSIGNED,
        Status CHARACTER(1),
        RawTxn BLOB,
        TxnMeta BLOB
    );

    INDEX TxLgrIndex ON
        Transactions(LedgerSeq);",

    TABLE AccountTransactions (
        TransID CHARACTER(64),
        Account CHARACTER(64),
        LedgerSeq BIGINT UNSIGNED,
        TxnSeq INTEGER
    );

    INDEX AcctTxIDIndex ON
        AccountTransactions(TransID);

    INDEX AcctTxIndex ON
        AccountTransactions(Account, LedgerSeq, TxnSeq, TransID);

    INDEX AcctLgrIndex ON
        AccountTransactions(LedgerSeq, Account, TransID);
```

The transaction's `Sequence` number shows up in the top-most `Transactions` table as the `FromSeq` field. But it makes no additional showing in any of the other tables or indexes. Note that it's easy to get confused by the `TxnSeq` fields in the other tables and indices. But the `TxnSeq` field is not the `Sequence` number that is embedded in the transaction. `TxnSeq` carries the order of transaction application within one ledger – a much different thing.

We spent some time examining these tables and came to the conclusion that they do not need any modifications to take `Ticket`s into account.

The strongest evidence that the `Ticket` would need to be present in the tables or indices would be if the transaction `Sequence` field (`FromSeq`) had a strong present there. Although `FromSeq` is present at the top-most level of the Transactions table, none of the other indices reference `FromSeq`.

There are currently two standard methodologies to extract the transactions associated with an account from the `Transactions` database table. Neither of those methodologies rely on the transaction `Sequence`. The methodologies are:

1. **The account_tx rpc command.** This command uses the `AccountTransactions` table. The technique is to examine consecutive ledgers by `LedgerSeq` looking for `Account` and saving the corresponding `TransID`. Those results are then placed in order first by `LedgerSeq` and then by `TxnSeq`. `TxnSeq` is the order in which transactions were placed in the ledger, not the `Sequence` number in the transaction. The order in which all transactions were applied to a ledger must also be the order in which any given account's transactions were applied.
1. **Account threading using the `PreviousTxnID` field of the account root.** By using the `PreviousTxnID` field and walking backwards through transactions using the `tx` RPC command you can request the last transaction that modified the account. By looking in the metadata of that transaction you can locate the previous value of the `PreviousTxnID` field. You can follow this chain until you run out of history or the account root is created.

Since neither of these methodologies rely on the transaction's `Sequence` number, they won't be made more efficient by adding `Ticket` information to the database. We have also worked with the Data team to see if they have any dependency on the `FromSeq` field (which might indicate a need for `TicketSequence` information in the table). No dependencies on `FromSeq` were identified by the Data team.

## Roads Not Taken

The Tickets proposal has been around for a while. Here are some additional features that have been considered and are _not_ part of the current implementation.

### Ticket Targets

The original Tickets proposal allowed an account to create a `Ticket` with a `Target`. The `Target` would be an account ID that is different from the account creating the `Ticket`. A `Ticket` with a `Target` could be consumed by either the account that created the `Ticket` or by the `Target` account.

The goal was to have one account that would only be used to produce `Ticket`s for an organization. Then those `Ticket`s could be assigned, using `Target`, to whatever accounts needed them.

However consider this scenario:

1. Bucky creates a `Ticket` with Cap's account as the `Target`. Bucky's account is at `Sequence` 5, so the `Ticket` is assigned 5.
1. In the mean time, Cap's account is also at `Sequence` 5. Cap creates an Offer on his account using `Sequence` 5. Cap's offer goes in the ledger.
1. Bucky tells his pal Cap that the `Ticket` is available.
1. Cap uses that `Ticket` to create another `Offer`. This new `Offer` also has `Sequence` 5, since that is the number on the `Ticket`.
1. If we take this to its logical conclusion, then Cap has two different `Offer`s in the ledger with identical ledger indices: the `Offer` he made with the `Sequence` and the `Offer` he made with the `Ticket`.

If including the `Target` were really important there would probably be ways of working around this difficulty. But any solution would impact the way that `Offer`, `Check`, `Escrow`, and `PayChan` ledger indices are calculated. That would be a very invasive change. We should think very hard before deciding to make that kind of change to the ledger.

### Ticket Expiration

When `Ticket`s had `Target`s, it was thought that it might be useful to give a `Ticket` an optional `Expiration`, similar to `Offer`s. However, at the moment, a `Ticket` can only be used by the account owning that particular `Ticket`. So there seems to be very little value in giving an `Expiration` to a `Ticket`.

### Ticket Cancel Transactions

When `Ticket`s had an `Expiration` field it was thought that a `TicketCancel` transaction would be necessary. Otherwise how could an expired `Ticket` be removed from the ledger? However since `Ticket`s, in this proposal, do not expire then `TicketCancel` transactions no longer fill a useful role. So `TicketCancel` is no longer proposed. If a `Ticket` needs to be removed from the ledger it can be consumed by any transaction on its account like, for example, a noop. See https://xrpl.org/about-canceling-a-transaction.html.

### Special Handling for Account Root Sequence Jumps

One of the features of the XRP Ledger is that the full transaction history of an account can be reconstructed. Prior to `Ticket`s if you found the transactions for every `Sequence` number on an account, then you know you have every transaction and you also know the order in which those transactions were applied to the ledger. With `Ticket`s things get more complicated.

The transaction metadata still contains the full story. But you can't simply look at the `Sequence` number.

- If the account root `Sequence` number does not change between two transactions, then the metadata will show a `Ticket` node being deleted.
- If the account root `Sequence` number leaps between transactions, then the metadata will show as many `Ticket`s being created as the size of the `Sequence` number leap.

If folks decide that digging around in metadata looking for `Ticket`s being created or deleted is too messy we could choose to add artifacts to the account root to annotate the change. Such account root additions would be purely to help external tools understand chains of transactions.

For a straw man, let's propose that we add two new optional fields in the account root:

- `SubSequence`, and
- `JumpSequence`.

`SubSequence` would work as follows:

1. We'd add a new optional account root entry called `SubSequence`, it would be 32-bit unsigned.
1. When we execute a transaction with a normal `Sequence` number, we remove the `SubSequence` field, if present.
1. When we execute a transaction with a `Ticket`:
   1. If no `SubSequence` field exists in the account root, we create one and set it to 1.
   1. If a `SubSequence` field exists in the account root, we increment it.

This will cause the metadata in the account root of the transaction to indicate whether the prior transaction was a ticketed one or not. And it doesn't (in general) tend to make the ledger larger since the `SubSequence` field is removed once we're done with it.

The `SubSequence` field would be sufficient to deal with the presence of `Tickets` in transactions. But it would not be sufficient to cover batch creation of `Tickets`. We would need yet another account root field to indicate that the `Sequence` number had taken a leap. For that we could consider adding an optional `JumpSeq` field to the account root. Its rules would be:

1. We'd add a new optional account root entry called `JumpSequence`, it would be 32-bit unsigned.
1. When we execute any transaction other than `TicketCreate` then we remove the `JumpSequence` field if it is present.
1. When we execute a `TicketCreate` transaction:
   1. If no `JumpSequence` field exists in the account root, we create one and set it to the count.
   1. If a `JumpSequence` field already exists in the account root, set it to the count.

We have seen no evidence that tools outside the XRP Ledger need this kind of information. So the additional fields are not being added.

### TicketSignerQuorum

As noted earlier, it requires the full complement of multisigners to construct a valid `TicketCreate` transaction. It has been suggested that this pain could be reduced by adding an optional `TicketSignerQuorum` field to the `SignerList`.

For those unfamiliar with multisigning in the XRP Ledger, an account is made multisigning by adding a `SignerList` to that account using the `SignerListSet` transaction. Each `SignerList` consists of one to eight signers, where each signer has a `SignerWeight` and the entire list has a `SignerQuorum`. For a transaction to be validly multisigned it does not need all signers, it only needs enough signers so that the sum of their `SignerWeight`s meets or exceeds the `SignerQuorum`.

By providing a `TicketSignerQuorum`, and having that value be smaller than the regular `SignerQuorum`, the creator of the `SignerList` would allow a `TicketCreate` transaction to require fewer signers. In fact, they could meet the `Ticket` creation quorum with a single (multisigned) signature if they set the `TicketSignerQuorum` to one. A `SignerListSet` transaction which set the `TicketSignerQuorum` larger than the `SignerQuorum` would be malformed.

The `TicketSignerQuorum` value would be a one-trick pony. The only time the `TicketSignerQuorum` would be checked would be on `TicketCreate` transactions. In all other cases the regular `SignerQuorum` would be checked.

This feature has not been added. Once `Ticket`s are in active use on the network we may find that this would be a desirable feature. If so, we can add it at that later time.

## New Attack Vectors

The point of `Ticket`s is to allow execution of transactions out of order. That, in turn opens up some vulnerabilities in the ledger. Here's what has been identified so far:

### Submit Order is not Canonical

Prior to `Ticket`s all transactions on a single account had to be submitted to the ledger in canonical order. With `Ticket`s you can submit a transaction with `TicketSequence` 5 followed by `TicketSequence` 4. If they are submitted quickly enough they will probably both go into the same ledger. They will be applied to the ledger in canonical order (4 followed by 5). Suppose that `Ticket`s 4 and 5 are already in the ledger and the following transactions are submitted:

```
Submit Order:
    AccountSet    signed with current  Regular Key and uses Ticket 5
    SetRegularKey replaces             Regular Key and uses Ticket 4

Applied To Ledger (Canonical Order):
    SetRegularKey replaces             Regular Key and uses Ticket 4
    AccountSet    signed with replaced Regular Key and uses Ticket 5
```

So the transactions work in submit order. The local rippled tries them in that order when the transactions are initially submitted to the network. Since the transactions both succeed in submit order, the transactions are forwarded to the full network.

The validators apply the transactions in canonical order. In canonical order the `SetRegularKey` is applied to the ledger first. So the `AccountSet` transaction fails; it has the wrong signature. Since the signature is wrong we cannot charge the fee. So the entire network has processed a transaction that is guaranteed to fail and a fee is not charged.

This is really a new version of a preexisting attack. A similar attack can be made by submitting two different transactions on the same account, and using the same `Sequence` number, but to two different rippled client handlers. Both of the transactions are valid, so the two client handlers will individually forward both transactions to the full network. One transaction will win and the other will fail with a `tefPAST_SEQ`. The one that fails is wasted work by the entire network.

### Tickets as Ledger Spam

There are two different kinds of ledger spam:

1. One form of spam is transactions that use up bandwidth and compute power but accomplish very little. The transaction fee is intended to combat this form of spam.
1. The other form of spam is excessive in-ledger storage by an account. The account reserve is intended to combat this form of spam. As an account keeps more objects in ledger, the reserve on that account increases. The account is motivated to reduce the in-ledger storage because they get the reserve back when an object they own is removed.

It is possible to argue that the account reserve is not always effective as a deterrent. Anyone who has a large amount of XRP that doesn't need to be liquid can tie up that liquidity in their reserve. They are not motivated to reduce that reserve until they need the liquidity. In effect they can view their reserve simply as a form of escrow.

This means a hostile or un-caring user with lots of XRP could create millions of `Ticket`s on their account. The entire network must pay the price for such volume in the ledger. So it makes sense to take preemptive steps to avoid this problem.

#### Approaches to Managing Ticket Ledger Spam

Four different approaches to managing this possible ledger spam were explored:

- We could change the `Ticket` storage format so multiple `Ticket`s occupy less space in the ledger.
- We can reduce the number of `Ticket`s that a single `TicketCreate` transaction can produce.
- We can make it more costly (increase the fee) for adding `Ticket`s.
- We can limit the number of `Ticket`s an account is allowed to keep in-ledger.

An extended discussion occurred. The conclusion was to choose limiting the number of `Ticket`s any individual account root can hold.

#### Limiting the Number of `Ticket`s an Account Can Keep In Ledger

For ticket count limiting to be effective, we need to make the number of `Ticket`s an account holds easy to discover. So we added an optional 32-bit `TicketCount` field to the account root. That optional `TicketCount` must be maintained with every Ticket-based operation. With this field the account's `TicketCount` can easily be found by looking in a single central location.

Once we have this `TicketCount` it becomes easy to set an arbitrary cap for the number of `Ticket`s an account can keep in ledger. The cap only needs to be enforced for `TicketCreate` transactions.

The only remaining question is the behavior when a `TicketCreate` would exceed the maximum threshold. The behavior we picked was to start with a threshold of 250 `Ticket`s. If a `TicketCreate` transaction would cause the number of `Ticket`s held by an account to exceed that threshold, then the `TicketCreate` fails with a `tecDIR_FULL` error. If the resulting `TicketCount` is at or below the threshold, then all of the requested `Ticket`s are created. This means, since the maximum number of `Ticket`s one `TicketCreate` can produce is 250, that maximum number can only be created if the account in question has no `Ticket`s.

## Summary

To briefly summarize the current proposal, we have the following new rules.

- An account can create a new ledger artifact: a `Ticket`.
- A `TicketSequence` can be used in place of a `Sequence` number in a transaction.
- A transaction that uses a `TicketSequence` must also include the `Sequence` field, but that `Sequence` field must be set to zero.
- Transactions that use `Ticket`s may be submitted to the network in any order; they are not order constrained like transactions with `Sequence` numbers.
- A transaction that includes both a `TicketSequence` and a non-zero `Sequence` field is malformed.
- A `TicketCreate` transaction can create up to 250 `Ticket`s in a single transaction.
- The maximum number of `Ticket`s that a single account can keep in the ledger is 250.
- Any `TicketCreate` transaction that would take a given account above the limit of 250 `Ticket`s fails with a `tecDIR_FULL`.
- Only the account that created the `Ticket` can use the `Ticket` in a valid transaction.
- Each `Ticket` on an account takes one standard reserve unit on that account.
- A transaction that uses a `Ticket` is not forwarded to the network unless the `Ticket` is present in the local ledger.
- When being applied to the ledger, transactions with `Ticket`s are sorted behind transactions with non-zero `Sequence` numbers.
- When a transaction with a `TicketSequence` is applied to the ledger, with either a `tesSUCCESS` or a `tec` code, that `Ticket` is removed from the ledger.

## FAQ

Q: **Are `Ticket`s required for using the XRP Ledger?**

A: No. `Ticket`s address a specific use case where submitting transactions in a pre-determined order is inconvenient. If you don't have that use case you do not need to know about `Ticket`s.

Q: **How much does a `Ticket` cost?**

A: The fee for the transaction that creates one or more `Ticket`s is the same fee as for other standard transactions. So, for example, multisigning the transaction makes it more expensive than signing with the master key or a regular key. But there are no special or unusual costs associated with the transaction.

In addition to the fee for the transaction, each `Ticket` held by an account increases that account's [reserve](https://xrpl.org/reserves.html#reserves). That reserve is correspondingly reduced when each `Ticket` is consumed.

Q: **How many `Ticket`s can I create in a single transaction?**

A: From 1 to 250. The compute time required for a `CreateTicket` transaction to add 250 `Ticket`s to the ledger is slightly less that the compute time required by a single complicated (3 path) payment. So the compute time to create 250 `Ticket`s has a reasonable bound.

Q: **How many `Ticket`s can I keep in my account?**

A: Up to 250. There has been minor concern about the possibility of (virtually) unlimited `Ticket`s owned by an account as being a form of ledger spam. We are preemptively removing that possibility. If the 250 limit is found to be too restrictive in practical situations then the limit is easy to increase (albeit with an amendment).

Q: **Can I create a `Ticket` on one account and use it in a different account?**

A. No. The `TicketSequence` number that each `Ticket` captures must be one that is associated with the account that creates the `Ticket`. See the [_**Ticket Targets**_](#Ticket-Targets) discussion.

Q: **How do I cancel a `Ticket`?**

A: `Ticket`s cannot be canceled, they must be consumed to be removed. One way to do that would be to associate a `Ticket` with a `NOOP` transaction (an [`AccountSet`](https://xrpl.org/accountset.html#accountset) that changes nothing). Another way to do it would be to use a `Ticket` in a transaction that will generate a `tec` error code.

Since `Ticket`s don't expire we don't foresee a need for an account to remove large numbers of `Ticket`s.

Q: **How can I get a list of the `Ticket`s on my account?**

A: The [`account_objects`](https://xrpl.org/account_objects.html#account_objects) RPC command can be used to list all objects held by an account. Specify `"type": "ticket"` to get only the un-consumed Tickets.

Q: **What happens if I use the same `Ticket` in two different transactions?**

A: Assuming that the `Ticket` is valid, at most one of those two transactions will be accepted into a validated ledger. When the first transaction is validated its `Ticket` is consumed. When the server sees the second transaction, it will note that the transaction is using a `Ticket` that is not in the ledger (since the first transaction consumed it) and could never be created. So the second transaction will fail with a `tef` code and never be forwarded to the network.

Q: **How do I know which `Ticket`s I can use?**

A: The [`account_objects`](https://xrpl.org/account_objects.html#account_objects) RPC command answers only part of this question. It tells you which `Ticket`s are available, in ledger, for use.

However if you have several transactions simultaneously getting signed outside of the ledger, then you must personally take steps to not use the same `Ticket` in two or more of those transactions. If you have responsibility for only one account then tracking is easy; just note the integer value of each `TicketSequence` you use. If you are responsible for several accounts, then you must keep separate lists for each of the accounts.

If several transaction creators are sharing one account, then they need to create a policy for which user can use which `Tickets`. Fixed schemes (e.g., Alice gets even `TicketSequence`s and Bob gets the odd ones) can get out of balance over time. Consider what happens with this policy if Alice writes a lot more transactions than Bob for a prolonged period.

A more sustainable approach for multiple transaction creators is that each party gets an initial set of assigned `Ticket`s. From that point on each party creates `Ticket`s when they need them and uses only `Ticket`s they created. A bit of stewardship is still required in this model. For example, if Bob acquires 230 `Ticket`s, then Alice can create at most 20 `Ticket`s until Bob burns down his supply. People still need to be considerate of their cosigners.

## Appendix A: Specification

### Transactions

#### TicketCreate Creates One Or More New Tickets

##### Parameters

| Field            | Style    | Description                                                                                                           |
| ---------------- | -------- | --------------------------------------------------------------------------------------------------------------------- |
| `Account`        | Required | The account that is adding one or more Tickets.                                                                       |
| `TicketCount`    | Required | The number of Tickets to add to the account.                                                                          |
| `Sequence`       | Required | The Sequence number of the transaction or zero.                                                                       |
| `TicketSequence` | Optional | The `TicketSequence` number to consume for the transaction. The corresponding `Ticket` must already be in the ledger. |

The following example is a `TicketCreate` transaction that creates 250 `Ticket`s and includes 4 multisigners.

```
{
    "Account" : "rDg53Haik2475DJx8bjMDSDPj4VX7htaMd",
    "TicketCount" : 250,
    "Fee" : "70",
    "Flags" : 2147483648,
    "Sequence" : 5143,
    "Signers" : [
      {
        "Signer" : {
          "Account" : "rwSqb8mM4hd7oKTiNWVzvjArgUnF2qYuhW",
          "SigningPubKey" : "EDD5DCA7954DAB...49225E107A15781",
          "TxnSignature" : "E4E23FC9FE7E7D8...B849B250651EB05"
        }
      },
      {
        "Signer" : {
          "Account" : "rBfCNiAc4rvrhLEm71j9kwLoScAStMpbf3",
          "SigningPubKey" : "EDE71DB591D0A5...DE26745A47DCC7C",
          "TxnSignature" : "A118FFCB7335BCA...524F075E8BEEB0A"
        }
      },
      {
        "Signer" : {
          "Account" : "rLHuMZjp7BeRJu2t8U39y5DemiJuYKo6zV",
          "SigningPubKey" : "03A9A1C13BEE02...0AF8832B1579AB9",
          "TxnSignature" : "3045022100FA0E7...3E293D372418478"
        }
      },
      {
        "Signer" : {
          "Account" : "rPstfVBNeskmior1fDET8429fJYBhRMJNh",
          "SigningPubKey" : "034932968FF101...E696F11314B56F2",
          "TxnSignature" : "3045022100F44F0...4F4F7EC062E55F7"
        }
      }
    ],
    "SigningPubKey" : "",
    "TransactionType" : "TicketCreate",
}
```

##### Restrictions / Validation

- If the Account would end up with more than 250 `Ticket`s in ledger as a consequence of this `TicketCreate`, then the transaction fails with a `tecDIR_FULL`.
- The Account must have sufficient funds to meet the reserve for all requested `Ticket`s. Otherwise `tecINSUFFICIENT_RESERVE` is returned.
- Either all of the requested `Ticket`s are created or none of them are.

##### Who Can Issue

The account to which the `Ticket`(s) will be attached. Any signature that's valid for the account creating the `Ticket`(s) is acceptable.

## Notes

If successful, this transaction increments the issuer's owner count by the number of `Ticket`s created. It inserts tracking entries in the owner directory of the `Account` for each of the created `Ticket`s.

If the `TicketCreate` transaction uses a `Sequence`, then the first created `Ticket` holds as its `TicketSequence` field a value one greater than the `Sequence` number of the transaction.

If the `TicketCreate` transaction uses a `TicketSequence`, then the first created `Ticket` holds as its `TicketSequence` field the value of the account root `Sequence`.

Each subsequent `Ticket` created by the transaction holds as its `TicketSequence` field a value one greater than the previously created `Ticket`.

The final `Sequence` number on the account root after the transaction completes is one greater than the `TicketSequence` value of the last `Ticket` created.

#### Consuming `Ticket`s In Transactions

All transactions associated with an account (i.e., not pseudo-transactions) can use a `TicketSequence` in place of the `Sequence`. Doing this allows the transaction to be submitted to the network in any order and not be blocked by unvalidated transactions with earlier (or later) `TicketSequence` or `Sequence` numbers.

In order to submit a transaction that uses a `Ticket` instead of a `Sequence` you must make the following adjustments to the transaction.

| Field            | Description                                                                                                                               |
| ---------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| `Sequence`       | The `Sequence` field must be present and must contain zero.                                                                               |
| `TicketSequence` | The `TicketSequence` field must be present and contain the `TicketSequence` value of a `Ticket` that is currently owned by the `Account`. |

In order to allow `Ticket`s to be consumed by transactions, all transactions associated with an account allow an optional `TicketSequence` field.

### Ledger Objects

#### New Ledger Type `Ticket` with Identifier `ltTICKET`

A `Ticket` in the ledger has the following fields:

| Field                 | Style    | Description                                                          |
| --------------------- | -------- | -------------------------------------------------------------------- |
| `sfAccount`           | Required | The ID of the account that owns the `Ticket`.                        |
| `sfTicketSequence`    | Required | The `TicketSequence`, an unsigned 32-bit integer.                    |
| `sfOwnerNode`         | Required | The page number for this `Ticket` in the `Ticket` owner's directory. |
| `sfPreviousTxnID`     | Required | Transaction threading support.                                       |
| `sfPreviousTxnLgrSeq` | Required | Transaction threading support.                                       |

#### `Ticket` Indexing Function

```
/** A ticket */
struct ticket_t
{
    Keylet operator()(
    AccountID const& owner,
    std::uint32_t ticketSeq) const
    {
        return { ltTICKET, sha512Half(std::uint16_t(spaceTicket), owner, sequence) };
    }

    Keylet operator()(uint256 const& key) const
    {
        return { ltTICKET, key };
    }
};
```

#### Changes To `AccountRoot`

To track the number of `Ticket`s an account owns, a new unsigned 32-bit optional `TicketCount` field is added to the `AccountRoot`. If an account has one or more `Ticket`s the `TicketCount` is maintained to reflect the total owned. If the number of owned `Ticket`s ever drops to zero, then the (optional) field is removed from the `AccountRoot`.

#### Changes To Amendments

The `Tickets` amendment has been in rippled for as long as there have been amendments. However this proposal introduces significant changes from the partial `Tickets` implementation that has been in place for the past years. In similar situations in the past we have chosen to use a new amendment, rather than use the old amendment name, to introduce the heavily modified feature.

The motivation for using a new amendment name is as follows:

1. The old amendment exists in old versions of the rippled software.
1. Therefore an old version of the software could enable the new amendment and yet not be compatible with the latest version of the feature.

Whereas if we change the amendment name then an old version of the software would not be able to enable the amendment; even partial support is not present in the old version of the software. In this case the old version of the software would become amendment blocked, which is exactly what we want.

Therefore we have a new amendment, `TicketBatch`, to enable the new features.

The preexisting `Tickets` amendment is removed. Even though the `Tickets` amendment has been available for a long time it has never been enabled. Since it was never enabled, removing the amendment will not leave any servers amendment blocked.

### RPC Commands

The following rippled RPC commands have been adjusted to accommodate `Tickets`:

#### `account_objects`

The `account_objects` RPC command is modified to accept `"type": "ticket"` in its arguments. This causes the `account_objects` command to return all of the `Ticket` objects on the account. Tests for tickets in `account_objects` are added.

#### `account_tx`

The `account_tx` RPC command has been be tested with `Ticket`s. It looks like no modifications to that command are required in order to support `Ticket`s.

#### `ledger_data`

The `ledger_data` RPC command accepts an argument `"type"`. (That `"type"` argument is undocumented [here](https://xrpl.org/ledger_data.html#ledger_data), I don't know whether that's intentional.) The command is augmented to support `"type": "ticket"`. This support occurred as a side effect of the fix for `account_objects`. Tests for tickets in `ledger_data` are added.

#### `ledger_entry`

The `ledger_entry` command is modified to return a `Ticket` object specified either as:

- A string containing the `Ticket` index as hexadecimal, or as
- A JSON object containing an `"owner"` and a `"ticket_sequence"` field.

Tests for `Ticket`s in `ledger_entry` are added.

### Sorting, Collating, and Validating Transactions

The following elements are all internal to the rippled software, but are added or changed due to the addition of `Ticket`s.

#### `SeqProxy`

Both the `CanonicalTXSet` and `TxQ` need to solve the problem of putting transactions in order, and the rules are changing with the addition of `Ticket`s. It was beneficial to add a new class that captures both the `Sequence` number and the optional `TicketSequence` value and provides an ordering.

#### `CanonicalTXSet`

The `mSeq` member of the `CanonicalTXSet::Key` type is replaced with a `SeqProxy`. That new member is taken into account in the `Key` comparison operators. That change has spread out to affect users of the `CanonicalTXSet`.

#### `TxQ`

The `TxQ` contains a few `std::map`s that use the transaction's `Sequence` number as the key. Those keys are replaced with a `SeqProxy` object. That change has spread out and affected users of the `TxQ`. Considerable effor was put into making the `TxQ` and `CanonicalTXSet` behave as similarly as possible.

The `TxQ` has the concept of blocker transactions for an account. The `TxQ` considers a transaction to be a blocker if the transaction changes how later transactions on that account can be signed. So, for instance, a `SetRegularKey` transaction is a blocker. The introduction of `Ticket`s affects blocker handling by the `TxQ`.

Prior to the introduction of `Ticket`s the `TxQ` allowed a blocker to follow other transactions in the account's queue. But once the blocker was in place no more transactions could be added for that account. This rule worked well because without `Ticket`s transactions for a single account were always applied in a well known order: each `Sequence` had to immediately follow the preceding `Sequence`. With `Ticket`s that expectation is no longer valid; transactions with `Ticket`s can go into the ledger in any order.

So the rules for how the `TxQ` handles blockers has changed. A blocker can only be added to the queue for an account if:

1. The queue for that account is empty, or
1. The blocking transaction replaces the only transaction in the account's queue.

These rules have the effect that a blocker must always be alone in the account's queue. Then, once the blocker has flushed through to the ledger, that account's queue is again open for general use.

#### `Transactor`

The `Transactor::checkSeq()` method needed to take the presence of `Ticket`s into account. That method has been adjusted and renamed to `checkSeqProxy()`. This method is called during `preclaim`, so it accomplishes many of the requirements noted in [_**Testing for Transaction Validity and Uniqueness**_](#Testing-for-Transaction-Validity-and-Uniqueness).

#### Impact in the SQLite Database

None identified, however tests were added to increase confidence.
