import os
import json
import math
import sqlite3
import asyncio
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import (
    FastAPI,
    HTTPException,
    UploadFile,
    File,
    WebSocket,
    WebSocketDisconnect,
    Path,
    Query,
    APIRouter,
    Depends,
    Header,
    status,
    Cookie,
    Response
)
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Body
from pydantic import BaseModel
from passlib.context import CryptContext

import gpxpy
import gpxpy.gpx
import httpx
import redis.asyncio as redis


# -----------------------------------
# Config
# -----------------------------------
APP_PORT = int(os.getenv("APP_PORT", "62000"))
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
ROUTE_NAME = os.getenv("ROUTE_NAME", "Route 62")
ROUTE_SLUG = os.getenv("ROUTE_SLUG", "route62")
REDIS_CHANNEL = os.getenv("REDIS_CHANNEL", f"passages:{ROUTE_SLUG}")
ADMIN_KEY = os.getenv("ADMIN_KEY", "0d803d527bf79cb747aeb51c42c15ad017e0d9f7fb3cbb7b6afa90b952e4fb4f")
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "https://api.pelevtt.cloud:443,http://pelevtt.cloud").split(",")
REDIS_ENABLED = os.getenv("REDIS_ENABLED", "true").lower() == "true"
GEO_SECURITY_RADIUS_KM = float(os.getenv("GEO_SECURITY_RADIUS_KM", "100"))

DATA_DIR = os.getenv("DATA_DIR", "data")
STATIC_DIR = os.getenv("STATIC_DIR", "static")
GPX_DIR = os.getenv("GPX_DIR", os.path.join(STATIC_DIR, "gpx"))
GPX_FILE = os.path.join(GPX_DIR, "trace.gpx")
DB_FILE = os.getenv("DB_FILE", os.path.join(DATA_DIR, "db.sqlite"))
CONFIG_FILE = os.getenv("CONFIG_FILE", os.path.join(DATA_DIR, "config.json"))


def get_cache_version() -> str:
        """Lit la version du cache dans le Service Worker."""
        sw_path = os.path.join(STATIC_DIR, "sw.js")
        try:
            with open(sw_path, "r", encoding="utf-8") as f:
                    content = f.read()
            import re
            match = re.search(r"const CACHE_VERSION = '([^']+)';", content)
            if match:
                    return match.group(1)
        except Exception:
            pass
        return "inconnue"


def render_index_html() -> str:
    """Injecte la route et la version dans la page d'accueil HTML."""
    index_path = os.path.join(STATIC_DIR, "index.html")
    with open(index_path, "r", encoding="utf-8") as f:
        html = f.read()

    route_code = get_route_code()
    cache_version = get_cache_version()

    html = html.replace("Pélé VTT 62", f"Pélé VTT {route_code}")
    html = html.replace(
        '<p class="version" id="app-version" style="font-size: 0.7rem; color: rgba(0,0,0,0.3); margin-top: 0.5rem;"></p>',
        f'<p class="version" id="app-version" style="font-size: 0.7rem; color: rgba(0,0,0,0.3); margin-top: 0.5rem;">v{cache_version}</p>'
    )

    return html

# Configuration sécurité authentification
def load_password_hash() -> str:
    """Charge le hash du mot de passe depuis le fichier config ou la variable d'environnement"""
    # 1. Vérifier si un fichier de config existe
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                config_data = json.load(f)
                if 'password_hash' in config_data:
                    return config_data['password_hash']
        except Exception as e:
            print(f"[WARNING] Erreur lecture config.json: {e}")
    
    # 2. Sinon, utiliser la variable d'environnement
    return os.getenv(
        "CONFIG_PASSWORD_HASH",
        # Hash par défaut de 'aaqq' - À CHANGER EN PRODUCTION
        "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMeshqdh.h5CjQqgPJ0d8/Qg.m"
    )

def get_gpx_key_points() -> Dict[str, Dict[str, float]]:
    """Extrait les points clés du GPX actif (départ, arrivée, pause midi)"""
    try:
        active_path = os.path.join(GPX_DIR, "active_gpx.json")
        if not os.path.exists(active_path):
            return {}
        
        with open(active_path, "r") as f:
            active_data = json.load(f)
            active_gpx = active_data.get("active")
        
        if not active_gpx:
            return {}
        
        gpx_path = os.path.join(GPX_DIR, active_gpx)
        if not os.path.exists(gpx_path):
            return {}
        
        with open(gpx_path, "r") as gpx_file:
            gpx = gpxpy.parse(gpx_file)
        
        points = {}
        
        # Récupérer tous les points du tracé
        all_points = []
        for track in gpx.tracks:
            for segment in track.segments:
                all_points.extend(segment.points)
        
        if all_points:
            # Point de départ
            start = all_points[0]
            points["depart"] = {"latitude": start.latitude, "longitude": start.longitude}
            
            # Point d'arrivée
            end = all_points[-1]
            points["arrivee"] = {"latitude": end.latitude, "longitude": end.longitude}
        
        # Chercher le waypoint "Ravitaillement chaud" pour la pause midi
        for waypoint in gpx.waypoints:
            if waypoint.name and "ravitaillement chaud" in waypoint.name.lower():
                points["pause_midi"] = {"latitude": waypoint.latitude, "longitude": waypoint.longitude}
                break
        
        # Si pas trouvé, utiliser le milieu du parcours par défaut
        if "pause_midi" not in points and all_points:
            mid_idx = len(all_points) // 2
            mid = all_points[mid_idx]
            points["pause_midi"] = {"latitude": mid.latitude, "longitude": mid.longitude}
        
        return points
    except Exception as e:
        print(f"[ERROR] Erreur extraction points GPX: {e}")
        return {}

def save_password_hash(password_hash: str) -> None:
    """Sauvegarde le hash du mot de passe dans le fichier config"""
    ensure_db_path()  # Créer le dossier data si nécessaire
    config_data = {}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                config_data = json.load(f)
        except Exception:
            pass
    
    config_data['password_hash'] = password_hash
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config_data, f, indent=2)

CONFIG_PASSWORD_HASH = load_password_hash()
SESSION_SECRET = os.getenv("SESSION_SECRET", secrets.token_hex(32))
SESSION_DURATION_HOURS = 24

# Contexte de hachage avec bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Stockage des sessions actives en mémoire (pour production: utiliser Redis)
active_sessions: Dict[str, Dict[str, Any]] = {}

# -----------------------------------
# FastAPI app initialization
# -----------------------------------
app = FastAPI(title=f"Velopointage API - {ROUTE_NAME}")
## L'appel à enable_sqlite_wal() est déplacé après la définition de ensure_db_path()

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# -----------------------------------
# Authentification simple
# -----------------------------------
async def verify_admin_key(x_admin_key: str = Header(None)) -> str:
    """Vérifie la clé d'administration pour les opérations sensibles"""
    if x_admin_key != ADMIN_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Clé d'administration invalide"
        )
    return x_admin_key


# -----------------------------------
# Authentification configuration (sessions)
# -----------------------------------
class LoginRequest(BaseModel):
    password: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class LoginAttempt:
    """Suivi des tentatives de connexion pour rate limiting"""
    def __init__(self):
        self.attempts: Dict[str, List[datetime]] = {}
        self.max_attempts = 5
        self.window_minutes = 15
    
    def is_blocked(self, ip: str) -> bool:
        """Vérifie si une IP est bloquée"""
        if ip not in self.attempts:
            return False
        
        # Nettoyer les anciennes tentatives
        cutoff = datetime.now() - timedelta(minutes=self.window_minutes)
        self.attempts[ip] = [t for t in self.attempts[ip] if t > cutoff]
        
        return len(self.attempts[ip]) >= self.max_attempts
    
    def record_attempt(self, ip: str):
        """Enregistre une tentative de connexion"""
        if ip not in self.attempts:
            self.attempts[ip] = []
        self.attempts[ip].append(datetime.now())
    
    def clear_attempts(self, ip: str):
        """Efface les tentatives pour une IP"""
        if ip in self.attempts:
            del self.attempts[ip]


login_attempts = LoginAttempt()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Vérifie un mot de passe contre son hash"""
    try:
        # Vérifier que le hash n'est pas vide
        if not hashed_password or not hashed_password.strip():
            print("[ERROR] Hash de mot de passe vide ou invalide")
            return False
        
        # Vérifier le format bcrypt basique
        if not hashed_password.startswith("$2b$") and not hashed_password.startswith("$2a$") and not hashed_password.startswith("$2y$"):
            print(f"[ERROR] Hash de mot de passe invalide (format incorrect) : {hashed_password[:20]}...")
            return False
            
        return pwd_context.verify(plain_password, hashed_password)
    except ValueError as e:
        print(f"[ERROR] Erreur de validation du mot de passe (hash invalide) : {e}")
        return False
    except Exception as e:
        print(f"[ERROR] Erreur inattendue lors de la vérification du mot de passe : {e}")
        return False


def create_session_token() -> str:
    """Crée un token de session sécurisé"""
    return secrets.token_urlsafe(32)


def create_session(user_type: str = "config_admin") -> tuple[str, datetime]:
    """Crée une nouvelle session"""
    token = create_session_token()
    expires = datetime.now() + timedelta(hours=SESSION_DURATION_HOURS)
    
    active_sessions[token] = {
        "user_type": user_type,
        "created_at": datetime.now(),
        "expires_at": expires,
        "last_activity": datetime.now()
    }
    
    return token, expires


def verify_session(session_token: Optional[str]) -> bool:
    """Vérifie si une session est valide"""
    if not session_token or session_token not in active_sessions:
        return False
    
    session = active_sessions[session_token]
    
    # Vérifier expiration
    if datetime.now() > session["expires_at"]:
        del active_sessions[session_token]
        return False
    
    # Mettre à jour dernière activité
    session["last_activity"] = datetime.now()
    return True


def require_auth(session_token: Optional[str] = Cookie(None, alias="config_session")) -> str:
    """Dépendance FastAPI pour vérifier l'authentification"""
    if not verify_session(session_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Non authentifié",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return session_token


def is_admin_session(session_token: Optional[str]) -> bool:
    """Indique si le cookie de session admin est valide, sans rendre l'auth obligatoire."""
    return verify_session(session_token)

# -----------------------------------
# Database helpers
# -----------------------------------
def ensure_db_path():
    folder = os.path.dirname(DB_FILE)
    if folder and not os.path.exists(folder):
        os.makedirs(folder, exist_ok=True)

## Suppression du mode WAL, plus d'activation automatique


def init_db() -> None:
    ensure_db_path()
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        # Table passages modifiée : on ajoute ville si besoin
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS passages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                equipe TEXT,
                latitude REAL,
                longitude REAL,
                timestamp TEXT,
                observateur TEXT
            )
            """
        )
        c.execute("PRAGMA table_info(passages)")
        columns = [row[1] for row in c.fetchall()]
        if "ville" not in columns:
            c.execute("ALTER TABLE passages ADD COLUMN ville TEXT DEFAULT NULL")
            conn.commit()

        # Table passages_archives (pour conserver l'historique)
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS passages_archives (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                equipe TEXT,
                latitude REAL,
                longitude REAL,
                timestamp TEXT,
                observateur TEXT,
                ville TEXT,
                date_archivage TEXT
            )
            """
        )

        # Table equipes
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS equipes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT UNIQUE NOT NULL,
                couleur TEXT DEFAULT '#000000',
                etat TEXT DEFAULT 'non partie'
            )
            """
        )
        # Ajouter colonne etat si elle n'existe pas
        c.execute("PRAGMA table_info(equipes)")
        eq_columns = [row[1] for row in c.fetchall()]
        if "etat" not in eq_columns:
            c.execute("ALTER TABLE equipes ADD COLUMN etat TEXT DEFAULT 'non partie'")
            conn.commit()
        
        # Ajouter colonnes latitude et longitude si elles n'existent pas
        c.execute("PRAGMA table_info(equipes)")
        eq_columns = [row[1] for row in c.fetchall()]
        if "latitude" not in eq_columns:
            c.execute("ALTER TABLE equipes ADD COLUMN latitude REAL")
            conn.commit()
        if "longitude" not in eq_columns:
            c.execute("ALTER TABLE equipes ADD COLUMN longitude REAL")
            conn.commit()
        
        # Ajouter colonne ville si elle n'existe pas
        c.execute("PRAGMA table_info(equipes)")
        eq_columns = [row[1] for row in c.fetchall()]
        if "ville" not in eq_columns:
            c.execute("ALTER TABLE equipes ADD COLUMN ville TEXT")
            conn.commit()

              # Valeurs par défaut si vide
        c.execute("SELECT COUNT(*) FROM equipes")
        count = c.fetchone()[0]
        if count == 0:
            default_equipes = [
                ("Equipe 1", "#FF0000", "non partie"),
                ("Equipe 2", "#0000FF", "non partie"),
                ("Equipe 3", "#00AA00", "non partie"),
                ("Equipe 4", "#FFA500", "non partie"),
            ]
            c.executemany(
                "INSERT INTO equipes (nom, couleur, etat) VALUES (?, ?, ?)",
                [(e[0], e[1], e[2]) for e in default_equipes]
            )
            conn.commit()


def get_passages(limit: int = 100) -> List[Dict[str, Any]]:
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM passages ORDER BY timestamp DESC LIMIT ?", (limit,))
        rows = c.fetchall()
    # Note : 'ville' est à l’index 6 (si colonne ajoutée)
    return [
        {
            "id": r[0],
            "equipe": r[1],
            "latitude": r[2],
            "longitude": r[3],
            "timestamp": r[4],
            "observateur": r[5],
            "ville": r[6] if len(r) > 6 else None,
        }
        for r in rows
    ]

def get_passages_archives(date_debut: Optional[str] = None, date_fin: Optional[str] = None, limit: int = 1000) -> List[Dict[str, Any]]:
    """Récupère les passages archivés avec filtrage optionnel par date"""
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        
        query = "SELECT * FROM passages_archives WHERE 1=1"
        params = []
        
        if date_debut:
            query += " AND timestamp >= ?"
            params.append(date_debut)
        
        if date_fin:
            query += " AND timestamp <= ?"
            params.append(date_fin)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        c.execute(query, params)
        rows = c.fetchall()
    
    return [
        {
            "id": r[0],
            "equipe": r[1],
            "latitude": r[2],
            "longitude": r[3],
            "timestamp": r[4],
            "observateur": r[5],
            "ville": r[6] if len(r) > 6 else None,
            "date_archivage": r[7] if len(r) > 7 else None,
        }
        for r in rows
    ]

def get_all_passages_today(include_archives: bool = True) -> List[Dict[str, Any]]:
    """Récupère tous les passages du jour (actuels + archives si demandé)"""
    today = datetime.now().date().isoformat()
    tomorrow = (datetime.now().date() + timedelta(days=1)).isoformat()
    
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        
        # Passages actuels
        c.execute(
            "SELECT * FROM passages WHERE timestamp >= ? AND timestamp < ? ORDER BY timestamp DESC",
            (today, tomorrow)
        )
        current_rows = c.fetchall()
        
        passages = [
            {
                "id": r[0],
                "equipe": r[1],
                "latitude": r[2],
                "longitude": r[3],
                "timestamp": r[4],
                "observateur": r[5],
                "ville": r[6] if len(r) > 6 else None,
                "archived": False,
            }
            for r in current_rows
        ]
        
        # Archives du jour si demandé
        if include_archives:
            c.execute(
                "SELECT * FROM passages_archives WHERE timestamp >= ? AND timestamp < ? ORDER BY timestamp DESC",
                (today, tomorrow)
            )
            archived_rows = c.fetchall()
            
            passages.extend([
                {
                    "id": r[0],
                    "equipe": r[1],
                    "latitude": r[2],
                    "longitude": r[3],
                    "timestamp": r[4],
                    "observateur": r[5],
                    "ville": r[6] if len(r) > 6 else None,
                    "archived": True,
                    "date_archivage": r[7] if len(r) > 7 else None,
                }
                for r in archived_rows
            ])
    
    # Trier par timestamp décroissant
    passages.sort(key=lambda x: x['timestamp'], reverse=True)
    return passages

# --- NOUVELLES FONCTIONS pour équipes en base ---

def get_equipes() -> List[Dict[str, Any]]:
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("SELECT id, nom, couleur, etat, latitude, longitude, ville FROM equipes ORDER BY nom")
        rows = c.fetchall()
    return [
        {
            "id": r[0],
            "nom": r[1],
            "couleur": r[2],
            "etat": r[3],
            "latitude": str(r[4]) if r[4] is not None else "",
            "longitude": str(r[5]) if r[5] is not None else "",
            "ville": r[6] if len(r) > 6 and r[6] is not None else ""
        }
        for r in rows
    ]

def save_equipes(equipes: List[Dict[str, str]]) -> None:
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("DELETE FROM equipes")
        unique_equipes = []
        for e in equipes:
            if not any(ue["nom"] == e["nom"] for ue in unique_equipes):
                unique_equipes.append(e)
        c.executemany(
            "INSERT INTO equipes (nom, couleur, etat) VALUES (?, ?, ?)",
            [(e["nom"], e["couleur"], e.get("etat", "roule")) for e in unique_equipes]
        )
        conn.commit()

# -----------------------------------
# Purge automatique à minuit (cron)
# -----------------------------------
def purge_passages() -> None:
    """Archive les passages du jour puis les supprime de la table principale"""
    try:
        with sqlite3.connect(DB_FILE) as conn:
            c = conn.cursor()
            # 1. Archiver tous les passages actuels
            date_archivage = datetime.now().isoformat()
            c.execute(
                """
                INSERT INTO passages_archives (equipe, latitude, longitude, timestamp, observateur, ville, date_archivage)
                SELECT equipe, latitude, longitude, timestamp, observateur, ville, ?
                FROM passages
                """,
                (date_archivage,)
            )
            archived_count = c.rowcount
            # 2. Supprimer les passages de la table principale
            c.execute("DELETE FROM passages")

            # 3. Réinitialiser les états, positions et villes des équipes
            c.execute("UPDATE equipes SET etat = 'non partie', latitude = NULL, longitude = NULL, ville = NULL")
            conn.commit()
        print(f"[{datetime.now()}] Purge quotidienne : {archived_count} passages archivés et supprimés, états remis à 'non partie'.")
    except Exception as e:
        print(f"Erreur lors de la purge des passages : {e}")


scheduler = BackgroundScheduler()


@app.on_event("startup")
async def startup_event():
    print(f"[Startup] Using DB file at: {os.path.abspath(DB_FILE)}")
    print(f"[Startup] Route context: name={ROUTE_NAME}, slug={ROUTE_SLUG}")
    print(f"[Startup] CORS allowed origins: {ALLOWED_ORIGINS}")
    print(f"[Startup] Redis enabled: {REDIS_ENABLED}")
    print(f"[Startup] Redis channel: {REDIS_CHANNEL}")
    
    # Validation du hash de mot de passe
    if not CONFIG_PASSWORD_HASH or not CONFIG_PASSWORD_HASH.strip():
        print("[WARNING] ⚠️  CONFIG_PASSWORD_HASH est vide ! Utilisation du hash par défaut.")
    elif not CONFIG_PASSWORD_HASH.startswith("$2b$") and not CONFIG_PASSWORD_HASH.startswith("$2a$") and not CONFIG_PASSWORD_HASH.startswith("$2y$"):
        print(f"[WARNING] ⚠️  CONFIG_PASSWORD_HASH a un format invalide (doit commencer par $2b$) : {CONFIG_PASSWORD_HASH[:30]}...")
        print("[WARNING] ⚠️  L'authentification ne fonctionnera pas ! Générez un hash valide avec generate_password_hash.py")
    else:
        print("[Startup] ✅ CONFIG_PASSWORD_HASH validé")
    
    # Init DB
    init_db()
    # Charger points GPX
    load_gpx_points()
    # Start Redis publisher/subscriber (only if enabled)
    global redis_pub, _redis_listener_task
    if REDIS_ENABLED:
        try:
            redis_pub = redis.from_url(REDIS_URL, decode_responses=True)
            _redis_stop.clear()
            _redis_listener_task = asyncio.create_task(redis_listener())
            print("[Startup] Redis listener started")
        except Exception as e:
            print(f"[Startup] Redis connection failed (will run in fallback mode): {e}")
            redis_pub = None
    else:
        print("[Startup] Redis disabled by configuration")
        redis_pub = None

    # Scheduler : start purge if pas déjà lancé
    if not scheduler.get_jobs():
        scheduler.add_job(purge_passages, "cron", hour=0, minute=0)
        scheduler.start()


@app.on_event("shutdown")
async def shutdown_event():
    global redis_pub, _redis_listener_task
    _redis_stop.set()
    if _redis_listener_task:
        _redis_listener_task.cancel()
        try:
            await _redis_listener_task
        except Exception:
            pass
    if redis_pub:
        try:
            await redis_pub.close()
        except Exception:
            pass
    scheduler.shutdown(wait=False)


# -----------------------------------
# Utils: haversine, GPX points
# -----------------------------------


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0  # rayon terre en km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


gpx_track_points: List[tuple] = []
gpx_cumdist: List[float] = []


def load_gpx_points() -> None:
    global gpx_track_points, gpx_cumdist
    gpx_track_points.clear()
    gpx_cumdist.clear()
    
    # Récupère le GPX actif
    active_path = os.path.join(GPX_DIR, "active_gpx.json")
    if not os.path.exists(active_path):
        return
    with open(active_path, "r") as f:
        active_file = json.load(f).get("active")
    if not active_file:
        return
    
    gpx_file_path = os.path.join(GPX_DIR, active_file)
    if not os.path.exists(gpx_file_path):
        return
    
    with open(gpx_file_path, "r", encoding="utf-8") as f:
        gpx = gpxpy.parse(f)
    
    pts = []
    for track in gpx.tracks:
        for seg in track.segments:
            for p in seg.points:
                pts.append((p.latitude, p.longitude))
    if not pts:
        for w in gpx.waypoints:
            pts.append((w.latitude, w.longitude))
    
    cum = 0.0
    gpx_track_points.extend(pts)
    gpx_cumdist.clear()
    prev = None
    for pt in pts:
        if prev is None:
            gpx_cumdist.append(0.0)
            prev = pt
            continue
        d = haversine_km(prev[0], prev[1], pt[0], pt[1])
        cum += d
        gpx_cumdist.append(cum)
        prev = pt


def nearest_point_distance_along_track(
    lat: float, lon: float
) -> Optional[tuple[float, float, int]]:
    if not gpx_track_points:
        return None
    best_i = -1
    best_dist = float("inf")
    for i, (plat, plon) in enumerate(gpx_track_points):
        d = haversine_km(lat, lon, plat, plon)
        if d < best_dist:
            best_dist = d
            best_i = i
    if best_i < 0:
        return None
    dist_from_start = gpx_cumdist[best_i]
    dist_to_end = gpx_cumdist[-1] - dist_from_start
    return dist_from_start, dist_to_end, best_i


def distance_to_gpx_track_km(lat: float, lon: float) -> Optional[float]:
    """Distance minimale entre une position et la trace GPX active."""
    if not gpx_track_points:
        return None
    return min(haversine_km(lat, lon, plat, plon) for plat, plon in gpx_track_points)


def geo_access_payload(lat: Optional[float], lon: Optional[float], admin_bypass: bool = False) -> Dict[str, Any]:
    """Construit le résultat d'autorisation géographique."""
    if admin_bypass:
        return {
            "allowed": True,
            "admin_bypass": True,
            "radius_km": GEO_SECURITY_RADIUS_KM,
            "distance_km": None,
            "message": "Accès autorisé via session admin.",
        }

    if lat is None or lon is None:
        return {
            "allowed": False,
            "admin_bypass": False,
            "radius_km": GEO_SECURITY_RADIUS_KM,
            "distance_km": None,
            "message": "Position GPS requise pour vérifier l'accès.",
        }

    distance_km = distance_to_gpx_track_km(lat, lon)
    if distance_km is None:
        return {
            "allowed": False,
            "admin_bypass": False,
            "radius_km": GEO_SECURITY_RADIUS_KM,
            "distance_km": None,
            "message": "Trace GPX active introuvable, vérification géographique impossible.",
        }

    allowed = distance_km <= GEO_SECURITY_RADIUS_KM
    return {
        "allowed": allowed,
        "admin_bypass": False,
        "radius_km": GEO_SECURITY_RADIUS_KM,
        "distance_km": round(distance_km, 2),
        "message": (
            "Position autorisée."
            if allowed
            else f"Accès refusé : vous êtes à {distance_km:.1f} km de la trace GPX active. Limite : {GEO_SECURITY_RADIUS_KM:.0f} km."
        ),
    }


def enforce_geo_access(lat: Optional[float], lon: Optional[float], session_token: Optional[str]) -> Dict[str, Any]:
    """Bloque l'action si la position est hors du rayon autorisé, sauf admin connecté."""
    payload = geo_access_payload(lat, lon, admin_bypass=is_admin_session(session_token))
    if not payload["allowed"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=payload["message"])
    return payload


def ensure_gpx_dir():
    if not os.path.exists(GPX_DIR):
        os.makedirs(GPX_DIR, exist_ok=True)

# -----------------------------------
# Pydantic models
# -----------------------------------
class EquipeItem(BaseModel):
    nom: str
    couleur: str
    etat: str = "non partie"
    
class EquipesUpdate(BaseModel):
    equipes: List[EquipeItem]

class EtatUpdate(BaseModel):
    etat: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    accuracy: Optional[float] = None

class Passage(BaseModel):
    equipe: str
    latitude: float
    longitude: float
    observateur: str


class GeoAccessRequest(BaseModel):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    accuracy: Optional[float] = None


# -----------------------------------
# WebSocket connection manager
# -----------------------------------
class ConnectionManager:
    def __init__(self):
        self.active: List[WebSocket] = []
        self.lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self.lock:
            self.active.append(websocket)

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self.lock:
            if websocket in self.active:
                self.active.remove(websocket)

    async def broadcast_json(self, message: Dict[str, Any]) -> None:
        to_remove = []
        async with self.lock:
            for ws in self.active:
                try:
                    await ws.send_json(message)
                except Exception:
                    to_remove.append(ws)
            for ws in to_remove:
                if ws in self.active:
                    self.active.remove(ws)


manager = ConnectionManager()

# -----------------------------------
# Redis client and listener
# -----------------------------------
redis_pub: Optional[redis.Redis] = None
_redis_listener_task: Optional[asyncio.Task] = None
_redis_stop = asyncio.Event()


async def redis_listener() -> None:
    global redis_pub
    try:
        rsub = redis.from_url(REDIS_URL, decode_responses=False)
        pubsub = rsub.pubsub()
        await pubsub.subscribe(REDIS_CHANNEL)
        while not _redis_stop.is_set():
            message = await pubsub.get_message(
                ignore_subscribe_messages=True, timeout=1.0
            )
            if message:
                data = message.get("data")
                if isinstance(data, (bytes, bytearray)):
                    try:
                        payload = json.loads(data.decode())
                    except Exception:
                        payload = {"type": "raw", "data": data.decode(errors="ignore")}
                elif isinstance(data, str):
                    try:
                        payload = json.loads(data)
                    except Exception:
                        payload = {"type": "raw", "data": data}
                else:
                    payload = {"type": "raw", "data": str(data)}

                await manager.broadcast_json(payload)
            await asyncio.sleep(0)
    except asyncio.CancelledError:
        pass
    except Exception as e:
        print("redis_listener error:", e)
    finally:
        try:
            await pubsub.unsubscribe(REDIS_CHANNEL)
            await rsub.close()
        except Exception:
            pass


async def reverse_geocode(lat: float, lon: float) -> Optional[str]:
    url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}&zoom=10&addressdetails=1"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("address", {}).get("city") or data.get("address", {}).get("town") or data.get("address", {}).get("village")
    return None

# -----------------------------------
# API routes
# -----------------------------------
@app.get("/api/equipes")
def api_get_equipes() -> List[Dict[str, Any]]:
    return get_equipes()


@app.post("/api/equipes")
def api_update_equipes(data: EquipesUpdate, _: str = Depends(require_auth)) -> Dict[str, Any]:
    try:
        # data.equipes est une liste d’objets avec nom + couleur
        save_equipes([e.dict() for e in data.equipes])
        return {"status": "ok", "equipes": data.equipes}
    except Exception as e:
        print(f"Erreur mise à jour équipes : {e}")
        raise HTTPException(status_code=500, detail="Erreur interne serveur")

# Contacts GG
class ContactsUpdate(BaseModel):
    tel_infirmerie: str = ""
    tel_velo: str = ""

@app.get("/api/contacts")
def api_get_contacts() -> Dict[str, str]:
    """Récupère les contacts GG depuis config.json"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                config_data = json.load(f)
                return {
                    "tel_infirmerie": config_data.get("tel_infirmerie", ""),
                    "tel_velo": config_data.get("tel_velo", "")
                }
        except Exception as e:
            print(f"Erreur lecture contacts: {e}")
    return {"tel_infirmerie": "", "tel_velo": ""}

@app.post("/api/contacts")
def api_update_contacts(data: ContactsUpdate, _: str = Depends(require_auth)) -> Dict[str, Any]:
    """Sauvegarde les contacts GG dans config.json"""
    try:
        ensure_db_path()
        config_data = {}
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    config_data = json.load(f)
            except Exception:
                pass
        
        config_data["tel_infirmerie"] = data.tel_infirmerie
        config_data["tel_velo"] = data.tel_velo
        
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config_data, f, indent=2)
        
        return {"status": "ok", "contacts": data.dict()}
    except Exception as e:
        print(f"Erreur sauvegarde contacts : {e}")
        raise HTTPException(status_code=500, detail="Erreur interne serveur")

# Config complète
@app.get("/api/config")
def api_get_config() -> Dict[str, str]:
    """Récupère la configuration complète (sans le hash de mot de passe)"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                config_data = json.load(f)
                # Ne pas exposer le hash du mot de passe
                return {
                    "tel_infirmerie": config_data.get("tel_infirmerie", ""),
                    "tel_velo": config_data.get("tel_velo", "")
                }
        except Exception as e:
            print(f"Erreur lecture config: {e}")
    return {"tel_infirmerie": "", "tel_velo": ""}


@app.post("/api/geo_access")
def api_geo_access(
    data: GeoAccessRequest,
    session_token: Optional[str] = Cookie(None, alias="config_session"),
) -> Dict[str, Any]:
    """Vérifie si une position est autorisée par rapport à la trace GPX active."""
    return geo_access_payload(
        data.latitude,
        data.longitude,
        admin_bypass=is_admin_session(session_token),
    )

# État d'équipe pour anim
class EtatEquipeUpdate(BaseModel):
    equipe_id: int
    etat: str
    anim: str
    position: Dict[str, float]
    timestamp: str

@app.post("/api/equipes/etat")
async def api_update_etat_equipe(
    data: EtatEquipeUpdate,
    session_token: Optional[str] = Cookie(None, alias="config_session"),
) -> Dict[str, Any]:
    """Mise à jour de l'état d'une équipe par un anim"""
    enforce_geo_access(data.position.get("lat"), data.position.get("lng"), session_token)

    try:
        with sqlite3.connect(DB_FILE) as conn:
            c = conn.cursor()
            
            # Récupérer le nom et la couleur de l'équipe
            c.execute("SELECT nom, couleur FROM equipes WHERE id = ?", (data.equipe_id,))
            row = c.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Équipe non trouvée")
            
            nom_equipe, couleur = row
            
            # Mapper les états de l'interface anim vers les états de la base
            etat_map = {
                'pause': 'pause',
                'spi': 'temps spi',
                'repas': 'pause midi',
                'roulant': 'roule'
            }
            etat_db = etat_map.get(data.etat, data.etat)
            
            # Récupérer la ville depuis les coordonnées pour tous les changements d'état
            ville = await reverse_geocode(data.position['lat'], data.position['lng'])
            
            # Mettre à jour l'état, la position ET la ville
            c.execute(
                "UPDATE equipes SET etat = ?, latitude = ?, longitude = ?, ville = ? WHERE id = ?",
                (etat_db, data.position['lat'], data.position['lng'], ville, data.equipe_id)
            )
            
            # Si l'équipe se remet à rouler, créer un point de passage
            if etat_db == 'roule':
                # Créer un passage avec l'anim comme observateur
                timestamp = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
                c.execute(
                    "INSERT INTO passages (equipe, latitude, longitude, timestamp, observateur, ville) VALUES (?, ?, ?, ?, ?, ?)",
                    (nom_equipe, data.position['lat'], data.position['lng'], timestamp, data.anim, ville)
                )
                print(f"[PASSAGE AUTO] {nom_equipe} - Remise en route par {data.anim}")
            
            conn.commit()
            
            # Broadcast via WebSocket
            await broadcast_etat_equipe(nom_equipe, etat_db, couleur)
            # Broadcast aussi le summary pour que tout soit à jour
            await broadcast_summary()
        
        return {"status": "ok", "etat": data.etat}
    except Exception as e:
        print(f"Erreur mise à jour état équipe : {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Demande d'assistance
class AssistanceRequest(BaseModel):
    type: str  # 'velo' ou 'medical'
    equipe_id: int
    anim: str
    position: Dict[str, float]
    timestamp: str

@app.post("/api/assistance")
async def api_assistance(data: AssistanceRequest) -> Dict[str, Any]:
    """Enregistre une demande d'assistance"""
    try:
        # Log de la demande d'assistance
        print(f"[ASSISTANCE {data.type.upper()}] Équipe ID: {data.equipe_id}, anim: {data.anim}, Position: {data.position}")
        
        # On pourrait stocker ça dans une table dédiée si besoin
        # Pour l'instant on log juste
        
        return {"status": "ok", "type": data.type}
    except Exception as e:
        print(f"Erreur enregistrement assistance : {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/equipe/{nom}/etat")
async def api_set_etat(
    nom: str,
    data: EtatUpdate = Body(...),
    session_token: Optional[str] = Cookie(None, alias="config_session"),
):
    etat = data.etat.lower()
    if etat not in ["roule", "temps spi", "pause", "pause midi", "non partie", "arrivée"]:
        raise HTTPException(status_code=400, detail="État invalide (roule / temps spi / pause / pause midi / non partie / arrivée)")

    enforce_geo_access(data.latitude, data.longitude, session_token)

    # Récupérer les points clés du GPX
    key_points = get_gpx_key_points()
    
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()

        # Récupérer l'état actuel
        c.execute("SELECT etat FROM equipes WHERE nom = ?", (nom,))
        row = c.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Équipe non trouvée")
        etat_actuel = row[0]

        # Met à jour l'état seulement si différent
        if etat != etat_actuel:
            c.execute("UPDATE equipes SET etat = ? WHERE nom = ?", (etat, nom))
            
            # Mettre à jour la position GPS selon l'état
            if etat == "non partie" and "depart" in key_points:
                lat = key_points["depart"]["latitude"]
                lon = key_points["depart"]["longitude"]
                c.execute("UPDATE equipes SET latitude = ?, longitude = ? WHERE nom = ?", (lat, lon, nom))
            elif etat == "arrivée" and "arrivee" in key_points:
                lat = key_points["arrivee"]["latitude"]
                lon = key_points["arrivee"]["longitude"]
                c.execute("UPDATE equipes SET latitude = ?, longitude = ? WHERE nom = ?", (lat, lon, nom))
            elif etat == "pause midi" and "pause_midi" in key_points:
                lat = key_points["pause_midi"]["latitude"]
                lon = key_points["pause_midi"]["longitude"]
                c.execute("UPDATE equipes SET latitude = ?, longitude = ? WHERE nom = ?", (lat, lon, nom))

        conn.commit()

    # Broadcast immédiat de l'état avec coordonnées puis summary
    await broadcast_etat_equipe(nom, etat)
    await broadcast_summary()
    return {"status": "ok", "equipe": nom, "etat": etat}

@app.post("/api/passage")
async def api_add_passage(
    p: Passage,
    session_token: Optional[str] = Cookie(None, alias="config_session"),
) -> Dict[str, Any]:
    enforce_geo_access(p.latitude, p.longitude, session_token)

    ville = await reverse_geocode(p.latitude, p.longitude)  # Ajout reverse geocoding

    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        timestamp = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
        c.execute(
            """
            SELECT 1 FROM passages
            WHERE equipe = ? AND observateur = ?
              AND ROUND(latitude, 4) = ROUND(?, 4)
              AND ROUND(longitude, 4) = ROUND(?, 4)
            """,
            (p.equipe, p.observateur, p.latitude, p.longitude),
        )
        if c.fetchone():
            raise HTTPException(
                status_code=400, detail="Équipe déjà pointée à cet endroit."
            )
        c.execute(
            """
            INSERT INTO passages (equipe, latitude, longitude, timestamp, observateur, ville)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (p.equipe, p.latitude, p.longitude, timestamp, p.observateur, ville),
        )
        last_id = c.lastrowid
        
        # Mettre à jour la position GPS de l'équipe pour réactivité instantanée
        c.execute(
            "UPDATE equipes SET latitude = ?, longitude = ?, etat = 'roule' WHERE nom = ?",
            (p.latitude, p.longitude, p.equipe)
        )
        
        conn.commit()

    res = nearest_point_distance_along_track(p.latitude, p.longitude)
    dist_from_start = res[0] if res else None
    dist_to_end = res[1] if res else None

    payload = {
        "type": "new_passage",
        "passage": {
            "id": last_id,
            "equipe": p.equipe,
            "latitude": p.latitude,
            "longitude": p.longitude,
            "timestamp": timestamp,
            "observateur": p.observateur,
            "distance_from_start_km": dist_from_start,
            "distance_to_end_km": dist_to_end,
        },
    }

    try:
        if redis_pub:
            await redis_pub.publish(REDIS_CHANNEL, json.dumps(payload))
    except Exception as e:
        print(f"Redis publish error: {e}")

    # Broadcast immédiat du nouveau passage puis de l'état avec coordonnées
    await manager.broadcast_json(payload)
    await broadcast_etat_equipe(p.equipe, "roule")
    await broadcast_summary()
    return {"status": "ok", "id": last_id}


@app.get("/api/passages")
def api_get_passages(limit: int = 100) -> List[Dict[str, Any]]:
    return get_passages(limit)


@app.get("/api/passages/today")
def api_get_passages_today(include_archives: bool = True) -> List[Dict[str, Any]]:
    """Récupère tous les passages du jour (actuels + archives)"""
    return get_all_passages_today(include_archives)


@app.get("/api/passages/archives")
def api_get_passages_archives(
    date_debut: Optional[str] = Query(None, description="Date de début au format ISO (YYYY-MM-DD)"),
    date_fin: Optional[str] = Query(None, description="Date de fin au format ISO (YYYY-MM-DD)"),
    limit: int = Query(1000, description="Nombre maximum de résultats")
) -> List[Dict[str, Any]]:
    """Récupère les passages archivés avec filtrage optionnel par date"""
    return get_passages_archives(date_debut, date_fin, limit)


@app.get("/api/summary")
def api_get_summary() -> List[Dict[str, Any]]:
    summary = []
    equipes = get_equipes()
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        for equipe in equipes:
            nom = equipe["nom"]
            # Utiliser les coordonnées de la table equipes si elles existent
            equipe_lat = equipe.get("latitude")
            equipe_lon = equipe.get("longitude")
            equipe_ville = equipe.get("ville")
            
            # Convertir les strings en float si nécessaire
            if equipe_lat and equipe_lat != "":
                try:
                    equipe_lat = float(equipe_lat)
                except (ValueError, TypeError):
                    equipe_lat = None
            else:
                equipe_lat = None
            
            if equipe_lon and equipe_lon != "":
                try:
                    equipe_lon = float(equipe_lon)
                except (ValueError, TypeError):
                    equipe_lon = None
            else:
                equipe_lon = None
            
            c.execute(
                """
                SELECT id, equipe, latitude, longitude, timestamp, observateur, ville
                FROM passages
                WHERE equipe = ?
                ORDER BY timestamp DESC LIMIT 1
                """,
                (nom,),
            )
            r = c.fetchone()
            
            # Priorité : coordonnées de la table equipes > coordonnées du dernier passage
            if equipe_lat is not None and equipe_lon is not None:
                lat, lon = equipe_lat, equipe_lon
            elif r:
                lat, lon = r[2], r[3]
            else:
                lat, lon = None, None
            
            # Priorité : ville de la table equipes > ville du dernier passage
            if equipe_ville:
                ville = equipe_ville
            elif r and len(r) > 6:
                ville = r[6]
            else:
                ville = None
            
            if r or (lat is not None and lon is not None):
                res = nearest_point_distance_along_track(lat, lon) if lat and lon else None
                summary.append(
                    {
                        "equipe": nom,
                        "couleur": equipe["couleur"],
                        "etat": equipe["etat"],
                        "last_passage": {
                            "id": r[0] if r else None,
                            "timestamp": r[4] if r else None,
                            "observateur": r[5] if r else None,
                            "latitude": lat,
                            "longitude": lon,
                            "ville": ville,
                        },
                        "distance_from_start_km": res[0] if res else None,
                        "distance_to_end_km": res[1] if res else None,
                    }
                )
            else:
                summary.append(
                    {
                        "equipe": nom,
                        "couleur": equipe["couleur"],
                        "etat": equipe["etat"],
                        "last_passage": None,
                        "distance_from_start_km": None,
                        "distance_to_end_km": None,
                    }
                )
    return summary
    
async def broadcast_etat_equipe(nom: str, etat: str, couleur: str = None):
    # Récupérer les coordonnées actuelles de l'équipe
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("SELECT latitude, longitude, couleur, ville FROM equipes WHERE nom = ?", (nom,))
        row = c.fetchone()
        lat, lon, db_couleur, ville = row if row else (None, None, None, None)
    
    payload = {
        "type": "etat_equipe",
        "equipe": nom,
        "etat": etat,
    }
    if couleur:
        payload["couleur"] = couleur
    elif db_couleur:
        payload["couleur"] = db_couleur
    
    # Inclure les coordonnées si disponibles
    if lat is not None and lon is not None:
        payload["latitude"] = float(lat) if lat else None
        payload["longitude"] = float(lon) if lon else None
    
    # Inclure la ville si disponible
    if ville:
        payload["ville"] = ville
    
    if redis_pub:
        try:
            await redis_pub.publish(REDIS_CHANNEL, json.dumps(payload))
        except Exception as e:
            print(f"Redis publish error: {e}")
    await manager.broadcast_json(payload)



async def broadcast_summary() -> None:
    try:
        summary = api_get_summary()
        payload = {"type": "summary", "summary": summary}
        if redis_pub:
            try:
                await redis_pub.publish(REDIS_CHANNEL, json.dumps(payload))
            except Exception as e:
                print(f"Redis publish summary error: {e}")
        await manager.broadcast_json(payload)
    except Exception as e:
        print(f"Erreur broadcast summary: {e}")

# -----------------------------------
# Route DELETE pour suppression GPX
# -----------------------------------
@app.delete("/api/gpx")
async def delete_gpx(filename: str = Query(...), _: str = Depends(require_auth)):
    gpx_path = os.path.join(GPX_DIR, filename)
    if os.path.exists(gpx_path):
        os.remove(gpx_path)
        return {"message": f"Fichier GPX '{filename}' supprimé"}
    else:
        raise HTTPException(status_code=404, detail="Fichier GPX introuvable")

# -----------------------------------
# Route DELETE pour suppression passage avec logs
# -----------------------------------
@app.delete("/api/passage/{id}")
async def api_delete_passage(id: int = Path(..., description="ID du passage à supprimer")):
    print(f"[DELETE] Requested deletion for passage id={id}")
    try:
        with sqlite3.connect(DB_FILE) as conn:
            c = conn.cursor()
            c.execute("SELECT 1 FROM passages WHERE id = ?", (id,))
            row = c.fetchone()
            print(f"[DELETE] Passage found: {row}")
            if not row:
                print(f"[DELETE] Passage id={id} not found")
                raise HTTPException(status_code=404, detail="Passage non trouvé")
            c.execute("DELETE FROM passages WHERE id = ?", (id,))
            conn.commit()
            print(f"[DELETE] Passage id={id} deleted")
    except Exception as e:
        print(f"[DELETE] Error deleting passage id={id}: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de la suppression : {e}")

    payload = {
        "type": "delete_passage",
        "id": id
    }
    try:
        if redis_pub:
            await redis_pub.publish(REDIS_CHANNEL, json.dumps(payload))
    except Exception as e:
        print(f"Redis publish error: {e}")

    await manager.broadcast_json(payload)
    await broadcast_summary()
    return {"status": "ok", "message": f"Passage {id} supprimé"}


# -----------------------------------
# WebSocket endpoint
# -----------------------------------
@app.websocket("/ws/passages")
async def websocket_endpoint(ws: WebSocket):
    await manager.connect(ws)
    try:
        passages = get_passages(limit=100)
        await ws.send_json({"type": "passages", "passages": passages})
        summary = api_get_summary()
        await ws.send_json({"type": "summary", "summary": summary})  # envoi résumé à la connexion
        while True:
            try:
                msg = await asyncio.wait_for(ws.receive_text(), timeout=None)
            except asyncio.CancelledError:
                break
            except WebSocketDisconnect:
                break
            except Exception:
                await asyncio.sleep(0.1)
    finally:
        await manager.disconnect(ws)


# -----------------------------------
# Upload GPX and reset passages
# -----------------------------------
@app.post("/api/upload_gpx")
async def api_upload_gpx(file: UploadFile = File(...), _: str = Depends(require_auth)):
    ensure_gpx_dir()
    filename = file.filename
    # Sécurité: vérifier que c'est un fichier GPX
    if not filename.lower().endswith(".gpx"):
        raise HTTPException(status_code=400, detail="Seuls les fichiers .gpx sont acceptés")
    dest_path = os.path.join(GPX_DIR, filename)
    with open(dest_path, "wb") as f:
        f.write(await file.read())
    return {"status": "ok", "filename": filename}


@app.post("/api/reset_passages")
async def reset_passages(_: str = Depends(require_auth)):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Supprime tous les passages
    c.execute("DELETE FROM passages")
    
    # Réinitialise tous les états d'équipes à "non partie"
        # Réinitialise tous les états, positions et villes d'équipes
    c.execute("UPDATE equipes SET etat = 'non partie', latitude = NULL, longitude = NULL, ville = NULL")
    
    conn.commit()
    conn.close()

    payload = {"type": "reset_passages"}
    try:
        if redis_pub:
            await redis_pub.publish(REDIS_CHANNEL, json.dumps(payload))
    except Exception as e:
        print(f"Redis publish reset error: {e}")

    # Broadcast aux WS + envoi d'un summary actualisé
    await manager.broadcast_json(payload)
    await broadcast_summary()

    return {"status": "ok"}
    
@app.get("/api/gpx_files")
def api_list_gpx_files():
    ensure_gpx_dir()
    files = [f for f in os.listdir(GPX_DIR) if f.lower().endswith(".gpx")]
    active_file = None
    active_path = os.path.join(GPX_DIR, "active_gpx.json")
    if os.path.exists(active_path):
        with open(active_path, "r") as f:
            active_file = json.load(f).get("active")
    return {"files": files, "active": active_file}

@app.post("/api/set_active_gpx")
def api_set_active_gpx(data: dict, _: str = Depends(require_auth)):
    filename = data.get("filename")
    src_path = os.path.join(GPX_DIR, filename)
    if not filename or not os.path.exists(src_path):
        raise HTTPException(status_code=404, detail="Fichier GPX non trouvé")

    # Enregistre comme actif
    with open(os.path.join(GPX_DIR, "active_gpx.json"), "w") as f:
        json.dump({"active": filename}, f)

    # Copie le GPX actif vers le fichier attendu par load_gpx_points()
    import shutil
    shutil.copy(src_path, GPX_FILE)

    # Recharge les points GPX
    load_gpx_points()

    return {"status": "ok", "active": filename}

# -----------------------------------
# Root / Index route
# -----------------------------------
@app.get("/sw.js")
def serve_service_worker():
    """Expose le service worker à la racine pour couvrir tout le site."""
    return FileResponse(
        os.path.join(STATIC_DIR, "sw.js"),
        media_type="application/javascript",
        headers={
            "Service-Worker-Allowed": "/",
            "Cache-Control": "no-cache",
        },
    )


@app.get("/")
def serve_index():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


def get_route_code() -> str:
    """Extrait un code court de route (ex: 62, 11) depuis le nom/slug."""
    import re

    match_name = re.search(r"(\d+)", ROUTE_NAME or "")
    if match_name:
        return match_name.group(1)

    match_slug = re.search(r"(\d+)", ROUTE_SLUG or "")
    if match_slug:
        return match_slug.group(1)

    return ROUTE_SLUG or "route"


@app.get("/site.webmanifest")
def serve_dynamic_site_manifest() -> JSONResponse:
    route_code = get_route_code()
    manifest = {
        "name": f"PéléVTT {route_code}",
        "short_name": f"PéléVTT{route_code}",
        "lang": "fr-FR",
        "description": f"Application de suivi des parcours VTT pour {ROUTE_NAME}",
        "start_url": "/?source=pwa",
        "id": "/static/index.html",
        "icons": [
            {
                "src": "/static/android-chrome-192x192.png",
                "sizes": "192x192",
                "type": "image/png",
            },
            {
                "src": "/static/android-chrome-512x512.png",
                "sizes": "512x512",
                "type": "image/png",
            },
            {
                "src": "/static/apple-touch-icon.png",
                "sizes": "180x180",
                "type": "image/png",
            },
        ],
        "theme_color": "#ffffff",
        "background_color": "#ffffff",
        "display": "standalone",
        "orientation": "portrait-primary",
        "scope": "/",
        "prefer_related_applications": False,
    }
    return JSONResponse(content=manifest, media_type="application/manifest+json")


@app.get("/site_anim.webmanifest")
def serve_dynamic_anim_manifest() -> JSONResponse:
    route_code = get_route_code()
    manifest = {
        "name": f"Anim PéléVTT {route_code}",
        "short_name": f"Anim PVT{route_code}",
        "lang": "fr-FR",
        "description": f"Application anim pour {ROUTE_NAME}",
        "start_url": "/static/anim.html?source=pwa",
        "id": "/static/anim.html",
        "icons": [
            {
                "src": "/static/android-chrome-192x192.png",
                "sizes": "192x192",
                "type": "image/png",
            },
            {
                "src": "/static/android-chrome-512x512.png",
                "sizes": "512x512",
                "type": "image/png",
            },
            {
                "src": "/static/apple-touch-icon.png",
                "sizes": "180x180",
                "type": "image/png",
            },
        ],
        "theme_color": "#ffffff",
        "background_color": "#ffffff",
        "display": "standalone",
        "orientation": "portrait-primary",
        "scope": "/",
        "prefer_related_applications": False,
    }
    return JSONResponse(content=manifest, media_type="application/manifest+json")


@app.get("/api/route_context")
def api_get_route_context() -> Dict[str, str]:
    """Expose le contexte d'instance pour le mode multi-route."""
    return {
        "route_name": ROUTE_NAME,
        "route_slug": ROUTE_SLUG,
        "redis_channel": REDIS_CHANNEL,
    }


@app.get("/api/app_version")
def api_get_app_version() -> Dict[str, str]:
    """Expose la version de cache utilisée par le Service Worker."""
    return {
        "version": get_cache_version(),
        "route_name": ROUTE_NAME,
        "route_slug": ROUTE_SLUG,
    }


# -----------------------------------
# Routes d'authentification configuration
# -----------------------------------
@app.post("/api/auth/login")
async def login(
    login_request: LoginRequest,
    response: Response,
    x_forwarded_for: Optional[str] = Header(None)
):
    """Authentification pour accès configuration"""
    # Récupérer l'IP cliente
    client_ip = x_forwarded_for.split(",")[0] if x_forwarded_for else "unknown"
    
    # Vérifier rate limiting
    if login_attempts.is_blocked(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Trop de tentatives. Réessayez dans 15 minutes."
        )
    
    # Vérifier le mot de passe
    if not verify_password(login_request.password, CONFIG_PASSWORD_HASH):
        login_attempts.record_attempt(client_ip)
        remaining = login_attempts.max_attempts - len(login_attempts.attempts.get(client_ip, []))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Mot de passe incorrect. {remaining} tentatives restantes."
        )
    
    # Créer la session
    token, expires = create_session()
    login_attempts.clear_attempts(client_ip)
    
    # Définir le cookie de session (HttpOnly, Secure si HTTPS)
    response.set_cookie(
        key="config_session",
        value=token,
        httponly=True,
        secure=False,  # Mettre True en production avec HTTPS
        samesite="lax",
        max_age=SESSION_DURATION_HOURS * 3600,
        expires=expires.strftime("%a, %d %b %Y %H:%M:%S GMT")
    )
    
    return {
        "status": "success",
        "message": "Authentification réussie",
        "expires_at": expires.isoformat()
    }


@app.post("/api/auth/logout")
async def logout(
    response: Response,
    session_token: Optional[str] = Cookie(None, alias="config_session")
):
    """Déconnexion et suppression de la session"""
    if session_token and session_token in active_sessions:
        del active_sessions[session_token]
    
    # Supprimer le cookie
    response.delete_cookie(key="config_session")
    
    return {"status": "success", "message": "Déconnexion réussie"}


@app.get("/api/auth/verify")
async def verify_auth(session_token: str = Depends(require_auth)):
    """Vérifie si l'utilisateur est authentifié"""
    session = active_sessions.get(session_token)
    return {
        "authenticated": True,
        "expires_at": session["expires_at"].isoformat() if session else None
    }


@app.post("/api/auth/change-password")
async def change_password(
    change_request: ChangePasswordRequest,
    session_token: str = Depends(require_auth)
):
    """Change le mot de passe de configuration"""
    global CONFIG_PASSWORD_HASH
    
    # Vérifier le mot de passe actuel
    if not verify_password(change_request.current_password, CONFIG_PASSWORD_HASH):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Mot de passe actuel incorrect"
        )
    
    # Valider le nouveau mot de passe
    if len(change_request.new_password) < 4:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le mot de passe doit contenir au moins 4 caractères"
        )
    
    # Générer le hash du nouveau mot de passe
    new_hash = pwd_context.hash(change_request.new_password)
    
    # Sauvegarder le nouveau hash
    try:
        save_password_hash(new_hash)
        CONFIG_PASSWORD_HASH = new_hash
        print(f"[INFO] Mot de passe changé avec succès")
        return {
            "status": "success",
            "message": "Mot de passe changé avec succès"
        }
    except Exception as e:
        print(f"[ERROR] Erreur lors de la sauvegarde du nouveau mot de passe: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la sauvegarde du nouveau mot de passe"
        )
