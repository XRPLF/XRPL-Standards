<pre>
  title: Ephemeral Attested Credentials & Enclave-Gated Domains (E-APD)
  description: Hardware-attested short-TTL credentials, in-place rollover, and zero-latency consensus-enforced venue ejection for autonomous agents on XRPL
  author: Walter Hawkins <contact@correntelabs.com>, Corrente Applied Cryptography Group
  status: Draft
  category: Amendment
  amendment: featureEphemeralCredentials
  requires: [XLS-70](../XLS-0070-credentials/README.md), [XLS-80](../XLS-0080-permissioned-domains/README.md)
  created: 2026-10-06
  updated: 2026-10-07
</pre>

# XLS-draft: Ephemeral Attested Credentials & Enclave-Gated Domains (E-APD)

## Abstract
This standard defines an architecture for **Ephemeral Attested Permissioned Domains (E-APD)** on the XRP Ledger, introducing the `featureEphemeralCredentials` amendment. By combining hardware-isolated Trusted Execution Environments (Intel TDX / AMD SEV-SNP / AWS Nitro Enclaves) with short Time-To-Live (TTL) cryptographic credentials (60 to 3,600 seconds, nominally 300 seconds), in-place renewal rollover, and consensus-enforced validation, E-APD enables real-time compliance enforcement, automated mandate auditing, and **deterministic, bounded venue ejection** for autonomous AI agents, algorithmic market makers, and institutional participants on XRPL.

## 1. Motivation

The introduction of [XLS-70 (Credentials)](../XLS-0070-credentials/README.md) and [XLS-80 (Permissioned Domains)](../XLS-0080-permissioned-domains/README.md) on the XRP Ledger establishes native primitives for institutional compliance and permissioned decentralized exchange (DEX) trading. However, the existing credential revocation lifecycle suffers from critical structural vulnerabilities when applied to high-frequency autonomous AI agents:

1. **The Revocation Latency Gap**: Conventional credentials are static and long-lived (issued for weeks, months, or years). If an autonomous trading agent experiences an invariant violation, prompt injection exploit, or runaway liquidity drain, the compliance issuer must broadcast an on-chain `CredentialDelete` transaction.
2. **The Front-Running Attack Vector**: An adversarial or compromised agent monitoring the XRPL mempool can detect an incoming `CredentialDelete` transaction and immediately front-run it with higher fee escalations, executing unauthorized swaps or draining liquidity pools before revocation finality.
3. **Mempool & Network Congestion Risk**: During periods of high network activity or fee spikes, revocation transactions can be delayed across multiple ledgers.

### The Solution: Inverting the Revocation Paradigm
Instead of issuing long-lived credentials and revoking them reactively, **E-APD inverts the architecture**:
* Credentials are issued with an **ultra-short TTL** (bounded between 60 and 3,600 seconds; nominally 300 seconds / 5 minutes).
* An off-chain hardware enclave (Intel TDX / AMD SEV-SNP) continuously monitors agent invariants, trade telemetry, risk parameters, and budget mandates.
* As long as all invariants hold, the enclave automatically issues an in-place cryptographic renewal before the active TTL elapses.
* If an agent violates policy, **the enclave halts renewal**.
* Once the remaining TTL elapses ($\le 300$ seconds bounded worst-case latency), the credential expires naturally at L1 consensus, and any subsequent transaction by the agent within permissioned domains immediately fails with `tecNO_PERMISSION`.
* **Accelerated Immediate Ejection**: If instant venue removal is required before the remaining TTL expires, the enclave issuer may additionally broadcast an explicit `CredentialDelete`, preserving the standard immediate revocation option while providing a hard consensus-enforced ceiling on exposure even if the network is completely congested.

---

## 2. Technical Specification

### 2.1 Amendment Gating: `featureEphemeralCredentials`
All modifications defined in this specification are gated by the amendment `featureEphemeralCredentials`:
* **Pre-Activation**: Any transaction specifying `tfEphemeral` (or unrecognized flag bits) fails with `temINVALID_FLAG`.
* **Post-Activation**: The `tfEphemeral` flag (`0x00010000`) is recognized by `CredentialCreate` and enforced by consensus.

### 2.2 Transaction Types & Modifications

#### 2.2.1 `CredentialCreate` Flags & Validation Rules
Extends XLS-70 `CredentialCreate` with the following flag:

| Flag Name | Flag Value | Description |
| :--- | :--- | :--- |
| `tfEphemeral` | `0x00010000` | Declares the credential as ephemeral. Requires mandatory bounded `Expiration` and enables in-place renewal rollover. |

##### Validation Invariants for `tfEphemeral`:
1. **Mandatory Expiration**: If `tfEphemeral` is set and the `Expiration` field is omitted, the transaction returns `temMALFORMED`.
2. **Bounded TTL**: Let $T_{\text{close}}$ be the `close_time` of the parent validated ledger. The `Expiration` field MUST satisfy:
   $$T_{\text{close}} + 60 \le \text{Expiration} \le T_{\text{close}} + 3600$$
   If $\text{Expiration} < T_{\text{close}} + 60$ or $\text{Expiration} > T_{\text{close}} + 3600$, the transaction fails with `temINVALID_EXPIRATION`.
3. **Hex-Encoded URI Blob**: The `URI` field represents a variable-length byte string (`Blob`, up to 256 bytes) containing the hex-encoded enclave attestation commitment.

#### 2.2.2 In-Place Renewal Rollover Semantics
Under XLS-70, a `Credential` object's ledger index is derived as `sha512Half(Issuer, Subject, CredentialType)`. Submitting a second `CredentialCreate` with identical parameters fails with `tecDUPLICATE`.

Under `featureEphemeralCredentials`, if `tfEphemeral` is set:
1. **Rollover Detection**: If a `Credential` ledger entry with identical `(Issuer, Subject, CredentialType)` already exists on the ledger, AND the transaction `Account` matches the existing credential's `Issuer`:
   - The transaction is processed as an **In-Place Renewal Rollover** rather than a duplicate.
   - The `Expiration` must be greater than the existing `Expiration` (`New.Expiration > Existing.Expiration`). If not, returns `temINVALID_EXPIRATION`.
   - The `Expiration` is updated in-place to the new validated timestamp.
   - The `URI` (attestation quote digest) is updated to the new value.
2. **Subject Auto-Acceptance Retention**: If the subject account previously accepted the credential via `CredentialAccept` (setting `lsfAccepted`), the `lsfAccepted` flag is preserved across ephemeral rollovers. The subject is NOT required to submit an additional `CredentialAccept` transaction for periodic renewals, allowing autonomous AI agents to operate gaslessly without ongoing credential management fees.

#### 2.2.3 Deterministic Ledger Close & Cleanup Behavior
1. **Execution-Time Consensus Validation**: When an account interacts with an XLS-80 `PermissionedDomain` (or XLS-81 `PermissionedDEX`), the validator checks whether:
   $$\text{CurrentLedgerCloseTime} \le \text{Credential.Expiration}$$
   If $\text{CurrentLedgerCloseTime} > \text{Credential.Expiration}$, the credential is treated as expired and returns `tecNO_PERMISSION`.
2. **Permissionless Cleanup via `CredentialDelete`**: In accordance with XRPL's bounded $O(1)$ computation invariant per ledger close, expired credentials are not pruned automatically across unindexed ledgers. Instead, once $\text{CurrentLedgerCloseTime} > \text{Credential.Expiration}$, **any account on the network may submit a standard `CredentialDelete` transaction** to remove the expired ledger entry and return the owner reserve (0.2 XRP) to the issuer, preventing persistent ledger bloat without degrading consensus throughput.

---

## 3. Wire Representation & Reference Implementation

### 3.1 Transaction Wire Format Example
In the XRP Ledger binary protocol and JSON RPC, `Blob` fields (including `CredentialType` and `URI`) are hex-encoded strings:

```json
{
  "TransactionType": "CredentialCreate",
  "Account": "rAttestedIssuerXenclave1111111111111",
  "Subject": "rAutonomousAgent402xxxxxxxxxxxxxxx",
  "CredentialType": "61747465737465645f6167656e74",
  "Flags": 65536,
  "Expiration": 789123456,
  "URI": "783430323A6174746573743A76313A7464783A38616362653439",
  "Fee": "12",
  "Sequence": 42
}
```

*Note: `CredentialType` decodes to `"attested_agent"`; `URI` decodes to `"x402:attest:v1:tdx:8acbe49"`; `Flags: 65536` corresponds to `0x00010000` (`tfEphemeral`).*

### 3.2 Reference Implementation (`xrpl.js`)

```typescript
import { Client, Wallet, CredentialCreate } from "xrpl";

export interface EphemeralCredentialConfig {
  issuerWallet: Wallet;
  agentAddress: string;
  ttlSeconds: number; // Must be bounded between 60 and 3600 seconds; e.g. 300 (5 minutes)
  attestationUri: string; // Enclave attestation receipt URI
}

export async function issueEphemeralCredential(
  client: Client,
  config: EphemeralCredentialConfig
): Promise<string> {
  if (config.ttlSeconds < 60 || config.ttlSeconds > 3600) {
    throw new Error("Ephemeral TTL must be bounded between 60 and 3600 seconds.");
  }

  // Derive expiration from the authoritative validated ledger close time
  const ledgerResponse = await client.request({
    command: "ledger",
    ledger_index: "validated"
  });
  const validatedCloseTime = ledgerResponse.result.ledger.close_time;
  const expiration = validatedCloseTime + config.ttlSeconds;

  const tx: CredentialCreate = {
    TransactionType: "CredentialCreate",
    Account: config.issuerWallet.classicAddress,
    Subject: config.agentAddress,
    CredentialType: Buffer.from("attested_agent", "utf8").toString("hex").toUpperCase(),
    Expiration: expiration,
    URI: Buffer.from(config.attestationUri, "utf8").toString("hex").toUpperCase(),
    Flags: 0x00010000 // tfEphemeral
  };

  const prepared = await client.autofill(tx);
  const signed = config.issuerWallet.sign(prepared);
  const result = await client.submitAndWait(signed.tx_blob);

  return result.result.hash;
}
```

---

## 4. Hardware Attestation Trust Model

1. **Enclave Key Isolation**: The credential issuer's private key (`rAttestedIssuer...`) is generated and held exclusively inside silicon-encrypted enclave memory (Intel TDX RTMR / AMD SEV-SNP VMPCK / AWS Nitro Enclaves). Neither host hypervisors nor cloud infrastructure operators can extract the signing key.
2. **Domain Trust Configuration**: In XLS-80 `PermissionedDomain` configuration, domain operators authorize specific issuer addresses. During domain onboarding, the issuer proves enclave custody by supplying an RFC 8785 canonical attestation quote linked to its XRPL account public key.
3. **URI Attestation Digest**: Each ephemeral issuance embeds an attestation reference (`x402:attest:v1:<enclave_type>:<hash>`) in the `URI` Blob, allowing third-party verifiers to validate runtime execution proofs against public hardware manufacturer root keys (Intel PCS / AMD ASK).

---

## 5. Security & Invariant Analysis

1. **Deterministic Bounded Ejection**: Halting renewal guarantees that within $\le \text{TTL}$ seconds (nominally 300s), the credential becomes consensus-invalid across all UNL validators with zero front-running risk.
2. **Immunity to Mempool Censorship**: Because revocation occurs via consensus time progression rather than an explicit transaction, attackers cannot delay revocation through fee escalation or network congestion.
3. **Reserve Integrity**: Permissionless `CredentialDelete` after expiration ensures that inactive ephemeral credentials can be pruned by any participant, unlocking owner reserves and preventing unbounded ledger state growth.

---

## 6. Backward Compatibility
Fully gated by the `featureEphemeralCredentials` amendment. Pre-activation servers continue standard XLS-70 and XLS-80 operation. Existing static credentials function without modification.
