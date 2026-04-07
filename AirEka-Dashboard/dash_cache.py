"""
AirEka — Cache côté Dash (TTL en mémoire)
Évite les appels API/LLM redondants entre les callbacks.

Usage :
    from dash_cache import dash_cache, cached_api_call

    # Décorer une fonction
    @dash_cache(ttl=300)
    def get_city_data(city): ...

    # Ou appel direct
    data = cached_api_call("forecast_Yaounde_7", load_forecast, "Yaounde", 7, ttl=300)
"""

import time
import threading
import hashlib
import json
from functools import wraps
from typing import Any, Callable

# ── Store thread-safe ─────────────────────────────────────────────────────────
_store: dict[str, tuple[Any, float]] = {}
_lock = threading.Lock()


def _make_key(*args, **kwargs) -> str:
    raw = json.dumps({"a": args, "k": kwargs}, default=str, sort_keys=True)
    return hashlib.md5(raw.encode()).hexdigest()


def cache_get(key: str) -> tuple[bool, Any]:
    with _lock:
        if key in _store:
            value, expires = _store[key]
            if time.time() < expires:
                return True, value
            del _store[key]
    return False, None


def cache_set(key: str, value: Any, ttl: int) -> None:
    with _lock:
        _store[key] = (value, time.time() + ttl)


def cache_invalidate(prefix: str | None = None) -> None:
    with _lock:
        if prefix:
            keys = [k for k in _store if k.startswith(prefix)]
            for k in keys:
                del _store[k]
        else:
            _store.clear()


# ── Décorateur ────────────────────────────────────────────────────────────────
def dash_cache(ttl: int = 300, key_prefix: str = ""):
    """
    Décorateur de cache pour les fonctions de chargement de données.

    @dash_cache(ttl=300)
    def load_my_data(city, days=30): ...
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            raw_key = f"{key_prefix}{func.__name__}:{_make_key(*args, **kwargs)}"
            hit, value = cache_get(raw_key)
            if hit:
                return value
            result = func(*args, **kwargs)
            cache_set(raw_key, result, ttl)
            return result
        return wrapper
    return decorator


def cached_api_call(key: str, func: Callable, *args, ttl: int = 300, **kwargs) -> Any:
    """
    Appel API avec cache.
    key    : clé explicite (ex: "forecast_Yaounde_7")
    func   : fonction à appeler si cache miss
    ttl    : durée de vie en secondes
    """
    hit, value = cache_get(key)
    if hit:
        return value
    result = func(*args, **kwargs)
    cache_set(key, result, ttl)
    return result


# ── Clés prédéfinies (évite les fautes de frappe) ────────────────────────────
def key_forecast(city: str, horizon: int = 7) -> str:
    return f"forecast:{city}:{horizon}"

def key_history(city: str, days: int = 30) -> str:
    return f"history:{city}:{days}"

def key_seasonal(city: str) -> str:
    return f"seasonal:{city}"

def key_stats(city: str) -> str:
    return f"stats:{city}"

def key_national() -> str:
    return "national:stats"

def key_all_cities() -> str:
    return "cities:all"

def key_ai(prompt_hash: str) -> str:
    return f"ai:{prompt_hash}"

def key_model_info() -> str:
    return "models:info"
