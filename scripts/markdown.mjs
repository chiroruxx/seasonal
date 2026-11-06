import { existsSync } from "node:fs";
import { readFile, writeFile } from "node:fs/promises";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { resolve } from "node:path";
import * as prettier from "prettier";

const root = fileURLToPath(new URL("../", import.meta.url));
const [mode, ...requestedFiles] = process.argv.slice(2);
if (!["format", "check", "lint"].includes(mode)) {
  throw new Error(`Unknown Markdown command: ${mode}`);
}

let files = requestedFiles;
if (files.length === 0) {
  const result = spawnSync(
    "git",
    ["ls-files", "--cached", "--others", "--exclude-standard", "-z"],
    { cwd: root, encoding: "utf8" },
  );
  if (result.error) throw result.error;
  if (result.status !== 0) {
    process.stderr.write(result.stderr);
    process.exit(result.status ?? 1);
  }
  files = [...new Set(result.stdout.split("\0"))].filter(
    (path) => path.endsWith(".md") && existsSync(resolve(root, path)),
  );
}

if (files.length === 0) {
  process.stdout.write("No Markdown files to check.\n");
  process.exit(0);
}
if (mode === "lint") {
  const result = spawnSync(
    process.execPath,
    [
      fileURLToPath(
        new URL(
          "../node_modules/markdownlint-cli2/markdownlint-cli2-bin.mjs",
          import.meta.url,
        ),
      ),
      ...files,
    ],
    { cwd: root, stdio: "inherit" },
  );
  if (result.error) throw result.error;
  process.exit(result.status ?? 1);
}

let changed = false;
for (const file of files) {
  const path = resolve(root, file);
  const info = await prettier.getFileInfo(path, {
    ignorePath: resolve(root, ".prettierignore"),
  });
  if (info.ignored) continue;
  if (info.inferredParser !== "markdown")
    throw new Error(`Not a Markdown file: ${file}`);
  const original = await readFile(path, "utf8");
  const options = await prettier.resolveConfig(path);
  let formatted = await prettier.format(original, {
    ...options,
    filepath: path,
  });
  // Prettier drops hard-break spaces at a paragraph's end. Keep explicit
  // two-space breaks on otherwise unchanged lines, including the pitch's last line.
  const hardBreakLines = new Set(
    original
      .split("\n")
      .filter((line) => /\S {2}$/.test(line))
      .map((line) => line.slice(0, -2)),
  );
  formatted = formatted
    .split("\n")
    .map((line) => {
      const content = line.replace(/ +$/, "");
      return hardBreakLines.has(content) ? `${content}  ` : line;
    })
    .join("\n");
  if (formatted !== original) {
    changed = true;
    if (mode === "format") await writeFile(path, formatted);
    process.stdout.write(
      `${mode === "format" ? "Formatted" : "Needs formatting"}: ${file}\n`,
    );
  }
}
if (mode === "check" && changed) process.exit(1);
process.stdout.write(`Markdown ${mode} complete (${files.length} files).\n`);
