import { readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, it } from "vitest";

const dir = join(__dirname, "../../../testvectors");
const files = readdirSync(dir).filter((f) => f.endsWith(".json"));

describe("shared money vectors", () => {
  for (const f of files) {
    const data = JSON.parse(readFileSync(join(dir, f), "utf8")) as { cases: { id: string }[] };
    for (const c of data.cases) {
      // Pendiente: implementar en src/ durante el Slice 1
      it.skip(`${f}:${c.id}`, () => {});
    }
  }
});
