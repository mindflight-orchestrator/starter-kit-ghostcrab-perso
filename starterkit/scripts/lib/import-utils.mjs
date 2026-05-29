import fs from 'node:fs';
import path from 'node:path';

export function parseArgs(argv) {
  const args = {};
  for (let i = 2; i < argv.length; i += 1) {
    const token = argv[i];
    if (!token.startsWith('--')) {
      continue;
    }
    const key = token.slice(2);
    const next = argv[i + 1];
    if (!next || next.startsWith('--')) {
      args[key] = true;
    } else {
      args[key] = next;
      i += 1;
    }
  }
  return args;
}

export function usage(text) {
  console.log(text.trim());
}

export function requireArgs(args, names) {
  const missing = names.filter((name) => !args[name]);
  if (missing.length) {
    throw new Error(`Missing required args: ${missing.map((name) => `--${name}`).join(', ')}`);
  }
}

export function readText(filePath) {
  return fs.readFileSync(filePath, 'utf8');
}

export function ensureDir(filePath) {
  const dir = path.dirname(filePath);
  fs.mkdirSync(dir, { recursive: true });
}

export function writeText(filePath, content) {
  ensureDir(filePath);
  fs.writeFileSync(filePath, content);
}

export function writeJson(filePath, value) {
  writeText(filePath, `${JSON.stringify(value, null, 2)}\n`);
}

export function writeJsonl(filePath, values) {
  writeText(filePath, `${values.map((value) => JSON.stringify(value)).join('\n')}\n`);
}

export function csvEscape(value) {
  if (value == null) return '';
  const text = typeof value === 'string' ? value : JSON.stringify(value);
  if (/[",\n\r]/.test(text)) {
    return `"${text.replaceAll('"', '""')}"`;
  }
  return text;
}

export function writeCsv(filePath, headers, rows) {
  const lines = [
    headers.map(csvEscape).join(','),
    ...rows.map((row) => headers.map((header) => csvEscape(row[header])).join(',')),
  ];
  writeText(filePath, `${lines.join('\n')}\n`);
}

export function readJson(filePath) {
  return JSON.parse(readText(filePath));
}

export function readJsonl(filePath) {
  return readText(filePath)
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => JSON.parse(line));
}

export function readJsonIfPossible(filePath) {
  const text = readText(filePath);
  const trimmed = text.trim();
  if (!trimmed.startsWith('{') && !trimmed.startsWith('[')) {
    return null;
  }
  return JSON.parse(trimmed);
}

export function parseCsv(text, delimiter = ',') {
  const rows = [];
  let row = [];
  let field = '';
  let inQuotes = false;

  for (let i = 0; i < text.length; i += 1) {
    const char = text[i];
    const next = text[i + 1];

    if (char === '"' && inQuotes && next === '"') {
      field += '"';
      i += 1;
      continue;
    }

    if (char === '"') {
      inQuotes = !inQuotes;
      continue;
    }

    if (char === delimiter && !inQuotes) {
      row.push(field);
      field = '';
      continue;
    }

    if ((char === '\n' || char === '\r') && !inQuotes) {
      if (char === '\r' && next === '\n') {
        i += 1;
      }
      row.push(field);
      rows.push(row);
      row = [];
      field = '';
      continue;
    }

    field += char;
  }

  if (field.length || row.length) {
    row.push(field);
    rows.push(row);
  }

  const [headers = [], ...dataRows] = rows.filter((candidate) => candidate.some((value) => value !== ''));
  return dataRows.map((values) => Object.fromEntries(headers.map((header, index) => [header, values[index] ?? ''])));
}

export function flattenRecord(record, prefix = '', out = {}) {
  for (const [key, value] of Object.entries(record ?? {})) {
    const nextKey = prefix ? `${prefix}.${key}` : key;
    if (value && typeof value === 'object' && !Array.isArray(value)) {
      flattenRecord(value, nextKey, out);
    } else {
      out[nextKey] = value;
    }
  }
  return out;
}

export function loadRecords(inputPath, kind = 'auto', delimiter = ',') {
  const text = readText(inputPath);
  const resolvedKind = kind === 'auto' ? inferKind(inputPath, text) : kind;

  if (resolvedKind === 'csv') {
    return { kind: resolvedKind, records: parseCsv(text, delimiter) };
  }

  if (resolvedKind === 'jsonl') {
    return { kind: resolvedKind, records: readJsonl(inputPath) };
  }

  if (resolvedKind === 'json') {
    const value = JSON.parse(text);
    if (Array.isArray(value)) {
      return { kind: resolvedKind, records: value };
    }
    const firstArray = Object.values(value).find(Array.isArray);
    return { kind: resolvedKind, records: firstArray ?? [value] };
  }

  throw new Error(`Unsupported source kind: ${resolvedKind}`);
}

export function inferKind(inputPath, text) {
  const ext = path.extname(inputPath).toLowerCase();
  if (ext === '.csv' || ext === '.tsv') return ext === '.tsv' ? 'tsv' : 'csv';
  if (ext === '.jsonl' || ext === '.ndjson') return 'jsonl';
  if (ext === '.json') return 'json';
  const trimmed = text.trim();
  if (trimmed.startsWith('{') || trimmed.startsWith('[')) return 'json';
  return 'csv';
}

export function getByPath(record, fieldPath) {
  if (!fieldPath) return undefined;
  if (Object.hasOwn(record, fieldPath)) return record[fieldPath];
  return fieldPath.split('.').reduce((value, key) => (value == null ? undefined : value[key]), record);
}

export function unique(values) {
  return [...new Set(values.filter((value) => value != null && value !== ''))];
}

export function isBlank(value) {
  return value == null || String(value).trim() === '';
}

export function slug(value) {
  return String(value ?? '')
    .trim()
    .toLowerCase()
    .normalize('NFKD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
}

export function applyFormula(formula, record) {
  return String(formula).replace(/\{([^}]+)\}/g, (_match, field) => {
    if (field.startsWith('raw:')) {
      return String(getByPath(record, field.slice(4)) ?? '');
    }
    return slug(getByPath(record, field));
  });
}

export function reportAndExit(report, outputPath) {
  if (outputPath) {
    writeJson(outputPath, report);
  } else {
    console.log(JSON.stringify(report, null, 2));
  }
  process.exit(report.ok ? 0 : 1);
}
