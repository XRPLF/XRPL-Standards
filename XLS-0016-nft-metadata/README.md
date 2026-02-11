<pre>
  xls: 16
  title: NFT Metadata
  description: Standard for NFT metadata
  author: Hubert Getrouw (@HubertG97)
  created: 2021-03-17
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/37
  status: Stagnant
  category: Ecosystem
</pre>

In addition to @WietseWind 's [XLS-14](https://github.com/XRPLF/XRPL-Standards/discussions/30) and @RichardAH 's proposal [XLS-15](../XLS-0015-concise-tx-id/README.md) here is a proposal to create a standard for the creation of metadata for the tokens created with a CTI in the currency code.

When issuing an indivisible token on the XRPL the only data given is the currency code. For optimal usage, there has to be more metadata for an NFT. For example a description and a URI to an IPFS file.
Using the Concise Transaction Identifier, a prior transaction can be used to mark the metadata contained in the memo's field for the use of the NFT.

The [Memos Field](https://xrpl.org/transaction-common-fields.html#memos-field) in an XRPL transaction is presented as an array of objects which contains one memo field per object. This field consists of the following fields:

- MemoData
- MemoFormat
- MemoType

The MemoData field can be used for the metadata itself and the MemoFormat indicates the nature of the given data inside the MemoData field (MIME type). To create a certain hierarchy for covering failure of the URI specified, the MemoType field contains the numbering of the data named as shown below followed by the MIME type:

- NFT/0 - _Description_ - `text/plain`
- NFT/1 - _Author_ - `text/plain`
- NFT/2 - _Primary URI_ - `text/uri`
- NFT/3 - _Back-up URI_ - `text/uri`
- NFT/4 - _Reduced image Data URI as last back-up_ - `text/uri`

The usage of a back-up URI and Data URI can be seen as optional and can be replaced with other kinds of data that have the preference of the issuer of the NFT for example contact information.
The limit of storage is 1kb of data in the memo's field in total. Multiple memos can be used to give as much information as fits to the 1kb of data.

If there is only one memo on the CTI referenced transaction and the memo data contains a URI of any sort then this is deemed to be the NFT content. The multiple memo's structure will be the advanced method to issue NFTs. The standard will also be compatible with previously created NFTs referred to as the simple method.

---

**Issuing**

For the metadata, there has to be created a transaction from the same address as the issuer of the NFT to for example a hot wallet. This transaction of 1 drop contains the description and URIs needed for the NFT.

The currency code for an NFT consists of 3 parts:

- Prefix 02 for HEX currency code
- [CTI](../XLS-0015-concise-tx-id/README.md) (Concise Transaction Identifier)
- Short name converted to HEX for the NFT to a maximum of 12 characters or less (filled up with 0's if it's less)

After this, a Trust line can be set up using the above currency code and the NFTs being transferred from the issuing address to the hot wallet.

---

### Advanced method

_For example_

**Issuer:** `rBzoA1EXxE2FeGV4Z57pMGRuzd3dfKxVUt`
**Hot wallet:** `rp9d3gds8bY7hkP8FmNqJZ1meMtYLtyPoz`

The JSON for the metadata transaction would look like this:

```
{
  "Account": "rBzoA1EXxE2FeGV4Z57pMGRuzd3dfKxVUt",
  "TransactionType": "Payment",
  "Amount": "1",
  "Destination": "rp9d3gds8bY7hkP8FmNqJZ1meMtYLtyPoz",
  "Fee": "100000",
  "Memos": [{
    "Memo": {
      "MemoData": "546861742773206F6E6520736D616C6C20696D616765206F66206D6F6F6E2C206F6E65206769616E74206C65617020666F72204E4654206F6E20746865205852504C",
      "MemoFormat": "746578742F706C61696E",
      "MemoType": "6E66742F30"
    }
  },
    {
      "Memo": {
        "MemoData": "48756265727420476574726F7577",
        "MemoFormat": "746578742F706C61696E",
        "MemoType": "6E66742F31"
      }
    },
    {
      "Memo": {
        "MemoData": "697066733A2F2F62616679626569686561786B696A3276656D6B7337726B716E6F67367933367579793337626B33346D697533776F72636A756F6833747532773279",
        "MemoFormat": "746578742F757269",
        "MemoType": "6E66742F32"
      }
    },

    {
      "Memo": {
        "MemoData": "68747470733A2F2F676574726F75772E636F6D2F696D672F707572706C656D6F6F6E2E706E67",
        "MemoFormat": "746578742F757269",
        "MemoType": "6E66742F33"
      }
    },
      {
      "Memo": {
        "MemoData": "646174613A696D6167652F6769663B6261736536342C52306C474F446C684641415541505141414141414142415145434167494441774D4542415146425155474267594842776348392F66342B506A352B666E362B7672372B2F76382F507A392F66332B2F76377741414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414141414143483542414541414241414C4141414141415541425141414157524943534F5A476D65614B7175624F74437A664D7551564D456937674D41494D554D684942554F4D784941454141544A736942674F4A674267654267456A476E413063673945524446464342364E4D6248305945684543454579784844414354316571383352486C69654D73474147414641414949436A495051776F4F66675A4A41544A5A5932414C4255634B535A516A684552424A41384355774F6750414B6649326445547156554A6A774166364345435352694F436F4D42416F6A6A61675149514137",
        "MemoFormat": "746578742F757269",
        "MemoType": "6E66742F34"
      }
    }]


}
```

Converted to human-readable output's [this](https://xrpcharts.ripple.com/#/transactions/24ADC5D0EF72DDA45A7464A7F74B762801FA12C26F6BFEEFC61CF72140623F27) transaction

Using this transaction's txn hash, txn_index, ledger_hash, and ledger_index creates a CTI of `23080995397183855`
Converted to HEX it will be `52000B03B6296F`

The name of the NFT will be '_Purple moon_'.
After conversing this to HEX the complete currency code looks like this `0252000B03B6296F507572706C65206D6F6F6E00`

**02** - _XRPL NFT identifier_
**52000B03B6296F** - _CTI_
**507572706C65206D6F6F6E00** - _NFT name_

When Issuing a token the same address has to be used as the sender of the aforementioned transaction.
As explained in this [blogpost](https://coil.com/p/Huub/Introduction-to-NFT-on-the-XRP-Ledger/4ee41zWW-) a Trust line has to be created between the Issuer and the hot wallet.

Make sure the issuer address has an `AccountSet` of `SetFlag` to `8`

```
{
    "TransactionType": "TrustSet",
    "Account": "rp9d3gds8bY7hkP8FmNqJZ1meMtYLtyPoz",
    "Fee": "12",
    "Flags" : 131072,
    "LimitAmount": {
      "currency": "0252000B03B6296F507572706C65206D6F6F6E00",
      "issuer": "rBzoA1EXxE2FeGV4Z57pMGRuzd3dfKxVUt",
      "value": "1000000000000000e-95"
    }
}
```

In the currency field the HEX converted currency code is used.
The value is set to `1000000000000000e-95` which will result in 10 NFTs.
More explanation about this can be found in @WietseWind's proposal [XLS-14](https://github.com/XRPLF/XRPL-Standards/discussions/30)

Last step is to send the tokens from the issuer to the hot wallet.

```
{
"TransactionType": "Payment",
"Account": "rBzoA1EXxE2FeGV4Z57pMGRuzd3dfKxVUt",
"Fee": "12",
"Destination" : "rp9d3gds8bY7hkP8FmNqJZ1meMtYLtyPoz",
"Amount": {
"currency": "0252000B03B6296F507572706C65206D6F6F6E00",
"issuer": "rBzoA1EXxE2FeGV4Z57pMGRuzd3dfKxVUt",
"value": "1000000000000000e-95"
    }
}
```

Now there are 10 Purple moon NFTs on address `rp9d3gds8bY7hkP8FmNqJZ1meMtYLtyPoz`

### Simple Method

The JSON for the metadata transaction would look like this:

```
{
  "Account": "rBzoA1EXxE2FeGV4Z57pMGRuzd3dfKxVUt",
  "TransactionType": "Payment",
  "Amount": "1",
  "Destination": "rp9d3gds8bY7hkP8FmNqJZ1meMtYLtyPoz",
  "Fee": "100000",
  "Memos": [{
    "Memo": {
      "MemoData": "697066733A2F2F62616679626569666C6A667870786F7A6E6A703273357266697270666A756E7876706B71737863727133766C626F6C346536717A376F7972693571",
      "MemoFormat": "746578742F757269",
      "MemoType": "7872706C2F6E6674"
    }
  }]
}
```

Converted to human-readable output's [this](https://xrpcharts.ripple.com/#/transactions/7DFCD417FCEE35F7BB3ABECD05C27BA71F1E845BFD29C19AF3CF5E55B44EA55C) transaction

After that, a trust set and sending the tokens is the same as the advanced method
