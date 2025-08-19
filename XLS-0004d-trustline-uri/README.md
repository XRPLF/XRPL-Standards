---
title: Standard URI instructing a wallet to add a trustline
type: draft
description: A URI standard for instructing wallets to add trustlines following the design of XLS-2d
author: Community Contributors
core_protocol_changes_required: false
---

I suggest we follow on closely from the design of XLS-2d

Query parameters:
`action=trustline`
`limit=<integer>`
`currency=<issuer address>:<currency code>`
`rippling=true|false (optional, default = false)`

I.e.

`{ url } ? { trust line instructions }`

So for example

`anything://any.domain/url/?action=trustline&limit=10000&currency=rvYAfWj5gh67oV6fW32ZzP3Aw4Eubs59B:USD&rippling=false`

I realise compounding the currency and issuer information is a little tacky here but we did it in the previous standard