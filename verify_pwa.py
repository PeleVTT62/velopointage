#!/usr/bin/env python3
"""
Script de vérification de la configuration PWA
Vérifie que tout est correct avant le déploiement
"""

import json
import re
from pathlib import Path


def check_service_worker():
    """Vérifie la configuration du Service Worker"""
    sw_path = Path("static/sw.js")
    
    if not sw_path.exists():
        return False, "❌ Fichier sw.js non trouvé"
    
    content = sw_path.read_text(encoding='utf-8')
    
    # Vérifier la version
    version_match = re.search(r"const CACHE_VERSION = '([^']+)';", content)
    if not version_match:
        return False, "❌ CACHE_VERSION non trouvée dans sw.js"
    
    version = version_match.group(1)
    
    # Vérifier que les ressources essentielles sont cachées
    required_assets = [
        '/static/index.html',
        '/static/anim.html',
        '/static/css/common.css',
        '/static/js/utils.js'
    ]
    
    missing_assets = []
    for asset in required_assets:
        if asset not in content:
            missing_assets.append(asset)
    
    if missing_assets:
        return False, f"❌ Ressources manquantes dans STATIC_ASSETS : {', '.join(missing_assets)}"
    
    return True, f"✅ Service Worker OK (version {version})"


def check_manifest(manifest_path, expected_name):
    """Vérifie un fichier manifest"""
    if not manifest_path.exists():
        return False, f"❌ Fichier {manifest_path.name} non trouvé"
    
    try:
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
        
        # Vérifier les propriétés essentielles
        required_fields = ['name', 'short_name', 'start_url', 'icons', 'theme_color', 'background_color', 'display']
        missing_fields = [field for field in required_fields if field not in manifest]
        
        if missing_fields:
            return False, f"❌ {manifest_path.name} : champs manquants : {', '.join(missing_fields)}"
        
        # Vérifier que les icônes existent
        for icon in manifest['icons']:
            # Les icônes peuvent avoir un chemin /static/ ou relatif
            icon_src = icon['src']
            if icon_src.startswith('/static/'):
                icon_path = Path(icon_src.lstrip('/'))
            else:
                icon_path = Path('static') / icon_src.lstrip('/')
            
            if not icon_path.exists():
                return False, f"❌ {manifest_path.name} : icône manquante : {icon['src']} (cherché dans {icon_path})"
        
        # Vérifier le nom
        if expected_name not in manifest['name']:
            return False, f"⚠️ {manifest_path.name} : nom attendu contenant '{expected_name}', trouvé '{manifest['name']}'"
        
        return True, f"✅ {manifest_path.name} OK ({manifest['name']})"
    
    except json.JSONDecodeError:
        return False, f"❌ {manifest_path.name} : JSON invalide"
    except Exception as e:
        return False, f"❌ {manifest_path.name} : erreur : {str(e)}"


def check_html_sw_registration(html_path):
    """Vérifie que le HTML enregistre le Service Worker"""
    if not html_path.exists():
        return False, f"❌ Fichier {html_path.name} non trouvé"
    
    content = html_path.read_text(encoding='utf-8')
    
    # Vérifier l'enregistrement du SW
    if "serviceWorker.register" not in content:
        return False, f"❌ {html_path.name} : pas d'enregistrement du Service Worker"
    
    if "/static/sw.js" not in content:
        return False, f"❌ {html_path.name} : mauvais chemin vers sw.js"
    
    # Vérifier la gestion des mises à jour
    if "updatefound" not in content:
        return False, f"⚠️ {html_path.name} : pas de gestion de updatefound"
    
    if "SKIP_WAITING" not in content:
        return False, f"⚠️ {html_path.name} : pas de message SKIP_WAITING"
    
    return True, f"✅ {html_path.name} : enregistrement SW OK"


def main():
    """Point d'entrée principal"""
    print("🔍 Vérification de la configuration PWA\n")
    
    checks = []
    
    # Vérifier le Service Worker
    checks.append(check_service_worker())
    
    # Vérifier les manifests
    checks.append(check_manifest(Path("site.webmanifest"), "PéléVTT"))
    checks.append(check_manifest(Path("site_anim.webmanifest"), "Anim"))
    
    # Vérifier l'enregistrement du SW dans les HTML
    checks.append(check_html_sw_registration(Path("static/index.html")))
    checks.append(check_html_sw_registration(Path("static/anim.html")))
    
    # Afficher les résultats
    print("\n📋 Résultats :\n")
    all_ok = True
    for success, message in checks:
        print(f"  {message}")
        if not success:
            all_ok = False
    
    print("\n" + "="*60)
    if all_ok:
        print("✅ Toutes les vérifications sont passées !")
        print("📦 Vous pouvez déployer en toute sécurité.")
    else:
        print("⚠️ Certaines vérifications ont échoué.")
        print("🔧 Corrigez les erreurs avant de déployer.")
        return 1
    
    print("="*60)
    return 0


if __name__ == "__main__":
    exit(main())
