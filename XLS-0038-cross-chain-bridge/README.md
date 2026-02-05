<pre>
  xls: 38
  title: Cross-Chain Bridge
  description: Enabling transfer of value between sidechains through locking and issuing mechanisms
  author: Mayukha Vadari <mvadari@ripple.com>, Scott Determan <scott.determan@ripple.com>
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/92
  status: Final
  category: Amendment
  created: 2023-02-22
</pre>

# Cross-Chain Bridge

## Abstract

A bridge connects two blockchains: a locking chain and an issuing chain (also called a mainchain and a sidechain). Both are independent ledgers, with their own validators and potentially their own custom transactions. Importantly, there is a way to move assets from the locking chain to the issuing chain and a way to return those assets from the issuing chain back to the locking chain: the bridge. This key operation is called a cross-chain transfer. In this proposal, a cross-chain transfer is not a single transaction. It happens on two chains, requires multiple transactions, and involves an additional server type called a "witness".

A bridge does not exchange assets between two ledgers. Instead, it locks assets on one ledger (the "locking chain") and represents those assets with wrapped assets on another chain (the "issuing chain"). A good model to keep in mind is a box with an infinite supply of wrapped assets. Putting an asset from the locking chain into the box will release a wrapped asset onto the issuing chain. Putting a wrapped asset from the issuing chain back into the box will release one of the existing locking chain assets back onto the locking chain. There is no other way to get assets into or out of the box. Note that there is no way for the box to "run out of" wrapped assets - it has an infinite supply.

```
                                            ┌─┐┌─┐┌─┐┌─┐┌─┐
                                            └─┘└─┘└─┘└─┘└─┘
                                               Witnesses
              ┌─────────────────────────┐                      ┌────────────────────────────┐
              │                         │                      │                            │
              │     Locking Chain       │                      │       Issuing Chain        │
              │                         │                      │                            │
              │             Lock XRP    |--------------------->│ Issue wXRP                 │
              │                         │                      │                            │
              │                         │                      │                            │
              │            Unlock XRP   |<---------------------| Return wXRP                │
              │                         │                      │                            │
              └─────────────────────────┘                      └────────────────────────────┘
```

## 1. Introduction

### 1.1. Terminology

- **Bridge**: A method of moving assets from one blockchain to another.
- **Locking chain**: The chain on which the assets originate. An asset is locked on this chain before it can be represented on the issuing chain, and will remain locked while the issuing chain uses the asset.
- **Issuing chain**: The chain on which the assets from the locking chain are wrapped. The issuing chain issues assets that represent assets that are locked on the locking chain.
- **Cross-chain transfer**: A protocol that moves assets from the locking chain to the issuing chain, or returns those assets from the issuing chain back to the locking chain. This generally means that the locking chain locks and unlocks a token, while the issuing chain mints and burns a wrapped version of that token. Usually (but not always), the mainchain will be locking and unlocking a token, and the sidechain will be minting and burning the wrapped version.
- **Source chain**: The chain that a cross-chain transfer begins from. The transfer is from the source chain and to the destination chain.
- **Destination chain**: The chain that a cross-chain transfer ends at. The transfer is from the source chain and to the destination chain.
- **Door account**: The account on the locking chain that is used to put assets into trust, or the account on the issuing chain used to issue wrapped assets. The name comes from the idea that a door is used to move from one room to another and a door account is used to move assets from one chain to another.
- **Attestation**: A message signed by a witness server attesting to a particular event that happened on the other chain. This is used because chains don't talk to each other directly.
- **Witness server**: A server that listens for transactions on one or both of the chains and signs attestations used to prove that certain events happened on a chain.
- **Cross-chain claim ID**: A ledger object used to prove ownership of the funds moved in a cross-chain transfer. This object represents a unique ID for each cross-chain transfer.

### 1.2. The Witness Server

A witness server is an independent server that helps provide proof that an event happened on either the locking chain or the issuing chain. It listens to transactions on one side of the bridge and submits attestations on the other side. This helps affirm that a transaction on the source chain occurred. The witness server is acting as an oracle, providing information to help prove that the assets were moved to the door account on the source chain (to be locked or burned). This then allows the recipient of those assets to claim the equivalent funds on the destination chain.

Since submitting a signature requires submitting a transaction and paying a fee, supporting rewards for signatures is an important requirement. The reward could be higher than the fee, providing an incentive for running a witness server.

### 1.3. Design Overview

This design proposes: 1 new server type, 3 new ledger objects, and 8 new transactions.

The new server type is:

- The witness server

The new ledger objects are:

- `Bridge`
- `XChainOwnedClaimID`
- `XChainOwnedCreateAccountClaimID`

The new transactions are:

- `XChainCreateBridge`
- `XChainModifyBridge`
- `XChainCreateClaimID`
- `XChainCommit`
- `XChainAddClaimAttestation`
- `XChainClaim`
- `XChainAccountCreateCommit`
- `XChainAddAccountCreateAttestation`

#### 1.3.1. A Cross-Chain Transfer

##### 1.3.1.1. Primitives

A cross-chain transfer moves assets from the locking chain to the issuing chain, or returns those assets from the issuing chain back to the locking chain. These transfers need some primitives:

1. Put assets into trust (lock assets) on the locking chain.

2. Issue or mint wrapped assets on the issuing chain.

3. Return or burn the wrapped assets on the issuing chain.

4. On the issuing chain, prove that assets were put into trust on the locking chain.

5. On the locking chain, prove that assets were returned or burned on the issuing chain.

6. A way to prevent the same assets from being wrapped multiple times (prevent transaction replay). The proofs that certain events happened on the different chains are public and can therefore theoretically be submitted multiple times. This must be valid only once to wrap or unlock assets.

##### 1.3.1.2. Process

In this scenario, a user is trying to transfer funds from their account on the source chain to their account on the destination chain.

1.  The user creates a cross-chain claim ID on the destination chain, via the **`XChainCreateClaimID`** transaction. This creates a **`XChainOwnedClaimID`** ledger object. The ledger object must specify the source account on the source chain.
2.  The user submits a **`XChainCommit`** transaction on the source chain, attaching the claimed cross-chain claim ID and including a reward amount (`SignatureReward`) for the witness servers. This locks or burns the asset on the source chain, depending on whether the source chain is a locking or issuing chain. This transaction must be submitted from the same account that was specified when creating the claim ID.
3.  The **witness server** signs an attestation saying that the funds were locked/burned on the source chain. This is then submitted as a **`XChainAddClaimAttestation`** transaction on the destination chain.
4.  When there is a quorum of witness attestations, the funds can be claimed on the destination chain. If a destination account is included in the initial transfer, then the funds automatically transfer when quorum is reached. Otherwise, the user can submit a **`XChainClaim`** transaction for the transferred value on the destination chain.
    - The rewards are then automatically distributed to the witness servers’ accounts on the destination chain.

**![Diagram of a cross-chain transfer](https://user-images.githubusercontent.com/8029314/220456650-fd888ef7-00e5-4a7a-a8bb-5a11865f5f72.png)**

#### 1.3.2. Setting Up a Cross-Chain Bridge

1.  The witness server(s) are spun up.
2.  The bridge is initialized on both of the chains via **`XChainCreateBridge`** transactions sent by the door accounts, which creates a **`Bridge`** ledger object on each chain. Each chain has a **door account** that controls that end of the bridge on-chain. On one chain, currency is locked and unlocked (the **locking chain**). On the other chain, currency is minted and burned, or issued and reclaimed (the **issuing chain**).
    - The `Bridge` ledger object can be modified via the **`XChainModifyBridge`** transaction.
3.  Both chains’ door accounts set up a signer list (via a `SignerListSet` transaction) using the witness servers’ signing keys, so that they control the funds that the bridge controls.
4.  Both chains’ door accounts disable the master key (via an `AccountSet` transaction), so that the witness servers as a collective have total control of the bridge.

#### 1.3.3. Account Creation

Account creation must happen via a different means. This is because the cross-chain transfer process requires an existing account on the destination chain, so if the user does not have an account on the destination chain, they have no way to transfer funds.

1. The user submits a **`XChainAccountCreateCommit`** transaction on the source chain. This locks or burns the asset on the source chain, depending on whether the source chain is a locking or issuing chain.
2. The witness servers each sign their attestations on the destination chain and submit them as **`XChainAddAccountCreateAttestation`** transactions. Since there is no `XChainOwnedClaimID` object on the destination chain to keep track of the attestations, the ledger instead creates a **`XChainOwnedCreateAccountClaimID`** object upon receiving the first attestation.
3. When there is a quorum of witness attestations, the funds are automatically transferred to the new account on the destination chain. The rewards are also automatically distributed to the witness servers’ accounts on the destination chain.

## 2. Changes to the XRPL

### 2.1. On-Ledger Objects

We propose three new objects:

1. A **`Bridge`** is a new object that describes a single cross-chain bridge.

2. A **`XChainOwnedClaimID`** is a new object that describes a single cross-chain claim ID.

3. A **`XChainOwnedCreateAccountClaimID`** is a new object that describes an account to be created on the issuing chain.

#### 2.1.1. The **`Bridge`** object

The **`Bridge`** object represents one end of a cross-chain bridge and holds data associated with the cross-chain bridge. Bridges are created using the **`XChainCreateBridge`** transaction.

The ledger object is owned by the door account and defines the bridge parameters. It is created with a `XChainCreateBridge` transaction, and modified with a `XChainModifyBridge`
transaction (only the `MinAccountCreateAmount` and `SignaturesReward` may be changed). It cannot be deleted. A door account may not own more than one `Bridge` object.

_Note:_ The signatures used to attest to chain events are on the `XChainOwnedClaimID` and `XChainOwnedAccountCreateClaimID` ledger objects, not on this ledger object.

##### 2.1.1.1. Fields

A **`Bridge`** object has the following fields:

| Field Name                 | Required? | JSON Type         | Internal Type   |
| -------------------------- | --------- | ----------------- | --------------- |
| `LedgerIndex`              | ✔️        | `string`          | `HASH256`       |
| `XChainBridge`             | ✔️        | `XChainBridge`    | `XCHAIN_BRIDGE` |
| `SignatureReward`          | ✔️        | `Currency Amount` | `AMOUNT`        |
| `MinAccountCreateAmount`   |           | `Currency Amount` | `AMOUNT`        |
| `XChainAccountCreateCount` | ✔️        | `number`          | `UINT64`        |
| `XChainAccountClaimCount`  | ✔️        | `number`          | `UINT64`        |
| `XChainClaimID`            | ✔️        | `number`          | `UINT64`        |

###### 2.1.1.1.1. `LedgerIndex`

The ledger index is a hash of a unique prefix for a bridge object, the door account for that side of the bridge, and the currency for that side of the bridge. For example, on the locking chain, the ledger index is a hash of the unique prefix for a bridge object, the locking chain door account, and the locking chain currency. The locking chain issuer is not hashed. This intentionally constrains door accounts to at most one bridge per currency type.

###### 2.1.1.1.2. `XChainBridge`

The bridge that this object correlates to - namely, the door accounts and the currencies.

This is the identity of the bridge and cannot be changed, as if it were to change, the object would be representing a different bridge.

It is used everywhere where a `XChainBridge` field exists. This is easier for users instead of expecting them to use the ledger object ID.

| Field Name          | Required? | JSON Type | Internal Type |
| ------------------- | --------- | --------- | ------------- |
| `LockingChainDoor`  | ✔️        | `string`  | `ACCOUNT`     |
| `LockingChainIssue` | ✔️        | `Issue`   | `ISSUE`       |
| `IssuingChainDoor`  | ✔️        | `string`  | `ACCOUNT`     |
| `IssuingChainIssue` | ✔️        | `Issue`   | `ISSUE`       |

**`LockingChainDoor`**

The door account on the locking chain.

**`LockingChainIssue`**

The asset that is locked and unlocked on the locking chain.

**`IssuingChainDoor`**

The door account on the issuing chain. For a XRP-XRP bridge, this must be the genesis account (the account that is created when the network is first started, which contains all of the XRP).

**`IssuingChainIssue`**

The asset that is minted and burned on the issuing chain. For an IOU-IOU bridge, the issuer of the asset must be the door account on the issuing chain, to avoid supply issues.

###### 2.1.1.1.3. `SignatureReward`

The total amount, in XRP, to be rewarded for providing a signature for a cross-chain transfer or for signing for the cross-chain reward. This will be split among the signers.

###### 2.1.1.1.4. `MinAccountCreateAmount`

The minimum amount, in XRP, required for a `XChainAccountCreateCommit` transaction. If this is not present, the `XChainAccountCreateCommit` transaction will fail. This field can only be present on XRP-XRP bridges.

###### 2.1.1.1.5. `XChainAccountCreateCount`

A counter used to order the execution of account create transactions. It is incremented every time a successful `XChainAccountCreateCommit` transaction is run for the source chain.

###### 2.1.1.1.6. `XChainAccountClaimCount`

A counter used to order the execution of account create transactions. It is incremented every time a `XChainAccountCreateCommit` transaction is "claimed" on the destination chain. When the "claim" transaction is run on the destination chain, the `XChainAccountClaimCount` must match the value that the `XChainAccountCreateCount` had at the time the `XChainAccountClaimCount` was run on the source chain. This orders the claims so that they run in the same order that the `XChainAccountCreateCommit` transactions ran on the source chain, to prevent transaction replay.

###### 2.1.1.1.7. `XChainClaimID`

The value of the next `XChainClaimID` to be created.

#### 2.1.2. The **`XChainOwnedClaimID`** object

The `XChainOwnedClaimID` ledger object represents a unique ID for each cross-chain transfer. It must be acquired on the destination chain before submitting a `XChainCommit` on the source chain. Its purpose is to prevent transaction replay attacks and is also used as a place to collect attestations from witness servers.

A `XChainCreateClaimID` transaction is used to create a new `XChainOwnedClaimID`. The ledger object is destroyed when the funds are successfully claimed on the destination chain.

##### 2.1.2.1. Fields

A **`XChainOwnedClaimID`** object may have the following fields:

| Field Name                | Required? | JSON Type         | Internal Type   |
| ------------------------- | --------- | ----------------- | --------------- |
| `LedgerIndex`             | ✔️        | `string`          | `HASH256`       |
| `XChainBridge`            | ✔️        | `XChainBridge`    | `XCHAIN_BRIDGE` |
| `OtherChainSource`        | ✔️        | `string`          | `ACCOUNT`       |
| `SignatureReward`         | ✔️        | `Currency Amount` | `AMOUNT`        |
| `XChainClaimAttestations` | ✔️        | `array`           | `ARRAY`         |
| `XChainClaimID`           | ✔️        | `string`          | `UINT64`        |

###### 2.1.2.1.1. `LedgerIndex`

The ledger index is a hash of a unique prefix for `XChainOwnedClaimID`s, the actual `XChainClaimID` value, and the fields in `XChainBridge`.

###### 2.1.2.1.2. `XChainBridge`

Which bridge the `XChainClaimID` correlates to.

###### 2.1.2.1.3. `OtherChainSource`

The account that must send the corresponding `XChainCommit` on the source chain. The destination may be specified in the `XChainCommit` transaction, which means that if the `OtherChainSource` isn't specified, another account can try to specify a different destination and steal the funds. This also allows tracking only a single set of signatures, since we know which account will send the `XChainCommit` transaction.

###### 2.1.2.1.4. `SignatureReward`

The total amount to pay the witness servers for their signatures. It must be at least the value of `SignatureReward` in the `Bridge` ledger object.

###### 2.1.2.1.5. `XChainClaimAttestations`

Attestations collected from the witness servers. This includes the parameters needed to recreate the message that was signed, including the amount, which chain (locking or issuing), optional destination, and reward account for that signature.

See the `XChainAddClaimAttestation` section for more details on what this looks like.

###### 2.1.2.1.6. `XChainClaimID`

The unique sequence number for a cross-chain transfer.

#### 2.1.3. The **`XChainOwnedCreateAccountClaimID`** object

The `XChainOwnedCreateAccountClaimID` ledger object is used to collect attestations for creating an account via a cross-chain transfer. It is created when a `XChainAddAccountCreateAttestation` transaction adds a signature attesting to a `XChainAccountCreateCommit` transaction and the
`XChainAccountCreateCount` is greater than or equal to the current `XChainAccountClaimCount` on the `Bridge` ledger object. It is destroyed when all the attestations have been received and the funds have transferred to the new account.

##### 2.1.3.1. Fields

A **`XChainOwnedCreateAccountClaimID`** object may have the following fields:

| Field Name                        | Required? | JSON Type      | Internal Type   |
| --------------------------------- | --------- | -------------- | --------------- |
| `LedgerIndex`                     | ✔️        | `string`       | `HASH256`       |
| `XChainBridge`                    | ✔️        | `XChainBridge` | `XCHAIN_BRIDGE` |
| `XChainAccountCreateCount`        | ✔️        | `number`       | `UINT64`        |
| `XChainCreateAccountAttestations` | ✔️        | `array`        | `ARRAY`         |

###### 2.1.3.1.1. `LedgerIndex`

The ledger index is a hash of a unique prefix for `XChainOwnedCreateAccountClaimID`s, the
`XChainAccountCreateCount`, and the fields in `XChainBridge`.

###### 2.1.3.1.2. `XChainBridge`

Door accounts and assets.

###### 2.1.3.1.3. `XChainAccountCreateCount`

An integer that determines the order that accounts created through cross-chain transfers must be performed. Smaller numbers must execute before larger numbers.

###### 2.1.3.1.4. `XChainCreateAccountAttestations`

Attestations collected from the witness servers. This includes the parameters needed to recreate the message that was signed, including the amount, destination, signature reward amount, and reward account for that signature. With the exception of the reward account, all signatures must sign the message created with common parameters.

See the `XChainAddAccountCreateAttestation` section for more details on what this looks like.

### 2.2. Transactions Controlling The Bridge

#### 2.2.1. The **`XChainCreateBridge`** transaction

The **`XChainCreateBridge`** transaction creates a new `Bridge` ledger object. This tells one chain (whichever chain the transaction is submitted on) the details of the bridge.

The transaction must be submitted by the door account. It must also be submitted on both chains that form the bridge in order to be a valid bridge. A door account may own multiple bridge objects, subject to a few constraints.

A bridge object must be owned by either the locking door account or the issuing chain door account. It is an error to try to create both sides of the bridge on the same chain. Doing so will result in a `tecDUPLICATE` error. For example, for a bridge with a locking door account of "Alice" and an issuing door account of "Bob" that locks "USD/gw" and issues "USD/bob", if Alice has already created this bridge, and Bob also tries to create this bridge _on the same chain as Alice_, then Bob's transaction will fail with a `tecDUPLICATE` error. It might appear that this constraint allows an account to try to block bridge creation by creating the other side of bridge accounts themselves. However, this would require them to either have the secret key for the door account or allow them to replay transactions (sidechains should have network ids that prevent transaction replay).

A second constraint is a door can own at most one bridge per currency type. For example, a door account may own a bridge that locks USD/gw and a second bridge that issues EUR/door. However, a door account may not own a bridge that lock USD/gw and a second bridge that issues USD/door. The reason for this constraint is a trust line represents a net balance between two accounts. This can cause the invariant to be violated. Assume the door account that has locked 100USD/gw. Now consider what would happen if a cross chain transaction sent 100USD/door to the gw account. The trust line would have a balance of zero! This would cause future cross chain transactions to fail for lack of funds. To avoid this scenario, the door account may have at most one bridge per currency. This applies to be both the locking and issuing side.

For an IOU-IOU bridge, the issuer of the IOU cannot have the `lsfAllowTrustLineClawback` set. Wrapped funds must always be backed by locked funds and clawback would break that invariant. If the flag is set the transaction will fail with `tecNO_PERMISSION`.

##### 2.2.1.1. Fields

The `XChainCreateBridge` transaction contains the following fields:

| Field Name               | Required? | JSON Type         | Internal Type   |
| ------------------------ | --------- | ----------------- | --------------- |
| `XChainBridge`           | ✔️        | `XChainBridge`    | `XCHAIN_BRIDGE` |
| `SignatureReward`        | ✔️        | `Currency Amount` | `AMOUNT`        |
| `MinAccountCreateAmount` |           | `Currency Amount` | `AMOUNT`        |

###### 2.2.1.1.1. `XChainBridge`

Which bridge (door accounts and issues) to create.

###### 2.2.1.1.2. `SignatureReward`

The signature reward split between the witnesses for submitting attestations.

###### 2.2.1.1.3. `MinAccountCreateAmount`

The minimum amount, in XRP, required for a `XChainAccountCreateCommit` transaction. If this is not present, the `XChainAccountCreateCommit` transaction will fail. This field can only be present on XRP-XRP bridges.

#### 2.2.2. The **`XChainModifyBridge`** transaction

The `XChainModifyBridge` transaction allows bridge managers to modify the parameters of the bridge. They can only change the `SignatureReward` and the `MinAccountCreateAmount`. This is because changing the door accounts or assets would essentially be creating a new bridge as opposed to modifying an existing one.

Note that this is a regular transaction that is sent by the
door account and requires the entities that control the witness servers to coordinate and provide the signatures for this transaction. This coordination happens outside the ledger.

Note that the signer list for the bridge is not modified through this transaction. The signer list is on the door account itself and is changed in the same way signer lists are changed on accounts (via a `SignerListSet` transaction).

##### 2.2.2.1. Fields

The `XChainModifyBridge` transaction contains the following fields:

| Field Name               | Required? | JSON Type         | Internal Type   |
| ------------------------ | --------- | ----------------- | --------------- |
| `XChainBridge`           | ✔️        | `XChainBridge`    | `XCHAIN_BRIDGE` |
| `SignatureReward`        |           | `Currency Amount` | `AMOUNT`        |
| `MinAccountCreateAmount` |           | `Currency Amount` | `AMOUNT`        |
| `Flags`                  | ✔️        | `number`          | `UINT32`        |

###### 2.2.2.1.1. `XChainBridge`

Which bridge (door accounts and issues) to modify.

###### 2.2.2.1.2. `SignatureReward`

The signature reward split between the witnesses for submitting attestations.

###### 2.2.2.1.3. `MinAccountCreateAmount`

The minimum amount, in XRP, required for a `XChainAccountCreateCommit` transaction. If this is not present, the `XChainAccountCreateCommit` transaction will fail. This field can only be present on XRP-XRP bridges.

###### 2.2.2.1.4. `Flags`

Specifies the flags for this transaction. In addition to the universal transaction flags that are applicable to all transactions (e.g., `tfFullyCanonicalSig`), the following transaction-specific flags are defined:

| Flag Name                    | Flag Value   | Description                                        |
| ---------------------------- | ------------ | -------------------------------------------------- |
| `tfClearAccountCreateAmount` | `0x00010000` | Clears the `MinAccountCreateAmount` of the bridge. |

### 2.3. Transactions for Cross-Chain Transfers

#### 2.3.1. The **`XChainCreateClaimID`** transaction

The `XChainCreateClaimID` transaction is the first step in a cross-chain transfer. The claim ID must be created on the destination chain before the `XChainCommit` transaction (which must reference this number) can be sent on the source chain. The account that will send the `XChainCommit` on the source chain must be specified in this transaction (see note on the `OtherChainSource` field in the `XChainOwnedClaimID` ledger object for
justification). The actual claim ID must be retrieved from a validated ledger.

##### 2.3.1.1. Fields

The `XChainCreateClaimID` transaction contains the following fields:

| Field Name         | Required? | JSON Type         | Internal Type   |
| ------------------ | --------- | ----------------- | --------------- |
| `XChainBridge`     | ✔️        | `XChainBridge`    | `XCHAIN_BRIDGE` |
| `SignatureReward`  | ✔️        | `Currency Amount` | `AMOUNT`        |
| `OtherChainSource` | ✔️        | `string`          | `ACCOUNT`       |

###### 2.3.1.1.1. `XChainBridge`

Which bridge to create the `XChainOwnedClaimID` for.

###### 2.3.1.1.2. `SignatureReward`

The amount, in XRP, to be used to reward the witness servers for providing signatures. This must match the amount on the `Bridge` ledger object.

This could be optional, but it is required so the sender can be made positively aware that these funds will be deducted from their account.

###### 2.3.1.1.3. `OtherChainSource`

The account that must send the `XChainCommit` transaction on the source chain.

Since the destination may be specified in the `XChainCommit` transaction, if the `OtherChainSource` wasn't specified, another account could try to specify a different destination and steal the funds.

This also allows us to limit the number of attestations that would be considered valid, since we know which account will send the `XChainCommit` transaction.

#### 2.3.2. The **`XChainCommit`** transaction

The `XChainCommit` transaction is the second step in a cross-chain transfer. It puts assets into trust on the locking chain so that they may be wrapped on the issuing chain, or burns wrapped assets on the issuing chain so that they may be returned on the locking chain.

##### 2.3.2.1. Fields

The `XChainCommit` transaction contains the following fields:

| Field Name              | Required? | JSON Type         | Internal Type   |
| ----------------------- | --------- | ----------------- | --------------- |
| `XChainBridge`          | ✔️        | `XChainBridge`    | `XCHAIN_BRIDGE` |
| `XChainClaimID`         | ✔️        | `string`          | `UINT64`        |
| `Amount`                | ✔️        | `Currency Amount` | `AMOUNT`        |
| `OtherChainDestination` |           | `string`          | `ACCOUNT`       |

###### 2.3.2.1.1. `XChainBridge`

Which bridge to use to transfer funds.

###### 2.3.2.1.2. `XChainClaimID`

The unique integer ID for a cross-chain transfer.

This must be acquired on the destination chain (via a `XChainCreateClaimID` transaction) and checked from a validated ledger before submitting this transaction.

If an incorrect sequence number is specified, the funds will be lost.

###### 2.3.2.1.3. `Amount`

The asset to commit, and the quantity.

This must match the door account's `LockingChainIssue` (if on the locking chain) or the door account's `IssuingChainIssue` (if on the issuing chain).

###### 2.3.2.1.4. `OtherChainDestination`

The destination account on the destination chain.

If this is not specified, the account that submitted the `XChainCreateClaimID` transaction on the destination chain will need to submit a `XChainClaim` transaction to claim the funds.

#### 2.3.3. The **`XChainAddClaimAttestation`** transaction

The `XChainAddClaimAttestation` transaction provides an attestation from a witness server attesting to a `XChainCommit` transaction on the other chain.

The signature must be from one of the keys on the door's signer list at the time the signature was provided. However, if the signature list changes between the time the signature was submitted and the quorum is reached, the new signature set is used and some of the currently collected signatures may be removed. Note that the reward is only sent to accounts that have keys on the current list.

_Note:_ Any account can submit signatures. This is important to support witness servers that work on the "subscription" model (see the `Witness Server` section for more details).

_Note:_ A quorum of signers need to agree on the `SignatureReward`, the same way they need to agree on the other data. A single witness server cannot provide an incorrect value for this in an attempt to collect a larger reward.

##### 2.3.3.1. Fields

The `XChainAddClaimAttestation` transaction contains the following fields:

| Field Name                 | Required? | JSON Type         | Internal Type   |
| -------------------------- | --------- | ----------------- | --------------- |
| `Amount`                   | ✔️        | `Currency Amount` | `AMOUNT`        |
| `AttestationRewardAccount` | ✔️        | `string`          | `ACCOUNT`       |
| `AttestationSignerAccount` | ✔️        | `string`          | `ACCOUNT`       |
| `Destination`              |           | `string`          | `ACCOUNT`       |
| `OtherChainSource`         | ✔️        | `string`          | `ACCOUNT`       |
| `PublicKey`                | ✔️        | `string`          | `BLOB`          |
| `Signature`                | ✔️        | `string`          | `BLOB`          |
| `WasLockingChainSend`      | ✔️        | `number`          | `UINT8`         |
| `XChainBridge`             | ✔️        | `XChainBridge`    | `XCHAIN_BRIDGE` |
| `XChainClaimID`            | ✔️        | `string`          | `UINT64`        |

###### 2.3.3.1.1. `Amount`

The amount committed via the `XChainCommit` transaction on the source chain.

###### 2.3.3.1.2. `AttestationRewardAccount`

The account that should receive this signer's share of the `SignatureReward`.

###### 2.3.3.1.3. `AttestationSignerAccount`

The account on the door account's signer list that is signing the transaction. Normally, the public key would be equivalent to the master key of the account. However, there is also the option of creating the account on the chain and setting a regular key, and using that key to sign attestations on behalf of the signer account.

###### 2.3.3.1.4. `Destination`

The destination account for the funds on the destination chain (taken from the `XChainCommit` transaction).

###### 2.3.3.1.5. `OtherChainSource`

The account on the source chain that submitted the `XChainCommit` transaction that triggered the event associated with the attestation.

###### 2.3.3.1.6. `PublicKey`

The public key used to verify the attestation signature.

###### 2.3.3.1.7. `Signature`

The signature attesting to the event on the other chain.

###### 2.3.3.1.8. `WasLockingChainSend`

A boolean representing the chain where the event occurred.

###### 2.3.3.1.9. `XChainBridge`

The bridge associated with the attestations.

###### 2.3.3.1.10. `XChainClaimID`

The `XChainClaimID` associated with the transfer, which was included in the `XChainCommit` transaction.

##### 2.3.3.2. Implementation Details

To add an attestation to a `XChainOwnedClaimID`, that ledger object must already exist.

#### 2.3.4. The **`XChainClaim`** transaction

The `XChainClaim` transaction allows the user to claim funds on the destination chain from a `XChainCommit` transaction.

This is normally not needed, but may be used to handle transaction failures or if the destination account was not specified in the `XChainCommit` transaction. It may only be used after a quorum of signatures have been sent from the witness servers.

If the transaction succeeds in moving funds, the referenced `XChainOwnedClaimID` ledger object will be destroyed. This prevents transaction replay. If the transaction fails, the `XChainOwnedClaimID` will not be destroyed and the transaction may be re-run with different parameters.

##### 2.3.4.1. Fields

The `XChainClaim` transaction contains the following fields:

| Field Name       | Required? | JSON Type         | Internal Type   |
| ---------------- | --------- | ----------------- | --------------- |
| `XChainBridge`   | ✔️        | `XChainBridge`    | `XCHAIN_BRIDGE` |
| `XChainClaimID`  | ✔️        | `string`          | `UINT64`        |
| `Destination`    | ✔️        | `string`          | `ACCOUNT`       |
| `DestinationTag` |           | `int`             | `UINT32`        |
| `Amount`         | ✔️        | `Currency Amount` | `AMOUNT`        |

###### 2.3.4.1.1. `XChainBridge`

The bridge associated with this transfer.

###### 2.3.4.1.2. `XChainClaimID`

The unique integer ID for a cross-chain transfer that was referenced in the relevant `XChainCommit` transaction.

###### 2.3.4.1.3. `Destination`

The destination account on the destination chain. It must exist or the transaction will fail. However, if the transaction fails in this case, the sequence number and collected signatures will not be destroyed and the transaction may be rerun with a different destination address.

###### 2.3.4.1.4. `DestinationTag`

An integer destination tag.

###### 2.3.4.1.5. `Amount`

The amount to claim on the destination chain.

This must match the amount attested to on the attestations associated with this `XChainClaimID`.

### 2.4. Transactions for Account Creation

Since the cross-chain transfer process requires an existing account on the destination chain, if the user does not have an account on the destination chain, they have no way to transfer funds. With a sidechain, there are no user accounts when the chain is first created. Therefore, account creation requires a special mechanism and special transactions.

#### 2.4.1. The **`XChainAccountCreateCommit`** transaction

The `XChainAccountCreateCommit` transaction is a special transaction used for creating accounts through a cross-chain transfer.

A normal cross-chain transfer requires a `XChainClaimID` (which requires an existing account on the destination chain). One purpose of the `XChainClaimID` is to prevent transaction replay. For this transaction, we use a different mechanism: the accounts must be claimed on the destination chain in the same order that the `XChainAccountCreateCommit` transactions occurred on the source chain.

This transaction can only be used for XRP-XRP bridges.

**IMPORTANT:** This transaction should only be enabled if the witness attestations will be reliably delivered to the destination chain. If the signatures are not delivered, then account creation will be blocked until the one waiting on attestations receives its attestations. This could be used maliciously. To disable this transaction on XRP-XRP bridges, the bridge's `MinAccountCreateAmount` should not be present.

_Note:_ If this account already exists, the XRP is transferred to the existing account. However, note that unlike the `XChainCommit` transaction, there is no error handling mechanism. If the claim transaction fails, there is no mechanism for refunds (except manually, via the witness signing keys on the door accounts' signer list). The funds are essentially permanently lost. This transaction should therefore only be used for account creation.

##### 2.4.1.1. Fields

The `XChainAccountCreateCommit` transaction contains the following fields:

| Field Name        | Required? | JSON Type         | Internal Type   |
| ----------------- | --------- | ----------------- | --------------- |
| `XChainBridge`    | ✔️        | `XChainBridge`    | `XCHAIN_BRIDGE` |
| `SignatureReward` | ✔️        | `Currency Amount` | `AMOUNT`        |
| `Destination`     | ✔️        | `string`          | `ACCOUNT`       |
| `Amount`          | ✔️        | `Currency Amount` | `AMOUNT`        |

###### 2.4.1.1.1. `XChainBridge`

The bridge to use to transfer funds.

###### 2.4.1.1.2. `SignatureReward`

The amount, in XRP, to be used to reward the witness servers for providing signatures.

This must match the amount on the `Bridge` ledger object.

This could be optional, but it is required so the sender can be made positively aware that these funds will be deducted from their account.

###### 2.4.1.1.3. `Amount`

The amount, in XRP, to use for account creation. This must be greater than or equal to the `MinAccountCreateAmount` specified in the `Bridge` ledger object.

###### 2.4.1.1.4. `Destination`

The destination account on the destination chain.

#### 2.4.2. The **`XChainAddAccountCreateAttestation`** transaction

The `XChainAddAccountCreateAttestation` transaction provides an attestation from a witness server attesting to a `XChainAccountCreateCommit` transaction on the other chain.

The signature must be from one of the keys on the door's signer list at the time the signature was provided. However, if the signature list changes between the time the signature was submitted and the quorum is reached, the new signature set is used and some of the currently collected signatures may be removed. Note that the reward is only sent to accounts that have keys on the current list.

_Note:_ Any account can submit signatures. This is important to support witness servers that work on the "subscription" model (see the `Witness Server` section for more details).

_Note:_ A quorum of signers need to agree on the `SignatureReward`, the same way they need to agree on the other data. A single witness server cannot provide an incorrect value for this in an attempt to collect a larger reward.

##### 2.4.2.1. Fields

The `XChainAddAccountCreateAttestation` transaction contains the following fields:

| Field Name                 | Required? | JSON Type         | Internal Type   |
| -------------------------- | --------- | ----------------- | --------------- |
| `Amount`                   | ✔️        | `Currency Amount` | `AMOUNT`        |
| `AttestationRewardAccount` | ✔️        | `string`          | `ACCOUNT`       |
| `AttestationSignerAccount` | ✔️        | `string`          | `ACCOUNT`       |
| `Destination`              | ✔️        | `string`          | `ACCOUNT`       |
| `OtherChainSource`         | ✔️        | `string`          | `ACCOUNT`       |
| `PublicKey`                | ✔️        | `string`          | `BLOB`          |
| `Signature`                | ✔️        | `string`          | `BLOB`          |
| `SignatureReward`          | ✔️        | `Currency Amount` | `AMOUNT`        |
| `WasLockingChainSend`      | ✔️        | `number`          | `UINT8`         |
| `XChainAccountCreateCount` | ✔️        | `string`          | `UINT64`        |
| `XChainBridge`             | ✔️        | `XChainBridge`    | `XCHAIN_BRIDGE` |

###### 2.4.2.1.1. `Amount`

The amount committed via the `XChainAccountCreateCommit` transaction on the source chain.

###### 2.4.2.1.2. `AttestationRewardAccount`

The account that should receive this signer's share of the `SignatureReward`.

###### 2.4.2.1.3. `AttestationSignerAccount`

The account on the door account's signer list that is signing the transaction. Normally, the public key would be equivalent to the master key of the account. However, there is also the option of creating the account on the chain and setting a regular key, and using that key to sign attestations on behalf of the signer account.

###### 2.4.2.1.4. `Destination`

The destination account for the funds on the destination chain.

###### 2.4.2.1.5. `OtherChainSource`

The account on the source chain that submitted the `XChainAccountCreateCommit` transaction that triggered the event associated with the attestation.

###### 2.4.2.1.6. `PublicKey`

The public key used to verify the signature.

###### 2.4.2.1.7. `Signature`

The signature attesting to the event on the other chain.

###### 2.4.2.1.8. `SignatureReward`

The signature reward paid in the `XChainAccountCreateCommit` transaction.

###### 2.4.2.1.9. `WasLockingChainSend`

A boolean representing the chain where the event occurred.

###### 2.4.2.1.10. `XChainAccountCreateCount`

The counter that represents the order that the claims must be processed in.

###### 2.4.2.1.11. `XChainBridge`

The bridge associated with the attestation.

##### 2.4.2.2. Implementation Details

Since `XChainOwnedCreateAccountClaimID` is ordered, it's possible for this object to collect a quorum of signatures but not be able to execute yet. As a result, the witness servers are designed to always deliver attestations in order. Therefore, in practice, this object should not be able to collect a quorum of attestations without being able to execute yet.
However, if this situation should occur (e.g. via a buggy witness server), then the object will not execute yet and another attestation will need to be sent to the object in order to execute it. In this case, it is okay to send an attestation that is already on the object.

## 3. The Witness Server

A witness server helps provide proof that some event happened on either the locking chain or the issuing chain. It does not validate transactions and does not need to coordinate with other witness servers. Instead, it listens to transactions from the chains. When it detects an event of interest on the source chain, it creates an attestation (a signed message) and uses the `XChainAddClaimAttestation` or `XChainAddAccountCreateAttestation` transactions to submit their attestation for the event to the destination chain. When a quorum of signatures are collected on the destination chain, the funds are released.

Since submitting a signature requires submitting a transaction and paying a fee, supporting rewards for signatures is an important requirement. The reward could be higher than the fee, providing an incentive for running a witness server.

It is possible for a witness server to provide attestations for one chain only - and it is possible for the door account on the locking chain to have a different signer's list than the door account on the issuing chain. The initial implementation of the witness server assumes it is providing attestation for both chains, however it is desirable to allow witness servers that only know about one of the chains.

The current design envisions two models for how witness servers are used:

1.  The servers are completely private. They submit transactions to the chains themselves and collect the rewards themselves. Allowing the servers to be private has the advantage of greatly reducing the attack surface on these servers. They won't have to deal with adversarial input to their RPC commands, and since their ip address will be unknown, it will be hard to mount an DOS attack.

2.  The witness server monitors events on a chain, but does not submit their signatures themselves. Instead, another party will pay the witness server for their signature (for example, through a subscription fee), and the witness server allows that party to collect the signer's reward. The account that receives the signature reward is part of the message that the witness server signs.

_Note:_ since submitting a signature requires submitting a transaction and paying a fee, supporting rewards for signatures is an important requirement. Of course, the reward can be higher than the fee, providing an incentive to run a witness server.

### 3.1. The Server Code

The witness server code is currently available [here](https://github.com/seelabs/xbridge_witness). However, the official repo will likely move to the XRPLF Github org if this proposal is accepted.

### 3.2. Witness Configuration

The witness configuration is stored in a file called `witness.json`.

#### 3.2.1. Fields

| Field Name       | Required? | JSON Type      |
| ---------------- | --------- | -------------- |
| `LockingChain`   | ✔️        | `object`       |
| `IssuingChain`   | ✔️        | `object`       |
| `RPCEndpoint`    | ✔️        | `object`       |
| `LogFile`        | ✔️        | `string`       |
| `LogLevel`       | ✔️        | `string`       |
| `DBDir`          | ✔️        | `string`       |
| `SigningKeySeed` | ✔️        | `string`       |
| `SigningKeyType` | ✔️        | `string`       |
| `XChainBridge`   | ✔️        | `XChainBridge` |

##### 3.2.1.1. `LockingChain`

The parameters for interacting with the locking chain.

| Field Name      | Required? | JSON Type |
| --------------- | --------- | --------- |
| `Endpoint`      | ✔️        | `object`  |
| `TxnSubmit`     | ✔️        | `object`  |
| `RewardAccount` | ✔️        | `string`  |

###### 3.2.1.1.1. `Endpoint`

The websocket endpoint of a `rippled` node synced with the locking chain.

The fields are as follows:

| Field Name | Required? | JSON Type |
| ---------- | --------- | --------- |
| `IP`       | ✔️        | `string`  |
| `Port`     | ✔️        | `string`  |

**`IP`**

The IP address of the `rippled` node.

_Note:_ This does not accept URLs right now.

**`Port`**

The port used for the websocket endpoint.

###### 3.2.1.1.2. `TxnSubmit`

The parameters for transaction submission on the locking chain.

| Field Name          | Required? | JSON Type |
| ------------------- | --------- | --------- |
| `ShouldSubmit`      | ✔️        | `boolean` |
| `SigningKeySeed`    |           | `string`  |
| `SigningKeyType`    |           | `string`  |
| `SubmittingAccount` |           | `string`  |

**`ShouldSubmit`**

A boolean indicating whether or not the witness server should submit transactions on the locking chain.

For the subscription model, the witness server should not submit transactions.

**`SigningKeySeed`**

The seed that the witness server should use to sign its transactions on the locking chain. This is required if `ShouldSubmit` is `true`.

**`SigningKeyType`**

The algorithm used to encode the `SigningKeySeed`. The options are `secp256k1` and `ed25519`. This is required if `ShouldSubmit` is `true`.

**`SubmittingAccount`**

The account from which the `XChainAddClaimAttestation` and `XChainAddAccountCreateAttestation` transactions should be sent. This is required if `ShouldSubmit` is `true`.

###### 3.2.1.1.1. `RewardAccount`

The account that should receive the witness's share of the `SignatureReward` on the locking chain.

##### 3.2.1.2. `IssuingChain`

The parameters for interacting with the issuing chain. This is identical to the `LockingChain` section.

##### 3.2.1.3. `RPCEndpoint`

The endpoint for RPC requests to the witness server.

| Field Name | Required? | JSON Type |
| ---------- | --------- | --------- |
| `IP`       | ✔️        | `string`  |
| `Port`     | ✔️        | `string`  |

###### 3.2.1.3.1. `IP`

The IP address for the endpoint.

###### 3.2.1.3.2. `Port`

The port for the endpoint.

##### 3.2.1.4. `LogFile`

The location of the log file.

##### 3.2.1.5. `LogLevel`

The level of logs to store in the log file. The options are `["All", "Trace", "Debug", "Info", "Warning", "Error", "Fatal", "Disabled","None"]`.

##### 3.2.1.6. `DBDir`

The location of the directory where the databases are stored.

##### 3.2.1.7. `SigningKeySeed`

The seed that the witness server should use to sign its attestations.

##### 3.2.1.8. `SigningKeyType`

The algorithm used to encode the `SigningKeySeed`. The options are `secp256k1` and `ed25519`.

##### 3.2.1.9. `XChainBridge`

The bridge that the witness server is monitoring. This is identical to the `XChainBridge` params in every transaction and ledger object.

### 3.3. Running a Witness Server

After downloading and building the code, run:

```
./xbridge_witnessd --conf witness.json
```

Further details are available in the README of the [repo](https://github.com/seelabs/xbridge_witness).

#### 3.3.1. Server Specs

The witness server is pretty lightweight, so it likely doesn't need very high specs. However, this has not been tested.

#### 3.3.2. Best Practices

In a production environment, a witness server should use different keys for each of signing attestations, signing locking chain transactions, and signing issuing chain transactions. This adds security and helps avoid transaction replay attack issues.

## 4. How to Build a Bridge

### 4.1. Setting Up a New Sidechain (AKA Building a XRP-XRP Bridge)

Setting up a new issuing chain with a XRP-XRP bridge is somewhat complex, because there are no accounts on the issuing chain, even for witnesses. As a result, witnesses cannot directly submit `XChainAddClaimAttestation` or `XChainAddAccountCreateAttestation` transactions.

Once the new network is set up and active (in other words, the validators are running and are successfully closing ledgers):

1. Ensure that the witnesses' transaction submission accounts are funded on the locking chain (if applicable).
2. Submit a `XChainCreateBridge` transaction on the locking chain from the door account.
   - This should be done before the `SignerListSet` for ease of setup.
   - The `MinAccountCreateAmount` value should be at minimum the account reserve on the issuing chain.
3. Submit a `SignerListSet` transaction on the locking chain from the door account, with the witnesses' signing keys as the signers.
4. Disable the master key on the locking chain's door account with an `AccountSet` transaction.
5. Submit a `XChainCreateBridge` transaction on the issuing chain from the door account. This door account already exists, since it must be the genesis account.
6. Submit `XChainAccountCreateCommit` transactions from account(s) that have enough funds, to create each of the witnesses' submission accounts on the issuing chain.
7. Create an attestation for each of the account create attestations for the `XChainAccountCreateCommit` transactions in step 6. These attestations should be signed by the genesis seed, since that is currently what controls the genesis account.
   - This could also be done via a witness server set up to not submit transactions, but it is easier to do by hand.
8. Submit a `XChainAddAccountCreateAttestation` transaction for each of the attestations from step 7 on the issuing chain, with the genesis account.
9. Submit a `SignerListSet` transaction on the issuing chain from the door account, with the witnesses' signing keys as the signers.
10. Disable the master key on the issuing chain's door account with an `AccountSet` transaction.

The bridge is now set up and can be used normally.

### 4.2. Building an IOU-IOU Bridge

Any two networks that have an IOU-IOU bridge between them should already have a XRP-XRP bridge between them, as a sidechain will need XRP for account reserves and transaction fees (while this _could_ be changed, in that case the `XChainBridge` amendment code could also be modified). This makes it simpler to set up an IOU-IOU bridge.

To set up an IOU-IOU bridge:

1. Ensure that the witnesses' transaction submission accounts are funded on the locking chain and issuing chain (if applicable).
2. Submit a `XChainCreateBridge` transaction on the locking chain from the door account.
   - This should be done before the `SignerListSet` for ease of setup.
   - The `MinAccountCreateAmount` value should not be included.
3. Submit a `SignerListSet` transaction on the locking chain from the door account, with the witnesses' signing keys as the signers.
4. Disable the master key on the locking chain's door account with an `AccountSet` transaction.
5. Submit a `XChainCreateBridge` transaction on the issuing chain from the door account.
6. Submit a `SignerListSet` transaction on the issuing chain from the door account, with the witnesses' signing keys as the signers.
7. Disable the master key on the issuing chain's door account with an `AccountSet` transaction.

The bridge is now set up and can be used normally.

## 5. Security

### 5.1. Trust Assumptions

The witness servers are trusted, and if a quorum of them collude they can steal funds from the door account.

#### 5.1.1. Use of the Signer List

The public keys that the witness servers use must match the public keys on that door's signer's list. But this isn't the only way to implement this. A bridge ledger object could contain a signer list that's independent from the door account. The reasons for using the door account's signers list are:

1.  The bridge signers list can be used to move funds from the account. Putting this list on the door account emphasizes this trust model.
2.  It allows for emergency action. If something goes very, very wrong, funds could still be moved if the entities on the signer list sign a regular `Payment` transaction.
3.  It's a more natural way to modify bridge parameters.

### 5.2. Transaction Replay Attacks

Normally, account sequence numbers prevent transaction replay on the XRP Ledger. However, this bridge design allows funds to move from an account via transactions not sent by that account (namely, the attestations submitted by the witness servers). All the information to replay these transactions are publicly available. This section describes how the different transactions prevent certain attacks - including transaction replay attacks.

To successfully run a `XChainClaim` transaction, the account sending the transaction must own the `XChainOwnedClaimID` ledger object referenced in the witness server's attestation. Since this ledger object is destroyed when the funds are successfully moved, the transaction cannot be replayed.

To successfully create an account with the `XChainAccountCreateCommit` transaction, the ordering number must match the current order number on the bridge ledger object. After the transaction runs, the order number on the bridge ledger object is incremented. Since this number is incremented, the transaction can not be replayed since the order number in the transaction will never match again.

Since the `XChainCommit` can contain an optional destination account on the destination chain, and the funds will move when the destination chain collects enough signatures, one attack would be for an account to watch for a `XChainCommit` to be sent and then send their own `XChainCommit` for a smaller amount. This attack doesn't steal funds, but it does result in the original sender losing their funds. To prevent this, when a `XChainOwnedClaimID` is created on the destination chain, the account that will send the `XChainCommit` on the source chain must be specified. Only the attestations from this transaction will be accepted on the `XChainOwnedClaimID`.

### 5.3. Error Handling

#### 5.3.1. Error Handling for Cross-Chain Transfers

Error handling for cross-chain transfers is straightforward. The `XChainOwnedClaimID` is only destroyed when a claim succeeds. If it fails for any reason (for example, if the destination account doesn't exist or has deposit auth set), then an explicit `XChainClaim` transaction may be submitted to redirect the funds.

#### 5.3.2. Error Handling for Cross-Chain Account Creates

If a cross-chain account create fails, the recovery of funds must happen outside the rules of the bridge system. The only way to recover them would be if the witness servers created a `Payment` transaction themselves. This is unlikely to happen and should not be relied upon. The `MinAccountCreateAmount` on the `Bridge` object is meant to prevent these transactions from failing due to having too little XRP.

#### 5.3.3. Error Handling for Signature Reward Delivery

If the signature reward cannot be delivered to the specified account, that portion of the signature reward is kept by the account that owns the `XChainOwnedClaimID`.

## 6. Proposed Implementation

A proposed implementation is available here: https://github.com/XRPLF/rippled/pull/4292

An in-development version of a witness server is available here: https://github.com/seelabs/xbridge_witness
