<pre>
  xls: 40
  title: Decentralized Identity on XRP Ledger
  description: Implementation of native support for W3C Decentralized Identifiers (DIDs) on XRP Ledger
  author: Aanchal Malhotra <amalhotra@ripple.com>
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/100
  status: Final
  category: Amendment
  created: 2023-03-30
</pre>

# 1. Abstract

Self-sovereign identity, defined as a lifetime portable digital identity that does not depend on any centralized authority, requires a new class of identifier that fulfills the following four requirements: persistence, global resolvability, cryptographic verifiability, and decentralization. [World Wide Web Consortium](https://www.w3.org/2022/07/pressrelease-did-rec.html.en) (W3C) standardized Decentralized Identifiers (DIDs) are a new type of identifier that enable verifiable, self-sovereign digital identity and are designed to be compatible with any distributed ledger or network. In the context of digital identities, W3C's standards for DIDs and Verifiable Credentials (VCs) are rapidly gaining traction, especially in blockchain-related domains. In this document we propose to implement native support for W3C DIDs on XRP Ledger.

To this end, we specify the following on XRPL:

- A new `DID method` that describes:
  - The format for XRP ledger DID, and
  - Defines how XRP ledger DIDs are generated
- How to do `CRUD operations` on XRP ledger DIDs

This specification conforms to the requirements specified in the [DID v1.0](https://www.w3.org/TR/did-core/) specification currently recommended by the W3C Credentials Community Group.

# 2. Principles & Goals

## 2.1. Principles

This proposal chooses to recommend W3C DID identity standard to satisfy the following first principles:

- **Decentralized:** Requires no central issuing agency and functions effectively in Decentralized Finance.

- **Persistent and Portable:** Inherently persistent and long-lived, not requiring the continued operation of any underlying organization and portable between different applications.

- **Cryptographically Verifiable:** Based on cryptographic proofs rather than out-of-band trust.

- **Universally Resolvable and Interoperable:** Open to any solution that recognizes the common W3C DID standards and requires no one specific software vendor implementation.

## 2.2. Goals & Non-Goals

- This document aims to define DID identifier format for XRP ledger conformant to W3C DID standards that can be created and owned by any XRPL account holder, and specify definitions for DID methods to create, read, update and delete DID (data) that can be implemented by any service, wallet, or application.

- This proposal is NOT intended as a competing decentralized identity standard; it aims to leverage existing (and emerging) decentralized identity standard proposed by W3C.
- The proposal is motivated to enable **individual users** to create, and manage their decentralized identifiers while having complete control over the private keys and contents of the identity object.

# 3. New On-Ledger Objects and Transactions

We propose one new ledger object and two new transaction types.

- **DID** is a new ledger object that is unique to an XRPL account and may contain a reference to, or the hash of, or the [W3C DID document](https://w3c-ccg.github.io/did-primer/#did-documents) itself associated with the corresponding DID.
- **DIDSet** is a new transaction type used to perform the following two operations:
  - `Create` the new ledger object `DID` with `URI`, and/or `Data`, and/or `DIDDocument` fields, thus adding the required reserve towards the account that initiated the transaction.
  - `Update` the mutable `URI`, `Data` and `DIDDocument` fields of the `DID` object.
- **DIDDelete** is a new transaction type used to delete the `DID` object, thus reducing the reserve requirement towards the account that created the object.

# 4. XRPL Decentralized Identifier (DID) Specification

In this section we specify the implementation details of W3C DID standard that are specific to XRP Ledger.

## 4.1. The `DID` Object

We propose a new ledger object called **`DID`** that holds references to or data associated with a single DID. The `DID` object is created and updated using the `DIDSet` transaction and is deleted using the `DIDDelete` transaction.

### 4.1.1. Object Fields

`DID` object may have the following required and optional fields.

| Field Name        |     Required?      | JSON Type | Internal Type |
| ----------------- | :----------------: | :-------: | :-----------: |
| `LedgerEntryType` | :heavy_check_mark: | `string`  |   `UINT16`    |

Identifies the type of ledger object. The proposal recommends the value `0x0049` as the reserved entry type.

---

| Field Name      |     Required?      | JSON Type | Internal Type |
| --------------- | :----------------: | :-------: | :-----------: |
| `PreviousTxnID` | :heavy_check_mark: | `string`  |   `Hash256`   |

The identifying hash of the transaction that most recently modified this object.

---

| Field Name          |     Required?      | JSON Type | Internal Type |
| ------------------- | :----------------: | :-------: | :-----------: |
| `PreviousTxnLgrSeq` | :heavy_check_mark: | `number`  |   `UINT32`    |

The index of the ledger that contains the transaction that most recently modified this object.

---

| Field Name | Required? | JSON Type | Internal Type |
| ---------- | :-------: | :-------: | :-----------: |
| `URI`      |           | `string`  |    `BLOB`     |

`URI` specifies a Universal Resource Identifier, a.k.a. URI that SHOULD point to the corresponding DID document or to the data associated with the DID. This field could be an HTTP(S) URL or IPFS URI. The `URI` field is NOT checked for validity, but the field is limited to a maximum length of 256 bytes.

---

| Field Name | Required? | JSON Type | Internal Type |
| ---------- | :-------: | :-------: | :-----------: |
| `Data`     |           | `string`  |    `BLOB`     |

`Data` field SHOULD contain the public attestations of identity credentials associated with the DID. The `Data` field is NOT checked for validity, but the field is limited to a maximum length of 256 bytes.

---

| Field Name    | Required? | JSON Type | Internal Type |
| ------------- | :-------: | :-------: | :-----------: |
| `DIDDocument` |           | `string`  |    `BLOB`     |

`DIDDocument` field SHOULD contain the <a href="https://www.w3.org/TR/did-core/#did-documents"> DID document </a> per W3C standards associated with the DID. The `DIDDocument` field is NOT checked for validity, and is limited to a maximum length of 256 bytes.

### 4.1.2. The `DID` Object ID Format

`DID` object may contain public data associated with the XRPL account's identity. This requires the `DID` to be:

- Unique in the XRPL namespace, and
- Uniquely associated with the XRPL account.

We compute the `DID` object ID, a.k.a., `DIDID`, as the `SHA-512Half` of the following values, concatenated in order:

- The `DID` space key (`0x0049`)
- The Account ID

### 4.1.3. Reserve Requirements

The account that creates the `DID` object will incur one owner reserve (2 XRP at the time of writing this document).

## 4.2. XRP Ledger DID Method Specification

In this section, we describe the DID method specification that conforms to the requirements specified in the DID specification currently published by the W3C Credentials Community Group. For more information about DIDs and DID method specifications, refer to the DID [Primer](https://github.com/WebOfTrustInfo/rwot5-boston/blob/master/topics-and-advance-readings/did-primer.md).

### 4.2.1. XRP Ledger DID Scheme

The DID format as defined by W3C is as follows:

```
"did:" method-name ":" method-specific-idstring
```

We propose the following format for DIDs on XRPL:

```
"did:xrpl": network-id: xrpl-specific-idstring
```

The components specific to the XRPL network are the following:

- `method-name`: The `"xrpl"` namestring specifies that this is a DID for XRP Ledger.
  A DID that uses this method MUST begin with the following prefix: `did:xrpl`. Per the DID specification, this string MUST be in lowercase. The remainder of the DID, after the prefix, is specified below.

- `method-specific-idstring` is formed by `network-id` and `xrpl-specific-idstring`
  - `network-id`: `network-id` is a chain ID which is an identifier of XRP ledger networks. It specifies the underlying network instance where the `DID` is stored. Per [XLS-37 specification](../XLS-0037-concise-transaction-identifier-ctid/README.md), in XRPL Protocol Chains the Network ID should match the chosen peer port.

- `xrpl-specific-idstring` is generated as described in the next section.

### 4.2.2. XRPL-specific-idstring Generation Method

XRPL DID MUST be unique within the XRPL network.

`xrpl-specific-idstring` is the `AccountID` or the hex of `master public key` of the `DID` object's account. See [this](https://xrpl.org/accounts.html#address-encoding) for more details on XRPL public keys.

Example:
A valid DID for an XRPL network may be

```
did:xrpl:1:rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh
```

or

```
did:xrpl:1:0330E7FC9D56BB25D6893BA3F317AE5BCF33B3291BD63DB32654A313222F7FD020
```

The above DIDs are case-insensitive and will resolve to the same `DID` object.

# 5. CRUD Operations

In this section we outline the following four CRUD operations for `did:xrpl` method.

- `Create`
- `Read`
- `Update`
- `Delete`

## 5.1. DIDSet Transaction

The proposal introduces a new transaction type: **`DIDSet`** that can be used to:

- `Create` a new `DID` object,
- `Update` the existing `DID` object.

### 5.1.1 Example **`DIDSet`** JSON

```
{
  "TransactionType": "DIDSet",
  "Account": "rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh",
  "Fee": "10",
  "Sequence": 391,
  "URI": "697066733A2F2F62616679626569676479727A74357366703775646D37687537367568377932366E6634646675796C71616266336F636C67747179353566627A6469",
  "Data": "",
  "SigningPubKey":"0330E7FC9D56BB25D6893BA3F317AE5BCF33B3291BD63DB32654A313222F7FD020",
  ...

  }
```

## Create

If the `DID` object associated with the `Account` does not exist,

- If either `URI`, `Data` or `DIDDocument` fields are not present in the transaction, then transaction fails.
- Otherwise, a successful `DIDSet` transaction creates a new `DID` object with the following object ID:

`SHA-512Half` of the following values, concatenated in order:

- The `DID` space key (`0x0049`)
- The Account ID of the `Account`, i.e. rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh

#### DID associated with this object is:

```
did:xrpl:1:rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh
```

or

```
did:xrpl:1:0330E7FC9D56BB25D6893BA3F317AE5BCF33B3291BD63DB32654A313222F7FD020
```

### Implicit DID document

Some minimalistic use cases might only need signatures and simple authorization tokens, but don't need support for multiple keys or devices, complex organizational hierarchies and other advanced rights management features.

To lower the entry level, we do not always require registering a `DID` by publishing a reference to or the DID Document on the ledger. If there's no explicitly registered `DID` found on the ledger then an implicit document is used instead as a default. Any update on this implicit document requires registering the `DID` object and applied changes on the ledger to be valid.

For example, the implicit DID Document of `did:xrpl:1:0330E7FC9D56BB25D6893BA3F317AE5BCF33B3291BD63DB32654A313222F7FD020` enables only a single key 0330E7FC9D56BB25D6893BA3F317AE5BCF33B3291BD63DB32654A313222F7FD020 to authorize changes on the DID document or sign credentials in the name of the DID.

## Update

If the `DID` object associated with the `Account` exists,

- If `URI`, `Data` and `DIDDocument` fields are not present, then transaction fails.
- Otherwise, a successful `DIDSet` transaction updates this object.

### 5.1.2. Transaction-specific fields

| Field Name        |     Required?      | JSON Type | Internal Type |
| ----------------- | :----------------: | :-------: | :-----------: |
| `TransactionType` | :heavy_check_mark: | `string`  |   `UINT16`    |

Indicates the new transaction type **`DIDSet`**. The integer value is 40.

---

| Field Name |     Required?      | JSON Type | Internal Type |
| ---------- | :----------------: | :-------: | :-----------: |
| `Account`  | :heavy_check_mark: | `string`  |  `AccountID`  |

Indicates the account which initiates the `DIDSet` transaction. This account MUST be a funded account on ledger.

---

| Field Name |     Required?      | JSON Type | Internal Type |
| ---------- | :----------------: | :-------: | :-----------: |
| `Fee`      | :heavy_check_mark: | `number`  |   `Amount`    |

Indicates the fee that the account submitting this transaction is willing to pay.

---

| Field Name | Required? | JSON Type | Internal Type |
| ---------- | :-------: | :-------: | :-----------: |
| `URI`      |           | `string`  |    `BLOB`     |

Indicates the `URI` field for this object.

---

| Field Name | Required? | JSON Type | Internal Type |
| ---------- | :-------: | :-------: | :-----------: |
| `Data`     |           | `string`  |    `BLOB`     |

Indicates the `Data` field for this object.

---

| Field Name    | Required? | JSON Type | Internal Type |
| ------------- | :-------: | :-------: | :-----------: |
| `DIDDocument` |           | `string`  |    `BLOB`     |

Indicates the DID document for this object.

:notebook: If the `URI`, `Data`, or `DIDDocument` fields are missing, they will remain unchanged. However, if they contain an empty string, they will be deleted, otherwise, they will be updated.

## 5.2. Read

The initial step in utilizing a DID for an application may involve resolving the DID to access the underlying DID Document or attestations. This resolution process unveils the cryptographic material and service endpoints linked to the specific DID.

In the case of XRPL DID, the `read` operation facilitates the resolution to the associated `DID` object. Upon successful resolution, applications can retrieve and utilize the relevant `URI` and/or `Data`, and/or `DIDDocument` fields contained within the `DID` object:

Given the input DID for an account, follow these steps:

- Retrieve the xrpl-specific-idstring of the DID.

- If the xrpl-specific-idstring represents a public key:
  - Compute the Account ID using the method described [here](https://xrpl.org/accounts.html#address-encoding).

- Retrieve the contents of the corresponding `DID` object in its raw format using the XRPL's [`ledger_entry`](https://xrpl.org/ledger_entry.html#ledger_entry) method. Use the `did` field to specify the Account ID to retrieve the `DID` object in the raw ledger format.

### Example

Given the DID **did:xrpl:1:rpfqJrXg5uidNo2ZsRhRY6TiF1cvYmV9Fg**, do the following:

- Retrieve `rpfqJrXg5uidNo2ZsRhRY6TiF1cvYmV9Fg`
- Perform the `ledger_entry` method request to retrieve the contents of `DID` object:

```
{
    "command": "ledger_entry",
    "did": "rpfqJrXg5uidNo2ZsRhRY6TiF1cvYmV9Fg",
    "ledger_index": 'validated',
  }
```

A sample response to the above query might look like this:

```
{
  "index": '46813BE38B798B3752CA590D44E7FEADB17485649074403AD1761A2835CE91FF',
  "ledger_hash": '4264238D7FBAF1BE54075BF69E63AAFE0CD33193EC15D08E6F4397B5389F181B',
  "ledger_index": 4,
  "node": {
    "Account": 'rpfqJrXg5uidNo2ZsRhRY6TiF1cvYmV9Fg',
    "DIDDocument": '646F63',
    "Data": '617474657374',
    "Flags": 0,
    "LedgerEntryType": 'DID',
    "OwnerNode": '0',
    "PreviousTxnID": 'A4C15DA185E6092DF5954FF62A1446220C61A5F60F0D93B4B09F708778E41120',
    "PreviousTxnLgrSeq": 4,
    "URI": '6469645F6578616D706C65',
    "index": '46813BE38B798B3752CA590D44E7FEADB17485649074403AD1761A2835CE91FF'
  },
  "validated": true
}

```

Upon receiving this response:

- A DID Document can be retrieved from the `DIDDocument` field
- An IPFS address (CAS) can be retrieved from the `URI` field. This address can then be resolved to retrieve additional DID Document(s) and/or associated data.
- Attestation data can be retrieved from the `Data` field.

:notebook: It is recommended that the applications implementing this method extend it to enable DID document/data fetching from the retrieved URI.

Alternatively, one can use the [`account_objects`](https://xrpl.org/account_objects.html#) command. Use the `account` field to specify the Account ID to retrieve all objects owned by that account, including `DID` object in the raw ledger format. Or optionally use the `type` field to filter the results by `ledger_entry` type, i.e. `DID` to retrieve the contents of just the `DID` object.

## 5.3. DIDDelete Transaction

XRP ledger `DID` object owner or controller MAY want to delete the object. For this, we introduce a new transaction type called **`DIDDelete`**. A successful transaction will remove the ledger object and reduce the reserve requirement of the owner account.

### 5.3.1. Example **`DIDDelete`** JSON

```
{
    "TransactionType": "DIDDelete",
    "Account": "rp4pqYgrTAtdPHuZd1ZQWxrzx45jxYcZex",
    "Fee": "12",
    "Sequence": 391,
    "SigningPubKey":"0293A815C095DBA82FAC597A6BB9D338674DB93168156D84D18417AD509FFF5904",
    "TxnSignature":"3044022011E9A7EE3C7AE9D202848390522E6840F7F3ED098CD13E...",
    ...
}
```

A successful `DIDDelete` transaction deletes the `DID` object corresponding to the `Account`

### 5.3.2. Transaction-Specific Fields

| Field Name        |     Required?      | JSON Type | Internal Type |
| ----------------- | :----------------: | :-------: | :-----------: |
| `TransactionType` | :heavy_check_mark: | `string`  |   `UINT16`    |

Indicates the new transaction type **`DIDDelete`**. The integer value is 41.

---

| Field Name |     Required?      | JSON Type | Internal Type |
| ---------- | :----------------: | :-------: | :-----------: |
| `Account`  | :heavy_check_mark: | `string`  |  `AccountID`  |

Indicates the account that initiated the transaction.

---

| Field Name |     Required?      | JSON Type | Internal Type |
| ---------- | :----------------: | :-------: | :-----------: |
| `Fee`      | :heavy_check_mark: | `string`  |   `Amount`    |

Indicates the fee that the account is willing to pay for this transaction.

# 6. Privacy and Security Considerations

There are several security and privacy considerations that implementers would want to take into consideration when implementing this specification.

## 6.1. Key Management

The entity which controls the private key associated with the `DID` object, i.e. the XRPL `Account` also effectively controls the reference to the DID Document which the DID resolves to. Thus great care should be taken to ensure that the private key is kept private. Methods for ensuring key privacy are outside the scope of this document.

## 6.2. DID Document Public Profile

The DID document or other data associated with the XRPL DID's `URI` and/or `Data`, and/or `DIDDocument` fields can contain any content, though it is recommended that it conforms to the W3C DID Document and Verifiable Credentials (VC) specification. As anchored DIDs on XRPL can be resolved by anyone, care should be taken to only update to resolve DID Documents and data which DO NOT expose any sensitive personal information, or information which one may not wish to be public. DID documents should be limited to verification methods and service endpoints, and SHOULD not store any personal information.

## 6.3. IPFS and Canonicity

IPFS allows anyone to store content publicly on the nodes in a distributed network. A common misconception is that anyone can edit content, however the content-addressability of IPFS means that this new edited content will have a different address to the original. While any entity can copy a DID Document anchored with an XRPL account's `DIDDocument` or `URI` fields, they cannot change the document that a DID resolves to via the XRPL `account_objects` resolution unless they control the private key which created the corresponding `DID` object.

For more, see [§ 10. Privacy Considerations](https://www.w3.org/TR/did-core/#privacy-considerations) in did-core.

# 7. Implementations

A proposed implementation is in progress here: https://github.com/XRPLF/rippled/pull/4636/

# 8. Appendices

## Appendix 1. DID Document

A DID is associated with a DID document. A DID document contains the necessary information to cryptographically verify the identity of the DID subject. W3C defines the [core properties](https://www.w3.org/TR/did-core/#core-properties) in a DID document, that describe relationships between the DID subject and the value of the property. For example, a DID document could contain cryptographic public keys such that the DID subject can use it to authenticate itself and proves its association with the DID. Usually, a DID document can be serialized to JSON representation or JSON-LD representation (see [DIDs v1.0]).

Applications may choose one of the following for the DID document associated with a DID:

- Store a reference on the ledger in the `URI` field of `DID` object to the DID document stored in one or more parts on other decentralized storage networks such as IPFS or STORJ.
- Store a minimal DID document in the `DIDDocument` field of the `DID` object.
- Specify a minimal implicit DID document generated from the DID and other available public information.

While not normative, a sample XRPL DID Document MAY look like:

```
{
  	"@context"   : "https://w3id.org/did/v1",
  	"id"         : "did:xrpl:1:rf1BiGeXwwQoi8Z2ueFYTEXSwuJYfV2Jpn",
 	"publicKey"  : [
		 		{
   	        		"id" :  "did:xrpl:1:rf1BiGeXwwQoi8Z2ueFYTEXSwuJYfV2Jpn #keys-1",
    	       		"type" :  ["CryptographicKey", "EcdsaKoblitzPublicKey"],
    	       		"curve" :  "secp256k1",
   	           		"expires" :  15674657,
    	       		"publicKeyHex": "04f42987b7faee8b95e2c3a3345224f00e00dfc67ba882…."
  				} ]
}
```

W3C defines the [core properties](https://www.w3.org/TR/did-core/#core-properties) in a DID document, that describe relationships between the DID subject and the value of the property.

## Appendix 2. Universal Resolver

A Universal Resolver is an identifier resolver that works with any decentralized identifier system, including W3C DIDs. Refer [here](https://github.com/decentralized-identity/universal-resolver). A driver for XRPL DID method resolution will be added to universal resolver configurations to make it publicly accessible.

## Appendix 3. Frequently Asked Questions

Q: Why use "Data" as the field name instead of a more specific term?

A: The term "Data" was chosen to maintain flexibility and inclusivity within the specification. While some issuers refer to this information as "Attestations," others may use alternative terminology such as "public validations" or other terms. By using the term "Data," we aim to ensure that the specification remains adaptable to various implementations and promotes interoperability and broader applicability across the ecosystem of decentralized identity systems.
