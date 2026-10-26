import { existsSync, readFileSync, readdirSync } from "node:fs";
import { join } from "node:path";
import { homedir } from "node:os";
import { fileURLToPath } from "node:url";

const name = "dsh-memoir";
const inject = ["commands"];

function storeRoot() {
  return process.env.MEMOIR_STORE || join(homedir(), ".claude", "memory");
}

/** CJK ~1 token/char, latin ~4 chars/token. Good enough to flag budget blowouts. */
function roughTokens(text) {
  const cjk = (text.match(/[一-鿿＀-￯]/g) ?? []).length;
  const rest = text.replace(/[一-鿿＀-￯]/g, " ");
  const words = rest.trim() ? rest.trim().split(/\s+/).length : 0;
  return cjk + Math.ceil(words / 4);
}

function walkMd(dir, acc = []) {
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const p = join(dir, entry.name);
    if (entry.isDirectory()) walkMd(p, acc);
    else if (entry.name.toLowerCase().endsWith(".md")) acc.push(p);
  }
  return acc;
}

function lastMaintained(root) {
  const state = join(root, ".memoir-state.json");
  if (!existsSync(state)) return null;
  try {
    const { lastMaintained } = JSON.parse(readFileSync(state, "utf8"));
    const days = Math.floor((Date.now() - new Date(lastMaintained).getTime()) / 86400000);
    return { date: lastMaintained, days };
  } catch {
    return null;
  }
}

function healthReport() {
  const root = storeRoot();
  if (!existsSync(root)) {
    return `memoir: no store at ${root}. Set MEMOIR_STORE to your memory directory.`;
  }

  const files = walkMd(root);
  const archived = files.filter((p) => /[\\/]archive[\\/]/.test(p));
  const lifecycle = {};
  for (const p of files) {
    const m = readFileSync(p, "utf8").slice(0, 600).match(/^lifecycle:\s*(\S+)/m);
    if (m) lifecycle[m[1]] = (lifecycle[m[1]] ?? 0) + 1;
  }

  const out = [`memoir store: ${root}`, `${files.length} memory files (${archived.length} archived)`];

  const hot = join(root, "HOT-MEMORY.md");
  if (existsSync(hot)) {
    const tok = roughTokens(readFileSync(hot, "utf8"));
    out.push(`HOT-MEMORY.md: ~${tok} tok${tok > 2000 ? " (over the 2000-token budget)" : ""}`);
  }

  const st = Object.entries(lifecycle).map(([k, v]) => `${k} ${v}`).join(", ");
  out.push(st ? `lifecycle: ${st}` : "lifecycle: no frontmatter in this store (run the migration spec first)");

  const last = lastMaintained(root);
  if (!last) out.push("last maintenance: never recorded");
  else {
    out.push(`last maintenance: ${last.date} (${last.days} days ago)`);
    if (last.days > 90) out.push("maintenance is overdue (threshold: 90 days)");
  }

  return out.join("\n");
}

function apply(ctx) {
  ctx.commands.register({
    name: "memoir-status",
    description: "memoir store health: file counts, lifecycle distribution, HOT-MEMORY budget, maintenance staleness",
    handler: () => ({ kind: "success", text: healthReport() }),
  });
}

export { apply, inject, name };

// ponytail: the self-check is the CLI; `MEMOIR_STORE=<dir> node lib/index.js` prints the same report.
if (process.argv[1] === fileURLToPath(import.meta.url)) console.log(healthReport());
