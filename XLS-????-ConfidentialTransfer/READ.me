# XLS-ConfidentialTransfer: Confidential transfers for XRPL

**Authors:** Murat Cenk  
**Status:** Draft  
**Type:** XRPL Standard (XLS)  
**Version:** 0.1

---

## Abstract

This standard proposes a confidential transfer mechanism for the XRPL that hides transaction amounts using elliptic curve encryption and ZKPs. The design introduces encrypted balance handling, homomorphic updates, and optional compliance features. Receiver privacy and full anonymity are supported as optional extensions.

---

## Motivation

While XRPL provides fast and efficient financial transfers, all transaction details are fully transparent. For enterprise, retail, and tokenized asset use cases, confidential transfers are essential to protect business-sensitive information and user privacy.

This proposal aims to:
- Enable confidential transaction amounts.
- Enable validation correctness.
- Offer optional compliance and privacy extensions.

---

## Specification

### Transaction Types

- **ConfidentialMint**: Converts a public XRP balance into an encrypted confidential balance.
- **ConfidentialSend**: Transfers confidential amounts between users using dual encryption and zero-knowledge proofs.

---

### ConfidentialMint Transaction Format

| Field           | Type   | Required | Description                                |
|----------------|--------|----------|--------------------------------------------|
| Amount          | UInt64 | Yes      | The plain XRP amount to convert            |
| EncryptedBalance| Blob   | Yes      | EC-ElGamal ciphertext of the amount        |
| EqualityProof   | Blob   | Yes      | ZK proof that EncryptedBalance equals Amount |
| PublicKey       | Blob   | Yes      | Sender's EC-ElGamal public key             |

---

### ConfidentialSend Transaction Format

| Field         | Type | Required | Description                                       |
|---------------|------|----------|---------------------------------------------------|
| C_send        | Blob | Yes      | Ciphertext encrypted with sender's key           |
| C_receive     | Blob | Yes      | Ciphertext encrypted with recipient’s key        |
| EqualityProof | Blob | Yes      | ZK proof: both ciphertexts encrypt the same value |
| RangeProof    | Blob | Yes      | ZK proof: sender balance - amount ≥ 0            |
| AuditorField  | Blob | Optional | Ciphertext encrypted with auditor's public key   |
| PublicKeys    | Blob | Yes      | Public keys used in the transaction              |

---

### Validation Rules

- Validate equality and range proofs
- Perform EC-ElGamal homomorphic updates:
  - `Sender_Balance' = Sender_Balance - C_send`
  - `Receiver_Balance' = Receiver_Balance + C_receive`
- Verify optional auditor encryption if provided
- Store updated encrypted balances in ledger

---

### Ledger Changes

- New encrypted balance field in AccountRoot object
- New transaction types: `ConfidentialMint` and `ConfidentialSend`
- Optional support for auditor ciphertexts and note objects

---

### Compliance: Selective Disclosure

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

- Validation: transfers public XRP to stealth address
- Receiver scans ledger with `b_view` key

---

### A.2 Use Case 2: Receiver Anonymity with Confidential Amounts

**Transaction Type:** `ReceiverPrivacyConfidentialSend`

| Field          | Type   | Required | Description                                 |
|----------------|--------|----------|---------------------------------------------|
| C_send         | Blob   | Yes      | Ciphertext encrypted with sender’s key      |
| C_receive      | Blob   | Yes      | Ciphertext encrypted to stealth recipient   |
| EqualityProof  | Blob   | Yes      | ZK proof that both ciphertexts match        |
| RangeProof     | Blob   | Yes      | ZK proof of sender balance sufficiency      |
| EphemeralKey   | Blob   | Yes      | Sender’s one-time key                       |
| StealthAddress | Blob   | Yes      | Receiver’s computed address                 |
| AuditorField   | Blob   | Optional | Encrypted payload for auditor               |

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

| Field         | Type   | Required | Description                                  |
|---------------|--------|----------|----------------------------------------------|
| Amount        | UInt64 | Yes      | Plain XRP amount                             |
| Commitment    | Blob   | Yes      | Pedersen commitment `C = r·G + m·H`          |
| OwnerKey      | Blob   | Yes      | `P = s·G + B_spend`                          |
| EphemeralKey  | Blob   | Yes      | One-time key `R = k·G`                        |
| EqualityProof | Blob   | Yes      | ZK proof `C` encodes `Amount`                |

**Validator Actions:**
- Verify `EqualityProof`
- Deduct `Amount` from public balance
- Store Note: `(Commitment, OwnerKey, EphemeralKey, Spent = false)`

---

### NoteMint Transaction Format

| Field         | Type | Required | Description                              |
|---------------|------|----------|------------------------------------------|
| Commitment    | Blob | Yes      | Pedersen commitment `C = r·G + m·H`      |
| OwnerKey      | Blob | Yes      | One-time key for note ownership          |
| EphemeralKey  | Blob | Yes      | For stealth detection                    |
| RangeProof    | Blob | Yes      | ZK proof: balance covers note amount     |

**Validator Actions:**
- Verify `RangeProof`
- Deduct note amount homomorphically
- Store Note with `Spent = false`

---

### ConfidentialTransfer Transaction Format

| Field          | Type | Required | Description                                   |
|----------------|------|----------|-----------------------------------------------|
| Ring           | Blob | Yes      | Ring of public keys                           |
| KeyImage       | Blob | Yes      | Unique tag for double-spend prevention        |
| RingSignature  | Blob | Yes      | Proof of signer ownership                     |
| NewNotes       | List | Yes      | New notes with (Commitment, OwnerKey, EphemeralKey) |
| RangeProofs    | Blob | Yes      | ZK range proofs on outputs                    |
| BalanceProof   | Blob | Yes      | ZK proof: input = sum(output)                 |

**Validator Actions:**
- Verify `RingSignature`, `KeyImage`, `RangeProofs`, `BalanceProof`
- Reject reused `KeyImage`
- Mark input note as spent
- Store new output notes

---

### ConfidentialBurn Transaction Format

| Field         | Type | Required | Description                              |
|---------------|------|----------|------------------------------------------|
| Commitment    | Blob | Yes      | Note commitment to burn                  |
| EqualityProof | Blob | Yes      | ZK proof: commitment encodes amount      |

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

## References

[1] Bulletproofs: Short Proofs for Confidential Transactions  
[2] EC-ElGamal Encryption  
[3] Schnorr-based Ring Signatures  
[4] XRPLF XLS-9d: Blinded Tags
