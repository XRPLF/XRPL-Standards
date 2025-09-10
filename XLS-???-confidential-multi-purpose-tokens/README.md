


<pre>
    title: Confidential Multi-Purpose Tokens for XRPL
    description: This amendment introduces Confidential Multi-Purpose Tokens on the XRP Ledger.
    author: Murat Cenk and Aanchal Malhotra 
    status: Discussion
    category: Amendment
    created: 2025-09-10
</pre>
#  Confidential Multi-Purpose Tokens for XRPL
## 1\. Abstract

This specification introduces Confidential Multi-Purpose Tokens (MPTs) on the XRP Ledger. Confidential MPTs provide confidential transfers and balances using EC-ElGamal encryption and Zero-Knowledge Proofs (ZKPs), while preserving XLS-33 semantics:

* Confidentiality: Individual balances and transfer amounts are encrypted.  
* Public auditability: Issuance limits are enforced by the existing OutstandingAmount ≤ MaxAmount rule.  
* Selective disclosure/view keys: The protocol offers flexible auditability through two distinct models. The primary mechanism provides trust-minimized, on-chain verification for pre-defined auditors and is extensible, allowing for the dynamic addition of new parties later via re-encryption. A simpler, trust-based alternative is also supported using issuer-controlled view keys for on-demand access.  
* Compatibility: Public and confidential balances coexist, with the second issuer account treated identically to other holders.  
* Issuer Control: Includes issuer-only mechanisms for freezing balances and clawing back funds directly to the issuer's reserve.

This design aligns naturally with [XLS-33](https://github.com/XRPLF/XRPL-Standards/tree/master/XLS-0033-multi-purpose-tokens) by keeping OutstandingAmount defined as the sum of all non-issuer balances. Supply consistency is enforced directly by validators, and confidentiality is achieved at the transaction level through equality and range proofs.

## 2\. Motivation

XLS-33 enables flexible tokenization on the XRP Ledger, but all balances and transfers remain publicly visible. This transparency limits adoption in institutional and privacy-sensitive contexts. Confidential MPTs address this gap by introducing encrypted balances and confidential transfers while preserving XLS-33 semantics.

The design uses a second-account model, where the issuer maintains a designated account treated as a regular holder. This keeps the definition of OutstandingAmount (OA) exactly as in XLS-33, the sum of all non-issuer balances, now including the issuer’s second account. A complementary value, ConfidentialOutstandingAmount (COA), tracks the confidential portion of circulation and MaxAmount (MA) continues to cap supply. By modeling confidential issuance through the second account rather than redefining OA, validators can enforce supply consistency with the existing invariant OA ≤ MA. 

### Benefits

* Confidentiality: Hides individual balances and transfer amounts using EC-ElGamal encryption and ZKPs.  
* Auditability: Public auditability is preserved via XLS-33’s existing OA semantics.  
* Flexible Compliance: Enables selective disclosure through multiple mechanisms, including a trust-minimized on-chain model and a simpler issuer-controlled view key model.  
* Compatibility: Maintains backward compatibility with XLS-33 by treating the issuer’s second account as a standard holder.  
* Enhanced Issuer Control: Provides optional Freeze and a Clawback transaction, giving issuers the tools needed to manage assets and enforce compliance.

## 3\. Scope

This XLS specifies the protocol changes required to support confidential MPTs, including: 

### New Transaction Types

* ConfidentialMPTConvert: Converts public MPT balances into encrypted form for a holder.  
* ConfidentialMPTSend: Confidential transfer of tokens between accounts, with encrypted amounts validated by ZKPs.  
* ConfidentialMPTMergeInbox: Merges a holder’s inbox balance into their spending balance, preventing stale-proof issues.  
* ConfidentialMPTConvertBack: Converts confidential balances back into public form, restoring visible balances or returning funds to the issuer’s reserve.  
* ConfidentialMPTClawback: An issuer-only transaction to forcibly convert a holder’s confidential balance back to the issuer's public reserve.

### New Ledger Fields and Objects
MPTokenIssuance Extensions: To support confidential MPTs, the MPTokenIssuance ledger object is extended with two new flags and three new fields. These serve as the global configuration and control settings for the token's confidential features.

New Flags:  
* lsfConfidential: If set, indicates that confidential transfers and conversions are enabled for this token issuance.  
* lsfConfidentialImmutable: If set, the lsfConfidential flag can never be changed after the token is issued, permanently locking the confidentiality setting.

New Fields:

* IssuerElGamalPublicKey: (Optional) A string containing the issuer’s 33-byte compressed ElGamal public key. This field is required if the lsfConfidential flag is set.  
* ConfidentialOutstandingAmount: (Required if lsfConfidential is set) The total amount of this token that is currently held in confidential balances. This value is adjusted with every ConfidentialMPTConvert and ConfidentialMPTClawback transaction.  
* AuditorPolicy: (Optional) An object containing the configuration for an on-chain auditor, including their public key and an immutability flag.

Managing Confidentiality Settings via MPTokenIssuanceSet:

The MPTokenIssuanceSet transaction is used by the issuer to manage the lsfConfidential flag and associated fields.\
* Initial Setup: When creating an MPTokenIssuance object, the issuer defines the initial state of lsfConfidential and lsfConfidentialImmutable. If lsfConfidential is set to true, IssuerElGamalPublicKey and ConfidentialOutstandingAmount (initialized to 0) become mandatory fields.\
* Modifying lsfConfidential: If lsfConfidentialImmutable is not set (false), the issuer can later use an MPTokenIssuanceSet transaction to change the lsfConfidential flag:
  * Enabling Confidentiality (false → true): The MPTokenIssuanceSet transaction must provide the IssuerElGamalPublicKey and initialize ConfidentialOutstandingAmount if they are not already present.
  * Disabling Confidentiality (true → false): This action is only permitted if the ConfidentialOutstandingAmount (COA) is 0. If any confidential funds are outstanding, the transaction will be rejected to prevent funds from being permanently locked. When disabling, the IssuerElGamalPublicKey and AuditorPolicy fields become optional and can be removed by a subsequent MPTokenIssuanceSettransaction.

MPToken Extensions: Extends per-account MPT objects with confidential balance fields:

  * ConfidentialBalance\_Spending (CB\_S): Encrypted spendable balance under the holder’s key.  
  * ConfidentialBalance\_Inbox (CB\_IN): Encrypted incoming balance under the holder’s key.  
  * CB\_S\_Version: Monotonically increasing version number for CB\_S.  
  * EncryptedBalanceIssuer: Same spendable balance encrypted under the issuer’s key (audit consistency).  
  * EncryptedBalanceAuditor (optional): Same balance encrypted under an auditor’s key.  
  * HolderElGamalPublicKey: Holder’s ElGamal public key.  
  * AuditorPublicKey (optional): Auditor’s ElGamal public key.  
 

### Proof System

The protocol relies on a ZKP system to validate confidential transactions without revealing sensitive data. Key proofs include:

* Equality Proofs: To ensure that values are consistent across different ciphertexts (e.g., for the sender, receiver, and issuer).  
* Range and Balance Sufficiency Proofs: To prove that a hidden transfer amount is a valid, non-negative value and does not exceed the sender's spendable balance.

## 4\. Definitions & Terminology

* MPT (Multi-Purpose Token): A token standard defined by XLS-33. Extended here to support confidential balances and transfers.  
* MPTokenIssuance (Object): Ledger object storing metadata for an MPT, including Currency, Issuer, MaxAmount (MA), and OutstandingAmount (OA).  
    
* MPToken (Object): Ledger object representing a holder’s balance of a given MPT. Extended to include confidential balance fields:  
  
* Second Account (Issuer-as-Holder): A designated account controlled by the issuer but treated as a holder.  
  * Included in OA (as a non-issuer balance).  
  * Included in COA (if confidential).  
  * Used to issue confidential balances into circulation without redefining OA.  
* OutstandingAmount (OA): Total of all non-issuer balances (public \+ confidential), including the issuer’s second account.  
* ConfidentialOutstandingAmount (COA): Total of all confidential balances of non-issuers, including the issuer’s second account.  
* MaxAmount (MA): Maximum allowed token supply. Invariant: OA ≤ MA.  
* EC-ElGamal Encryption: Public-key encryption scheme with additive homomorphism. Used for encrypted balances and homomorphic updates.  
* Balance Proofs: ZKPs proving that confidential transfers are valid:  
  * Equality proofs ensure ciphertexts represent the same amount under different keys.  
  * Range proofs ensure transferred amounts are non-negative and ≤ balance.  
* Split-Balance Model: Confidential balances divided into:  
  * Spending (CB\_S): Stable, used in proofs.  
  * Inbox (CB\_IN): Receives new transfers, merged into CB\_S explicitly. Prevents stale-proof rejection.  
* Auditor Policy: Optional issuance-level configuration that allows balances to be encrypted under an auditor’s key for selective disclosure.  
* Freeze: An issuer-initiated action using the TrustSet transaction. This action sets the ConfidentialBalanceFrozen flag on the holder's MPToken object, preventing them from executing ConfidentialMPTSend or ConfidentialMPTConvertBack transactions.  
* Clawback: A privileged process initiated by the issuer via a ConfidentialMPTClawback transaction. It uses a ZKP to verifiably convert a holder's total confidential balance (spending \+ inbox) directly into the issuer's public reserve, ensuring the ledger's accounting remains consistent.

## 5\. Protocol Overview

The Confidential MPT protocol is built on three core design principles: the Issuer Second Account model, the Split-Balance Model for reliable transfers, and a Multi-Ciphertext Architecture for privacy and compliance.

**The Issuer Second Account Model:** To introduce confidential tokens without altering the fundamental supply rules of XLS-33, the protocol uses an issuer-controlled second account. This account is treated by the ledger as a standard, non-issuer holder.

* Issuing into Circulation: The issuer creates new confidential supply by executing a public ConfidentialMPTConvert transaction, moving funds from its public reserve to this second account.  
* Preserving Invariants: Because the second account is a non-issuer, its balance is counted in OA. This elegantly preserves the existing OA ≤ MA invariant, allowing validators to enforce the supply cap without needing to decrypt any confidential data. All subsequent confidential transfers between holders are simply redistributions that do not change the OA.

**The Split-Balance Model:** To solve the "stale proof" problem where an incoming transfer could invalidate a user's just-created proof for an outgoing transfer. Each account's confidential balance is split into two parts:

* Spending Balance (CB\_S): A stable balance used to generate proofs for outgoing ConfidentialMPTSend transactions.  
* Inbox Balance (CB\_IN): A separate balance that receives all incoming transfers.  
* Merging: Users explicitly merge their Inbox into their Spending balance using the proof-free ConfidentialMPTMergeInbox transaction. Each merge increments a version number (CB\_S\_Version), which is bound to new proofs to prevent replays and ensure proofs always reference a known, stable balance.

**The Multi-Ciphertext Architecture:** A single confidential balance is represented by multiple parallel ciphertexts, each serving a distinct purpose. ZK equality proofs are the cryptographic glue that guarantees all of these ciphertexts represent the exact same hidden amount.

* Holder Encryption: The primary balance is encrypted under the holder's key, giving them sole control over spending their funds.  
* Issuer Encryption: The same balance is also encrypted under the issuer's key (EncryptedBalanceIssuer). This serves as a "master copy," allowing the issuer to monitor aggregate supply and facilitate audits without being able to spend the funds.  
* Optional Auditor Encryption: If an AuditorPolicy is active, the balance is also encrypted under an auditor's key (EncryptedBalanceAuditor). This enables on-chain selective disclosure, where the auditor can independently verify balances. The issuer can also use its master copy to re-encrypt balances for new auditors on-demand, providing forward-looking compliance.

## 6\. Transaction Types

### ConfidentialMPTConvert

**Purpose**: Converts a visible (public) MPT balance into confidential form. By default, the converted amount is credited to the holder’s Inbox (CB\_IN) to avoid staleness. For issuer funding, this transaction discloses the plaintext Amount while delivering confidential value to the second account (treated as a holder). Both OA and COA remain maintained in plaintext.

#### Use Cases

* Holder → self (public → confidential): public balance decreases, confidential balance increases; OA unchanged, COA increases (both in plaintext).  
* Issuer → second account (public → confidential): issuer’s public reserve decreases, second account’s confidential balance increases; OA increases (plaintext), COA increases (plaintext).  
* Supports hybrid circulation where tokens can exist both publicly and confidentially.

#### Transaction Fields

| Field | Required | JSON Type | Description |
| :---- | :---- | :---- | :---- |
| TransactionType | Yes | String | Must be "ConfidentialMPTConvert". |
| Account | Yes | String | The account initiating the conversion. |
| MPTokenIssuanceID | Yes | String | The unique identifier for the MPT being converted. |
| Amount | Yes | String | Public (visible) amount to convert into a confidential balance. |
| HolderElGamalPublicKey | Conditional | String | Required if Account is not the Issuer. |
| EncryptedAmountForHolder | Conditional | Object | Ciphertext under the holder’s key. Required if Account is not the Issuer. |
| Receiver | Conditional | String | The issuer’s second account. Required if Account is the Issuer. |
| ReceiverElGamalPublicKey | Conditional | String | The public key of the Receiver. Required if Account is the Issuer. |
| EncryptedAmountForReceiver | Conditional | Object | Ciphertext under the Receiver’s key. Required if Account is the Issuer. |
| EncryptedAmountForIssuer | Yes | Object | An audit-mirror ciphertext for the issuer, encrypted with the issuer's key. |
| ZKProof | Yes | Object | A Zero-Knowledge Proof validating the conversion. |

#### Ledger Changes

* Holder → self (public → confidential)  
  * MPToken.Balance \-= Amount (public ↓).  
  * Confidential balance increases:  
    * Else (default):  
      * CB\_IN ⊕= EncryptedAmountForHolder  
  * EncryptedBalanceIssuer ⊕= EncryptedAmountForIssuer  
  * Add HolderElGamalPublicKey if absent.  
    Public ↓, Confidential ↑, OA unchanged (plaintext), COA ↑ (plaintext).  
* Issuer → second account (public → confidential)  
  * IssuerPublicBalance \-= Amount (public ↓).  
  * On receiver’s MPToken (second account):  
    * CB\_IN ⊕= EncryptedAmountForReceiver  
    * EncryptedBalanceIssuer ⊕= EncryptedAmountForIssuer  
    * Add ReceiverElGamalPublicKey if absent.  
      Issuer public ↓, Second account confidential ↑, OA ↑ (plaintext), COA ↑ (plaintext).

#### Validator Checks 

Here is the unified list of checks.  
1. Common Checks (Always Performed): These rules are validated first, regardless of the path.
   * Verify Amount: Check that the Amount ≥ 0 and conforms to standard XRPL and XLS-33 formatting rules.  
   * Verify Confidentiality is Enabled: Confirm that the ConfidentialTransfersEnabled flag is set to true on the token's MPTokenIssuance object.  
   * Verify Ciphertext Formatting: Ensure all provided ciphertext fields (e.g., EncryptedAmountForIssuer, etc.) contain valid, well-formed EC points.

2. Path-Specific Checks (Conditional): The validator then checks if the Account sending the transaction is also the Issuer to determine which path's rules to apply.  
   * If Account ≠ Issuer (Holder Path)  
   This path is for a regular holder converting their public tokens to confidential.
      * Check for Required Fields: Verify that HolderElGamalPublicKey and EncryptedAmountForHolder are present in the transaction.  
      * Check Sufficient Public Balance: Ensure the holder has enough public funds for the conversion (Amount ≤ holder's public MPToken.Balance).  
      * Verify Zero-Knowledge Proof: The ZKProof must prove that the plaintext Amount correctly encrypts to both the EncryptedAmountForHolder and the EncryptedAmountForIssuer ciphertexts. 
   * If Account = Issuer (Issuer Path): This path is for the issuer creating new confidential supply by funding their second account.
     * Check for Required Fields: Verify that Receiver, ReceiverElGamalPublicKey, and EncryptedAmountForReceiver are present.  
     * Check Supply Limit: Ensure the conversion does not exceed the token's maximum supply (Amount ≤ MaxAmount \- OutstandingAmount).  
     * Enforce No Self-Funding: The Receiver address must not be the same as the Issuer address.  
     * Verify Zero-Knowledge Proof: The ZKProof must prove that the plaintext Amount correctly encrypts to both the EncryptedAmountForReceiver and the EncryptedAmountForIssuer ciphertexts.

#### Example A — Holder converts 150 units (default → Inbox)

```json
{
  "TransactionType": "ConfidentialMPTConvert",
  "Account": "rBob",
  "Issuer": "rAlice",
  "Currency": "USD",
  "Amount": "150",
  "HolderElGamalPublicKey": "pkBob...",
  "EncryptedAmountForHolder": { "A": "...", "B": "..." },
  "EncryptedAmountForIssuer": { "A": "...", "B": "..." },
  "ZKProof": { "zkp_bytes_here" }
}
```

#### Example B — Issuer funds second account confidentially

```json
{
  "TransactionType": "ConfidentialMPTConvert",
  "Account": "rAlice",
  "Issuer": "rAlice",
  "Currency": "USD",
  "Amount": "500",
  "Receiver": "rIssuerSecondAcct",
  "ReceiverElGamalPublicKey": "pkSecond...",
  "EncryptedAmountForReceiver": { "A": "...", "B": "..." },
  "EncryptedAmountForIssuer": { "A": "...", "B": "..." },
  "ZKProof": { "zkp_bytes_here" }
}
```

### ConfidentialMPTSend

**Purpose:** Confidential transfer of MPT value between accounts while keeping the amount hidden. Receiver is credited to Inbox (CB\_IN) to avoid staleness; the receiver later merges to Spending (CB\_S).

#### Use Cases

* Holder → holder (including second account): confidential redistribution with hidden amount.  
* Second account → holder (or holder → second account): confidential redistribution inside non‑issuers.  
* Not for issuer funding: issuer must not use ConfidentialMPTSend to initially fund the second account; use ConfidentialMPTConvert instead (to update OA in plaintext).

#### Transaction Fields

| Field | Required | JSON Type | Internal Type | Description                                                                                                                                                            |
| :---- | :---- | :---- | :---- |:-----------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| TransactionType | Yes | String | UInt16 | Must be "ConfidentialMPTSend".                                                                                                                                         |
| Account | Yes | String | AccountID | The sender's account address.                                                                                                                                          |
| MPTokenIssuanceID | Yes | String | UInt256 | The unique identifier for the MPT being converted.                                                                                                                     |
| Receiver | Yes | String | AccountID | The recipient's account address.                                                                                                                                       |
| EncryptedAmountForSender | Yes | Object | Struct (EC Point Pair) | EC-ElGamal ciphertext for the sender, representing a debit to their balance.                                                                                           |
| EncryptedAmountForReceiver | Yes | Object | Struct (EC Point Pair) | EC-ElGamal ciphertext for the receiver, representing a credit to their balance.                                                                                        |
| EncryptedAmountForIssuer | Yes | Object | Struct (EC Point Pair) | EC-ElGamal ciphertext for the issuer, used for auditing purposes.                                                                                                      |
| EncryptedAmountForAuditor | Optional | Object | Struct (EC Point Pair) | EC-ElGamal ciphertext for a designated auditor, if an audit policy is active.                                                                                          |
| AuditorPublicKey | Conditional | String | Blob (EC Point) | The auditor's public key. Required if EncryptedAmountForAuditor is present.                                                                                            |
| ZKProof | Yes | Object | Blob | A ZKP that validates the entire transaction, ensuring the amount is positive, within the sender's balance, and that all ciphertexts are consistent. |

#### Ledger Changes

* Sender (holder)  
  * ConfidentialBalance\_Spending ⊖= EncryptedAmountForSender  
  * CB\_S\_Version \+= 1  
* Receiver (holder)  
  * ConfidentialBalance\_Inbox ⊕= EncryptedAmountForReceiver  
  * EncryptedBalanceIssuer ⊕= EncryptedAmountForIssuer
* OA / COA effects (plaintext accounting)  
  * Holder ↔ holder (including second account): Public balances unchanged; OA unchanged, COA unchanged (pure redistribution inside non‑issuers).  
  * Issuer involved as sender: Not allowed (would change OA without plaintext disclosure). Use ConfidentialMPTConvert instead.

### Validator Checks

1. Prerequisites and Account Rules: These are foundational checks to ensure the transaction is valid in its context.

   * Verify Issuance: Confirm that the token issuance defined by Issuer and Currency exists and has ConfidentialTransfersEnabled set to true.  
   * Enforce Sender Role: The sender (Account) must not be the Issuer. The issuer must use ConfidentialMPTConvert to fund its second account, not this transaction type.  
   * Verify Accounts: Check that both the Account and Receiver are valid, distinct addresses on the ledger.

2. Field Presence and Formatting: These checks validate the structure and content of the transaction itself.

   * Check Required Fields: Ensure that all required fields are present, including EncryptedAmountForSender, EncryptedAmountForReceiver, and EncryptedAmountForIssuer. 
   * Validate Cryptographic Primitives: Verify that all provided public keys and ciphertexts are well-formed secp256k1 elliptic curve points.  
   * Validate Auditor Fields: If the optional EncryptedAmountForAuditor is included, the AuditorPublicKey field must also be present and must match the public key defined in the token's AuditorPolicy.

3. ZKP Verification: The validator must confirm that the ZKProof correctly proves all of the following:

   * Sufficient Balance (Range Proof): The hidden transfer amount is greater than zero and less than or equal to the sender's current confidential spending balance (0 \< amount ≤ CB\_S).  
   * Value Equality: All provided ciphertexts (EncryptedAmountForSender, EncryptedAmountForReceiver, EncryptedAmountForIssuer, and EncryptedAmountForAuditor if present) encrypt the exact same hidden amount.  
   * Replay Protection (Transcript Binding): The proof is cryptographically bound to the unique details of this transaction including the sender's current spending balance version (CB\_S\_Version) to prevent the proof from being reused in a replay attack.

Example — Holder → Holder (with auditor)

```json
{
  "TransactionType": "ConfidentialMPTSend",
  "Account": "rBob",
  "Issuer": "rAlice",
  "Currency": "USD",
  "Receiver": "rCarol",

  "EncryptedAmountForSender":   { "A": "...", "B": "..." },
  "EncryptedAmountForReceiver": { "A": "...", "B": "..." },
  "EncryptedAmountForIssuer":   { "A": "...", "B": "..." },
  "EncryptedAmountForAuditor":  { "A": "...", "B": "..." },

  "SenderElGamalPublicKey":   "pkBob...",
  "ReceiverElGamalPublicKey": "pkCarol...",
  "AuditorPublicKey":         "pkAuditor...",
  "ZKProof": "zkp_bytes_here"
}
```

Net effect: Public balances unchanged; confidential amount is redistributed (sender CB\_S ↓, receiver CB\_IN ↑). OA (plaintext) unchanged; COA (plaintext) unchanged.

### ConfidentialMPTMergeInbox

**Purpose:** Moves all funds from the inbox balance into the spending balance, then resets the inbox to a canonical encrypted zero (EncZero). This ensures that proofs reference only stable spending balances and prevents staleness from incoming transfers.

#### Use Cases

* A holder merges newly received confidential transfers into their spendable balance.  
* The issuer merges its own inbox into the spending balance (applies to the second account).  
* Required periodically to combine funds before subsequent confidential sends.

#### Transaction Fields

| Field | Required | JSON Type | Internal Type | Description |
| :---- | :---- | :---- | :---- | :---- |
| TransactionType | Yes | String | UInt16 | Must be "ConfidentialMPTMergeInbox". |
| Account | Yes | String | AccountID | The account address performing the inbox merge. |
| MPTokenIssuanceID | Yes | String | UInt256 | The unique identifier for the MPT being converted. |

#### Ledger Changes

1. The ConfidentialBalance\_Spending (CB\_S) is updated by homomorphically adding the ConfidentialBalance\_Inbox (CB\_IN) to it.  
   * CB\_S ← CB\_S ⊕ CB\_IN  
2. The ConfidentialBalance\_Inbox (CB\_IN) is reset to a canonical, valid encryption of zero.  
   * CB\_IN ← EncZero(Account, Issuer, Currency)  
3. The spending balance version number is incremented to prevent replay attacks.  
   * CB\_S\_Version ← CB\_S\_Version \+ 1

All updates are homomorphic; global supply fields like OutstandingAmount (OA) and ConfidentialOutstandingAmount (COA) are unaffected by this operation.

#### Validator Checks

* (Issuer, Currency) issuance exists under XLS-33.  
* Target MPToken object exists or is created with required keys.  
* Operation is deterministic: no user-supplied ciphertexts, only canonical updates.  
* Domain separation enforced: transaction type is "ConfidentialMPTMergeInbox".

#### Rationale & Safety

* No value choice: ledger moves exactly the inbox, no risk of misreporting.  
* No ZKP needed: no proof obligation since the value is known to ledger state.  
* Staleness control: version bump invalidates any in-flight proofs tied to old CB\_S.  
* EncZero safety: inbox reset uses deterministic ciphertext of 0 so it remains a valid ElGamal ciphertext.

Canonical Encrypted Zero  
To ensure inbox fields always contain a valid ciphertext after reset:  
EncZero(Acct, Issuer, Curr): r = H("EncZero" || Acct || Issuer || Curr) mod n, curve order n\
return (R = r·G, S = r·Pk),  Pk: ElGamal public key of Acct

* Deterministic across validators (no randomness beacon).  
* Represents encryption of 0 under account’s key.  
* Keeps inbox proofs well-formed.

Example
```json
{
  "TransactionType": "ConfidentialMPTMergeInbox",
  "Account": "rBob",
  "Issuer": "rAlice",
  "Currency": "USD"
}
```

### ConfidentialMPTConvertBack

**Purpose**: Convert confidential into public MPT value.

* For a holder: restore public balance from CB\_S.  
* For the issuer’s second account: return confidential supply to issuer reserve.

**Accounting Effects:**

* Holder path: OA unchanged, COA ↓, IPB unchanged.  
* Second-account path: OA ↓, COA ↓, IPB ↑.

**Transaction Fields:**

| Field | Required | JSON Type | Internal Type | Description |
| :---- | :---- | :---- | :---- | :---- |
| TransactionType | Yes | String | UInt16 | Must be "ConfidentialMPTConvertBack". |
| Account | Yes | String | AccountID | The account converts funds from confidential back to public. |
| Issuer | Yes | String | AccountID | The address of the token issuer. |
| Currency | Yes | String | Currency | The token's currency code (e.g., "USD"). |
| Amount | Yes | String | Amount | The plaintext amount to be revealed and credited back to the public balance. |
| EncryptedAmountForAccount | Yes | Object | Struct (EC Point Pair) | Ciphertext showing the decrement from the account's confidential balance. |
| EncryptedAmountForIssuer | Yes | Object | Struct (EC Point Pair) | An audit-mirror ciphertext for the issuer, encrypted with the issuer's key. |
| EncryptedAmountForAuditor | Optional | Object | Struct (EC Point Pair) | Optional. A ciphertext for a designated auditor, if an audit policy is active. |
| ZKProof | Yes | Object | Blob | A bundle of ZKPs verifying that the revealed Amount matches the encrypted values and that the account had a sufficient confidential balance. |

**Ledger Changes**

A) Holder path (Account ≠ IssuerSecondAccount)

* CB\_S \ ⊖= EncryptedAmountForAccount  
* EncryptedBalanceIssuer \= EncryptedBalanceIssuer \- EncryptedAmountForIssuer  
* CB\_S\_Version \+= 1  
* MPToken.Balance \+= Amount (public balance restored)  
  Net: OA \=, COA ↓, IPB \=

B) Issuer second account path (Account \= IssuerSecondAccount)

* CB\_S ⊖= EncryptedAmountForAccount  
* EncryptedBalanceIssuer ⊖= EncryptedAmountForIssuer  
* EncryptedBalanceAuditor ⊖= EncryptedAmountForAuditor (if present)  
* CB\_S\_Version \+= 1  
* IssuerPublicBalance \+= Amount (issuer reserve restored)  
  Net: OA ↓, COA ↓, IPB ↑

### Validator Checks

1. Prerequisites and Basic Rules: These are the initial high-level checks for the transaction's context and validity.

   * Verify Issuance: Confirm that the token issuance defined by Issuer and Currency exists and has the ConfidentialTransfersEnabled flag set to true.  
   * Verify Amount: Check that the plaintext Amount is greater than 0 and conforms to standard XRPL formatting rules.

2. Field Presence and Formatting: These checks validate the structure and content of the transaction itself before performing expensive cryptographic operations.

   * Check Required Fields: Ensure that all required fields are present, including EncryptedAmountForAccount and EncryptedAmountForIssuer.  
   * Validate Cryptographic Primitives: Verify that all provided ciphertext fields are well-formed secp256k1 elliptic curve points.  
   * Validate Auditor Fields: If the optional EncryptedAmountForAuditor is included, verify that an AuditorPolicy is active for the token issuance.

3. ZKP Verification: The validator must confirm that the ZKProof bundle correctly proves all of the following claims:

   * Ciphertext-Plaintext Equality: The provided ciphertexts (EncryptedAmountForAccount, EncryptedAmountForIssuer, and EncryptedAmountForAuditor if present) all correctly encrypt the public plaintext Amount.  
   * Sufficient Balance: The Account has a sufficient confidential spending balance to cover the conversion (Amount ≤ CB\_S). This is proven without revealing the total balance.  
   * Replay Protection (Transcript Binding): The proof is cryptographically bound to the unique details of this transaction, including the Account's current spending balance version (CB\_S\_Version), to prevent replay attacks.

Example — Holder converts back 75 units

```json
{
  "TransactionType": "ConfidentialMPTConvertBack",
  "Account": "rBob",
  "Issuer": "rAlice",
  "Currency": "USD",
  "Amount": "75",

  "EncryptedAmountForAccount": { "A": "...", "B": "..." },
  "EncryptedAmountForIssuer":  { "A": "...", "B": "..." },

  "ZKProofs": {
    "EqualityProof": {
      "Type": "CiphertextToPlainEqualityProof",
      "Proof": "zkp_bytes_here"
    },
    "BalanceProof": {
      "Type": "RangeProof",
      "Proof": "zkp_bytes_here"
    }
  }
}
```

**Edge Case Analysis (Low-Volume Transaction Flow):** Alice, the issuer, converts 50 ConfidentialMPT into her second account, performs a single confidential send of 20 to Bob (a holder), and then executes a ConvertBack of 30\.

Step 1\. Issuer Convert (Alice → second account, 50\)

* Publicly revealed: Amount \= 50\.  
* Ledger effect: OA ↑ 50, COA ↑ 50, IPB ↓ 50\.  
* Outsiders now know: 50 CMPT entered confidential circulation.

Step 2\. Confidential Send (Alice’s second account → Bob, amount 20\)

* Public sees: sender \= Alice’s second account, receiver \= Bob, ciphertexts, ZKPs.  
* Amount 20 is hidden.  
* Ledger effect: OA, COA, IPB unchanged (just redistribution).

Step 3\. *ConvertBack* (Alice’s second account → issuer reserve, 30\)

* Publicly revealed: Amount \= 30\.  
* Ledger effect: OA ↓ 30, COA ↓ 30, IPB ↑ 30  
* Alice’s confidential balance is now 0, but outsiders cannot know this since ElGamal ciphertexts for 0 look indistinguishable from nonzero.

**What outsiders can infer**

* Net change in the confidential pool is 50  −  30  = 20\. So, 20 CMPT remain somewhere in confidential circulation.  
* But they cannot know whether Bob got 20, 15, 5, or even 0 — because Alice’s second account may still hold some of the 20\.

**Why no exact leakage**

* ElGamal ciphertexts are randomized: encrypting 0 produces a different-looking ciphertext each time.  
* Outsiders cannot look at the second account’s balance ciphertext and say it is zero.  
* Thus, they cannot deduce whether Alice’s second account was emptied or kept some confidential balance.

**Note:** This design allows tokens to move between public and private states. While the Convert and ConvertBack transactions show their amounts to provide this flexibility, they still protect the privacy of individual balances and transfers. Observers can only see the total change in circulation, not how the private supply is shared among holders. ElGamal randomization makes it impossible to tell the difference between accounts with zero balances. This ensures that outsiders cannot know if a specific account is empty or still holds private tokens.

### ConfidentialMPTClawback

Clawback involves the issuer forcibly reclaiming funds from a holder's account. This action is fundamentally incompatible with standard confidential transfers, as the issuer does not possess the holder's private ElGamal key and therefore cannot generate the required ZKPs for a normal ConfidentialMPTSend. To solve this, the protocol introduces a single and privileged transaction that allows an issuer to verifiably reclaim funds in one uninterruptible step.

This issuer-only transaction is designed to convert a holder's entire confidential balance directly into the issuer's public reserve.

| Field | Required | JSON Type | Description |
| :---- | :---- | :---- | :---- |
| TransactionType | Yes | String | Must be "ConfidentialMPTClawback". |
| Account | Yes | String | The issuer's account address, which must sign the transaction. |
| HolderToClawback | Yes | String | The address of the holder whose funds are being clawed back. |
| RevealedAmount | Yes | String | The plaintext amount of the holder's total confidential balance. |
| ZKProof | Yes | Object | A ZKP proving RevealedAmount is the correct decryption of the holder's EncryptedBalanceIssuer. |

#### How the Clawback Process Works

1. Issuer Decrypts and Prepares: The issuer takes the EncryptedBalanceIssuer ciphertext from the HolderToClawback's MPToken object and uses its own private key to decrypt it, revealing the holder's total confidential balance, m.  
2. Issuer Submits Transaction: The issuer creates and signs a ConfidentialMPTClawback transaction, setting the RevealedAmount field to m. It also generates and includes an equality proof.  
3. Validator Verification and Execution: Validators receive the transaction and perform a series of checks and state changes as a single:  
   * Verification: They first confirm the transaction was signed by the token Issuer and that the ZKProof is valid. The proof provides cryptographic certainty that the RevealedAmount is the true value hidden in the holder's on-ledger ciphertext.  
   * Ledger Changes: If the proof is valid, the validators execute all of the following changes at once:  
     1. The ConfidentialBalance\_Spending and ConfidentialBalance\_Inbox are set to a valid encryption of zero.  
     2. The global COA is decreased by the RevealedAmount.  
     3. The global OA is also decreased by the RevealedAmount.  
     4. The Issuer's public reserve balance is increased by the RevealedAmount.

This single transaction securely and verifiably moves the funds directly from the holder's confidential balance to the issuer's public reserve, ensuring the integrity of the ledger's public accounting is perfectly maintained.

### MPTokenIssuanceSet \- Confidential Side Effects

The standard MPTokenIssuanceSet transaction is used by an issuer to lock the public MPTs of a specific holder. To support confidential freezes without introducing a new transaction type, the logic of MPTokenIssuanceSet is extended with the following side effects. When a MPTokenIssuanceSet transaction is processed to lock or unlock a holder's public MPTs, validators must perform these additional checks and actions after all standard validation is complete.

#### Validator Logic Extension for MPTokenIssuanceSet

1. Check for Lock/Unlock Action: The validator confirms that the MPTokenIssuanceSet transaction is being used to modify the lock status of a specific holder's public MPT balance.  
2. Execute Confidential Side Effect:  
   * If the transaction is locking the holder's public balance, the validator must find the holder's corresponding MPToken object and set its ConfidentialBalanceFrozen field to true.  
   * If the transaction is unlocking the holder's public balance, the validator must find the holder's corresponding MPToken object and set its ConfidentialBalanceFrozen field to false.

## 7\. Auditability & Compliance

The Confidential MPT model is designed to provide robust privacy for individual transactions while ensuring both the integrity of the total token supply and a high degree of flexibility for regulatory compliance and auditing.

To achieve this balance, this protocol offers flexible auditability through two distinct mechanisms. The primary method is on-chain selective disclosure, where each confidential balance is dually encrypted under a designated auditor's public key, allowing for independent, trust-minimized verification. This model is also designed for dynamic, forward-looking compliance; if a new auditor or party requires access later, the issuer can re-encrypt existing balances under the new key and provide cryptographic equality proofs to grant them access without disrupting the system or sharing existing keys. As a simpler, trust-based alternative, the protocol also supports an issuer-mediated model using view keys. In this approach, the issuer controls a separate set of keys that provide read-only access and can be shared directly with auditors on an as-needed basis.

The technical foundation for both of these models is a multi-ciphertext architecture, where each confidential balance is maintained under several different public keys (e.g., holder, issuer, and optional auditor) to serve these distinct purposes.

#### **Mechanism 1: On-Chain Selective Disclosure (A Trust-Minimized Approach)**

The primary method for compliance is on-chain selective disclosure, which provides cryptographically enforced auditability directly on the ledger.

* Auditor-Specific Encryption: When an AuditorPolicy is active, each confidential balance is dually encrypted under the designated auditor's public key and stored in the EncryptedBalanceAuditor field on the ledger.  
* Independent Verification: This allows the auditor to use their own private key to independently decrypt and verify any holder's balance at any time, without needing cooperation from the issuer or the holder.  
* Dynamic, Forward-Looking Compliance: This model is designed for flexibility. If a new auditor or regulatory body requires access after the token has been issued, the issuer can facilitate this without disrupting the system. The process is as follows:  
  1. The issuer uses its private key to decrypt its own on-ledger copy of a holder's balance (EncryptedBalanceIssuer).  
  2. The issuer then re-encrypts this balance under the new auditor’s public key.  
  3. Finally, the issuer provides the new ciphertext to the auditor along with a ZK equality proof that  cryptographically proves that the new ciphertext matches the official on-ledger version.

This powerful re-encryption capability enables targeted, on-demand compliance without ever sharing the issuer's private key or making user balances public.

#### **Mechanism 2: Issuer-Mediated Auditing (A Simple View Key Model)**

As a simpler, trust-based alternative, the protocol also supports an issuer-mediated model using **view keys**.

* **Issuer-Controlled Keys**: In this approach, the issuer controls a separate set of "view keys." All confidential balances and transaction amounts are also encrypted under these keys.  
* **On-Demand Disclosure**: When an audit is required, the issuer can share the relevant view key directly with an auditor or regulator. This key grants the third party **read-only access** to view the necessary confidential information.  
* **Trust Assumption**: This model is operationally simpler but requires the auditor to trust that the issuer is providing the correct and complete set of view keys for the scope of the audit.

**Foundational Elements for Public Integrity**

Both compliance models are built upon foundational elements that ensure the integrity of the total token supply remains publicly verifiable at all times.

* Issuer Ciphertexts (EncryptedBalanceIssuer): Every confidential balance is dually encrypted under the issuer's public key. This serves two critical functions:  
  * It acts as the "master copy" that enables the issuer to perform the re-encryption required for dynamic selective disclosure.  
  * It allows the issuer to monitor aggregate confidential circulation and reconcile it with public issuance.  
* Confidential Outstanding Amount (COA): This plaintext field on the ledger tracks the aggregate total of all non-issuer confidential balances. It provides a global, public view of the confidential supply, allowing any observer to validate the system's most important invariant: OutstandingAmount ≤ MaxAmount.

**Example Audit Flows**

* Public Supply Audit (No Keys Required)  
  1. An observer reads the public ledger fields: OA, COA, and MA.  
  2. They validate the invariant OA ≤ MA.  
  3. They can conclude that the total supply is within its defined limits without seeing any individual balances.  
* Selective Disclosure Audit (Auditor Uses Own Key)  
  1. A regulator is designated as an auditor under the on-chain policy.  
  2. The auditor fetches a holder’s ledger object and uses their own private key to decrypt the EncryptedBalanceAuditor field, revealing the holder's confidential balance.  
  3. This balance can be cross-checked against the global COA for consistency.  
* View Key Audit (Issuer Provides Key)  
  1. A regulator requests access to a user's transaction history.  
  2. The issuer provides the regulator with the appropriate view key.  
  3. The regulator uses the view key to decrypt the relevant confidential balances and transaction amounts.

## 8\. Privacy Properties

Confidential MPT transactions are designed to minimize information leakage while preserving verifiability of supply and balances. Validators and external observers see only ciphertexts and ZKPs and never learn the underlying amounts except where amounts are already revealed in XLS-33 semantics.

**Publicly Visible Information**

* Transaction type (ConfidentialMPTConvert, ConfidentialMPTSend, etc.).  
* Involved accounts (Account, Issuer, Destination).  
* Currency code (e.g., "USD").  
* Ciphertexts (ElGamal pairs under holder, issuer, optional auditor keys).  
* ZKPs (non-interactive proofs of correctness).  
* For issuer funding (Convert → second account): Amount is revealed, consistent with visible mint events in XLS-33.

**Hidden Information**

* Amounts moved in ConfidentialMPTSend, ConfidentialMPTMerge.  
* Holder balances (except their public balance field).  
* Distribution of confidential supply across holders.

**Transaction-Type Privacy Notes**

* Convert (holder):  
  * Public → Confidential: Amount is revealed once, but only as a conversion event.  
  * Thereafter, spending is hidden.  
  * OA unchanged, COA ↑.  
* Convert (issuer → second account):  
  * Amount visible (already disclosed in XLS-33 issuance).  
  * Confidential balance seeded in the second account.  
  * OA ↑, COA ↑.  
* Send:  
  * No amounts revealed.  
  * OA unchanged, COA unchanged.  
* Merge:  
  * No amounts revealed.  
  * OA unchanged, COA unchanged.  
* Convert back (second account):  
  * Amount revealed (issuer reserve increases).  
  * OA ↓, COA ↓, IPB ↑.  
* Convert back (holder):  
  * Amount revealed.  
  * OA unchanged, COA ↓, HPB ↑.

## 9\. Security Considerations

Confidential MPTs introduce cryptographic mechanisms that require careful validation and enforcement. This section summarizes key security invariants, proof requirements, and considerations against potential attack vectors.

### Proof Requirements

Every confidential transaction must carry appropriate ZKPs:

* Convert: Equality proof that Amount is consistently encrypted under holder and issuer keys.  
* Send: Range proof (balance ≥ transfer amount) and equality proof (ciphertexts match across holder/issuer/auditor keys).  
* Optional auditor keys: Additional equality proofs binding auditor ciphertexts to the same plaintext.

### Confidential Balance Consistency

* Each confidential balance entry maintains parallel ciphertexts:  
* Holder key (spendable balance).  
* Issuer key.  
* Auditor key(s), if enabled.  
* Validators require a proof that all ciphertexts encrypt the same plaintext, preventing divergence between views.

### Issuer Second Account Model

* Issuer must use a designated second account for confidential issuance.  
* Prevents redefinition of OA semantics and keeps compatibility with XLS-33.  
* Validators enforce that direct confidential issuance from the issuer account is invalid.

### Privacy Guarantees

* Transaction amounts are hidden in all confidential transfers except:  
  * Issuer mint events (already visible in legacy MPTs).  
  * Conversion from public → confidential, where only the converted amount is disclosed once.  
* Redistribution among holders (including issuer’s second account) leaks no amounts.

### Auditor & Compliance Controls

* If AuditorPolicy is enabled, ciphertexts under auditor keys must be validated with equality proofs.  
* Prevents issuers from selectively encrypting incorrect balances for auditors.  
* Selective disclosure allows compliance without undermining public confidentiality.

### Attack Surface & Mitigations

* Replay attacks: Transactions bound to unique ledger indices/versions; proofs must include domain separation.  
* Malformed ciphertexts: Validators reject invalid EC points.  
* Balance underflow: Range proofs prevent spending more than available.  
* Auditor collusion: Auditors see balances only if granted view keys; public supply integrity remains trustless.  
* Issuer misbehavior: Enforced by supply invariants and public COA/OA/MA checks.

## 10\. Analysis of Transaction Cost and Performance

The efficiency is critical to the viability of Confidential MPTs. This analysis compares potential methods for range proofs to determine their impact on transaction size and overall performance.

#### Foundational Assumptions

First, let's establish the size of our basic cryptographic building blocks.

* Curve: secp256k1  
* Scalar: An integer modulo the curve order, which is 32 bytes for secp256k1.  
* Compressed EC Point: A point on the curve represented by its x-coordinate and a prefix byte, totaling 33 bytes.  
* EC-ElGamal Ciphertext: A pair of EC points (C1​,C2​), resulting in 2×33=66 bytes.

We will use the ConfidentialMPTSend transaction as our benchmark, as its cryptographic payload is the most complex:

* 3 Ciphertexts (Sender, Receiver, Issuer): 3×66 \= 198 bytes.  
* 2 Public Keys (Sender, Receiver): 2×33 \= 66 bytes.  
* Equality Proofs: Proofs that all ciphertexts encrypt the same amount, totaling 196 bytes.  
* Range Proof: The proof that the hidden amount is non-negative.

Option 1: Decomposition Range Proof  
This method involves breaking the amount into its individual bits and generating a separate proof for each bit to show it is either 0 or 1\. The proof size is linear to the number of bits.

1a: Using 64-bit Values

* Total Range Proof Size: For a 64-bit amount, the size is 64 bits×130 bytes/bit≈8,320 bytes (8.1 kB).  
* Total Crypto Payload: 198(ciphertexts)+66(keys)+194(equality)+8,320(range)≈8.8 kB.  
* Performance Impact: An overhead of nearly 9 kB is extremely large and generally considered impractical for production systems due to high fees and network load.

1b: Using 40-bit Values  
Reducing the bit length provides a significant, but insufficient, size reduction.

* Total Range Proof Size: For a 40-bit amount, the size is 40 bits×130 bytes/bit=5,200 bytes (5.1 kB).  
* Total Crypto Payload: 198(ciphertexts)+66(keys)+194(equality)+5,200(range)≈5.7 kB.  
* Performance Impact: While a 35% reduction from the 64-bit version, a payload of over 5 kB is still far too large to be viable on a high-performance ledger.

Option 2: Bulletproofs  
Bulletproofs are a modern ZKP system designed for efficiency, with proof sizes that grow logarithmically with the number of bits (O(logn)).

##### Using 64-bit Values

* Total Range Proof Size: A Bulletproof for a 64-bit value is highly compact, estimated at \~650 bytes. Equality proofs can be efficiently aggregated into this single proof.  
* Total Crypto Payload: 198(ciphertexts)+66(keys)+650(proof)≈914 bytes.  
* Performance Impact: An overhead of less than 1 kB is efficient and perfectly viable. The one-time computational cost to verify is a widely accepted trade-off for the enormous savings in data size.  
  * Note on 40-bit values: Bulletproofs require a bit length that is a power of two. A 40-bit proof would need to be padded to 64 bits, offering no size savings over a native 64-bit proof.

Summary

| Metric | Decomposition (64-bit) | Decomposition (40-bit) | Bulletproofs (64-bit) |
| :---- | :---- | :---- | :---- |
| Proof Size Complexity | O(n) \- Linear | O(n) \- Linear | O(logn) \- Logarithmic |
| Total Crypto Payload | \~8.8 kB | \~5.7 kB | \~914 bytes |
| Computational Complexity (Prover) | 256 scalar multiplications | 160 scalar multiplications | 128 scalar multiplications |
| Computational Complexity (Verifier) | 256 separate scalar multiplications | 160 separate scalar multiplications | 2log2​(n)+c scalar multiplications (c is a small constant). For a 64-bit value, \~17 terms, plus 2-3 individual scalar multiplications. |

Bulletproofs are an efficient choice. Even when reducing the bit length, the decomposition approach results in a transaction payload that is over 6 times larger than a Bulletproof.

## 11\. Frequently Asked Questions (FAQ)

This section addresses common questions about Confidential MPTs and their design choices, ranging from basic functionality to advanced research topics.  
Q1. Can confidential and public balances coexist?

* Yes. Issuers and holders may hold both public and confidential balances of the same MPT.  
* Conversions between the two are explicit transactions (ConfidentialMPTConvert).  
* Hybrid ecosystems are fully supported.

Q2. Why introduce a separate Merge transaction?

* Incoming transfers could make proofs stale if balances were a single field.  
* Split balances (CB\_S and CB\_IN) isolate proofs to a stable spending balance.  
* The Merge transaction consolidates funds deterministically and bumps the version counter.  
* It is proof-free and cheap to validate.

Q3. What happens if a user forgets to merge their inbox?

* Incoming funds accumulate in CB\_IN.  
* They remain safe but cannot be spent until merged into CB\_S.  
* Wallets are expected to merge before a send if needed.

Q4. Can confidential transactions be used in DEX, escrow, or checks?

* Not in this version.    
* Confidential MPT extensions focus on regular confidential MPT payments between accounts.    
* Integration with XRPL’s DEX, escrow, or checks requires further research — e.g., how to represent offers or locked balances without leaking amounts.  

Q5. Can the issuer disable confidential transfers after enabling them?

* If \`ConfidentialityConfigImmutable \= false\`, the issuer may enable or disable \`ConfidentialTransfersEnabled\` after issuance.    
* If \`ConfidentialityConfigImmutable \= true\`, the setting is locked permanently and cannot be changed.    
* This prevents issuers from weakening privacy guarantees after launch.

Q6. How does compliance fit in?

* Each confidential balance is stored as parallel ciphertexts:  
  * Under the holder’s key (CB\_S/CB\_IN),  
  * Under the issuer’s key (EncryptedBalanceIssuer),  
  * Under an auditor’s key (EncryptedBalanceAuditor), if enabled.  
* ZKPs prove all ciphertexts encrypt the same value.  
* Public can verify supply limits via issuer ciphertexts; auditors may decrypt balances if permitted.

Q7. What happens if a holder loses their ElGamal private key?

* The holder cannot decrypt or spend their confidential balances.  
* The funds remain valid on-ledger but are effectively locked.

Q8. What prevents replay or proof reuse?

* All ZKPs are transcript-bound with domain separation.  
* Binding includes transaction type, issuer, currency, and version counters.  
* Replaying a proof in another context will fail verification.

Q9. Are confidential transactions more expensive than standard MPT transactions?

* Yes. They include extra ciphertexts and ZKPs, which increase transaction size and verification cost.  
* Efficiency remains a design goal: proofs are lightweight (range \+ equality), and aggregation may reduce overhead in the future.

Q10. What happens if validators cannot verify a ZKP?

* The transaction is rejected during consensus, just like an invalid signature.  
* This prevents malformed or incorrect confidential balances from entering the ledger.

Q11. Why not just rely on client-side retry for stale proofs?

* Retry works only if the account rarely receives funds.  
* In active accounts, constant incoming transfers can keep invalidating proofs, preventing sends entirely.  
* The split-balance \+ merge model solves this by ensuring proofs always reference a stable spending balance.

Q12. Why not auto-merge the inbox during a send?

* Implicit merges would unexpectedly change version numbers, invalidating queued proofs.  
* They also create hidden state changes that complicate audits.  
* Explicit Merge keeps the process deterministic and user-controlled.

Q13. Why not reuse Convert for merging?

* Convert moves public → confidential and touches plaintext fields.  
* It requires equality proofs and ciphertext inputs from the user.  
* Merge is confidential → confidential, deterministic, and proof-free.

Q14. Why does the issuer need a second account?

* In the second-account model, issuer’s public reserve is converted into confidential supply by sending to a designated holder account (the second account).  
* This keeps XLS-33 semantics intact: OutstandingAmount \= non-issuer balances.  
* The downside is operational overhead: issuer must manage an additional account.

Q15. Will proofs be optimized in future versions?

* Current design uses per-transaction range and equality proofs.  
* Future work will focus on optimizing proofs to reduce transaction size and verification cost.  
* Benchmarking is needed to balance validator performance and UX.

Q16. Can there be more than one auditor?

* Presently, only one optional AuditorPolicy is supported.  
* Future extensions may allow multi-auditor setups using threshold encryption or policy-driven key distribution.

Q17. How will DEX and escrow support be added?

* Research is needed on how to represent offers and escrows confidentially without leaking amounts.  
* This is a research topic for future revisions.

Q18. Are there edge cases mixing public and confidential balances?

* Yes. Partial conversions, payment channels, or checks may create consistency edge cases.  
* Further work is needed to guarantee consistent semantics across hybrid scenarios.

Q19. Can auditors get partial/limited visibility?

* Current auditor view key model is binary (full access or none).  
* Future work may enable fine-grained selective disclosure:  
  * Time-limited access,  
  * Restricted access to subsets of accounts,  
  * Policy-based encryption.

Q20. Is the system quantum-safe?

* Today’s design uses EC-ElGamal over secp256k1 (not PQ-safe).  
* Future directions include PQ-friendly schemes (e.g., lattice-based).  
* The migration path remains open research.

Q21. Why require explicit Merge instead of eliminating it in future?

* Merge solves staleness deterministically today.  
* Issuers and wallets may prefer less operational overhead.  
* Future designs may revisit whether the second-account model or protocol refinements can simplify this requirement.

Q22. How does a confidential clawback work? Does it take all my confidential funds?   
Yes, it is a total operation. The issuer initiates a single transaction that provides a ZKP to the network of your total confidential balance (both spending and inbox). If the proof is valid, the network simultaneously deletes your entire confidential balance and credits the issuer's public reserve with the exact, proven amount.

## Acknowledgements

We would like to thank David Schwartz, Ayo Akinyele, Kenny Lei, Shashwat Mittal, and Shawn Xie for their invaluable feedback and insightful discussions which improved this specification.  
