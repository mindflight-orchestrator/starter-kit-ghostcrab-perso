#!/usr/bin/env node
import {
  applyFormula,
  getByPath,
  isBlank,
  loadRecords,
  parseArgs,
  readJson,
  reportAndExit,
  requireArgs,
  slug,
  usage,
  writeJsonl,
} from './lib/import-utils.mjs';

const args = parseArgs(process.argv);

if (args.help) {
  usage(`
Usage:
  node scripts/transform_source_to_jsonb.mjs --input data/source.csv --workspace my-workspace --schema-id my-workspace:item --record-id-field id --content-field name --output-records output/normalized_records.jsonl

Options:
  --input            Source CSV, JSON, or JSONL file.
  --workspace        Target workspace id.
  --mapping-json     Optional JSON mapping contract for richer transforms.
  --schema-id        Fallback target schema id when no mapping JSON is provided.
  --record-id-field  Fallback stable id field.
  --content-field    Fallback content field.
  --output-records   JSONL records output path.
  --output-edges     JSONL edges output path.
  --report           Report path. If omitted, prints JSON to stdout.
`);
  process.exit(0);
}

requireArgs(args, ['input', 'workspace', 'output-records']);

const { records } = loadRecords(args.input, args.kind ?? 'auto', args.delimiter ?? ',');
const mapping = args['mapping-json'] ? readJson(args['mapping-json']) : fallbackMapping(args);
const normalizedRecords = [];
const normalizedEdges = [];
const pendingReview = [];

for (const sourceRecord of records) {
  for (const entityRule of mapping.entities) {
    const recordId = buildRecordId(entityRule, sourceRecord);
    const schemaId = entityRule.target_schema_id;

    if (isBlank(recordId)) {
      pendingReview.push({ code: 'missing_record_id', entity_rule: entityRule.target_schema_id, sourceRecord });
      continue;
    }

    const facets = {};
    for (const [facetKey, facetRule] of Object.entries(entityRule.facets ?? {})) {
      facets[facetKey] = resolveFacet(facetRule, sourceRecord);
    }
    facets.record_id = recordId;

    const content = resolveContent(entityRule, sourceRecord, recordId);

    normalizedRecords.push({
      source_ref: entityRule.source_ref_formula ? applyFormula(entityRule.source_ref_formula, sourceRecord) : recordId,
      schema_id: schemaId,
      content,
      facets,
      entities: [
        {
          id: recordId,
          node_type: entityRule.node_type ?? schemaId.split(':').at(-1),
          label: content,
        },
      ],
      edges: [],
    });
  }

  for (const edgeRule of mapping.edges ?? []) {
    const source = applyFormula(edgeRule.source_record_id_formula, sourceRecord);
    const target = applyFormula(edgeRule.target_record_id_formula, sourceRecord);
    if (isBlank(source) || isBlank(target)) {
      pendingReview.push({ code: 'unresolved_reference', edge_label: edgeRule.label, source, target, sourceRecord });
      continue;
    }
    normalizedEdges.push({
      source,
      target,
      label: edgeRule.label,
      confidence: edgeRule.confidence ?? 1,
      metadata: edgeRule.metadata ?? {},
    });
  }
}

writeJsonl(args['output-records'], normalizedRecords);
if (args['output-edges']) {
  writeJsonl(args['output-edges'], normalizedEdges);
}

reportAndExit(
  {
    ok: pendingReview.length === 0,
    counts: {
      source_records: records.length,
      normalized_records: normalizedRecords.length,
      normalized_edges: normalizedEdges.length,
      pending_review: pendingReview.length,
    },
    pending_review: pendingReview,
  },
  args.report,
);

function fallbackMapping(cliArgs) {
  requireArgs(cliArgs, ['schema-id', 'record-id-field']);
  const contentField = cliArgs['content-field'] ?? cliArgs['record-id-field'];
  return {
    workspace_id: cliArgs.workspace,
    entities: [
      {
        target_schema_id: cliArgs['schema-id'],
        node_type: cliArgs['schema-id'].split(':').at(-1),
        record_id_formula: `{raw:${cliArgs['record-id-field']}}`,
        source_ref_formula: `source:{${cliArgs['record-id-field']}}`,
        content_field: contentField,
        facets: {
          title: { from: contentField },
        },
      },
    ],
    edges: [],
  };
}

function buildRecordId(rule, record) {
  if (rule.record_id_formula) return applyFormula(rule.record_id_formula, record);
  if (rule.record_id_field) return `${rule.record_id_prefix ?? rule.target_schema_id.split(':').at(-1)}:${slug(getByPath(record, rule.record_id_field))}`;
  return '';
}

function resolveFacet(rule, record) {
  if (rule == null || typeof rule !== 'object') return rule;
  if (Object.hasOwn(rule, 'const')) return rule.const;
  if (rule.from) return getByPath(record, rule.from);
  return null;
}

function resolveContent(rule, record, recordId) {
  if (rule.content_template) return applyFormula(rule.content_template, record);
  if (rule.content_field) return String(getByPath(record, rule.content_field) ?? recordId);
  return recordId;
}
