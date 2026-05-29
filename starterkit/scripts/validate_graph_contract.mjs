#!/usr/bin/env node
import {
  parseArgs,
  readJson,
  readJsonl,
  readText,
  reportAndExit,
  requireArgs,
  unique,
  usage,
} from './lib/import-utils.mjs';

const args = parseArgs(process.argv);

if (args.help) {
  usage(`
Usage:
  node scripts/validate_graph_contract.mjs --nodes output/graph_nodes.jsonl --edges output/graph_edges.jsonl --allowed-labels works_for,owns --output output/graph_contract.report.json

Options:
  --nodes          Graph node staging JSONL.
  --edges          Graph edge staging JSONL.
  --model          Optional model contract JSON/YAML/text to infer labels from.
  --allowed-labels Comma-separated allowed edge labels.
  --edge-rules     Optional JSON file: [{ "label": "...", "source_node_types": [], "target_node_types": [] }].
  --output         Report path. If omitted, prints JSON to stdout.
`);
  process.exit(0);
}

requireArgs(args, ['nodes', 'edges']);

const nodes = readJsonl(args.nodes);
const edges = readJsonl(args.edges);
const nodeById = new Map(nodes.map((node) => [node.record_id ?? node.name, node]));
const errors = [];
const warnings = [];

const allowedLabels = new Set([
  ...parseList(args['allowed-labels']),
  ...extractLabelsFromModel(args.model),
]);

if (!allowedLabels.size) {
  warnings.push({ code: 'no_allowed_labels_supplied', message: 'Endpoint resolution will be checked, but labels are not constrained.' });
}

const rules = args['edge-rules'] ? readJson(args['edge-rules']) : [];

for (const edge of edges) {
  const sourceId = edge.source_record_id ?? edge.source;
  const targetId = edge.target_record_id ?? edge.target;
  const label = edge.edge_label ?? edge.label ?? edge.type;
  const sourceNode = nodeById.get(sourceId);
  const targetNode = nodeById.get(targetId);

  if (!sourceNode) errors.push({ code: 'missing_source_node', source: sourceId, edge });
  if (!targetNode) errors.push({ code: 'missing_target_node', target: targetId, edge });
  if (allowedLabels.size && !allowedLabels.has(label)) errors.push({ code: 'invalid_edge_label', label, edge });

  const rule = rules.find((candidate) => candidate.label === label);
  if (rule && sourceNode && targetNode) {
    const sourceType = sourceNode.node_type ?? sourceNode.type;
    const targetType = targetNode.node_type ?? targetNode.type;
    if (rule.source_node_types?.length && !rule.source_node_types.includes(sourceType)) {
      errors.push({ code: 'edge_source_type_mismatch', label, expected: rule.source_node_types, actual: sourceType, edge });
    }
    if (rule.target_node_types?.length && !rule.target_node_types.includes(targetType)) {
      errors.push({ code: 'edge_target_type_mismatch', label, expected: rule.target_node_types, actual: targetType, edge });
    }
  }
}

reportAndExit(
  {
    ok: errors.length === 0,
    counts: {
      nodes: nodes.length,
      edges: edges.length,
      allowed_labels: allowedLabels.size,
      labels_seen: unique(edges.map((edge) => edge.edge_label ?? edge.label ?? edge.type)).length,
    },
    errors,
    warnings,
  },
  args.output,
);

function parseList(value) {
  if (!value) return [];
  return String(value)
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean);
}

function extractLabelsFromModel(modelPath) {
  if (!modelPath) return [];
  const text = readText(modelPath);
  const labels = new Set();
  for (const match of text.matchAll(/edge_labels_allowed:\s*([\s\S]*?)(?:\n\S|$)/g)) {
    for (const label of match[1].matchAll(/-\s*"?([A-Za-z0-9_:-]+)"?/g)) labels.add(label[1]);
  }
  for (const match of text.matchAll(/"edge_label"\s*:\s*"([^"]+)"|"label"\s*:\s*"([A-Za-z0-9_:-]+)"/g)) {
    labels.add(match[1] ?? match[2]);
  }
  return [...labels];
}
