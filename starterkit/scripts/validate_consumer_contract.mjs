#!/usr/bin/env node
import {
  parseArgs,
  readJsonIfPossible,
  readJsonl,
  readText,
  reportAndExit,
  requireArgs,
  usage,
} from './lib/import-utils.mjs';

const args = parseArgs(process.argv);

if (args.help) {
  usage(`
Usage:
  node scripts/validate_consumer_contract.mjs --contract templates/consumer_contract.yaml --base-url http://localhost:5174 --graph-nodes output/graph_nodes.jsonl --graph-edges output/graph_edges.jsonl --output output/consumer.report.json

Options:
  --contract     Consumer contract YAML or JSON.
  --base-url     Optional base URL for HTTP checks.
  --graph-nodes  Optional graph node staging JSONL.
  --graph-edges  Optional graph edge staging JSONL.
  --output       Report path. If omitted, prints JSON to stdout.
`);
  process.exit(0);
}

requireArgs(args, ['contract']);

const text = readText(args.contract);
const json = readJsonIfPossible(args.contract);
const errors = [];
const warnings = [];
const checks = [];

const nativeGraphRequired = json
  ? JSON.stringify(json).includes('"native_graph":true') || JSON.stringify(json).includes('"native_graph": true')
  : /native_graph:\s*true/.test(text);

if (nativeGraphRequired) {
  if (!args['graph-nodes'] || !args['graph-edges']) {
    errors.push({ code: 'native_graph_required_without_graph_staging' });
  } else {
    const nodes = readJsonl(args['graph-nodes']);
    const edges = readJsonl(args['graph-edges']);
    checks.push({ id: 'native-graph-node-count', ok: nodes.length > 0, count: nodes.length });
    checks.push({ id: 'native-graph-edge-count', ok: edges.length > 0, count: edges.length });
    if (nodes.length === 0) errors.push({ code: 'graph_nodes_empty' });
    if (edges.length === 0) errors.push({ code: 'graph_edges_empty' });
  }
}

const paths = extractHttpPaths(text, json);
if (paths.length && !args['base-url']) {
  warnings.push({ code: 'http_checks_skipped_no_base_url', count: paths.length });
}

if (args['base-url']) {
  for (const checkPath of paths) {
    const url = new URL(checkPath, args['base-url']).toString();
    try {
      const response = await fetch(url);
      const bodyText = await response.text();
      let body = null;
      try {
        body = JSON.parse(bodyText);
      } catch {
        body = bodyText.slice(0, 200);
      }
      const ok = response.ok && hasNonEmptyPayload(body);
      checks.push({ id: checkPath, type: 'http', url, status: response.status, ok });
      if (!ok) errors.push({ code: 'http_check_failed', path: checkPath, status: response.status });
    } catch (error) {
      checks.push({ id: checkPath, type: 'http', url, ok: false, error: error.message });
      errors.push({ code: 'http_check_error', path: checkPath, message: error.message });
    }
  }
}

reportAndExit(
  {
    ok: errors.length === 0,
    contract: args.contract,
    checks,
    errors,
    warnings,
  },
  args.output,
);

function extractHttpPaths(contractText, contractJson) {
  if (contractJson) {
    const paths = [];
    collectPaths(contractJson, paths);
    return paths;
  }
  return [...contractText.matchAll(/path:\s*"([^"]+)"/g)].map((match) => match[1]);
}

function collectPaths(value, paths) {
  if (Array.isArray(value)) {
    for (const item of value) collectPaths(item, paths);
    return;
  }
  if (value && typeof value === 'object') {
    if (typeof value.path === 'string') paths.push(value.path);
    for (const item of Object.values(value)) collectPaths(item, paths);
  }
}

function hasNonEmptyPayload(body) {
  if (Array.isArray(body)) return body.length > 0;
  if (body && typeof body === 'object') {
    if ('nodeCount' in body || 'edgeCount' in body) return Number(body.nodeCount ?? 0) > 0 || Number(body.edgeCount ?? 0) > 0;
    if ('nodes' in body || 'edges' in body) return (body.nodes?.length ?? 0) > 0 || (body.edges?.length ?? 0) > 0;
    if ('entityCount' in body) return Number(body.entityCount) > 0;
    return Object.keys(body).length > 0;
  }
  return Boolean(body);
}
