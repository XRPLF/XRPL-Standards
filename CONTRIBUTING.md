# CONTRIBUTING

The work of the [XRP Ledger](https://xrpl.org) community is open, collaborative, and welcoming of all contributors participating in good faith. Part of that effort involves standardization, and this document outlines how anyone can contribute to that process. 

## Licensing
Any XRPL Standards document can be referred to interchangeably as an "XLS", "XRPL Standard", or "document".  Copyright on all content is subject to the terms of this [license](LICENSE), and all contributors grant everyone a royalty-free license to use their contributions, including the following grants: 

- Copyright: a royalty-free license to anyone to use any contributions submitted to this repository.
- Patent: a commitment to license on a royalty-free basis any essential patent claims relating to any contributions in this repository.

## Specification Process

### 1. Start a Discussion & Gather Feedback

Before opening a PR with any kind of formal proposal, please first gather community input by starting a [Discussion](https://github.com/XRPLF/XRPL-Standards/discussions). Discussions are suitable for early work-in-progress: ask, suggest, add, and make sweeping changes. Collecting such feedback helps to refine your concept, and is required in order to move forward in the specification process.

#### Discussion Title
When creating a new discussion for your idea, the discussion title should follow the naming convention `XLS-{0000}d {Title}`, where `{0000}` is a unique number for the XLS, `d` indicates that the document is a Draft (i.e., work in progress), and `{Title}` is a descriptive title for the proposed document.

#### Specification Number
Use the next number that has not yet been used. If a conflict occurs, it will be fixed by a maintainer or editor. Maintainers or editors also reserve the right to remove or re-number proposals as necessary. The number is important, as it will be used to reference features and ideas throughout the community.

### 2. Closing a Discussion

When a discussion has produced a well-refined standard, authors should post a comment to the discussion noting that the discussion will be closed in a few days. This allows time (for those engaged with the discussion) to submit final commentary. 

Once this waiting period has elapsed, the standard's author may close the discussion from further comment, and then move the discussion to a [**specification pull request**](#3-specification-pull-requests) to add the standard into the repository as a markdown file (see below for specification formats).

Next, the discussion author should edit the discussion to include a link to the PR. The last comment on the discussion should also be a link to the PR.

The intention of this workflow is that the discussion be closed from further comments, with further comments instead being posted on the PR for fine-tuning and alignment with implementation or adoption, as appropriate.

### 3. Specification Pull Requests

When opening a specification PR, there are two document types: *Drafts* and *Candidate Specifications*. The type and status of any particular document has no bearing on the priority of that document. Typically, the further along in the process, the more likely it is that any particular XLS will be implemented or adopted.

#### Drafts

A _Draft_ is a document that proposes some new feature, protocol or idea related to the XRP Ledger. The criteria for getting the document merged is minimal: project maintainers will review the document to ensure style conformance and applicability, but will otherwise not require editorial fixes before allowing it to be published.

A document does not need to have an implementation in order to become a Draft. A Draft may or may not have implementation(s) available and no code is required prior to the Draft being published.

A Draft is often stable enough for people to experiment with, but has not necessarily been endorsed by the entire community. When there are competing Drafts that address the same problem in different ways, all such Drafts can continue to be refined, promoted, and used independently, without any blocking. Implementors can create software to implement this type of standard into their codebase to explore how it works in a real world setting.

Any, or all, competing Drafts _may_ graduate into a Candidate Specification.

Notice that a Draft is not a [rubber-stamp](https://idioms.thefreedictionary.com/rubber-stamp) of the content in any particular document. Documents can still undergo significant changes and potentially be discarded all together.

##### Publishing a Draft

To publish a new Draft, submit a Pull Request to this repo with a new folder and a new Markdown file. The folder MUST follow the naming convention `XLS-{0000}d-{title}` where `{0000}` is the unique number referencing the XLS, `d` indicates that the document is a Draft, and `{title}` is a lower case title with spaces replaced by hyphens (`-`). The submission should have front-matter (similar to GitHub pages rendered from Markdown) specifying at least a `title` and `type`. The `type` MUST have the value `draft`.

An example draft name is: `XLS-20d-non-fungible-token-support-native`

Use the following template when creating the Markdown file: [xls-template.md](./xls-template.md)

Assuming there is consensus to publish, one of the project maintainers will review the submission and confirm the document's XLS number, often making a follow-up commit to the PR which renames the file as appropriate.

#### Candidate Specifications

A _Candidate Specification_ is a document that was previously a Draft, but is considered stable enough by the community such that no further changes are required. Once an XLS becomes a Candidate Specification, no further substantive changes are allowed under the same XLS number.

##### Publishing a Candidate Specification

When a Draft is considered stable, there is a call for review from the community to publish the document as a Candidate Specification by making a PR to remove the `d` from the document folder name and update the `type` to `candidate-specification`.


Once published as a Candidate Specification, no further substantive changes are allowed under the same XLS number.

For Specifications that require changes or implementation in the XRP Ledger server software and protocol, the Candidate Specification cannot be published until the relevant change has been merged into [the software's `master` branch](https://github.com/XRPLF/rippled/tree/master).

#### Errata

The community may discover errors in a Candidate Specification. In these circumstances, it is possible to update the document to fix typos or clarify the original meaning of the document.

### Deprecated or Rejected XLSs

An XLS document may be rejected after public discussion has settled and comments have been made summarizing the rationale for rejection. Similarly, a document may be deprecated when its use should be discouraged. A member of the core maintainer team will move rejected and deprecated proposals to the `/rejected` folder in this repo.
