<pre>
  xls: 34
  title: Token-Enabled Escrows and Payment Channels
  description: Amendment to enable Escrows and Payment Channels to use IOU balances in addition to XRP
  author: Richard Holland (@RichardAH), Denis Angell (@dangell7)
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/88
  status: Withdrawn
  withdrawal-reason: Superseded by XLS-85
  category: Ecosystem
  created: 2023-01-23
</pre>

> This proposal, XLS34d, replaces [XLS27d](https://github.com/XRPLF/XRPL-Standards/discussions/72)

# Token-Enabled Escrows and Payment Channels

The proposed amendment to the XRPL protocol, `PaychanAndEscrowForTokens`, would introduce changes to the ledger objects, transactions, and rpc methods to enable `Escrows` and `PayChannels` to use Trustline balances.

## 1. Problem Statement

The XRPL supports several types of on-ledger negotiable Instruments, namely: `Escows`, `PayChannels` and `Checks`. While each of these instruments is implemented as a first-class on-ledger object, only the `Check` object supports the use of Trustline balances. `PayChannels` and `Escrows` support only the native asset XRP. This limitation is a barrier to wider-spread use of these Instruments for reasons including:

- Regulatory compliance.
- Unwillingness to hold a counter-party-free asset (i.e. XRP).
- Volatility and exchange-rate risk.

## 2. Constraints

The amendment has the following constraints:

- Allow `Escrows` to use Trustline balances.
- Allow `PayChannels` to use Trustline balances.
- Allow Issuers to retain freeze and authorization control over their Issued tokens even when they are locked into Instruments.
- Avoid unnecessary multiplication of on-ledger entities.
- Avoid unnecessarily burdening the ledger computationally.

## 3. Implementation

An Instrument can only be created over a Trustline balance if both parties (source and destination):

- Are Authorised to hold the Trustline,
- Do not have a frozen Trustline for the issuer/currency pair, and
- Can ripple the balance through its Issuer.

The destination may not have a Trustline yet. This is not a bar to creating the Instrument provided that a hypothetical Trustline created at the same time the Instrument is created, from the destination account to the Issuer, for the relevant currency, would meet the above requirements.

Settlement of an Instrument (e.g. `EscrowFinish`, `PaymentChannelClaim`) carries the same semantics as crossing an offer: If no Trustline exists on the destination side, then a Trustline with zero limit is created and the tokens (balance) are placed into that line. However creation of a Trustline requires the transaction to be signed by the receiving account (because it creates an on-ledger object and increases the Owner Count and thus the XRP reserve locked by the destination account.)

### 3.1. New Field: `LockedBalance`.

If all or some of the Trustline balance is locked by a `PayChannel` or an `Escrow` then this amount is accounted for in the `LockedBalance` field. The Trustline Balance less the Locked Balance is the user's spendable balance for that asset. This may be zero if the whole balance is locked.

The rules for the LockedBalance field are as follows:

- If there is no LockedBalance on the Trustline then the LockedBalance is zero.
- If a LockedBalance reaches zero on the Trustline then the LockedBalance field is removed from the `RippleState` object and no longer takes up space on the ledger.
- A LockedBalance can never exceed the amount in the `Balance` field.
- A LockedBalance can never represent a negative balance..

For each Instrument (e.g. `Escrow`, `PayChan`) a user holds that locks up some tokens from a Trustline:

- Locking X tokens into the Instrument increases the LockedBalance on the Trustline by X.
- Upon settlement of the Instrument, both the LockedBalance and the Balance of the Trustline are together decremented by the amount of the settlement (and the Balance on the counter-party's Trustline is incremented by the settlement amount, less transaction fees).
- If the Instrument is cancelled in whole or in part, the amount returned to the first party is decremented from the LockedBalance.
- Multiple Instruments acting on the same Trustline accumulate toward the LockedBalance.

### 3.2. New Field: `LockCount`.

The LockCount field on a RippleState ledger object indicates the total number of locks held against the balance of the Trustline. This is always exactly the number of Instruments (e.g. `Escrows`, `PayChannels`) locking a non-zero amount of the Trustline balance. Adding an additional instrument increments the LockCount. Removing an instrument decrements the LockCount.

The LockCount field exists to account for any floating point _dust_ that is left after the final instrument locking a trustline balance is released. If the LockCount reaches zero but the LockBalance is non-zero (typically extrtemely small) then the LockBalance is assumed to be zero, and is thus deleted.

### 3.3. New Field: `TransferRate`.

The TransferRate field on a `PayChannel` or `Escrow` ledger object indicates the current `TransferRate` at which the funds are locked.

The TransferRate is set at the time of instrument creation and is updated on subsequent funding/settlement events.

The TransferRate always favours the instrument holder. If the TransferRate is better than the current transfer rate for the asset, then settlement will occur at the better rate, and visa versa. If the current transfer rate is higher than the TransferRate then the preceding still applies but in the case of a PayChan no further PaymentChannelFund transactions are allowed.

### 3.4. The impact on Trustlines.

It is possible an Issuer causes an Instrument that uses some of their issued tokens to become frozen. They can do this by simply freezing their side of their Trustline with either of the parties to the Instrument. This prevents the Instrument from being resolved or cancelled until the freeze is lifted.

`Escrows` and `PayChannels` in this or any state are a bar to account deletion. Trustlines with LockedBalance (from any source) are also a bar to account deletion.

It is posssible for an Issuer to create a `PayChannel` or `Escrow` using their own token. The settlement of the Instrument follows the same guidlines as above.

## 4. Final Documentation & SDK Changes

&nbsp;

The proposed changes would include modifications to the following ledger objects;

- [`RippleState`](#411-ripplestate-ledger-object)
- [`PayChannel`](#412-paychannel-ledger-object)
- [`Escrow`](#413-escrow-ledger-object)

The propossed changes would include modifications to the following transactions;

- [`PaymentChannelCreate`](#421-paymentchannelcreate-transaction)
- [`PaymentChannelFund`](#422-paymentchannelfund-transaction)
- [`PaymentChannelClaim`](#423-paymentchannelclaim-transaction)
- [`EscrowCreate`](#411-escrowcreate-transaction)

The propossed changes would include modifications to the following rpc methods;

- [`account_lines`](#431-account_lines-method)
- [`account_channels`](#432-account_channels-method)
- [`account_objects`](#433-account_objects-method)
- [`channel_authorize`](#434-channel_authorize-method)
- [`channel_verify`](#435-channel_verify-method)

&nbsp;

## 4.1. Ledger Object Changes

&nbsp;

### 4.1.1. `RippleState` Ledger Object

The following fields would be added to the [`RippleState`](https://xrpl.org/ripplestate.html#ripplestate-fields) Ledger Object;

| Field Name      | JSON Type | Internal Type | Description                                                      |
| --------------- | --------- | ------------- | ---------------------------------------------------------------- |
| `LockCount`     | number    | uint32        | The total number of lock balances on a RippleState ledger object |
| `LockedBalance` | object    | Amount        | The current amount of locked tokens for a specific trustline     |

&nbsp;

### 4.1.2. `PayChannel` Ledger Object

The following fields would be modified on the [`PayChannel`](https://xrpl.org/paychannel.html#paychannel-fields) Ledger Object;

| Field Name     | JSON Type        | Internal Type | Description                                                                                                                                                                                                                                                                      |
| -------------- | ---------------- | ------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `Amount`       | object or string | Amount        | Total that has been allocated to this channel. This includes amounts that has been paid to the destination address. This is initially set by the transaction that created the channel and can be increased if the source address sends a PaymentChannelFund transaction.         |
| `Balance`      | object or string | Amount        | Total already paid out by the channel. The difference between this value and the Amount field is how much can still be paid to the destination address with PaymentChannelClaim transactions. If the channel closes, the remaining difference is returned to the source address. |
| `TransferRate` | number           | UInt32        | The fee to charge when users make claims on a payment channel, initially set on the creation of a payment channel and updated on subsequent funding or claim transactions.                                                                                                       |

&nbsp;

### 4.1.3. `Escrow` Ledger Object

The following fields would be modified on the [`Escrow`](https://xrpl.org/escrow-object.html#escrow-fields) Ledger Object;

| Field Name     | JSON Type        | Internal Type | Description                                                                                                                                       |
| -------------- | ---------------- | ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| `Amount`       | object or string | Amount        | The amount to be delivered by the held payment.                                                                                                   |
| `TransferRate` | number           | UInt32        | The fee to charge when users finish an escrow, initially set on the creation of an escrow contract, and updated on subsequent finish transactions |

&nbsp;

## 4.2. Transaction Changes

&nbsp;

### 4.2.1. `PaymentChannelCreate` transaction

The following fields would be modified on the [`PaymentChannelCreate`](https://xrpl.org/paymentchannelcreate.html#paymentchannelcreate-fields) transaction;

| Field Name | Required? | JSON Type        | Internal Type | Description                                                                                                                                                                                                                                        |
| ---------- | --------- | ---------------- | ------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `Amount`   | Yes       | object or string | Amount        | Amount to deduct from the sender's balance and set aside in this channel. While the channel is open, the amount can only go to the Destination address. When the channel closes, any unclaimed amount is returned to the source address's balance. |

&nbsp;

### 4.2.2. `PaymentChannelFund` transaction

The following fields would be modified on the [`PaymentChannelFund`](https://xrpl.org/paymentchannelfund.html#paymentchannelfund-fields) transaction;

| Field Name | Required? | JSON Type        | Internal Type | Description                                              |
| ---------- | --------- | ---------------- | ------------- | -------------------------------------------------------- |
| `Amount`   | Yes       | object or string | Amount        | Amount to add to the channel. Must be a positive amount. |

&nbsp;

### 4.2.3. `PaymentChannelClaim` transaction

The following fields would be modified on the [`PaymentChannelClaim`](https://xrpl.org/paymentchannelclaim.html#paymentchannelclaim-fields) transaction;

| Field Name | Required? | JSON Type        | Internal Type | Description                                                                                                                                                                                                                                                                |
| ---------- | --------- | ---------------- | ------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `Balance`  | No        | object or string | Amount        | Total amount delivered by this channel after processing this claim. Required to deliver amount. Must be more than the total amount delivered by the channel so far, but not greater than the Amount of the signed claim. Must be provided except when closing the channel. |
| `Amount`   | No        | object or string | Amount        | The amount authorized by the Signature. This must match the amount in the signed message. This is the cumulative amount that can be dispensed by the channel, including amounts previously redeemed.                                                                       |

&nbsp;

### 4.2.4. `EscrowCreate` transaction

The following fields would be modified on the [`EscrowCreate`](https://xrpl.org/escrowcreate.html#escrowcreate-fields) transaction;

| Field Name | Required? | JSON Type        | Internal Type | Description                                                                                                                                                                                                    |
| ---------- | --------- | ---------------- | ------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `Amount`   | No        | object or string | Amount        | Amount to deduct from the sender's balance and escrow. Once escrowed, the amount can either go to the Destination address (after the FinishAfter time) or returned to the sender (after the CancelAfter time). |

&nbsp;

## 4.3. RPC Method Changes

&nbsp;

### 4.3.1. `account_lines` method

Each `RippleState` Object has the following field added to the [`account_lines`](https://xrpl.org/account_lines.html#response-format) method:

| Field           | Type   | Internal Type | Description                                                       |
| --------------- | ------ | ------------- | ----------------------------------------------------------------- |
| `LockedBalance` | object | Amount        | The total amount locked in payment channels or escrow.            |
| `LockCount`     | number | uint32        | The total number of lock balances on a RippleState ledger object. |

&nbsp;

### 4.3.2. `account_channels` method

Each `PayChannel` Object has the following fields updated on the [`account_channels`](https://xrpl.org/account_channels.html#response-format) method:

| Field          | Type             | Internal Type | Description                                                                                                                                                                |
| -------------- | ---------------- | ------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `Amount`       | object or string | Amount        | The total amount allocated to this channel.                                                                                                                                |
| `Balance`      | object or string | Amount        | The total amount paid out from this channel, as of the ledger version used. (You can calculate the amount left in the channel by subtracting balance from amount.          |
| `TransferRate` | number           | UInt32        | The fee to charge when users make claims on a payment channel, initially set on the creation of a payment channel and updated on subsequent funding or claim transactions. |

&nbsp;

### 4.3.3. `account_objects` method

Each `Escrow` Object has the following fields updated on the [`account_objects`](https://xrpl.org/account_objects.html#response-format) method:

| Field          | Type             | Internal Type | Description                                                                                                                                       |
| -------------- | ---------------- | ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| `Amount`       | object or string | Amount        | The amount to be delivered by the held payment.                                                                                                   |
| `TransferRate` | number           | UInt32        | The fee to charge when users finish an escrow, initially set on the creation of an escrow contract, and updated on subsequent finish transactions |

&nbsp;

### 4.3.4. `channel_authorize` method

The request includes the following updated fields for the [`channel_authorize`](https://xrpl.org/channel_authorize.html#request-format) method:

| Field    | Required? | Type             | Internal Type | Description                                                                                                                                                                         |
| -------- | --------- | ---------------- | ------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `Amount` | Yes       | object or string | Amount        | Cumulative amount to authorize. If the destination has already received a lesser amount from this channel, the signature created by this method can be redeemed for the difference. |

&nbsp;

### 4.3.5. `channel_verify` method

The request includes the following updated fields for the [`channel_verify`](https://xrpl.org/channel_verify.html#request-format) method:

| Field    | Required? | Type             | Internal Type | Description                                   |
| -------- | --------- | ---------------- | ------------- | --------------------------------------------- |
| `Amount` | Yes       | object or string | Amount        | The amount the provided signature authorizes. |

&nbsp;
