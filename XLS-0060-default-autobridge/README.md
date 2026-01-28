<pre>
  xls: 60
  title: Default AutoBridge
  description: Use autobridging in IOU-IOU Payment transactions
  author: tequ (@tequdev)
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/175
  created: 2024-02-05
  status: Stagnant
  category: Amendment
</pre>

## Abstract

Currently, if the Path field is not specified in an IOU-IOU Payment transaction, only direct pairs of two currencies are used internally. This proposal would change this default behavior to use IOU-XRP-IOU as well as OfferCreate transaction's.

## Changes

If the Path field is unspecified in the IOU_A->IOU_B Payment transaction, the path through IOU_A/XRP and IOU_B/XRP is used in addition to the IOU_A/IOU_B path.

If existing transaction types or future transaction types to be implemented are similarly cross-currency transactions, it will be possible to use bridge paths in addition to direct paths by default.

### Technical

Add an additional path with XRP as the intermediate between two currencies to in flow() method in Flow.cpp when `defaultPaths`=`true`.

Use XRP-mediated paths to the paths under the following conditions:

- Path is not specified
- SendMax is set.
- The issuer and currency of Amount and SendMax are different.

### Payment transaction

If the Path field is not specified and the SendMax field is set, the transaction will use the XRP-mediated path.

No impact if the NoRippleDirect flag is set.

### OfferCreate transaction

No impact as Path is always set.

### CheckCash transaction

(using flow())

No impact as it only processes when the fields corresponding to Amount and SendMax are the same.

_If future amendments allow cross-currency checks, composite paths will be available._

### XChainBridge transaction

(using flow())

No impact as SendMax is processed as null.

### PathFind command

(using flow())
No impact as DefaultPaths is false.
