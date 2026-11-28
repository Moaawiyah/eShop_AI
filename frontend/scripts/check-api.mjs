// Drift check for the generated API files (AC-048).
// Regenerates openapi.json (from the backend) and schema.d.ts into a temp
// directory and fails when either differs from the committed copy.
import { spawnSync } from "node:child_process";
import { mkdtempSync, readFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const frontend = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const committed = join(frontend, "src", "lib", "api");
const temp = mkdtempSync(join(tmpdir(), "eshop-api-"));

function run(command, args, cwd) {
  const result = spawnSync(command, args, { cwd, stdio: "inherit" });
  if (result.error || result.status !== 0) {
    console.error(`Command failed: ${command} ${args.join(" ")}`);
    process.exit(2);
  }
}

try {
  const openapi = join(temp, "openapi.json");
  const schema = join(temp, "schema.d.ts");
  run(
    "uv",
    ["run", "python", "scripts/export_openapi.py", openapi],
    join(frontend, "..", "backend"),
  );
  run(
    join(frontend, "node_modules", ".bin", "openapi-typescript"),
    [openapi, "-o", schema],
    frontend,
  );

  const stale = [
    ["openapi.json", openapi],
    ["schema.d.ts", schema],
  ].filter(
    ([name, fresh]) =>
      readFileSync(join(committed, name), "utf8") !==
      readFileSync(fresh, "utf8"),
  );
  if (stale.length > 0) {
    console.error(
      `Generated API types are stale (${stale.map(([name]) => name).join(", ")}): run npm run generate:api`,
    );
    process.exit(1);
  }
  console.log("Generated API types are up to date.");
} finally {
  rmSync(temp, { recursive: true, force: true });
}
