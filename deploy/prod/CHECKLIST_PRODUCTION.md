# Checklist Production

Cette checklist est conçue pour une mise en service professionnelle sur tout serveur compatible Docker.

## 1. Pré-requis plateforme

- Docker Engine installé et opérationnel
- Docker Compose v2 disponible
- Horloge système synchronisée (NTP)
- Espace disque suffisant pour logs, base et sauvegardes

## 2. Sécurité de base

- Changer les secrets par défaut dans .env
- Restreindre ALLOWED_ORIGINS aux domaines réels
- Activer HTTPS via reverse proxy (Nginx, Traefik, Caddy, Synology)
- Limiter les accès SSH par clés et pare-feu

## 3. Lancement initial

- Créer le fichier .env cible depuis deploy/prod/.env.example
- Démarrer la stack avec deploy/prod/docker-compose.yml
- Vérifier l’état des services avec docker compose ps
- Vérifier les endpoints /api/route_context et /api/app_version

## 4. Vérifications fonctionnelles

- Connexion interface TTV
- Changement du mot de passe admin (obligatoire)
- Affichage des équipes par défaut
- Import d’un GPX test
- Vérification PWA installable

## 5. Exploitation

- Journalisation centralisée ou rotation des logs
- Sauvegarde quotidienne des volumes data et gpx
- Test de restauration mensuel
- Supervision HTTP et alerte sur santé des conteneurs

## 6. Mises à jour

- Sauvegarde avant mise à jour
- Déploiement avec --build --remove-orphans
- Contrôle de version applicative après déploiement
- Vérification des healthchecks après warm-up

## 7. Retour arrière

- Conserver la dernière version stable de l’image
- Documenter la commande de rollback
- Vérifier l’intégrité des données après rollback
