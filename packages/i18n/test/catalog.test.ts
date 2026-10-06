import { describe, expect, it } from "vitest";

import { createI18n, defaultLocale, resources } from "../src/index";

type Tree = { [key: string]: string | Tree };

function flatten(tree: Tree, prefix = ""): string[] {
  return Object.entries(tree).flatMap(([key, value]) =>
    typeof value === "string" ? [`${prefix}${key}`] : flatten(value, `${prefix}${key}.`),
  );
}

describe("catálogo de traducciones", () => {
  const base = flatten(resources[defaultLocale].translation).sort();

  it("es-MX es el locale por defecto y no tiene valores vacíos", () => {
    const i18n = createI18n();
    expect(i18n.language).toBe("es-MX");
    for (const key of base) {
      expect(i18n.t(key as never)).not.toBe("");
      expect(i18n.t(key as never)).not.toBe(key);
    }
  });

  it("todos los locales tienen exactamente las claves de es-MX", () => {
    for (const [locale, { translation }] of Object.entries(resources)) {
      expect(flatten(translation).sort(), locale).toEqual(base);
    }
  });

  it("una clave inexistente devuelve la clave, no texto inventado", () => {
    expect(createI18n().t("no.existe" as never)).toBe("no.existe");
  });
});
