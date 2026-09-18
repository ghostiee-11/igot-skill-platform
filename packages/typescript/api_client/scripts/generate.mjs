import { execFileSync } from "node:child_process";
import { mkdirSync, readdirSync } from "node:fs";
import { basename, dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const packageRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const repositoryRoot = resolve(packageRoot, "../../..");
const contractsRoot = join(repositoryRoot, "contracts", "http");
const outputRoot = join(packageRoot, "src", "generated");
const executable = process.platform === "win32" ? "openapi-typescript.cmd" : "openapi-typescript";
const binary = join(packageRoot, "node_modules", ".bin", executable);
const specs = readdirSync(contractsRoot).filter((file) => file.endsWith(".openapi.json")).sort();

if (specs.length === 0) {
  throw new Error("No exported OpenAPI contracts found. Start the services and run npm run contracts:export first.");
}

mkdirSync(outputRoot, { recursive: true });
for (const spec of specs) {
  const service = basename(spec, ".openapi.json");
  execFileSync(binary, [join(contractsRoot, spec), "--output", join(outputRoot, `${service}.ts`)], {
    stdio: "inherit",
  });
}
