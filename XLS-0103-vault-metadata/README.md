<pre>
  title: Standard Metadata for Vaults
  description: Recommended use of the Vault arbitrary data field to improve discoverability, attribution, and context for Single-Asset Vaults on XRPL
  author: Ashray Chowdhry, Julian Berridi
  category: Ecosystem
  status: Proposal
  requires: XLS-65
  created: 2026-01-28
</pre>

# Standard Metadata for Vaults

## 1. Abstract

Single-Asset Vaults on the XRP Ledger include an arbitrary data field intended to store freeform metadata about the Vault. While this field provides flexibility, the lack of a common convention makes it difficult for ecosystem participants to understand what a Vault represents, who operates it, and how it should be interpreted.

Today, associating a Vault with its operator or purpose often requires out-of-band knowledge, such as manually inspecting the owning account’s domain field or relying on off-ledger context. This creates friction for block explorers, indexers, analytics platforms, and users attempting to evaluate Vaults.

This document proposes a minimal, optional convention for using the Vault arbitrary data field to provide basic, human-readable context about a Vault. By standardizing a small set of fields, services can more reliably surface, label, and attribute Vaults across the XRPL ecosystem.

This proposal does not restrict how the arbitrary data field may otherwise be used. Vaults that follow this recommendation will simply be easier to identify and integrate into downstream applications.

## 2. Motivation

The Vault object includes a `Data` field defined as:

> **Data**: Arbitrary metadata about the Vault. Limited to 256 bytes.

Because this field is unstructured, there is currently no consistent way to:

- Display a meaningful name for a Vault
- Link a Vault to a website or external source of information
- Understand the focus or strategy of a Vault at a glance

As Vaults become more widely used for institutional and ecosystem-facing use cases, the absence of standardized metadata limits transparency and usability.

## 3. Specification

This proposal defines a minimal JSON-based convention for the Vault `Data` field. The convention focuses on compact key names to accommodate the 256-byte size limit, while still providing sufficient context for discovery and attribution.

All fields defined below are optional but recommended.

### 3.1. Base Fields

| Field Name | Key | Description                                        | Example                      | Type   | Required? |
| ---------- | --- | -------------------------------------------------- | ---------------------------- | ------ | --------- |
| `name`     | `n` | Human-readable name of the Vault or fund           | LATAM Private Credit Fund II | string | ✔️        |
| `website`  | `w` | Website associated with the Vault operator or fund | examplefund.com              | string | ✔️        |

### 3.2. Usage Guidelines

- The `Data` field should contain a valid JSON object when following this convention.
- Short key names are recommended to minimize on-ledger storage usage.
- The `website` field may point to a fund page, dashboard, or general operator website.
- This convention is intended to complement, not replace, other attribution mechanisms such as account domain fields.

### 3.3. Example

The following example demonstrates a Vault `Data` payload that follows this recommendation:

```json
{
  "n": "LATAM Private Credit Fund II",
  "w": "examplefund.com"
}
```

## 4. Rationale

This standard was designed with the following considerations:

### 4.1. Compact Key Names

The 256-byte limit on the Vault `Data` field necessitates efficient use of space. Single-character keys (`n`, `w`) minimize overhead while remaining intuitive enough for developers to understand. This approach is similar to other space-constrained metadata formats used in blockchain ecosystems.

### 4.2. JSON Format

JSON was chosen as the data format because:

- It is widely supported across programming languages and platforms
- It provides structure while remaining human-readable
- It allows for easy extension with additional fields in the future
- It is already familiar to XRPL developers

### 4.3. Minimal Required Fields

Only two fields are recommended as required (`name` and `website`) to keep the barrier to adoption low. These two fields provide the most critical information for discovery and attribution:

- **Name**: Allows users and applications to display a meaningful identifier
- **Website**: Provides a verifiable link to the operator for additional context

Additional fields can be added by individual implementations without breaking compatibility with this standard.

### 4.4. Optional Convention

This standard is intentionally optional and does not restrict other uses of the `Data` field. Vault operators who need to store different metadata for specialized use cases can do so without violating this standard. However, following this convention improves interoperability across the ecosystem.

## 5. Security Considerations

### 5.1. Data Validation

Applications consuming Vault metadata should validate the JSON structure and sanitize all fields before display to prevent injection attacks or malformed data from causing issues.

### 5.2. Website Verification

The `website` field is not cryptographically verified and should not be treated as authoritative proof of ownership. Applications should:

- Display website URLs clearly to users for manual verification
- Consider cross-referencing with the account's `Domain` field
- Implement additional verification mechanisms if needed for high-trust scenarios

### 5.3. Immutability Considerations

Once a Vault is created, the `Data` field can be modified by the Vault owner through a `VaultSet` transaction. Applications should be aware that metadata can change and may want to track historical values for audit purposes.

### 5.4. Size Limits

The 256-byte limit is enforced at the protocol level. Applications should validate that their metadata fits within this limit before attempting to create or update a Vault.

### 5.5. No Sensitive Information

The `Data` field is publicly visible on the ledger. Vault operators should never include sensitive information such as private keys, personal data, or confidential business information in this field.
