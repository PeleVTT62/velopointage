#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Installation des prerequis Velopointage pour Linux

Usage:
  ./deploy/github/install-prerequisites.sh

Ce script prepare une machine Linux pour l'installateur guide:
- curl
- git
- openssl
- Docker Engine
- Docker Compose v2

Il cible en priorite Debian et Ubuntu, et fonctionne aussi sur
les distributions prises en charge par le script officiel Docker.
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if [[ "$(uname -s)" != "Linux" ]]; then
  echo "Erreur: ce script est prevu pour Linux uniquement."
  exit 1
fi

if [[ -f /etc/os-release ]]; then
  # shellcheck disable=SC1091
  source /etc/os-release
  distro_name="${PRETTY_NAME:-${NAME:-Linux}}"
else
  distro_name="Linux"
fi

run_as_root() {
  if [[ "${EUID}" -eq 0 ]]; then
    "$@"
    return
  fi

  if command -v sudo >/dev/null 2>&1; then
    sudo "$@"
    return
  fi

  echo "Erreur: sudo est requis pour installer les prerequis."
  exit 1
}

install_base_tools() {
  if command -v apt-get >/dev/null 2>&1; then
    run_as_root apt-get update
    run_as_root apt-get install -y curl git openssl ca-certificates
    return
  fi

  if command -v dnf >/dev/null 2>&1; then
    run_as_root dnf install -y curl git openssl ca-certificates
    return
  fi

  if command -v yum >/dev/null 2>&1; then
    run_as_root yum install -y curl git openssl ca-certificates
    return
  fi

  if command -v zypper >/dev/null 2>&1; then
    run_as_root zypper --non-interactive install curl git openssl ca-certificates
    return
  fi

  if command -v pacman >/dev/null 2>&1; then
    run_as_root pacman -Sy --noconfirm curl git openssl ca-certificates
    return
  fi

  echo "Erreur: gestionnaire de paquets non pris en charge automatiquement."
  echo "Installe manuellement curl, git, openssl, Docker Engine et Docker Compose v2."
  exit 1
}

install_docker() {
  if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
    return
  fi

  tmp_script="$(mktemp)"
  trap 'rm -f "$tmp_script"' EXIT

  curl -fsSL https://get.docker.com -o "$tmp_script"
  run_as_root sh "$tmp_script"
}

print_post_install() {
  echo ""
  echo "Prerequis installes pour ${distro_name}."

  if getent group docker >/dev/null 2>&1 && id -nG "$USER" 2>/dev/null | grep -qw docker; then
    echo "Le groupe docker est deja actif pour l'utilisateur courant."
  elif getent group docker >/dev/null 2>&1; then
    echo ""
    echo "Pour utiliser Docker sans sudo, execute ensuite :"
    echo "  sudo usermod -aG docker $USER"
    echo "Puis reconnecte-toi a ta session shell."
  fi

  echo ""
  echo "Tu peux ensuite lancer :"
  echo "  ./deploy/github/install.sh"
}

echo "Preparation des prerequis Velopointage sur ${distro_name}..."
install_base_tools
install_docker
print_post_install
