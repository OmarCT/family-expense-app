---
description: Crear una migración Alembic con su política RLS y prueba de frontera
argument-hint: <descripción>
---
En `services/core`: `poetry run alembic revision -m "$ARGUMENTS"`. Si añade o cambia una tabla con datos de hogar, incluye en la misma migración `ENABLE ROW LEVEL SECURITY`, `FORCE ROW LEVEL SECURITY` y las políticas por membresía/participación, y crea la prueba de frontera (no miembro, miembro removido, no participante). Nunca edites migraciones previas.
