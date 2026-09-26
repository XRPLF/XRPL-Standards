# Meta XLS: XLS Process and Guidelines

<pre>
  xls: 1
  title: XLS Process and Guidelines
  description: Formalizes the process and structure for XRP Ledger Standards
  author: Mayukha Vadari (@mvadari), Vito Tumas (@Tapanito)
  status: Living
  category: Meta
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/340
  created: 2025-09-22
  updated: 2025-12-02
</pre>

## 1. Abstract

This document formalizes the XRP Ledger Standards (XLS) process, clarifying categories of standards, defining their lifecycle, and establishing editorial responsibilities. It:

- Introduces four categories of XLSes - `Amendment`, `System`, `Ecosystem`, and `Meta` - to resolve ambiguity between protocol-level changes and community-driven conventions.
- Standardizes the progression of XLSes from idea to finalization.
- Introduces clear formatting and content requirements.
- Specifies how discussions, ownership, and editorial oversight are managed.

Inspired by Ethereum’s [EIP-1](https://eips.ethereum.org/EIPS/eip-1), this proposal adapts established standards processes to the unique needs of the XRPL ecosystem, ensuring transparency, accountability, and long-term maintainability of the standards that guide XRPL development.

## 2. Motivation

The existing XLS process lacks clarity and consistency. In practice, “XLS” has been used to describe both protocol-level amendments and off-chain community standards, leading to confusion within the ecosystem. Furthermore, the lack of a formalized lifecycle, staleness rules, and editorial responsibilities has made it difficult to track proposals, maintain quality, and ensure transparency. This document introduces structure to the process, aligning the XLS process with proven practices from other ecosystems (most notably Ethereum’s EIPs), while tailoring them to the needs of the XRPL community.

## 3. XLS Categories

The name “XLS” can often get confusing, since it can refer to something that is an amendment (e.g. XLS-20 for the NFT amendment) or something that is a community standard and does not have any on-chain enforcement (e.g. XLS-24 for the NFT metadata standard). Ethereum disambiguates these with EIPs vs ERCs, for example.

This document proposes splitting XLSes into four categories: **Amendment**, **System**, **Ecosystem**, and **Meta**. Each category will be a selectable “category” when creating a discussion.

### 3.1. Amendment XLSes

This category contains standards that would require an amendment. Every feature amendment must have an XLS associated with it.

Some examples:

- [XLS-20](https://github.com/XRPLF/XRPL-Standards/tree/master/XLS-0020-non-fungible-tokens) (NFTs)
- [XLS-30](https://github.com/XRPLF/XRPL-Standards/tree/master/XLS-0030-automated-market-maker) (AMM)

### 3.2. System XLSes

This category contains standards that would not require an amendment, but do affect some other part of the XRPL protocol. This includes RPCs, the p2p protocol, or similar. This involves core-level code changes in rippled.

Every major system-level design change should have an XLS associated with it.

Some examples:

- [XLS-45](https://github.com/XRPLF/XRPL-Standards/tree/master/XLS-0045-prepublish-validator-lists) (Prepublish Validator Lists)
- [XLS-69](https://github.com/XRPLF/XRPL-Standards/tree/master/XLS-0069-simulate) (`simulate`)

### 3.3. Ecosystem XLSes

This category contains standards that pertain to the community or off-chain data, such as metadata standards.

Some examples:

- [XLS-24](https://github.com/XRPLF/XRPL-Standards/discussions/69) (NFT metadata)
- [XLS-50](https://github.com/XRPLF/XRPL-Standards/discussions/145) (Expanded TOML info for validators)

### 3.4. Meta XLSes

This category contains standards that pertain to XLSes themselves, such as this document.

## 4. XLS Process

Every XLS must have a status included in its heading:

- **Idea**: An idea that is pre-draft. This is currently reflected by the “Pre-Proposal Idea” category in the existing XLS discussions.
- **Proposal**: A fairly fleshed-out proposal for an XLS. This is currently reflected by the "Standard Proposal" category in the existing XLS discussions.
- **Draft**: The first formally tracked stage of an XLS in development. An XLS is merged by an XLS Editor into the XLS repository when properly formatted. XLS numbers will be assigned at this stage.
- **Final**: This XLS represents the final standard. A `Final` XLS exists in a state of finality and should only be updated to correct errata and add non-normative clarifications. For rippled-related XLSes, the XLS can only be considered `Final` once the rippled PR has been merged. For other XLSes, there needs to be at least one project that has implemented full support of the Standard.
- **Living**: A special status for XLSes that are designed to be continually updated and not reach a state of finality. This includes, for example, this XLS.
- **Deprecated**: This is an XLS in any category that was deprecated, as it is no longer supported. Due to the nature of XRP Ledger such features, especially amendment ones, may or may not be permanently removed from the codebase. Only a `Final` feature may be `Deprecated` .
- **Stagnant**: Any XLS in `Draft` if inactive for a period of 6 months or greater is moved to `Stagnant`. An XLS may be resurrected from this state by Authors or XLS Editors through moving it back to Draft.
- **Withdrawn**: The XLS Author(s) have withdrawn the proposed XLS. This state has finality and can no longer be resurrected using this XLS number. If the idea is pursued at a later date it is considered a new proposal.
  - If the XLS is withdrawn because it is superseded, the newer replacement XLS is linked.

<img width="951" height="471" alt="image" src="https://github.com/user-attachments/assets/7371b656-023e-486b-8945-7b7581ca6927" />

_Note: the “Review” and “Last Call” statuses have been removed from those listed in EIP-1, as we do not have formal processes established for review for XLSes (e.g. Core EIPs need to be approved by all client implementations). This may be re-added in the future, if such processes are desired._

### 4.1. Format: Ideas

There are no formatting requirements for Ideas.

### 4.2. Format: Proposals

The main formatting requirement for a `Proposal` is that its title must include its category - e.g. `Meta XLS: XLS Process and Guidelines`. It must generally be in the format of a `Ddraft` and should contain most of the sections required for `Draft`s, as this will make `Draft` generation easier later and distinguishes `Proposal`s from `Idea`s, but does not need to be a full-fledged `Draft`.

### 4.3. Format: Drafts and Onward

Any XLS that wants to be considered for `Draft` status should have the following parts:

- **Preamble**: RFC 822 style headers containing metadata about the XLS, including the XLS number, a short descriptive title (limited to a maximum of 44 characters), a description (limited to a maximum of 140 characters), and the author details. Irrespective of the category, the title and description should not include XLS number. See below for details.
- **Abstract**: Abstract is a multi-sentence (short paragraph) technical summary. This should be a very terse and human-readable version of the specification section. Someone should be able to read only the abstract to get the gist of what this specification does.
- **Motivation** (optional): A motivation section is critical for XLSes that want to change the protocol. It should clearly explain why the existing protocol specification is inadequate to address the problem that the XLS solves. This section may be omitted if the motivation is evident.
- **Specification**: The technical specification should describe the syntax and semantics of any new feature. The specification should be detailed enough to allow competing, interoperable implementations. See below for details.
- **Rationale**: The rationale fleshes out the specification by describing what motivated the design and why particular design decisions were made. It should describe alternate designs that were considered and related work, e.g. how the feature is supported in other languages. The rationale should discuss important objections or concerns raised during discussion around the XLS.
- **Backwards Compatibility** (optional): All XLSes that introduce backwards incompatibilities must include a section describing these incompatibilities and their consequences. The XLS must explain how the author proposes to deal with these incompatibilities. This section may be omitted if the proposal does not introduce any backwards incompatibilities, but this section must be included if backward incompatibilities exist.
- **Test Plan** (optional): A description of the process to test the feature the authors are proposing. The test plan may be either inlined in the XLS file or included in the `../xls-###/<filename>` directory, where `###` refers to the XLS number. An implementation test plan is mandatory for XLSes that affect rippled. This section may be omitted for Ecosystem and Meta proposals.
- **Reference Implementation** (optional): An optional section that contains a reference/example implementation that people can use to assist in understanding or implementing this specification. For an Amendment/System XLS, a `Final` XLS must include a link to the rippled PR(s)/commit(s).
- **Security Considerations**: All XLSes must contain a section that discusses the security implications/considerations relevant to the proposed change. Include information that might be important for security discussions, surfaces risks, and can be used throughout the life-cycle of the proposal. E.g. include security-relevant design decisions, concerns, important discussions, implementation-specific guidance and pitfalls, an outline of threats and risks and how they are being addressed. XLS submissions missing the `Security Considerations` section will be rejected. An XLS cannot proceed to status `Final` without a `Security Considerations` discussion deemed sufficient by the reviewers.
- **Appendix** (optional): Other information pertaining to the spec that are not strictly a part of the spec, such as tradeoffs and alternate approaches considered.
  - **FAQ** (optional): A list of questions the author expects to be asked about the spec, and their answers. It is highly recommended but not required to include this section, to make it easier for spec readers to understand it.
  - **Design Discussion** (optional): An optional section that summarizes why the given design decisions were made, to avoid the need to rehash that discussion.

All sections must be filled out with reasonable completeness and effort.

#### 4.3.1. Preamble

Each XLS must begin with an [RFC 822](https://www.ietf.org/rfc/rfc822.txt) style header preamble, contained in a `<pre>` HTML block. The headers must appear in the following order.

- `xls`: XLS number (assigned by the Editors - this field must not be included in `Idea`s or `Proposal`s). This field should _only_ contain the number and nothing else.
- `title`: The XLS title is a few words, not a complete sentence. This field should _only_ contain the title, not an `XLS` prefix or the XLS number.
- `description`: Description is one full (short) sentence
- `implementation`: A link to the `rippled` (or other repo) PR associated with the spec, if applicable. This must be included for `Amendment` and `System` proposals for them to be considered `Final`.
- `author`: The list of the author’s or authors’ name(s) and/or username(s), or name(s) and email(s).
- `category`: One of `Amendment`, `System`, `Ecosystem`, or `Meta`.
- `status`: `Draft`, `Final`, `Living`, `Deprecated`, `Stagnant`, `Withdrawn`
- `withdrawal-reason`: A sentence explaining why the XLS was withdrawn. (Optional field, only needed when status is Withdrawn. If this proposal was superseded by another, that can be listed here.)
- `proposal-from`: A link to the `Proposal` associated with this XLS. This field may be excluded from old standards (due to processes changing over time) but must be included in any new XLS (as there must be a `Proposal` before a PR is created).
- `requires`: XLS number(s) (Optional field)
- `created`: The date the XLS was created on.
- `updated`: The date the XLS was last updated.

_Headers that permit lists must separate elements with commas._
_Headers requiring dates will always do so in the format of ISO 8601 (yyyy-mm-dd)._

### 4.4. Format: Amendment XLS

An amendment usually introduces a set of semantically coherent ledger objects and transactions. The specification must make clear the purpose, introduced ledger entries and transactions. Optionally, the amendment specification can introduce new APIs, and include an optional F.A.Q.

_Note: all fields specified above in the “Drafts and Onward” section must also be included here._

#### 4.4.1. Index

A Markdown index to make navigating a long specification easier. This field is optional and left to the author’s discretion.

#### 4.4.2. Introduction

A section to succinctly introduce the protocol that the amendment introduces.

- **Terminology** (optional): A section to provide a glossary of terms used across the specification.
- **System Diagram** (optional): For complex protocols a system diagram that describes the relationship between different components of the system.
- **Summary**
  - **Serialized Types**: A list of serialized types and their purpose introduced by the amendment.
  - **Ledger Entries**: A list of ledger entries and their purpose introduced by the amendment.
  - **Transactions**: A list of transactions and their purpose introduced by the amendment.
  - **API**: A list of RPCs and their purpose introduced by the amendment (if applicable).

#### 4.4.3. Specification

The technical specification describing the syntax and semantics of a new feature. The specification should be detailed enough to allow competing, interoperable implementations. See below for details.

This will be codified in a template later.

##### 4.4.3.1. Serialized Types

`Serialized Types` documents one or more new "serialized types" (or STypes) introduced or modified by the specification. Most specifications will not need such sections, as the[ existing types](https://xrpl.org/docs/references/protocol/binary-format#type-list) are generally enough. Each SType must be in its own numbered section, with the following subsections:

###### 4.4.3.1.1. `SType` value

Each SType has its own unique value associated with it, so that when an object is being deserialized, the deserializer knows which decoder to use. The current values are specified [here](https://github.com/XRPLF/rippled/blob/develop/include/xrpl/protocol/SField.h#L60).

###### 4.4.3.1.2. JSON Representation

This subsection describes how an instance of the new SType will be represented in JSON (which is how most users will see and interact with it). For example, an `STAccount` is represented as an r-address `string`.

###### 4.4.3.1.3. Additional Accepted JSON Inputs

This optional subsection describes additional JSON representations may be parsed. For example, a `UInt32` can be passed in as an `int`, a `uint`, or a `string`, even though its output is always a `uint`.

###### 4.4.3.1.4. Binary Encoding

This subsection describes how an instance of the new SType will be encoded or serialized in binary. For example, [this](https://xrpl.org/docs/references/protocol/binary-format#accountid-fields) describes how an `STAccount` is serialized.

###### 4.4.3.1.5. Example JSON and Binary Encoding

Provide JSON and binary examples for what this SType will look like.

##### 4.4.3.2. Ledger Entries

`Ledger Entries` documents one or more new ledger entry objects introduced or modified by the specification. Each ledger entry must be in its own numbered section, with the following subsections:

###### 4.4.3.2.1. Object Identifier

Each object on the XRP Ledger must have a unique object identifier (ID or key). The ID for a given object within the ledger is calculated using "tagged hashing". This involves hashing some object-specific parameters along with a type-specific prefix called the `key space` (a 16-bit value) to ensure that different objects have different IDs, even if they use the same set of parameters The key space is given as a `hex` representation in the specification. This section introduces the key space and the algorithm for how to calculate a unique object identifier. It is critical that the algorithm does not create collisions between two objects.

###### 4.4.3.2.2. Fields

This subsection describes the ledger entry fields in a tabular format, indicating whether a field is constant or optional, its JSON type (for reference, actual storage is binary), Internal Type, and Default Value. The field table MUST include all standard ledger entry fields (like `LedgerEntryType`, `Flags`, `PreviousTxnID`, `PreviousTxnLgrSeq`, `OwnerNode`) as well as fields unique to the ledger entry. The `Account` field is typical for objects owned by a single account.

These columns must all be included in the table:

- **Field Name**: The column indicates the field's name. Fields follow the `PascalCase` naming convention. For existing field names (and their associated types), please refer to `sfields.macro`. A rule of thumb is to reuse already existing fields whenever possible and sensible.
- **Constant**: Indicates whether the Ledger Entry field is mutable after creation.
  - **Yes**: the field is constant.
  - **No**: the field is not constant.
- **Required**: Indicates whether the field is required for the object to be valid.
  - **Yes**: The field is required
  - **No**: The field is optional.
  - **Conditional**: The field is required under certain circumstances, described in the subsection following the fields table.
- **Internal Type**: The internal data type of the field. Refer to [this page](https://xrpl.org/docs/references/protocol/binary-format#type-list) for all internal types (e.g., `UINT16`, `ACCOUNT`, `HASH256`). Internal types must be in all capital letters. Please refer to [`sfields.macro`](https://github.com/XRPLF/rippled/blob/develop/include/xrpl/protocol/detail/sfields.macro) for a list of existing internal types.
- **Default Value**: The field's default value when the ledger entry is created.
  - `N/A`: The field does not have a default value or is always required.
- **Description**: A brief description of the field. Further details can be written in a subsection of **Fields**.

The table may be followed by subsections for fields requiring further details that are too long for the Description column.

###### 4.4.3.2.3. Flags

This subsection describes all the ledger entry `lsf` flags in a tabular format.

These columns must all be included in the table:

- **Flag Name**: The column indicates the flag's name. Flags follow the `lsfPascalCase` naming convention.
- **Flag Value**: The column indicates the flag's value. Flag values are powers of 2 expressed as 32-bit integers, written in hexadecimal with a `0x` prefix (e.g., `0x00010000`).
- **Description**: A brief description of the flag. Further details can be written in a subsection of **Flags**.

###### 4.4.3.2.4. Ownership

All XRP Ledger objects must have an owner. The owner is an `AccountRoot` object, and the ownership relationship is typically established by adding the object's ID to an `OwnerDirectory` ledger entry associated with the owner's account. This subsection captures which `AccountRoot` object's `OwnerDirectory` the ledger entry is registered. A single ledger entry may be linked from one or more unique `DirectoryNode` pages, usually under one `OwnerDirectory`.

_Note: there are a handful of object types (such as `FeeSettings`) that don’t have an owner. If an amendment is of that ilk, that should be specified in this section._

###### 4.4.3.2.5. Reserves

Creating ledger entries typically requires an increase in the owner's XRP reserve to discourage ledger bloat and account for the cost of storage. Each new ledger entry directly owned by an account typically increments the owner reserve by one unit (currently 0.2 XRP, as of last check, but subject to change by [Fee Voting](https://xrpl.org/docs/concepts/consensus-protocol/fee-voting)). This section should confirm whether this standard behavior applies or specify any deviations.

###### 4.4.3.2.6. Deletion

This subsection captures the conditions under which the ledger entry can be deleted from the ledger. It should specify:

- What transaction(s) can delete the object.
- Any prerequisite conditions for deletion (e.g., object state, zero balances, no linked objects).
- Is the ledger entry a "blocker" for deleting its owner `AccountRoot` (i.e., whether it must be deleted before the account can be deleted).

###### 4.4.3.2.7. Pseudo-Account

This section is optional. A "pseudo-account" might be associated if the newly introduced ledger entry needs to hold assets (XRP, IOUs or MPTs) or issue tokens (e.g., MPTs). A pseudo-account is a programmatically derived `Account` that cannot submit transactions, send or receive funds directly via standard payments, or have a key pair. For further details about pseudo-accounts, refer to [XLS-64](https://github.com/XRPLF/XRPL-Standards/pull/274) (or the relevant accepted standard). This section should specify if a pseudo-account is used, how its `AccountID` is derived, and its purpose.

###### 4.4.3.2.8. Freeze/Lock

This section is optional. If the protocol holds assets on behalf of other users, it must comply with the existing compliance features `Freeze`, `Deep Freeze` for IOUs and `Locking` for MPTs. This section describes how said freezing is handled.

###### 4.4.3.2.9. Invariants

Invariants are logical statements that MUST be true of a ledger entry's state before and after the execution of any transaction (whether successful or not). They help ensure that no transaction leads to an invalid or inconsistent ledger state. Use `<object>` for the state before and `<object>'` (see the added grave) for the state after.

###### 4.4.3.2.10. RPC Name

In RPCs like `account_objects` and `ledger_data`, a short, `snake_case` form of the name of a ledger entry is accepted in the `type` parameter, to filter the ledger entries returned by type. This section should specify that version of the entry's name.

###### 4.4.3.2.11. Example JSON

Provide JSON examples for what the ledger object will look like.

##### 4.4.3.3. Transactions

This section details new or modified transactions introduced by the specification.

Transaction names should be descriptive, often taking the form of `<LedgerEntryName><Verb>`, where:

- `<LedgerEntryName>` is the name of the ledger entry the transaction primarily interacts with (e.g., `Example`). \*`<Verb>` identifies the action of this transaction (e.g., `Set`, `Delete`, `Invoke`).

One example of this naming convention is `ExampleSet` and `ExampleDelete`. Most specifications introducing new objects will have at least:

- `<Object>Set` (or `<Object>Create` and `<Object>Update` if distinct complex logic): A transaction to create or update an object.
- `<Object>Delete`: A transaction to delete the object.

The following subsections must be included in a `Transaction` section.

###### 4.4.3.3.1. Fields

This section outlines transaction fields, provides details about them, defines special logic, failure conditions, and state changes. This table should list fields specific to this transaction. Common transaction fields (e.g., `Account`, `Fee`, `Sequence`, `Flags` (common transaction flags), `SigningPubKey`, `TxnSignature`) are assumed unless their usage has special implications for this transaction type.

The following columns should be included:

- **Field Name:** The column indicates the field's name. Fields follow the `PascalCase` naming convention. For existing field names (and their associated types), please refer to `sfields.macro`. A rule of thumb is to reuse already existing fields whenever possible and sensible.
- **Required?**:
  - **Yes**, **No**, or **Conditional** (with conditions explained).
- **JSON Type**: For JSON submission (e.g., `string`, `number`, `object`, `array`).
- **Internal Type**: The internal data type of the field. Refer to `rippled` for all internal types (e.g., `UINT16`, `ACCOUNT`, `HASH256`). Internal types must be in all capital letters. Please refer to `sfields.macro` for a list of existing internal types.
- **Default Value**: If any. `N/A` if none or always required.
- **Description**: Succinct description of the field.

###### 4.4.3.3.2. Flags

This subsection describes all the ledger entry `tf` flags in a tabular format.

These columns must all be included in the table:

- **Flag Name**: The column indicates the flag's name. Flags follow the `tfPascalCase` naming convention.
- **Flag Value**: The column indicates the flag's value. Flag values are powers of 2 expressed as 32-bit integers, written in hexadecimal with a `0x` prefix (e.g., `0x00010000`).
- **Description**: A brief description of the flag. Further details can be written in a subsection of **Flags**.

###### 4.4.3.3.3. Transaction Fee

Submitting a transaction typically requires paying a transaction fee. A typical transaction costs 10 drops as of last check (subject to change by [Fee Voting](https://xrpl.org/docs/concepts/consensus-protocol/fee-voting)). This section should confirm whether this standard behavior applies or specify any deviations.

###### 4.4.3.3.4. Failure Conditions

This section describes all conditions under which the transaction will fail. Each condition must map to a specific error code. The list must be exhaustive, descriptive, and indexed for easy reference.

Failure conditions are grouped into two categories:

- Data validation failures: Return a `tem` code
- Protocol-level failures: Return `tec` codes. With rare exceptions they may return a `ter`, `tef`, or `tel` code. If another error code must be returned, justification must be provided.

In case of a transaction failure, an XRP Ledger server returns an error code indicating the outcome. These codes are crucial for clients to understand why a transaction was not successful. Please refer to the [documentation](https://xrpl.org/docs/references/protocol/transactions/transaction-results) for existing error codes. When defining failure conditions for a new transaction type in an XLS, reuse existing codes whenever an existing code accurately describes the failure condition. This helps maintain consistency and avoids unnecessary proliferation of codes.

If the new transaction logic introduces novel failure reasons not adequately covered by existing generic codes, a new error code (usually a `tec` code) should be proposed. This new code must be clearly defined and justified and would eventually be added to [rippled](https://github.com/XRPLF/rippled/blob/develop/include/xrpl/protocol/TER.h) if the XLS is adopted. XLS authors will primarily define error codes for their specific transaction logic failures.

###### 4.4.3.3.5. State Changes

This section describes the changes made to the ledger state if the transaction executes successfully. It should omit default state changes common to all transactions (e.g., fee processing, sequence number increment, setting `PreviousTxnID`/`PreviousTxnLgrSeq` on modified objects). The list must be exhaustive, descriptive, and indexed for easy reference. When using the same transaction to create and update an object, the expected behavior is identified by the presence or absence of the object identifier (e.g., `tx.ExampleID`). A successfully applied transaction must return a `tesSUCCESS` code.

###### 4.4.3.3.6. Metadata Fields

This section describes any additions or modifications (synthetic or otherwise) to the transaction metadata. This section must not be included if the transaction does not make any such additions or modifications.

The following columns should be included in the table:

- **Field Name:** The column indicates the field's name. Validated fields follow the `PascalCase` naming convention, while synthetic fields follow the `snake_case` naming convention. For existing field names (and their associated types), please refer to `sfields.macro` and `jss.h`. A rule of thumb is to reuse already existing fields whenever possible and sensible.
- **Validated**:
  - **Yes**: if the field is validated (e.g. `DeliveredAmount`)
  - **No**: if the field is synthetic (e.g. `nftoken_id`)
- **Always Present?**:
  - **Yes**, **No**, or **Conditional** (with conditions explained).
- **Type**: If the field is synthetic, this should specify the The JSON type of the field (e.g., `string`, `number`, `object`, `array`).
- **Description**: Succinct description of the field.

###### 4.4.3.3.7. Example JSON

Provide JSON examples for transaction submission.

##### 4.4.3.4. Permissions

This section details new or modified [granular account permissions](https://github.com/XRPLF/XRPL-Standards/tree/master/XLS-0074-account-permissions#23-granular-permissions) introduced by the specification.

No subsections are required for this section. The section must mention what transaction type(s) this granular permission applies to, and what the scope of the granular permission is.

The new transaction type permissions are implied by the addition of the transaction.

##### 4.4.3.5. API/RPCs

New amendments often introduce new APIs or modify existing APIs. Those API descriptions should also be outlined in a spec. APIs are how developers and users will be interacting with the new feature, so it is important to achieve consensus on the format and fields (especially since a breaking change would require bumping the API version).

For each new API added (or modified), these sections should be included:

###### 4.4.3.5.1. Request Fields

- **Field Name:** The column indicates the field's name. Fields follow the `snake_case` naming convention. For existing field names, please refer to `jss.h`. A rule of thumb is to reuse already existing fields whenever possible and sensible.
- **Required?**:
  - **Yes**, **No**, or **Conditional** (with conditions explained).
- **JSON Type**: The JSON type of the field (e.g., `string`, `number`, `object`, `array`).
- **Description**: Succinct description of the field.

###### 4.4.3.4.2. Response Fields

- **Field Name:** The column indicates the field's name. Fields follow the `PascalCase` naming convention. For existing field names (and their associated types), please refer to `sfields.macro`. A rule of thumb is to reuse already existing fields whenever possible and sensible.
- **Always Present?**:
  - **Yes**, **No**, or **Conditional** (with conditions explained).
- **JSON Type**:The JSON type of the field (e.g., `string`, `number`, `object`, `array`).
- **Description**: Succinct description of the field.

###### 4.4.3.5.3. Failure Conditions

This section describes the conditions under which the API will fail. This must be an exhaustive, descriptive list. Each condition should ideally map to a specific error code. The list should be indexed for easy reference.

In case of an API failure, an XRP Ledger server returns an error code and error message indicating the outcome. These codes and messages are crucial for clients to understand why an API was not successful. Please refer to the [documentation](https://xrpl.org/docs/references/http-websocket-apis/api-conventions/error-formatting) for what this looks like. When defining failure conditions for a new API in an XLS, reuse existing codes whenever an existing code accurately describes the failure condition. This helps maintain consistency and avoids unnecessary proliferation of codes.

If the new API logic introduces novel failure reasons not adequately covered by existing generic codes, a new error code should be proposed. This new code must be clearly defined and justified and would eventually be added to [rippled](https://github.com/XRPLF/rippled/blob/develop/include/xrpl/protocol/ErrorCodes.h) if the XLS is adopted. XLS authors will primarily define error codes for their specific API logic failures.

### 4.5. Stale Proposals/Ideas

All discussions will be checked for staleness after 90 days, and if no one responds for another 30 days, the discussion will be closed and locked. The author can reach out to the repo maintainers to reopen the issue at a later date, if desired.

The repo could use [this Github Action](https://github.com/marketplace/actions/stalesweeper) to enforce this rule automatically.

## 5. Writing Specs for Already-Implemented Features

Many parts of the XRP Ledger are currently undocumented and un-specced. Giving them a new XLS number would make it seem like said feature is new, which is not the case. Therefore, these specs will be given a slightly different prefix, `PXLS`, to indicate that it is a "Preceding" XLS.

## 6. XLS Ownership

The XLS author writes the XLS. By default, the author is also the owner and champion, who shepherds the discussions and builds community consensus around the idea. At any time, the author can choose a different champion for the XLS.

### 6.1. Transferring XLS Ownership

It occasionally becomes necessary to transfer ownership of XLSes to a new champion. In general, we’d like to retain the original author as a co-author of the transferred XLS, but that’s really up to the original author. A good reason to transfer ownership is because the original author no longer has the time or interest in updating it or following through with the XLS process, or has fallen off the face of the 'net (i.e. is unreachable or isn’t responding to email). A bad reason to transfer ownership is because you don’t agree with the direction of the XLS. We try to build consensus around an XLS, but if that’s not possible, you can always submit a competing XLS.

If you are interested in assuming ownership of an XLS, send a message asking to take over, addressed to both the original author and the XLS editor. If the original author doesn’t respond to the email in a timely manner, the XLS editor will make a unilateral decision, which can be reversed if needed.

## 7. XLS Editors

XLS Editors are those that have at least “write” access to the XRPL-Standards repository.

### 7.1. XLS Editor Responsibilities

The editors don’t pass judgment on XLSes. They merely do the administrative & editorial part.

For each new XLS that comes in, an editor does the following:

- Read the XLS to check if it is ready: sound and complete. The ideas must make technical sense, even if they don’t seem likely to get to final status.
- The title should accurately describe the content.
- Check the XLS for language (spelling, grammar, sentence structure, etc.), markup (GitHub flavored Markdown), code style
- If the XLS isn’t ready, the editor will send it back to the author for revision, with specific instructions.

Once the XLS is ready to be merged, the XLS editor will:

- Assign an XLS number (generally incremental; editors can reassign if number sniping is suspected)
- Merge the corresponding pull request
- Send a message back to the XLS author with the next step.

The following is a non-exhaustive list of what editors do and don’t:

#### 7.1.1. What Editors Do

The editors’ mission is to serve the broad XRP Ledger community, both present and future, by:

- **Publishing Proposals**: Making proposals, including their history and associated discussions available over the long term at no cost. By doing so, editors foster transparency and ensure that valuable insights from past proposals are accessible for future decision-making and learning.
- **Facilitating Discussion**: Providing a forum for discussing proposals open to anyone who wants to participate civilly. By encouraging open dialogue and collaboration, we aim to harness the collective knowledge and expertise of the XRP Ledger community in shaping proposals.
- **Upholding Quality**: Upholding a measure of minimally-subjective quality for each proposal as defined by its target audience. By adhering to defined criteria, we promote the development of high-quality and relevant proposals that drive the evolution of the XRP Ledger.

#### 7.1.2. What Editors Don’t Do

On the other hand, editors do not:

- **Decide Winners**: If there are multiple competing proposals, editors will publish all of them. They are not in the business of deciding what is the right path for XRP Ledger, nor do they believe that there is One True Way to satisfy a need.
- **Assert Correctness**: While they might offer technical feedback from time to time, they are not experts nor do they vet every proposal in depth. Publishing a proposal is not an endorsement or a statement of technical soundness.
- **Manage**: They do not track implementation status, schedule work, or set fork dates or contents.
- **Track Registries**: They want all proposals to eventually become immutable, but a registry will never get there if anyone can keep adding items. To be clear, exhaustive and/or static lists are fine.
- **Provide Legal Advice**: Trademarks, copyrights, patents, prior art, and other legal matters are the responsibility of authors and implementers, not XLS Editors. They are not lawyers, and while they may occasionally make comments touching on these areas, they cannot guarantee any measure of correctness.

#### 7.1.3. Membership

Anyone may apply to join as an XLS Editor. Specific eligibility requirements are left to individual current XLS Editors, but the general requirements are:

- A strong belief in the above mission
- Proficiency with English (both written and spoken)
- Reading and critiquing XLSes

XLS Editors are expected to meet these requirements throughout their tenure, and not doing so is grounds for removal. Any member may delegate some or all of their responsibilities/powers to tools and/or to other people.

### 7.2. Current Editors

The current XLS editors are:

- Mayukha Vadari ([@mvadari](https://github.com/mvadari))
- David Fuelling ([@sappenin](https://github.com/sappenin))
- Vito Tumas ([@Tapanito](https://github.com/Tapanito))

## 8. Rationale

The design of this process balances familiarity with existing standards frameworks and the specific needs of the XRPL community.

The categories ensure that it’s easy to distinguish between the very different types of XLSes. An Ecosystem XLS has very different implications compared to an Amendment XLS, and previously they were all under the same umbrella.

The more formalized statuses and process make it easier for XLS writers to understand what their specs need to look like and how to move them along the process, and make it easier for XLS readers to understand what the current status of the spec is.

Automatic closure of inactive discussions ensures the process remains active and reduces noise in the repository, while allowing authors to revive proposals at any time.

Editors are now explicitly not decision-makers but facilitators, ensuring decentralization and preventing gatekeeping.

## 9. Security Considerations

This proposal does not directly alter XRPL consensus or protocol behavior and therefore carries minimal direct security risks.

However, governance processes themselves can affect the security of the ecosystem. By formalizing categories, statuses, and editor responsibilities, this document mitigates risks of ambiguity, miscommunication, and fragmentation that could otherwise lead to competing or unclear implementations. Transparent rules for authorship, ownership transfer, and editor conduct further reduce the risk of malicious exploitation of unclear standards governance.

## 10. History

This document was derived heavily from Ethereum’s [EIP-1](https://eips.ethereum.org/EIPS/eip-1) (written by Martin Becze and Hudson Jameson et al) and [EIP-5069](https://eips.ethereum.org/EIPS/eip-5069) (written by Pooja Ranjan, Gavin John, Sam Wilson, et al), which in turn was derived from Bitcoin’s [BIP-0001](https://github.com/bitcoin/bips/blob/master/bip-0001.mediawiki) and Python’s [PEP-0001](https://peps.python.org/pep-0001/). In many places text was simply copied and modified. None of the people involved with those precursors are responsible for its use in the XRP Ledger Standards process, and should not be bothered with technical questions specific to the XRPL or the XLS. Please direct all comments to the XLS editors.

Some previous conversations on this topic in this repo, in no particular order:

- https://github.com/XRPLF/XRPL-Standards/discussions/160
- https://github.com/XRPLF/XRPL-Standards/discussions/21
- https://github.com/XRPLF/XRPL-Standards/discussions/32

## Appendix

### Appendix A: Changelog from the Existing System

- The post-PR process of finalizing an XLS is more standardized.
- The role of the XLS Editor (i.e. those that maintain this repo) is more formalized.
- XLS numbers are assigned at PR creation instead of at discussion creation.
  - _Note: this does not mean numbers will be gatekept. Any proposed XLS can obtain a number if they follow the process to become a Draft._
- XLS discussions and drafts can become stale/stagnant if a certain amount of time passes without any progress.

### Appendix B: FAQ

#### B.1: How can I create a PR for a new XLS if I don’t know the number?

With EIPs, the PR author creates a PR with a document titled `eip-draft.md`, and there is a bot that informs the author what number they have been assigned. This repo can implement a similar setup (e.g. create `XLS-draft/README.md`).

The initial rollout of this system will probably involve a maintainer assigning numbers instead of a bot.

#### B.2: What do we do about the unused numbers in the middle, like XLS-36?

They are simply skipped. This way, XLS numbers are roughly incrementing in order of time of assignment.

#### B.3: What will happen to existing XLS numbers that Discussions have already claimed?

Those will remain with those discussions, to avoid confusion. The process proposed in this document will, if consensus agrees, be applied to future `Proposal`s and `Idea`s.

#### B.4: What will happen to XLSes that have already been written and merged into the repo?

They will be grandfathered in for now. Ideally someone (perhaps with the help of an AI) will go back and update them to match the desired format.
