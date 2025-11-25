---
xls: 104d
title: Auto-Compounding Single-Asset Yield Vault using Smart Issuer Accounts and Hooks
status: Draft
author: lj26ft (@lj26ft) & EverArcade Team
created: 2025-11-25
type: Standards Track
requires: Hooks Amendment
discussions-to: https://github.com/XRPLF/xrpl-standards/discussions
---

# XLS-104d: Auto-Compounding Single-Asset Yield Vault using Smart Issuer Accounts and Hooks

## Abstract

This standard defines a non-custodial, auto-compounding, single-asset yield vault built entirely with existing XRPL features: black-holed issuer accounts (Angell’s pattern) + immutable Hooks for all logic.  
No new ledger objects are introduced, preserving decentralization while delivering 2–4× higher effective APY than static vaults.

## Motivation

Manual harvesting in existing vaults (e.g., XLS-65d) is expensive UX on a low-fee ledger.  
A fully on-chain, Hooks-driven vault removes external keepers and scales to millions of instances without bloating rippled nodes.

## Design Principles

- 100 % XRPL-native settlement
- Zero additional storage load on consensus nodes
- Execution via Hooks amendment (mainnet-ready) + optional Evernode compute and Xahau CronSet
- Direct revenue share for XRPL validators and Evernode hosts

## Specification

### Vault Structure
A vault is a regular XRPL account:
- Master key disabled + black-holed
- Default Hook set to the official vault WASM
- Vault shares issued via trustlines (XLS-20)

### Trigger Mechanisms
1. Permissionless poke (any tx with “harvest” memo) + 0.2 % bounty  
2. Keeperless automation via Xahau CronSet transaction (recommended)

### Fee Model (basis points)
| Fee Type            | Rate | Recipient                            | Notes                                      |
|---------------------|------|--------------------------------------|--------------------------------------------|
| Performance fee     | 1500 | 70 % Owner, 20 % Evernode hosts, 10 % XRPL validators | 10 % carve-out exclusive to opted-in validators |
| Poke bounty         | 20   | 100 % to submitting host            | Only active when using poke trigger        |
| Protocol / arcade rake | 400 | Treasury + incentives               | Configurable                               |

### Validator Incentive
3 % of every harvested yield (300 bp of the performance fee) is reserved exclusively for opted-in XRPL validators, distributed pro-rata via emitted Payments from the harvest Hook.

## Current Status & Roadmap
- Hook reference implementation in active development (C + Rust)
- First Xahau alphanet deployment targeted within 7–14 days of this draft
- Live test vaults and EverArcade front-end to follow alphanet validation
- Full source will be published at https://github.com/everarcade/xrpl-vault-hook upon alphanet launch

## Open Questions
1. Fixed vs. governance-adjustable validator carve-out?
2. Recommended CronSet intervals for different yield strategies?
3. Standard vault registry Hook for on-chain discovery?

Feedback welcome in Discussions.
