<pre>
  xls: 76
  title: Min Incoming Amount
  description: Allow an account holder to specify a minimum amount of XRP that can be received in a Payment
  author: Kris Dangerfield (@xrpl365)
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/219
  created: 2024-08-23
  status: Deprecated
  category: Amendment
</pre>

# XLS-76 - Min Incoming Amount

## Abstract

Based on an original idea by Khaled Elawadi @khaledelawadi, this proposal introduces a new feature to the XRP Ledger that allows an account holder to specify a minimum amount of XRP that can be received.

This feature is designed to prevent what is commonly referred to as "dusting," where small amounts of XRP are sent to an account, potentially cluttering an account with unwanted transactions.

## Rationale

Dusting attacks involve sending tiny amounts of value to a large number of wallets. Currently, XRP Ledger accounts can receive any amount of XRP, regardless of how small. While this might seem harmless, dusting can lead to cluttered transaction histories, potential privacy risks, and significant ledger memo spam.

The Min Incoming Amount feature aims to mitigate these issues by allowing account owners to set a threshold for incoming transactions. Any transaction below the specified minimum amount will be automatically rejected, ensuring that the account only receives transactions of value that meet or exceed the defined threshold.

## Amendment

The proposed change introduces a new field on the `AccountRoot` ledger object called `sfIncomingMin`, which is of type `SF_AMOUNT`.

This field allows users to define the minimum amount of XRP that their account is willing to accept.

## New Field on `AccountRoot`

| Field           | Type   | Required | Description                                                                  |
| :-------------- | :----- | :------- | :--------------------------------------------------------------------------- |
| `sfIncomingMin` | Amount |          | Specifies the minimum amount of XRP (in drops) that the account will accept. |

## Updating the `AccountSet` Transaction

To set, update or remove the `sfIncomingMin` field, users would use the existing `AccountSet` transaction, so it would be updated to store the new field.

Omitting the optional field would do nothing, it would not change any setting that currently exists.

Setting `sfIncomingMin` to zero would remove it from the object, essentially disabling the feature.

#### Failure Conditions

- If amount != XRP amount
- ⁠If amount < 0
- ⁠If incoming min is NOT set and amount is 0

#### State Changes

- Updates the Field `sfIncomingMin` on AccountRoot Ledger Entry.

## Examples

Setting a Minimum Incoming Amount:

```
{
  "TransactionType": "AccountSet",
  "Account": "rExampleAccountID",
  "IncomingMin": "5000000" // 5 XRP in drops
}
```

Removing the Minimum Incoming Amount:

```
{
  "TransactionType": "AccountSet",
  "Account": "rExampleAccountID",
  "IncomingMin": "0" // Removes field from the object and disables the feature
}
```

## Implementation

```
IF Transaction IS Payment
   AND Amount IS "XRP"
   AND DestinationAccount HAS IncomingMin
   AND IncomingMin GREATER THAN Amount
   THEN
   REJECT TRANSACTION
ELSE
   // NORMAL FLOW
END IF
```

## Flows

#### Flow 1: Setting a Minimum Incoming Amount

**Scenario:** Sarah wants to prevent her account from receiving small, insignificant XRP transactions (commonly known as dusting).

1. Sarah performs an AccountSet transaction and sets an IncomingMin of "500000" drops.
2. Sarah's account now has protection against receiving a Payment less than 0.5 XRP.

#### Flow 2: Receiving a Transaction Greater than the Minimum Incoming Amount

**Scenario:** John, unaware of Sarah’s new setting, tries to send her 100 XRP as a token of appreciation.

1. John initiates a payment transaction of 100 XRP from his XRP wallet.
2. The Payment is unaffected by the change Sarah made and the payment is received gratefully.

#### Flow 3: Receiving a Transaction Less than the Minimum Incoming Amount

**Scenario:** "Nasty Nick", a known duster, unaware of Sarah’s new setting, tries to send her 0.00001 XRP, along with a tricky memo.

1. Nick initiates a payment transaction of 0.00001 XRP from his XRP wallet.
2. The Payment is rejected by the ledger when evaluating the incoming Amount vs Sarah's IncomingMin.
3. Sarah's transaction history is unaffected and she never even knew what Nasty Nick tried to do.

#### Flow 4: Removing the Minimum Incoming Amount

**Scenario:** After some time, Sarah decides she no longer needs the minimum incoming amount restriction on her account.

1. Sarah performs an AccountSet transaction and sets an IncomingMin of "0" drops.
2. The IncomingMin field is removed from her Account Root.
3. Sarah's account is no longer protected.

#### Flow 5: Transaction Handling with Min Incoming Amount Set

**Scenario:** "Nasty Nick", is back, and once again he tries to send her 0.00001 XRP, along with a tricky memo.

1. Nick initiates a payment transaction of 0.00001 XRP from his XRP wallet.
2. The Payment is accepted by the ledger because the protection Sarah once had has been removed.
3. Sarah's transaction history now contains a new transaction from Nick, and a bunch of other dusters.

#### Flow 6: Setting a Minimum Incoming Amount with Incorrect Values

**Scenario:** Sarah wants to re-enable the protection on her account, after the nasty surprise from Nick.

1. Sarah performs an AccountSet transaction and sets an IncomingMin of "-500000" drops, an invalid value.
2. The transaction is rejected with an error, and Sarah is informed that the value must be positive.
3. Sarah decides to try again with a correct value - GO TO Flow 1.

## Considerations

**Backward Compatibility**
The addition of the `sfIncomingMin` field will be optional. Accounts that do not set this field will continue to accept all incoming amounts as usual.

**Usability**
The Min Incoming Amount feature is simple to configure and will be integrated seamlessly into existing wallet interfaces using the familiar `AccountSet` transaction type.

**Potential Misuse**
While this feature prevents dusting, users should be cautious about setting the threshold too high, as it might prevent legitimate small transactions from being accepted.

**Partial Payments**
Partial payments allow a sender to specify a maximum amount they are willing to spend, and the transaction delivers as much as possible of the destination amount, potentially less than the full amount specified by the sender. If a partial payment is made and the amount delivered is less than the specified `sfIncomingMin` threshold, this creates an edge-case where the tiny amount may be legitimate, yet be rejected. It makes sense for the `sfIncomingMin` to apply to the actual amount received, as this aligns with the goal of preventing dusting, but means the code will need to use the delivered_amount to prevent partial payments from being used as a work-around to this amendment.

**Effect on Reserves**
If an account's balance marginally drops below the account reserve, this creates an edge-case where the user will not be able to receive a tiny amount as it is blocked by `sfIncomingMin` and being below the account reserve would mean they cannot perform an AccountSet to temporarily remove the limit. The only option would be to receive an amount greater than `sfIncomingMin` which in 99.9% of cases should not be problematic given the it would ideally be set at 1 XRP or less, however in a scenario where the limit was set artificially high...

**Maximum limit**
This spec does not allow for a maximum value on the `sfIncomingMin` field. Adding such a limit may be seen as protecting a user from setting an overly high value, however on balance given the ease at which a limit can be reduced or even removed, it is felt that the arbitrary limit removes user choice.

**Account Locking - Reserve & No Maximum Limit.**
There is an edge case where a user is not prevented from setting a very high limit and the account balance drops below the reserve creating a situation where the account would essentially be rendered unusable. If this edge-case were considered serious enough to require a solution, either a sensible maximum limit could be introduced OR an additional step on transaction rejection to check the account balance is not below the reserve. A maximum amount limit adds very minimal overhead to the amendment but does remove user choice. Testing for account balance would introduce a more intensive test that needs to be applied to every rejected transaction. On balance the arbitrary minimum does offer protection against the ege-case and does not conflict with fundamental principle of the proposal.

## Conclusion

The Min Incoming Amount feature provides a straightforward solution to the problem of dusting on the XRP Ledger.

By introducing the `sfIncomingMin` field on the `AccountRoot` ledger object and utilizing the existing `AccountSet` transaction for configuration, account holders gain the ability to reject small, potentially unwanted transactions.

This enhances account security and reduces clutter, making the XRP Ledger more user-friendly and secure.
