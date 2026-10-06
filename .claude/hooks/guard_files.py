#!/usr/bin/env python3
"""Bloquea ediciones directas de lockfiles y de testvectors ya existentes sin pasar por revisión."""
import json
import sys

data = json.load(sys.stdin)
path = (data.get("tool_input") or {}).get("file_path", "")
name = path.rsplit("/", 1)[-1]

if name in {"poetry.lock", "pnpm-lock.yaml"}:
    print(f"{name} lo genera el gestor (poetry lock / pnpm install); no lo edites a mano.", file=sys.stderr)
    sys.exit(2)
if "/.env" in path and not path.endswith(".env.example"):
    print("No edites archivos .env; usa .env.example con placeholders.", file=sys.stderr)
    sys.exit(2)
if "/migrations/versions/" in path and "Edit" == data.get("tool_name"):
    print("No edites migraciones existentes: crea una nueva con alembic revision.", file=sys.stderr)
    sys.exit(2)
sys.exit(0)
