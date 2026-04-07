"""
Module IA — Commentaires experts via Llama 3.1 8B (HuggingFace/Novita)
Fournit des interprétations de qualité d'air pour AirEka Cameroun.
"""
import os
import requests
import logging
import time
from dash_cache import cached_api_call
import hashlib
import json

logger = logging.getLogger(__name__)

HF_TOKEN = os.environ.get("HF_TOKEN", "")
HF_MODEL   = "meta-llama/llama-3.1-8b-instruct"
HF_API_URL = "https://router.huggingface.co/novita/v3/openai/chat/completions"
TIMEOUT    = 8

# Cache simple en mémoire (évite appels répétés)
_cache: dict[str, tuple[str, float]] = {}
CACHE_TTL = 1800  # 30 min

SYSTEM_PROMPT_FR = """Tu es un expert senior en santé publique et en pollution atmosphérique travaillant pour AirEka,
une plateforme de surveillance de la qualité de l'air au Cameroun couvrant 40 villes réparties dans 10 régions.

Contexte AirEka :
- Seuils OMS : AQI 0-50 Bon, 51-100 Modéré, 101-150 Mauvais (groupes sensibles), 151-200 Mauvais, 201-300 Très mauvais, >300 Dangereux
- Polluants principaux : PM2.5 (seuil OMS 15 µg/m³), PM10 (45 µg/m³), NO₂ (10 µg/m³), SO₂, O₃
- Cameroun : climat tropical avec saison sèche (nov-avr, pollution élevée) et saison des pluies (mai-oct, air plus propre)
- Sources de pollution : trafic dense, industries (Douala), feux de brousse (Extrême-Nord), biomasse

Règles de réponse :
- Réponses en français, ton professionnel mais accessible
- Concis : 2-4 phrases maximum sauf si demandé autrement
- Utilise les données numériques fournies pour appuyer les interprétations
- Formule des recommandations sanitaires concrètes et actionnables
- Ne jamais inventer de données non fournies"""

SYSTEM_PROMPT_EN = """You are a senior public health and air pollution expert working for AirEka,
an air quality monitoring platform covering 40 cities across 10 regions in Cameroon.

AirEka context:
- WHO thresholds: AQI 0-50 Good, 51-100 Moderate, 101-150 Unhealthy for Sensitive Groups, 151-200 Unhealthy, 201-300 Very Unhealthy, >300 Hazardous
- Main pollutants: PM2.5 (WHO threshold 15 µg/m³), PM10 (45 µg/m³), NO₂ (10 µg/m³), SO₂, O₃
- Cameroon: tropical climate with dry season (Nov–Apr, high pollution) and rainy season (May–Oct, cleaner air)
- Pollution sources: heavy traffic, industry (Douala), bush fires (Far North), biomass burning

Response rules:
- Respond in English, professional yet accessible tone
- Concise: 2–4 sentences maximum unless asked otherwise
- Use the provided numerical data to support interpretations
- Give concrete, actionable health recommendations
- Never invent data not provided"""

# backward compat
SYSTEM_PROMPT = SYSTEM_PROMPT_FR

def call_llm_cached(user_prompt: str, max_tokens: int = 200,
                    temperature: float = 0.4, lang: str = 'fr') -> str:
    key = "ai:" + hashlib.md5(user_prompt.encode()).hexdigest()[:16]
    return cached_api_call(key, call_llm, user_prompt, max_tokens, temperature, lang, ttl=1800)


def _cache_key(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()[:16]


def call_llm(user_prompt: str, max_tokens: int = 200, temperature: float = 0.4, lang: str = 'fr') -> str:
    """Appelle l'API HuggingFace et retourne la réponse texte."""
    key = _cache_key(user_prompt)
    now = time.time()
    if key in _cache:
        text, ts = _cache[key]
        if now - ts < CACHE_TTL:
            return text

    sys_prompt = SYSTEM_PROMPT_EN if lang == 'en' else SYSTEM_PROMPT_FR
    try:
        resp = requests.post(
            HF_API_URL,
            headers={"Authorization": f"Bearer {HF_TOKEN}",
                     "Content-Type": "application/json"},
            json={
                "model": HF_MODEL,
                "messages": [
                    {"role": "system", "content": sys_prompt},
                    {"role": "user",   "content": user_prompt}
                ],
                "max_tokens": max_tokens,
                "temperature": temperature,
                "stream": False
            },
            timeout=TIMEOUT
        )
        resp.raise_for_status()
        text = resp.json()["choices"][0]["message"]["content"].strip()
        _cache[key] = (text, now)
        return text
    except Exception as e:
        logger.warning(f"[AI] Erreur LLM: {e}")
        return ""


# ─── Fonctions spécialisées ──────────────────────────────────────────────────

def ai_comparison(city1: str, aqi1: float, pm25_1: float, no2_1: float,
                  city2: str, aqi2: float, pm25_2: float, no2_2: float,
                  lang: str = 'fr') -> str:
    if lang == 'en':
        prompt = f"""Compare air quality between {city1} and {city2} in Cameroon.

Current data:
- {city1}: AQI={aqi1}, PM2.5={pm25_1} µg/m³, NO₂={no2_1} µg/m³
- {city2}: AQI={aqi2}, PM2.5={pm25_2} µg/m³, NO₂={no2_2} µg/m³

Provide: 1) Epidemiological interpretation (health impacts, at-risk groups), 2) Likely causes of the gap, 3) Priority action for the most polluted city."""
    else:
        prompt = f"""Compare la qualité de l'air entre {city1} et {city2} au Cameroun.

Données : {city1} AQI={aqi1}, PM2.5={pm25_1}, NO₂={no2_1} µg/m³ | {city2} AQI={aqi2}, PM2.5={pm25_2}, NO₂={no2_2} µg/m³

Fournis : 1) Interprétation épidémiologique (impacts, populations à risque), 2) Causes probables de l'écart, 3) Recommandation prioritaire pour la ville la plus polluée."""
    return call_llm(prompt, max_tokens=280, lang=lang)


def ai_trend_forecast(city: str, aqi_now: float, aqi_forecast: list[float],
                      pm25: float, season: str = "", lang: str = 'fr') -> str:
    avg_fc = round(sum(aqi_forecast) / len(aqi_forecast), 1) if aqi_forecast else aqi_now
    if lang == 'en':
        trend = "rising" if avg_fc > aqi_now * 1.05 else ("falling" if avg_fc < aqi_now * 0.95 else "stable")
        prompt = f"""Analyze the air quality trend for {city} (Cameroon).
Current AQI={aqi_now}, PM2.5={pm25} µg/m³{', ' + season if season else ''}
7-day forecast: {[round(v,0) for v in aqi_forecast]} → avg {avg_fc} (trend: {trend})
In 2–3 sentences: interpret for a public decision-maker, mention health risks and one concrete preventive measure."""
    else:
        trend = "hausse" if avg_fc > aqi_now * 1.05 else ("baisse" if avg_fc < aqi_now * 0.95 else "stable")
        prompt = f"""Analyse la tendance AQI à {city} (Cameroun). AQI={aqi_now}, PM2.5={pm25} µg/m³{', ' + season if season else ''}
Prévisions 7j : {[round(v,0) for v in aqi_forecast]} → moyenne {avg_fc} (tendance: {trend})
En 2-3 phrases pour un décideur : risques sanitaires + une mesure préventive concrète."""
    return call_llm(prompt, max_tokens=220, lang=lang)


def ai_policy_region(region: str, aqi: float, pm25: float, cities: list[str],
                     dominant: str = "PM2.5", lang: str = 'fr') -> str:
    if lang == 'en':
        cat = 'Hazardous' if aqi > 200 else 'Very Unhealthy' if aqi > 150 else 'Unhealthy'
        prompt = f"""You advise the Cameroonian government on region {region}.
Data: AQI={aqi} ({cat}), PM2.5={pm25} µg/m³ ({round(pm25/15,1)}× WHO limit), affected cities: {', '.join(cities[:4])}, dominant pollutant: {dominant}
Provide 3 urgent, region-specific policy recommendations with realistic timelines."""
    else:
        cat = 'Dangereux' if aqi > 200 else 'Très mauvais' if aqi > 150 else 'Mauvais'
        prompt = f"""Tu conseilles le gouvernement camerounais sur la région {region}.
AQI={aqi} ({cat}), PM2.5={pm25} µg/m³ ({round(pm25/15,1)}× OMS), villes : {', '.join(cities[:4])}, polluant dominant : {dominant}
Formule 3 recommandations politiques urgentes avec délai réaliste."""
    return call_llm(prompt, max_tokens=300, lang=lang)


def ai_dashboard_alert(worst_city: str, worst_aqi: float, n_alert: int, n_critical: int,
                       lang: str = 'fr') -> str:
    if lang == 'en':
        prompt = f"""Write a concise 2-sentence alert for a public decision-maker dashboard.
National situation Cameroon: {n_alert} cities on alert, {n_critical} critical. Worst city: {worst_city} AQI={worst_aqi}.
Message: current situation + immediate recommended action. Urgent but factual tone."""
    else:
        prompt = f"""Rédige une alerte concise (2 phrases) pour un tableau de bord décideur.
Cameroun : {n_alert} villes en alerte, {n_critical} critiques. Pire : {worst_city} AQI={worst_aqi}.
Situation + action immédiate. Ton urgent mais factuel."""
    return call_llm(prompt, max_tokens=120, lang=lang)


def ai_weather_air_comment(city: str, aqi: float, pm25: float, temp: float,
                           humidity: float, wind: float, rain: float,
                           lang: str = 'fr') -> str:
    if lang == 'en':
        prompt = f"""As a health-environment expert, comment on today's situation for a resident of {city}.
Weather: {temp}°C, humidity {humidity}%, wind {wind} km/h, rain {rain} mm. Air quality: AQI={aqi}, PM2.5={pm25} µg/m³.
In 2 sentences: weather-pollution link today + one practical daily tip."""
    else:
        prompt = f"""Expert santé-environnement : commente la situation du jour pour un habitant de {city}.
Météo : {temp}°C, humidité {humidity}%, vent {wind} km/h, pluie {rain} mm. AQI={aqi}, PM2.5={pm25} µg/m³.
En 2 phrases : lien météo-pollution + conseil pratique personnalisé."""
    return call_llm(prompt, max_tokens=180, lang=lang)


def ai_health_gauge(city: str, aqi: float, pm25: float, pm10: float,
                    no2: float, dominant: str, lang: str = 'fr') -> str:
    if lang == 'en':
        prompt = f"""You are an environmental health physician. Explain today's situation to a patient in {city}.
AQI={aqi}, PM2.5={pm25} µg/m³, PM10={pm10} µg/m³, NO₂={no2} µg/m³, dominant pollutant: {dominant}.
In 2–3 sentences: health effects today + practical recommendations (who should protect themselves, how)."""
    else:
        prompt = f"""Médecin en santé environnementale : explique la situation à un patient de {city}.
AQI={aqi}, PM2.5={pm25}, PM10={pm10}, NO₂={no2} µg/m³, polluant dominant : {dominant}.
En 2-3 phrases : effets santé + recommandations pratiques (qui se protéger, comment)."""
    return call_llm(prompt, max_tokens=200, lang=lang)


_ROLE_PERSONA = {
    'fr': {
        "citizen":    "un habitant de la ville qui veut protéger sa santé au quotidien",
        "decision":   "un décideur public cherchant des recommandations politiques et d'action",
        "researcher": "un chercheur ou épidémiologiste analysant les données de pollution",
    },
    'en': {
        "citizen":    "a city resident who wants to protect their daily health",
        "decision":   "a public decision-maker seeking policy and action recommendations",
        "researcher": "a researcher or epidemiologist analysing pollution data",
    },
}

_TAB_CONTEXT = {
    'fr': {
        "my_city": "Ma Ville (données locales en temps réel)", "health": "Santé (recommandations médicales)",
        "alerts": "Alertes (villes à risque)", "today": "Vue nationale (toutes les villes)",
        "trends": "Tendances & Comparaison", "regions": "Analyse régionale",
        "policies": "Recommandations politiques", "simulation": "Simulateur 'Et si'",
        "models": "Modèles ML & performance",
    },
    'en': {
        "my_city": "My City (real-time local data)", "health": "Health (medical recommendations)",
        "alerts": "Alerts (at-risk cities)", "today": "National view (all cities)",
        "trends": "Trends & Comparison", "regions": "Regional analysis",
        "policies": "Policy recommendations", "simulation": "What-if simulator",
        "models": "ML Models & performance",
    },
}


def ai_chatbot_response(question: str, city: str, aqi: float, pm25: float,
                        pm10: float, no2: float, o3: float, so2: float,
                        trend: float, region: str,
                        role: str = "citizen", tab: str = "",
                        history: list[dict] | None = None,
                        lang: str = 'fr') -> str:
    persona = _ROLE_PERSONA.get(lang, _ROLE_PERSONA['fr']).get(role, _ROLE_PERSONA['fr']['citizen'])
    tab_ctx = _TAB_CONTEXT.get(lang, _TAB_CONTEXT['fr']).get(tab, "")

    history_block = ""
    if history:
        u_lbl = "User" if lang == 'en' else "Utilisateur"
        a_lbl = "Assistant"
        lines = "\n".join(
            f"{u_lbl if h['role'] == 'user' else a_lbl}: {h['content']}"
            for h in history[-6:]
        )
        history_block = f"\n{'Recent history' if lang=='en' else 'Historique récent'} :\n{lines}\n"

    if lang == 'en':
        aqi_cat = ('Good' if aqi <= 50 else 'Moderate' if aqi <= 100 else
                   'Unhealthy for Sensitive' if aqi <= 150 else 'Unhealthy' if aqi <= 200 else 'Very Unhealthy')
        national_kw = ("national", "cameroon", "country", "all cities", "global", "overall")
    else:
        aqi_cat = ('Bon' if aqi <= 50 else 'Modéré' if aqi <= 100 else
                   'Mauvais (sensibles)' if aqi <= 150 else 'Mauvais' if aqi <= 200 else 'Très mauvais')
        national_kw = ("national", "cameroun", "pays", "toutes", "globale", "ensemble")

    national_ctx = ""
    if any(w in question.lower() for w in national_kw):
        try:
            from api_client import load_national_stats
            nat = load_national_stats() or {}
            if nat:
                if lang == 'en':
                    national_ctx = f"\nNational context: avg AQI={nat.get('national_avg_aqi','?')}, avg PM2.5={nat.get('national_avg_pm25','?')} µg/m³"
                else:
                    national_ctx = f"\nContexte national : AQI moyen={nat.get('national_avg_aqi','?')}, PM2.5 moyen={nat.get('national_avg_pm25','?')} µg/m³"
        except Exception:
            pass

    if lang == 'en':
        prompt = f"""You are speaking to {persona}.
Active tab: {tab_ctx or 'general'}
Real-time data — {city} (region {region}):
AQI={aqi} ({aqi_cat}), PM2.5={pm25} µg/m³ ({round(pm25/15,1)}× WHO), PM10={pm10} µg/m³, NO₂={no2} µg/m³, O₃={o3} µg/m³, SO₂={so2} µg/m³ | Trend: {trend:+.1f}%{national_ctx}
{history_block}
Question: {question}
Adapt your language level to the profile. Use provided data. Max 3–4 sentences."""
    else:
        prompt = f"""Tu parles à {persona}.
Onglet actif : {tab_ctx or 'général'}
Données temps réel — {city} (région {region}) :
AQI={aqi} ({aqi_cat}), PM2.5={pm25} µg/m³ ({round(pm25/15,1)}× OMS), PM10={pm10}, NO₂={no2}, O₃={o3}, SO₂={so2} µg/m³ | Tendance : {trend:+.1f}%{national_ctx}
{history_block}
Question : {question}
Adapte au profil. Utilise les données fournies. 3-4 phrases max."""
    return call_llm(prompt, max_tokens=260, temperature=0.5, lang=lang)


def ai_pollutant_risks(city: str, pollutants: list[tuple], lang: str = 'fr') -> dict[str, str]:
    """pollutants: [(name, value, threshold, unit), ...]"""
    lines = "\n".join(
        f"- {n}: {v:.1f} {u} (WHO limit {thr} {u}, ratio {v/max(thr,0.1):.2f}x)"
        for n, v, thr, u in pollutants
    )
    if lang == 'en':
        prompt = f"""Health analysis for {city}. For each pollutant below, write ONE short phrase (max 12 words) describing the health impact. Reply line by line in strict format "NAME: phrase":\n\n{lines}"""
    else:
        prompt = f"""Analyse sanitaire pour {city}. Pour chaque polluant, rédige UNE phrase courte (max 12 mots) sur l'impact santé. Format strict "NOM: phrase":\n\n{lines}"""
    raw = call_llm(prompt, max_tokens=160, temperature=0.3, lang=lang)
    result = {}
    for line in (raw or "").split("\n"):
        if ":" in line:
            k, _, v = line.partition(":")
            k = k.strip("- ").strip()
            if k:
                result[k] = v.strip()
    return result


def ai_simulation_insight(city: str, base_aqi: float, new_aqi: float,
                          variation: float, main_factor: str,
                          pm25: float, no2: float, lang: str = 'fr') -> str:
    if lang == 'en':
        direction = "increase" if variation > 0 else "decrease"
        prompt = f"""You are analyzing a 'what-if' simulation result for {city} (Cameroon).
Base AQI={base_aqi:.0f} → Simulated AQI={new_aqi:.0f} ({direction} of {abs(variation):.1f} pts)
Simulated parameters: PM2.5={pm25} µg/m³, NO₂={no2} µg/m³. Dominant factor: {main_factor}
In 2–3 sentences: interpret for a researcher (physico-chemical mechanisms, health implications), then one targeted policy recommendation."""
    else:
        direction = "hausse" if variation > 0 else "baisse"
        prompt = f"""Simulation 'Et si' pour {city}. AQI={base_aqi:.0f} → {new_aqi:.0f} ({direction} de {abs(variation):.1f} pts)
PM2.5={pm25}, NO₂={no2} µg/m³. Facteur dominant : {main_factor}
En 2-3 phrases pour un chercheur : mécanismes + implication sanitaire + recommandation politique ciblée."""
    return call_llm(prompt, max_tokens=220, lang=lang)


def ai_alert_summary(worst_city: str, worst_aqi: float, n_at_risk: int, lang: str = 'fr') -> str:
    if lang == 'en':
        prompt = f"""Health alert for Cameroonian citizens. {n_at_risk} cities at risk, worst: {worst_city} (AQI={worst_aqi}).
In 2 sentences: health risk + recommended protection for vulnerable groups (children, elderly, asthmatics)."""
    else:
        prompt = f"""Alerte sanitaire citoyens camerounais. {n_at_risk} villes à risque, pire : {worst_city} (AQI={worst_aqi}).
En 2 phrases : risque sanitaire + protection pour groupes vulnérables (enfants, âgés, asthmatiques)."""
    return call_llm(prompt, max_tokens=150, lang=lang)
