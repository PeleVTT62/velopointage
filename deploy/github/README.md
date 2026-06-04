# Déploiement GitHub minimal (1 route)

Ce mode permet de déployer rapidement une route sur tout serveur compatible Docker.

## Compatibilité serveur

Compatible avec tout environnement disposant de:

- Docker Engine
- Docker Compose v2

Exemples courants: VM Linux, serveur bare-metal Linux, Synology Container Manager.

## Objectif

- Installation rapide et guidée
- Valeurs par défaut opérationnelles
- Aucun GPX préchargé
- Configuration claire, sans complexité inutile

## 1. Récupérer le dépôt

```bash
git clone <URL_DU_REPO>
cd velopointage
```

## 2. Installer les prérequis sur Linux si besoin

Sur Debian, Ubuntu et la plupart des VPS Linux, un script prépare automatiquement la machine:

```bash
./deploy/github/install-prerequisites.sh
```

Ce script installe:

- curl
- git
- openssl
- Docker Engine
- Docker Compose v2

## 3. Installation guidée recommandée

```bash
./deploy/github/install.sh
```

Le script réalise automatiquement:

- création ou mise à jour de .env.github-minimal
- génération des secrets ADMIN_KEY et SESSION_SECRET
- paramétrage route et URL publique
- questions guidées sur le numéro de route, l'adresse web et le port
- création des dossiers de données
- déploiement Docker

Mot de passe admin par défaut de l'interface configuration: pelevtt

## 4. Vérifier le service

```bash
curl -fsS http://localhost:62000/api/route_context
curl -fsS http://localhost:62000/api/app_version
```

## 5. Actions obligatoires après installation

- Changer le mot de passe admin à la première connexion
- Vérifier ALLOWED_ORIGINS avec le domaine réel
- Conserver .env.github-minimal hors partage public

## 6. Notes techniques

- Les équipes par défaut sont injectées automatiquement si la base est vide.
- Le dossier instances/default/gpx démarre vide.
- Les mises à jour applicatives se font via docker compose up -d --build.

## 7. Mise à jour facile depuis GitHub

Commande recommandée:

```bash
./deploy/github/update.sh
```

Le script fait automatiquement:

- vérification de l'état local Git (pas de changements non commités)
- récupération des dernières modifications depuis GitHub
- mise à jour de la branche locale
- redéploiement Docker avec rebuild

Option utile:

```bash
./deploy/github/update.sh --branch main
```
