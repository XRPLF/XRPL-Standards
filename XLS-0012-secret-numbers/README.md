<pre>
  xls: 12
  title: Secret Numbers
  description: Derive XRPL account keypairs based on 8x 6 digits for user-friendly, language-agnostic account secrets
  author: Wietse Wind <w@xrpl-labs.com>, Nik Bougalis (@nbougalis)
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/15
  status: Final
  category: Ecosystem
  created: 2020-05-13
</pre>

# XLS-12: Secret Numbers

### Derive XRPL account keypairs based on 8x 6 digits

##### Abstract

Existing XRPL account secrets are prone to typo's and not that user friendly. Using numbers means the secrets will be language (spoken, written) agnostic. Existing secrets (family seed, mnemonic) may be intimidating for the public that's relatively new to cryptocurrencies / blockchain technology & very prone to user error (eg. when writing down or reading).

## Background

The common formats for XRPL account secrets are (at the time of writing the first (TypeScript) [Secret Numbers implementation](https://github.com/WietseWind/xrpl-secret-numbers), July 2019):

- Family Seed, eg. `sh1HiK7SwjS1VxFdXi7qeMHRedrYX`
- Mnemonic, eg. `car banana apple road ...`

Both secrets contain characters that can be easily confuesed or misread. A range of numbers (0-9) is easier to write down (alphabet of just 10 defferent chars (numbers)).

The Secret Numbers encoding method can be used on HEX private keys as well. As HEX private keys are hardly being used & for the sake of offering backwards compatibility for generated Secret Numbers, I propose this to be used with the entropy that can be used for ripple-keypairs as well.

## Secret Numbers

A secret based on the Secret Numbers standard contains 8 blocks of 6 digits: the first five digits are int representations of the entropy, the 6th digit is a checksum based on the five preceding digits + the block number.

A secret now looks like:

```
554872 394230 209376 323698 140250 387423 652803 258676
```

A block indicator can be added to make it easier for users to enter the right block:

```
A. 554872
B. 394230
   ...
H. 258676
```

The first five digits are the decimal representation of a chunk of the entropy buffer, and will be in the range of `0 - 65535` (`0000 - FFFF`).

## Compatibility

Secret Numbers can be used as entropy-param for eg. the `generateSeed` method of [ripple-keypairs](https://github.com/ripple/ripple-keypairs). This means a secret based on the Secret Numbers standard can always be turned in a family seed for backwards compatibility with existing XRPL clients.

## Encoding / Decoding

- Secret Numbers contain 6 digits in the range of 0-9 per position.
- Secret numbers contain 5 digits (int) entropy and a 6th checksum.
- The checksum digit is based on the 5 digits entropy and the block position. This way a block of 6 digits entered at the wrong position (A-H) can be detected as being invalid.
- A "Secret Number"-chunk should be represented as a string containing six digits, as there can be leading zeroes.

### Calculating

Position is the block number starting at zero (0 - 7). The position then multiplied & incremented (`* 2 + 1`) to make sure it results in an odd number.

```
calculateChecksum(position: number, value: number): number {
  return value * (position * 2 + 1) % 9
}
```

##### Samples

| HEX  | Decimal | Block # | Calculation               | Checksum | Result |
| ---- | ------- | ------- | ------------------------- | -------- | ------ |
| AF71 | 44913   | 0       | `44913 * (0 * 2 + 1) % 9` | 3        | 449133 |
| 0000 | 0       | 2       | `    0 * (2 * 2 + 1) % 9` | 0        | 000000 |
| FFFF | 65535   | 3       | `65535 * (3 * 2 + 1) % 9` | 6        | 655356 |
| FFFF | 65535   | 4       | `65535 * (4 * 2 + 1) % 9` | 0        | 655350 |
| CD91 | 52625   | 7       | `52625 * (7 * 2 + 1) % 9` | 3        | 526253 |

## Implementations

- TypeScript [![npm version](https://badge.fury.io/js/xrpl-secret-numbers.svg)](https://www.npmjs.com/xrpl-secret-numbers) - Github: https://github.com/WietseWind/xrpl-secret-numbers

## Representations

#### String

```
554872 394230 <...> 258676
```

#### Human Readable & entry

```
A. 554872
B. 394230
   ...
H. 258676
```

#### QR Codes

```
xrplsn:554872394230<...>258676
```
