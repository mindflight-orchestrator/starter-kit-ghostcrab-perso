#!/usr/bin/env node
import crypto from 'node:crypto';
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
  node scripts/update_syncstate.mjs --syncstate output/syncstate.json --source data/source.csv --workspace my-workspace --status profiled

Options:
  --syncstate             Syncstate JSON path.
  --source                Single source file.
  --source-list           Newline-delimited source file list.
  --workspace             Workspace id.
  --status                Status to assign: discovered | profiled | transformed | injected | pending_review | deleted.
  --mark-missing-deleted  Mark previously tracked files absent from this run as deleted.
  --output                Report path. If omitted, prints JSON to stdout.
`);
  process.exit(0);
}

requireArgs(args, ['syncstate', 'workspace']);

const sources = collectSources(args);
if (!sources.length) throw new Error('Provide --source or --source-list.');

const now = new Date().toISOString();
const syncstate = fs.existsSync(args.syncstate)
  ? readJson(args.syncstate)
  : { workspace_id: args.workspace, last_run: null, files: {} };

syncstate.workspace_id = syncstate.workspace_id ?? args.workspace;
syncstate.last_run = now;
syncstate.files = syncstate.files ?? {};

const seen = new Set();
const changed = [];
const unchanged = [];

for (const source of sources) {
  const stat = fs.statSync(source);
  const hash = sha256(source);
  const prior = syncstate.files[source];
  const next = {
    last_modified: stat.mtime.toISOString(),
    size: stat.size,
    sha256: hash,
    status: args.status ?? prior?.status ?? 'discovered',
    updated_at: now,
  };
  syncstate.files[source] = { ...prior, ...next };
  seen.add(source);
  if (!prior || prior.sha256 !== hash || prior.size !== stat.size) {
    changed.push(source);
  } else {
    unchanged.push(source);
  }
}

const markedDeleted = [];
if (args['mark-missing-deleted']) {
  for (const filePath of Object.keys(syncstate.files)) {
    if (!seen.has(filePath) && syncstate.files[filePath].status !== 'deleted') {
      syncstate.files[filePath].status = 'deleted';
      syncstate.files[filePath].deleted_at = now;
      markedDeleted.push(filePath);
    }
  }
}

writeJson(args.syncstate, syncstate);

reportAndExit(
  {
    ok: true,
    syncstate: args.syncstate,
    counts: {
      seen: seen.size,
      changed: changed.length,
      unchanged: unchanged.length,
      marked_deleted: markedDeleted.length,
    },
    changed,
    marked_deleted: markedDeleted,
  },
  args.output,
);

function collectSources(cliArgs) {
  const sources = [];
  if (cliArgs.source) sources.push(cliArgs.source);
  if (cliArgs['source-list']) {
    const list = fs
      .readFileSync(cliArgs['source-list'], 'utf8')
      .split(/\r?\n/)
      .map((line) => line.trim())
      .filter(Boolean);
    sources.push(...list);
  }
  return sources;
}

function sha256(filePath) {
  return crypto.createHash('sha256').update(fs.readFileSync(filePath)).digest('hex');
}
