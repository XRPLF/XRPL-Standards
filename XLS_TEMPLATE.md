<pre>
  xls: <XLS number>
  title: <The title is a few words, not a complete sentence>
  description: <Description is one full (short) sentence>
  author: <a comma separated list of the author(s) with email addresses>
  discussion-from: [link to XRPL-Standards discussion where this XLS was proposed]
  status: Discussion
  category: Meta
  requires: [optional, based on if it depends on other features]
  created: YYYY-MM-DD
</pre>

<!--
  This is the suggested template for new XLS specifications. After you have filled in the requisite fields, please delete these comments.

  The requirements to sections depend on the type of proposal. For example, amendments require some information that may not be relevant for other kinds of proposals. Please adapt the template as appropriate.

  The title should be 44 characters or less.

  TODO: Remove this comment before submitting
-->

# Title

## 1. Abstract

<!--
  The Abstract is a multi-sentence (short paragraph) technical summary. This should be a very terse and human-readable version of the specification section. Someone should be able to read only the abstract to get the gist of what this specification does.

  TODO: Remove this comment before submitting
-->

## 2. Motivation

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

For "Internal Type", most fields should use existing types defined in the XRPL binary format's type list here: https://xrpl.org/docs/references/protocol/binary-format#type-list . If a new type must be defined, add a separate section describing the rationale for the type, its binary format, and JSON representation.

When defining transactions, please identify any potential error scenarios. If a transaction can fail with a `tec`-class result code, specify the appropriate code. Remember that tec codes are immutable ledger entries, so changing them can cause compatibility issues with older data. Additionally, as tec codes are limited in number, it's best to reuse existing codes whenever possible. While error code details may be initially vague or incomplete, they should be refined as the proposal progresses through the candidate specification process.
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

# Appendix

## Appendix A: FAQ

### A.1: Question
