# 📱 Installation des Applications PWA

## Deux applications distinctes

Le système PéléVTT 62 propose deux applications installables séparément :

### 1. 🎯 Application TTV

**URL d'accès** : `https://votre-domaine.com/static/index.html`

**Pour qui** : TTV, coordinateurs, observateurs

**Fonctionnalités** :
- ✅ Carte en temps réel avec toutes les équipes
- ✅ Suivi des passages GPS
- ✅ Configuration des équipes et tracés GPX
- ✅ Interface observateur pour enregistrer des passages
- ✅ Statistiques et historique complet

**Installation sur mobile** :
- **iOS** : Safari → Partager → "Sur l'écran d'accueil"
- **Android** : Chrome → Menu (⋮) → "Installer l'application"

**Icône** : PéléVTT 62 (logo principal)

---

### 2. 🚴 Application anim

**URL d'accès** : `https://votre-domaine.com/static/anim.html`

**Pour qui** : anim d'équipes sur le terrain

**Fonctionnalités** :
- ✅ Sélection de son équipe
- ✅ Déclaration d'état simplifié (pause, temps spi, repas, on roule)
- ✅ Demande d'assistance (vélo ou médicale) avec SMS automatique
- ✅ GPS automatique pour géolocalisation
- ✅ Interface ultra-simple et rapide

**Installation sur mobile** :
- **iOS** : Safari → Partager → "Sur l'écran d'accueil"
- **Android** : Chrome → Menu (⋮) → "Installer l'application"

**Icône** : Anim PéléVTT 62

---

## 🔄 Mises à jour automatiques

Les deux applications se mettent à jour automatiquement :
- Au lancement si une nouvelle version est disponible
- Ou toutes les heures si l'app reste ouverte
- Message "Nouvelle version disponible !" avec rechargement après 3s

**Aucune action requise de la part des utilisateurs** ✨

---

## 💡 Conseils d'utilisation

### Pour les TTV

1. Installer l'**Application TTV** sur votre téléphone/tablette
2. L'utiliser pour :
   - Suivre toutes les équipes en temps réel
   - Configurer les traces GPX
   - Gérer les équipes et couleurs
   - Enregistrer des passages manuellement si besoin

### Pour les anim

1. Installer l'**Application anim** sur votre téléphone
2. Au premier lancement :
   - Entrer votre nom
   - Sélectionner votre équipe
   - Autoriser l'accès à la localisation GPS
3. Pendant le parcours :
   - Déclarer l'état de votre équipe en un clic
   - Demander assistance si besoin (SMS automatique avec position)

---

## 🛠️ Fonctionnement hors ligne

Les deux applications fonctionnent en mode hors ligne :
- Les pages et ressources sont mises en cache
- L'interface reste disponible sans connexion
- Les actions sont enregistrées localement et synchronisées quand la connexion revient

**Note** : Certaines fonctionnalités nécessitent une connexion :
- Envoi de passages/états en temps réel
- Affichage carte avec fonds de carte
- Synchronisation entre appareils

---

## ❓ FAQ

### Peut-on installer les deux applications ?
Oui ! Elles sont complètement indépendantes. Un TTV peut avoir les deux sur son téléphone.

### Comment différencier les deux applications ?
- Les noms sont différents : "PéléVTT 62" vs "Anim PéléVTT 62"
- Les interfaces sont distinctes dès l'ouverture

### Faut-il désinstaller pour mettre à jour ?
Non ! Les mises à jour sont automatiques. L'application se recharge simplement avec la nouvelle version.

### Que se passe-t-il si je perds la connexion ?
L'application continue de fonctionner localement. Les données seront synchronisées dès que la connexion revient.

### Comment désinstaller ?
- **iOS** : Maintenir l'icône appuyée → "Supprimer l'app"
- **Android** : Maintenir l'icône appuyée → "Désinstaller"

---

## 🚀 Pour les administrateurs

### Déployer les deux applications

Les deux applications sont servies automatiquement par le même serveur. Aucune configuration spéciale nécessaire.

### URLs à partager

Créez des QR codes ou des liens directs :
- TTV : `https://votre-domaine.com/static/index.html`
- anim : `https://votre-domaine.com/static/anim.html`

### Forcer la mise à jour

```bash
python3 bump_version.py
git add static/sw.js
git commit -m "Bump version"
# Déployer
```

Les deux applications se mettront à jour automatiquement pour tous les utilisateurs !
