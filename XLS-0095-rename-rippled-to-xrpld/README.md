<pre>
  xls: 95
  title: Rename ripple(d) to xrpl(d)
  description: Renames references of "ripple(d)" to "xrpl(d)" in the documentation and codebase, and other downstream changes.
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/384
  author: Bart Thomee (@bthomee)
  status: Draft
  category: System
  created: 2025-10-22
</pre>

# System XLS: Renaming ripple(d) to xrpl(d)

## 1 Abstract

This document describes a process to rename references of "ripple(d)" to "xrpl(d)" in the documentation and codebase of the XRPL open source project. This includes renaming the GitHub repository, the binary, configuration files, C++ namespaces, include guards, CMake files, code comments, artifacts, copyright notices, and the Ripple epoch.

## 2 Motivation

In the initial phases of development of the XRPL, the open source codebase was called “rippled” and it remains with that name even today. Today, over 1000 nodes run the application, and code contributions have been submitted by developers located around the world. The XRPL community is larger than ever. We at Ripple are proposing a few changes to the project in light of the decentralized and diversified nature of XRPL.

Some of what we describe here was floated [previously](https://github.com/XRPLF/XRPL-Standards/discussions/121) (see items 7 and 8), but ultimately was not followed up on. We are now taking this up again, because we deem it still to be the right thing to do.

## 3 Specification

### 3.1 Overview

We aim to make the following changes.

#### 3.1.1 Repository

We will rename the [rippled](https://github.com/XRPLF/rippled) GitHub repository to [xrpld](https://github.com/XRPLF/xrpld). After renaming, the former URL will forward all requests to the latter URL, so anyone with the old link will still be able to find the codebase.

#### 3.1.2 Binary

We will rename the `rippled` binary to `xrpld`, and add a symlink named `rippled` that points to `xrpld`, so that node operators do not have to change anything on their end initially. We will further remove this symlink six months later to complete the switchover.

#### 3.1.3 Config

We will rename the `rippled.cfg` configuration file to `xrpld.cfg`, and to modify the code to accept both files. As above, we will further remove the old configuration file six months later to complete the switchover.

#### 3.1.4 Namespace

We will rename the `ripple` C++ namespace to `xrpl`. This will require other projects, such as `clio` to make a one-time update to their codebase as well, which we will help them with.

#### 3.1.5 Include guards

C++ include guards are used to prevent the contents of a header file from being included multiple times in a single compilation unit. These include guards currently start with `RIPPLE_` or `RIPPLED_`. We will rename both prefixes to `XRPL_`.

#### 3.1.6 CMake

We will rename the compiler files from `RippleXXX.cmake` or `RippledXXX.cmake` to `XrplXXX.cmake`, and any references to `ripple` and `rippled` (with or without capital letters) to `xrpl` and `xrpld`, respectively.

#### 3.1.7 Code and comments

We will rename references to `ripple` and `rippled` (with or without capital letters) to `xrpl` and `xrpld`, respectively. We will leave flags such as `tfNoRippleDirect` and `ltRIPPLE_STATE` untouched, as those do not refer to the company but to the concept of [rippling](https://xrpl.org/docs/concepts/tokens/fungible-tokens/rippling).

#### 3.1.8 Artifacts

The .rpm and .deb packages, and the [Docker image](https://hub.docker.com/r/rippleci/rippled) will be renamed too. As above, we will maintain the current artifacts for a period of six months, after which they will no longer be updated.

#### 3.1.9 Copyright notices

The root of the repository contains a [LICENSE.md](http://license.md/) file that lists the original contributors for the year of 2011, and the XRP Ledger developers from 2012 onwards, which is as intended. However, this is sometimes inconsistent with the individual copyright notices scattered throughout the codebase, which refer to XRP Ledger developers in different ways.

Going forward, unless the copyright notices in individual files reference public code used from external projects (e.g. Bitcoin), such notices will be removed and the license file in the root of the repo will consistently apply throughout.

#### 3.1.10 Ripple epoch

We will rename the Ripple epoch, which refers to the timestamp of 01/01/2001 at 0:00 UTC, to XRPL epoch.

These changes should also be made in the various xrpl libraries, where functions such as `xrpl.utils.datetime_to_ripple_time` will be maintained for six months. During that time period they will forward calls to the renamed function and will print a warning to the log about the deprecation.

#### 3.1.11 Other

After making the changes described above, there will invariably be a few references that we somehow missed, or newly appeared after an open PR gets merged. We will update these on a case-by-case basis.

#### 3.1.12 Documentation

Once all references have been updated throughout the XRPLF codebases, we will also update the docs, code, samples, and tutorials hosted at [xrpl.org](https://xrpl.org/).

### 3.2 Implementation

To minimize disruption to contributors, operators, and others, we aim to implement the changes as follows.

#### 3.2.1 Execution

We will first make the changes that are purely cosmetic and do not require any action by the community:

- Include guards
- CMake
- Code and comments
- Copyright notices

We will next make the changes that should also be safe but carry some risk of unexpected behavior:

- Config
- Binary

We will finally make the changes that may require action from some community members and that carry more risk:

- Repository
- Namespace
- Ripple epoch
- Artifacts

Each of the changes listed above will be made separately. To avoid contributors having to rebase their PRs many times, we will perform the changes in the first group quickly. As the third group of changes is the most impactful and may need extensive collaboration with the community, we will roll them out slowly.

#### 3.2.2 Script

To assist developers in making the same changes to their forks or open PRs, we will add a script to the repository that will apply all changes to their local branch. This script will be updated each time we make a change.

#### 3.2.3 Support

Contributors, operators, and others may need to take some actions as part of this proposal. For instance, build failures are expected in PRs after we rename the namespace from `ripple` to `xrpl`. We will work with each of them to ensure the changes occur as smoothly as possible.

## 4 Rationale

Rolling out of the changes in stages as described above minimizes disruption to contributors, operators, and others. Instead of making the changes one by one, we can also combine groups of changes into a chain of PRs, which could reduce effort by contributors at the expense of more complex coordination of these in-flight PRs and a higher burden for reviewers. We opted for the former approach to keep things simple, but may reconsider if needed.

## 5 Security Considerations

The changes primarily involve renaming references in the codebase and documentation, and do not affect the functioning of the application. This notwithstanding, thorough testing will be conducted to verify that all changes are correctly implemented and do not introduce any regressions.

## 6 Appendix

### 6.1 FAQ

**Q: Why is this change necessary?**
A: The change is intended to better reflect the decentralized and diversified nature of the XRPL community.

**Q: I'm a node operator. What do I need to do?**
A: Initially, nothing. The `rippled` binary (symlink) and `rippled.cfg` configuration file will continue to work as before. However, within six months after the changes have been made, you will need to switch to using the `xrpld` binary and `xrpld.cfg` configuration file. This may involve updating scripts, automation, and/or monitoring that you use to manage your node.

**Q: I'm a developer with an open PR. What do I need to do?**
A: After the changes have been made, you will need to rebase your PR onto the updated `develop` branch. To assist you with this, we will provide a script that applies all changes to your local branch. Please reach out to us if you need help with this.

**Q: I'm a developer with a fork of the codebase. What do I need to do?**
A: Similar to the previous question, you will need to update your fork to reflect the changes made in the `develop` branch.

**Q: I'm a user of the XRPL. What do I need to do?**
A: Nothing will change for you. The changes are internal to the codebase and documentation, and do not affect the user experience.

**Q: Will there be any changes to the functionality of rippled?**
A: Similar to the previous question, no, the changes are purely cosmetic and do not affect the functionality of the application.
