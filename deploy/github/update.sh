#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ENV_FILE="$ROOT_DIR/.env.github-minimal"
COMPOSE_FILE="$ROOT_DIR/deploy/github/docker-compose.yml"
BRANCH=""

usage() {
  cat <<'EOF'
Mise a jour Velopointage depuis GitHub (mode 1 route)

Usage:
  ./deploy/github/update.sh [options]

Options:
  --branch <nom>      Branche Git a mettre a jour (auto si omis)
  -h, --help          Affiche cette aide

Comportement:
  1) Verifie que le depot local est propre
  2) Recupere les dernieres modifications GitHub
  3) Met a jour la branche locale
  4) Redemarre l'application avec rebuild Docker
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --branch)
      BRANCH="${2:-}"
      shift 2
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
    exit 1
  fi
}

require_cmd git
require_cmd docker

if ! docker compose version >/dev/null 2>&1; then
  echo "Erreur: docker compose plugin introuvable."
  exit 1
fi

if [[ ! -d "$ROOT_DIR/.git" ]]; then
  echo "Erreur: depot git introuvable dans $ROOT_DIR"
  exit 1
fi

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Erreur: fichier env introuvable: $ENV_FILE"
  echo "Lance d'abord l'installation: ./deploy/github/install.sh"
  exit 1
fi

if [[ ! -f "$COMPOSE_FILE" ]]; then
  echo "Erreur: fichier compose introuvable: $COMPOSE_FILE"
  exit 1
fi

cd "$ROOT_DIR"

if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "Erreur: des modifications locales non committees sont presentes."
  echo "Commit/stash tes changements puis relance la mise a jour."
  exit 1
fi

echo "Recherche des mises a jour GitHub..."
git fetch --prune origin

if [[ -z "$BRANCH" ]]; then
  BRANCH="$(git symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null | sed 's#^origin/##' || true)"
fi

if [[ -z "$BRANCH" ]]; then
  BRANCH="main"
fi

echo "Mise a jour de la branche locale: $BRANCH"

current_branch="$(git rev-parse --abbrev-ref HEAD)"
if [[ "$current_branch" != "$BRANCH" ]]; then
  git checkout "$BRANCH"
fi

git pull --ff-only origin "$BRANCH"

echo "Redeploiement Docker en cours..."
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" up -d --build

echo
echo "Mise a jour terminee."
echo "Verification rapide conseillee:"
echo "- curl -fsS http://localhost:62000/api/app_version"
echo "- docker compose --env-file .env.github-minimal -f deploy/github/docker-compose.yml ps"