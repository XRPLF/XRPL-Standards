<pre>
    xls: 10
    title: Non-Transferable Token (NTT) standard
    description: A standard for non-transferable tokens on the XRP Ledger
    author: RichardAH (@RichardAH)
    proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/20
    created: 2020-04-05
    status: Stagnant
    category: Ecosystem
</pre>

## Changelog

28-7-21: Name of this standard was changed from `Issuer Controlled Token` to `Non-Transferable Token` to reflect industry norms

## 1. Introduction

The XRPL supports 160bit currency codes as discussed here: [https://xrpl.org/currency-formats.html#nonstandard-currency-codes](https://xrpl.org/currency-formats.html#nonstandard-currency-codes) which include as a subset the standard three letter ISO 4217 codes the reader is probably familiar with (e.g. “USD”, “CAD”, etc.)

The intention of currency codes on the XRPL is to provide fungible IOUs that can be “rippled” between accounts across trusted issuers, facilitating end to end value exchange across multiple unrelated parties on the ledger.

However in recent years, particularly with the rise in popularity of programmable money platforms such as Ethereum, it has become apparent that tokens outside the typical fungible form might also fill important use-cases.

## 2. User Controlled Tokens

The standard IOU on the XRPL exists as a relationship between two parties: a _user_ and an _issuer_. In order to use the issuer’s token, the user must first add a trustline to their XRPL account for the specified currency code and issuer. Once the trustline exists the issuer (or potentially another user) may send IOUs to that trustline balance. More background here: [https://xrpl.org/trust-lines-and-issuing.html](https://xrpl.org/trust-lines-and-issuing.html)

## 3. Non-transferable Tokens (aka Issuer Controlled Tokens)

This standard proposes a second way to use the trustline mechanism on the XRPL: An issuer controlled token.

In this model the user no longer is required to add a trustline to the issuer. In fact the user need not do anything. Instead the issuer creates a trustline from the user to itself with a nominal unity balance for a 160 bit “custom” currency code and with rippling disabled. This currency code contains the token information, the trustline itself is just a storage mechanism.

Any third party looking at the user’s XRPL account will see this “token” attached to the user’s account.

Issuer Controlled Tokens have the following properties:

1. The token is completely controlled by the issuer. The issuer may at any time close the trustline unilaterally, erasing the token from the ledger.
2. The token is inherently non-fungible (although a fungibility layer could be added through smart contacts.)
3. The issuer can revoke and re-issue the token at any time with an updated currency code.
4. The token’s currency encodes 160 bits of arbitrary data (152 bits if excluding the first 8 bits as a type code).
5. The token is publicly visible to anyone who looks up the user’s account on the XRPL.

Possible uses for such a token include black and whitelisting / stamps, smart contract per-account state storage and payment and informational pointers expanding on the purpose, behaviour and/or ownership of an XRPL account.

## 4. Namespace

Much like addresses in Internet Protocol space, 160bit currency codes are at risk of nonsensical and overlapping allocation without some sort of standardised allocation scheme.

By convention the first byte of the 160bit currency code determines the currency code “type”. Byte 0x00 (XRP) cannot be used, and 0x01 has been used previously for demurrage. No complete database of known currency types exists. Some adhoc defacto standards have emerged such as “if the currency code decodes to valid ASCII then display the said ASCII string” but these are not widespread.

In order to preserve top level “type” codes this standard proposes to reserve 0xFF as the type code for Issuer Controlled Tokens.

## 5. Token Specification

[ Type = 0xFF ] [ Sub type = 0x0000-0xFFFF ] [ Payload = 136b ]

Byte 0 – Type code: must be 0xFF meaning Issuer Controlled Token

Byte 1-2 — Subtype code: Unsigned big endian 16 bit integer. Allocated according to a standards database such as this one. This number 0-65,535 tells wallets how to interpret this token.

Byte 3-19 – Payload bytes: 136 bits of arbitrary data the token encodes.

## 6. Spam Prevention

Since it is possible for anyone to be an issuer they may produce a token that appears on any user’s account (provided they are willing to lock up 5 XRP to do so). This produces something of a problem for wallet software: which tokens are legitimate and which are spam?

Wallets should give the user the option to display all Issuer Controlled Tokens or to display only tokens from a whitelist pre-populated by the wallet software. That whitelist should include as a subset a community controlled whitelist described below. The wallet should also allow the end user to update and add entries to the whitelist.

## 7. Allocation and Community Bulletin Board

It is proposed that a community “bulletin board” account be created on the XRPL that has no known private key, I.e. a blackhole account. To this account issuer controlled tokens will be assigned from a community XRPL account controlled collectively by key members of the XRPL community through multi-signing.

In order to whitelist an issuer of a token, the issuer’s 20 byte account ID is truncated at the end by five bytes. Five bytes are then prepended to the start of the account ID in comprising: 0xFF FF FF, followed by the sub-type of the white listed token.

An alternative way to do this would have been to open a trustline to the issuer from the community account, however the above has an additional advantage: by changing the sub-type of the entry to 0xFF FF F**E** we can signal that the token is actually blacklisted rather than whitelisted. Thus the concept of a bulletin board.

Further information relevant to all wallets can be stored on the community bulletin board in this way, simply by allocating subtype numbers for those notice types. For example known scam accounts can be placed on the bulletin board, or URL pointers to lists of known scam accounts.
