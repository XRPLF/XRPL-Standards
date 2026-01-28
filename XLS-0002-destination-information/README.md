<pre>
  xls: 2
  title: XRPL destination information
  description: A standard for encoding destination information with backwards compatibility for web browsers
  author: Wietse Wind <w@xrpl-labs.com>
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/27
  status: Stagnant
  category: Ecosystem
  created: 2019-02-25
</pre>

Currently several apps are using a variety of methods to encode destination information;

- rPEPPER7kfTD9w2To4CQk6UCfuHM9c6GDY?dt=123
- rPEPPER7kfTD9w2To4CQk6UCfuHM9c6GDY:123
- Deprecated Ripple URI syntax: https://ripple.com//send?to=rPEPPER7kfTD9w2To4CQk6UCfuHM9c6GDY&amount=30&dt=123

I feel the best way to implement this, is by allowing Apps to register Deep Links (URI handlers) while keeping the destinations backwards compatible with Web browsers, so users without any app to handle a URI can display a page by the app creator with an instruction.

I propose to allow any URL prefix, with a default set of GET URL params, supporting the existing params proposed in the (deprecated) Ripple URI standard;

so:

{ any URL } ? { params }

Where params may _all_ be optional except for the account address:

- `to` (account address, rXXXX..)
- `dt` (destination tag, uint32)
- `amount` (float, default currency: XRP (1000000 drops))
- ...

So App 1 may use:
https://someapp.com/sendXrp?to=...

... While App 2 uses:
https://anotherapp.net/deposit-xrp?to=...&dt=1234&amount=10
