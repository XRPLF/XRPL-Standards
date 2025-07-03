# XLS-ConfidentialTransfer: Confidential transfers for XRPL

**Authors:** Murat Cenk, Aanchal Malhotra  
**Status:** Draft  
**Type:** XRPL Standard (XLS)  
**Version:** 0.1

---

## Abstract

This standard proposes a confidential transfer mechanism for the XRPL that hides transaction amounts using elliptic curve encryption and zero-knowledge proofs (ZKPs). The design introduces encrypted balance handling, homomorphic updates, and optional compliance features. Receiver privacy and full anonymity are supported as optional extensions.

---

## Motivation

While XRPL provides fast and efficient financial transfers, all transaction details are fully transparent. For enterprise, retail, and tokenized asset use cases, confidential transfers are essential to protect business-sensitive information and user privacy.

This proposal aims to:
- Enable confidential transaction amounts.
- Enable validation correctness.
- Offer optional compliance and privacy extensions.

---

## Terminology

| Term                | Definition                                                                                                               |
|---------------------|--------------------------------------------------------------------------------------------------------------------------|
| **Account**          | XRPL classic address (e.g., `rEXAMPLE...`) that authorizes the transaction and provides public XRP for minting.          |
| **PublicKey**        | EC-ElGamal public key used to encrypt confidential balances; not necessarily the public key of the XRPL account owner.   |
| **SigningPubKey**    | XRPL signing key used to authorize the transaction; corresponds to the `Account` and verified via `TxnSignature`.        |
| **EncryptedBalance** | An EC-ElGamal ciphertext representing an encrypted XRP amount, stored in the ledger.                                     |
| **EqualityProof**    | ZKP that the plaintext `Amount` matches the EC-ElGamal ciphertext (`EncryptedBalance`).                                  |
| **RangeProof**       | ZKP that an encrypted amount is within a valid range (e.g., non-negative).                                               |
| **ConfidentialMint** | Transaction that deducts public XRP from the `Account` and creates an encrypted confidential balance.                    |
| **ConfidentialSend** | Transaction that transfers encrypted funds between users using dual encryption and ZKPs.                |
| **StealthAddress**   | One-time encryption key derived from a recipient’s viewing and spending keys; hides recipient identity on-chain.         |
| **Note**             | A cryptographic commitment to a confidential amount; used in the full anonymity mode for balance ownership and spending. |
| **KeyImage**         | Unique elliptic curve point derived from a private key; used in ring signature–based schemes to prevent double spending. |

---
## Notation and Curve Parameters

| Symbol     | Meaning                                                                                      |
|------------|----------------------------------------------------------------------------------------------|
| `G`        | Generator point of the elliptic curve group (e.g., for secp256k1).                           |
| `H`        | Independent generator used for Pedersen commitments (must be chosen so log_G(H) is unknown). |
| `r`        | Random scalar in the finite field `Z_p`, used as a blinding factor for encryption.            |
| `m`        | Plaintext amount to be encrypted (e.g., XRP value).                                          |
| `pk`       | EC-ElGamal public key used to encrypt the plaintext value.                                   |
| `sk`       | EC-ElGamal private key corresponding to `pk`; used to decrypt ciphertexts.                   |
| `A`        | First component of ciphertext: `A = r · G`.                                                  |
| `B`        | Second component of ciphertext: `B = m · G + r · pk`.                                        |
| `(A, B)`   | EC-ElGamal ciphertext tuple representing the encrypted value `m`.                            |

---
## Specification

### Transaction Types

- **ConfidentialMint**: Converts a public XRP balance into an encrypted confidential balance.
- **ConfidentialSend**: Transfers confidential amounts between users using dual encryption and ZKPs.

---
### ConfidentialMint Transaction

The `ConfidentialMint` transaction converts a known amount of XRP from a user’s public balance into an 
encrypted confidential balance using EC-ElGamal encryption. This serves as 
the entry point for participating in the confidential transfer system. When a ConfidentialMint transaction 
is processed, the XRP amount specified in the Amount field is deducted from the sender’s standard XRP balance. 
This sender is identified by the Account field, which corresponds to a classic XRPL account 
(i.e., the account paying the fee and authorizing the transaction). 
The encrypted version of the same amount, provided in the EncryptedBalance field, 
is then recorded as a confidential balance. The encrypted balance is stored under the sender’s AccountRoot, but each encrypted value is associated with the corresponding EC-ElGamal PublicKey. 
This allows multiple confidential balances, potentially with different ownership keys, to coexist under a single XRPL account. Although the encrypted balance is attached to the account that initiated the mint, 
only the holder of the private key corresponding to the PublicKey can decrypt or spend the confidential funds. 
This design enables private ownership of encrypted funds while preserving account-level structure and compatibility 
with XRPL’s existing ledger model.

This transaction:
- Deducts a plaintext `Amount` from the sender’s public XRP balance
- Initializes an encrypted balance using `EncryptedBalance`
- Includes a ZKP (`EqualityProof`) verifying that the encrypted value matches the stated `Amount`

---

#### Format

| Field               | Type       | Required | Description                                                                   |
|--------------------|------------|----------|-------------------------------------------------------------------------------|
| `TransactionType`   | UInt16     | Yes      | Must be set to `ConfidentialMint`                                             |
| `Account`           | AccountID  | Yes      | XRPL account funding the mint and authorizing the transaction                 |
| `Amount`            | UInt64     | Yes      | XRP amount to be converted to a confidential balance                          |
| `EncryptedBalance`  | Blob       | Yes      | EC-ElGamal ciphertext of `Amount`                                             |
| `EqualityProof`     | Blob       | Yes      | ZKP that the ciphertext matches the plaintext `Amount`    |
| `PublicKey`         | Blob       | Yes      | EC-ElGamal public key used for encryption        |
| `Fee`               | UInt64     | Yes      | XRP fee for processing the transaction                                        |
| `Sequence`          | UInt32     | Yes      | Sequence number of the sender’s account                                       |
| `SigningPubKey`     | Blob       | Yes      | Standard XRPL public key used to sign the transaction                         |
| `TxnSignature`      | Blob       | Yes      | Signature authorizing the transaction                                         |

---

#### JSON Example

```json
{
  "TransactionType": "ConfidentialMint",
  "Account": "rEXAMPLEsQp3cAZ1nE7j2YZQ1fHGsmqQLYg",
  "Amount": "1000000",
  "EncryptedBalance": "028f12...e9b3",
  "EqualityProof": "03ab45...cc11",
  "PublicKey": "0381c5...af12",
  "Fee": "10",
  "Sequence": 100,
  "SigningPubKey": "EDD6C5...A12F",
  "TxnSignature": "3044...0220"
}

```
#### Transaction Flow

This section describes how the `ConfidentialMint` transaction is constructed, submitted, and validated.

1. **User Prepares the Transaction**
    - Select a public `Amount` of XRP to convert.
    - Generate a random scalar `r`.
    - Compute EC-ElGamal ciphertext:
      ```
      A = r · G
      B = Amount · G + r · PublicKey
      EncryptedBalance = (A, B)
      ```

2. **Generate ZKP**
    - Construct a Chaum–Pedersen proof to show:
      ```
      A = r · G
      B - Amount · G = r · PublicKey
      ```
    - The result is stored in `EqualityProof`.

3. **Create the Transaction**
    - Populate required fields:
        - `TransactionType`, `Account`, `Amount`, `EncryptedBalance`
        - `EqualityProof`, `PublicKey`, `Fee`, `Sequence`, `SigningPubKey`, `TxnSignature`

4. **Submit to XRPL Network**
    - The transaction is submitted via standard XRPL submission flow.

5. **Validation by XRPL Validators**
    - Check signature validity.
    - Verify `EncryptedBalance` structure and curve points.
    - Verify `EqualityProof` with respect to `Amount`, `PublicKey`, and `EncryptedBalance`.
    - Confirm sufficient public XRP funds.
    - Subtract `Amount` from `Account`'s public balance.
    - The new EncryptedBalance is stored under the EncryptedBalances field in the sender’s AccountRoot, indexed by the provided EC-ElGamal PublicKey.

6. **Ledger Update**
    - The account state is updated with the new encrypted balance, allowing the user to participate in confidential transfers.

### Ledger Modifications

The `ConfidentialMint` transaction updates the sender’s `AccountRoot` object by attaching an `EncryptedBalances` field. This field holds one or more encrypted balance entries, each associated with an EC-ElGamal `PublicKey`. The confidential funds are stored in EC-ElGamal ciphertext form and can only be spent by the holder of the corresponding private key.

Each entry consists of:
- `PublicKey`: the EC-ElGamal public key used during minting
- `EncryptedBalance`: a ciphertext containing `(A, B)` curve points

This design supports future extensions (e.g., multiple balances per account or stealth addresses) and preserves compatibility with XRPL’s ledger format.

#### Example

```json
{
  "Account": "rAlice...",
  "EncryptedBalances": [
    {
      "PublicKey": "03abcd...",
      "EncryptedBalance": {
        "A": "028f12...",
        "B": "03a7e4..."
      }
    }
  ]
}
```
---
### ConfidentialSend Transaction

The ConfidentialSend transaction enables private transfer of encrypted balances between accounts on the XRPL using EC-ElGamal encryption, ZKPs, and additive homomorphism. The protocol ensures:
- The transaction amount remains hidden from the public. 
- The sender’s and receiver’s encrypted balances are updated directly, without decryption. 
- Optional compliance mechanisms are supported via selective disclosure. 
- Transaction correctness is enforced cryptographically, without linking the encrypted input/output to specific XRPL identities. 
- Anyone can construct and submit the transaction on behalf of the sender, as long as it is signed with a valid XRPL SigningPubKey corresponding to the Account.

This transaction:
- Deducts the encrypted amount from the sender’s encrypted balance (`C_send`) using homomorphic subtraction.
- Credits the encrypted amount to the receiver’s balance (`C_receive`) using homomorphic addition.
- Includes an equality proof demonstrating that `C_send` and `C_receive` encrypt the same amount.
- Includes a range proof to prove the sender’s remaining confidential balance remains non-negative after the deduction.
- Specifies the EC-ElGamal public keys used for encryption and verification of both sender and receiver.

---

#### Public Key Usage

This transaction involves two independent key types, each serving distinct roles:

| Role                        | Key Type                    | Usage                                                                 |
|-----------------------------|-----------------------------|-----------------------------------------------------------------------|
| XRPL Transaction Signing    | XRPL signing key (secp256k1 or ed25519) | Authorizes the transaction at the XRPL ledger level (`Account`)       |
| Confidential Balance Control| EC-ElGamal public key       | Defines who can decrypt or control the encrypted balances             |

- The XRPL signing key must be authorized for the XRPL `Account` and is verified using existing XRPL rules (master key, regular key, or multi-sign).
- The EC-ElGamal public keys are not required to be linked to an XRPL account. They are used exclusively for encrypting values and verifying zero-knowledge proofs. This decouples confidentiality from account identity and enables flexible, privacy-preserving ownership of funds.

---

#### Format

| Field               | Type      | Required | Description                                                                 |
|--------------------|-----------|----------|-----------------------------------------------------------------------------|
| `TransactionType`   | UInt16    | Yes      | Must be set to `ConfidentialSend`                                           |
| `Account`           | AccountID | Yes      | XRPL account authorizing and funding the transaction                        |
| `RecipientAccount`  | AccountID | Yes      | XRPL account receiving the confidential funds                               |
| `C_send`            | Blob      | Yes      | Ciphertext encrypted with sender’s EC-ElGamal public key                    |
| `C_receive`         | Blob      | Yes      | Ciphertext encrypted with receiver’s EC-ElGamal public key                  |
| `EqualityProof`     | Blob      | Yes      | ZKP that `C_send` and `C_receive` encrypt the same value                    |
| `RangeProof`        | Blob      | Yes      | ZKP that sender’s encrypted balance minus `C_send` is non-negative          |
| `PublicKeys`        | Object    | Yes      | EC-ElGamal public keys used for encryption/proofs                           |
| `AuditorField`      | Blob      | Optional | Encrypted copy of amount for auditor compliance + ZK equality proof         |
| `Fee`               | UInt64    | Yes      | XRP fee for processing the transaction                                      |
| `Sequence`          | UInt32    | Yes      | Sequence number of the sender’s account                                     |
| `SigningPubKey`     | Blob      | Yes      | XRPL public key used to authorize the transaction                           |
| `TxnSignature`      | Blob      | Yes      | Signature over the transaction blob                                         |

---

#### JSON Example

```json
{
"TransactionType": "ConfidentialSend",
"Account": "rEXAMPLEsQp3cAZ1nE7j2YZQ1fHGsmqQLYg",
"RecipientAccount": "rRecipientAccount1234567890abcd",
"C_send": "02ff33...ab12",
"C_receive": "035c22...cd45",
"EqualityProof": "0211cc...dead",
"RangeProof": "04aa88...beef",
"PublicKeys": {
"Sender": "03abc1...dd11",
"Receiver": "02fe11...bb44"
},
"AuditorField": "03e77...555a",
"Fee": "10",
"Sequence": 101,
"SigningPubKey": "EDD6C5...A12F",
"TxnSignature": "3045...0210"
}
```
---

#### Transaction Flow

The following steps describe how a `ConfidentialSend` transaction is constructed, submitted, and validated:

---

##### Step 1: Sender Prepares the Transfer

- The sender selects the plaintext amount `m` to transfer.
- Two EC-ElGamal ciphertexts are generated:
    - `C_send = (A1, B1) = (r1 · G, m · G + r1 · pk_sender)`
    - `C_receive = (A2, B2) = (r2 · G, m · G + r2 · pk_receiver)`
- Where:
    - `r1`, `r2` are randomly chosen blinding scalars.
    - `pk_sender` is the EC-ElGamal public key used to deduct balance from the sender.
    - `pk_receiver` is the EC-ElGamal public key used to assign balance to the receiver.

---

##### Step 2: Generate Equality Proof

- A ZK equality proof is generated to prove that both ciphertexts encrypt the same value `m`:
  ```
  Dec(pk_sender, C_send) = Dec(pk_receiver, C_receive) = m
  ```
- This proof ensures validators can verify the transfer is amount-consistent without learning `m`.

---

##### Step 3: Generate Range Proof

- A ZK range proof is constructed to prove that the sender has enough encrypted balance:
  ```
  EncryptedBalance_sender − C_send ≥ 0
  ```
- This prevents overdrafts and ensures correctness without disclosing the actual balance.

---

##### Step 4: (Optional) Add Auditor Encryption

- For compliance, an optional auditor ciphertext is created:
  ```
  C_auditor = (A3, B3) = (r3 · G, m · G + r3 · pk_auditor)
  ```
- An equality proof is attached to prove that `C_auditor` also encrypts `m`.

---

##### Step 5: Construct the Transaction

- Construct the transaction with the following fields:
    - `TransactionType`, `Account`, `RecipientAccount`, `Fee`, `Sequence`
    - `C_send`, `C_receive`, `EqualityProof`, `RangeProof`, `PublicKeys`
    - Optional `AuditorField`
    - `SigningPubKey`, `TxnSignature`

---

##### Step 6: Submit to XRPL Network

- Submit the transaction via standard XRPL APIs.
- It is signed using the sender’s `SigningPubKey`.

---

##### Step 7: Validation by XRPL Validators

Validators perform the following checks:

- Verify transaction signature.
- Validate curve points and ciphertext formats.
- Check:
    - `EqualityProof` to ensure amount consistency.
    - `RangeProof` to verify sufficient funds.
    - Optional auditor encryption and proof.

If valid:

- Locate the AccountRoot of the RecipientAccount and update its ConfidentialBalance field using homomorphic addition with C_receive. Reject if the ElGamalPublicKey in PublicKeys. Receiver does not match the one registered under RecipientAccount.
  ```
  EncryptedBalance_sender' = EncryptedBalance_sender − C_send
  ```
- Update the recipient’s encrypted balance:
  ```
  EncryptedBalance_receiver' = EncryptedBalance_receiver + C_receive
  ```

All balance updates are performed using EC-ElGamal's additive homomorphism.

---

##### Step 8: Recipient Decrypts the Value

- The recipient decrypts `C_receive` using their private key `sk_receiver`:
  ```
  m = Dec(sk_receiver, C_receive)
  ```
- The plaintext amount is revealed only to the recipient, ensuring transaction confidentiality.


---

#### Confidential Ledger State Fields

Each XRPL account that participates in confidential transfers is associated with the following additional fields in its `AccountRoot` entry:

| Field Name           | Type     | Description                                                                 |
|----------------------|----------|-----------------------------------------------------------------------------|
| `ConfidentialBalance`| Blob     | EC-ElGamal–encrypted balance associated with a specific ElGamal public key registered under the XRPL account.|
| `ElGamalPublicKey`   | Blob     | The EC-ElGamal public key registered under this XRPL account for receiving encrypted funds |
| `AuditorKeys`        | Blob     | (Optional) Auditor public keys for selective disclosure (if applicable)    |

> Note: These fields are maintained in the XRPL account’s `AccountRoot`, but the `ConfidentialBalance` is cryptographically bound to the registered `ElGamalPublicKey`, not the XRPL signing key. This separation preserves privacy and enables flexible key management.

---

#### Ledger Modification Flow

On successful validation of a `ConfidentialSend` transaction:

1. **Sender Account:**
    - `ConfidentialBalance` is decreased homomorphically by the encrypted amount `C_send`.
    - The range proof is verified to ensure that the resulting encrypted balance remains non-negative.

2. **Receiver Account:**
    - `RecipientAccount` is used to locate the XRPL account of the receiver.
    - The receiver’s `AccountRoot` is retrieved using this `RecipientAccount`.
    - The `ElGamalPublicKey` field of the receiver’s `AccountRoot` must exactly match the `PublicKeys.Receiver` provided in the transaction.
    - If no match is found or if the field is missing, the transaction is rejected.
    - Upon success, the receiver’s `ConfidentialBalance` is increased homomorphically by `C_receive`.

3. **AuditorField (Optional):**
    - If provided, the encrypted copy of the transferred amount is either:
        - Stored with the transaction (for external off-chain audit), or
        - Verified against known auditor public keys using a ZK equality proof.

4. **Standard Fields:**
    - `Sequence` number of the sender’s XRPL account is incremented (ensuring replay protection).
    - The XRP `Fee` is deducted from the sender’s public XRP balance (not from the confidential balance).

---
#### Privacy and Isolation

- Encrypted balances are maintained separately from public XRP balances and do not interfere with existing XRPL operations.
- Validators cannot infer:
    - The confidential transaction amount (due to encryption and ZKPs),
    - The contents or value of any encrypted balance,
    - Any off-chain relationship between an ElGamal key and other XRPL accounts.
- Because the RecipientAccount is explicitly included in the transaction and used to locate the receiver’s AccountRoot, this creates an on-ledger association between the XRPL identity and their confidential balance key.
- This design trades off full anonymity for balance encryption and protocol simplicity, while still supporting optional privacy extensions such as stealth addresses or note-based models.

---

#### Compliance Support

- Ledger changes accommodate optional auditor extensions by allowing encrypted amount disclosure under separate auditor public keys.
- Future upgrades may include selective decryption support.

---

### Ledger Changes

The ConfidentialSend transaction modifies the XRPL ledger by homomorphically updating the encrypted balances of both the sender and the receiver. No plaintext values are revealed or stored during this process. These changes are isolated to confidential balance fields associated with EC-ElGamal public keys, leaving standard XRP balances unaffected.

- Key ledger-level changes introduced by this proposal:
- Addition of encrypted balance fields in the AccountRoot object. 
- Introduction of new transaction types: ConfidentialMint and ConfidentialSend. 
- Optional support for auditor ciphertexts and note-based extensions.

---
### Compliance Extension

Two supported methods:
- **Auditor Encryption**: Encrypted output for auditor + equality proof
- **On-Demand Disclosure**: Users may share decryption key/amount when required

---



## Appendix A: Receiver Privacy Extensions

### A.1 Use Case 1: Receiver Anonymity Only (No Amount Confidentiality)

**Transaction Type:** `ReceiverPrivacySend`

| Field          | Type   | Required | Description                                |
|----------------|--------|----------|--------------------------------------------|
| Amount         | UInt64 | Yes      | Public amount of XRP being sent            |
| EphemeralKey   | Blob   | Yes      | One-time public key `R = r·G`              |
| StealthAddress | Blob   | Yes      | `P = H(r·B_view) + B_spend`                |
| Metadata       | Blob   | Optional | Encrypted memo or payload                  |

### Stealth Protocol

This section describes how sender and receiver generate unlinkable, one-time addresses using elliptic curve Diffie-Hellman and hashing. The goal is to enable recipient privacy by ensuring that only the receiver can detect and spend funds sent to a stealth address.

#### Participants

- **Alice (Sender)**:
  - Holds keypair: private key `a`, public key `A = a * G`
- **Bob (Receiver)**:
  - Holds keypair: private key `b`, public key `B = b * G`

Here, `G` is the generator point of the elliptic curve group.

#### Step 1: Receiver Key Generation (Bob)

- Bob generates a static keypair:
  - Private key: `b ∈ Z_q`
  - Public key: `B = b * G`

This keypair is used for deriving stealth addresses and later recovering received notes.

#### Step 2: Stealth Address Generation (Alice)

- Alice generates a fresh ephemeral scalar `r ∈ Z_q`
- Computes the temporary public key `R = r * G`

This `R` is published with the transaction.

- Computes the shared secret:

      s = H(r * B)

  where `H` is a cryptographic hash function mapping to `Z_q`.

- Derives the one-time public key for the recipient:

      P = s * G + B

This `P` is the stealth address used in the note or output.

#### Step 3: Recipient Detection and Key Recovery (Bob)

- Bob monitors the ledger for transactions containing `R`.
- For each detected `R`, Bob computes:

      s = H(b * R)

- Reconstructs the one-time public key:

      P = s * G + B

- Computes the corresponding one-time private key:

      a' = s + b  ∈ Z_q

This ensures:

      a' * G = (s + b) * G = s * G + B = P

Bob can now use `a'` to spend the funds sent to stealth address `P`, and only Bob can compute this key.

#### Validation
- Sender transfers public XRP to stealth address.
- Receiver scans ledger with `b_view` key.

---

### A.2 Use Case 2: Receiver Anonymity with Confidential Amounts

**Transaction Type:** `ReceiverPrivacyConfidentialSend`

| Field          | Type   | Required | Description                               |
|----------------|--------|----------|-------------------------------------------|
| C_send         | Blob   | Yes      | Ciphertext encrypted with sender’s key    |
| C_receive      | Blob   | Yes      | Ciphertext encrypted to stealth recipient |
| EqualityProof  | Blob   | Yes      | ZKP that both ciphertexts match           |
| RangeProof     | Blob   | Yes      | ZKP of sender balance sufficiency         |
| EphemeralKey   | Blob   | Yes      | Sender’s one-time key                     |
| StealthAddress | Blob   | Yes      | Receiver’s computed address               |
| AuditorField   | Blob   | Optional | Encrypted payload for auditor             |

- Validation same as `ConfidentialSend`
- No additional ledger change

---

## Appendix B: Full Confidential and Private Transfers

Combines:
- Confidential balances and amounts
- Receiver anonymity (stealth addresses)
- Sender anonymity (ring signatures)

---

### Transaction Types

| Transaction Type          | Description                                           |
|---------------------------|-------------------------------------------------------|
| NoteMintFromPublic        | Creates a confidential note from public XRP           |
| NoteMint                  | Creates a confidential note from confidential balance |
| ConfidentialTransfer      | Spends a note with ring signature and stealth address |
| ConfidentialBurn          | Converts a note back into public XRP                  |

---

### NoteMintFromPublic Transaction Format

| Field         | Type   | Required | Description                         |
|---------------|--------|----------|-------------------------------------|
| Amount        | UInt64 | Yes      | Plain XRP amount                    |
| Commitment    | Blob   | Yes      | Pedersen commitment `C = r·G + m·H` |
| OwnerKey      | Blob   | Yes      | `P = s·G + B_spend`                 |
| EphemeralKey  | Blob   | Yes      | One-time key `R = k·G`              |
| EqualityProof | Blob   | Yes      | ZKP `C` encodes `Amount`            |

**Validator Actions:**
- Verify `EqualityProof`
- Deduct `Amount` from public balance
- Store Note: `(Commitment, OwnerKey, EphemeralKey, Spent = false)`

---

### NoteMint Transaction Format

| Field         | Type | Required | Description                         |
|---------------|------|----------|-------------------------------------|
| Commitment    | Blob | Yes      | Pedersen commitment `C = r·G + m·H` |
| OwnerKey      | Blob | Yes      | One-time key for note ownership     |
| EphemeralKey  | Blob | Yes      | For stealth detection               |
| RangeProof    | Blob | Yes      | ZKP: balance covers note amount     |

**Validator Actions:**
- Verify `RangeProof`
- Deduct note amount homomorphically
- Store Note with `Spent = false`

---

### ConfidentialTransfer Transaction Format

| Field          | Type | Required | Description                                         |
|----------------|------|----------|-----------------------------------------------------|
| Ring           | Blob | Yes      | Ring of public keys                                 |
| KeyImage       | Blob | Yes      | Unique tag for double-spend prevention              |
| RingSignature  | Blob | Yes      | Proof of signer ownership                           |
| NewNotes       | List | Yes      | New notes with (Commitment, OwnerKey, EphemeralKey) |
| RangeProofs    | Blob | Yes      | ZK range proofs on outputs                          |
| BalanceProof   | Blob | Yes      | ZKP: input = sum(output)                            |

### One-Time Ring Signatures and Key Images

This section describes a cryptographic scheme that allows a sender to prove, in ZK, that they control one of a set of public keys without revealing which one. It preserves sender anonymity while preventing double-spending via key images.

#### Key Definitions

Let `G` be the elliptic curve generator (e.g., Ed25519 or secp256k1). Let:

- `x ∈ Z_l` be the sender’s private key
- `P = x * G` be the corresponding public key
- `Hp(P)` be a hash-to-curve function that maps `P` deterministically to a curve point
- The **key image** is defined as:

      I = x * Hp(P)

This `I` is unlinkable to `x` but uniquely identifies a spent key.

---

### Signature Construction

Let `m` be the message to sign, and `S = {P_0, P_1, ..., P_n}` be a set of public keys (the ring). The signer is at index `s` with private key `x_s`.

1. **Generate randomness:**
  - Choose random scalars `q_i ∈ Z_l` for all `i ∈ [0, n]`
  - Choose random responses `w_i ∈ Z_l` for all `i ≠ s`

2. **Compute commitments:**

   For all `i ∈ [0, n]`:

  - If `i == s`:

        L_i = q_i * G  
        R_i = q_i * Hp(P_i)

  - If `i ≠ s`:

        L_i = q_i * G + w_i * P_i  
        R_i = q_i * Hp(P_i) + w_i * I

3. **Compute challenge:**

   c = H(m || L_0 || ... || L_n || R_0 || ... || R_n)

4. **Compute responses for signer’s index `s`:**

   c_s = c - Σ_{i ≠ s} c_i mod l  
   r_s = q_s - c_s * x_s mod l

5. **The final ring signature is:**

   σ = (I, {c_i}, {r_i}) for i = 0 to n

---

### Signature Verification

Given message `m`, signature `σ = (I, {c_i}, {r_i})`, and public key ring `S = {P_0, ..., P_n}`:

1. **Recompute commitments:**

   For each `i`:

       L_i' = r_i * G + c_i * P_i  
       R_i' = r_i * Hp(P_i) + c_i * I

2. **Recompute challenge:**

       c' = H(m || L_0' || ... || L_n' || R_0' || ... || R_n')

3. **Accept the signature if:**

       c' = Σ_{i=0 to n} c_i mod l

---

### Key Image Linkability

To prevent double-spending:

- Validators maintain a global set of used key images.
- If the key image `I` has already been recorded, the transaction is rejected.
- Otherwise, the key image `I` is added to the ledger as spent.

Since the key image is deterministically derived from the signer’s private key (`I = x * Hp(P)`), it uniquely identifies a spent note without revealing which ring member signed the transaction.



**Validator Actions:**
- Verify `RingSignature`, `KeyImage`, `RangeProofs`, `BalanceProof`
- Reject reused `KeyImage`
- Mark input note as spent
- Store new output notes

---

### ConfidentialBurn Transaction Format

| Field         | Type | Required | Description                    |
|---------------|------|----------|--------------------------------|
| Commitment    | Blob | Yes      | Note commitment to burn        |
| EqualityProof | Blob | Yes      | ZKP: commitment encodes amount |

**Validator Actions:**
- Verify `EqualityProof`
- Mark note as spent
- Credit XRP to public balance

---

## Security Considerations

- ZKPs must be sound
- EC-ElGamal ciphertexts must be randomized
- Key images must be collision-resistant
- Auditing metadata must not leak confidential values

---
## Appendix C: Technical Explanation
### EC-ElGamal ciphertext and homomorphic properties

Let G be the generator of the elliptic curve group, and let pk = x * G denote the user’s EC-ElGamal public key for a private scalar x in Z_q. To encrypt a known plaintext amount m in Z_q, the user samples a random blinding scalar r in Z_q and computes the ciphertext:

    C = (c1, c2) = (r * G, m * G + r * pk)

This ciphertext C = (c1, c2), where both components are curve points, encrypts the amount m while preserving homomorphic properties. Given two ciphertexts:

    C1 = (r1 * G, m1 * G + r1 * pk)
    C2 = (r2 * G, m2 * G + r2 * pk)

The component-wise addition yields:

    C1 + C2 = ((r1 + r2) * G, (m1 + m2) * G + (r1 + r2) * pk)

which is a valid EC-ElGamal encryption of (m1 + m2). Similarly, subtraction:

    C1 - C2 = ((r1 - r2) * G, (m1 - m2) * G + (r1 - r2) * pk)

produces a ciphertext encrypting (m1 - m2). These homomorphic properties enable secure balance updates on ledger entries without revealing the plaintext amounts.

---
### Equality Proof Between Plaintext and Ciphertext

In the `ConfidentialMint` transaction, the `EqualityProof` is a ZKP showing that a given plaintext amount `m` matches the encrypted value in the EC-ElGamal ciphertext `C = (A, B)`.

The encryption is defined as:

    A = r * G
    B = m * G + r * pk

where:
- `G` is the generator of the elliptic curve group,
- `pk = x * G` is the recipient’s public key,
- `r` is a random blinding scalar in Z_q,
- `m` is the plaintext amount.

The goal is to prove knowledge of `r` such that both:

    A = r * G
    B - m * G = r * pk

This corresponds to a standard **Chaum-Pedersen proof** of equality of discrete logarithms across two bases (`G` and `pk`), without revealing `r`.

#### Steps to Generate the EqualityProof

1. Choose a random scalar `t ∈ Z_q`
2. Compute the commitments:
   `T1 = t * G`
   `T2 = t * pk`
3. Compute the challenge:
   `c = H(A, B, T1, T2, m)`
   where `H` is a cryptographic hash function modeled as a random oracle
4. Compute the response:
   s = t + c * r mod q

#### The Proof

The proof consists of the tuple `(T1, T2, s)`

#### Verification

To verify the proof, the verifier recomputes the challenge `c` and checks that:

    s * G  == T1 + c * A
    s * pk == T2 + c * (B - m * G)

If both equalities hold, the verifier is convinced that the ciphertext `(A, B)` correctly encrypts the known plaintext `m` without learning `r`.

---

### Equality Proof Between Two EC-ElGamal Ciphertexts

This section describes a ZKP that two EC-ElGamal ciphertexts encrypt the same plaintext value `m`, possibly using different public keys and randomness. The proof reveals nothing about `m`, `r1`, or `r2`.

#### Setting

Let:

    C1 = (R1, S1) = (r1 * G, m * G + r1 * P1)
    C2 = (R2, S2) = (r2 * G, m * G + r2 * P2)

where:
- `G` is the curve generator,
- `P1`, `P2` are EC-ElGamal public keys,
- `r1`, `r2 ∈ Z_q` are blinding scalars (nonces),
- `m ∈ Z_q` is the plaintext scalar value to encrypt.

The prover wants to convince the verifier that:

    S1 - r1 * P1 = S2 - r2 * P2 = m * G

which implies that both ciphertexts encrypt the same `m`.

This reduces to proving that two group elements `A1` and `A2` have the same discrete logarithm base `G`:

    A1 = S1 - r1 * P1
    A2 = S2 - r2 * P2
    log_G(A1) = log_G(A2) = m

#### Protocol (Non-Interactive via Fiat–Shamir)

1. Prover computes:
   A1 = S1 - r1 * P1 and A2 = S2 - r2 * P2

2. Chooses a random scalar `w ∈ Z_q`

3. Computes:
   t1 = w * G and t2 = w * G

4. Computes challenge:
   c = H(G, A1, A2, t1, t2)

5. Computes response:
   z = w + c * m mod q

#### The Proof

The proof consists of A1, A2, t1, t2, and z.

#### Verification

The verifier recomputes `c` and checks that:

    z * G == t1 + c * A1
    z * G == t2 + c * A2

Since `A1 = A2`, verifying either is sufficient, but verifying both adds consistency and protection against malformed inputs.

If the equations hold, the verifier is convinced that both ciphertexts encrypt the same plaintext `m` without learning anything about `m`, `r1`, or `r2`.




---
### Bitwise Range Proof

In the `ConfidentialSend` transaction, the `RangeProof` field is a ZKP
that ensures the  `balanace - m ≥  0`. This prevents encoding invalid or negative amounts
while maintaining confidentiality.

#### Bit Decomposition

The prover represents the amount `m ∈ Z_q` as a binary sum:

    m = b_0 * 2^0 + b_1 * 2^1 + ... + b_{n-1} * 2^{n-1}, where each b_i ∈ {0,1}

#### Commitments to Bits

Each bit `b_i` is committed using a Pedersen commitment:

    C_i = b_i * G + r_i * H

where
- `G` and `H` are independent elliptic curve generators
- `r_i ∈ Z_q` is a blinding factor for bit `i`

#### Aggregation of Commitments

The prover computes the overall commitment to the amount:

    C = ∑_{i=0}^{n-1} 2^i * C_i = m * G + r * H

where

    r = ∑_{i=0}^{n-1} 2^i * r_i

This `C` serves as the link between the bitwise decomposition and the encrypted value.

#### Bit Validity Proofs (b_i ∈ {0,1})

For each bit commitment `C_i`, the prover constructs a ZK OR-proof
demonstrating that:

    C_i = 0 * G + r_0 * H    or    C_i = 1 * G + r_1 * H

This is instantiated using a standard disjunctive Σ-protocol based on by Cramer, Damgård, and Schoenmakers (CRYPTO 1994).  The interactive protocol is converted to a non-interactive form via the Fiat–Shamir heuristic.

#### Linking to EC-ElGamal Ciphertext

The bit commitment `C` is linked to the EC-ElGamal ciphertext:

    (A, B) = (r * G, m * G + r * pk)

This is done using the `EqualityProof` described earlier, via a Chaum–Pedersen protocol
showing that:

    C - m * G = r * H
    B - m * G = r * pk

Without revealing `m` or `r`.

#### Summary

The complete bitwise range proof includes:
- `n` Pedersen commitments to bits: C_0, ..., C_{n-1}
- `n` OR-proofs that each b_i ∈ {0,1}
- An aggregation check that ∑ 2^i * C_i = C
- An EqualityProof that C and the ciphertext represent the same `m`

This ensures that `m` is a valid non-negative amount encrypted under EC-ElGamal
while maintaining ZK.

---
### Base-3 Range Proof

As an alternative to bitwise decomposition, the `RangeProof` may use a base-3 (ternary) decomposition,
where the plaintext amount `m ∈ [0, 3^n)` is expressed using digits in `{0, 1, 2}`.

This method reduces the number of proof elements compared to bitwise proofs, at the cost of more complex
per-digit validity checks. It is particularly useful when optimizing for proof size.

#### Base-3 Decomposition

The prover expresses the value `m` as:

    m = d_0 * 3^0 + d_1 * 3^1 + ... + d_{n-1} * 3^{n-1}, where each d_i ∈ {0, 1, 2}

#### Commitments to Digits

Each ternary digit `d_i` is committed using a Pedersen commitment:

    C_i = d_i * G + r_i * H

Where:
- `G` and `H` are independent elliptic curve generators
- `r_i ∈ Z_q` is a blinding scalar

#### Aggregation of Commitments

The prover computes the aggregate commitment to the value:

    C = ∑_{i=0}^{n-1} 3^i * C_i = m * G + r * H

Where:

    r = ∑_{i=0}^{n-1} 3^i * r_i

This `C` links the ternary digit commitments to the encrypted value `m`.

#### Digit Validity Proofs (d_i ∈ {0,1,2})

To ensure each committed digit `d_i` is in `{0,1,2}`, the prover uses a ZK OR-proof over three cases:

    C_i = 0 * G + r_0 * H
    C_i = 1 * G + r_1 * H
    C_i = 2 * G + r_2 * H

This is a 3-ary disjunctive Σ-protocol, following the generalized Cramer–Damgård–Schoenmakers (CDS) framework.

As with bitwise proofs, this interactive protocol is made non-interactive via the Fiat–Shamir transform.

#### Linking to EC-ElGamal Ciphertext

The aggregate commitment `C` is linked to the EC-ElGamal ciphertext `(A, B)` using the same
`EqualityProof` described earlier:

    A = r * G
    B = m * G + r * pk

The `EqualityProof` confirms that both representations encode the same plaintext `m`.

#### Summary

A base-3 range proof includes:
- `n` Pedersen digit commitments: C_0, ..., C_{n-1}
- `n` 3-ary OR-proofs ensuring d_i ∈ {0,1,2}
- An aggregation check: ∑ 3^i * C_i = C
- An EqualityProof linking `C` and the ciphertext

Using base-3 decomposition reduces the number of digits required (compared to base-2),
trading off slightly more complex per-digit proofs for fewer total commitments.
---
### Bulletproof Range Proof

As an alternative to bitwise or base-3 decompositions, the `RangeProof` may use **Bulletproofs** by Bünz, Bootle, Boneh, Poelstra, Wuille, and Maxwell that is
a logarithmic-size ZKP system efficiently proving that a committed value lies
within a certain range without revealing it.

This approach significantly reduces proof size and verification time for typical 64-bit confidential
amounts, and is suitable when compactness and scalability are important.

#### Commitment

The prover commits to the amount `m` using a standard Pedersen commitment:

    C = m * G + r * H

Where:
- `G`, `H` are independent elliptic curve generators
- `r ∈ Z_q` is a blinding scalar
- `m ∈ Z_q` is the confidential plaintext amount

#### Range Statement

The prover proves in ZK that:

    0 ≤ m < 2^n

For example, with `n = 64`, the proof shows that `m` is a valid 64-bit non-negative integer.

Unlike bitwise proofs, Bulletproofs do **not** require committing to each bit individually. Instead,
the full range proof is built from the single commitment `C`.

#### Proof Protocol

The Bulletproof protocol constructs an inner product argument that proves `m` is composed of valid bits
without sending each bit commitment separately. The protocol includes:

1. Vector polynomials encoding the bits of `m`
2. An interactive proof of the inner product
3. Fiat–Shamir transformation to make it non-interactive

The resulting proof size is:

    Size = 2 * log₂(n) + 9 group elements

For `n = 64`, the proof is ~700 bytes — significantly smaller than bitwise or base-3 alternatives.

#### Linking to EC-ElGamal Ciphertext

The Pedersen commitment `C` used in the Bulletproof must be shown to match the plaintext value
used in the EC-ElGamal ciphertext:

    A = r * G
    B = m * G + r * pk

This linkage is proven using the standard `EqualityProof` described earlier:

    C - m * G = r * H
    B - m * G = r * pk

#### Summary

A Bulletproof-based range proof includes:
- A single Pedersen commitment `C = m * G + r * H`
- A compact logarithmic-size ZKP that `m ∈ [0, 2^n)`
- An `EqualityProof` linking `C` and the EC-ElGamal ciphertext

Bulletproofs are well-suited for high-performance applications where minimizing proof size and
verification cost is critical, while preserving strong ZK guarantees.
## References

[1] Bulletproofs: Short Proofs for Confidential Transactions  
[2] EC-ElGamal Encryption  
[3] Schnorr-based Ring Signatures  
[4] XRPLF XLS-9d: Blinded Tags
