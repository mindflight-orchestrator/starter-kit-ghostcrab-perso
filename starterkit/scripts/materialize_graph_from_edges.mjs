#!/usr/bin/env node
import { parseArgs, readJsonl, reportAndExit, requireArgs, usage, writeJsonl } from './lib/import-utils.mjs';

const args = parseArgs(process.argv);

if (args.help) {
  usage(`
Usage:
  node scripts/materialize_graph_from_edges.mjs --records output/normalized_records.jsonl --edges output/normalized_edges.jsonl --workspace my-workspace --output-nodes output/graph_nodes.jsonl --output-edges output/graph_edges.jsonl

Options:
  --records       Normalized records JSONL.
  --edges         Normalized edges JSONL.
  --workspace     Target workspace id.
  --output-nodes  Graph node staging JSONL.
  --output-edges  Graph edge staging JSONL.
  --report        Report path. If omitted, prints JSON to stdout.
`);
  process.exit(0);
}

requireArgs(args, ['records', 'edges', 'workspace', 'output-nodes', 'output-edges']);

const records = readJsonl(args.records);
const edges = readJsonl(args.edges);
const nodeById = new Map();

for (const record of records) {
  const entity = record.entities?.[0];
  const recordId = record.facets?.record_id ?? entity?.id ?? record.source_ref;
  nodeById.set(recordId, {
    workspace_id: args.workspace,
    record_id: recordId,
    schema_id: record.schema_id,
    node_type: entity?.node_type ?? record.schema_id.split(':').at(-1),
    label: entity?.label ?? record.content,
    metadata: {
      source_ref: record.source_ref,
      facets: record.facets ?? {},
    },
  });
}

const unresolved = [];
const stagedEdges = [];

for (const edge of edges) {
  if (!nodeById.has(edge.source) || !nodeById.has(edge.target)) {
    unresolved.push(edge);
    continue;
  }
  stagedEdges.push({
    workspace_id: args.workspace,
    source_record_id: edge.source,
    target_record_id: edge.target,
    edge_label: edge.label,
    confidence: edge.confidence ?? 1,
    metadata: edge.metadata ?? {},
  });
}

writeJsonl(args['output-nodes'], [...nodeById.values()]);
writeJsonl(args['output-edges'], stagedEdges);

reportAndExit(
  {
    ok: unresolved.length === 0,
    counts: {
      graph_nodes: nodeById.size,
      source_edges: edges.length,
      graph_edges: stagedEdges.length,
      unresolved_edges: unresolved.length,
    },
    unresolved_edges: unresolved,
    outputs: {
      nodes: args['output-nodes'],
      edges: args['output-edges'],
    },
  },
  args.report,
);
