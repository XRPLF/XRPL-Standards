<pre>
  xls: [XLS number]
  title: [The title is a few words, not a complete sentence]
  description: [Description is one full (short) sentence]
  implementation: [optional - link to rippled PR for Amendment/System XLSes]
  author: [a comma separated list of the author(s) with email addresses]
  category: [Amendment | System | Ecosystem | Meta]
  status: [Draft | Final | Living | Deprecated | Stagnant | Withdrawn]
  proposal-from: [link to XRPL-Standards Proposal discussion where this XLS was proposed]
  requires: [optional - XLS number(s) if this depends on other features]
  created: YYYY-MM-DD
  updated: YYYY-MM-DD
</pre>

> **Note:** This is the suggested template for new XLS specifications. After you have filled in the requisite fields, please delete the guidance text (italicized bracketed instructions).

_[The requirements to sections depend on the type of proposal. For example, amendments require some information that may not be relevant for other kinds of proposals. Please adapt the template as appropriate.]_

_[The title should be 44 characters or less. The title should NOT include "XLS" prefix or the XLS number.]_

_[For Proposals (pre-Draft stage), the title must include the category prefix (e.g., "Meta XLS: XLS Process and Guidelines").]_

# [Title]

## 1. Abstract

_[Abstract is a multi-sentence (short paragraph) technical summary. This should be a very terse and human-readable version of the specification section. Someone should be able to read only the abstract to get the gist of what this specification does.]_

## 2. Motivation _(Optional)_

_[A motivation section is critical for XLSes that want to change the protocol. It should clearly explain why the existing protocol specification is inadequate to address the problem that the XLS solves. This section may be omitted if the motivation is evident.]_

## 3. Specification

_[The technical specification should describe the syntax and semantics of any new feature. The specification should be detailed enough to allow competing, interoperable implementations.]_

> **Note:** It is recommended to follow RFC 2119 and RFC 8174. Do not remove the key word definitions if RFC 2119 and RFC 8174 are followed.

_[For Amendment XLSes, use the [AMENDMENT_TEMPLATE.md](./AMENDMENT_TEMPLATE.md) to structure this section with detailed subsections for Serialized Types, Ledger Entries, Transactions, Permissions, and RPCs as needed.]_

_[For other XLS types, provide a clear technical specification.]_

## 4. Rationale

_[The rationale fleshes out the specification by describing what motivated the design and why particular design decisions were made. It should describe alternate designs that were considered and related work, e.g. how the feature is supported in other languages. The rationale should discuss important objections or concerns raised during discussion around the XLS.]_

## 5. Backwards Compatibility _(Optional)_

_[All XLSes that introduce backwards incompatibilities must include a section describing these incompatibilities and their consequences. The XLS must explain how the author proposes to deal with these incompatibilities. This section may be omitted if the proposal does not introduce any backwards incompatibilities, but this section must be included if backward incompatibilities exist.]_

## 6. Test Plan _(Optional)_

_[A description of the process to test the feature the authors are proposing. The test plan may be either inlined in the XLS file or included in the `../xls-###/<filename>` directory, where `###` refers to the XLS number. An implementation test plan is mandatory for XLSes that affect rippled. This section may be omitted for Ecosystem and Meta proposals.]_

## 7. Reference Implementation _(Optional)_

_[An optional section that contains a reference/example implementation that people can use to assist in understanding or implementing this specification. For an Amendment/System XLS, a `Final` XLS must include a link to the rippled PR(s)/commit(s).]_

## 8. Security Considerations

_[All XLSes must contain a section that discusses the security implications/considerations relevant to the proposed change. Include information that might be important for security discussions, surfaces risks, and can be used throughout the life-cycle of the proposal. E.g. include security-relevant design decisions, concerns, important discussions, implementation-specific guidance and pitfalls, an outline of threats and risks and how they are being addressed. XLS submissions missing the `Security Considerations` section will be rejected. An XLS cannot proceed to status `Final` without a `Security Considerations` discussion deemed sufficient by the reviewers.]_

## 9. Operational Considerations

_[All XLSes should contain a section that discusses the integration implications of the proposed change, for end users and developers integrating this feature into their applications. This should include information on how the change will be integrated with existing systems, and any potential impact on other XLSes or the overall ecosystem. This section is optional for Meta XLSes.]_

# Appendix _(Optional)_

## Appendix A: FAQ _(Optional)_

_[A list of questions the author expects to be asked about the spec, and their answers. It is highly recommended but not required to include this section, to make it easier for spec readers to understand it.]_

### A.1: [Question]

_[Answer to the question]_
