<pre>
  xls: 55
  title: Remit
  description: Atomic Multi-Asset Payments for XRPL Protocol Chains
  author: Richard Holland (@RichardAH)
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/156
  created: 2023-12-03
  status: Final
  category: Amendment
</pre>

## Introduction

**_Remit_** is a new payment transactor designed for XRPL Protocol Chains, which allows a sender to send multiple currencies and tokens atomically to a specified destination. It is a push payment that delivers "no matter what" and is designed for retail and Hooks use-cases.

## Constraints

Using _Remit_ the sender may send:

- one or more Issued Currencies, and/or,
- one or more pre-existing URITokens owned by the sender and/or,
- one new URIToken created in-line as part of the transaction.

The transactor has the following behaviours:

- If the destination does not exist, the sender pays to create it.
- If the destination does not have the required trust-lines, the sender pays to create these.
- The exact amounts and tokens are always delivered as specified in the transaction, if validated with code tesSUCCESS.
- The sender pays all transfer fees on currencies, and the fees are not subtracted from the sent amount.
- Where the sender pays to create objects, this is a separate amount not taken from the amounts specified in the transaction.
- The transaction is atomic, either all amounts and tokens are delivered in the exact specified amount or none of them are.
- The transactor does no conversion or pathing, the sender must already have the balances and tokens they wish to send.
- When no amounts or tokens are specified, the transaction may still succeed. This can be used to create an account or ensure an account already exists.

## Specification

A _Remit_ transaction contains the following fields:
Field | Required | Type | Description
-|-|-|-
sfAccount | ✅ |AccountID | The sender
sfDestination | ✅ |AccountID | The recipient. Does not need to exist. Will be created if doesn't exist.
sfDestinationTag | ❌ |UInt32 | May be used by the destination to differentiate sub-accounts.
sfAmounts | ❌|Array of Amounts | Each of the currencies (if any) to send to the destination. Sender must have funded trustlines for each. Destination does not need trustlines.
sfURITokenIDs | ❌| Array of URITokenIDs | Each of the URITokens (if any) to send to the destination.
sfMintURIToken | ❌| URIToken | If included, an inline URIToken to be created and delivered to the destination, for example a receipt.
sfBlob | ❌ | Blob | A hex blob up to 128 kib to supply to a receiving Hook at the destination.
sfInform | ❌ | AccountID | A third party. If supplied, their Hooks will be weakly executed (but the sender will pay for that execution).
sfInvoiceID | ❌ | UInt256 | An arbitrary identifier for this remittance.

## Example Transaction

```
{
      "TransactionType" : "Remit",
      "Account" : "rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh",
      "Destination" : "raod38dcxe6AGWfqxtZjPUfUdyrkWDe7d",
      "Amounts" : [
         {
            "AmountEntry" : {
               "Amount" : "123"
            }
         },
         {
            "AmountEntry" : {
               "Amount" : {
                  "currency" : "USD",
                  "issuer" : "rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh",
                  "value" : "10"
               }
            }
         },
         {
            "AmountEntry" : {
               "Amount" : {
                  "currency" : "ABC",
                  "issuer" : "rpfZurEGaJvpioTaxYpjh1EAtMXFN1HdtB",
                  "value" : "12"
               }
            }
         }
      ],
      "URITokenIDs" : [
         "C24DAF43927556F379F7B8616176E57ACEFF1B5D016DC896222603A6DD11CE05",
         "5E69C2D692E12D615B5FAC4A41989DA1EA5FD36E8F869B9ECA1121F561E33D2A"
      ],
      "MintURIToken" : {
         "URI" : "68747470733A2F2F736F6D652E757269"
      }
}
```

## Unwanted Remits

Users who do not want to receive _Remit_ transactions can either set the _asfDisallowIncomingRemit_ on their accounts or install a Hook that will regulate incoming Remits. Alternatively they can simply burn unwanted URITokens or return unwanted Issued Currencies in order to claim the reserve that was paid by the sender.

## Chain Requirements

XLS-55 depends on the adoption of XLS-35 on the applicable chain.
