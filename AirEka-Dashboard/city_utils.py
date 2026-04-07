"""
AirEka — Utilitaires de résolution de ville (côté dashboard Dash).
Centralise la normalisation, la résolution et le cache TTL des données villes.
"""

import unicodedata
import time
import threading
import logging
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)

# ── Cache TTL pour get_cities_data() ─────────────────────────────────────────
_cities_cache: Dict = {'data': None, 'ts': 0}
_cities_lock = threading.Lock()
_CITIES_TTL = 120  # 2 minutes

# Données statiques minimales (last-resort fallback)
_CITIES_STATIC_FALLBACK = [
    {'city': 'Yaoundé',    'region': 'Centre',       'lat': 3.8480,  'lon': 11.5021, 'aqi': 178, 'pm25': 72.3,  'pm10': 118.5, 'no2': 42.8, 'so2': 28.1, 'o3': 38.2, 'trend': 0.0},
    {'city': 'Douala',     'region': 'Littoral',     'lat': 4.0511,  'lon': 9.7679,  'aqi': 165, 'pm25': 68.2,  'pm10': 112.5, 'no2': 38.5, 'so2': 25.2, 'o3': 35.5, 'trend': 0.0},
    {'city': 'Bafoussam',  'region': 'Ouest',        'lat': 5.4781,  'lon': 10.4174, 'aqi': 135, 'pm25': 55.0,  'pm10': 90.2,  'no2': 31.5, 'so2': 20.5, 'o3': 38.5, 'trend': 0.0},
    {'city': 'Garoua',     'region': 'Nord',         'lat': 9.3011,  'lon': 13.3975, 'aqi': 145, 'pm25': 58.9,  'pm10': 97.3,  'no2': 35.2, 'so2': 24.5, 'o3': 32.5, 'trend': 0.0},
    {'city': 'Maroua',     'region': 'Extrême-Nord', 'lat': 10.5910, 'lon': 14.3159, 'aqi': 132, 'pm25': 54.3,  'pm10': 89.7,  'no2': 32.1, 'so2': 22.3, 'o3': 34.2, 'trend': 0.0},
    {'city': 'Bamenda',    'region': 'Nord-Ouest',   'lat': 5.9600,  'lon': 10.1517, 'aqi': 45,  'pm25': 18.7,  'pm10': 31.2,  'no2': 12.4, 'so2': 6.8,  'o3': 48.2, 'trend': 0.0},
    {'city': 'Bertoua',    'region': 'Est',          'lat': 4.5750,  'lon': 13.6847, 'aqi': 88,  'pm25': 37.2,  'pm10': 61.5,  'no2': 22.5, 'so2': 14.8, 'o3': 39.5, 'trend': 0.0},
    {'city': 'Ngaoundéré', 'region': 'Adamaoua',     'lat': 7.3212,  'lon': 13.5839, 'aqi': 112, 'pm25': 46.8,  'pm10': 77.3,  'no2': 28.9, 'so2': 19.5, 'o3': 37.5, 'trend': 0.0},
    {'city': 'Ebolowa',    'region': 'Sud',          'lat': 2.9000,  'lon': 11.1500, 'aqi': 52,  'pm25': 21.6,  'pm10': 35.8,  'no2': 14.2, 'so2': 8.5,  'o3': 42.1, 'trend': 0.0},
    {'city': 'Buea',       'region': 'Sud-Ouest',    'lat': 4.1667,  'lon': 9.2333,  'aqi': 48,  'pm25': 19.5,  'pm10': 32.5,  'no2': 13.2, 'so2': 7.2,  'o3': 46.5, 'trend': 0.0},
]


def _norm(name: str) -> str:
    """Normalise un nom de ville : supprime accents, met en minuscules."""
    if not name:
        return ""
    nfd = unicodedata.normalize("NFD", str(name))
    return nfd.encode("ascii", "ignore").decode().lower().strip()


def get_cities_data(force: bool = False) -> List[Dict]:
    """
    Retourne la liste des villes depuis l'API (cache TTL=2 min).
    Ne bloque jamais : retourne le cache expiré ou le fallback statique si l'API est down.
    """
    global _cities_cache
    now = time.time()

    with _cities_lock:
        cached = _cities_cache['data']
        ts = _cities_cache['ts']

    if not force and cached and (now - ts) < _CITIES_TTL:
        return cached

    try:
        from api_client import load_cities_from_api
        data = load_cities_from_api()
        if data and len(data) >= 5:
            with _cities_lock:
                _cities_cache['data'] = data
                _cities_cache['ts'] = now
            return data
    except Exception as e:
        logger.warning(f"[city_utils] get_cities_data API error: {e}")

    # Retourner le cache même expiré, ou le fallback statique
    if cached:
        logger.debug("[city_utils] get_cities_data: retour cache expiré")
        return cached

    logger.warning("[city_utils] get_cities_data: fallback statique")
    return _CITIES_STATIC_FALLBACK


def invalidate_cities_cache() -> None:
    """Invalide le cache des villes pour forcer un rechargement."""
    with _cities_lock:
        _cities_cache['ts'] = 0


def resolve_city(
    city_filter: Optional[str],
    user_city: Optional[str] = None,
    cities_data: Optional[List[Dict]] = None,
    fallback: str = "Yaoundé",
) -> str:
    """
    Résout la ville à afficher selon la priorité :
      1. Filtre utilisateur (si non 'all', non None, non vide)
      2. Ville du profil utilisateur
      3. fallback (Yaoundé par défaut)

    Valide toujours contre cities_data. Ne retourne jamais 'all'.
    """
    if cities_data is None:
        cities_data = get_cities_data()

    candidates = []
    if city_filter and city_filter not in ("all", "", None):
        candidates.append(city_filter)
    if user_city and user_city not in ("all", "", None):
        candidates.append(user_city)
    candidates.append(fallback)
    candidates.append("Yaoundé")

    for cand in candidates:
        matched = _find_city(cand, cities_data)
        if matched:
            return matched
    return fallback


def _find_city(name: str, cities_data: List[Dict]) -> Optional[str]:
    """
    Cherche la ville dans cities_data par nom normalisé.
    Retourne le nom exact tel qu'en DB, ou None si introuvable.
    """
    norm_target = _norm(name)
    for c in cities_data:
        city_name = c.get("city", "")
        if _norm(city_name) == norm_target:
            return city_name
    return None


def is_valid_city(name: str, cities_data: Optional[List[Dict]] = None) -> bool:
    """Vérifie si un nom de ville existe dans cities_data."""
    if cities_data is None:
        cities_data = get_cities_data()
    return _find_city(name, cities_data) is not None


def get_regions(cities_data: Optional[List[Dict]] = None) -> List[str]:
    """Retourne la liste triée des régions."""
    if cities_data is None:
        cities_data = get_cities_data()
    return sorted(set(c['region'] for c in cities_data if c.get('region')))


def get_national_stats(cities_data: Optional[List[Dict]] = None) -> Dict:
    """
    Calcule les stats nationales depuis cities_data.
    Essaie d'abord l'API (load_national_stats), fallback sur calcul local.
    """
    # Essai API
    try:
        from api_client import load_national_stats
        nat = load_national_stats()
        if nat and nat.get('national_avg_aqi'):
            return {
                'aqi':   round(nat.get('national_avg_aqi', 0), 1),
                'pm25':  round(nat.get('national_avg_pm25', 0), 1),
                'no2':   round(nat.get('national_avg_no2', 0), 1),
                'trend_aqi':  nat.get('trend_aqi', 0.0),
                'trend_pm25': nat.get('trend_pm25', 0.0),
                'cities_count': nat.get('cities_count', 0),
            }
    except Exception as e:
        logger.warning(f"[city_utils] get_national_stats API error: {e}")

    # Fallback calcul local
    if cities_data is None:
        cities_data = get_cities_data()
    if not cities_data:
        return {'aqi': 0, 'pm25': 0, 'no2': 0, 'trend_aqi': 0.0, 'trend_pm25': 0.0, 'cities_count': 0}

    n = len(cities_data)
    return {
        'aqi':   round(sum(c.get('aqi', 0)  for c in cities_data) / n, 1),
        'pm25':  round(sum(c.get('pm25', 0) for c in cities_data) / n, 1),
        'no2':   round(sum(c.get('no2', 0)  for c in cities_data) / n, 1),
        'trend_aqi':  0.0,
        'trend_pm25': 0.0,
        'cities_count': n,
    }
