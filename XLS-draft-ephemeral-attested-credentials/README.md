<pre>
  title: Ephemeral Attested Credentials & Enclave-Gated Domains (E-APD)
  description: Hardware-attested short-TTL credentials and zero-latency consensus-enforced venue ejection for autonomous agents on XRPL
  author: Walter Hawkins <contact@correntelabs.com>, Corrente Applied Cryptography Group
  status: Draft
  category: Amendment
  requires: [XLS-70](../XLS-0070-credentials/README.md), [XLS-80](../XLS-0080-permissioned-domains/README.md)
  created: 2026-10-06
</pre>

# XLS-draft: Ephemeral Attested Credentials & Enclave-Gated Domains (E-APD)

## Abstract
This standard defines an architecture for **Ephemeral Attested Permissioned Domains (E-APD)** on the XRP Ledger. By combining hardware-isolated Trusted Execution Environments (TEEs) with short Time-To-Live (TTL) cryptographic credentials (300 to 900 seconds), E-APD enables real-time compliance enforcement, automated mandate auditing, and **zero-latency consensus-enforced venue ejection** for autonomous AI agents, algorithmic market makers, and institutional participants on XRPL.

## 1. Motivation

The introduction of [XLS-70 (Credentials)](../XLS-0070-credentials/README.md) and [XLS-80 (Permissioned Domains)](../XLS-0080-permissioned-domains/README.md) on the XRP Ledger establishes native primitives for institutional compliance and permissioned decentralized exchange (DEX) trading. However, the existing revocation lifecycle suffers from critical structural vulnerabilities when applied to high-frequency autonomous AI agents:

1. **The Revocation Latency Gap**: Conventional credentials are static and long-lived (issued for weeks, months, or years). If an autonomous trading agent experiences an invariant violation, prompt injection exploit, or runaway liquidity drain, the compliance issuer must broadcast an on-chain `CredentialDelete` transaction.
2. **The Front-Running Attack Vector**: An adversarial or compromised agent monitoring the XRPL mempool can detect an incoming `CredentialDelete` transaction and immediately front-run it with higher fee escalations, executing unauthorized swaps or draining liquidity pools before revocation finality.
3. **Mempool & Network Congestion Risk**: During periods of high network activity or fee spikes, revocation transactions can be delayed across multiple ledgers.

### The Solution: Inverting the Revocation Paradigm
Instead of issuing long-lived credentials and revoking them reactively, **E-APD inverts the architecture**:
* Credentials are issued with an **ultra-short TTL** (e.g., 300 seconds / 5 minutes).
* An off-chain hardware enclave (Intel TDX / AMD SEV-SNP) continuously monitors agent invariants, trade telemetry, and budget mandates.
* As long as all invariants hold, the enclave automatically issues a cryptographic renewal.
* If an agent violates policy, **the enclave simply halts renewal**.
* On the very next ledger close (~3.5 seconds), the credential expires naturally at L1 consensus, and any subsequent transaction by the agent immediately fails with `tecNO_PERMISSION`.

Zero on-chain revocation transactions are needed. Front-running is mathematically impossible.

---

## 2. Technical Specification

### 2.1 Transaction Types & Modifications

#### 2.1.1 `CredentialCreate` with Ephemeral Flag
Extends XLS-70 `CredentialCreate` with an optional `Flags` field:
* `tfEphemeral`: Indicates that this credential requires deterministic expiration and is issued by an attested hardware issuer.

```json
{
  "TransactionType": "CredentialCreate",
  "Account": "rAttestedIssuerXenclave1111111111111",
  "Subject": "rAutonomousAgent402xxxxxxxxxxxxxxx",
  "CredentialType": "61757468656e746963617465645f6167656e74",
  "Flags": 65536,
  "Expiration": 789123456,
  "URI": "https://api.ashlar.blue/attestation/quote/tdx-v4-01",
  "Fee": "12",
  "Sequence": 42
}
```

#### 2.1.2 Automatic L1 Consensus Expiration
When validating an account's eligibility to submit transactions within an XLS-80 `PermissionedDomain`:
1. The engine checks if `CurrentLedgerTime > Credential.Expiration`.
2. If expired, the transaction is rejected immediately with `tecNO_PERMISSION`.
3. The expired ledger object is lazily pruned or garbage-collected during subsequent ledger closes without charging additional reserves.

---

## 3. Reference Implementation via `xrpl.js`

```typescript
import { Client, Wallet, CredentialCreate } from "xrpl";

export interface EphemeralCredentialConfig {
  issuerWallet: Wallet;
  agentAddress: string;
  ttlSeconds: number; // e.g. 300 (5 minutes)
  attestationUri: string;
}

export async function issueEphemeralCredential(
  client: Client,
  config: EphemeralCredentialConfig
): Promise<string> {
  const currentLedger = await client.getLedgerIndex();
  const ledgerCloseTime = Math.floor(Date.now() / 1000) - 946684800; // Ripple Epoch offset
  const expiration = ledgerCloseTime + config.ttlSeconds;

  const tx: CredentialCreate = {
    TransactionType: "CredentialCreate",
    Account: config.issuerWallet.classicAddress,
    Subject: config.agentAddress,
    CredentialType: Buffer.from("attested_agent").toString("hex").toUpperCase(),
    Expiration: expiration,
    URI: Buffer.from(config.attestationUri).toString("hex").toUpperCase(),
    Flags: 0x00010000 // tfEphemeral
  };

  const prepared = await client.autofill(tx);
  const signed = config.issuerWallet.sign(prepared);
  const result = await client.submitAndWait(signed.tx_blob);

  return result.result.hash;
}
```

---

## 4. Security & Invariant Analysis

1. **Physical Silicon Root of Trust**:
   The private signing key of the credential issuer resides exclusively in memory encrypted by hardware silicon (Intel TDX / AMD SEV-SNP). Cold-boot attacks, physical bus sniffing, and host hypervisor inspection cannot extract the key.
2. **Deterministic Ejection**:
   Because ledger close time is enforced by consensus across all UNL validators, an expired credential cannot be accepted by any validator. Ejection is non-bypassable.
3. **Reserve Efficiency**:
   Ephemeral credentials do not permanently consume account owner reserves. Once expired, the reserve is unlocked upon automatic pruning.

---

## 5. Backward Compatibility
Fully backwards compatible with standard XLS-70 and XLS-80 deployments. Clients not participating in Ephemeral Domains continue to use standard static credentials without modification.
