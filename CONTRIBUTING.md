# CONTRIBUTING

Contributions to the XRPL-Standards repo are free, open source, and follow the following document publishing process.

Any XRPL-Standards document can be referred to interchangeably as an "XLS" (XRPL Standard), "RFC" (Request for Comments), or "document".

## Summary

Copyright on all content is subject to the terms of the [MIT License](LICENSE).

All contributors grant everyone:

Copyright – a royalty-free license to use the copyrights for their contributions.
Patent – a commitment to license on a royalty-free basis their essential patent claims reading on their contributions.

## Background

The work of the XRP Ledger community is open source, collaborative, and welcoming of all contributors participating in good faith. [Learn more about the XRP Ledger at XRPL.org](https://xrpl.org/).

This XRPL-Standards process is influenced by the well-established [IETF RFC process](https://www.ietf.org/standards/process/informal/).

## Process

The XRPL-Standards process attempts to be easy to use, but also rigorous enough that there are permalinks to revisions of documents for reference purposes.

### Gathering Feedback Before Submitting

Please gather community input before opening a PR. Collecting such feedback may be helpful to refine your concept.

Start a [Discussion](https://github.com/XRPLF/XRPL-Standards/discussions) under this repo.

You can also have a conversation with other community members in the [XRP Ledger Developers Discord server](https://xrpldevs.org/).

Discussions are suitable for early work-in-progress: ask, suggest, add, and make sweeping changes.

Once settled, the discussion should be converted to a **PULL REQUEST** adding the standard to the repo with one or more commits. At this time, the discussion should be archived and closed from further comments, with any further comments being posted on the PR for fine-tuning and alignment with implementation (as appropriate).

When opening a PR, there are two document types: *Drafts* and *Candidate Specifications*. The type and status of any particular document has no bearing on the priority of that document, although typically the further along in the process, the more likely it is that any particular XLS will be implemented.

### Drafts

A _Draft_ is a document that proposes some new feature, protocol or idea related to the XRP Ledger. The criteria for getting the document merged is minimal: project maintainers will review the document to ensure style conformance and applicability, but will otherwise not require editorial fixes before allowing it to be published.

A Draft is often stable enough for people to experiment with, but has not necessarily been endorsed by the entire community. When there are competing Drafts that address the same problem in different ways, all such Drafts can continue to be refined, promoted, and used independently, without any blocking. Implementors can create software to implement this type of standard into their codebase to explore how it works in a real world setting.

Any, or all, competing Drafts may graduate into a Candidate Specification.

Notice that a Draft is not a [rubber-stamp](https://idioms.thefreedictionary.com/rubber-stamp) of the content in any particular document. Documents can still undergo significant changes and potentially be discarded all together.

#### Publishing a Draft

To publish a new Draft, submit a Pull Request to this repo with a new folder and a new Markdown file. The folder MUST follow the naming convention `XLS-0000d-{title}`, `0000` is the unique number referencing the XLS, `d` indicates that the document is a Draft, and `title` is a lower case title with spaces replaced by hyphens (`-`). The submission should have front-matter (similar to GitHub pages rendered from Markdown) specifying at least a `title`, `type`, and `revision` (an integer, starting at 1 and incrementing with each revision of the RFC). The `type` MUST have the value `draft`.

Use the following template when creating the Markdown file: [xls-template.md](./xls-template.md)

Assuming there is consensus to publish, one of the project maintainers will review the submission and confirm the document's RFC number, often making a follow-up commit to the PR which renames the file as appropriate.

Subsequent updates to the document should increment the `revision` number in the front-matter.

### Candidate Specifications

A _Candidate Specification_ is a document that was previously a Draft that is considered stable enough by the community such that no further changes are required. Once an XLS becomes a Candidate Specification, no further substantive changes are allowed under the same RFC number.

#### Publishing a Candidate Specification

When a Draft is considered stable, there is a call for review from the community to publish the document as a Candidate Specification.

Assuming there is consensus to publish, a maintainer will remove the `d` from the document name, and update the `type` to `candidate-specification`.

Once published as a Candidate Specification, no further substantive changes are allowed under the same RFC number.

#### Errata

The community may discover errors in a Candidate Specification. In these circumstances, it is possible to update the document to fix typos or clarify the original meaning of the document. In these circumstances, the `revision` number should be incremented.

### Deprecated or Rejected RFCs

An RFC document may be rejected after public discussion has settled and comments have been made summarizing the rationale for rejection. Similarly, a document may be deprecated when its use should be discouraged. A member of the core team will move rejected and deprecated proposals to the `/rejected` folder in this repo.
