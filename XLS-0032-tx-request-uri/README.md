<pre>
    xls: 32
    title: Request URI Structure
    author: Ryan (@interc0der)
    description: A standard URI schema for making payments and sharing data between platforms on the XRP Ledger
    created: 2022-07-28
    proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/81
    status: Stagnant
    category: Ecosystem
</pre>

# Abstract

This proposal is a standard URI schema for making payments and sharing data between platforms on the XRP Ledger.

While developing on the XRP Ledger, it is common to create a payment request schema for manufacturing and storing transaction objects in a database. These objects, and/or the architecture in which they are stored, are usually proprietary and not interoperable with other applications or tools. A well-thought schema would enable a broader ecosystem of applications that can exchange ledger-related data.

The main goal of this proposal is to promote interoperability between applications and prioritize user accessibility, by standardizing a URI schema (syntax and semantics) for off-chain requests on the XRP Ledger.

# 1. Introduction

As adoption of the XRP Ledger grows and more developers build applications on top of the XRP Ledger, commonly agreed-upon standards are increasingly important for interoperability and prioritizing user accessibility on the XRP Ledger.

Certain features of the XRP Ledger require the construction and/or storage of payment requests. For instance, a user might want to send a payment request to a client in the form of an invoice. This invoice, amongst other things, is essentially a future payload to be resolved by the client. Currently, a developer could assign this invoice a universally unique identification number (UUID) and store its corresponding payload within a database. Alternatively, the developer could choose to convert this invoice into a payment link or QR code. If the latter is chosen, this link or QR Code might not be interoperable with other applications or platforms.

### 1.1 Context Example

XRPL Labs, by way of the XUMM app, relies upon QR codes for main interactions between their mobile app and xApps. They have chosen a structure or schema for payloads that closely resembles the payload schema for signing payments on the XRP Ledger. For this reason, their implementation and methodology are advantageous to a standardized URI scheme for links and non-XUMM QR Codes.

### 1.2 Problem/Solution

Limitations to this payload structure include passing simple parameters such as account address, destination tag, or messages. A thoughtful and defined XRPL URI standard could give direction to new developers and could provide more interoperability between applications. See [XLS-2](../XLS-0002-destination-information/README.md) for the beginning discussions around a URI standard for combining account addresses and destination tags, represented by query parameter “dt”.

### 1.3 Motivation

The purpose of this standard is to create a universal URI schema for links and QR codes that are commonly used in making payments today. Large inspiration is taken from the URI schema standards from Bitcoin BIP-0021 and Ethereum EIP 681.

# 2. Specifications

### 2.1 Generic Syntax

Uniform Resource Identifiers (URI’s) are defined and their general syntax is documented by the Network Working Group in RFC 2396. A later foundational publication was made for URI syntax in RFC 3986, making RFC 2396 obsolete and consolidating other URI publications under a unified standard.

The URI syntax is dependent upon the scheme. In general, absolute
URI are written as follows:

```
      <scheme>:<scheme-specific-part>
```

Refer to Appendix A for common syntax variables found within RFC 2396.

These variables will be used for defining the syntax for the URI schema within this proposed standard. In addition, this standard will use Augmented Backus-Naur Form (ABNF) syntax notion [RFC2234] which corresponds to the notion used in RFC 3986.

### 2.2 Syntax

The absolute URI of the XRPL URI standard may be written as follows:

```
      <protocol>:<type><query>
```

### 2.3 Protocol

The protocol component defines the scheme name for the URI. Per RFC 3986, “the scheme name refers to the specification for the assigning identifier within that scheme.” For this standard, and the scheme within, the protocol shall be defined as follows:

```
      protocol = ﹡( "xrpl" [ "." version ] )
```

### 2.3.1 Versioning

The protocol will contain a version identifier for backward compatibility and flexibility for future alterations to the URI’s schema rules.

### 2.4 Type

The `type` component defines the particular type of data held within the URI.

```
      type = ﹡( "account"
		/ "ledger"
		/ "tx"
		/ "payload"
		/ "offline"
		/ "token"
		/ "nftoken" )
```

It should be noted that we are intentionally not defining an `action` here. While the URI type implies an action to be taken by the receiving application, this standard is not explicitly defining an action or function. An `action` component could be added to this standard in the future.

### 2.5 Query

The `query` component will share the general formatting as defined in RFC 3986.

For this standard, only particular parameters will be acceptable. The limitations or restrictions to the acceptable parameters are made for a few reasons: (1) **size** - limits the size of link or size of the data for accessibility, and (2) **security** - a controlled parameter field limits attack vectors and future vulnerabilities.

Those acceptable parameters will be dependent on the <type> of the URI.

```
    query =  "?" ﹡( account_data
			    / ledger_data
			    / tx_data
			    / payload_data
			    / offline_data
			    / token_data
			    / nftoken_data )

```

---

If the type of the URI is `account`, the acceptable query is written as follows:

```
    account_data = ﹡( ( ﹡( "address" "=" <address> ) [ "tag" "=" <tag> ] ) / ﹡( "xaddress" "=" <address> ) )

```

---

If the type of the URI is `ledger`, the acceptable query is written as follows:

```
    ledger_data = ﹡( "seq" "=" <sequence> )
```

---

If the type of the URI is `tx`, the acceptable query is written as follows:

```
    tx_data = ﹡( "hash" "=" <hash> )
```

---

If the type of the URI is `payload`, the acceptable query is written as follows:

```
    payload_data = ﹡( "tx" "=" <binary> ) <callback>

    callback = [ uuid=uuid url=url jwt=authToken ]
```

---

If the type of the URI is `offline`, the acceptable query is written as follows:

```
    offline_data = ﹡( "blob" "=" <binary> ) <callback>

    callback = [ uuid=uuid url=url jwt=authToken ]
```

\*\*\*
If the type of the URI is `token`, the acceptable query is written as follows:

```
    token_data = ﹡( "address" "=" <address> ) *( "code" "=" <code> )
```

---

If the type of the URI is `nftoken`, the acceptable query is written as follows:

```
    nftoken_data = ﹡( "id" "=" <id> )
```

### 2.6 Semantics

The `type` field is required. This is how we determine what type of XRPL data is being passed by the URI. All Characters must be properly URI encoded.

### 2.6.1 Account Type

This type is intended for passing a single XRPL address and tag. Currently, you can achieve this same functionality by the use of XLS 2. This standard will supersede XLS 2.

The address parameter is required for this data type. The tag parameter is optional.

> _Address, string, secp256k1 or ED25519, length 33 bytes to 36 bytes_

### 2.6.2 Ledger Type

This type is intended for passing a ledger data block of the XRP Ledger.

The seq parameter is required for this data type.

> _Sequence Number, integer, 256 bits_

### 2.6.3 Tx Type

This type is intended for passing a transaction hash of the XRP Ledger.

The hash parameter is required for this data type.

> _Hash, string, hex, 256 bits_

### 2.6.4 Payload Type

The `payload` type is reserved for preparing transactions on the XRP Ledger. It is intended that this type will be used in conjunction with an XRPL client.

The transaction parameter is the only field required. The transaction parameter should be a serialized representation of an XRPL transaction object. For acceptable fields and formats, see the submit command method and options [here](https://js.xrpl.org/modules.html#Transaction).

### 2.6.5 Offline Type

The `offline` type is reserved for sending offline, air-gapped, signed transaction (binary) data to an online machine for submission and validation on the ledger.

The signed parameter is the only field required. For more information on offline transactions on the XRP Ledger, see [here](https://xrpl.org/offline-account-setup.html).

> _Blob, tx_blob, string, hex, 256 bits_

### 2.6.6 Token Type

This type is intended for passing a single XRPL issuing address and issued currency code.

The address parameter is required for this data type. The currency parameter is required.

Address, string, secp256k1 or ED25519, length 33 bytes to 36 bytes

> _Currency code, 3-character string or 160-bit hexadecimal_

### 2.6.7 Nftoken Type

This type is intended for passing the id of a certain nftoken on the XRP Ledger.

The id parameter is required for this data type.

> _TokenID, string, Hash256, 256 bits_

# 3. Considerations

### 3.1 Security

By accessing data directly within the URI, most of the security discussions around path resolution in RFC 3986 do not apply to this URI standard. However, like most forms of communication on the internet, when an application is receiving data from an untrusted, third-party, incoming data needs to be strictly parsed and users need to be aware of the inherent risks.

### 3.1.1 Cross-Site Request Forgery (CSRF)

Any time an application accesses data from an outside source, in the form of a QR code or link, it should be recognized that the data may be corrupted or incorrect. To avoid forgery, all data from the incoming URI should be reviewed and confirmed by the user before proceeding. This step is especially important when dealing with payloads or payments that concern value. For instance, a user might bring in a malformed payload from an outside application using this standard. The malformed payload might contain payment to an unexpected address. In this case, the receiving application should ask the user to review the incoming data to prevent any unexpected behavior or loss of funds.

### 3.1.2 Strict Parsing Rules

Incoming data should have strict parsing rules to prevent unexpected behaviors. For this standard, we are intentionally defining a set of data types and a set of accepted parameters to simplify the parsing and data cleansing, reducing potential attack vectors. All fields have strict types and data limits to avoid hidden redirects and/or phishing schemes.

### 3.2 Resolved Requests

### 3.2.1 Callback

For applications looking for status updates on an issued URI, callback parameters are defined for both the Payload URI and the offline URI. It is envisioned that status update callback functionality will behave similarly to OAuth2 authentication protocols. The callback parameters let the issuing application define a payload UUID, endpoint for receiving responses, and a JSON Web Token (JWT). Main status updates for payloads include “/scan”, “/sign”, “/reject”, “/error”, and “/expire”. Responses will be sent to the endpoint provided in the callback URL with respective slug parameters. Response URL will be written as follows:

```
    https://{URL}/{uuid}/{status}
```

If desired, it is the responsibility of the original party to capture and process each response.

### 3.2.2 Tickets and Sequence Numbers

Alternatively, the issuing application can ask the user to reserve sequence numbers for their URI payloads. Payloads can be assigned to one of the sequence numbers and the issuing application can check the sequence number to determine if the payload has been resolved by any counterparty.

### 3.2.3 Shared Database

If the issuing party and the signing party have access to the same database, payload status can be tracked and recorded within the shared database. Each party would then be able to check and verify the status of the request.

### 3.3 Size Limitations

The main goal of this standard is to create a unified way to pass data between applications. In order to gain full adoption, we have to be careful that the packets of data do not exceed a certain bytecode threshold.

Why? Typical QR codes have 177x177 modules, or 31,329 squares, holding up to 3KB of encoded data. This translates to roughly 4,269 alphanumeric characters at the lowest redundancy settings. Larger QR codes could hold more data with larger redundancy, but in order to have QR codes accessible on smaller, low-end devices, the encoded data should not exceed that of 3KB.

Considering the size limitations, we have chosen to split the URI into data type categories. This prioritizes data relevancy, segmenting data based on type to ensure the smallest possible packets of data. The largest sized URI in this standard will come from the payload URI. Running some experiments, payload URI’s should be anywhere between 100 and 1000 alphanumeric characters, which is under the 4,269 limit.

# 4. Backward Compatibility

Adopting previous standards and schemas, if the data type field is not provided, the schema will fall back to XLS 2. The schema is written as follows:

```
      "xrpl" ":" ﹡( address ) [ "&" "dt" "=" tag ]
```

```
      address = ALPHANUM
      tag = DIGIT
```

# 5. Conclusion

As we continue to build on the XRP Ledger, it is imperative to work together as a cohesive developer community and align standards that improve the overall experience of users. This proposal presents a standard URI schema to pass data between applications in a unified way.

### Summary

The following summarizes the main points within this proposal.

1.  Interoperability should be a key focus when sharing data between different applications and ecosystems.

2.  (7) type categories are presented to help describe the data contained within the requested QR code or link.

3.  Considerations are made for security, resolve mechanism, size limits, and backward compatibility.

### Call to Action

Upon review of this proposal, we encourage teams to start an internal discussion around adopting this standard. From the points made within this proposal, it is clear that the ecosystem could use a consistent URI structure, and with full community support and adoption, users would benefit from the accessibility and interoperability when sharing data & transactions between applications.

---

To help kickstart discussion, below is a list of questions teams may consider:

1. How easy is it to integrate a standard URI within our codebase?

2. Are there any features or data types that are needed for your business which are not found within this proposal?

3. Does this standard enable a more consistent ecosystem for users? Will your users benefit from adopting this standard or something similar?

---

Please consider leaving your thoughts, criticism, and addendums in the comment section below. We are eager to hear feedback from the community and look forward to a strong critique. This will help make improvements, and hopefully, finalize the standard for use in existing & future projects.

# Appendices

### Appendix A. General Syntax Rules

### A.1 Syntax Variables

```
    URIC          = ( RESERVED / UNRESERVED / ESCAPED )
    RESERVED      = ( ";" / "/" / "?" / ":" / "@" / "&" / "=" / "+" /
                    "$" / "," )
    UNRESERVED    = ( ALPHANUM / MARK )
    MARK          = ( "-" / "_" / "." / "!" / "~" / "*" / "'" /
                    "(" / ")" )
    ESCAPED       = "%" HEX HEX
    HEX           = ( DIGIT / "A" / "B" / "C" / "D" / "E" / "F" /
                    "a" / "b" / "c" / "d" / "e" / "f" )
    UPHEX         = ( DIGIT / "A" / "B" / "C" / "D" / "E" / "F" )
    ALPHANUM      = ( ALPHA / DIGIT )
    LOWALPHA      = %x61-7A ; A-Z
    UPALPHA       = %x41-5A ; a-z
```

### A.2 Data Types Syntax

```
    address = ALPHANUM
    tag = DIGIT

    code = ( UPALPHA / HEX )

    sequence = DIGIT
    hash = HEX

    transaction = (
		AccountDelete
		/ AccountSet
		/ CheckCancel
		/ CheckCash
		/ CheckCreate
		/ DepositPreauth
		/ EscrowCancel
		/ EscrowCreate
		/ EscrowFinish
		/ NFTokenAcceptOffer
		/ NFTokenBurn
		/ NFTokenCancelOffer
		/ NFTokenCreateOffer
		/ NFTokenMint
		/ OfferCancel
		/ OfferCreate
		/ Payment
		/ PaymentChannelClaim
		/ PaymentChannelCreate
		/ PaymentChannelFund
		/ SetRegularKey
		/ SignerListSet
		/ TicketCreate
		/ TrustSet ) ; Refer to <https://js.xrpl.org/modules.html#Transaction>

    binary = HEX

    id = ( UPALPHA / DIGIT )
```

### A.3 Simple Syntax

```
    xrpl ["." version ] ":"
		﹡( "account"
		    / "ledger"
		    / "tx"
		    / "payload"
		    / "offline"
		    / "token"
		    / "nftoken" )
		"?" (   ( address = ALPHANUM [ tag = DIGIT ] )
			/ xaddress = ALPHANUM
			/ hash = UPHEX
			/ seq = DIGIT
			/ tx = UPHEX
			/ id = ( UPALPHA / DIGIT )
			/ code = ( UPALPHA / UPHEX )
			/ blob = UPHEX  )
```

### Appendix B. Examples

### B.1 Account Example

An `account` type with address and tag.

```
    xrpl:account?address=rpfBYsmNBB7Y6z7qHS8g26KE3y3hHaTxkq&tag=000001
```

### B.2 Ledger Example

A `ledger` type with ledger sequence number.

```
    xrpl:ledger?seq=7295400
```

### B.3 Tx Example

A `tx` type with transaction hash.

```
    xrpl:tx?hash=73734B611DDA23D3F5F62E20A173B78AB8406AC5015094DA53F53D39B9EDB06C
```

### B.4 Payload Example

A `payload` type with `AccountRoot` transaction object.

```
    JSON = {
      LedgerEntryType: 'AccountRoot',
      Flags: 0,
      Sequence: 1,
      PreviousTxnLgrSeq: 7,
      OwnerCount: 0,
      PreviousTxnID: 'DF530FB14C5304852F20080B0A8EEF3A6BDD044F41F4EBBD68B8B321145FE4FF',
      Balance: '10000000000',
      Account: 'rLs1MzkFWCxTbuAHgjeTZK4fcCDDnf2KRv'
    } ; prior to serializing

    xrpl:payload?tx=1100612200000000240000000125000000072D0000000055DF530FB14C5304852F20080B0A8EEF3A6BDD044F41F4EBBD68B8B321145FE4FF6240000002540BE4008114D0F5430B66E06498D4CEEC816C7B3337F9982337
```

### B.5 Offline Example

An `offline` type with `offerCreate` transaction object.

```
    JSON = {
      "Account": "rMBzp8CgpE441cp5PVyA9rpVV7oT8hP3ys",
      "Expiration": 595640108,
      "Fee": "10",
      "Flags": 524288,
      "OfferSequence": 1752791,
      "Sequence": 1752792,
      "SigningPubKey": "03EE83BB432547885C219634A1BC407A9DB0474145D69737D09CCDC63E1DEE7FE3",
      "TakerGets": "15000000000",
      "TakerPays": {
        "currency": "USD",
        "issuer": "rvYAfWj5gh67oV6fW32ZzP3Aw4Eubs59B",
        "value": "7072.8"
      },
      "TransactionType": "OfferCreate",
      "TxnSignature": "30440220143759437C04F7B61F012563AFE90D8DAFC46E86035E1D965A9CED282C97D4CE02204CFD241E86F17E011298FC1A39B63386C74306A5DE047E213B0F29EFA4571C2C",
      "hash": "73734B611DDA23D3F5F62E20A173B78AB8406AC5015094DA53F53D39B9EDB06C"
    } ;

    xrpl:offline?blob=120007220008000024001ABED82A2380BF2C2019001ABED764D55920AC9391400000000000000000000000000055534400000000000A20B3C85F482532A9578DBB3950B85CA06594D165400000037E11D60068400000000000000A732103EE83BB432547885C219634A1BC407A9DB0474145D69737D09CCDC63E1DEE7FE3744630440220143759437C04F7B61F012563AFE90D8DAFC46E86035E1D965A9CED282C97D4CE02204CFD241E86F17E011298FC1A39B63386C74306A5DE047E213B0F29EFA4571C2C8114DD76483FACDEE26E60D8A586BB58D09F27045C46
```

### B.6 Token Example

A `token` type with an issuing account and currency code.

```
    xrpl:token?address=rpfBYsmNBB7Y6z7qHS8g26KE3y3hHaTxkq&code=USD
```

### B.7 NFToken Example

A `nftoken` type with id.

```
    xrpl:nftoken?id=000B013A95F14B0044F78A264E41713C64B5F89242540EE208C3098E00000D65
```

# References

#### RFC 2234 - Augmented BNF for Syntax Specifications: ABNF

https://www.rfc-editor.org/rfc/rfc2234

#### RFC 2396 - Uniform Resource Identifiers (URI): Generic Syntax

https://www.rfc-editor.org/rfc/rfc2396

#### RFC 2718 - Guidelines for new URL Schemes

https://www.rfc-editor.org/rfc/rfc2718

#### RFC 3986 - Uniform Resource Identifier (URI): Generic Syntax

https://www.rfc-editor.org/rfc/rfc3986

#### XRPL - XLS-2

https://github.com/XRPLF/XRPL-Standards/blob/master/XLS-0002-destination-information/README.md

#### XRPL - XLS-3

https://github.com/XRPLF/XRPL-Standards/blob/master/XLS-0003-deeplink-signed-transactions/README.md

#### XRPL - XLS-4

https://github.com/XRPLF/XRPL-Standards/blob/master/XLS-0004-trustline-uri/README.md

#### XRPL - XLS-15

https://github.com/XRPLF/XRPL-Standards/blob/master/XLS-0015-concise-tx-id/README.md

#### Ethereum - EIP 681

https://github.com/ethereum/EIPs/blob/master/EIPS/eip-681.md

#### Bitcoin - BIP 0021

https://en.bitcoin.it/wiki/BIP_0021

# Credits

A special thanks to Manuel Otto and Pablo Padillo for offering comments and initial suggestions during the formation of this proposal.

# Implementation

https://github.com/standardconnect/xls-32d

  <p>
    <code>npm install xls-32d@latest</code>
  </p>
  <p>or</p>
  <p>
    <code>yarn add xls-32d@latest</code>
  </p>

Here is an example showing off the consise transaction identifier (CTI) integration.

```

import xls32d from 'xls32';

const input = {
type: 'cti',
params: {
  networkId: 1,
  ledger_hash: 'F8A87917637D476E871D22A1376D7C129DAC9E25D45AD4B67D1E75EA4418654C',
  ledger_index: '62084722',
  txn_hash: '1C0FA22BBF5D0A8A7A105EB7D0AD7A2532863AA48584493D4BC45741AEDC4826',
  txn_index: '25',
},
};

const uri = xls32d.encode(input);
console.log(uri)

```

See unit testing for more examples...
https://github.com/standardconnect/xls-32d/tree/main/tests

# Changelog

2022-07-29

1. Update references to include all previous standards pertaining to URI standardization
   XLS-2 https://github.com/XRPLF/XRPL-Standards/blob/master/XLS-0002-destination-information/README.md
   XLS-3 https://github.com/XRPLF/XRPL-Standards/blob/master/XLS-0003-deeplink-signed-transactions/README.md
   XLS-4 https://github.com/XRPLF/XRPL-Standards/blob/master/XLS-0004-trustline-uri/README.md
   XLS-15 https://github.com/XRPLF/XRPL-Standards/blob/master/XLS-0015-concise-tx-id/README.md

2023-01-22

1. Add implementation https://github.com/standardconnect/xls-32d

2023-02-01

1. Updated to version 0.0.30beta and added to implementation section; https://github.com/standardconnect/xls-32d
