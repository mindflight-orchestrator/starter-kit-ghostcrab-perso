#!/usr/bin/env node
import fs from 'node:fs';
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
  node scripts/write_pending_files.mjs --transform-report output/transform.report.json --pending-review output/pending_review.json --pending-ddl output/pending_ddl.json

Options:
  --transform-report  Report from transform_source_to_jsonb.mjs.
  --graph-report      Optional graph report to include unresolved edges.
  --pending-review    Output pending_review.json.
  --pending-ddl       Output pending_ddl.json.
  --append            Append to existing pending files.
  --output            Summary report path. If omitted, prints JSON to stdout.
`);
  process.exit(0);
}

requireArgs(args, ['pending-review', 'pending-ddl']);

const ddlCodes = new Set(['needs_model_extension', 'unknown_entity_type', 'missing_schema', 'unknown_node_type']);
const pendingReview = args.append ? readArrayIfExists(args['pending-review']) : [];
const pendingDdl = args.append ? readArrayIfExists(args['pending-ddl']) : [];

for (const item of collectItems(args)) {
  const normalized = {
    code: item.code ?? 'pending_review',
    severity: item.severity ?? 'review',
    source: item.source ?? 'import_pipeline',
    item,
  };
  if (ddlCodes.has(normalized.code)) {
    pendingDdl.push(normalized);
  } else {
    pendingReview.push(normalized);
  }
}

writeJson(args['pending-review'], pendingReview);
writeJson(args['pending-ddl'], pendingDdl);

reportAndExit(
  {
    ok: true,
    counts: {
      pending_review: pendingReview.length,
      pending_ddl: pendingDdl.length,
    },
    outputs: {
      pending_review: args['pending-review'],
      pending_ddl: args['pending-ddl'],
    },
  },
  args.output,
);

function collectItems(cliArgs) {
  const items = [];
  if (cliArgs['transform-report']) {
    const report = readJson(cliArgs['transform-report']);
    items.push(...(report.pending_review ?? []).map((item) => ({ source: 'transform', ...item })));
    items.push(...(report.errors ?? []).map((item) => ({ source: 'transform', ...item })));
  }
  if (cliArgs['graph-report']) {
    const report = readJson(cliArgs['graph-report']);
    items.push(...(report.unresolved_edges ?? []).map((item) => ({ code: 'unresolved_reference', source: 'graph', ...item })));
    items.push(...(report.errors ?? []).map((item) => ({ source: 'graph', ...item })));
  }
  return items;
}

function readArrayIfExists(filePath) {
  if (!fs.existsSync(filePath)) return [];
  const value = readJson(filePath);
  return Array.isArray(value) ? value : [];
}
