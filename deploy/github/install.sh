#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ENV_FILE="$ROOT_DIR/.env.github-minimal"
ENV_EXAMPLE="$ROOT_DIR/deploy/github/.env.example"
COMPOSE_FILE="$ROOT_DIR/deploy/github/docker-compose.yml"
PREREQ_SCRIPT="$ROOT_DIR/deploy/github/install-prerequisites.sh"
NON_INTERACTIVE=0
FORCE=0
ROUTE_NUMBER=""
ALLOWED_ORIGINS=""
APP_PORT=""

usage() {
  cat <<'EOF'
Installation rapide Velopointage

Usage:
  ./deploy/github/install.sh [options]

Options:
  --route-number <N>   Numero de route (ex: 11)
  --origin <URL>       URL publique autorisee (ALLOWED_ORIGINS)
  --port <PORT>        Port HTTP local (defaut: 62000)
  --non-interactive    Lance sans questions (valeurs par defaut si non fournies)
  --force              Ecrase les valeurs deja presentes dans .env.github-minimal
  -h, --help           Affiche cette aide

Exemples:
  ./deploy/github/install.sh
  ./deploy/github/install.sh --route-number 11 --origin https://route11.example.org --port 62010
  ./deploy/github/install.sh --non-interactive --route-number 62 --origin https://route62.example.org
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --route-number)
      ROUTE_NUMBER="${2:-}"
      shift 2
      ;;
    --origin)
      ALLOWED_ORIGINS="${2:-}"
      shift 2
      ;;
    --port)
      APP_PORT="${2:-}"
      shift 2
      ;;
    --non-interactive)
      NON_INTERACTIVE=1
      shift
      ;;
    --force)
      FORCE=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Erreur: option inconnue: $1"
      echo
      usage
      exit 1
      ;;
  esac
done

require_cmd() {
  local cmd="$1"
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "Erreur: commande manquante: $cmd"
    if [[ "$cmd" == "docker" ]]; then
      echo "Sur Linux, tu peux preparer la machine avec: ./deploy/github/install-prerequisites.sh"
    fi
    exit 1
  fi
}

set_env_value() {
  local key="$1"
  local value="$2"

  if grep -q "^${key}=" "$ENV_FILE"; then
    sed -i.bak "s|^${key}=.*|${key}=${value}|" "$ENV_FILE"
  else
    printf '\n%s=%s\n' "$key" "$value" >> "$ENV_FILE"
  fi
}

normalize_compose_escaped_value() {
  local key="$1"
  local current_value

  current_value="$(grep "^${key}=" "$ENV_FILE" | head -n 1 | cut -d= -f2- || true)"

  if [[ -n "$current_value" && "$current_value" == \$2* && "$current_value" != \$\$* ]]; then
    current_value="${current_value//\$/\$\$}"
    sed -i.bak "s|^${key}=.*|${key}=${current_value}|" "$ENV_FILE"
  fi
}

is_port_in_use() {
  local port="$1"

  if command -v lsof >/dev/null 2>&1; then
    lsof -nP -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1
    return $?
  fi

  if command -v ss >/dev/null 2>&1; then
    ss -ltn | awk '{print $4}' | grep -E "(^|:)${port}$" >/dev/null 2>&1
    return $?
  fi

  if command -v netstat >/dev/null 2>&1; then
    netstat -lnt 2>/dev/null | awk '{print $4}' | grep -E "(^|:)${port}$" >/dev/null 2>&1
    return $?
  fi

  return 1
}

generate_token() {
  if command -v openssl >/dev/null 2>&1; then
    openssl rand -hex 32
  else
    python3 - <<'PY'
import secrets
print(secrets.token_hex(32))
PY
  fi
}

require_cmd docker

if ! docker compose version >/dev/null 2>&1; then
  echo "Erreur: docker compose plugin introuvable."
  echo "Sur Linux, tu peux preparer la machine avec: ./deploy/github/install-prerequisites.sh"
  exit 1
fi

if [[ ! -f "$COMPOSE_FILE" ]]; then
  echo "Erreur: fichier compose introuvable: $COMPOSE_FILE"
  exit 1
fi

if [[ ! -f "$ENV_FILE" ]]; then
  cat "$ENV_EXAMPLE" > "$ENV_FILE"
fi

if [[ "$NON_INTERACTIVE" -eq 0 ]]; then
  echo "Installation guidee Velopointage"
  echo ""
  echo "Ce programme va preparer votre configuration"
  echo "et lancer l'application sur ce serveur avec des valeurs adaptees a votre route."
  echo ""
  echo "Si Docker n'est pas encore installe sur une machine Linux, lance d'abord :"
  echo "./deploy/github/install-prerequisites.sh"
  echo ""
  echo "Trois informations vont vous etre demandees :"
  echo "- le numero de route"
  echo "- l'adresse web publique de l'application"
  echo "- le port local a utiliser sur ce serveur"
  echo ""
  echo "Laisser vide pour conserver la valeur proposee."
  echo

  if [[ -z "$ROUTE_NUMBER" ]]; then
    read -r -p "Numero de route [00]: " ROUTE_NUMBER
  fi

  if [[ -z "$ROUTE_NUMBER" ]]; then
    ROUTE_NUMBER="00"
  fi

  ROUTE_NUMBER="${ROUTE_NUMBER// /}"
else
  ROUTE_NUMBER="${ROUTE_NUMBER:-00}"
  ROUTE_NUMBER="${ROUTE_NUMBER// /}"
fi

if [[ ! "$ROUTE_NUMBER" =~ ^[0-9]+$ ]]; then
  echo "Erreur: le numero de route doit contenir uniquement des chiffres."
  exit 1
fi

route_slug="route${ROUTE_NUMBER}"
route_name="Route ${ROUTE_NUMBER}"
default_origin="https://${route_slug}.example.org"

if [[ "$NON_INTERACTIVE" -eq 0 ]]; then
  if [[ -z "$ALLOWED_ORIGINS" ]]; then
    read -r -p "Adresse web publique (ALLOWED_ORIGINS) [${default_origin}]: " ALLOWED_ORIGINS
  fi
  ALLOWED_ORIGINS="${ALLOWED_ORIGINS:-$default_origin}"
else
  ALLOWED_ORIGINS="${ALLOWED_ORIGINS:-$default_origin}"
fi

if [[ "$NON_INTERACTIVE" -eq 0 ]]; then
  if [[ -z "$APP_PORT" ]]; then
    read -r -p "Port HTTP local [62000]: " APP_PORT
  fi
  APP_PORT="${APP_PORT:-62000}"
else
  APP_PORT="${APP_PORT:-62000}"
fi

if [[ ! "$APP_PORT" =~ ^[0-9]+$ ]]; then
  echo "Erreur: le port doit etre numerique."
  exit 1
fi

if is_port_in_use "$APP_PORT"; then
  echo "Erreur: le port ${APP_PORT} est deja utilise sur ce serveur."
  echo "Choisis un autre port avec --port ou relance le script."
  exit 1
fi

admin_key="$(generate_token)"
session_secret="$(generate_token)"

set_env_value "APP_PORT" "$APP_PORT"
set_env_value "ROUTE_NAME" "$route_name"
set_env_value "ROUTE_SLUG" "$route_slug"
set_env_value "ALLOWED_ORIGINS" "$ALLOWED_ORIGINS"
set_env_value "ADMIN_KEY" "$admin_key"
set_env_value "SESSION_SECRET" "$session_secret"
normalize_compose_escaped_value "CONFIG_PASSWORD_HASH"

rm -f "$ENV_FILE.bak"

mkdir -p "$ROOT_DIR/instances/default/data" "$ROOT_DIR/instances/default/gpx"

echo
echo "Deploiement en cours..."
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" up -d --build

echo
echo "Installation terminee"
echo "- URL locale: http://localhost:${APP_PORT}"
echo "- Route: ${route_name} (${route_slug})"
echo "- Mot de passe admin par defaut: pelevtt"
echo "- Mise a jour facile ensuite: ./deploy/github/update.sh"
echo
echo "Action requise: change le mot de passe admin apres la premiere connexion."
