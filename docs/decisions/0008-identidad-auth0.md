# ADR-0008: Identidad con Auth0

- Estado: Aceptada
- Fecha: 2026-10-05

## Decisión
Auth0 con código por email (passwordless), Google y Sign in with Apple; tenants de desarrollo y producción. El core valida JWT (JWKS, `aud`, `iss`) detrás de una interfaz `TokenVerifier`. El usuario interno se identifica por `sub`; los placeholders no tienen cuenta. Sesiones por dispositivo revocables en el core, revocadas automáticamente al remover del hogar.

## Consecuencias
Borrar cuenta purga email y vínculos de auth y anonimiza como "Former member". Apple exige Sign in with Apple si hay otros logins sociales.
