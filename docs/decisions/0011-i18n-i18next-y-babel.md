# ADR-0011: i18n con i18next (clientes) y Babel (servicios Python)

- Estado: Aceptada
- Fecha: 2026-10-06

## Contexto
La regla 8 prohíbe cadenas visibles en código: todo texto sale de claves de traducción, con `es-MX` como primer idioma. Los nombres sembrados (categorías) se guardan como claves, no como texto.

## Decisión
- **Clientes (web y móvil):** `i18next` con `react-i18next`. El catálogo vive en un paquete compartido `packages/i18n`, de modo que ambos clientes usan las mismas claves. `es-MX` es el idioma por defecto y de respaldo.
- **Servicios Python:** `Babel` para locale y formato (moneda, fechas) y catálogos `.po` por locale en `services/core`, con la misma convención de claves. El servidor devuelve códigos de error estables; el texto se resuelve por clave.

## Alternativas descartadas
- Cadenas en código o diccionarios por app: se desincronizan entre web y móvil.
- `expo-localization` desde el inicio: se añade cuando haya un segundo idioma; hoy el locale por defecto es `es-MX`.

## Consecuencias
Dos dependencias nuevas en TypeScript (`i18next`, `react-i18next`) y una en Python (`babel`). Añadir un idioma exige el catálogo completo en ambos lados; una prueba verifica que no falten claves frente a `es-MX`.
