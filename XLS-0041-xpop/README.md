<pre>
    xls: 41
    title: XRPL Proof of Payment Standard (XPOP)
    author: Richard Holland (@RichardAH)
	description: An offline non-interactive cryptographic proof that a transaction was successfully submitted to the XRP Ledger and what its impact (metadata) was
	proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/107
    created: 2023-05-04
    status: Final
    category: Ecosystem
</pre>

# XLS-41

# Abstract

An XRPL Proof of Payment (XPOP) is an offline non-interactive cryptographic proof that a transaction was successfully submitted to the XRP Ledger and what its impact (metadata) was.

# Background

The XRPL is comprised of a chain of blocks (Ledgers) co-operatively and deterministically computed, shared and subsequently signed (validated) by a quorum of rippled nodes (validators) operating in a socially trusted group known as a Unique Node List (UNL). The UNL is typically published by a trusted third party in a format known as a Validator List (VL). (Examples: https://vl.xrplf.com, https://vl.ripple.com). Each VL is cryptographically signed by a master publishing key. Users of the network ultimately trust this publisher (key) to choose appropriate validators for the UNL that will co-operate to make forward progress and not conspire to defraud them.

# Proof

Each VL contains a list of validators signed for by the VL publisher key.

Each validator is a key that signs validation messages over each Ledger header.

Each Ledger header contains the root hash of two patricia merkle tries:

- the current (”account”) state for the ledger, and
- the transactions and their metadata in that Ledger.

A quorum (from a given VL) of signed validation messages proves a Ledger was correctly closed and became part of the block chain.

Thus if one trusts the VL publisher key, then one can form a complete chain of validation from the VL key down to a transaction and its meta data without connectivity to the internet. This is an XPOP.

# Format

XPOPs are a JSON object with the following schema:

```
{
	"ledger": {
		"acroot": merkle root of account state map | hex string,
		"txroot": merkle root of transaction map | hex string ,
		"close": close time | int,
		"coins": total drops | int or string,
		"cres": close time resolution | int,
		"flags": ledger flags | int,
		"pclose": parent close time | int,
		"phash": parent hash | hex string,
	},
	"transaction": {
		"blob": serialized transaction | hex string,
		"meta": serialized metadata | hex string,
		"proof": <see below>
	},
	"validation": {
		"data": {
			validator pub key or master key | base58 string : serialized validation message | hex string
			... for each validation message
		},
		"unl": {
			"blob": base64 encoded VL blob as appearing on vl site | base64 string,
			... remaining fields from vl site
		}
	}
}
```

The `proof` key inside `transaction` section has one of two possible forms:

1. List form:

   In this form the merkle proof is a list of lists (and strings) containing the minimum number of entries to form the merkle proof. Each list contains 16 entries (branches `0` through `F`). For each branch either the the root hash of that branch is provided as a 64 hex nibble string, or a further list of 16 entries is provided, until the transaction that the proof proves is reached. If a list contains fewer than 16 entries then the verifier should infer that the remaining entries are all null entries (hash strings that are sequences of 0s).

```
# list form
"proof": [
	hex string for branch '0',
	...
        hex string for branch 'A',
	# branch 'B' is a list
	[
			hex string for branch 'B0',
			... ,
			hex string for branch 'BE',
			# branch 'BF' is a list
			[
				hex string for branch 'BF0',
				...
			]
	],
	hex string for branch 'C',
	...
]

```

1. Tree form:

   In this form the merkle proof is an object of objects containing the entire transaction map for the ledger. This form is useful if many XPOPs must be generated for the same ledger and the size of each individual XPOP is less relevant than the amount of work to make and store the XPOPs. Each object contains three keys: `children`, `hash`, `key`.
   - The `children` key is always either an empty object or is keyed with only the branches which actually exist there, each as a single hex nibble `0` - `F`.
   - The `hash` key is always a 64 nibble hex string: either the hash over the children (with appropriate namespace) or, if a leaf node, the hash over the node (with appropriate namespace).
   - The `key` key is always a 64 nibble hex string: the keylet (index) of the object at this location.

   ```
   # tree form
   "proof": {
     "hash" : hex string,
     "key" : hex string,
   	"children" : {
   		"0":
   		{
   			"children": {},
   			"hash": hex string,
   			"key": hex string
   		},
   		...
   		"F":
   		{ ...}
   	}
   }
   ```

# Verifying

See reference implementation at: [xpop-verifier-py](https://github.com/RichardAH/xpop-verifier-py/blob/main/verify.py)
