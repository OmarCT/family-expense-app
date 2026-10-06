# ADR-0009: Expo con dev client y módulos nativos propios

- Estado: Aceptada
- Fecha: 2026-10-05

## Decisión
Expo con *dev client* y prebuild (CNG). ML Kit (Android) y Apple Vision (iOS) se envuelven como **Expo Modules** locales en `apps/mobile/modules/` con una interfaz común TS (`scanReceipt(imageUri) → RawOcr`). El parser heurístico vive en TypeScript, probado con el conjunto de tickets reales.

## Consecuencias
No se versionan `ios/` ni `android/` (se generan). Builds con EAS. Si un módulo exige configuración nativa que Expo no cubre, se reevalúa bare workflow.
