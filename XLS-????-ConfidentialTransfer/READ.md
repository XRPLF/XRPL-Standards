# XLS-ConfidentialTransfer: Confidential transfers for XRPL

**Authors:** Murat Cenk, Aanchal Malhotra  
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
### EC-ElGamal Ciphertext of the amount
- Let G be the generator of the elliptic curve group.
- Let pk be the user’s EC-ElGamal public key.
- The user wants to encrypt a known plaintext amount m.
- The ciphertext is of the form C = (r⋅G, m⋅G + r⋅pk) where r is a randomly chosen blinding scalar and the operation "⋅" is used for representing the elliptic curve scalar multiplication (point multipli action) operation.
### Equality between plaintext and ciphertext
The EqualityProof in the ConfidentialMint transaction proves, in zero-knowledge, that the plaintext amount m (given explicitly as Amount) matches the encrypted value in the EncryptedBalance field (an EC-ElGamal ciphertext).
The proof aims to prove that the provided plaintext Amount = m was correctly encrypted into EncryptedBalance C = (A, B), where A = r⋅G, B = m⋅G + r⋅pk without revealing r.
#### How to Generate EqualityProof
- The EqualityProof is a sigma protocol proving knowledge of r such that A = r⋅G and B − m⋅G = r⋅pk. This is a standard Chaum-Pedersen proof of equality of discrete logarithms across two bases (G and pk), showing the discrete logarithm of A base G is equal to the discrete logarithm of B - mG base pk.
#### Steps to Generate the Proof
- Choose a random scalar t ∈ Zq
- Compute commitments: T1 = t⋅G and T2 = t⋅pk
- Compute challenge c = H(A,B,T1,T2,m)
- Compute response s = t + c⋅r mod q
#### The proof
The proof is then commitments (T1,T2) and the response s. 
#### Verification 
This tuple allows the verifier to check
s⋅G = T1 + c⋅A
s⋅pk = T2 + c(B−mG)
If both hold, the verifier is convinced the ciphertext indeed encrypts m, without learning r.

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
### Equality between two two EC-ElGamal ciphertexts
This section presents the construction of a ZKP for plaintext equality between two EC-ElGamal ciphertexts by showing that both ciphertexts encrypt the same message, possibly under different public keys and randomness.
#### Setting
- Let the two ciphertexts be C1 = (R1, S1) = (r1G,mG + r1P1) and C2 = (R2, S2) =  (r2G,mG + r2P2) where m ∈ Zq is the message (as a scalar), r1, r2 ∈ Zq​ are random nonces, and P1 and P2​ are public keys of two parties. We want to prove in zero-knowledge that both ciphertexts encrypt the same value m, without revealing it. Prove knowledge of m, r1, r2m, r1​, r2​ such that
S1 − r1P1 = mG = S2 − r2P2.
- In other words, S1 − r1P1 = S2 − r2P2.This reduces to proving that the discrete log of two points is equal under different bases.
Protocol (non-interactive, Fiat–Shamir)
- Let’s define A1 = S1 − r1P1 and  A2 = S2 − r2P2. So we want to prove that
logG(A1) = logG(A2) = m.
- Prover chooses random w ∈ Zq.
- Computes t1 = wG and t2 = wG (same generator here, but could be different if generalizing)
- Computes challenge c = H(G,A1,A2,t1,t2)(using a hash function modeled as a random oracle)
- Computes response z = w + c⋅m mod q.
#### the proof
- The proof sent to verifier c and z.
#### Verification
Checks if zG is equal to t1 + cA1 and t2 + cA2. Since A1 = A2, both equations are equivalent and only one is necessary, but sending both gives integrity.


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

### Stealth Protocol
Let the two primary parties involved in the protocol be:
- Alice (Sender): Holds keys a (private key) and A  (public key, where A = aG), where G is the generator point on the elliptic curve.
- Bob (Receiver): Holds keys b (private key) and B (public key, where B = bG).
#### Key Generation by the Receiver (Bob): 
- Bob, the recipient, generates an elliptic curve key pair. The private key is b and the public key is B = bG. This key pair will be used to derive a stealth address and facilitate the process of recipient verification.
#### Stealth Address Creation by the Sender (Alice) 
- Alice, the sender, generates a random scalar r to ensure the one-time nature of the stealth address. 
- Alice calculates the temporary public key R as follows: R = rG. 
- R is included in the transaction and shared publicly, but it cannot be linked to Alice or Bob without their private keys. 
- Alice computes the shared secret s using Bob's public key B: s = H(rB) where H is a cryptographic hash function that ensures the output is uniformly distributed and secure. 
- Alice uses the shared secret s to derive the one-time public key P for this transaction: P = sG+B. The resulting P is a unique public key only recognizable only by Bob, the recipient.
#### Recipient Key Recovery by Bob
- Bob scans the blockchain for transactions containing the temporary public key R. 
- For each detected R, Bob computes the shared secret: s = H(bR). 
- Bob then reconstructs P using the shared secret and his public key: P = sG + B. 
- To spend the funds, Bob computes the one-time private key a′ = H(bR) + b. 
- This ensures that: a′G = (H(bR) + b)G = sG + B = P and Bob can now use a′ to authorize transactions involving P.

#### Validation
- Sender transfers public XRP to stealth address.
- Receiver scans ledger with `b_view` key.

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

#### One-time ring signatures and key images

A one-time ring signature allows a sender to prove they control one of a set of public keys without revealing which one. This ensures sender anonymity. To prevent double-spending, each signature includes a key image derived from the sender’s private key. This image is verifiable for uniqueness but does not reveal which key it was derived from.
#### Key Definitions
Let G be the elliptic curve base point used by XRPL (e.g., Ed25519 or secp256k1). We have
- x be the private key
- P = x·G be the public key
- Hp(P) be a hash-to-curve function
- I = x·Hp(P) be the key image
#### Signature construction
Given a message m and a ring of public keys S = {P₀, P₁, ..., Pₙ}, the signer is at index s and has private key x_s.
1. Generate random scalars qᵢ for all i ∈ [0, n]
2. Generate random responses wᵢ for all i ≠ s
3. Compute:
   - Lᵢ = qᵢ·G if i = s, else Lᵢ = qᵢ·G + wᵢ·Pᵢ
   - Rᵢ = qᵢ·Hp(Pᵢ) if i = s, else Rᵢ = qᵢ·Hp(Pᵢ) + wᵢ·I

4. Compute challenge:
c = H(m || L₀, ..., Lₙ || R₀, ..., Rₙ)
5. Derive:
   - cₛ = c - Σ_{i ≠ s} cᵢ mod l
   - rₛ = qₛ - cₛ·x_s mod l
6. The final signature is:
σ = (I, {cᵢ}, {rᵢ})
#### Signature verification
Given a message m, signature σ = (I, {cᵢ}, {rᵢ}), and public key set S = {P₀, ..., Pₙ}:
1. Compute:
   - Lᵢ' = rᵢ·G + cᵢ·Pᵢ
   - Rᵢ' = rᵢ·Hp(Pᵢ) + cᵢ·I
2. Compute challenge:
c' = H(m || L₀', ..., Lₙ' || R₀', ..., Rₙ')
3. Accept the signature if:
c' = Σ_{i=0 to n} cᵢ mod l
#### Key image linkability
Validators maintain a global set of used key images. To prevent double-spending:
If the key image I has been seen before, the transaction is rejected.
If not, the key image is added to the ledger as spent and the transaction is accepted.
Because I = x·Hp(P) is unique for each private key x, a note can only be spent once.



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
