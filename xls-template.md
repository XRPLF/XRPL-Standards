---
title: <The title is a few words, not a complete sentence>
type: draft
description: <Description is one full (short) sentence>
author: <a comma separated list of the author(s)>
# The format of each author should be one of the following:
# - Author's name, author's affiliation (organization or company) + GitHub username (in parenthesis)
# - Author's name, author's affiliation + email (in angle brackets)
#
# Example: FirstName LastName, OrganizationName (@GitHubUsername) , FirstName LastName, BarCompany <foo@bar.com>
requires: <XLS number(s)> # Only required when you reference an XLS in the `Specification` section. Otherwise, remove this field.
core_protocol_changes_required: <true/false> # Indicates whether the proposal requires any changes to the core protocol.
---

<!--
  This is the suggested template for new XLS specifications. After you have filled in the requisite fields, please delete these comments.
  
  The requirements to sections depend on the type of proposal. For example, amendments require some information that may not be relevant for other kinds of proposals. Please adapt the template as appropriate.

  The title should be 44 characters or less.

  TODO: Remove this comment before submitting
-->

## Abstract

<!--
  The Abstract is a multi-sentence (short paragraph) technical summary. This should be a very terse and human-readable version of the specification section. Someone should be able to read only the abstract to get the gist of what this specification does.

  TODO: Remove this comment before submitting
-->

## Motivation

<!--
  This section is optional.

  The motivation section should include a description of any nontrivial problems the XLS solves. It should not describe how it solves those problems, unless it is not immediately obvious. It should not describe why the XLS should be made into a standard, unless it is not immediately obvious.

  With a few exceptions, external links are not necessary in this section. If you feel that a particular resource would demonstrate a compelling case for the XLS, then save it as a printer-friendly PDF, put it in the folder with this XLS, and link to that copy.

  TODO: Remove this comment before submitting
-->

## Specification

<!--
  The Specification section should describe the syntax and semantics of any new feature. The specification should be detailed enough to allow competing, interoperable implementations.

  It is recommended to follow RFC 2119 and RFC 8170. Do not remove the key word definitions if RFC 2119 and RFC 8170 are followed.

  TODO: Remove this comment before submitting
-->

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "NOT RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in RFC 2119 and RFC 8174.

<!--
The following is an example of how you can document new transactions, ledger entry types, and fields:

#### **`<entry name>`** ledger entry

<High level overview, explaining the object>

##### Fields

<Any explanatory text about the fields overall>

---

| Field Name        | Required?        |  JSON Type      | Internal Type     |
|-------------------|:----------------:|:---------------:|:-----------------:|
| `<field name>` | :heavy_check_mark: | `<string, number, object, array, boolean>` | `<UINT128, UINT160, UINT256, ...>` |

<Any explanatory text about specific fields. For example, if an object must contain exactly one of three fields, note that here.>

###### Flags

> | Flag Name            | Flag Value  | Description |
>|:---------------------:|:-----------:|:------------|
>| `lsf<flag name>` | `0x0001`| <flag description> |

<Any explanatory text about specific flags>

For "Internal Type, most fields should use existing types defined in the XRPL binary format's type list here: https://xrpl.org/docs/references/protocol/binary-format#type-list . If a new type must be defined, add a separate section describing the rationale for the type, its binary format, and JSON representation.

For cases of transaction definitions, note any error cases that can occur. If the transaction can fail with a tec-class result code, specify which code to use. (Since tec codes are immutable data recorded in the ledger, changing them can render previous data incompatible with the current implementation. Also, tec codes are finite and limited, so it's best to reuse existing codes where appropriate.) Details of error codes can be vague or incomplete at first, but should be refined as the proposal moves through the candidate specification process.
-->

## Rationale

<!--
  The rationale fleshes out the specification by describing what motivated the design and why particular design decisions were made. It should describe alternate designs that were considered and related work, e.g. how the feature is supported in other languages.

  The current placeholder is acceptable for a draft.

  TODO: Remove this comment before submitting
-->

TBD

## Backwards Compatibility

<!--

  This section is optional.

  All XLS specs that introduce backwards incompatibilities must include a section describing these incompatibilities and their severity. This section must explain how the author proposes to deal with these incompatibilities. Submissions without a sufficient backwards compatibility treatise may be rejected outright.

  The current placeholder is acceptable for a draft.

  TODO: Remove this comment before submitting
-->

No backward compatibility issues found.

## Test Cases

<!--
  This section is optional.

  The Test Cases section should include expected input/output pairs, but may include a succinct set of executable tests. It should not include project build files. No new requirements may be be introduced here (meaning an implementation following only the Specification section should pass all tests here.)
  If the test suite is too large to reasonably be included inline, then consider adding it as one or more files in the folder with this XLS. External links are discouraged.

  TODO: Remove this comment before submitting
-->

## Invariants

<!--
  This section is optional, but recommended.

  Invariants are rules for a feature's behavior that should never be broken, which define the borders of normal behavior and the assumptions involved in the design. If a situation violates an invariant, then it can be identified as unintended behavior; this helps to catch and prevent bugs. Code for the XRP Ledger includes invariant checks, which can prevent a transaction from executing if it would otherwise violate an invariant rule, preventing buggy or corrupted data from becoming part of the XRP Ledger's immutable history. The invariants defined here can be used to create invariant checks, although this spec can include invariants that are impractical to check at runtime.

  TODO: Remove this comment before submitting

-->

## Reference Implementation

<!--
  This section is optional.

  The Reference Implementation section should include a minimal implementation that assists in understanding or implementing this specification. It should not include project build files. The reference implementation is not a replacement for the Specification section, and the proposal should still be understandable without it.
  If the reference implementation is too large to reasonably be included inline, then consider adding it as one or more files in the folder with this XLS. External links are discouraged.

  TODO: Remove this comment before submitting
-->

## Security Considerations

<!--
  All XLS documents must contain a section that discusses the security implications/considerations relevant to the proposed change. Include information that might be important for security discussions, surfaces risks, and can be used throughout the lifecycle of the proposal. For example, include security-relevant design decisions, concerns, important discussions, implementation-specific guidance and pitfalls, an outline of threats and risks, and how they are being addressed. Submissions missing the "Security Considerations" section may be rejected.

  The current placeholder is acceptable for a draft.

  TODO: Remove this comment before submitting
-->

Needs discussion.

