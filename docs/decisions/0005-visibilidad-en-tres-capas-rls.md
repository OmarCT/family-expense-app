# ADR-0005: Visibilidad en tres capas con RLS de PostgreSQL

- Estado: Aceptada
- Fecha: 2026-10-05

## Decisión
1. El evento declara sus participantes. 2. RLS de PostgreSQL por membresía de hogar y participación, con contexto por transacción (`SET LOCAL app.user_id`, `app.household_id`). 3. Filtros equivalentes en feed y proyectores.
El rol de la aplicación **no** es dueño de las tablas ni tiene `BYPASSRLS`.

## Consecuencias
Suite de frontera obligatoria (no miembro, miembro removido, no participante). Un gasto participants-only no aparece ni como tombstone. Los workers que leen datos usan el mismo mecanismo de contexto.
