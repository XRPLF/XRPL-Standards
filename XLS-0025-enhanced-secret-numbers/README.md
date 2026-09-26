<pre>
  xls: 25
  title: Enhanced Secret Numbers
  description: Enhances XLS-12 secret number format by introducing an additional block for encoding ancillary information, and supporingt for longer secrets.
  author: Nik Bougalis <nikb@bougalis.net>
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/63
  status: Final
  category: Ecosystem
  created: 2021-12-10
</pre>

# Enhanced Secret Numbers

## Abstract

The Secret Numbers proposal **<a href="https://github.com/XRPLF/XRPL-Standards/tree/master/XLS-12">XLS-12</a>** introduces a new format for secrets - based on blocks of numbers/digits (0-9) with block-level checksums - to generate XRP Ledger account keys and address. This draft proposes augmenting and enhancing **XLS-12** to make the format more flexible and more robust.

### Motivation

The XRP Ledger typically uses 128-bit seeds as the cryptographic material from which cryptographic keys for accounts are derived. Such seeds are generally too long for humans to remember and the existing formats are hard to <em>transcribe</em>. Prior to XLS-12, there were 4 canonical encoding for the seed data:

1. A Base58-based encoding scheme beginning with the letter `s` (in this format, the result is often, but _incorrectly_, referred to as a private key); or
2. A word-based "mnemonic", encoded using a variant of RFC 1751; or
3. A raw hex string, directly representing the 128-bit seed; or
4. A passphrase, an arbitrary string of words which is hashed to produce a seed.

By way of example, let's use the well-known [genesis account](https://xrpl.org/accounts.html#special-addresses), `rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh`, which has an associated **`secp256k`** key:

1. The seed for the account is `snoPBrXtMeMyMHUVTgbuqAfg1SUTb`;
2. The mnemonic is `I IRE BOND BOW TRIO LAID SEAT GOAL HEN IBIS IBIS DARE`;
3. The raw hex is `DEDCE9CE67B451D852FD4E846FCDE31C`; and
4. The corresponding passphrase is `masterpassphrase`.

The **XLS-12** standard introduced a new format, secret mumbers, which consists of 8 blocks of 6 digits, where the first five digits correspoding to a 16-bit number (from 0 to 65535) and the 6th digit is a checksum based on the five preceding digits and the index of the block. The **XLS-12** secret numbers for the genesis account are: `570521-598543-265488-209520-212450-201006-286214-581400`.

### Issues with XLS-12

The **XLS-12** specification, while convenient and easier to transcribe, has several drawbacks:

First, it encodes no ancillary information about the information encoded (e.g. whether it is meant to derive a **secp256k1** or an **Ed25519** key) and is limited to only encoding seeds, from which keys are then derived. Second, the block-level checksum is inefficient and detects only a small percentage of errors.

Lastly, it's unclear whether the secret numbers should be used to create a **secp256k1** or an **Ed25519** key. For example, given the above `570521-598543-265488-209520-212450-201006-286214-581400` secret numbers, an implementation could derive an **Ed25519** and, therefore, an account that is not the well-known genesis account. Tools that support secret numbers typically resort to detecting the type of account, usually in a semi- automated fashion, but on occasion by resorting to asking the user to confirm their intended public address.

### Enhancements to XLS-12

This proposal aims to address these problems by proposing extensions to **XLS-12** which retaining backwards compatibility. There are three primary changes:

1. Using a simplified but more powerful per-block checksum;
2. Introducing an additional block, which is used to encode ancillary information; and
3. Support for longer blocks, allowing encoding of 128-bit and 256-bit secrets.

Secret numbers compatible with this specification will always be composed of an odd number of blocks; secret numbers compatible with the **XLS-12** specification will always be composed of an even number of blocks&mdash;or more specifically, precisely 8 blocks. This makes it possible to seamlessly detect which standard was used and allows for backwards compatibility.

#### Per-block checksusm

Under **XLS-12** the Nth block consists of 16 bits of raw key material, and an additional checksum digit. Assuming the keying material has value `X` the N<sub>th</sub> block would be: `(X * 10) + ((X * (N * 2 + 1)) % 9)`.

In theory, the checksum digit can take any value from [0,...,9] but, by construction, not all checksum digits are equally likely across all blocks, reducing their usefulness. For blocks at positions 2 and 8, the only valid checksum digits are `0`, `3` and `6`; blocks at position 5 are worse, with `0` being the _only_ valid checksum digit.

This proposal simplifies the checksum function for key blocks by reducing it to a simple multiplication by 13, a prime number. That is, the N<sub>th</sub> key block simply becomes: `X * 13`. Under this scheme, the possible values are multiple of 13 and and the range is from [0,...,851955]. This scheme avoids the position-dependent behavior observed with the existing scheme and allows for more efficient error detection.

#### Information Block

This proposal _prepends_ an additional 6-digit block, composed of two 16-bit values, that encodes ancillary information about the content and a checksum of the blocks that can be used to detect whole-block transposition, or incorrect blocks.

First, calculate the checksum of all blocks as `(∑(𝑥[i] * π[i]>)) mod 256`, where `𝑥[i]` is the i<sup>th</sup> 16-bit block of data being encoded and `π[i]` is the i<sup>th</sup> prime number. The result is an 8-bit value, `C`.

##### Flags

The proposal also defines an 8-bit field, that can be used to specify details or ancillary information about the key. This proposal defines this as a bitfield named `F`. The following flags are defined:

| Value  | Meaning                                                                                                                                     |
| ------ | ------------------------------------------------------------------------------------------------------------------------------------------- |
| `0x01` | The data block represents a raw 128-bit _seed_, from which private keys can be derived using the derivation algorithm defined in `rippled`. |
| `0x02` | The private key calculated or derived from this block of data is used with the **secp256k1** algorithm.                                     |
| `0x04` | The private key calculated or derived from this block of data is used with the **Ed25519** algorithm.                                       |
| `0x08` | The data block represents an **Ed25519** validator master key. This flag cannot be combined with any other flags.                           |
| `0x10` | The data block represents the fulfillment of a `PREIMAGE-SHA256` cryptocondition. This flag cannot be combined with any other flags.        |

##### Using Flags

The different flags used with extended keys make it possible to directly encode different types of keys as well as allow for 128-bit and 256-bit keys.

For example:

- A 256-bit **`secp256k`** (or **`Ed25519`**, if the `0x08` flag is included) key can be directly encoded as 17 groups, if they information block does not include the `0x01` flag.
- A 256-bit preimage for a cryptocondition can be encoded as 17 groups, if the information block includes the `0x10` flag.

Other flags may be added in the future. A compliant implementation of this proposal _SHOULD_ fail if any flags other than the ones it understands are used.

##### Information Block Checksum

By construction, no valid XLS12 block can have a value greater than 655356 (i.e. 65535 \* 10 + (65535 % 9)). This means that any block that begins with a 7, 8 or 9 cannot be a valid XLS12 block. This means that we can construct the first block in such a way so as to allow for automatic detection of "classic" XLS-12 keys and "extended" keys as defined in this proposal.

Again, assume that C is the checksum described above and F is the flag bitfield, then the information block checksum `X` is defined as:

    X = (F ^ C) % 3

The information block itself is then calculated as:

    A = ((X + 7) * 100000) + (C * 256 + F)

The end result is an A block that begins with 7, 8 or 9, which means it cannot be a valid XLS12 block, while still retaining a checksum in the A block.
