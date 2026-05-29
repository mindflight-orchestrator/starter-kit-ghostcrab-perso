#!/usr/bin/env node
import {
  parseArgs,
  readJsonIfPossible,
  readText,
  reportAndExit,
  requireArgs,
  usage,
} from './lib/import-utils.mjs';

const args = parseArgs(process.argv);

if (args.help) {
  usage(`
Usage:
  node scripts/validate_source_profile.mjs --profile templates/source_profile.yaml --output output/source_profile.validation.json

Options:
  --profile   Source profile YAML or JSON.
  --strict    Treat warnings as failures.
  --output    Report path. If omitted, prints JSON to stdout.
`);
  process.exit(0);
}

requireArgs(args, ['profile']);

const text = readText(args.profile);
const json = readJsonIfPossible(args.profile);
const errors = [];
const warnings = [];
const allowedClassifications = new Set([
  'mapped',
  'derived',
  'relation_candidate',
  'ignored',
  'pending_review',
  'unmapped',
  'identity_candidate',
  'enum_candidate',
]);

if (json) {
  const profile = json.profile ?? json;
  if (!profile.workspace_id) errors.push({ code: 'missing_workspace_id' });
  if (!profile.source?.kind) errors.push({ code: 'missing_source_kind' });
  if (!Array.isArray(profile.field_inventory) || profile.field_inventory.length === 0) {
    errors.push({ code: 'missing_field_inventory' });
  }
  if (!Array.isArray(profile.identity_candidates) || profile.identity_candidates.length === 0) {
    warnings.push({ code: 'missing_identity_candidates' });
  }
  for (const field of profile.field_inventory ?? []) {
    if (!allowedClassifications.has(field.classification)) {
      errors.push({
        code: 'invalid_field_classification',
        field: field.source_field,
        classification: field.classification,
      });
    }
    if (field.classification === 'ignored' && !field.notes && !field.reason) {
      warnings.push({ code: 'ignored_field_without_reason', field: field.source_field });
    }
  }
  const unmappedCount = (profile.field_inventory ?? []).filter((field) => field.classification === 'unmapped').length;
  if (unmappedCount) warnings.push({ code: 'unmapped_fields_present', count: unmappedCount });
} else {
  for (const required of ['workspace_id:', 'source:', 'shape:', 'identity_candidates:', 'field_inventory:']) {
    if (!text.includes(required)) errors.push({ code: 'missing_source_profile_section', section: required.slice(0, -1) });
  }

  const placeholders = text.match(/<[^>]+>/g) ?? [];
  if (placeholders.length) warnings.push({ code: 'template_placeholders_present', count: placeholders.length });

  const classifications = [...text.matchAll(/classification:\s*"?([^"\n#]+)"?/g)].map((match) => match[1].trim());
  for (const classification of classifications) {
    if (!allowedClassifications.has(classification)) {
      errors.push({ code: 'invalid_field_classification', classification });
    }
  }
  if (classifications.includes('unmapped')) {
    warnings.push({ code: 'unmapped_fields_present', count: classifications.filter((value) => value === 'unmapped').length });
  }
  if (!/uniqueness:\s*"(unique|mostly_unique)"/.test(text) && !/stability:\s*"(stable|derived)"/.test(text)) {
    warnings.push({ code: 'no_stable_identity_confirmed' });
  }
}

reportAndExit(
  {
    ok: errors.length === 0 && (!args.strict || warnings.length === 0),
    profile: args.profile,
    strict: Boolean(args.strict),
    errors,
    warnings,
  },
  args.output,
);
