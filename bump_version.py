#!/usr/bin/env python3
"""
Script pour incrémenter automatiquement la version du cache PWA
À exécuter avant chaque déploiement pour forcer la mise à jour des clients
"""

import re
import sys
from pathlib import Path


def bump_version(sw_path: Path, bump_type: str = "patch") -> str:
    """
    Incrémente la version dans le fichier sw.js
    
    Args:
        sw_path: Chemin vers le fichier sw.js
        bump_type: Type d'incrémentation (major, minor, patch)
    
    Returns:
        Nouvelle version
    """
    # Lire le fichier
    content = sw_path.read_text(encoding='utf-8')
    
    # Trouver la version actuelle
    pattern = r"const CACHE_VERSION = '(\d+)\.(\d+)\.(\d+)';"
    match = re.search(pattern, content)
    
    if not match:
        print("❌ Erreur: Version non trouvée dans sw.js")
        sys.exit(1)
    
    major, minor, patch = map(int, match.groups())
    
    # Incrémenter selon le type
    if bump_type == "major":
        major += 1
        minor = 0
        patch = 0
    elif bump_type == "minor":
        minor += 1
        patch = 0
    else:  # patch
        patch += 1
    
    new_version = f"{major}.{minor}.{patch}"
    
    # Remplacer la version
    new_content = re.sub(
        pattern,
        f"const CACHE_VERSION = '{new_version}';",
        content
    )
    
    # Écrire le fichier
    sw_path.write_text(new_content, encoding='utf-8')
    
    return new_version


def main():
    """Point d'entrée principal"""
    # Déterminer le type d'incrémentation
    bump_type = sys.argv[1] if len(sys.argv) > 1 else "patch"
    
    if bump_type not in ["major", "minor", "patch"]:
        print("❌ Usage: python bump_version.py [major|minor|patch]")
        sys.exit(1)
    
    # Chemin vers sw.js
    sw_path = Path(__file__).parent / "static" / "sw.js"
    
    if not sw_path.exists():
        print(f"❌ Erreur: {sw_path} non trouvé")
        sys.exit(1)
    
    # Incrémenter la version
    old_version = re.search(r"const CACHE_VERSION = '([^']+)';", sw_path.read_text())
    old_version = old_version.group(1) if old_version else "inconnue"
    
    new_version = bump_version(sw_path, bump_type)
    
    print(f"✅ Version incrémentée: {old_version} → {new_version}")
    print(f"📝 Fichier mis à jour: {sw_path}")
    print("\n💡 N'oubliez pas de:")
    print("   1. Commiter les changements")
    print("   2. Déployer l'application")
    print("   3. Les clients se mettront à jour automatiquement sous 3 secondes")


if __name__ == "__main__":
    main()
