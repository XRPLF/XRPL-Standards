<pre>
  xls: 3
  title: Sharing and deeplinking signed transactions
  description: A standard for encoding HEX signed transactions for air-gapped submissions with deep link support
  author: Wietse Wind <w@xrpl-labs.com>
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/26
  status: Stagnant
  category: Ecosystem
  created: 2019-02-25
</pre>

Currently several apps are using a variety of methods to encode HEX signed transactions (to be submitted air gapped);

- { HEX }
- ripple:signed-transaction:{ HEX }
- ripple://signed/{ HEX }

I feel the best way to implement this, is by allowing Apps to register Deep Links (URI handlers) while keeping the destinations backwards compatible with Web browsers, so users without any app to handle a URI can display a page by the app creator with an instruction.

I propose to allow any URL prefix:
{ any URI with exactly one folder } / { HEX }

So App 1 may use:
https://someapp.com/submitTx/{ HEX }

... While App 2 uses:
https://someapp.com/send-xrpl-tx/{ HEX }

I would propose to limit the amount of slashes before the HEX to a _fixed amount of slashes_ (eg. one folder, as the App 1 and App 2 examples show) so parsers can easily split the URI without having to use regular expressions.

Limitations:
MSIE limits URL parsing to 2,083 chars. Safari 65k chars. Todo: need to test this on modern mobile OS'es.

P.S. Another option (proposal) would be to use a specific syntax (prefix) instead of fixed (one) folder; eg.
`https://xrpl-labs.com/xrpl:signed-transaction:<SIGNEDBLOB>`

... Where the fixed prefix in this case is `xrpl:signed-transaction:`.
