import { readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

import { orderByTiebreak, tiebreakKey, toHex } from "../src/index";

type Json = Record<string, unknown>;
type Handler = (input: Json) => Json;

// Al implementar una regla, regístrala aquí; las que faltan se omiten de forma explícita.
const handlers: Record<string, Handler> = {
  tiebreak_hash: (input) => ({
    digest_hex: toHex(tiebreakKey(input["item_id"] as string, input["user_id"] as string)),
  }),
  tiebreak_order: (input) => ({
    order: orderByTiebreak(input["item_id"] as string, input["user_ids"] as string[]),
  }),
};

const dir = join(__dirname, "../../../testvectors");
const files = readdirSync(dir).filter((f) => f.endsWith(".json"));

describe("shared money vectors", () => {
  for (const f of files) {
    const data = JSON.parse(readFileSync(join(dir, f), "utf8")) as {
      rule: string;
      cases: { id: string; input: Json; expected: Json }[];
    };
    const handler = handlers[data.rule];
    for (const c of data.cases) {
      if (handler === undefined) {
        it.skip(`${f}:${c.id} (pendiente: regla ${data.rule}, Slice 1)`, () => {});
      } else {
        it(`${f}:${c.id}`, () => {
          expect(handler(c.input)).toEqual(c.expected);
        });
      }
    }
  }
});
