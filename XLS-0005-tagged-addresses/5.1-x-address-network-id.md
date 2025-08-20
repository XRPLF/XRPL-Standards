<pre>
  XLS-5.1 - XRP Ledger Proposed Standard #5.1

  Title:        Tagged Addresses with NetworkID
  Author:       Richard Holland (XLS-5.1)
  Affiliation:  XRPLF, XRPL-Labs
  Created:      2023-11-02

  Base Standard:  https://github.com/XRPLF/XRPL-Standards/tree/master/XLS-0005-tagged-addresses (Nikolaos D. Bougalis)

</pre>


# Introduction
X-Addresses provide a way to encode all relevant payment endpoint information (r-address, destination tag / no destination tag) in a single user-friendly, checksum-protected address format. This is primarily intended to prevent users sending funds to exchanges without including the correct destination tag.

However, with the recent release of the **Xahau** network and planned further expansion of the XRP Ledger Protocol ecosystem, there is now an additional, highly relevant, piece of payment endpoint information: destination *NetworkID*. Without this information users (or their wallet software) could accidentally send to the same endpoint but on the wrong network.

## Extension
The XLS-5 standard is base58 encoded packed binary containing a destination account ID, destination tag (or deliberate absence of a destination tag), and a flags field. In this updated standard we now provide a way to encode the Network ID.

To signal a NetworkID has been included as a little endian encoded UINT32 as the final 4 bytes of the packed data we now set the most significant bit (0x80) on the flags UINT8 high.

Further, we deprecate the **T** prefix mode of X-addresses. Thereafter all X-addresses that lack _NetworkID_ are assumed to refer to XRPL Mainnet (NetworkID = 0).

Finally, we deprecate the 64bit destination tag flag, to make parsing easier for libraries and because no implementation of the XRPL protocol supports 64bit tags.

`[← 2 byte prefix →|← 160 bits of account ID →|← 8 bits of flags →|← 32 bits of tag →|← 32 bits of NetworkID →]`



## Revised Format Table
For ease of lookup here is the complete revise format table:
Byte Offset | Length | Field Name | Value |Explanation
-|-|-|-|-
0  | 2 | Identifying prefix | `0x0544` | This produces a leading *X* when encoded
2 | 20 | Account ID | `<20b AccountID>` | The destination Account ID
22 | 1 | Flags |  | Information about the format as below
|  |  |  | `0x00` | No destination tag. No NetworkID.
|  |  |  | `0x01` | Destination tag present. No NetworkID.
|  |  |  | `0x80` | No destination tag. NetworkID present.
|  |  |  | `0x81` | Destination tag present. NetworkID present.
|  |  |  |          | All other flag combinations are invalid.
23 | 4 | Destination Tag | `<4b dest tag>` | Little endian. If *no destination tag* is specified by flags, this must be `0x00000000`
27 | 4 | Network ID | `<4b NetworkID>` | Little endian. If *no Network ID* is specified by flags, this must be `0x00000000`


