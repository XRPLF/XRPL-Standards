#!/usr/bin/env node

const fs = require('node:fs');
const path = require('node:path');

const root = path.resolve(__dirname, '..', '..');
const catalogPath = path.join(root, 'xunia', 'ontology', 'catalog.json');
const catalog = JSON.parse(fs.readFileSync(catalogPath, 'utf8'));
const errors = [];

const requireValue = (condition, code) => {
  if (!condition) errors.push(code);
};

const unique = (values) => new Set(values).size === values.length;

requireValue(catalog.id === 'XUNIA-XRPL-STANDARDS-ONTOLOGY', 'ONTOLOGY_ID_INVALID');
requireValue(/^\d+\.\d+\.\d+$/.test(catalog.version), 'ONTOLOGY_VERSION_INVALID');
requireValue(catalog.generatedFrom.xuniaRepository === 'sonoxo/XRPL-StandardsXUNIA-', 'XUNIA_REPOSITORY_INVALID');
requireValue(catalog.generatedFrom.authoritativeUpstream === 'XRPLF/XRPL-Standards', 'UPSTREAM_INVALID');
requireValue(catalog.generatedFrom.authorityClaim === false, 'UPSTREAM_AUTHORITY_MUST_NOT_BE_CLAIMED');

requireValue(unique(catalog.objectTypes), 'DUPLICATE_OBJECT_TYPE');
requireValue(unique(catalog.linkTypes), 'DUPLICATE_LINK_TYPE');
requireValue(unique(catalog.statuses), 'DUPLICATE_STATUS');
requireValue(unique(catalog.categories), 'DUPLICATE_CATEGORY');
requireValue(unique(catalog.repositories.map((item) => item.id)), 'DUPLICATE_REPOSITORY_ID');
requireValue(unique(catalog.pathways.map((item) => item.id)), 'DUPLICATE_PATHWAY_ID');

const requiredRepositories = [
  'sonoxo/XRPL-StandardsXUNIA-',
  'sonoxo/xrpl.jsXUNIA',
  'sonoxo/rippledXUNIA',
  'sonoxo/xuniadao',
];

for (const repository of requiredRepositories) {
  requireValue(catalog.repositories.some((item) => item.repository === repository), `REPOSITORY_REQUIRED:${repository}`);
}

for (const pathway of catalog.pathways) {
  requireValue(pathway.actions.length > 0, `PATHWAY_ACTION_REQUIRED:${pathway.id}`);
  if (pathway.mutation) {
    requireValue(pathway.humanApprovalRequired, `MUTATION_APPROVAL_REQUIRED:${pathway.id}`);
    requireValue(pathway.actions.includes('REQUEST_HUMAN_APPROVAL'), `APPROVAL_ACTION_REQUIRED:${pathway.id}`);
    requireValue(pathway.actions.includes('SIGN_WITH_EXTERNAL_WALLET'), `EXTERNAL_SIGNER_REQUIRED:${pathway.id}`);
  }
}

const controls = catalog.controls;
requireValue(controls.provenanceRequired, 'PROVENANCE_REQUIRED');
requireValue(controls.officialStatusReadFromDocumentPreamble, 'DOCUMENT_STATUS_MUST_BE_AUTHORITATIVE');
requireValue(controls.draftIsNotFinal, 'DRAFT_FINAL_BOUNDARY_REQUIRED');
requireValue(controls.implementationEvidenceRequired, 'IMPLEMENTATION_EVIDENCE_REQUIRED');
requireValue(controls.humanApprovalRequiredForMutation, 'HUMAN_APPROVAL_CONTROL_REQUIRED');
requireValue(controls.externalSignerRequired, 'EXTERNAL_SIGNER_CONTROL_REQUIRED');
requireValue(controls.walletSeedStorage === false, 'WALLET_SEED_STORAGE_BLOCK_REQUIRED');
requireValue(controls.privateKeyStorage === false, 'PRIVATE_KEY_STORAGE_BLOCK_REQUIRED');
requireValue(controls.automaticFundMovement === false, 'AUTOMATIC_FUND_MOVEMENT_BLOCK_REQUIRED');
requireValue(controls.automaticTokenIssuance === false, 'AUTOMATIC_TOKEN_ISSUANCE_BLOCK_REQUIRED');
requireValue(controls.upstreamOwnershipPreserved, 'UPSTREAM_OWNERSHIP_REQUIRED');
requireValue(controls.upstreamAffiliationClaim === false, 'UPSTREAM_AFFILIATION_MUST_NOT_BE_CLAIMED');

if (errors.length > 0) {
  console.error(JSON.stringify({ valid: false, errors }, null, 2));
  process.exit(1);
}

console.log(JSON.stringify({
  valid: true,
  ontology: catalog.id,
  version: catalog.version,
  repositories: catalog.repositories.length,
  pathways: catalog.pathways.length,
  controls: 'PASS',
}, null, 2));
