<pre>
    title:  Confidential Multi-Purpose Tokens for XRPL
    description: This amendment introduces Confidential Multi-Purpose Tokens (MPTs) on the XRP Ledger.
    author: Murat Cenk <mcenk@ripple.com>, Aanchal Malhotra <amalhotra@ripple.com>, Ayo Akinyele <jakinyele@ripple.com>
    status: Ongoing
    category: Amendment
    created: Jan 15, 2026
</pre>

# Confidential Multi-Purpose Tokens for XRPL

## 1. Abstract

This specification introduces **Confidential Multi-Purpose Tokens (Confidential MPTs)** on the XRP Ledger as an extension of the XLS-33 Multi-Purpose Token standard. Confidential MPTs enable **confidential balances and transfers** using EC-ElGamal encryption and zero-knowledge proofs (ZKPs), while preserving the core accounting semantics and supply invariants of XLS-33.

The design provides the following properties:

- **Confidentiality:** Individual balances and transfer amounts are encrypted and are not revealed to validators or external observers.
- **Public auditability:** Issuance limits remain publicly enforceable through the existing invariant  
  `OutstandingAmount ≤ MaxAmount`, without requiring decryption of confidential balances.
- **Selective disclosure / view keys:** The protocol supports flexible auditability through two models:  
  (i) a trust-minimized, on-chain auditor model based on encrypted balance mirroring and zero-knowledge consistency proofs, which is extensible to additional auditors via re-encryption; and  
  (ii) a simpler, trust-based alternative using issuer-controlled view keys for on-demand disclosure.
- **Compatibility:** Public and confidential balances may coexist for the same token. A designated issuer second account is treated identically to other non-issuer holders, preserving XLS-33 issuance semantics.
- **Issuer control:** Existing issuer controls are preserved and extended to confidential balances, including issuer-initiated freezing and clawback to the issuer’s reserve.

Confidential MPTs align directly with XLS-33 by maintaining `OutstandingAmount` as the sum of all non-issuer balances. Supply consistency is enforced deterministically by validators using plaintext ledger fields, while confidentiality is achieved at the transaction level through equality proofs and compact range proofs.

## 2. Motivation

XLS-33 enables flexible tokenization on the XRP Ledger, but all balances and transfers remain publicly visible. This transparency limits adoption in institutional and privacy-sensitive contexts. Confidential MPTs address this gap by introducing encrypted balances and confidential transfers while preserving XLS-33 semantics.

The design maintains the standard definition of OutstandingAmount (OA) as the sum of all non-issuer balances. A complementary value, ConfidentialOutstandingAmount (COA), tracks the confidential portion of circulation, ensuring that while individual balances are encrypted, the global supply remains auditable. MaxAmount (MA) continues to cap the total supply, allowing validators to enforce consistency with the existing invariant OA ≤ MA.

### 2.1 Benefits

- Confidentiality: Hides individual balances and transfer amounts using EC-ElGamal encryption and ZKPs.
- Auditability: Public auditability is preserved via XLS-33’s existing OA semantics.
- Flexible Compliance: Enables selective disclosure through multiple mechanisms, including a trust-minimized on-chain model and a simpler issuer-controlled view key model.
- Compatibility: Maintains backward compatibility with XLS-33 by treating the issuer’s second account as a standard holder.
- Enhanced Issuer Control: Provides optional Freeze and a Clawback transaction, giving issuers the tools needed to manage assets and enforce compliance.

## 3. Scope

This XLS specifies the protocol changes required to support confidential MPTs, including:

### 3.1 New Transaction Types

- ConfidentialMPTConvert: Converts public MPT balances into encrypted form for a holder.
- ConfidentialMPTSend: Confidential transfer of tokens between accounts, with encrypted amounts validated by ZKPs.
- ConfidentialMPTMergeInbox: Merges a holder’s inbox balance into their spending balance, preventing stale-proof issues.
- ConfidentialMPTConvertBack: Converts confidential balances back into public form, restoring visible balances or returning funds to the issuer’s reserve.
- ConfidentialClawback: An issuer-only transaction to forcibly convert a holder’s confidential balance back to the issuer's public reserve.

### 3.2 New Ledger Fields and Objects

MPTokenIssuance Extensions: To support confidential MPTs, the MPTokenIssuance ledger object is extended with two new flags and three new fields. These serve as the global configuration and control settings for the token's confidential features.

### 3.2.1 New Flags:

- lsfMPTCanPrivacy: If set, indicates that confidential transfers and conversions are enabled for this token issuance.
- lsmfMPTCannotMutatePrivacy: If set, the lsfMPTCanPrivacy flag can never be changed after the token is issued, permanently locking the confidentiality setting.

### 3.2.3 New Fields:

- IssuerElGamalPublicKey: (Optional) A string containing the issuer’s 33-byte compressed ElGamal public key. This field is required if the lsfMPTCanPrivacy flag is set.
- ConfidentialOutstandingAmount: (Required if lsfMPTCanPrivacy is set) The total amount of this token that is currently held in confidential balances. This value is adjusted with every ConfidentialMPTConvert, ConfidentialMPTConvertBack, and ConfidentialClawback transaction.
- AuditorPolicy: (Optional) An object containing the configuration for an on-chain auditor, including their public key and an immutability flag.

### 3.3 Managing Confidentiality Settings

The confidentiality status of an MPT is controlled by the `lsfMPTCanPrivacy` flag on the `MPTokenIssuance` object. Only when this flag is enabled can the token support confidential transfers.

### 3.3.1 Mutability & Defaults

- **Default Behavior (Mutable):** By default, an MPT issuance is created with `lsmfMPTCannotMutatePrivacy` set to **false**. This means the issuer retains the ability to toggle the privacy setting (`lsfMPTCanPrivacy`) on or off via [`MPTokenIssuanceSet`](https://xrpl.org/docs/references/protocol/transactions/types/mptokenissuanceset) transactions.
- **Permanent Lock (Immutable):** If the issuer sets the `tmfMPTCannotMutatePrivacy` flag during the [`MPTokenIssuanceCreate`](https://xrpl.org/docs/references/protocol/transactions/types/mptokenissuancecreate) transaction, the `lsfMPTCanPrivacy` setting becomes permanent and can never be changed.

### 3.3.2 Enabling Confidentiality

There are two ways to enable the `lsfMPTCanPrivacy` flag:

- **At Creation:** The issuer can set the `tfMPTCanPrivacy` flag immediately during the `MPTokenIssuanceCreate` transaction. More can be read here
- **Post-Creation (Update):** If the issuance was created with mutability enabled (i.e., `lsmfMPTCannotMutatePrivacy` is false), the issuer can later submit an `MPTokenIssuanceSet` transaction to enable `lsfMPTCanPrivacy`.

### 3.3.3 Disabling Confidentiality

If the issuance is mutable, the issuer may disable `lsfMPTCanPrivacy` via `MPTokenIssuanceSet`, but only under strict conditions:

- **Zero Confidential Supply:** The transaction will fail if the `ConfidentialOutstandingAmount` (COA) is greater than 0. This constraint prevents user funds from being trapped in a confidential state that the ledger no longer recognizes.

### 3.4 MPToken Extensions: Extends per-account MPT objects with confidential balance fields:

- ConfidentialBalance_Spending (CB_S): Encrypted spendable balance under the holder’s key.
- ConfidentialBalance_Inbox (CB_IN): Encrypted incoming balance under the holder’s key.
- CB_S_Version: Monotonically increasing version number for CB_S.
- EncryptedBalanceIssuer: The issuer's confidential tracking of the total funds they have issued to this specific holder. This encrypted balance (under the IssuerElGamalPublicKey) serves as an audit-mirror, which, when decrypted by the issuer, conceptually matches the holder's total confidential balance (sum of CB_S and CB_IN).
- EncryptedBalanceAuditor (optional): Same balance encrypted under an auditor’s key.
- HolderElGamalPublicKey: Holder’s ElGamal public key.
- AuditorPublicKey (optional): Auditor’s ElGamal public key.

### 3.5 Proof System

The protocol relies on a set of ZKPs to validate confidential transactions without revealing balances or transfer amounts. The following proof types are used:

- **Plaintext–ciphertext equality proofs:** Prove that a publicly known amount `m` is correctly encrypted.

- **Plaintext equality proofs:** Prove that multiple ElGamal ciphertexts encrypt the same plaintext value, ensuring consistency of a confidential amount across the sender, receiver, issuer, and optional auditor.

- **ElGamal–Pedersen equality proofs:** Link ElGamal-encrypted values to Pedersen commitments, allowing confidential amounts and balances to be used as inputs to range proofs without revealing the underlying values.

- **Range proofs:** Prove that confidential amounts and post-transfer confidential balances lie within a valid range, enforcing non-negativity and preventing overspending.

## 4. Definitions & Terminology

- **MPT (Multi-Purpose Token):** A token standard defined by XLS-33, extended here to support confidential balances and transfers.

- **MPTokenIssuance (Object):** Ledger object storing metadata for an MPT, including `Currency`, `Issuer`, `MaxAmount` (MA), and `OutstandingAmount` (OA).

- **MPToken (Object):** Ledger object representing a holder’s balance of a given MPT. Extended to include confidential balance fields.

- **Second Account (Issuer-as-Holder):** A designated account controlled by the issuer but treated by the ledger as a standard non-issuer holder.

- **OutstandingAmount (OA):** The total of all non-issuer balances (public and confidential), including the issuer’s second account.

- **ConfidentialOutstandingAmount (COA):** The total amount of an MPT currently held in confidential balances by non-issuers, including the issuer’s second account.

- **MaxAmount (MA):** The maximum allowed token supply. Invariant: `OA ≤ MA`.

- **EC-ElGamal Encryption:** A public-key encryption scheme with additive homomorphism, used for encrypted balances and homomorphic balance updates.

- **Zero-Knowledge Proofs (ZKPs):** Cryptographic proofs used to validate confidential transactions without revealing amounts, including:
  - **Plaintext–ciphertext equality proofs** and **plaintext equality proofs**, ensuring consistency across ElGamal ciphertexts under different public keys.
  - **ElGamal–Pedersen equality proofs**, linking encrypted values to Pedersen commitments.
  - **Range proofs**, ensuring confidential amounts and post-transfer balances are non-negative and lie within a valid range.

- **Split-Balance Model:** Confidential balances are divided into:
  - **Spending (CB_S):** Stable balance used for spending and proofs.
  - **Inbox (CB_IN):** Receives incoming transfers and must be explicitly merged into `CB_S`, preventing stale-proof rejection.

- **Auditor Policy:** An optional issuance-level configuration that enables selective disclosure by encrypting balances under an auditor’s public key.

- **Clawback:** A privileged issuer-only operation performed via a `ConfidentialClawback` transaction, which forcibly converts a holder’s confidential balance back into the issuer’s public reserve while preserving ledger accounting consistency through ZKPs.

## 5. Protocol Overview

The Confidential MPT protocol is built on three core design principles: the issuer second account model, the split-balance model for reliable transfers, and a multi-ciphertext architecture for privacy and compliance.

### 5.1 The Issuer Second Account Model

To introduce confidential tokens without modifying the supply semantics of XLS-33, the protocol uses an issuer-controlled second account that is treated by the ledger as a standard non-issuer holder.

- **Issuing into circulation:** The issuer introduces confidential supply by executing a `ConfidentialMPTConvert` transaction, moving funds from its public reserve into the issuer’s second account.

- **Preserving invariants:** Because the second account is a non-issuer, its balance is included in `OutstandingAmount` (OA). This preserves the existing `OA ≤ MaxAmount` invariant and allows validators to enforce the supply cap without decrypting confidential balances. All subsequent confidential transfers between non-issuer holders are redistributions that do not modify OA.

### 5.2 The Split-Balance Model

To prevent stale-proof failures—where an incoming transfer could invalidate a proof generated for an outgoing transfer—each account’s confidential balance is split into two components:

- **Spending balance (CB_S):** A stable balance used for generating proofs in outgoing `ConfidentialMPTSend` transactions.
- **Inbox balance (CB_IN):** A separate balance that receives all incoming confidential transfers.
- **Merging:** Holders explicitly merge `CB_IN` into `CB_S` using the proof-free `ConfidentialMPTMergeInbox` transaction. Each merge increments a monotonically increasing version number (`CB_S_Version`), which is bound to newly generated proofs to prevent replay and ensure proofs reference a stable balance.

### 5.3 The Multi-Ciphertext Architecture

A single confidential balance is represented by multiple parallel ciphertexts, each serving a distinct purpose. ZK equality proofs ensure that all ciphertexts correspond to the same hidden amount.

- **Holder encryption:** The primary balance is encrypted under the holder’s public key, granting exclusive spending authority.

- **Issuer encryption:** The same balance is also encrypted under the issuer’s public key (`EncryptedBalanceIssuer`). This encrypted mirror supports supply consistency checks and issuer-level auditing without granting spending capability.

- **Optional auditor encryption:** If an `AuditorPolicy` is active, balances are additionally encrypted under an auditor’s public key (`EncryptedBalanceAuditor`), enabling on-chain selective disclosure. The issuer may also re-encrypt balances for newly authorized auditors using its encrypted mirror, supporting forward-looking compliance.

## 6. Transaction: `ConfidentialMPTConvert`

**Purpose:**  
Converts a holder’s own visible (public) MPT balance into confidential form. The converted amount is credited to the holder’s confidential inbox balance (`CB_IN`) to avoid immediate proof staleness, requiring an explicit merge into the spending balance (`CB_S`) before use. This transaction also serves as the opt-in mechanism for confidential MPT participation: by executing it (including a zero-amount conversion), a holder’s `HolderElGamalPublicKey` is recorded on their `MPToken` object, enabling the holder to receive and manage confidential funds.

This transaction is a **self-conversion only**. Issuers introduce supply exclusively through existing XLS-33 public issuance mechanisms. The issuer’s designated second account participates in confidential MPTs by executing `ConfidentialMPTConvert` as a regular holder, with no special privileges. In all cases, `OutstandingAmount` (OA) and `ConfidentialOutstandingAmount` (COA) are maintained in plaintext according to existing invariants.

### 6.1 Use Cases

- **Holder → self (public → confidential):**  
  Public balance decreases and confidential balance increases; OA unchanged, COA increases (both in plaintext).
- **Issuer second account → self (public → confidential):**  
  After being funded publicly via XLS-33 issuance, the second account converts its own balance like any holder; OA unchanged, COA increases.
- **Hybrid circulation:**  
  Tokens may coexist in public and confidential form.

### 6.2 Transaction Fields

| Field Name               | Required? | JSON Type | Internal Type | Description                                                                                                                                                 |
| :----------------------- | :-------- | :-------- | :------------ | :---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `TransactionType`        | ✔️        | `string`  | `UInt16`      | Must be `ConfidentialMPTConvert`.                                                                                                                           |
| `Account`                | ✔️        | `string`  | `AccountID`   | The account initiating the conversion.                                                                                                                      |
| `MPTokenIssuanceID`      | ✔️        | `string`  | `UInt256`     | The unique identifier for the MPT issuance.                                                                                                                 |
| `MPTAmount`              | ✔️        | `number`  | `UInt64`      | The public plaintext amount $m$ to convert.                                                                                                                 |
| `HolderElGamalPublicKey` |           | `string`  | `Blob`        | The holder's ElGamal public key ($pk_A$). Mandatory if the account has not yet registered a key (initialization). Forbidden if a key is already registered. |
| `HolderEncryptedAmount`  | ✔️        | `string`  | `Blob`        | ElGamal ciphertext credited to the holder's $CB_{IN}$.                                                                                                      |
| `IssuerEncryptedAmount`  | ✔️        | `string`  | `Blob`        | ElGamal ciphertext credited to the issuer's mirror balance.                                                                                                 |
| `AuditorEncryptedAmount` |           | `string`  | `Blob`        | ElGamal Ciphertext for the auditor. **Required** if `sfAuditorElGamalPublicKey` is present on the issuance.                                                 |
| `BlindingFactor`         | ✔️        | `string`  | `Blob`        | The 32-byte scalar value used to encrypt the amount. Used by validators to verify the ciphertexts match the plaintext `MPTAmount`.                          |
| `ZKProof`                |           | `string`  | `Blob`        | A Schnorr Proof of Knowledge (PoK): prove the knowledge of the private key for the provided ElGamal Public Key.                                             |

**Notes:**

- This transaction performs **self-conversion only**; there is no `Receiver` field.
- Issuers introduce supply via existing XLS-33 public issuance. The issuer’s second account executes this transaction as a regular holder.

### 6.3. Failure Conditions

- **`temDISABLED`**: The `ConfidentialTransfer` feature is not enabled on the ledger.
- **`temMALFORMED`**:
  - `sfHolderElGamalPublicKey` is present but `sfZKProof` is not present (registering holder pub key)
  - `sfHolderElGamalPublicKey` is absent but `sfZKProof` is not absent (`sfZKProof` should not be provided if it's not registering holder pub key)
  - `sfHolderElGamalPublicKey` length is invalid, it should be 64.
  - `sfBlindingFactor` length is invalid, it should be 32.
  - `sfZKProof` length is invalid, it should be Schnorr Proof Length, which is 65.
- **`temBAD_CIPHERTEXT`**: Any provided ciphertext (`Holder`, `Issuer`, or `Auditor`) has an invalid length or represents an invalid elliptic curve point.
- **`tecNO_PERMISSION`**: The issuance has `sfAuditorElGamalPublicKey` set, but the transaction does not include `sfAuditorEncryptedAmount`.
- **`temBAD_AMOUNT`**: `MPTAmount` exceeds `maxMPTokenAmount`.
- **`tecINSUFFICIENT_FUNDS`**: The holder does not have enough public MPT balance to cover the `MPTAmount`.
- **`tecDUPLICATE`**: A public key is provided in the transaction, but the account already has a registered key.
- **`tecBAD_PROOF`**:
  - The `BlindingFactor` fails to reconstruct the provided ciphertexts given the plaintext `MPTAmount`.
  - The Schnorr `ZKProof` fails to verify the holder's knowledge of the secret key.

### 6.4. State Changes

If the transaction is successful:

- The holder's public **`sfMPTAmount`** is decreased by the converted amount.
- The **`sfConfidentialOutstandingAmount`** on the `MPTokenIssuance` object is increased by the converted amount.
- The holder's **`sfHolderElGamalPublicKey`** is registered on their `MPToken` object if it was not already present.
- The **`sfConfidentialBalanceInbox`** and **`sfIssuerEncryptedBalance`** are updated by homomorphically adding the provided ciphertexts.
- If initializing confidential state for the first time, **`sfConfidentialBalanceSpending`** is initialized with an encrypted zero and the version counter is set to 0.

### 6.5 Example — Holder converts 150 units (public → confidential, default to Inbox)

```json
{
  "Account": "rBob...",
  "TransactionType": "ConfidentialMPTConvert",
  "MPTokenIssuanceID": "610F33...",
  "MPTAmount": 1000,
  "HolderElGamalPublicKey": "038d...",
  "HolderEncryptedAmount": "AD3F...",
  "IssuerEncryptedAmount": "BC2E...",
  "BlindingFactor": "EE21...",
  "ZKProof": "ABCD..."
}
```

## 7. Transaction: `ConfidentialMPTSend`

**Purpose:**  
Performs a confidential transfer of MPT value between accounts while keeping the transfer amount hidden. The transferred amount is credited to the receiver’s confidential inbox balance (`CB_IN`) to avoid proof staleness; the receiver may later merge these funds into the spending balance (`CB_S`) via `ConfidentialMPTMergeInbox`.

### 7.1. Fields

| Field Name                   | Required? | JSON Type | Internal Type | Description                                                                                         |
| :--------------------------- | :-------- | :-------- | :------------ | :-------------------------------------------------------------------------------------------------- |
| `TransactionType`            | ✔️        | `string`  | `UInt16`      | Must be `ConfidentialMPTSend`.                                                                      |
| `Account`                    | ✔️        | `string`  | `AccountID`   | The sender's XRPL account.                                                                          |
| `Destination`                | ✔️        | `string`  | `AccountID`   | The receiver's XRPL account.                                                                        |
| `MPTokenIssuanceID`          | ✔️        | `string`  | `UInt256`     | Identifier of the MPT issuance being transferred.                                                   |
| `SenderEncryptedAmount`      | ✔️        | `string`  | `Blob`        | Ciphertext used to homomorphically debit the sender's spending balance.                             |
| `DestinationEncryptedAmount` | ✔️        | `string`  | `Blob`        | Ciphertext credited to the receiver's inbox balance.                                                |
| `IssuerEncryptedAmount`      | ✔️        | `string`  | `Blob`        | Ciphertext used to update the issuer mirror balance.                                                |
| `ZKProof`                    | ✔️        | `string`  | `Blob`        | ZKP bundle establishing equality, linkage, and range sufficiency.                                   |
| `PedersenCommitment`         | ✔️        | `string`  | `Blob`        | A cryptographic commitment to the user's confidential spending balance.                             |
| `AuditorEncryptedAmount`     |           | `string`  | `Blob`        | Ciphertext for the auditor. **Required** if `sfAuditorElGamalPublicKey` is present on the issuance. |

### 7.2 Use Cases

- **Holder → holder (including the issuer’s second account):**  
  Confidential redistribution of value with the transfer amount hidden.

- **Second account ↔ holder:**  
  Confidential redistribution among non-issuer holders under identical rules.

### 7.3. Failure Conditions

- **`temDISABLED`**: The `ConfidentialTransfer` feature is not enabled on the ledger.
- **`temMALFORMED`**: The sender is the issuer, or the account attempts to send to itself.
- **`temBAD_CIPHERTEXT`**: `AuditorEncryptedAmount` (if present) has invalid length or invalid EC point.
- **`tecNO_TARGET`**: The destination account does not exist.
- **`tecNO_AUTH`**: The issuance does not have the `lsfMPTCanTransfer` flag set.
- **`tecNO_PERMISSION`**: The issuance does not support privacy (`lsfMPTCanPrivacy`), or one of the participating accounts lacks a registered ElGamal public key or required confidential fields (`sfHolderElGamalPublicKey`, `sfConfidentialBalanceSpending`, etc.).
- **`terFROZEN`**: Either the sender or receiver's balance is currently frozen.
- **`tecBAD_PROOF`**: The provided Zero-Knowledge Proof fails to verify equality or range constraints.

### 7.4. State Changes

If the transaction is successful:

- **Sender Balance**: The sender's `sfConfidentialBalanceSpending` is homomorphically decremented.
- **Sender Versioning**: The sender's `sfConfidentialBalanceVersion` is incremented by 1 to prevent stale-proof replay.
- **Receiver Balance**: The receiver's `sfConfidentialBalanceInbox` is homomorphically incremented.
- **Issuer Mirrors**: The `sfIssuerEncryptedBalance` for both the sender and receiver are updated homomorphically to maintain audit consistency.
- **Global Supply**: Plaintext supply fields (`OA` and `COA`) remain unchanged.

### 7.5. Example Transaction

```javascript
{
  "Account": "rSenderAccount...",
  "TransactionType": "ConfidentialMPTSend",
  "Destination": "rReceiverAccount...",
  "MPTokenIssuanceID": "610F33B8EBF7EC795F822A454FB852156AEFE50BE0CB8326338A81CD74801864",
  "SenderEncryptedAmount": "AD3F...",
  "DestinationEncryptedAmount": "DF4E...",
  "PedersenCommitment": "038A...",
  "IssuerEncryptedAmount": "BC2E...",
  "ZKProof": "84af..."
}
```

Net effect: Public balances unchanged; confidential amount is redistributed (sender CB_S ↓, receiver CB_IN ↑). OA (plaintext) unchanged; COA (plaintext) unchanged.

## 8. Transaction: `ConfidentialMPTMergeInbox`

**Purpose:** Moves all funds from the inbox balance into the spending balance, then resets the inbox to a canonical encrypted zero (EncZero). This ensures that proofs reference only stable spending balances and prevents staleness from incoming transfers.

### 8.1 Use Cases

- A holder merges newly received confidential transfers into their spendable balance.
- The issuer merges its own inbox into the spending balance (applies to the second account).
- Required periodically to combine funds before subsequent confidential sends.

### 8.2 Transaction Fields

| Field Name          | Required? | JSON Type | Internal Type | Description                                 |
| :------------------ | :-------- | :-------- | :------------ | :------------------------------------------ |
| `TransactionType`   | ✔️        | `string`  | `UInt16`      | Must be `ConfidentialMPTMergeInbox`.        |
| `Account`           | ✔️        | `string`  | `AccountID`   | The account performing the merge.           |
| `MPTokenIssuanceID` | ✔️        | `string`  | `UInt256`     | The unique identifier for the MPT issuance. |

### 8.2.1. Failure Conditions

- **`temDISABLED`**: The `featureConfidentialTransfer` is not enabled.
- **`temMALFORMED`**: The account submitting the transaction is the **Issuer**. Issuers do not use the split-balance model.
- **`tecOBJECT_NOT_FOUND`**: The `MPTokenIssuance` or the user's `MPToken` object does not exist.
- **`tecNO_PERMISSION`**:
  - The issuance does not have the `lsfMPTCanPrivacy` flag set.
  - The user's `MPToken` object has not been initialized (missing `sfConfidentialBalanceInbox` or `sfConfidentialBalanceSpending`).
- **`tefINTERNAL`**: A system invariant failure where the issuer attempts to merge (checked again at preclaim).

### 8.3. State Changes

If the transaction is successful:

- **Update Spending Balance:** The current `sfConfidentialBalanceInbox` is homomorphically **added** to `sfConfidentialBalanceSpending`.
- **Reset Inbox:** The `sfConfidentialBalanceInbox` is reset to a canonical **encrypted zero**. This ensures the account is ready to receive new transfers without arithmetic errors.
- **Increment Version:** The `sfConfidentialBalanceVersion` is incremented by 1. If the version reaches the maximum 32-bit integer value, it wraps around to 0.

### 8.4. Rationale & Safety

- No value choice: ledger moves exactly the inbox, no risk of misreporting.
- No ZKP needed: no proof obligation since the value is known to ledger state.
- Staleness control: version bump invalidates any in-flight proofs tied to old CB_S.
- EncZero safety: inbox reset uses deterministic ciphertext of 0 so it remains a valid ElGamal ciphertext.

Canonical Encrypted Zero  
To ensure inbox fields always contain a valid ciphertext after reset:  
EncZero(Acct, Issuer, Curr): r = H("EncZero" || Acct || Issuer || Curr) mod n, curve order n\
return (R = r·G, S = r·Pk), Pk: ElGamal public key of Acct

- Deterministic across validators (no randomness beacon).
- Represents encryption of 0 under account’s key.
- Keeps inbox proofs well-formed.

### 8.5. Example Transaction

```json
{
  "Account": "rUserAccount...",
  "TransactionType": "ConfidentialMPTMergeInbox",
  "MPTokenIssuanceID": "610F33B8EBF7EC795F822A454FB852156AEFE50BE0CB8326338A81CD74801864"
}
```

## 9. Transaction: `ConfidentialMPTConvertBack`

### 9.1 Purpose: Convert confidential into public MPT value.

- For a holder: restore public balance from CB_S.
- For the issuer’s second account: return confidential supply to issuer reserve.

### 9.2 Account Effects

- Confidential Supply (COA): Decreases (COA ↓).
- Total Supply (OA): Unchanged. (Tokens are converted to public form, not burned).
- Holder Public Balance: Increases.
- Holder Confidential Balance: Decreases.

### 9.3. Fields

| Field Name               | Required? | JSON Type | Internal Type | Description                                                                                                                        |
| :----------------------- | :-------- | :-------- | :------------ | :--------------------------------------------------------------------------------------------------------------------------------- |
| `TransactionType`        | ✔️        | `string`  | `UInt16`      | Must be `ConfidentialMPTConvertBack`.                                                                                              |
| `Account`                | ✔️        | `string`  | `AccountID`   | The account performing the conversion.                                                                                             |
| `MPTokenIssuanceID`      | ✔️        | `string`  | `UInt256`     | The unique identifier for the MPT issuance.                                                                                        |
| `MPTAmount`              | ✔️        | `number`  | `UInt64`      | The plaintext amount to credit to the public balance.                                                                              |
| `HolderEncryptedAmount`  | ✔️        | `string`  | `Blob`        | Ciphertext to be subtracted from the holder's `sfConfidentialBalanceSpending`.                                                     |
| `IssuerEncryptedAmount`  | ✔️        | `string`  | `Blob`        | Ciphertext to be subtracted from the issuer's mirror balance.                                                                      |
| `BlindingFactor`         | ✔️        | `string`  | `Blob`        | The 32-byte scalar value used to encrypt the amount. Used by validators to verify the ciphertexts match the plaintext `MPTAmount`. |
| `AuditorEncryptedAmount` |           | `string`  | `Blob`        | Ciphertext for the auditor. **Required** if `sfAuditorElGamalPublicKey` is present on the issuance.                                |
| `PedersenCommitment`     | ✔️        | `string`  | `Blob`        | A cryptographic commitment to the user's confidential spending balance.                                                            |
| `ZKProof`                | ✔️        | `string`  | `Blob`        | A bundle containing the **Pedersen Linkage Proof** (linking the ElGamal balance to the commitment) and the **Range Proof**.        |

### 9.4. Failure Conditions

- **`temDISABLED`**: The `featureConfidentialTransfer` is not enabled.
- **`temMALFORMED`**:
  - The account is the Issuer
  - The `BlindingFactor` is not exactly 32 bytes.
- **`temBAD_CIPHERTEXT`**: Ciphertext lengths or formats are invalid.
- **`temBAD_AMOUNT`**: `MPTAmount` is zero or greater than the maximum allowable supply.
- **`tecOBJECT_NOT_FOUND`**: The `MPToken` or `MPTokenIssuance` does not exist.
- **`tecNO_PERMISSION`**:
  - The issuance does not have the `lsfMPTCanPrivacy` flag.
  - The user's `MPToken` is missing the `sfConfidentialBalanceSpending` or `sfHolderElGamalPublicKey` fields.
  - The issuance has `sfAuditorElGamalPublicKey` set, but the transaction does not include `sfAuditorEncryptedAmount`.
- **`tecINSUFFICIENT_FUNDS`**:
  - **Global Check:** The global `sfConfidentialOutstandingAmount` is less than the requested `MPTAmount`.
  - **Local Check:** The user's confidential balance is insufficient (enforced via ZK Proof verification).
- **`tecBAD_PROOF`**:
  - The `BlindingFactor` fails to verify the integrity of the ciphertexts.
  - The `ZKProof` fails the **Pedersen Linkage** check (proving the commitment matches the on-ledger balance).
  - The `ZKProof` fails the **Range Proof** (proving the remaining balance is non-negative).
- **`terFROZEN`**: The account or issuance is frozen.

### 9.5. State Changes

If the transaction is successful:

- **Public Balance:** The user's `sfMPTAmount` is increased by `MPTAmount`.
- **Global Supply:** The `sfConfidentialOutstandingAmount` on the issuance is decreased by `MPTAmount`.
- **Spending Balance:** The `sfConfidentialBalanceSpending` is updated via **homomorphic subtraction** of `HolderEncryptedAmount`.
- **Issuer Mirror:** The `sfIssuerEncryptedBalance` is updated via **homomorphic subtraction** of `IssuerEncryptedAmount`.
- **Version:** The `sfConfidentialBalanceVersion` is incremented by 1.

### 9.6. Example Transaction

```json
{
  "Account": "rUserAccount...",
  "TransactionType": "ConfidentialMPTConvertBack",
  "MPTokenIssuanceID": "610F33...",
  "MPTAmount": 500,
  "HolderEncryptedAmount": "AD3F...",
  "IssuerEncryptedAmount": "BC2E...",
  "AuditorEncryptedAmount": "C1A9...",
  "BlindingFactor": "12AB...",
  "PedersenCommitment": "038A...",
  "ZKProof": "ABCD..."
}
```

### 9.7. Edge Case Analysis (Low-Volume Transaction Flow):

\*\* Alice, the issuer, converts 50 ConfidentialMPT into her second account, performs a single confidential send of 20 to Bob (a holder), and then executes a ConvertBack of 30\.

Step 1. Issuer Convert (Alice → second account, 50\)

- Publicly revealed: Amount \= 50\.
- Ledger effect: OA ↑ 50, COA ↑ 50, IPB ↓ 50\.
- Outsiders now know: 50 CMPT entered confidential circulation.

Step 2. Confidential Send (Alice’s second account → Bob, amount 20\)

- Public sees: sender \= Alice’s second account, receiver \= Bob, ciphertexts, ZKPs.
- Amount 20 is hidden.
- Ledger effect: OA, COA, IPB unchanged (just redistribution).

Step 3. _ConvertBack_ (Alice’s second account → issuer reserve, 30\)

- Publicly revealed: Amount \= 30\.
- Ledger effect: OA ↓ 30, COA ↓ 30, IPB ↑ 30
- Alice’s confidential balance is now 0, but outsiders cannot know this since ElGamal ciphertexts for 0 look indistinguishable from nonzero.

### 9.7.1 What Outsiders can Infer:

- Net change in the confidential pool is 50  −  30  = 20\. So, 20 CMPT remain somewhere in confidential circulation.
- But they cannot know whether Bob got 20, 15, 5, or even 0 — because Alice’s second account may still hold some of the 20\.

### 9.7.2 Why no exact leakage:

- ElGamal ciphertexts are randomized: encrypting 0 produces a different-looking ciphertext each time.
- Outsiders cannot look at the second account’s balance ciphertext and say it is zero.
- Thus, they cannot deduce whether Alice’s second account was emptied or kept some confidential balance.

**Note:** This design allows tokens to move between public and private states. While the Convert and ConvertBack transactions show their amounts to provide this flexibility, they still protect the privacy of individual balances and transfers. Observers can only see the total change in circulation, not how the private supply is shared among holders. ElGamal randomization makes it impossible to tell the difference between accounts with zero balances. This ensures that outsiders cannot know if a specific account is empty or still holds private tokens.

## 10. Transaction: `ConfidentialClawback`

Clawback involves the issuer forcibly reclaiming funds from a holder's account. This action is fundamentally incompatible with standard confidential transfers, as the issuer does not possess the holder's private ElGamal key and therefore cannot generate the required ZKPs for a normal ConfidentialMPTSend. To solve this, the protocol introduces a single and privileged transaction that allows an issuer to verifiably reclaim funds in one uninterruptible step.

This issuer-only transaction is designed to convert a holder's entire confidential balance directly into the issuer's public reserve.

### 10.1. Fields

| Field Name          | Required? | JSON Type | Internal Type | Description                                         |
| :------------------ | :-------- | :-------- | :------------ | :-------------------------------------------------- |
| `TransactionType`   | ✔️        | `string`  | `UInt16`      | Must be `ConfidentialClawback`.                     |
| `Account`           | ✔️        | `string`  | `AccountID`   | The **Issuer** account sending the transaction.     |
| `Holder`            | ✔️        | `string`  | `AccountID`   | The account from which funds are being clawed back. |
| `MPTokenIssuanceID` | ✔️        | `string`  | `UInt256`     | The unique identifier for the MPT issuance.         |
| `MPTAmount`         | ✔️        | `number`  | `UInt64`      | The plaintext total amount being removed.           |
| `ZKProof`           | ✔️        | `string`  | `Blob`        | An Equality Proof validating the amount.            |

### 10.2 How the Clawback Process Works

1. Issuer Decrypts and Prepares: The issuer takes the EncryptedBalanceIssuer ciphertext from the HolderToClawback's MPToken object and uses its own private key to decrypt it, revealing the holder's total confidential balance, m.
2. Issuer Submits Transaction: The issuer creates and signs a ConfidentialClawback transaction, setting the RevealedAmount field to m. It also generates and includes an equality proof.
3. Validator Verification and Execution: Validators receive the transaction and perform a series of checks and state changes as a single:
   - Verification: They first confirm the transaction was signed by the token Issuer and that the ZKProof is valid. The proof provides cryptographic certainty that the RevealedAmount is the true value hidden in the holder's on-ledger ciphertext.
   - Ledger Changes: If the proof is valid, the validators execute all of the following changes at once:
     1. The ConfidentialBalance_Spending and ConfidentialBalance_Inbox are set to a valid encryption of zero.
     2. The global COA is decreased by the RevealedAmount.
     3. The global OA is also decreased by the RevealedAmount.
     4. The Issuer's public issuance capacity is restored (Global OutstandingAmount is decreased by the RevealedAmount), effectively burning the clawed-back tokens.

This single transaction securely and verifiably moves the funds directly from the holder's confidential balance to the issuer's public reserve, ensuring the integrity of the ledger's public accounting is perfectly maintained.

### 10.3. Failure Conditions

- **`temDISABLED`**: The `featureConfidentialTransfer` is not enabled.
- **`temMALFORMED`**:
  - The `Account` is not the issuer of the `MPTokenIssuanceID`.
  - The `Account` is attempting to claw back from itself (`Account` == `Holder`).
  - The `ZKProof` length is incorrect.
- **`temBAD_AMOUNT`**: `MPTAmount` is zero or exceeds the maximum limits.
- **`tecNO_TARGET`**: The `Holder` account does not exist.
- **`tecOBJECT_NOT_FOUND`**: The `MPTokenIssuance` or the holder's `MPToken` object does not exist.
- **`tecNO_PERMISSION`**:
  - The issuance does not have the `lsfMPTCanClawback` flag set.
  - The issuance is missing the `sfIssuerElGamalPublicKey`.
  - The holder's `MPToken` is missing the `sfIssuerEncryptedBalance`.
- **`tecINSUFFICIENT_FUNDS`**: The `MPTAmount` exceeds the global `sfConfidentialOutstandingAmount`.
- **`tecBAD_PROOF`**: The ZKP fails to prove that the `sfIssuerEncryptedBalance` (the mirror balance) encrypts the plaintext `MPTAmount`.

### 10.4. State Changes

If the transaction is successful, the holder's confidential state is reset, and the tokens are removed from the total supply:

- **Holder State Reset:**
  - `sfConfidentialBalanceInbox` is set to **Encrypted Zero**.
  - `sfConfidentialBalanceSpending` is set to **Encrypted Zero**.
  - `sfIssuerEncryptedBalance` is set to **Encrypted Zero**.
  - `sfAuditorEncryptedBalance` (if present) is set to **Encrypted Zero** (using the Auditor's public key).
  - `sfConfidentialBalanceVersion` is reset to `0`.
- **Supply Reduction:**
  - The global `sfConfidentialOutstandingAmount` (COA) is decreased by `MPTAmount`.
  - The global `sfOutstandingAmount` (OA) is decreased by `MPTAmount`.

### 10.5. Example Transaction

```json
{
  "Account": "rIssuerAccount...",
  "TransactionType": "ConfidentialClawback",
  "Holder": "rMaliciousHolder...",
  "MPTokenIssuanceID": "610F33B8EBF7EC795F822A454FB852156AEFE50BE0CB8326338A81CD74801864",
  "MPTAmount": 1000,
  "ZKProof": "a1b2..."
}
```

## 11. Transaction: `MPTokenIssuanceSet` (Extensions)

The existing `MPTokenIssuanceSet` transaction is extended to manage the confidential lifecycle of an MPT issuance. This includes enabling/disabling privacy status and registering encryption keys.

### 11.1. New Fields

| Field Name                | Description                                                                      |
| :------------------------ | :------------------------------------------------------------------------------- |
| `IssuerElGamalPublicKey`  | The 33-byte EC-ElGamal public key used for the issuer's mirror balances.         |
| `AuditorElGamalPublicKey` | The 33-byte EC-ElGamal public key used for regulatory oversight (if applicable). |

### 11.2. Usage & Mutability

This transaction is the only method to register keys or modify the privacy status (`tmfMPTSetPrivacy`) of an issuance. However, these actions are subject to strict state constraints to prevent funds from becoming locked or un-auditable.

### 11.3. Failure Conditions

- **`temDISABLED`**: The `featureConfidentialTransfer` is not enabled.
- **`temMALFORMED`**:
  - The provided Public Key is not exactly 33 bytes (`ecPubKeyLength`).
  - The transaction attempts to mutate privacy fields while also acting as a Holder.
  - **Atomic Key Rule:** The transaction contains `sfAuditorElGamalPublicKey` but does **not** contain `sfIssuerElGamalPublicKey`.
- **`tecNO_PERMISSION`**:
  - **Privacy Toggle Constraint:** The transaction attempts to set or clear the `lsfMPTCanPrivacy` flag, but the `sfConfidentialOutstandingAmount` is greater than 0.
  - **Key Rotation Constraint:** The transaction provides a `sfIssuerElGamalPublicKey` (or Auditor Key), but the issuance object **already** has one. (Keys are immutable once set).
  - **Dependency:** The transaction provides a `sfIssuerElGamalPublicKey`, but the issuance does not have the `lsfMPTCanPrivacy` flag enabled (and is not enabling it in this transaction).
  - **Circulation Lock:** The transaction attempts to upload keys, but the `sfConfidentialOutstandingAmount` field is already present (tokens are already in circulation).

### 11.4. State Changes

If successful:

- **Flags:** The `lsfMPTCanPrivacy` flag is updated (if mutable).
- **Keys:** The `sfIssuerElGamalPublicKey` and/or `sfAuditorElGamalPublicKey` are stored on the `MPTokenIssuance` ledger entry.

## 12. Auditability & Compliance

The Confidential MPT model is designed to provide robust privacy for individual transactions while ensuring both the integrity of the total token supply and a high degree of flexibility for regulatory compliance and auditing.

To achieve this balance, this protocol offers flexible auditability through two distinct mechanisms. The primary method is on-chain selective disclosure, where each confidential balance is dually encrypted under a designated auditor's public key, allowing for independent, trust-minimized verification. This model is also designed for dynamic, forward-looking compliance; if a new auditor or party requires access later, the issuer can re-encrypt existing balances under the new key and provide cryptographic equality proofs to grant them access without disrupting the system or sharing existing keys. As a simpler, trust-based alternative, the protocol also supports an issuer-mediated model using view keys. In this approach, the issuer controls a separate set of keys that provide read-only access and can be shared directly with auditors on an as-needed basis.

The technical foundation for both of these models is a multi-ciphertext architecture, where each confidential balance is maintained under several different public keys (e.g., holder, issuer, and optional auditor) to serve these distinct purposes.

### **Mechanism 1: On-Chain Selective Disclosure (A Trust-Minimized Approach)**

The primary method for compliance is on-chain selective disclosure, which provides cryptographically enforced auditability directly on the ledger.

- Auditor-Specific Encryption: When an AuditorPolicy is active, each confidential balance is dually encrypted under the designated auditor's public key and stored in the EncryptedBalanceAuditor field on the ledger.
- Independent Verification: This allows the auditor to use their own private key to independently decrypt and verify any holder's balance at any time, without needing cooperation from the issuer or the holder.
- Dynamic, Forward-Looking Compliance: This model is designed for flexibility. If a new auditor or regulatory body requires access after the token has been issued, the issuer can facilitate this without disrupting the system. The process is as follows:
  1. The issuer uses its private key to decrypt its own on-ledger copy of a holder's balance (EncryptedBalanceIssuer).
  2. The issuer then re-encrypts this balance under the new auditor’s public key.
  3. Finally, the issuer provides the new ciphertext to the auditor along with a ZK equality proof that cryptographically proves that the new ciphertext matches the official on-ledger version.

This powerful re-encryption capability enables targeted, on-demand compliance without ever sharing the issuer's private key or making user balances public.

### **Mechanism 2: Issuer-Mediated Auditing (A Simple View Key Model)**

As a simpler, trust-based alternative, the protocol also supports an issuer-mediated model using **view keys**.

- **Issuer-Controlled Keys**: In this approach, the issuer controls a separate set of "view keys." All confidential balances and transaction amounts are also encrypted under these keys.
- **On-Demand Disclosure**: When an audit is required, the issuer can share the relevant view key directly with an auditor or regulator. This key grants the third party **read-only access** to view the necessary confidential information.
- **Trust Assumption**: This model is operationally simpler but requires the auditor to trust that the issuer is providing the correct and complete set of view keys for the scope of the audit.

**Foundational Elements for Public Integrity**

Both compliance models are built upon foundational elements that ensure the integrity of the total token supply remains publicly verifiable at all times.

- Issuer Ciphertexts (EncryptedBalanceIssuer): Every confidential balance is dually encrypted under the issuer's public key. This serves two critical functions:
  - It acts as the "master copy" that enables the issuer to perform the re-encryption required for dynamic selective disclosure.
  - It allows the issuer to monitor aggregate confidential circulation and reconcile it with public issuance.
- Confidential Outstanding Amount (COA): This plaintext field on the ledger tracks the aggregate total of all non-issuer confidential balances. It provides a global, public view of the confidential supply, allowing any observer to validate the system's most important invariant: OutstandingAmount ≤ MaxAmount.

**Example Audit Flows**

- Public Supply Audit (No Keys Required)
  1. An observer reads the public ledger fields: OA, COA, and MA.
  2. They validate the invariant OA ≤ MA.
  3. They can conclude that the total supply is within its defined limits without seeing any individual balances.
- Selective Disclosure Audit (Auditor Uses Own Key)
  1. A regulator is designated as an auditor under the on-chain policy.
  2. The auditor fetches a holder’s ledger object and uses their own private key to decrypt the EncryptedBalanceAuditor field, revealing the holder's confidential balance.
  3. This balance can be cross-checked against the global COA for consistency.
- View Key Audit (Issuer Provides Key)
  1. A regulator requests access to a user's transaction history.
  2. The issuer provides the regulator with the appropriate view key.
  3. The regulator uses the view key to decrypt the relevant confidential balances and transaction amounts.

## 13. Privacy Properties

Confidential MPT transactions are designed to minimize information leakage while preserving verifiability of supply and balances. Validators and external observers see only ciphertexts and ZKPs and never learn the underlying amounts except where amounts are already revealed in XLS-33 semantics.

**Publicly Visible Information**

- Transaction type (ConfidentialMPTConvert, ConfidentialMPTSend, etc.).
- Involved accounts (Account, Issuer, Destination).
- Currency code (e.g., "USD").
- Ciphertexts (ElGamal pairs under holder, issuer, optional auditor keys).
- ZKPs (non-interactive proofs of correctness).
- For issuer funding (Convert → second account): Amount is revealed, consistent with visible mint events in XLS-33.

**Hidden Information**

- Amounts moved in ConfidentialMPTSend, ConfidentialMerge.
- Holder balances (except their public balance field).
- Distribution of confidential supply across holders.

**Transaction-Type Privacy Notes**

- Convert (holder):
  - Public → Confidential: Amount is revealed once, but only as a conversion event.
  - Thereafter, spending is hidden.
  - OA unchanged, COA ↑.
- Convert (issuer → second account):
  - Amount visible (already disclosed in XLS-33 issuance).
  - Confidential balance seeded in the second account.
  - OA ↑, COA ↑.
- Send:
  - No amounts revealed.
  - OA unchanged, COA unchanged.
- Merge:
  - No amounts revealed.
  - OA unchanged, COA unchanged.
- Convert back (second account):
  - Amount revealed (issuer reserve increases).
  - OA ↓, COA ↓, IPB ↑.
- Convert back (holder):
  - Amount revealed.
  - OA unchanged, COA ↓, HPB ↑.

## 14. Security Considerations

Confidential MPTs introduce cryptographic mechanisms that require careful validation and enforcement. This section summarizes key security invariants, proof requirements, and considerations against potential attack vectors.

### Proof Requirements

Every confidential transaction must carry appropriate ZKPs:

- Convert: Equality proof that Amount is consistently encrypted under holder and issuer keys.
- Send: Range proof (balance ≥ transfer amount) and equality proof (ciphertexts match across holder/issuer/auditor keys).
- Optional auditor keys: Additional equality proofs binding auditor ciphertexts to the same plaintext.

### Confidential Balance Consistency

- Each confidential balance entry maintains parallel ciphertexts:
- Holder key (spendable balance).
- Issuer key.
- Auditor key(s), if enabled.
- Validators require a proof that all ciphertexts encrypt the same plaintext, preventing divergence between views.

### Issuer Second Account Model

- Issuer must use a designated second account for confidential issuance.
- Prevents redefinition of OA semantics and keeps compatibility with XLS-33.
- Validators enforce that direct confidential issuance from the issuer account is invalid.

### Privacy Guarantees

- Transaction amounts are hidden in all confidential transfers except:
  - Issuer mint events (already visible in legacy MPTs).
  - Conversion from public → confidential, where only the converted amount is disclosed once.
- Redistribution among holders (including issuer’s second account) leaks no amounts.

### Auditor & Compliance Controls

- If AuditorPolicy is enabled, ciphertexts under auditor keys must be validated with equality proofs.
- Prevents issuers from selectively encrypting incorrect balances for auditors.
- Selective disclosure allows compliance without undermining public confidentiality.

### Attack Surface & Mitigations

- Replay attacks: Transactions bound to unique ledger indices/versions; proofs must include domain separation.
- Malformed ciphertexts: Validators reject invalid EC points.
- Balance underflow: Range proofs prevent spending more than available.
- Auditor collusion: Auditors see balances only if granted view keys; public supply integrity remains trustless.
- Issuer misbehavior: Enforced by supply invariants and public COA/OA/MA checks.

## 15. Analysis of Transaction Cost and Performance

The efficiency is critical to the viability of Confidential MPTs. This analysis compares potential methods for range proofs to determine their impact on transaction size and overall performance.

### Foundational Assumptions

First, let's establish the size of our basic cryptographic building blocks.

- Curve: secp256k1
- Scalar: An integer modulo the curve order, which is 32 bytes for secp256k1.
- Compressed EC Point: A point on the curve represented by its x-coordinate and a prefix byte, totaling 33 bytes.
- EC-ElGamal Ciphertext: A pair of EC points (C1​,C2​), resulting in 2×33=66 bytes.

We will use the ConfidentialMPTSend transaction as our benchmark, as its cryptographic payload is the most complex:

- 3 Ciphertexts (Sender, Receiver, Issuer): 3×66 \= 198 bytes.
- 2 Public Keys (Sender, Receiver): 2×33 \= 66 bytes.
- Equality Proofs: Proofs that all ciphertexts encrypt the same amount, totaling 196 bytes.
- Range Proof: The proof that the hidden amount is non-negative.

Option 1: Decomposition Range Proof  
This method involves breaking the amount into its individual bits and generating a separate proof for each bit to show it is either 0 or 1. The proof size is linear to the number of bits.

1a: Using 64-bit Values

- Total Range Proof Size: For a 64-bit amount, the size is 64 bits×130 bytes/bit≈8,320 bytes (8.1 kB).
- Total Crypto Payload: 198(ciphertexts)+66(keys)+194(equality)+8,320(range)≈8.8 kB.
- Performance Impact: An overhead of nearly 9 kB is extremely large and generally considered impractical for production systems due to high fees and network load.

1b: Using 40-bit Values  
Reducing the bit length provides a significant, but insufficient, size reduction.

- Total Range Proof Size: For a 40-bit amount, the size is 40 bits×130 bytes/bit=5,200 bytes (5.1 kB).
- Total Crypto Payload: 198(ciphertexts)+66(keys)+194(equality)+5,200(range)≈5.7 kB.
- Performance Impact: While a 35% reduction from the 64-bit version, a payload of over 5 kB is still far too large to be viable on a high-performance ledger.

Option 2: Bulletproofs  
Bulletproofs are a modern ZKP system designed for efficiency, with proof sizes that grow logarithmically with the number of bits (O(logn)).

#### Using 64-bit Values

- Total Range Proof Size: A Bulletproof for a 64-bit value is highly compact, estimated at \~650 bytes.
- Equality proofs are ~200 bytes
- Total Crypto Payload: 198 (ciphertexts) + 66 (keys) + 850 (proofs) ≈ 1100 bytes.
- Performance Impact: An overhead of ~ 1.1 kB is efficient and viable. The one-time computational cost to verify is a widely accepted trade-off for the enormous savings in data size.
  - Note on 40-bit values: Bulletproofs require a bit length that is a power of two. A 40-bit proof would need to be padded to 64 bits, offering no size savings over a native 64-bit proof.

Summary

| Metric                              | Decomposition (64-bit)              | Decomposition (40-bit)              | Bulletproofs (64-bit)                                                                                                                   |
| :---------------------------------- | :---------------------------------- | :---------------------------------- | :-------------------------------------------------------------------------------------------------------------------------------------- |
| Proof Size Complexity               | O(n) \- Linear                      | O(n) \- Linear                      | O(logn) \- Logarithmic                                                                                                                  |
| Total Crypto Payload                | \~8.8 kB                            | \~5.7 kB                            | \~ 1100 bytes                                                                                                                           |
| Computational Complexity (Prover)   | 256 scalar multiplications          | 160 scalar multiplications          | 128 scalar multiplications                                                                                                              |
| Computational Complexity (Verifier) | 256 separate scalar multiplications | 160 separate scalar multiplications | 2log2​(n)+c scalar multiplications (c is a small constant). For a 64-bit value, \~17 terms, plus 2-3 individual scalar multiplications. |

Bulletproofs are an efficient choice. Even when reducing the bit length, the decomposition approach results in a transaction payload that is over 6 times larger than a Bulletproof.

## 16. Frequently Asked Questions (FAQ)

This section addresses common questions about Confidential MPTs and their design choices, ranging from basic functionality to advanced research topics.

Q1. Can confidential and public balances coexist?\
Yes, both issuers and holders may simultaneously maintain both public and confidential balances of the same MPT, fully supporting hybrid ecosystems with explicit conversions between the two using ConfidentialMPTConvert transactions.

Q2. Why introduce a separate Merge transaction?\
A separate Merge transaction is introduced because incoming transfers could cause proofs to become stale if all balances were in a single field, while split balances (CB_S and CB_IN) isolate proofs to a stable spending balance, allowing the Merge transaction to consolidate funds deterministically and update the version counter without requiring a proof, making it cheap to validate.

Q3. What happens if a user forgets to merge their inbox?\
If a user forgets to merge their inbox, incoming funds will accumulate in CB_IN, remaining safe but unable to be spent until they are consolidated into CB_S via a merge, therefore wallets are expected to perform this merge before a send if necessary.

Q4. Can confidential transactions be used in DEX, escrow, or checks?\
No, this version of confidential MPT extensions focuses solely on regular confidential MPT payments between accounts, as integration with XRPL’s DEX, escrow, or checks would require further research into how to represent offers or locked balances without revealing their amounts.

Q5. How does compliance fit in?\
Compliance is supported by storing each confidential balance as parallel ciphertexts under the holder’s key (CB_S/CB_IN), the issuer’s key (EncryptedBalanceIssuer), and an optional auditor’s key (EncryptedBalanceAuditor) if enabled, with ZKPs ensuring all ciphertexts encrypt the same value, allowing the public to verify supply limits via issuer ciphertexts and auditors to decrypt balances if permitted.

Q6. What happens if a holder loses their ElGamal private key?\
If a holder loses their ElGamal private key, they will be unable to decrypt or spend their confidential balances, which will remain valid on-ledger but are effectively locked and irrecoverable by that holder.

Q7. What prevents replay or proof reuse?\
Replay and proof reuse are prevented because all ZKPs are transcript-bound with domain separation, meaning the binding includes transaction type, issuer, currency, and version counters, so attempting to replay a proof in another context will result in a failed verification.

Q8. Are confidential transactions more expensive than standard MPT transactions?\
Yes, confidential transactions are more expensive than standard MPT transactions as they include extra ciphertexts and ZKPs, which increase both transaction size and verification cost, though efficiency remains a design goal with lightweight proofs and future aggregation possibilities.

Q9. What happens if validators cannot verify a ZKP?

If validators cannot verify a ZKP, the transaction is rejected during consensus, functioning identically to an invalid signature and thus preventing malformed or incorrect confidential balances from entering the ledger.

Q10. Why does the issuer need a second account?

The issuer utilizes a second account as a designated holder account to convert their public reserve into the confidential supply. This approach is primarily used to keep the existing XLS-33 semantics intact, ensuring that the OutstandingAmount accurately reflects non-issuer balances.

Q11. Will proofs be optimized in future versions?

The current design employs separate range and equality proofs for each transaction. However, future work will definitely prioritize optimizing these proofs to significantly reduce both transaction size and the associated verification cost for validators. Thorough benchmarking will be essential to find the right balance between validator performance and overall user experience.

Q12. Can there be more than one auditor?

At present, the protocol supports only a single, optional AuditorPolicy. Future extensions could explore multi-auditor setups, potentially leveraging advanced cryptographic techniques such as threshold encryption or more sophisticated policy-driven key distribution mechanisms.

Q13. Is the system quantum-safe?

Today's design relies on EC-ElGamal over secp256k1, which is not considered quantum-safe. The long-term plan includes migrating to post-quantum friendly schemes, such as those based on lattice cryptography. The specific migration path and timeline for achieving quantum resistance remain an open area of research.

Q14. Why require explicit Merge instead of eliminating it in future?

The explicit MergeInbox transaction is currently required because it deterministically solves the issue of "staleness," ensuring that all received funds are consolidated before spending. While issuers and wallets might prefer less operational overhead, the current design offers clear, verifiable guarantees. Future designs may revisit whether we can eliminate this explicit merge requirement.

## Acknowledgements

We would like to thank David Schwartz, Ayo Akinyele, Kenny Lei, Shashwat Mittal, and Shawn Xie for their invaluable feedback and insightful discussions which improved this specification.
