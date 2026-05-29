#!/usr/bin/env node
import { parseArgs, readText, reportAndExit, requireArgs, usage } from './lib/import-utils.mjs';

const args = parseArgs(process.argv);

if (args.help) {
  usage(`
Usage:
  node scripts/validate_mapping_contract.mjs --mapping templates/mapping_external_to_canonical.yaml --output output/mapping.validation.json

Options:
  --mapping          YAML or JSON mapping contract.
  --source-profile   Optional source profile file.
  --model            Optional target model contract file.
  --output           Report path. If omitted, prints JSON to stdout.
`);
  process.exit(0);
}

requireArgs(args, ['mapping']);

const mappingText = readText(args.mapping);
const errors = [];
const warnings = [];

for (const required of [
  'workspace_id',
  'source_contract',
  'record_id_rules',
  'field_to_facet',
  'relation_extraction',
  'pending_review_rules',
]) {
  if (!mappingText.includes(`${required}:`)) {
    errors.push({ code: 'missing_mapping_section', section: required });
  }
}

if ((mappingText.match(/<[^>]+>/g) ?? []).length) {
  warnings.push({
    code: 'template_placeholders_present',
    message: 'The mapping still contains <placeholder> values. This is acceptable for a template, not for a write run.',
  });
}

if (args['source-profile']) {
  const sourceProfile = readText(args['source-profile']);
  if (!sourceProfile.includes('field_inventory') && !sourceProfile.includes('headers')) {
    warnings.push({ code: 'source_profile_shape_unknown', file: args['source-profile'] });
  }
}

if (args.model) {
  const modelText = readText(args.model);
  if (!modelText.includes('workspace_id') && !modelText.includes('schema')) {
    warnings.push({ code: 'model_contract_shape_unknown', file: args.model });
  }
}

reportAndExit(
  {
    ok: errors.length === 0,
    mapping: args.mapping,
    errors,
    warnings,
  },
  args.output,
);
