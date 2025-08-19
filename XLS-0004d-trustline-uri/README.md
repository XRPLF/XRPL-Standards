# 0004 XLS-4d Standard URI instructing a wallet to add a trustline

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