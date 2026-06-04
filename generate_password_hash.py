#!/usr/bin/env python3
"""
Script pour générer un hash bcrypt de mot de passe
Usage: python generate_password_hash.py
"""

import sys
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def main():
    print("=" * 60)
    print("Générateur de hash de mot de passe pour configuration")
    print("=" * 60)
    print()
    
    if len(sys.argv) > 1:
        password = sys.argv[1]
    else:
        password = input("Entrez le mot de passe à hasher : ")
    
    if not password:
        print("❌ Erreur : Mot de passe vide")
        sys.exit(1)
    
    # Générer le hash
    password_hash = pwd_context.hash(password)
    
    print()
    print("✅ Hash généré avec succès !")
    print()
    print("-" * 60)
    print("Hash bcrypt :")
    print(password_hash)
    print("-" * 60)
    print()
    print("📋 Pour utiliser ce hash, ajoutez-le dans votre fichier .env :")
    print()
    print(f"CONFIG_PASSWORD_HASH={password_hash}")
    print()
    print("Ou modifiez la variable CONFIG_PASSWORD_HASH dans main.py")
    print()


if __name__ == "__main__":
    main()
