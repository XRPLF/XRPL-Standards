# XRP Ledger Standards

XRP Ledger Standards (XLSs) describe standards and specifications relating to the XRP Ledger ecosystem that help achieve the following goals:

- Ensure interoperability and compatibility between XRP Ledger core protocol, ecosystem applications, tools, and platforms.
- Maintain a continued, excellent user experience around every application or system.
- Drive alignment and agreement in the XRPL community (i.e., developers, users, operators, etc).

# [Contributing](./CONTRIBUTING.md)

The exact process for organizing and contributing to this repository is defined in [CONTRIBUTING.md](./CONTRIBUTING.md). If you would like to contribute, please read more there.

## XUNIA ontology integration

Command: **`/glass xrpl standards`**

This XUNIA-maintained repository includes a machine-readable standards ontology for connecting XLS evidence to token, wallet, client, node, approval, and audit pathways.

- [Ontology guide](xunia/ontology/README.md)
- [Machine catalog](xunia/ontology/catalog.json)
- [JSON Schema](xunia/ontology/schema.json)
- [Validator](scripts/validate-xunia-ontology.cjs)

The ontology preserves `XRPLF/XRPL-Standards` as the authoritative upstream. It does not change the official category or lifecycle status of any XLS, and it does not claim XRPLF or Ripple endorsement.

