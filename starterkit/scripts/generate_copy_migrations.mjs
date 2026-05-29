#!/usr/bin/env node
import path from 'node:path';
import {
  parseArgs,
  readJsonl,
  reportAndExit,
  requireArgs,
  usage,
  writeCsv,
} from './lib/import-utils.mjs';

const args = parseArgs(process.argv);

if (args.help) {
  usage(`
Usage:
  node scripts/generate_copy_migrations.mjs --workspace my-workspace --records output/normalized_records.jsonl --output-dir output/migrations

Options:
  --workspace     Target workspace id.
  --records       Normalized records JSONL.
  --graph-nodes   Optional graph node staging JSONL.
  --graph-edges   Optional graph edge staging JSONL.
  --output-dir    Directory for CSV files.
  --prefix        File prefix (default: migration).
  --created-at    Timestamp override (default: current ISO timestamp).
  --output        Report path. If omitted, prints JSON to stdout.
`);
  process.exit(0);
}

requireArgs(args, ['workspace', 'records', 'output-dir']);

const prefix = args.prefix ?? 'migration';
const createdAt = args['created-at'] ?? new Date().toISOString();
const records = readJsonl(args.records);
const outputs = {};

const facetsRows = records.map((record) => ({
  workspace_id: args.workspace,
  source_ref: record.source_ref,
  schema_id: record.schema_id,
  content: record.content,
  facets: JSON.stringify(record.facets ?? {}),
  created_at: createdAt,
}));

outputs.mfo_facets = path.join(args['output-dir'], `${prefix}_mfofacets.csv`);
writeCsv(outputs.mfo_facets, ['workspace_id', 'source_ref', 'schema_id', 'content', 'facets', 'created_at'], facetsRows);

let graphNodeCount = 0;
let graphEdgeCount = 0;

if (args['graph-nodes']) {
  const nodes = readJsonl(args['graph-nodes']);
  graphNodeCount = nodes.length;
  outputs.graph_entity = path.join(args['output-dir'], `${prefix}_graph_entity.csv`);
  writeCsv(
    outputs.graph_entity,
    ['workspace_id', 'type', 'name', 'metadata', 'confidence', 'created_at'],
    nodes.map((node) => ({
      workspace_id: args.workspace,
      type: node.node_type ?? node.type ?? 'entity',
      name: node.record_id ?? node.name,
      metadata: JSON.stringify(node.metadata ?? node),
      confidence: node.confidence ?? 1,
      created_at: createdAt,
    })),
  );
}

if (args['graph-edges']) {
  const edges = readJsonl(args['graph-edges']);
  graphEdgeCount = edges.length;
  outputs.graph_relation_staging = path.join(args['output-dir'], `${prefix}_graph_relation_staging.csv`);
  writeCsv(
    outputs.graph_relation_staging,
    ['workspace_id', 'type', 'source_record_id', 'target_record_id', 'confidence', 'metadata', 'created_at'],
    edges.map((edge) => ({
      workspace_id: args.workspace,
      type: edge.edge_label ?? edge.label ?? edge.type,
      source_record_id: edge.source_record_id ?? edge.source,
      target_record_id: edge.target_record_id ?? edge.target,
      confidence: edge.confidence ?? 1,
      metadata: JSON.stringify(edge.metadata ?? {}),
      created_at: createdAt,
    })),
  );
}

reportAndExit(
  {
    ok: true,
    counts: {
      mfo_facets: facetsRows.length,
      graph_entity: graphNodeCount,
      graph_relation_staging: graphEdgeCount,
    },
    outputs,
    note: 'graph_relation_staging must be resolved to graph.entity ids before COPY into graph.relation.',
  },
  args.output,
);
