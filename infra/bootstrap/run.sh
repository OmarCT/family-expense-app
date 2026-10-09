#!/usr/bin/env bash
# Ejecuta terraform del bootstrap con la cuenta, el estado y las variables de UN solo entorno.
# Mezclarlos (credenciales de una cuenta con el estado de otra) puede hacer que Terraform dé por
# borrados los recursos de la otra cuenta y sobrescriba su estado.
#
#   ./run.sh <staging|prod> init
#   ./run.sh <staging|prod> plan|apply|import|output [opciones de terraform]
set -euo pipefail
cd "$(dirname "$0")"

env="${1:-}"
cmd="${2:-}"
case "$env" in
  staging) profile=fea-staging; state=terraform.tfstate;      varfile=staging.tfvars ;;
  prod)    profile=fea-prod;    state=terraform.prod.tfstate; varfile=prod.tfvars ;;
  *) echo "uso: ./run.sh <staging|prod> <init|plan|apply|import|output> [opciones]" >&2; exit 2 ;;
esac
[ -n "$cmd" ] || { echo "falta el subcomando de terraform" >&2; exit 2; }
shift 2

fail() { echo "error: $*" >&2; exit 1; }

# terraform.tfvars y *.auto.tfvars se cargan solos y mezclarían entornos.
if [ -e terraform.tfvars ] || compgen -G "*.auto.tfvars" >/dev/null; then
  fail "existe terraform.tfvars o *.auto.tfvars; renómbralo a $varfile (cada entorno usa su archivo)"
fi
[ -f "$varfile" ] || fail "falta $varfile (copia terraform.tfvars.example y rellénalo)"

declared=$(sed -n 's/^[[:space:]]*aws_account_id[[:space:]]*=[[:space:]]*"\([0-9]\{12\}\)".*/\1/p' "$varfile")
[ -n "$declared" ] || fail "$varfile no define aws_account_id"
actual=$(AWS_PROFILE="$profile" aws sts get-caller-identity --query Account --output text) \
  || fail "no pude identificar la cuenta del perfil $profile (¿aws sso login --profile $profile?)"
[ "$declared" = "$actual" ] \
  || fail "el perfil $profile es la cuenta $actual, pero $varfile apunta a la cuenta $declared"

is_prod=false
grep -Eq '^[[:space:]]*environment[[:space:]]*=[[:space:]]*"prod"' "$varfile" && is_prod=true
if [ "$env" = prod ] && [ "$is_prod" = false ]; then fail "$varfile debe definir environment = \"prod\""; fi
if [ "$env" = staging ] && [ "$is_prod" = true ]; then fail "$varfile es de staging y define environment = \"prod\""; fi

if [ -s "$state" ] && ! grep -q "arn:aws:iam::${actual}:oidc-provider/" "$state"; then
  fail "$state no contiene recursos de la cuenta $actual; es el estado de otro entorno"
fi

export AWS_PROFILE="$profile" AWS_REGION=us-east-2
case "$cmd" in
  init)                   exec terraform init "$@" ;;
  output)                 exec terraform output -state="$state" "$@" ;;
  plan|apply|import)      exec terraform "$cmd" -state="$state" -var-file="$varfile" "$@" ;;
  *) fail "subcomando no admitido: $cmd (usa init, plan, apply, import u output)" ;;
esac
