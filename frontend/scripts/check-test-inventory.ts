import { existsSync, readFileSync } from 'node:fs';
import { Glob } from 'bun';

const mapFile = 'tests/coverage-map.json';
if (!existsSync(mapFile)) {
  console.error('Missing tests/coverage-map.json');
  process.exit(1);
}
const map = JSON.parse(readFileSync(mapFile, 'utf8')) as Record<string, string[]>;
const sources = [...new Glob('src/**/*.svelte').scanSync('.')].sort();
const mapped = Object.keys(map).sort();
const failures: string[] = [];

for (const source of sources) {
  if (!map[source]) failures.push(`Unmapped shipped component or page: ${source}`);
}
for (const source of mapped) {
  if (!sources.includes(source)) failures.push(`Coverage map references a missing source: ${source}`);
  for (const testFile of map[source] ?? []) {
    if (!existsSync(testFile)) {
      failures.push(`Missing test file for ${source}: ${testFile}`);
      continue;
    }
    const content = readFileSync(testFile, 'utf8');
    if (!/\b(?:test|it)\s*\(/.test(content)) {
      failures.push(`No test declaration found in ${testFile}`);
    }
  }
}

const result = Bun.spawnSync(['bunx', 'vitest', 'list'], {
  stdout: 'pipe',
  stderr: 'pipe'
});
if (result.exitCode !== 0) {
  console.error(result.stderr.toString());
  failures.push('vitest could not collect the test inventory');
}
const collected = new Set(
  result.stdout
    .toString()
    .split('\n')
    .map((line) => line.split(' > ')[0]?.trim())
    .filter(Boolean)
);
for (const source of sources) {
  for (const testFile of map[source] ?? []) {
    if (existsSync(testFile) && !collected.has(testFile)) {
      failures.push(`Test file is not collected by Vitest: ${testFile} (for ${source})`);
    }
  }
}

if (failures.length) {
  console.error(failures.join('\n'));
  process.exit(1);
}
console.log(`Frontend test inventory OK: ${sources.length} components/pages mapped to collected tests.`);
