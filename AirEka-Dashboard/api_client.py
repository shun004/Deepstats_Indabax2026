"""
Client HTTP pour l'API AirEka VERSION OPTIMISÉE avec cache.

Changements vs v1 :
  - Toutes les fonctions de chargement sont cachées (TTL configurable)
  - Le cache évite les appels HTTP répétés entre les callbacks Dash
  - Importer dash_cache.py dans le même dossier pour activer le cache
"""
import logging
import os
import time
import threading
from datetime import date
from typing import Optional

import unicodedata
import requests

logger = logging.getLogger(__name__)

# ── Cache TTL en mémoire (thread-safe) ───────────────────────────────────────
# Si dash_cache.py est disponible, on l'utilise ; sinon fallback simple.
try:
    from dash_cache import dash_cache, cached_api_call, cache_set, cache_get
    _CACHE_AVAILABLE = True
    logger.info("[api_client] Cache dash_cache actif")
except ImportError:
    _CACHE_AVAILABLE = False
    logger.warning("[api_client] dash_cache.py introuvable — cache désactivé")

    # Fallback minimaliste
    _simple_store: dict = {}
    _simple_lock = threading.Lock()

    def cache_get(key):
        with _simple_lock:
            if key in _simple_store:
                v, exp = _simple_store[key]
                if time.time() < exp:
                    return True, v
                del _simple_store[key]
        return False, None

    def cache_set(key, value, ttl):
        with _simple_lock:
            _simple_store[key] = (value, time.time() + ttl)

    def dash_cache(ttl=300, key_prefix=""):
        """Décorateur no-op si dash_cache non disponible."""
        def decorator(func):
            return func
        return decorator

    def cached_api_call(key, func, *args, ttl=300, **kwargs):
        return func(*args, **kwargs)


def _norm_city(name: str) -> str:
    """Yaounde → Yaounde, Yaoundé → Yaounde (strip accents)."""
    return unicodedata.normalize("NFD", name).encode("ascii", "ignore").decode()


API_BASE = os.environ.get("API_BASE", "https://shun004-aireka-api.hf.space")
TIMEOUT  = 6 


# ─────────────────────────────────────────────────────────────────────────────
# Classe principale
# ─────────────────────────────────────────────────────────────────────────────

class AirEkaAPI:
    """Interface haut niveau vers l'API AirEka."""

    def __init__(self, base_url: str = API_BASE, timeout: int = TIMEOUT):
        self.base    = base_url.rstrip("/")
        self.timeout = timeout
        self._session = requests.Session()  # Réutiliser la connexion TCP

    def _get(self, path: str, params: dict | None = None) -> dict | list | None:
        try:
            r = self._session.get(
                f"{self.base}{path}", params=params, timeout=self.timeout
            )
            r.raise_for_status()
            return r.json()
        except requests.exceptions.ConnectionError:
            logger.debug(f"[api_client] API indisponible : {path}")
            return None
        except Exception as e:
            logger.warning(f"[api_client] GET {path} : {e}")
            return None

    # ── Données villes ────────────────────────────────────────────────────────

    def get_dashboard(self) -> dict:
        return self._get("/dashboard") or {}

    def get_all_cities(self) -> list[dict]:
        data = self._get("/predictions/all/latest")
        return data.get("cities", []) if data else []

    def get_city(self, city: str) -> dict:
        return self._get(f"/cities/{_norm_city(city)}") or {}

    # ── Prévisions ────────────────────────────────────────────────────────────

    def get_forecast(self, city: str, days: int = 7) -> list[dict]:
        data = self._get(f"/predictions/{_norm_city(city)}/forecast", {"horizon": days})
        return data.get("forecast", []) if data else []

    def get_history(self, city: str, days: int = 30) -> list[dict]:
        data = self._get(f"/predictions/{_norm_city(city)}/history", {"days": days})
        return data.get("history", []) if data else []

    def get_range(self, city: str, start: date | str, end: date | str) -> dict:
        return self._get(
            f"/predictions/{_norm_city(city)}/range",
            {"start": str(start), "end": str(end)},
        ) or {}

    def get_timeseries(self, city: str, days: int = 365) -> list[dict]:
        data = self._get(f"/predictions/{_norm_city(city)}/timeseries", {"days": days})
        return data.get("timeseries", []) if data else []

    def get_stats(self, city: str) -> dict:
        data = self._get(f"/predictions/{_norm_city(city)}/stats")
        return data.get("stats", {}) if data else {}

    def get_seasonal(self, city: str) -> dict:
        return self._get(f"/predictions/{_norm_city(city)}/seasonal") or {}

    # ── National ──────────────────────────────────────────────────────────────

    def get_national(self) -> dict:
        data = self._get("/national")
        if data:
            data.setdefault("national_avg_aqi",  data.get("aqi",  0))
            data.setdefault("national_avg_pm25", data.get("pm25", 0))
            data.setdefault("national_avg_no2",  data.get("no2",  0))
            data.setdefault("trend_aqi",  0.0)
            data.setdefault("trend_pm25", 0.0)
        return data or {}

    def get_regions(self) -> list[dict]:
        data = self._get("/national/regions")
        return data.get("regions", []) if data else []

    def get_national_timeseries(self, days: int = 30) -> list[dict]:
        data = self._get("/national/timeseries", {"days": days})
        return data.get("timeseries", []) if data else []

    def get_national_seasonal(self) -> dict:
        return self._get("/national/seasonal") or {}

    # ── Extras ────────────────────────────────────────────────────────────────

    def compare(self, city1: str, city2: str, days: int = 30) -> dict:
        return self._get("/compare/", {"city1": city1, "city2": city2, "days": days}) or {}

    def get_model_info(self) -> dict:
        return self._get("/models/info") or {}

    def get_alert_summary(self) -> dict:
        return self._get("/alerts/summary") or {}

    def health(self) -> dict:
        return self._get("/health") or {}

    def is_available(self) -> bool:
        h = self.health()
        return h.get("status") == "ok"


# ─────────────────────────────────────────────────────────────────────────────
# Instance partagée (singleton)
# ─────────────────────────────────────────────────────────────────────────────

_api = AirEkaAPI()

# Flag pour éviter de tester l'API à chaque appel quand elle est down
_api_down_until: float = 0.0
_API_DOWN_BACKOFF = 30  # secondes avant de réessayer


def _api_is_reachable() -> bool:
    global _api_down_until
    if time.time() < _api_down_until:
        return False
    ok = _api.is_available()
    if not ok:
        _api_down_until = time.time() + _API_DOWN_BACKOFF
        logger.warning(f"[api_client] API down — retry dans {_API_DOWN_BACKOFF}s")
    return ok


# ─────────────────────────────────────────────────────────────────────────────
# Fonctions publiques AVEC CACHE
# ─────────────────────────────────────────────────────────────────────────────

def is_api_available() -> bool:
    return _api_is_reachable()


def load_cities_from_api() -> Optional[list]:
    """Cache 2 min."""
    key = "cities:all"
    hit, val = cache_get(key)
    if hit:
        return val
    cities = _api.get_all_cities()
    result = cities if cities else None
    if result:
        cache_set(key, result, 120)
    return result


def load_national_stats() -> Optional[dict]:
    """Cache 2 min."""
    key = "national:stats"
    hit, val = cache_get(key)
    if hit:
        return val
    result = _api.get_national() or None
    if result:
        cache_set(key, result, 120)
    return result


def load_forecast(city: str, horizon: int = 7) -> list:
    """Cache 30 min."""
    key = f"forecast:{_norm_city(city)}:{horizon}"
    hit, val = cache_get(key)
    if hit:
        return val
    result = _api.get_forecast(city, horizon)
    cache_set(key, result, 1800)
    return result


def load_city_history(city: str, days: int = 30) -> list:
    """Cache 5 min."""
    key = f"history:{_norm_city(city)}:{days}"
    hit, val = cache_get(key)
    if hit:
        return val
    result = _api.get_history(city, days)
    cache_set(key, result, 300)
    return result


def load_city_timeseries(city: str, days: int = 365) -> list:
    """Cache 1h — longue série temporelle."""
    key = f"timeseries:{_norm_city(city)}:{days}"
    hit, val = cache_get(key)
    if hit:
        return val
    result = _api.get_timeseries(city, days)
    cache_set(key, result, 3600)
    return result


def load_city_stats(city: str) -> dict:
    """Cache 15 min."""
    key = f"stats:{_norm_city(city)}"
    hit, val = cache_get(key)
    if hit:
        return val
    result = _api.get_stats(city)
    cache_set(key, result, 900)
    return result


def load_city_seasonal(city: str) -> dict:
    """Cache 1h — saisonnalité stable."""
    key = f"seasonal:{_norm_city(city)}"
    hit, val = cache_get(key)
    if hit:
        return val

    result = _api.get_seasonal(city)
    seasonal = result.get("seasonal", []) if result else []

    # Si l'API retourne moins de 10 mois, compléter depuis le parquet local
    months_with_data = sum(1 for e in seasonal if e.get("aqi", 0) > 0)
    if months_with_data < 10:
        try:
            import pandas as pd, os
            pq_path = os.path.join(os.path.dirname(__file__), "air_eka_api", "results(7)", "base_complete.parquet")
            if not os.path.exists(pq_path):
                import sys
                sys.path.insert(0, os.path.join(os.path.dirname(__file__), "air_eka_api"))
                from core.config import settings
                pq_path = settings.PARQUET_PATH
            df = pd.read_parquet(pq_path)
            city_col = "city_indabax" if "city_indabax" in df.columns else "city"
            date_col = next((c for c in df.columns if c.lower() in ("date", "time")), None)
            norm = _norm_city(city)
            sub = df[df[city_col].apply(lambda x: _norm_city(str(x))) == norm].copy()
            if not sub.empty and date_col:
                sub["month"] = pd.to_datetime(sub[date_col]).dt.month
                monthly = sub.groupby("month")[["aqi_global", "pm2_5", "pm10", "no2"]].mean().round(1).reset_index()
                monthly.rename(columns={"aqi_global": "aqi", "pm2_5": "pm25"}, inplace=True)
                api_months = {e["month"]: e for e in seasonal}
                merged = []
                for _, row in monthly.iterrows():
                    m = int(row["month"])
                    if m in api_months and api_months[m].get("aqi", 0) > 0:
                        merged.append(api_months[m])
                    else:
                        merged.append({"month": m, "aqi": row.get("aqi", 0),
                                       "pm25": row.get("pm25", 0), "pm10": row.get("pm10", 0),
                                       "no2": row.get("no2", 0)})
                result = {"city": city, "seasonal": sorted(merged, key=lambda x: x["month"])}
        except Exception as e:
            logger.warning(f"[api_client] seasonal parquet fallback: {e}")

    cache_set(key, result or {"city": city, "seasonal": seasonal}, 3600)
    return result or {"city": city, "seasonal": seasonal}


def load_national_seasonal() -> dict:
    """Cache 1h."""
    key = "national:seasonal"
    hit, val = cache_get(key)
    if hit:
        return val
    result = _api.get_national_seasonal()
    cache_set(key, result, 3600)
    return result


def load_national_timeseries(days: int = 30) -> list:
    """Cache 15 min."""
    key = f"national:timeseries:{days}"
    hit, val = cache_get(key)
    if hit:
        return val
    result = _api.get_national_timeseries(days)
    cache_set(key, result, 900)
    return result


def load_regions() -> list:
    """Cache 15 min."""
    key = "regions:all"
    hit, val = cache_get(key)
    if hit:
        return val
    result = _api.get_regions()
    cache_set(key, result, 900)
    return result


def load_city_comparison(city1: str, city2: str, days: int = 30) -> dict:
    """Cache 10 min."""
    key = f"compare:{_norm_city(city1)}:{_norm_city(city2)}:{days}"
    hit, val = cache_get(key)
    if hit:
        return val
    result = _api.compare(city1, city2, days)
    cache_set(key, result, 600)
    return result


def load_model_info() -> dict:
    """Cache 24h — métadonnées des modèles immuables."""
    key = "models:info"
    hit, val = cache_get(key)
    if hit:
        return val
    result = _api.get_model_info()
    cache_set(key, result, 86400)
    return result


def load_alert_summary() -> dict:
    """Cache 5 min."""
    key = "alerts:summary"
    hit, val = cache_get(key)
    if hit:
        return val
    result = _api.get_alert_summary()
    cache_set(key, result, 300)
    return result


def load_range(city: str, start: date | str, end: date | str) -> dict:
    """Cache 30 min pour les plages historiques."""
    key = f"range:{_norm_city(city)}:{start}:{end}"
    hit, val = cache_get(key)
    if hit:
        return val
    result = _api.get_range(city, start, end)
    cache_set(key, result, 1800)
    return result


# ─────────────────────────────────────────────────────────────────────────────
# Préchauffage du cache au démarrage (optionnel)
# ─────────────────────────────────────────────────────────────────────────────

def warm_cache_background(cities_data: list, top_n: int = 5) -> None:
    """
    Pré-charge en arrière-plan les données des villes les plus consultées.
    À appeler après load_data() dans app.py :

        from api_client import warm_cache_background
        warm_cache_background(CITIES_DATA)
    """
    def _warm():
        time.sleep(3)  # Laisser l'app démarrer d'abord
        if not _api_is_reachable():
            logger.info("[api_client] warm_cache: API indisponible, skip")
            return
        try:
            # Stats nationales
            load_national_stats()
            load_national_timeseries(30)

            # Top N villes par AQI
            top = sorted(cities_data, key=lambda x: x.get("aqi", 0), reverse=True)[:top_n]
            for c in top:
                city = c["city"]
                load_forecast(city, 7)
                load_city_history(city, 30)
                logger.debug(f"[api_client] warm_cache: {city} ✓")

            # Métadonnées modèles (très stables)
            load_model_info()

            logger.info(f"[api_client] Cache préchauffé ({top_n} villes) ✓")
        except Exception as e:
            logger.warning(f"[api_client] warm_cache erreur: {e}")

    t = threading.Thread(target=_warm, daemon=True, name="AirEka-WarmCache")
    t.start()