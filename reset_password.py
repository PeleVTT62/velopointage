#!/usr/bin/env python3
"""
Script pour réinitialiser le mot de passe de configuration
À exécuter dans le conteneur Docker ou localement avec les dépendances installées
"""

import json
import os
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Mot de passe par défaut
DEFAULT_PASSWORD = "aaqq"
CONFIG_FILE = os.path.join("data", "config.json")


def reset_password():
    print("=" * 60)
    print("Réinitialisation du mot de passe")
    print("=" * 60)
    print()
    
    # Demander le nouveau mot de passe
    import sys
    if len(sys.argv) > 1:
        new_password = sys.argv[1]
        print(f"Nouveau mot de passe : {new_password}")
    else:
        use_default = input(f"Utiliser le mot de passe par défaut '{DEFAULT_PASSWORD}' ? (o/n) : ").lower()
        if use_default == 'o':
            new_password = DEFAULT_PASSWORD
        else:
            new_password = input("Entrez le nouveau mot de passe : ")
    
    if not new_password:
        print("❌ Erreur : Mot de passe vide")
        return
    
    # Générer le hash
    print("\n🔐 Génération du hash...")
    password_hash = pwd_context.hash(new_password)
    
    # Créer le dossier data si nécessaire
    os.makedirs("data", exist_ok=True)
    
    # Sauvegarder dans config.json
    config_data = {}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                config_data = json.load(f)
        except Exception as e:
            print(f"⚠️  Erreur lecture config existant : {e}")
    
    config_data['password_hash'] = password_hash
    
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config_data, f, indent=2)
    
    print()
    print("✅ Mot de passe réinitialisé avec succès !")
    print()
    print(f"📁 Fichier : {CONFIG_FILE}")
    print(f"🔑 Mot de passe : {new_password}")
    print(f"🔐 Hash : {password_hash[:30]}...")
    print()
    print("🔄 Redémarrez l'application pour appliquer les changements")
    print()
    
    # Afficher les commandes de redémarrage
    print("Commandes de redémarrage :")
    print("  Docker : sudo docker compose restart app")
    print("  Local  : Ctrl+C puis relancer uvicorn")
    print()


if __name__ == "__main__":
    try:
        reset_password()
    except KeyboardInterrupt:
        print("\n\n❌ Annulé par l'utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur : {e}")
        import traceback
        traceback.print_exc()
