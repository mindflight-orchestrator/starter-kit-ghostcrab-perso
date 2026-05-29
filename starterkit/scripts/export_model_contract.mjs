#!/usr/bin/env node
import {
  parseArgs,
  readJson,
  reportAndExit,
  requireArgs,
  usage,
  writeJson,
} from './lib/import-utils.mjs';

const args = parseArgs(process.argv);

if (args.help) {
  usage(`
Usage:
  node scripts/export_model_contract.mjs --workspace my-workspace --output-plan output/model_export_call.json --output output/model_contract.report.json

Options:
  --workspace     Target workspace id.
  --depth         tables_only | tables_and_columns | full (default: full).
  --output-plan   Writes the host-specific MCP call plan.
  --exported      Optional exported model JSON to validate.
  --output        Report path. If omitted, prints JSON to stdout.
`);
  process.exit(0);
}

requireArgs(args, ['workspace']);

const depth = args.depth ?? 'full';
const plan = {
  tool: 'ghostcrab_workspace_export_model',
  arguments: {
    workspace_id: args.workspace,
    depth,
  },
  note: 'Run this through the active MCP host, then pass the JSON result back with --exported.',
};

if (args['output-plan']) {
  writeJson(args['output-plan'], plan);
}

const errors = [];
const warnings = [];
let exportedSummary = null;

if (args.exported) {
  const exported = readJson(args.exported);
  const text = JSON.stringify(exported);
  const workspaceFound = text.includes(args.workspace);
  const schemaIds = [...text.matchAll(/"schema_id"\s*:\s*"([^"]+)"/g)].map((match) => match[1]);
  const edgeLabels = [...new Set([...text.matchAll(/"edge_label"\s*:\s*"([^"]+)"|"label"\s*:\s*"([A-Z][A-Z0-9_:-]+)"/g)].map((match) => match[1] ?? match[2]).filter(Boolean))];
  const projections = [...text.matchAll(/"scope"\s*:\s*"([^"]+)"/g)].map((match) => match[1]);

  if (!workspaceFound) errors.push({ code: 'workspace_not_found_in_export', workspace_id: args.workspace });
  if (!schemaIds.length && !text.includes('table')) warnings.push({ code: 'no_schema_ids_detected' });
  if (!edgeLabels.length) warnings.push({ code: 'no_edge_labels_detected' });

  exportedSummary = {
    workspace_found: workspaceFound,
    schema_id_count: new Set(schemaIds).size,
    edge_label_count: edgeLabels.length,
    projection_scope_count: new Set(projections).size,
  };
} else {
  warnings.push({ code: 'plan_only', message: 'No exported model was supplied; only the MCP call plan was generated.' });
}

reportAndExit(
  {
    ok: errors.length === 0,
    mode: args.exported ? 'validated_export' : 'plan_only',
    plan,
    exported_summary: exportedSummary,
    errors,
    warnings,
  },
  args.output,
);
