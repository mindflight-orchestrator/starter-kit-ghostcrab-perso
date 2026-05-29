#!/usr/bin/env node
import fs from 'node:fs';
import { parseArgs, readJson, reportAndExit, usage, writeJson } from './lib/import-utils.mjs';

const args = parseArgs(process.argv);

if (args.help) {
  usage(`
Usage:
  node scripts/audit_import_pipeline.mjs --manifest templates/import_manifest.yaml --profile-report output/source_profile.report.json --mapping-report output/mapping.validation.json --transform-report output/transform.report.json --graph-report output/graph.report.json --output output/audit.report.json

Options:
  --manifest          Import manifest path, YAML or JSON. Existence is checked only.
  --profile-report    JSON report from profile_source.mjs.
  --profile-validation-report JSON report from validate_source_profile.mjs.
  --model-report      JSON report from export_model_contract.mjs.
  --mapping-report    JSON report from validate_mapping_contract.mjs.
  --transform-report  JSON report from transform_source_to_jsonb.mjs.
  --pending-report    JSON report from write_pending_files.mjs.
  --facet-report      JSON report from import_facets.mjs.
  --graph-report      JSON report from materialize_graph_from_edges.mjs.
  --graph-contract-report JSON report from validate_graph_contract.mjs.
  --consumer-report   Optional consumer validation report.
  --output            Audit report path. If omitted, prints JSON to stdout.
`);
  process.exit(0);
}

const reportInputs = [
  ['profile', args['profile-report']],
  ['profile_validation', args['profile-validation-report']],
  ['model', args['model-report']],
  ['mapping', args['mapping-report']],
  ['transform', args['transform-report']],
  ['pending', args['pending-report']],
  ['facets', args['facet-report']],
  ['graph', args['graph-report']],
  ['graph_contract', args['graph-contract-report']],
  ['consumer', args['consumer-report']],
].filter(([, file]) => file);

const missing = [];
const reports = {};

if (args.manifest && !fs.existsSync(args.manifest)) {
  missing.push({ code: 'missing_manifest', file: args.manifest });
}

for (const [name, file] of reportInputs) {
  if (!fs.existsSync(file)) {
    missing.push({ code: 'missing_report', name, file });
    continue;
  }
  reports[name] = readJson(file);
}

const failedReports = Object.entries(reports)
  .filter(([, report]) => report.ok === false)
  .map(([name, report]) => ({ name, errors: report.errors ?? report.pending_review ?? report.unresolved_edges ?? [] }));

const audit = {
  ok: missing.length === 0 && failedReports.length === 0,
  checked_at: new Date().toISOString(),
  manifest: args.manifest ?? null,
  missing,
  failed_reports: failedReports,
  reports,
};

if (args['manifest-json-output']) {
  writeJson(args['manifest-json-output'], audit);
}

reportAndExit(audit, args.output);
