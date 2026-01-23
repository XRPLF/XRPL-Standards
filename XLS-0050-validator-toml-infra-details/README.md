<pre>
  xls: 50
  title: Aiming for a healthy distribution of (validator) infrastructure
  description: Best practices for the geographical & provider distribution of validators
  author: Wietse Wind (@WietseWind)
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/145
  created: 2023-11-14
  status: Final
  category: Ecosystem
</pre>

# Abstract

The network is at risk of centralised consensus failure when too many validators (especially dUNL validators) are running on the same cloud provider/network. While negative [UNL helps](.), the network is still at the risk of a halt when a large infra/cloud provider has an outage.

This proposal introduces best practices for the geographical & provider distribution of validators, something those composing dUNL contents & those adding trusted validators to their `rippled` & `xahaud` config manually.

ℹ️ Note: this proposal is only focussing at **validators**, as their (instant lack of) availability could harm network forward progress. All arguments (motivation) apply to RPC nodes, hubs, as well, but e.g. RPC nodes could benefit from live HTTP failover availability & them being offline doesn't directly harm the network's forward progress.

# Motivation

With high performing cloud servers (VPS, dedicated) are more and more common, and with cloud providers often beating convenience and price of self hosting / colocation, several validator operators are running their validators at the same cloud providers. Independently executed network crawls show large clusters of validators at only a handful cloud providers. Most common providers are:

- Google (Google Cloud Platform)
- Amazon AWS
- DigitalOcean
- Hetzner

When looking at traceroutes, things look even worse when taking the datacenter/POP of these cloud providers into account, as cloud providers, through availability and pricing, route customers to specific preferred datacenter locations (and thus: routes).

As a result of a significant number of validators running on cloud infra at a small number of cloud providers, an outage at one cloud provider (datacenter, power, infra, routing, BGP, ...) can potentially drop the network below the consensus threshold. With Negative UNL taking 256 ledgers to kick in, this is unwanted.

# Proposal

Things to take into account picking a suitable provider (cloud, infrastructure):

- Significant distribution across ASN (networks) as per validator IP address
- Significant distribution across physical location (datacenters, POPs)

### 1. Validator operator resource location selection

Validator operators (even when not on the UNL, if they prefer to be on dUNL / in each other's validator lists) should always:

- Take the above into account
- Preferably prevent running their validator on a cloud provider
- If running on a cloud provider: preferably pick the least used cloud provider & cloud provider datacenter location (POP) by other validator operators

### 2. TOML contents

A typical `validator` section in the `xrp-ledger.toml` and `xahau.toml` preferably contains a `server_country` property:

```toml
[[VALIDATORS]]
...
server_country = "??"
```

The following properties **must** be added:

- `network_asn` (integer) containing the ASN (autonomous system number) of the IP address the validator uses to connect out (see Appendix A & Appendix B)

#### ⚖️ **CONSIDERATION: publishing the ASN could be considered an attack vector, as it would expose the provider to DDoS to take down connectivity to certain validators. However, if the network is sufficiently decentralised/distributed from a infrastructure point of view, taking down one or to routes wouldn't harm the network.**

The following properties **should** be added:

- `server_location` (string) containing a written explanation of provider provided location details (see Appendix A)
- `server_cloud` (boolean) if the server is running at a cloud provider (e.g. VPS / cloud dedicated: **a server you will never physically see, won't know how to find is a cloud server.**, so VPS / dedicated rented machine: cloud = true. Your own bare metal, colocated: cloud = false)

#### ⚠️ **NEVER PUBLISH YOUR VALIDATOR IP ADDRESS IN YOUR TOML!**

### 3. UNL publishers & validator operators

UNL publishers & validator operators should start to obtain ASN & geographical location from trusted validator operators, and take them into account when composing the UNL list contents.

UNL publishers should not add validators to the UNL without the above TOML properties.

# Call for immediate action

### Validator operators

- Update your TOML with the above information
- Check your manual validator list additions for the above properties

### UNL publishers

- Check the validators on the published UNL for the above TOML properties
- Call for adding the above TOML properties
- Communicate a "Grace Period" for those not disclosing this info
- (If communication is possible) work with operators of reliable validators if they are running on cloud/infra hotspots, ask them to migrate
- (If communication is not possible) over time, replace validator operators on cloud/infra hotspots, for reliable validators providing more provider & geographical redundancy.

# Appendix A - sample TOML values

### Example: Cloud: VPS / Rented dedicated

```toml
server_country = "NL"
server_location = "DigitalOcean AMS3 (Amsterdam, NL)"
server_cloud = true
network_asn = 14061
```

### Example: Non-Cloud: Self hosted or own hardware, colocated

```toml
server_country = "NL"
server_location = "Private datacenter (Utrecht area, NL)"
server_cloud = false
network_asn = 16089
```

# Appendix B - obtaining the ASN (autonomous system number)

To obtain the ASN for your IP address (usually your provider or provider's upstream provider), you will need the IP address used by your validator to connect out to others. Providing there are no proxy settings & the machine has native IP connectivity to the outside world, you can find/confirm your outgoing IP address by executing (bash):

```bash
curl --silent https://myip.wtf/text
```

You can find the ASN for the IP range this IP is allocated from using:

```bash
whois -h whois.cymru.com {ip}
```

A one-line command to obtain IP and obtain ASN:

```bash
whois -h whois.cymru.com $(curl --silent https://myip.wtf/text)
```

Sample output:

```
AS      | IP               | AS Name
14061   | 31.239.49.82     | MyBackYardServerRack LTD USA
```

In this case `14061` is the integer value for your `network_asn` property in your TOML file.

#### ⚠️ **Warning! The AS name may contain a location identifier. This usually refers to the original place the IP range was allocated / the headquarters of the owner of the IP range. This is in NO WAY an indication of the physical location of your machine.**
