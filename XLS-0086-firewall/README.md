<pre>
  xls: 86
  title: Firewall
  description: Time-based spending limits and whitelist functionality to prevent unauthorized account drainage on the XRPL.
  author: Kris Dangerfield (@krisdangerfield), Denis Angell (@angell_denis)
  status: Draft
  category: Amendment
  created: 2024-11-29
</pre>

# XLS-86d - Firewall

## Abstract

This proposal introduces a new security feature for the XRP Ledger, referred to as the "Firewall."

The proposed Firewall feature allows account owners to configure time-based, value-limited safeguards on outgoing transactions. These restrictions ensure that even if a private key is compromised, an attacker cannot immediately drain the account, giving the owner time to secure their assets. The Firewall will integrate seamlessly with existing transaction flows and is an optional feature that users can enable at their discretion. Additionally, the proposal outlines the creation of a whitelist mechanism, allowing trusted accounts to bypass the firewall restrictions, to strike a balance between security and usability, allowing the feature to be configured so that it does not interfere with genuine day-to-day transactions.

This feature is particularly beneficial for retail users and small enterprises, offering a simpler alternative or complement to multisig protection.

## Rationale

The XRPL protocol currently does not have a native mechanism to prevent a compromised account from being instantly drained by an attacker. This risk is a substantial deterrent to the mainstream adoption of self-custody solutions.

Multisignature (multisig) functionality was introduced to mitigate this risk by adding additional layers of authorization. However, in practice, this solution has not been widely adopted. Major XRP Ledger wallets do not support multisig in a way that allows average users to easily benefit from the functionality; also the complexity of setting up and managing multisig accounts makes it inaccessible for many users. Additionally, even multisig protected accounts can be drained if multiple private keys are compromised by a malicious actor.

The objective of this amendment is to propose a user-friendly and secure mechanism that can be easily implemented as an alternative to multisig or used in combination with multisig to further enhance security.

When enabled on an account, it will prevent an attacker from instantly draining an account and provide the user with an opportunity to move their funds to an alternative authorized backup account.

The system will seamlessly integrate with the current transaction flow and activate only when the user's predefined rules are triggered. Additionally, the amendment is entirely optional, requiring users to opt-in to benefit from its features.

## Overhead

- It is anticipated that there will need to be an efficient test at the start of each transaction to check if the firewall is active on an account.
- If not active, the amendment would add no further overhead.
- If the firewall is active, the rules would be applied as guards which return to the normal flow as early as possible, adding the least overhead possible to a transaction.
- When all guards are satisfied, there is a need for an efficient mechanism to track a value total within a defined time period.
- The amount tests are very simple and should add little overhead, as it is a simple operator test of `(tx.Amount + firewall.runningTotal) > firewall.Amount`.

## Basic Flows

**Account compromise without firewall engaged**

1. A user has their private key compromised.
2. The attacker adds a new regular key and disables the master key, thus locking the user out of the account.
3. The attacker now moves the entire balance to their own wallet.
4. The assets are lost.

**Account compromise with firewall engaged**

1. A user has their private key compromised.
2. The attacker adds a new regular key and attempts to disabled the master key, but since the firewall is engaged the master key cannot be disabled; this is part of the spec.
3. The attacker has account access via the PK, so attempts to send the entire balance to another account, which is then blocked because the account is not on the whitelist and either a) the user has not set an optional maximum value or b) the user set an appropriate value of say 500 XRP as the limit. In either scenario the transaction fails and any further drain attempt is limited to the configured maximum value.
4. The attacker tries to add their account to the whitelist, but this fails because the Firewall is already engaged and changes to `FirewallWhitelistSet` transaction now require the transaction to be signed by the account specified in `sfPublicKey`.
5. The attacker decides to get value out of the account via another transaction: eg... They mint an NFT and list for sale for the entire account balance, create an offer and then attempt to drain the wallet by accepting such an offer. The transaction is blocked by the Firewall on the basis that the Firewall protects any transaction against value moving from an account, not just a Payment. All other attempts to do this by Escrow, Offer, etc will be blocked by applying the same logic over max value within defined period where destination is not on the Whitelist.
6. As a last ditch attempt, the attacker attempts to delete the account, setting their own account as the destination for the balance, but this fails because the Account cannot be deleted with the `AccountDelete` transaction when the `Firewall` is enabled.
7. The account owner can now move the entire balance to their designated backup account and there is nothing the attacker can do to stop it.

**Owner wants to delete their account**

1. The user attempts to delete their account, but this fails with error informing that account delete cannot complete, if the Firewall is engaged.
2. The user deletes the Firewall.
3. The account can be deleted in the normal way.

**Day to Day use**

1. A user engages the Firewall with the optional time-period of 24 hours and value limit of 500 XRP.
2. The user wants to send 5000 XRP to Bitstamp; Bitstamp is a trusted account (with Destination Tag) set on the `FirewallWhitelist`. The payment is sent as normal and the firewall allows the payment to proceed with no noticeable difference.
3. The user wants to send a payment to a `SuperCoolNewProject` to subscribe to a new app. The payment is for 75 XRP. The payment is sent as normal because the payment expends 75 XRP of the users defined 500 XRP daily limit (within the 24 hours period). The firewall allows the payment to proceed as normal.
4. The user makes 2 more payments successfully a few hours later, both for 100 XRP each. The user has now expended 275 XRP of the 500 XRP limit.
5. The user makes a payment of 250 XRP, 23 hours from the time of the 75 XRP subscription. The payment is rejected because a) the payment is going to an account that is not on the whitelist and; b) the payment total plus the current running total now exceeds the 500 XRP limit set by the user within a 24 hour period.
6. In this Day-to-Day scenario; the Firewall is acting like a current banking app that has a maximum daily spend value set. The user _COULD_ choose to override this and allow the payment to proceed; and there are different ways to do this. One way is to increase the limit; another would be to shorten the time-period; another would be to add the destination account to the whitelist; another would be to delete the firewall entirely; a pretty cool way (if XLS 56 is enabled) would be to do a batch transaction that adds the account to the firewall long enough for the transaction to proceed and then immediately removes it.
7. This may be considered a frustration to the user, however it is how most current bank accounts work and this is the firewall in action but considering the alternative, which is that an attacker now has their private key; this is a small price to pay for being able to sleep well at night.
8. The user is not prevented from spending their money; the worst case outcome for the user is a mild amount of frustration; AND this could be limited by UI/UX as a simple check on the Firewall would inform them that a payment would fail, thus preventing a failed transaction and with XLS 56 enabled its possible a user experience would evolve that totally mitigates the frustration.

## Limitations

This proposal only protects XRP; it does not prevent the draining of any other asset held on an account. However, with broad support, the specification could be updated to include protection for issued assets and potentially other assets like NFTs.

## Audience

This proposal is not a replacement for multisig; it is proposed as an easier alternative for retail and small enterprises and as an additional feature that could be used to further enhance multisig-protected accounts.

## Amendment

The proposed amendment introduces a new feature that allows for configuration of time based, value limits on outgoing transactions.

When a transaction is submitted, it will only be accepted if the value (including the SUM of all other successful transactions, within the defined time-period), is less than the amount defined on the firewall; OR the transaction destination is listed on the firewall whitelist OR the transaction destination is the BackupAccount on the firewall ledger entry.

The amendment adds the following:

- A new ledger entry: `Firewall`
- A new transaction type: `FirewallSet`
- A new transaction type: `FirewallDelete`
- A new ledger entry: `FirewallWhitelist`
- A new transaction type: `FirewallWhitelistSet`

## New Ledger Entry: `Firewall`

The `Firewall` ledger entry is a new on-ledger object that stores the rules to be applied to all outgoing transactions, as well as a safeguard for authorization of updates to the object once set.

The object has the following fields:

| Field             | Type      | Required | Description                                                                                                                                                                |
| ----------------- | --------- | -------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| sfAccount         | AccountID | ✔️       | The account for which the`Firewall` is set.                                                                                                                                |
| sfPublicKey       | PublicKey | ✔️       | A required public key to an account that is allowed to update the`Firewall` and `FirewallWhitelist`.                                                                       |
| sfBackupAccount   | AccountID | ✔️       | A required account authorized to receive funds (without restriction) in the event of compromise.                                                                           |
| sfTimePeriod      | UInt64    |          | Time period in seconds (e.g., 86400 seconds = 24 hours)                                                                                                                    |
| sfTimePeriodStart | UInt32    |          | The starting time (Ripple epoch time) that is used with sfTimePeriod to create a window of time for tracking total.<br />This field is only updatable from within rippled. |
| sfAmount          | Amount    |          | Firewall Amount in drops (1 XRP = 1,000,000 drops)                                                                                                                         |
| sfTotalOut        | Amount    |          | Total amount (in drops) in a specific time period. Is reset at the end of the period.<br />This field is only updatable from within rippled.                               |

Example `Firewall` object:

```json
{
  "LedgerEntryType": "Firewall",
  "Account": "rU9XRmcZiJXp5J1LDJq8iZFujU6Wwn9cV9",
  "PublicKey": "EDPUBLICKEY",
  "BackupAccount": "YourBackupAddress",
  "TimePeriod": 86400,
  "TimePeriodStart": 123412345,
  "Amount": "100000000",
  "TotalOut": "5000000"
}
```

## New Transaction Type: `FirewallSet`

The `FirewallSet` transaction is used to set and update the `Firewall`.

To set the `Firewall` the `sfPublicKey` and `sfBackupAccount` are required.

To update the `Firewall` `sfSignature` field is required, which will be validated against the `sfPublicKey` on the firewall ledger entry object.

| Field             | Type      | Required | Description                                                                                                                                     |
| ----------------- | --------- | -------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| sfTransactionType | String    | ✔️       | The type of transaction:`FirewallSet`.                                                                                                          |
| sfAccount         | AccountID | ✔️       | The account for which the`Firewall` is set.                                                                                                     |
| sfPublicKey       | PublicKey |          | The PublicKey set during initialization that will be used later to validate the signature for updates to the `Firewall` and `FirewallWhitelist` |
| sfBackupAccount   | AccountID |          | The Backup account set during initialization that can be used to bypass the firewall.                                                           |
| sfTimePeriod      | UInt64    |          | Time period in seconds (e.g., 86400 seconds = 24 hours)                                                                                         |
| sfAmount          | Amount    |          | Firewall Amount in drops (1 XRP = 1,000,000 drops)                                                                                              |
| sfSignature       | Blob      |          | The signature that will be validated against the`PublicKey` on the firewall ledger entry object.                                                |

### `FirewallSet` - Create

```json
{
  "TransactionType": "FirewallSet",
  "Account": "rU9XRmcZiJXp5J1LDJq8iZFujU6Wwn9cV9",
  "PublicKey": "EDPUBLICKEY",
  "BackupAccount": "rY6CEmcZiJXp5L4LDJq3gZFujU6Wwn7xH3",
  "TimePeriod": 86400,
  "Amount": "1000000000"
}
```

#### Failure Conditions

- BackupAccount == Account
- PublicKey (AccountID) == Account
- PublicKey (AccountID) == BackupAccount
- Missing PublicKey Field
- Missing BackupAccount Field
- TimePeriod <= 0
- Amount <= 0

#### State Changes

- Creates the `Firewall` Ledger Entry, setting the fields.

### `FirewallSet` - Update

```json
{
  "TransactionType": "FirewallSet",
  "Account": "rU9XRmcZiJXp5J1LDJq8iZFujU6Wwn9cV9",
  "TimePeriod": 43200,
  "Amount": "2000000000",
  "Signature": "xxxxxxxSomeSignatureVerifiableAgainstThePublicKeyStoredOnTheFirewallObjectXxxxxxxx"
}
```

#### Failure Conditions

- BackupAccount == Account
- PublicKey (AccountID) == Account
- PublicKey (AccountID) == BackupAccount
- Missing Signature Field
- Signature is invalid

#### State Changes

- Updates the `Firewall` Ledger Entry, setting the fields.

## New Transaction Type: `FirewallDelete`

The `FirewallDelete` transaction is used to delete the `Firewall` object.

To delete the `Firewall` the transaction must include `sfSignature` of the transaction which will be validated against the `sfPublicKey` on the firewall ledger entry object.

| Field             | Type      | Required | Description                                                                                      |
| ----------------- | --------- | -------- | ------------------------------------------------------------------------------------------------ |
| sfTransactionType | String    | ✔️       | The type of transaction:`FirewallDelete`.                                                        |
| sfAccount         | AccountID | ✔️       | The account for which the`Firewall` is set.                                                      |
| sfSignature       | Blob      |          | The signature that will be validated against the`PublicKey` on the firewall ledger entry object. |

### `FirewallDelete`

```json
{
  "TransactionType": "FirewallDelete",
  "Account": "rU9XRmcZiJXp5J1LDJq8iZFujU6Wwn9cV9",
  "Signature": "xxxxxxxSomeSignatureVerifiableAgainstThePublicKeyStoredOnTheFirewallObjectXxxxxxxx"
}
```

#### Failure Conditions

- Firewall Object Does Not Exist
- Missing Signature Field

#### State Changes

- Removes the `Firewall` ledger entry.
- Removes all `FirewallWhitelist` entries.

## New Ledger Entry: `FirewallWhitelist`

The `FirewallWhitelist` ledger entry is a new on-ledger object that stores the accountID of an account that is authorized to bypass the configured rules of the firewall.
It closely mirrors the implementation of `DepositPreauth` in reverse.

The object has the following fields:

| Field               | Type      | Required | Description                                                                                                          |
| ------------------- | --------- | -------- | -------------------------------------------------------------------------------------------------------------------- |
| sfAuthorize         | AccountID | ✔️       | The account being authorized to bypass the firewall.                                                                 |
| sfDestTag           | UInt32    |          | To support the sending of funds to a specific wallet that uses Destination Tags to segregate funds. ie: An Exchange. |
| sfOwnerNode         | UInt64    | ✔️       | The owner node of the account authorizing the outgoing transaction.                                                  |
| sfPreviousTxnID     | Hash256   | ✔️       | The ID of the previous transaction that modified this ledger entry.                                                  |
| sfPreviousTxnLgrSeq | UInt32    | ✔️       | The ledger sequence number of the previous transaction that modified this ledger entry.                              |

Example `FirewallWhitelist` object:

```json
{
  "LedgerEntryType": "FirewallWhitelist",
  "Authorize": "rU9XRmcZiJXp5J1LDJq8iZFujU6Wwn9cV9",
  "OwnerNode": "0000000000000000",
  "PreviousTxnID": "5DB01B7E2D4E5F6A3B3E2D4E5F6A3B3E2D4E5F6A3B3E2D4E5F6A3B3E2D4E5F6A",
  "PreviousTxnLgrSeq": 12345678
}
```

## New Transaction Type: `FirewallWhitelistSet`

The `FirewallWhitelistSet` transaction is used to authorize specific accounts to bypass the configured firewall rules.

- To authorize an account, populate the sfAuthorize field.
- To unauthorize an account, populate the sfUnauthorize field.

To be a valid transaction one of these fields must contain a valid active accountID.

**Security:**

To add an account to the whitelist or remove an account from the whitelist the transaction must include a signature of the transaction which will be validated against the `PublicKey` on the firewall ledger entry object.

| Field             | Type      | Required | Description                                                                                                          |
| :---------------- | --------- | -------- | -------------------------------------------------------------------------------------------------------------------- |
| sfTransactionType | String    | ✔️       | The type of transaction:`FirewallWhitelistSet`.                                                                      |
| sfAccount         | AccountID | ✔️       | The account authorizing the outgoing transaction.                                                                    |
| sfAuthorize       | AccountID |          | The account being authorized.                                                                                        |
| sfDestTag         | UInt32    |          | To support the sending of funds to a specific wallet that uses Destination Tags to segregate funds. ie: An Exchange. |
| sfUnauthorize     | AccountID |          | The account being unauthorized.                                                                                      |
| sfSignature       | Blob      | ✔️       | The signature that will be validated against the`PublicKey` on the firewall ledger entry object.                     |

### `FirewallWhitelistSet` - Authorize

```json
{
  "TransactionType": "FirewallWhitelistSet",
  "Account": "rU9XRmcZiJXp5J1LDJq8iZFujU6Wwn9cV9",
  "Authorize": "rWhitelisted1",
  "Signature": "xxxxxxxSomeSignatureVerifiableAgainstThePublicKeyStoredOnTheFirewallObjectXxxxxxxx"
}
```

### `FirewallWhitelistSet` - Unauthorize

```json
{
  "TransactionType": "FirewallWhitelistSet",
  "Account": "rU9XRmcZiJXp5J1LDJq8iZFujU6Wwn9cV9",
  "Unauthorize": "rWhitelisted1",
  "Signature": "xxxxxxxSomeSignatureVerifiableAgainstThePublicKeyStoredOnTheFirewallObjectXxxxxxxx"
}
```

#### Failure Conditions

- Authorize and Unauthorize fields missing
- Authorize already exists
- ~~Authorize account is not active~~ _(removed on the basis you may want to register an account to activate)_
- Unauthorize does not exist
- Missing Signature Field
- Signature is invalid

#### State Changes

- Updates the `FirewallWhitelist` Ledger Entry, setting the fields.

## Transaction Processing

When a transaction is submitted from an account with the firewall enabled, the following rules apply:

- **Transaction Type**: The Firewall blocks various transaction types, e.g., Payment, EscrowCreate, NFTokenCreateOffer, and any other transaction that results in XRP leaving an account because a payment is not the only way an attacker can effectively drain an account.
- **Currency Type**: The Firewall will only apply rules to transactions involving XRP. Limits on trustlines, issued currencies or other asset types, could be included in an upgraded specification.
- **Transaction Rules**:
  - If the destination is the `BackupAccount` set on the firewall ledger entry, the transaction is successful (`tesSUCCESS`).
  - If the destination is authorized, the transaction is successful (`tesSUCCESS`).
  - If the `TotalOut`, is less than the configured firewall amount, the transaction is successful (`tesSUCCESS`)
  - Else the transaction is rejected (`tecFIREWALL_REJECTION`)

### Calculating `TotalOut`

To implement the time based amount limit, we must have access to a total amount of XRP that has already left the account within the defined time period and this method must be very efficient.

First: The calculation of total amount should be deferred, so it only runs, after all other guards have passed and it is now required.

**Proposed Algorithm**

```
BEGIN
    current_time = GET current time
    start_time = GET start time from firewall
    time_period = GET time period from firewall
    transaction_amount = GET transaction amount

    IF start_time IS NOT_SET THEN
        // No transactions have been tracked in the current time period
        SET firewall start time TO current_time
        ADD transaction_amount TO firewall total out // This will currently be 0
    ELSE
        IF current_time - start_time > time_period THEN
            // The monitoring period has expired, so reset
            SET firewall total out TO 0
            SET firewall start time TO current_time
            ADD transaction_amount TO firewall total out // which will be 0 after reset
        ELSE
            // Add the transaction amount to the ongoing total
            ADD transaction_amount TO firewall total out
        END IF
    END IF
END
```

**Key Points to Understand**

- **Monitoring Period:** The firewall tracks transactions within a specific time period calculated between the time of the first transaction (`start time`) within a new period and the length of the user-defined (`time period`). When the period expires, the (`total out`) is reset, and a new period begins on the next successful transaction.
- **Transaction Tracking:** Each transaction amount is added to a running total (`total out`), which helps in tracking the total outgoing amount within the defined period.
- **Total Reset:** When a transaction occurs and the time period has expired, the start time is set to the current time, and the (`total out`) is set to 0 to ensure that the firewall only considers transactions within the new current period.
- **Effects of Whitelist:** Any transaction to a whitelisted account has no effect on the calculation of the running total (`total out`) and this code would never run.

## Compromised Account Protection

Upon enabling the firewall feature, the following measures are implemented:

- **Public Key and Signature Verification**: All updates to the Firewall OR FirewallWhitelist must include the signature of the Account specified in the firewall field sfPublicKey; this ensures that if an account is compromised the attacker cannot remove the firewall or add another account to the whitelist.
- **Master Key Protection**: Upon setting the Firewall feature, the master key cannot be disabled. If an `AccountSet` transaction attempts to disable the master key (`tfDisableMaster`), the transaction is rejected. This is to prevent an attacker from locking the owner out of their account.
- **Account deletion:** An account may not be deleted once the Firewall is engaged as this is a potential exploit for an attacker to drain an account.

The combination of requiring a second level of security to modify the firewall feature, along with the prevention of an attacker from locking a user out of their account, means that while an attacker may have the private key, the maximum damage they can do is drain the account of an amount less than that configured by the user within their given timeframe. The account owner can at any time instigate a payment of their full account balance to either their chosen backup account or any other account on their whitelist.

## Ideas

**Use with Batch (XLS 56)**

One interesting use case could be with combining Firewall with Batch (XLS 56) on high balance accounts that make regular automated payments.

Consider an account essentially locked down by enabling firewall with an Amount of zero. The only way to make a payment is to a whitelisted account.

Create a batch TX.

1. Add destination account to whitelist
2. Send payment
3. Remove destination account from whitelist

The balance cannot be drained even if the private key is compromised.

Implementing a design pattern where the signature account `sfPublicKey` is sufficiently segregated from the main account would result in a lightweight form of multiSig.

## FAQ

### A.1 What happens if my seed/private key is compromised?

If you keys are compromised then you would want to move your funds from your account to a whitelisted account.

### A.2 Can the attacker disable my keys?

No, with firewall the disable master key functionality is disabled

### A.3 Can the attacker add themselves as a whitelisted account?

No, not without approval from the account that you intrusted during setup.

### A.4 Does the PublicKey that is signing firewall updates need to be a 3rd party?

No, this could be another account that you own or a 3rd party you trust

### A.5 Do I need to set an `BackupAccount`?

Yes, you are required to set the backup account when you setup the firewall for the first time.

### A.6 Do I need to set an `Amount` and a `TimePeriod`?

No, this is optional functionality to allow you to send small amounts without having to add the account to the whitelist.
