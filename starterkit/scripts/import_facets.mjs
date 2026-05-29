#!/usr/bin/env node
import { parseArgs, readJsonl, reportAndExit, requireArgs, usage, writeJsonl } from './lib/import-utils.mjs';

const args = parseArgs(process.argv);

if (args.help) {
  usage(`
Usage:
  node scripts/import_facets.mjs --records output/normalized_records.jsonl --workspace my-workspace --output output/mcp_upsert_calls.jsonl

Options:
  --records    Normalized records JSONL.
  --workspace  Target workspace id.
  --output     JSONL MCP call plan path.
  --write      Reserved for host-specific MCP execution. Default is dry-run.
  --report     Report path. If omitted, prints JSON to stdout.
`);
  process.exit(0);
}

requireArgs(args, ['records', 'workspace', 'output']);

if (args.write) {
  throw new Error('Direct MCP writes are intentionally not implemented in this portable starterkit script. Generate the call plan, review it, then execute through the active MCP host.');
}

const records = readJsonl(args.records);
const calls = records.map((record) => ({
  tool: 'ghostcrab_upsert',
  arguments: {
    schema_id: record.schema_id,
    workspace_id: args.workspace,
    match: {
      facets: {
        record_id: record.facets?.record_id ?? record.source_ref,
      },
    },
    create_if_missing: true,
    set_content: record.content,
    set_facets: record.facets ?? {},
  },
}));

writeJsonl(args.output, calls);

reportAndExit(
  {
    ok: true,
    mode: 'dry_run',
    counts: {
      normalized_records: records.length,
      planned_mcp_calls: calls.length,
    },
    output: args.output,
  },
  args.report,
);
