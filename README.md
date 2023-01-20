# XRP Ledger Standards / Drafts

To ensure interoperability between XRP (Ledger) applications, tools, platforms, pursuing a great user experience, it would be best if the
community (developers, users) agree on certain implementations.
  
# Contributing / Workflow

### All drafts start as [**DISCUSSIONS**](https://github.com/xrp-community/standards-drafts/discussions).

Drafts (discussions) are considered work in progress, and are up for [discussion (please discuss, ask, suggest, add, ...)](https://github.com/xrp-community/standards-drafts/discussions). Once settled on the standard, the discussion will be locked and converted to an **ISSUE**, to be referred to in a **PULL REQUEST** adding the standard to the **CODE** (commit). Now the issue can be resolved. 

In case a XLS draft results in an amendment to [rippled](https://github.com/XRPLF/rippled), it is considered adopted when the amendment is merged into the codebase. Hereafter it is the responsibility of the XLS author to update the draft to match the final implementation prior to creating an **ISSUE**.

It is not necessary to copy the entire draft to the **ISSUE**, but only to refer to the discussion.

# Directory
When a standard moves to a folder + file(s) in the Code section of this repository, it will be added to the `standards.toml` file:
https://github.com/XRPLF/XRPL-Standards/blob/master/standards.toml

# Numbering

Standards must be numbered and referenced in the following format: XLS-# where # is a natural number (without left padded zeros), called the __Standard Number__.

# Revisions

If a standard requires revision a separator '.' may be added. E.g. XLS-1.1

# Drafts

A standard which has not yet been adopted may 'hold' a Standard Number but must be referred to with a __d__ suffix until it becomes a full standard. For example XLS-10d or XLS-1.2d

