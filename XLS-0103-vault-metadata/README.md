<pre>
  xls: 103
  title: Standard Data for Vaults
  description: Recommended use of the Vault arbitrary data field to improve discoverability, attribution, and context for Single-Asset Vaults on XRPL
  author: Ashray Chowdhry, Julian Berridi
  status: Draft
  category: Ecosystem
  requires: XLS-65
  created: 2026-01-28
  updated: 2026-01-28
</pre>

# Standard Data for Vaults

## Abstract

Single-Asset Vaults on the XRP Ledger include an arbitrary data field intended to store freeform metadata about the Vault. While this field provides flexibility, the lack of a common convention makes it difficult for ecosystem participants to understand what a Vault represents, who operates it, and how it should be interpreted.

Today, associating a Vault with its operator or purpose often requires out-of-band knowledge, such as manually inspecting the owning account’s domain field or relying on off-ledger context. This creates friction for block explorers, indexers, analytics platforms, and users attempting to evaluate Vaults.

This document proposes a minimal, optional convention for using the Vault arbitrary data field to provide basic, human-readable context about a Vault. By standardizing a small set of fields, services can more reliably surface, label, and attribute Vaults across the XRPL ecosystem.

This proposal does not restrict how the arbitrary data field may otherwise be used. Vaults that follow this recommendation will simply be easier to identify and integrate into downstream applications.

---

## 1. Background and Motivation

The Vault object includes a `Data` field defined as:

> **Data**: Arbitrary metadata about the Vault. Limited to 256 bytes.

Because this field is unstructured, there is currently no consistent way to:

- Display a meaningful name for a Vault
- Link a Vault to a website or external source of information
- Understand the focus or strategy of a Vault at a glance

As Vaults become more widely used for institutional and ecosystem-facing use cases, the absence of standardized metadata limits transparency and usability.

---

## 2. Proposed Data Convention

This proposal defines a minimal JSON-based convention for the Vault `Data` field. The convention focuses on compact key names to accommodate the 256-byte size limit, while still providing sufficient context for discovery and attribution.

All fields defined below are optional but recommended.

### 2.1. Base Fields

| Field Name | Key | Description                                        | Example                      | Type   | Required? |
| ---------- | --- | -------------------------------------------------- | ---------------------------- | ------ | --------- |
| `name`     | `n` | Human-readable name of the Vault or fund           | LATAM Private Credit Fund II | string | ✔️        |
| `website`  | `w` | Website associated with the Vault operator or fund | examplefund.com              | string | ✔️        |

---

## 3. Usage Guidelines

- The `Data` field should contain a valid JSON object when following this convention.
- Short key names are recommended to minimize on-ledger storage usage.
- The `website` field may point to a fund page, dashboard, or general operator website.
- This convention is intended to complement, not replace, other attribution mechanisms such as account domain fields.

---

## 4. Example

The following example demonstrates a Vault `Data` payload that follows this recommendation:

```json
{
  "n": "LATAM Private Credit Fund II",
  "w": "examplefund.com"
}
```
