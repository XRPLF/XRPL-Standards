# XRP Ledger Standards / Drafts

To ensure interoperability between XRP (Ledger) applications, tools, platforms, pursuing a great user experience, it would be best if the
community (developers, users) agree on certain implementations.
  
# Contributing / Workflow

### All drafts start as [**DISCUSSIONS**](https://github.com/xrp-community/standards-drafts/discussions).

Drafts (discussions) are considered work in progress, and are up for [discussion (please discuss, ask, suggest, add, ...)](https://github.com/xrp-community/standards-drafts/discussions). Once settled on the standard, the discussion will be converted to an **ISSUE**, to be referred to in a **PULL REQUEST** adding the standard to the **CODE** (commit). Now the issue can be resolved.

# Directory
When a standard moves to a folder + file(s) in the Code section of this repository, it will be added to the `standards.toml` file:
https://github.com/XRPLF/XRPL-Standards/blob/master/standards.toml

# Numbering

Standards must be numbered and referenced in the following format: XLS-# where # is a natural number (without left padded zeros), called the __Standard Number__.

# Revisions

If a standard requires revision a separator '.' may be added. E.g. XLS-1.1

# Drafts

A standard which has not yet been adopted may 'hold' a Standard Number but must be referred to with a __d__ suffix until it becomes a full standard. For example XLS-10d or XLS-1.2d

# Reserved Standard Numbers

XLS-1 through XLS-100 inclusive are reserved for core protocol and communication and between or within contracts.

# Remaining Standard Numbers

XLS-200 and beyond are 'user-space' standards and may represent any optional or non-core functionality desired.

# Minimum Implementation

A contract to be XLS-standards compliant must implement, at minimum, XLS-1 (or preferably the latest revision thereto) which defines the call, call-back and interface exposure procedures for contract communication.
