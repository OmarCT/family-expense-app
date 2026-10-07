import { createHash, randomBytes } from "node:crypto";
import { describe, expect, it } from "vitest";

import { sha256, toHex } from "../src/index";

const utf8 = (s: string): Uint8Array => new TextEncoder().encode(s);

describe("sha256 sin dependencias", () => {
  it("coincide con los vectores NIST", () => {
    expect(toHex(sha256(utf8("")))).toBe(
      "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    );
    expect(toHex(sha256(utf8("abc")))).toBe(
      "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
    );
    expect(toHex(sha256(utf8("abcdbcdecdefdefgefghfghighijhijkijkljklmklmnlmnomnopnopq")))).toBe(
      "248d6a61d20638b8e5c026930c3e6039a33ce45964ff2167f6ecedd419db06c1",
    );
  });

  it("coincide con node:crypto en longitudes alrededor de los bordes de bloque", () => {
    for (const length of [0, 1, 54, 55, 56, 57, 63, 64, 65, 119, 120, 121, 127, 128, 129, 1000]) {
      const data = new Uint8Array(randomBytes(length));
      expect(toHex(sha256(data)), `longitud ${length}`).toBe(
        createHash("sha256").update(data).digest("hex"),
      );
    }
  });
});
