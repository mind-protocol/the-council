#!/usr/bin/env node
// PostToolUse hook: signale les fichiers écrits/édités qui dépassent la limite
// de lignes et demande leur découpage.
const fs = require('fs');
const path = require('path');

const LIMIT = 500;
const SKIP = /(package-lock\.json|yarn\.lock|pnpm-lock\.yaml)$|\.lock$|\.min\.[a-z]+$/i;

let raw = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', (chunk) => {
  raw += chunk;
});
process.stdin.on('end', () => {
  let file;
  try {
    const input = JSON.parse(raw);
    file = (input.tool_response && input.tool_response.filePath) ||
      (input.tool_input && input.tool_input.file_path);
  } catch (err) {
    return;
  }
  if (!file || SKIP.test(file)) return;

  let lines;
  try {
    const content = fs.readFileSync(file, 'utf8');
    lines = content.split('\n');
    if (lines[lines.length - 1] === '') lines.pop();
    lines = lines.length;
  } catch (err) {
    return;
  }
  if (lines <= LIMIT) return;

  process.stdout.write(JSON.stringify({
    systemMessage: `${path.basename(file)} : ${lines} lignes (limite ${LIMIT}) — à découper.`,
    hookSpecificOutput: {
      hookEventName: 'PostToolUse',
      additionalContext: `Le fichier ${file} fait ${lines} lignes, au-delà de la limite de ${LIMIT} fixée pour ce projet. Découpe-le en modules plus petits et cohérents : extrais les responsabilités distinctes dans des fichiers séparés et mets à jour les imports. Si le découpage nuirait réellement à la lisibilité, laisse le fichier tel quel et explique pourquoi.`,
    },
  }));
});
