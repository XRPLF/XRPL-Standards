<pre>
  xls: 4
  title: Trustline Add URI
  description: A URI standard for instructing wallets to add trustlines following the design of XLS-2
  author: Richard Holland (@RichardAH)
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/25
  status: Stagnant
  category: Ecosystem
  created: 2019-03-06
</pre>

I suggest we follow on closely from the design of XLS-2

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
