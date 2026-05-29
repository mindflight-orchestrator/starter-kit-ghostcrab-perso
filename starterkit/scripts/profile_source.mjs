#!/usr/bin/env node
import path from 'node:path';
import {
  flattenRecord,
  getByPath,
  isBlank,
  loadRecords,
  parseArgs,
  reportAndExit,
  requireArgs,
  usage,
  writeJson,
} from './lib/import-utils.mjs';

const args = parseArgs(process.argv);

if (args.help) {
  usage(`
Usage:
  node scripts/profile_source.mjs --input data/source.csv --workspace my-workspace --output output/source_profile.report.json

Options:
  --input       Source CSV, JSON, or JSONL file.
  --workspace   Target workspace id.
  --kind        csv | json | jsonl | auto (default: auto).
  --delimiter   CSV delimiter (default: comma).
  --output      Report path. If omitted, prints JSON to stdout.
`);
  process.exit(0);
}

requireArgs(args, ['input', 'workspace']);

const delimiter = args.delimiter ?? ',';
const { kind, records } = loadRecords(args.input, args.kind ?? 'auto', delimiter);
const flattened = records.map((record) => flattenRecord(record));
const headers = [...new Set(flattened.flatMap((record) => Object.keys(record)))].sort();
const rowCount = flattened.length;

const fieldInventory = headers.map((field) => {
  const values = flattened.map((record) => getByPath(record, field));
  const nonBlankValues = values.filter((value) => !isBlank(value));
  const uniqueValues = [...new Set(nonBlankValues.map((value) => String(value)))];
  const nullRate = rowCount === 0 ? 1 : Number(((rowCount - nonBlankValues.length) / rowCount).toFixed(4));
  const enumLike = uniqueValues.length > 0 && uniqueValues.length <= Math.min(30, Math.max(10, rowCount * 0.2));
  const likelyId = /(^id$|_id$|uuid|email|domain|slug|key|code)/i.test(field);

  return {
    source_field: field,
    observed_type: inferType(nonBlankValues),
    null_rate: nullRate,
    unique_count: uniqueValues.length,
    example_values: uniqueValues.slice(0, 5),
    classification: likelyId ? 'identity_candidate' : enumLike ? 'enum_candidate' : 'unmapped',
    target_hint: '',
    notes: '',
  };
});

const identityCandidates = fieldInventory
  .filter((field) => field.classification === 'identity_candidate' || field.unique_count === rowCount)
  .map((field) => ({
    field: field.source_field,
    uniqueness: field.unique_count === rowCount ? 'unique' : 'unknown',
    stability: /email|domain|uuid|id|slug|key/i.test(field.source_field) ? 'stable' : 'unknown',
    notes: '',
  }));

const detectedEnums = fieldInventory
  .filter((field) => field.classification === 'enum_candidate')
  .map((field) => ({
    field: field.source_field,
    values: field.example_values,
    target_enum_hint: '',
  }));

const profile = {
  workspace_id: args.workspace,
  source: {
    id: path.basename(args.input).replace(/\.[^.]+$/, ''),
    kind,
    path: args.input,
    encoding: 'utf-8',
    delimiter: kind === 'csv' ? delimiter : null,
    owner: '',
    exported_at: '',
  },
  shape: {
    row_count: rowCount,
    headers,
    sample_records: records.slice(0, 5),
  },
  identity_candidates: identityCandidates,
  field_inventory: fieldInventory,
  detected_enums: detectedEnums,
  relation_candidates: [],
  ignored_fields: [],
  profiling_warnings: identityCandidates.length
    ? []
    : [{ code: 'no_obvious_identity_candidate', message: 'No obvious stable id/email/domain/slug field was detected.' }],
};

if (args['template-output']) {
  writeJson(args['template-output'], profile);
}

reportAndExit({ ok: true, profile }, args.output);

function inferType(values) {
  if (!values.length) return 'unknown';
  const strings = values.map((value) => String(value));
  if (strings.every((value) => value === 'true' || value === 'false')) return 'boolean';
  if (strings.every((value) => !Number.isNaN(Number(value)))) return 'number';
  if (strings.every((value) => /^\d{4}-\d{2}-\d{2}/.test(value))) return 'date';
  return 'string';
}
