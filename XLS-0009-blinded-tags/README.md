<pre>
    xls: 9
    title: Blinded Tags
    author: Nik Bougalis (@nbougalis)
    description: Introduces _tag blinding_, a blinded tag is mutated in such a way that it is meaningful only to the sender and the recipient of a transaction, but appears random to everyone else.
    created: 2020-03-31
    proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/22
    status: Stagnant
    category: Amendment
</pre>

# Abstract

The XRP Ledger supports source and destination tags which can allow a single account to hold funds for multiple users. These arrangements are commonly called _hosted wallets_. When sending _from_ a hosted wallet, the account uses a **source tag** to tell which user prompted the transaction. When sending _to_ a hosted wallet, the **destination tag** tells the account how to further distribute those funds.

A typical example is an exchange like Bitstamp. When you want to deposit funds, Bitstamp provides two pieces of information: an address identifying a Bitstamp wallet, and a destination tag. Several (if not all) Bitstamp customers use the same Bitstamp address, but each customer gets a separate, unique destination tag.

A destination tag is presently an unsigned 32-bit integer. This means that there are 4,294,967,296 possible destination tags. While that's certainly enough tags to allow an exchange to use a unique tag per customer today and perhaps even for the foreseeable future, using a fixed tag presents privacy challenges: it allows transactions to be correlated by treating the `{ address, tag }` pair as a unique address corresponding to a single customer.

As a possible workaround, exchanges could allow users to generate new tags as necessary. In fact, several existing exchanges do just that. The problem with this scheme is that it complicates things for the exchange and for the customer. This also uses more destination tags, which are still finite.

This proposal attempts to alleviate this concern by specifying a standard that allows for _tag blinding_. A blinded tag is mutated in such a way that it is meaningful only to the sender and the recipient of a transaction, but appears random to everyone else.

# The Proposal

The goal of this proposal is to ensure that if blinded tags are in use, an attacker capable of observing every payment transaction will be unable to isolate a pair of transactions that refer to the same unblinded tag. This proposal aims to be secure, minimal, and performant; ideally, it should be possible to implement tag blinding as a single function call that does not noticeably increase the time necessary to assemble a transaction. Similarly, using a blinded tag should not make it significantly harder for the intended recipient to process a transaction.

## Protocol Changes

This proposal assumes several new flags and fields for supporting blinded destination tags. One amendment to the XRP Ledger would introduce all of the following:

Two new [AccountRoot ledger-state flags](https://xrpl.org/accountroot.html#accountroot-flags):

- `lsfRequiresBlindedTags`
- `lsfSupportsBlindedTags`

Two corresponding [AccountSet flags](https://xrpl.org/accountset.html#accountset-flags) to be used for enabling and disabling these flags:

- `asfRequiresBlindedTags`
- `asfSupportsBlindedTags`

#### Interaction between `lsfRequireDest` and blinded tags:

If the existing `lsfRequireDest` account flag is set on an account, then all transactions for which a `DestinationTag` can be specified must include a destination tag. For accounts which support blinded tags, the `BlindedDestinationTag` may be specified instead. More specifically:

|  `lsfRequireDest`  | `lsfSupportsBlindedTags` | `lsfRequiresBlindedTags` | Description                                                                        |
| :----------------: | :----------------------: | :----------------------: | :--------------------------------------------------------------------------------- |
|        :x:         |           :x:            |           :x:            | The `DestinationTag` may be used. The `BlindedDestinationTag` may **not** be used. |
|        :x:         |           :x:            |    :heavy_check_mark:    | The `BlindedDestinationTag` may be used. The `DestinationTag` may **not** be used. |
|        :x:         |    :heavy_check_mark:    |           :x:            | The `DestinationTag` or `BlindedDestinationTag` may be used.                       |
|        :x:         |    :heavy_check_mark:    |    :heavy_check_mark:    | Invalid configuration.                                                             |
| :heavy_check_mark: |           :x:            |           :x:            | The `DestinationTag` is required. The `BlindedDestinationTag` may not be used.     |
| :heavy_check_mark: |           :x:            |    :heavy_check_mark:    | The `BlindedDestinationTag` is required. The `DestinationTag` may not be used.     |
| :heavy_check_mark: |    :heavy_check_mark:    |           :x:            | Either the `DestinationTag` or `BlindedDestinationTag` is required.                |
| :heavy_check_mark: |    :heavy_check_mark:    |    :heavy_check_mark:    | Invalid configuration.                                                             |

#### New optional Transaction fields:

|           Tag           |     Type     | Description                                                                                                                       |
| :---------------------: | :----------: | :-------------------------------------------------------------------------------------------------------------------------------- |
|   `BlindedSourceTag`    | 64-bit UInt  | Blinded analog of `SourceTag`. If this tag is provided, the `SourceTag` field MUST NOT be provided.                               |
| `BlindedDestinationTag` | 64-bit UInt  | Blinded analog of `DestinationTag`. If this tag is provided, the `DestinationTag` field MUST NOT be provided.                     |
|     `KeyIdentifier`     | 32-bit UInt  | MUST BE provided if and only if the transaction also provides a `BlindedSourceTag` field, `BlindedDestinationTag` field, or both. |
|      `RandomValue`      | 256-bit UInt | MUST BE provided if and only if the transaction also provides a `BlindedSourceTag` field, `BlindedDestinationTag` field, or both. |

**Note:** The new fields are supported on transaction which support the `DestinationTag` and `SourceTag` fields. Not all transaction types support them.

The rest of this specification describes the use and meaning of these new fields and flags.

## Usage

In order to **receive** transactions with blinded tags, individuals accounts must opt-in to the feature set. This will be accomplished through the new and existing account settings, which can be enabled with an [AccountSet transaction](https://xrpl.org/accountset.html).

- The recipient must create a new **`secp256k1`** keypair. The sender must set the public key of this keypair as the `MessageKey` of their account. Effectively, this means that the exchange will have associated an additional public key to their receiving wallet address.
  - The `MessageKey` account field already exists in the XRP Ledger and is not used for any specific purpose at the time of writing.
- The recipient must enable one of two new account flags:
  - `RequiresBlindedTags` if you _must_ use blinded destination tags to send to this address, or
  - `SupportsBlindedTags` if you _may_ use blinded destination tags to send to this address.

You do not need to configure any settings in the XRP Ledger to send transactions using blinded destination tags.

### ECIES

This proposal uses [ECIES](https://en.wikipedia.org/wiki/Integrated_Encryption_Scheme) to securely derive a shared key between the sender and the recipient, from which the blinding factors can be derived.

The ECIES process is different for the sender and the recipient.

#### Common Information required

Both sender and recipient need the following common information:

1. The elliptic curve domain parameters for **secp256k1** _( `p` , `a` , `b` , `G` , `n` , `h` )_.
2. The key derivation function _KDF_ = **RIPEMD-160**.
3. The sequence number (or ticket number) associated with the transaction, _N_.

##### Sender

The process always begins with the sender, who can choose whether to use blinded tags or not. Depending on the configuration of the recipient's account, blinded destination tags may or may not be supported and, if supported, may or may not be required. It is the responsibility of the sender to assemble the transaction appropriately.

In addition to the common information, the sender requires:

- The recipient's **secp256k1** public key, _K<sub>pub</sub>_

  (The recipient publishes this in their account's `MessageKey` field.)

###### Steps:

1. Generate a random number _r_, between 0 and 2<sup>128</sup>-1, and calculate _R = rG_.
2. Calculate _P = rK<sub>pub</sub>_.
3. Calculate the shared encryption key _X = KDF(P<sub>x</sub> || N),...)_ where _P<sub>x</sub>_ represents the x-coordinate of the point _P_ which **should not** be the point at infinity, and `...` denotes any additional parameters the function may require.
4. Return _{X, R}_.

##### Recipient

In addition to the common information, the recipient requires:

- The value _R_ that the sender calculated.

###### Steps:

1. Calculate _P = K<sub>sec</sub>R_.
2. Calculate the shared encryption key _X = KDF(P<sub>x</sub> || N),...)_ where _P<sub>x</sub>_ represents the x-coordinate of the point _P_ which **should not** be the point at infinity, and `...` denotes any additional parameters the function may require.
3. Return _{X, R}_.

### Random Blinding Factor Generation

The sender and recipient must generate the same blinding factors in order for this proposal to work. This specification explicitly outlines the algorithm to use. To ensure interoperability, implementers must not deviate from this specification.

Using ECIES the sender and recipient can each derive the same 160-bit shared secret value _X_, then split this value into a 32-bit **key identifier** and two 64-bit **blinding factors**, as follows:

- To get _B<sub>dst</sub>_, the **destination tag blinding factor**: _X mod 2<sup>64</sup>_.
- To get _B<sub>src</sub>_, the **source tag blinding factor tag**: _(X >>> 64) mod 2<sup>64</sup>_, where `>>>` is the "right shift" operator.
- To get _Z_, the **key identifier**: _(X >>> 128) mod 2<sup>32</sup>_, where `>>>` is the "right shift" operator.

Both 64-bit tag blinding factors must remain secret. The 32-bit key identifier is made public.

## What the sender of a transaction does

If the sender determines that the recipient of a transaction supports blinded tags, **the sender** does the following:

1. Calculate the shared secret using ECIES.
2. If a blinded destination tag is required:
   1. Start with an unblinded destination tag, _U<sub>dst</sub>_.
   2. Calculate the destination tag blinding factor _B<sub>dst</sub>_ as explained above.
   3. Calculate the blinded destination tag as _T<sub>dst</sub> = U<sub>dst</sub> ⊕ B<sub>dst</sub>_.
   4. Set the `BlindedDestinationTag` field in the transaction to _T<sub>dst</sub>_.
3. If a blinded source tag is required:
   1. Start with an unblinded source tag, _U<sub>src</sub>_.
   2. Calculate the source tag blinding factor _B<sub>src</sub>_ as explained above.
   3. Calculate _T<sub>src</sub> = U<sub>src</sub> ⊕ B<sub>src</sub>_.
   4. Set the `BlindedSourceTag` field in the transaction to _T<sub>src</sub>_.
4. Calculate the key identifier _Z_ as explained above.
5. Set the `KeyIdentifier` field in the transaction to _Z_.
6. Set the `RandomValue` field in the transaction to _R_.

## What the recipient of a transaction does:

When the recipient receives a transaction, they examine if the transaction for the presence of the `BlindedDestinationTag` and `BlindedSourceTag` fields; if they are present, the recipient needs to preprocess the transaction to unblind the tags. **The recipient** unblinds the tags as follows:

1. Extract the random value _R_ from the `RandomValue` field.
2. Calculate the shared secret using ECIES and `R`.
3. If the `KeyIdentifier` field is present, do the following:
   1. Calculates the key identifier _Z_ as explained above.
   2. Compares _Z_ to the `KeyIdentifier` field in the transaction.
   3. If _Z_ and the `KeyIdentifier` field are not the same, try to use an older keypair to determine the secret key to use. (Older keypairs are based on all `MessageKey` values the recipient has previously set.)
4. If the `BlindedDestinationTag` field is present:
   1. Calculate the destination tag blinding factor _B<sub>dst</sub>_ as described above.
   2. Calculates the unblinded destination tag _U<sub>dst</sub> = `BlindedDestinationTag` ⊕ B<sub>dst</sub>_.
5. If the `BlindedSourceTag` field is present:
   1. Calculate the source tag blinding factor _B<sub>src</sub>_ as described above.
   2. Calculate the unblinded source tag _U<sub>src</sub> = `BlindedSourceTag` ⊕ B<sub>src</sub>_.

Once the preprocessing stage is complete, the recipient now processes the incoming transaction normally, but uses the calculated unblinded source and destination tags (_U<sub>src</sub>_ and _U<sub>dst</sub>_ respectively) instead of the blinded tags present in the transaction.

## Miscellaneous Details

### Privacy Comment:

A different blinding factor is used for source and destination tags. This is necessary because of the nature of the exclusive OR operator. Consider:

    X = A ⊕ K
    Y = B ⊕ K

Now, consider:

    X ⊕ Y = (A ⊕ K) ⊕ (B ⊕ K) = (A ⊕ B) ⊕ (K ⊕ K) = A ⊕ B

So, if both a source and a destination tag are present and the same blinding factor is used for both, then performing an exclusive OR operation "cancels out" the blinding factor and yields a stable token for a given pair _U<sub>src</sub>_ and _U<sub>dst</sub>_. By using separate blinding factors for the two, this attack is mitigated.

### Tag Address Space Extension

The existing `SourceTag` and `DestinationTag` fields are defined 32-bit values. As stated earlier, this restricts the number of tags available. Several questions about extending the fields to 64-bit have been raised. While a protocol extension could be implemented, redefining the existing fields as 64-bit values, such a change would be highly disruptive and would break existing code.

Since the `BlindedSourceTag` and `BlindedDestinationTag` fields are new, no backward compatibility issues are present. Furthermore, since the new fields are opt-in (that is, both the source and the destination must explicitly _opt in_ for the fields to be usable, existing code can continue operating normally.

Therefore, this proposal purposefully chooses to define `BlindedSourceTag` and `BlindedDestinationTag` as 64-bit fields, and to allow the underlying 'unblinded' tags to have a usable range of _0_ through _2<sup>64</sup>_ inclusive.

### Perfect Forward Secrecy

The scheme proposed does not afford perfect forward secrecy. The compromise of the recipient's secret key could allow an attacker to "unblind" the source and destination tags for all transactions where the compromised key or its corresponding public counterpart was used.

While implementing a scheme that affords perfect forward secrecy is possible, the additional complexity associated with doing so seems excessive, given the stated goal of this proposal: to improve the privacy of the existing system, where source and destination tags are transported in cleartext.

## Integration with the X-address specification

The recently proposed and adopted [**X-address**](https://github.com/xrp-community/standards-drafts/issues/6) format allows the packed encoding of an address and a destination tag into a single address.

The blinding scheme is not conducive to pre-generation of blinded tags. Despite this, we recommend adding de minimis support, by allowing the use of 64-bit tags by setting that `TAG_64` field in the **X-address**.

The tag specified in the **X-address** should be unblinded; applications (wallets) should accept such addresses and blind the tag, if appropriate, according to the sender's configuration.

## Integration with tickets

No consideration is given at this time on how this scheme integrates with tickets.
