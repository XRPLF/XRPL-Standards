<pre>
    xls: 21
    title: 21: Allocating Asset Code Prefixes
    description: This proposal defines a mechanism for setting aside prefixes for specific formats and publishing a list of formats potentially in use.
    author: Rome Reginelli (@mDuo13)
    proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/53
    created: 2021-07-28
    status: Stagnant
    category: Ecosystem
</pre>

# Proposal for Allocating Asset Code Prefixes

Asset codes in the XRP Ledger protocol are natively 160 bits; the reference implementation of the core server defines a shortcut to display 3-character "ISO 4217-like" currency codes using ASCII. These [standard-currency codes](https://xrpl.org/currency-formats.html#standard-currency-codes) use the prefix `0x00` to distinguish them from other asset codes and to prevent haphazard and inconsistent decoding and display of asset codes. (Note: XRP does not usually use a currency code, but when it does, it has an all-zeroes value, which can be considered a special case of the Standard Currency Codes format.)

Various other formats have been proposed and even implemented, but until now there has been no organization around the reserving of different prefixes. This proposal defines a mechanism for setting aside prefixes for specific formats and publishing a list of formats potentially in use.

## Canonical List

A table of asset code prefixes would be added to xrpl.org and maintained by the XRPL.org contributors. A starting point for the table might be something like this:

| Prefix        | Status | Name                                        | Standard                                                                                       |
| ------------- | ------ | ------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| `0x00`        | ✅     | Standard Currency Codes                     | https://xrpl.org/currency-formats.html#standard-currency-codes                                 |
| `0x01`        | ❌     | Interest-Bearing (Demurrage) Currency Codes | https://xrpl.org/demurrage.html                                                                |
| `0x02`        | ❌     | XLS-14 Non-Fungible Tokens                  | https://github.com/XRPLF/XRPL-Standards/discussions/30                                         |
| `0x03`        | 📄     | XLS-30 AMM LP Tokens                        | https://github.com/XRPLF/XRPL-Standards/blob/master/XLS-0030-automated-market-maker/README.md  |
| `0x20`—`0x7E` | ⚠️     | Full ASCII codes                            |                                                                                                |
| `0xEC`        | 📄     | Extended Prefixes.                          | Reserved for additional prefixes. [See below](#extended-prefixes).                             |
| `0xFF`        | 📄     | Non-Transferrable Tokens                    | https://github.com/XRPLF/XRPL-Standards/blob/master/XLS-0010-non-transferable-tokens/README.md |

Any prefixes not listed in the table are considered available (🆓).

Explanation of status labels:

- ✅ Accepted. This prefix is used for a specific format which has been accepted an XRP Ledger Standard.
- 📄 Proposed. This prefix has been set aside for use with a proposed or in-development standard.
- ❌ Deprecated. This prefix was previously used, but the associated format is not currently recommended for implementation or use.
- ⚠️ Reserved. This prefix does not have a proper standard, but is discouraged to prevent overlap with emergent usage or for other reasons.
- 🆓 Available. This prefix has not yet been used by any standard format.

### Reserving Prefixes

To reserve a prefix, one would create an [XRPL standard draft](https://github.com/XRPLF/XRPL-Standards) per the standard procedure, and note in the draft the request to receive either a specific unused prefix or the next available prefix. A maintainer for XRPL.org can check the proposal and, judging that it is made in good faith, update the list on XRPL.org to add the new prefix as "Reserved" with a link to the draft discussion.

Proposals that reserve multiple prefixes are discouraged, but may be granted if after additional scrutiny it is justified to set aside multiple top-level prefixes for the proposal. In most cases, sub-types or variations on the same format can be defined in the asset code's payload data, such as the next 8 bits following the prefix.

When the corresponding XRPL Standards Draft is accepted as a full standard, the prefix changes from the "Reserved" to "Accepted" status. A maintainer of XRPL.org can update the list to track the new status of the code, and update the link to point to the full standard. Similarly, a standards proposal can move an Accepted or Reserved prefix to Deprecated.

If a Standards Draft is withdrawn, any prefix(es) reserved for that draft can be made available again or moved to Deprecated, based on the best judgment of maintainers as to whether the reuse of a prefix is likely to lead to confusion, incompatibilities, or other problems.

## Extended Prefixes

Since it seems possible that, eventually, there may be more than 256 different formats, the prefix `0xEC` is reserved for additional prefixes. For any asset code starting in `0xEC`, the next 8 bits indicate the rest of the currency code. For example, `0xEC00` would be the first extended prefix, then `0xEC01`, and so on, with `0xECEC` being reserved for further-extended prefixes, recursively.

Extended prefixes are less desirable than regular prefixes since, by the nature of the asset code's fixed size, extended prefixes have fewer remaining bits to work with. With a normal currency code, the prefix occupies 8 bits, leaving 152 bits for the rest of the asset code. With singly-extended prefixes, the prefix is 16 bits, leaving 144 bits of payload. With doubly-extended prefixes, it drops to 132 bits of payload, and so on. Still, this is a decent amount of room to work with, especially since each format can define a potentially large number of unique asset codes.

## ASCII Codes

It seems that some XRPL users may already be using a de-facto standard of using the entire 160-bit asset code value to represent a text code / name for the asset. We can avoid overlapping with this usage by avoiding any codes that start with printable ASCII characters, which have codes from `0x20` through `0x7E`.

There's probably not much we can do for asset codes in the wild that use extended ASCII or UTF-8. A subsequent proposal could set aside a prefix for a more standardized and flexible format. (For example, you may want to set aside a few bytes for a currency symbol e.g. $, €, ¥, or 💩.)
