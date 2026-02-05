<pre>
  xls: 45
  title: Prepublish Validator Lists
  description: Future activation date and improved expiration handling of UNLs
  author: Ed Hennis <ed@ripple.com>
  proposal-from: https://github.com/XRPLF/XRPL-Standards/pull/124
  status: Final
  category: System
  created: 2020-06-17
</pre>

## Abstract

Each XRPL server (node) must be configured with a UNL (Unique Node List), which
lists the validating nodes that the server considers trusted. A validator list
includes the public key of the list publisher, a manifest, a signature, a
version, and a base64-encoded blob that contains a UNL.

This document defines version 2 of the VL (Validator List) spec. Compared to
version 1, it adds a future effective date so that nodes in the peer-to-peer
network can switch to a new UNL simultaneously. It also supports publishing
multiple UNLs in one file, allowing future UNLs to be included alongside a
current UNL.

This spec also defines the enforcement of the UNL expiration date so that a
server will act similarly to being amendment-blocked if it has no active valid
UNL.

This spec was finalized and implemented in `rippled` version
[1.7.0-b10](https://github.com/XRPLF/rippled/pull/3720) on January 11, 2021. The
original pull request was titled ["Support UNLs with future effective dates:
(UNL v2)"](https://github.com/XRPLF/rippled/pull/3619). The purpose of this XLS
is to make the specification of these changes widely accessible so that related
tooling can be updated. Any further improvements to the VL format should be
defined in a new spec and implemented in `rippled` with a new pull request. Most
of the following content is written from the perspective of `rippled` before
these changes were merged.

## Motivation

Right now, UNLs are very time sensitive. They contain an expiration
date, after which the node will act like it doesn't have any validators configured.
The node will be unable to fully validate any ledger until it gets an updated
VL.

When a new UNL is published, it becomes live immediately. This
introduces the possibility of different nodes using different UNLs until
everybody "catches up". The protocol broadcast functionality helps
mitigate this issue by getting the UNL propagated faster, but it's still
not synchronous, and could still cause problems if the network topology
is "unfriendly". It also requires publishers to time the release of
new UNLs carefully so the old one doesn't expire first.

## Specification

<!--
  The Specification section should describe the syntax and semantics of any new feature. The specification should be detailed enough to allow competing, interoperable implementations.

  It is recommended to follow RFC 2119 and RFC 8170. Do not remove the key word definitions if RFC 2119 and RFC 8170 are followed.

  TODO: Remove this comment before submitting
-->

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "NOT RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in RFC 2119 and RFC 8174.

<!--
The following is an example of how you can document new object types and fields:

#### The **`<object name>`** object

<High level overview, explaining the object>

##### Fields

<Any explanatory text about the fields overall>

---

| Field Name        | Required?        |  JSON Type      | Internal Type     |
|-------------------|:----------------:|:---------------:|:-----------------:|
| `<field name>` | :heavy_check_mark: | `<string, number, object, array, boolean>` | `<UINT128, UINT160, UINT256, ...>` |

<Any explanatory text about specific fields>

###### Flags

> | Flag Name            | Flag Value  | Description |
>|:---------------------:|:-----------:|:------------|
>| `lsf<flag name>` | `0x0001`| <flag description> |

<Any explanatory text about specific flags>
-->

### Overview of changes

1. Add functionality to the UNL to include a future effective date. Change
   the published file format to allow multiple UNLs to be returned.
   (Limit number of future UNLs to mitigate some potential attacks.) All
   nodes will start using the new UNL after the first validated ledger with
   an earlier close time (falling back to the wall clock if necessary, such
   as when the node is not synced).
2. Add enforcement of the expiration date by changing rippled's behavior
   to something similar to being amendment blocked (reuse that code as much
   as possible).

### Data format

#### Glossary

| Term or acronym       | Definition                                                                                                                |
| --------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| VL                    | **V**alidator **L**ist. Also known as the "UNL", this is the list of validators that a server trusts not to collude.      |
| UNL                   | **U**nique **N**ode **L**ist. Also known as the "VL", this is the list of validators that a server trusts not to collude. |
| UNL file (or VL file) | A file containing a publisher's manifest, public key, etc., and one or more UNLs.                                         |

#### Current format

The current format of the VL file (e.g. as downloaded from
https://vl.ripple.com/) is

```
{
  "public_key" : string representing the publisher's hex-encoded master
    public key,
  "manifest" : string representing the base-64 or hex-encoded manifest
    containing the publisher's master and signing public keys,
  "version": unsigned integer representing the VL format version. Currently
    only 1 is valid,
  "signature": string representing the hex-encoded signature of the blob
    using the publisher's signing key,
  "blob": string representing base-64 encoded JSON containing the actual list.
    See below
}
```

The `blob` format is

```
{
  "sequence" : Unsigned integer sequence of this VL. The sequence number
    must increase monotonically. More specifically, validator lists with
    sequences less than the current are ignored. The special sequence
    UInt(-1) indicates that the master key is revoked,
  "expiration" : Unsigned integer representing the ripple time point when
    this list will no longer be valid,
  "validators" : [
    {
      "validation_public_key" : hex-encoded master public key,
      "manifest" : (optional) base64 or hex-encoded validator manifest
    },
    ...Optionally repeats...
  ]
}
```

"[ripple time](https://xrpl.org/docs/references/protocol/data-types/basic-data-types/#specifying-time)"
is the number of seconds since the "Ripple Epoch" of January 1, 2000 (00:00
UTC). This is similar to how the [Unix epoch](https://en.wikipedia.org/wiki/Unix_time)
works, except the Ripple Epoch is 946,684,800 seconds after the Unix Epoch. Do
not convert Ripple Epoch times to Unix Epoch times in 32-bit variables, as this
could lead to integer overflows.

#### Future format

The `blob` v2 format adds a single field to the v1 format:

```
"effective" : Unsigned integer representing the ripple time point when the
  list will become valid
```

So the full `blob` v2 format will be:

```
{
  "sequence" : Unsigned integer sequence of this VL. The sequence number
    must increase monotonically. More specifically, validator lists with
    sequences less than the current are ignored. The special sequence
    UInt(-1) indicates that the master key is revoked,
  "effective" : Unsigned integer representing the ripple
    time point when the list will become valid,
  "expiration" : Unsigned integer representing the ripple time point when
    this list will no longer be valid,
  "validators" : [
    {
      "validation_public_key" : hex-encoded master public key,
      "manifest" : (optional) base64 or hex-encoded validator manifest
    },
    ...Optionally repeats...
  ]
}
```

Using this `blob` v2 format, the VL v2 file format will remove `blob`
and `signature` and add:

```
"blobs-v2" : [
  {
    "manifest" : OPTIONAL string representing the base-64 or hex-encoded
      manifest containing the publisher's master and signing public keys,
    "signature": string representing the hex-encoded signature of the blob
      using the publisher's signing key,
    "blob" : string representing the base64-encoded json representation of
      the blob
  },
  ...Optionally repeats...
]
```

So the full VL v2 format will be:

```
{
  "public_key" : string representing the publisher's hex-encoded master
    public key,
  "manifest" : string representing the base-64 or hex-encoded manifest
    containing the publisher's master and signing public keys,
  "version": unsigned integer representing the VL format version. Both
    1 and 2 will be valid, with 1 signfiying the old format, and
      2 signifying the new.
  "blobs-v2" : [
    {
      "manifest" : OPTIONAL string representing the base-64 or
        hex-encoded manifest containing the publisher's master and signing
        public keys,
      "signature": string representing the hex-encoded signature of the blob
        using the publisher's signing key,
      "blob" : string representing the base64-encoded json representation of
        the blob
    },
    ...Optionally repeats...
  ]
}
```

If the `expiration` of a `blob` is not greater than `effective`, the
`blob` will be considered malformed. Clients MAY process the other
`blob`s in the file as if the blob with that sequence were not present.

If the `manifest` is not present in a `blobs-v2` array entry, then the
top-level `manifest` will be used when checking the signature. This allows
a publisher to keep any old, `blob`s and their `signature`s if they ever need
to update their manifest. Most publishers will only need to use this field
very rarely. (Currently, if the VL processing sees a `stale` manifest, where
the public key hasn't been completely revoked, it will be used without a
problem. I'm not sure this behavior is correct. Consider treating a
`stale` manifest as an `untrusted` list.)

Pros of the new format:

- By signing each `blob` separately, the VL file can be modified to
  move the `blob`s around in the `blobs-v2` array as older `blob`s expire
  and new `blob`s are added without requiring any extra signing.
- The objects in the `blobs-v2` array don't necessarily need to be in
  order, but it will simplify maintenance if they are.
- Old `blob`s can be left in the `blobs-v2` array without causing any harm, as
  long as a more recent blob has already been added. In other words, old data
  can be cleaned up when it's convenient.

Cons:

- Each `blob` will need to be signed separately, even if they are all built at
  once.

##### Migration strategy

**Don't implement any migration strategy in code**

This is the simplest option. Don't do anything with the files, don't
modify the URLs. Leave the decision of when and how to migrate to
publishers. If they want to publish both versions simultaneously, then
they will need to communicate different URLs to operators. If not, then
they can wait until an appropriate time (e.g. when enough nodes have
upgraded, or if they want to pressure nodes to upgrade), and then make
a single clean switchover from v1 to v2.

In terms of the code, if the file version is 1, then rippled will follow
the v1 rules, and if it's 2, rippled will follow the v2 rules.

Pros:

- Keeps rippled code simple
- If a publisher chooses to publish a v2 UNL file while there are still
  nodes on the network that won't understand it, newer peers will
  [communicate](#protocol-changes-for-v2-unl-broadcasts) the "current"
  UNL to older peers, if they're connected sufficiently.

Cons:

- Adoption will probably be delayed until some other "limiting event" or
  synchronization point happens which forces all nodes to upgrade. This
  will most likely be when an amendment is enabled that no v1-only nodes
  support.

See the [appendix](#appendix) for descriptions of some other migration
strategies that were considered and rejected.

---

:bangbang: Support for XLS-45 has been fully deployed across all XRPL Mainnet
nodes.

This is because, after the "UNLv2" implementation was included in a release,
amendments from that release (or later) have been enabled. For details, see
[Amendment Blocked Servers](https://xrpl.org/docs/concepts/networks-and-servers/amendments/#amendment-blocked-servers).

---

### Rippled changes

#### Overview

When rippled downloads a v2 VL file from a URL (web or file) or receives an
updated network protocol message with more than one VL, it will store all
valid and potentially valid current and future VLs internally. This may
include VLs already in memory in addition to the ones downloaded (this is
particularly relevant if a peer splits a single file into multiple
messages). The automatic cache files will always be written as v2 for
simplicity.

As with current behavior, after processing new VLs, rippled will broadcast
them to peers. If the peer supports a protocol version which supports v2 VLs,
rippled will broadcast the same set of VLs that it is storing. If not, it will
only send the currently active VL. As now, rippled will avoid transmitting VLs
that it believes the peer already has.

Before starting a new consensus round, in addition to checking the expiration
date of the current VL, also check the effective date of the next VL, based
on the previous ledger close time if reasonable or the wall clock if not.
Rotate to the next VL if it becomes effective, and broadcast to peers that
don't understand the v2 format. If the current VL has expired without a
replacement, rippled will go into a state similar to being amendment blocked.
Unlike being amendment blocked, rippled will be able to resume normal
operations if it downloads or receives a valid active VL.

Any RPC method that reports the amendment blocked state will also report the
expired VL state as appropriate.

The /vl/ peer endpoint will be modified to support returning a v2 list via
a version number embedded in the path, which, similar to broadcast messages,
will be built using the stored current and future VLs.

#### Data structures

The `ValidatorList` currently defines a member to hold the published VLs
and look them up by the public key of the publisher:

```C++
// Published lists stored by publisher master public key
hash_map<PublicKey, PublisherList> publisherLists_;
```

First, `PublisherList` will need to be modified to add a
`TimeKeeper::time_point validFrom;` member to store the `effective` date.
This member will not be `optional`.
Instead, if an older VL is encountered which does not contain an `effective`
field, this member will be assigned as if it was `0`, i.e. the start of the
ripple epoch. The existing `TimeKeeper::time_point expires` field will be renamed to
`validUntil`.

Then, the `publisherLists_` member will be modified to hold a collection of
`PublisherList` as the value type.

Without going into too much implementation detail, define a new
structure to hold the VLs, and use it for the `publisherLists_`:

```C++
struct PublisherListCollection
{
  PublisherList current;
  std::vector<PublisherList> remaining;
};

// Published lists stored by publisher master public key
hash_map<PublicKey, PublisherListCollection> publisherLists_;
```

The `current` VL will be defined as the one which

1. Has the largest sequence number that
2. Has ever been effective (the `effective` date is absent or in the past).
   - If this VL has expired, all VLs with previous sequence numbers will
     also be considered expired, and thus there will be no valid VL until
     one with a larger sequence number becomes effective. This is to prevent
     erroneous or intentional "funny business" allowing old VLs to reactivate.
   - This maps to the current expiration behavior.

The `remaining` list will hold any relevant VLs which have a larger sequence
number than `current`. By definition they will all have an `effective`
date in the future. Relevancy will be determined by sorting the VLs by
sequence number, then iterating over the list and removing any VLs for
which the following VL (ignoring gaps) has the same or earlier
`effective` date.

If a series of VLs is created such that the `expiration` date of one
is later than the `effective` date of the following VL, then that contiguous
series of VLs won't expire until the `expiration` date of the last
VL of the chain, regardless of any gaps in their sequence numbers.

A "well-behaved" publisher is expected to maintain their VL file to reduce
the need for rippled to drop any VLs. Their VLs will be published such
that VL sequence `n` will be effective before VL sequence `n+1`. If
pending VL sequence `n` needs to be replaced, it may be replaced with
`n+1` with an earlier `effective` date, but sequence `n` should be
removed from the published site.

#### File processing.

File download code will not need any changes.

The `ValidatorSite::parseJsonResponse` function will need to be modified to
deal with the new top level `blobs-v2` field, and pass an array of
`blob/signature/manifest` tuples (where the manifest is only provided if it
overrides) to `ValidatorList::applyListAndBroadcast`. For the remainder
of this document, these tuples will be referred to as `BlobInfo`, though
they may not have that name in the implementation.
The top-level `BlobInfo` can be added to that array.

Additionally, `applyListAndBroadcast` will need to add a `NetworkOPs
const&` parameter so that
[`clearUNLBlocked`](#stopping-and-resuming-operations-on-expiration)
can be called when a new VL is accepted.

In the initial release, to prevent potential abuse and attacks,
**any VL collection with more than 5 entries will be considered malformed.**

`ValidatorList::applyListAndBroadcast` will need to be rewritten to send each
`BlobInfo` individually to `ValidatorList::applyList` and process the
collective results (both in memory and in the file). Both `applyList` and
`verify` in `ValidatorList` will only need to be modified to handle the
`effective` date, and update the new `PublisherListCollection::current`
if appropriate. It may be possible for more than one VL from a list to be
assigned to `current` as the list is processed - that's OK, because any
older versions will be
overwritten. However, the mutex lock will need to be moved up to
`applyListAndBroadcast` (or a new intermediate wrapper function),
`applyList` will need to be made private, and some tests will need to be
updated. Finally, the list will need to be filtered before broadcasting,
to only send those which are worth keeping (it would make the most sense
to build the `PublisherListCollection` first, then build the v2 message
from that), and to send an appropriate message to peers which understand
the older and newer protocols (see [below for protocol
changes](#protocol-changes-for-v2-unl-broadcasts)).

As a last step, `applyListAndBroadcast` (or the new intermediate wrapper
function) will iterate over _all_ of the known publishers in
`publisherLists_`. If all of them are valid and up to date, it will call
[`NetworkOPs::clearUNLBlocked`](#stopping-and-resuming-operations-on-expiration).
This is the only mechanism that will allow node to resume normal
operation if a VL expires without a replacement and
`setUNLBlocked` is called.

In `applyList` and `verify`, all `blob`s will be validated independently.
New `ListDisposition` values, `pending` and `known_sequence` will be added
for VLs which have not yet reached their `effective` date. `pending` will
be returned for VLs with future `effective` dates and `sequence` numbers
larger than the max VL `sequence` in `PublisherListCollection`.
`known_sequence` will be returned for VLs with a future `effective` date,
and a `sequence` not greater than the max VL `sequence` in
`PublisherListCollection` - though not necessarily _in_ the
`PublisherListCollection`.

A VL which gets a `pending` result will always be treated as new (because
it is), while a `known_sequence` result will always be treated as if it
is held in the `PublisherListCollection` members, even if it is not. This
is to prevent a publisher from "rewriting the future" by replacing an
already published `sequence` number or trying to fill in a gap. Publishers
should always use a new `sequence` when publishing a new list, even if
it's not yet effective.

The intention of `pending` and `known_sequence` are to correspond
to `accepted` and `same_sequence`, respectively, in both the way the
decision is made, and in the way the VL is treated.

`verify` will be modified to reject any `applyManifest` result that
isn't `ManifestDisposition::accepted`. Any VL files that use the
`blobs-v2` object `manifest` entry should be processed before any that
don't, and will be cached in memory until rippled restarts. This will be
important to test. However, it is important to document that best
practice when incrementing the Manifest sequence number is to resign all
valid `blob`s, publish them with their new signatures, and never
populate the `manifest` field in `BlobInfo`. _(Is this worth supporting
right out of the gate? Is the benefit of not needing to resign blobs in
this rare situation worth the extra complexity and data field?)_

The processor can safely ignore any older VLs, including any that are
expired, or which have a lower sequence number than the `current`.

#### Reading and writing cache files

Reading cache files (e.g.
`cache.ED2677ABFFD1B33AC6FBC3062B71F1E8397C1505E1C42C64D11AD1B28FF73F4734`
written to the `[node_db]` directory) will not require any extra
changes, because the same code path is used for processing files as
http(s) URLs.

The only change needed is to write the files out in the v2 format. The
`CacheValidatorFile` function will need to set up the JSON object to
populate `blobs-v2` instead of `blob/signature` from `current` and
`remaining`. Always write the blobs in sequence order. [Also add a field
to write out the publisher's public
key.](https://github.com/ripple/rippled/pull/3488) Change the JSON
construction to use `jss` parameters instead of strings.

Refactor the construction code used to build the JSON in
`CacheValidatorFile` and `getAvailable` to call a common function so we
can avoid inconsistencies.

#### Protocol changes for V2 UNL broadcasts

A new entry will need to be added to `suppportedProtocolList`, incrementing
the current maximum version.

We could reuse the `TMValidatorList` message for sending VL collections,
but that will waste a lot of bandwidth because of duplicated data, such
as the `manifest`. Instead, create two new message types that will
mimic the v2 file format:

```C++
message TMValidatorListV2
{
  optional bytes manifest;
  required bytes blob;
  required bytes signature;
}
message TMValidatorListCollection
{
  required uint32 version;
  required bytes manifest;
  repeated TMValidatorListV2 blobs;
}
```

Peers that do not support the incremented protocol version will be sent
a single `TMValidatorList` containing the `current` VL. Those that do
will be sent one or more `TMValidatorListCollection`s.

The `TMValidatorListCollection` will be built from the
`PublisherListCollection`, creating one `TMValidatorListV2` for each
`BlobInfo`, then populating the `blobs` array in the
`TMValidatorListCollection`. Currently, the `Peer` object keeps track of
the latest sequence sent to that peer. When building the message for the peer,
continue to only send VLs the peer has not seen. For optimization, this may
require grouping peers by most recent sequence before building the message(s).

Before sending, check the message size, splitting it into multiple
messages if necessary. Use `Message.getBuffer().size()`. If the size is
larger than the message size limit (64Mb), split the array of
`TMValidatorListV2`s in half until it's small enough. If it gets down to
a single `BlobInfo`, send a `TMValidatorList`. If that is still larger
than the limit, don't send it at all.

Fortunately, because the messages are distinct, no conditional
processing needs to be done for the different messages. Processing of
the old `TMValidatorList` does not need to change at all (other than to
update for the changed API). The new `TMValidatorListCollection` should
be able to build the `BlobInfo` array directly from the `blobs` member
of the message and pass that to the updated
`ValidatorList::applyListAndBroadcast`.

#### Expiration and automatic rotation

There are two functions where the VL `expiration` is currently checked:

- `ValidatorList::expires`
- `ValidatorList::updateTrusted`

##### `ValidatorList::expires`

For now, no changes will be made to `expires` to rotate VLs. When
computing the return value, starting with `current` and continuing into
`remaining`, find the last VL where the `effective` date overlaps with
the `expiration` date of the previous. Use that VL's `expiration` date
in the return value calculation.

##### `ValidatorList::updateTrusted`

`updateTrusted` will be modified to take the `closeTime` of the
validated ledger (this might available in the caller
`NetworkOPsImp::beginConsensus` as `closingInfo.parentCloseTime`, but
check the implementation to confirm, and get the correct value if not)
and a `const&` to the `NetworkOPsImp` calling object.

For all time comparisons, if the wall clock time is more than 30 seconds
ahead of the `closeTime`, it will be used instead.

- While iterating over the publisher lists, if the first entry in `remaining`
  has an `effective` date before the `closeTime`, then it will be moved to
  `current`, and removed from `remaining`.
- Additionally, the `expiration` will be compared to the `closeTime`. If
  the `current` VL has expired and no replacement has been pulled out of
  `remaining`, then in addition to calling `removePublisherList`, call
  [`NetworkOPs::setUNLBlocked`](#stopping-and-resuming-operations-on-expiration).
  (Note that `removePublisherList` is also called from
  `ValidatorList::verify`, but that removes the publisher entirely. As
  currently implemented, if there is another publisher configured, the
  node will not get stuck. Is this behavior correct?)
  - If at the end of `updateTrusted`, `unlSize` is 0, (or `quorum` is set
    to max), also call `NetworkOPs::setUNLBlocked`. This
    addresses the scenario where all the publisher manifests are
    revoked.
- Finally, any updated `current` VLs will be broadcast to older peers (those
  that don't support the updated protocol version) so that they can get on
  the new VL as soon as possible.

#### Stopping and resuming operations on expiration

Define a new `std::atomic<bool> unlBlocked_{false};` in
`NetworkOPsImp`. The set and clear functions will set and clear the flag
respectively. The set function will also set the operating mode to
`TRACKING`. Also define an `isUNLBlocked` that returns the
value of the new flag. This parallels the `setAmendmentBlocked`
function except that this flag can be cleared.

Define a new `bool NetworkOPs::isBlocked()` function that
returns `isAmendmentBlocked() || isUNLBlocked()`. Call this
function in place of `isAmendmentBlocked` at all of the non-reporting
call sites listed [below](#expiration-call-tree-in-current-code) and in
`setMode` where `amendmentBlocked` is checked directly . At the
reporting sites, call `isUNLBlocked` separately, and report
that result.

As [described](#validatorlistupdatetrusted) [above](#file-processing),
`setUNLBlocked` is called when a VL expired.
`clearUNLBlocked` is called whenever a new downloaded VL is
accepted (in `ValidatorList::applyList`).

#### Reporting

There are two functions that return validator information for reporting
purposes via the RPC interface:

- `NetworkOPsImp::getServerInfo`
  - Will be left unchanged, since it only reports the number of sources
    and the next expiration time via `expires`.
- `ValidatorList::getJson`
  - This function loops over all the publishers, and includes information about
    all of their VLs the JSON `publisher_lists` array of objects.
  - Keep the same format and fields for the `current` VL (`seq, expiration,
list`). I don't think it's necessary to include `effective` for the
    `current` VL because it's no longer relevant.
  - Add an array of objects for `remaining` containing the same fields
    as `current`, plus a new field for `effective`.

#### Expand `/vl/` URL handling

Currently a request sent on the peer port to `/vl/{public key}` will
return the current (and only) VL for the publisher with that public key
if that key is trusted (`[validator_list_keys]` in the config). This
behavior will remain unchanged, and thus will stay backward compatible.

To support V2, the URL format will be changed to
`/vl[/{version}]/{public_key}`, where `version` is optional and defaults
to 1. The `ValidatorList::getAvailable` function will be modified to
take the version number.

If version is 1, `getAvailable` will return a version 1 `Json` object in
the same format as returned now, using the values from `current`.

If version is 2, `getAvailable` returns a version 2 `Json` object as
described [above](#future), building the `blobs-v2` array from `current`
and `remaining`. Don't forget to include `public_key`!

Any other value of version will return an unseated optional.

### UNL-tool changes (signer)

#### Need to add handling of `effective` date in UI and resulting `blob`

When signing a UNL, the "unl-tool" prompts for the "sequence number" and
"validity in days". It then adds that "validity" value to the current
date to compute the expiration date, rounding (up or down?) to midnight
UTC. It then builds the `blob` JSON, stringifies it, base 64 encodes it,
and signs it.

To support version 2, the unl-tool will add a prompt for the effective
date, and change the prompt for the expiration date. The workflow will
be something like:

- Prompt "Sequence number:", read the unsigned int value.
- Prompt "Delay until effective in days:", read the unsigned int value.
  - The `effective` time value will be computed from today plus this
    value , and rounded _down_ to midnight UTC, then converted to
    "ripple time".
  - If the value is 0, the `effective` field will not be populated.
- Prompt "Expiration after effective in days:", read the unsigned int value.
  - The `expiration` time value will be computed from the `effective`
    time plus this value. Rounding will not be necessary since the process
    adds whole days, and UTC doesn't have leap years. (_Is this
    correct?_)
  - A value of 0 will be invalid and cause an error or reprompt.
- Once the JSON is built, with or without the `effective` field, the
  signing process can continue unmodified.

## Backwards Compatibility

This spec was carefully designed and implemented to ensure that there are no backward compatibility issues.

## Reference Implementation

As noted above, this has already be implemented in rippled in commit
[4b9d3ca](https://github.com/XRPLF/rippled/commit/4b9d3ca7de7c5758fbd6ae774c74196fa6b4268c).

## Security Considerations

Needs discussion.

## Appendix

### Roads not taken

#### Migration options

These options were considered, but rejected because the risk of a v1 node seeing
and processing a v2 node before it's effective was deemed unacceptable.

##### 1. Implement backward compatibility

The UNL file format will be allowed to have multiple versions
simultaneously. The v1 data will be in the top-level `blob` and `signature`
fields. The v2 data will be in a single new top-level `blobs-v2` field,
described below.

The `blob` v2 format will only add fields to the v1 format,
which should be ignored by existing v1 parsers, and thus will be backward
compatible if allowed.

Older rippled nodes should be able to use the new format VL without any
problems until they get upgraded or amendment blocked for another
reason.

If `version` is 1, then `blob` and `signature` MUST be present, and will be
treated as if they are included in the `blobs-v2` array, even if there is no
`blobs-v2` array, or it's empty. This helps avoid data duplication and allows
for backward compatibility.

If `version` is 2, then `blobs-v2` MUST be present, and the file will be
considered malformed if either `blob` or `signature` are present, though
clients MAY ignore them.

Pros:

- With `version` 1, the file is both forward and backward compatible.
  Since older clients will ignore the `effective` date, the VL will be
  valid as long as it's not expired.

Cons:

- To maintain backward compatibility with `version` 1, the "next" `blob`
  (i.e. the first blob listed in `blobs-v2`) will have to be manually moved
  into the top level `blob` and `signature` sometime between the
  new VL's `effective` and the old VL's `expiration`. Until this is done,
  old clients will be using the outdated VL. This could be mitigated if
  newer nodes broadcast the updated VL to older nodes when they switch.
- If an older node ever sees a v2-formatted blob, it will start using it
  immediately, regardless of the `effective` date. Because this
  information can be sent via protocol messages, a buggy or malicious
  peer could cause this to happen prematurely.

Once the network has moved on to the point that older versions of rippled can
not function (e.g. because they are amendment blocked), then publishers
can change their `version` number to 2, and stop populating the top-level
`blob` and `signature` fields.

##### 2. Distinct versioning with optional URL migrations

Instead of handling the migration in the file and rippled code, this
option allows the publisher to _optionally_ publish two UNL files at
separate URLs. For example: https://vl.ripple.com (for v1) and
https://vl.ripple.com/v2 (for v2, obviously).

First, each version will be interpreted strictly - it's either v1 or v2,
though v1 interpreters will ignore the `effective` field in the blob if
it's present.

If the publisher chooses to publish multiple UNLs simultaneously, they
will be responsible for manually moving the current UNL to the v1 file
at the appropriate time.

To assist with migration of nodes, define a hard-coded path, `/v2`, and
for every URL defined in `[validator_list_sites]` that does not contain
that substring, add both the original URL and the URL with the path
appended to the list of UNL download sites. For example, if the config
file contains

```
[validator_list_sites]
https://vl.ripple.com
```

Then rippled will attempt to use both https://vl.ripple.com and
https://vl.ripple.com/v2.

But if the config file contains

```
[validator_list_sites]
https://vl.ripple.com/v2
```

Then only https://vl.ripple.com/v2 will be used.

Add a boolean configuration option to the validators.txt processing
named `[use_validator_site_suffix]` that defaults to true, but can be
overridden by node operators to explicitly disable this behavior.

Pros:

- Simplifies rippled code and file processing because there's no need to
  worry about conditional processing.

Cons:

- If the publisher publishes both v1 and v2 UNLs simultaneously, and
  doesn't use the default suffix, operators using their v2 UNL will have
  to manually change their config file.
- Like with their "backward compatibility" option, to maintain backward
  compatibility with `version` 1, the "next" `blob`
  (i.e. the first blob listed in `blobs-v2`) will have to be manually
  moved into the v1 file sometime between the new VL's `effective` and
  the old VL's `expiration`. Until this is done, old clients will be
  using the outdated VL. This could be mitigated if newer nodes
  broadcast the updated VL to older nodes when they switch.
- By default rippled will make twice as many requests to the publishers'
  websites. This isn't too bad, since requests are only made every
  5 minutes, but this may still be significant enough to mention.
- If an older node ever sees a v2-formatted blob, it will start using it
  immediately, regardless of the `effective` date. Because this
  information can be sent via protocol messages, a buggy or malicious
  peer could cause this to happen prematurely.

## References

### Issues

- [Allow prepublishing of a UNL with a future activation date](https://github.com/ripple/rippled/issues/3548)
- [Validator List Expiration Improvements](https://github.com/ripple/rippled/issues/3470)

### Expiration call tree in current code

- `expiration` is checked
  - `ValidatorList::expires` returns the earliest date that any VL expires.
    - `NetworkOPsImp::getServerInfo`
    - `RCLConsensus::Adaptor::preStartRound`
    - `ValidatorList::getJson`
  - `ValidatorList::updateTrusted` - All validators from expired lists are
    removed from the list of master public keys (`keyListings`). Also sets
    `quorum_` to maxint.
    - `NetworkOPsImp::beginConsensus`

- `AmendmentTable::hasUnsupportedEnabled`
  - `LedgerMaster::setValidLedger` calls `NetworkOPs::setAmendmentBlocked`
- `amendmentBlocked_` is checked
  - `NetworkOPsImp::isAmendmentBlocked`
    - `RCLConsensus::Adaptor::preStartRound`
    - `LedgerMaster::setValidLedger`
    - `ApplicationImp::serverOkay`
    - `NetworkOPsImp::getServerInfo`
    - `ripple::RPC::conditionMet<T>`
  - `NetworkOPsImp::setMode`
