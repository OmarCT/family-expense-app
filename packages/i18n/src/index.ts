import i18next, { type i18n } from "i18next";

import esMX from "./locales/es-MX.json";

export const defaultLocale = "es-MX";

export const resources = {
  "es-MX": { translation: esMX },
} as const;

export type Locale = keyof typeof resources;

declare module "i18next" {
  interface CustomTypeOptions {
    defaultNS: "translation";
    resources: { translation: typeof esMX };
  }
}

export function createI18n(locale: Locale = defaultLocale): i18n {
  const instance = i18next.createInstance();
  void instance.init({
    lng: locale,
    fallbackLng: defaultLocale,
    resources,
    initAsync: false,
    interpolation: { escapeValue: false },
    returnNull: false,
  });
  return instance;
}
