import assert from "node:assert/strict";
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import test from "node:test";
import { lint } from "markdownlint/promise";
import { micromark } from "micromark";
import { math, mathHtml } from "micromark-extension-math";

const command = fileURLToPath(new URL("markdown.mjs", import.meta.url));

test("Markdown formatting preserves explicit hard breaks and checks the requested file", () => {
  const directory = mkdtempSync(join(tmpdir(), "seasonal-markdown-"));
  try {
    const file = join(directory, "pitch.md");
    const untouched = join(directory, "untouched.md");
    writeFileSync(file, "#  テスト\n\nひとつめ  \n最後の行  \n");
    writeFileSync(untouched, "#  そのまま\n");
    const run = (mode) =>
      spawnSync(process.execPath, [command, mode, file], { encoding: "utf8" });
    assert.equal(run("check").status, 1);
    const result = run("format");
    assert.equal(result.status, 0, result.stderr);
    const formatted = readFileSync(file, "utf8");
    assert.match(formatted, /ひとつめ {2}\n最後の行 {2}\n$/);
    assert.equal(run("check").status, 0);
    assert.equal(readFileSync(untouched, "utf8"), "#  そのまま\n");
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
});

test("the patched math dependency preserves Markdown linting and math rendering", async () => {
  const markdown = "# Math\n\nInline $a_b + c$ and display math:\n\n$$\n\\frac{1}{2}\n$$\n";
  const result = await lint({ strings: { math: markdown } });
  assert.deepEqual(result.math, []);

  const html = micromark(markdown, {
    extensions: [math()],
    htmlExtensions: [mathHtml()],
  });
  assert.match(html, /class="math math-inline"/);
  assert.match(html, /class="math math-display"/);
  assert.match(html, /class="katex"/);
  assert.match(html, /<mfrac>/);

  const invalid = await lint({ strings: { math: `${markdown}\n##  Invalid heading\n` } });
  assert.ok(invalid.math.some((error) => error.ruleNames.includes("MD019")));
});
