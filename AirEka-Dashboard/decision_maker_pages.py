"""
AirEka — Pages pour le rôle Décideur (Maire)
Indicateurs stratégiques, tableaux de bord territoriaux
"""

from dash import html, dcc
import plotly.graph_objects as go
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import random
import dash_leaflet as dl
from concurrent.futures import ThreadPoolExecutor

from app import aqi_color, aqi_label, aqi_bg, aqi_icon, t, fa
from city_utils import get_cities_data as _gcd, get_regions as _gr, get_national_stats as _gns

# Compatibilité : CITIES_DATA et NATIONAL sont recalculés dynamiquement dans chaque fonction
def _CITIES():  return _gcd()
def _NAT():     return _gns(_gcd())
def _REGIONS(): return _gr(_gcd())


def _graph_ai_block(city_data: dict, values: list, kind: str = 'history', lang: str = 'fr'):
    """Bloc IA compact sous un graphique (évolution ou saisonnalité)."""
    try:
        from ai_commentary import call_llm
        city = city_data.get('city', 'National')
        aqi  = city_data.get('aqi', 0)
        pm25 = city_data.get('pm25', 0)
        vals = [v for v in (values or []) if v]
        if not vals:
            return []
        avg = round(sum(vals) / len(vals), 1)
        if kind == 'history':
            if lang == 'en':
                trend = "rising" if vals[-1] > vals[0] else "falling" if vals[-1] < vals[0] else "stable"
                prompt = f"In 2 sentences for a decision-maker: interpret the 7-day AQI trend for {city} (current AQI {aqi}, PM2.5={pm25}µg/m³, trend {trend}, avg {avg}). Recommend one action."
            else:
                trend = "hausse" if vals[-1] > vals[0] else "baisse" if vals[-1] < vals[0] else "stable"
                prompt = f"En 2 phrases pour un décideur : interprète l'évolution AQI de {city} sur 7 jours (AQI {aqi}, PM2.5={pm25}µg/m³, tendance {trend}, moyenne {avg}). Recommande une action."
        else:
            months_fr = ['Jan','Fév','Mar','Avr','Mai','Jun','Jul','Aoû','Sep','Oct','Nov','Déc']
            months_en = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
            peak_m = (months_en if lang=='en' else months_fr)[vals.index(max(vals))]
            if lang == 'en':
                prompt = f"In 2 sentences for a decision-maker: interpret the seasonal AQI pattern for {city} (peak in {peak_m} at {max(vals):.0f}, trough {min(vals):.0f}). Recommend one seasonal measure."
            else:
                prompt = f"En 2 phrases pour un décideur : interprète la saisonnalité AQI de {city} (pic en {peak_m} à {max(vals):.0f}, creux {min(vals):.0f}). Quelle mesure saisonnière préconises-tu ?"
        text = call_llm(prompt, max_tokens=120, temperature=0.4, lang=lang)
        if not text:
            return []
        return [html.Div([
            html.I(className="fas fa-robot", style={'color': '#7c3aed', 'fontSize': '11px', 'marginRight': '6px'}),
            html.Span(text, style={'fontSize': '11px', 'color': 'var(--text-secondary)', 'lineHeight': '1.5'})
        ], style={'marginTop': '10px', 'padding': '10px 12px', 'borderRadius': '10px',
                  'background': 'rgba(124,58,237,0.06)', 'border': '1px solid rgba(124,58,237,0.2)'})]
    except Exception:
        return []


def _ai_trend_block(city: str, aqi_now: float, forecast_values: list, pm25: float, lang: str = 'fr'):
    """Bloc HTML avec commentaire IA sur la tendance — affiché sous les prévisions."""
    from dash import html
    ai_text = ""
    try:
        from ai_commentary import ai_trend_forecast
        ai_text = ai_trend_forecast(city, aqi_now, forecast_values, pm25, lang=lang)
    except Exception:
        pass
    if not ai_text:
        return html.Div()
    return html.Div([
        html.Div([
            html.I(className="fas fa-robot",
                   style={'color': '#7c3aed', 'marginRight': '7px', 'fontSize': '12px'}),
            html.Span("Analyse IA", style={'fontWeight': '700', 'fontSize': '11px', 'color': '#7c3aed'})
        ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '6px', 'marginTop': '10px'}),
        html.P(ai_text, style={
            'fontSize': '11px', 'lineHeight': '1.65', 'color': 'var(--text-primary)',
            'margin': '0', 'whiteSpace': 'pre-wrap'
        })
    ], style={
        'padding': '10px 12px', 'borderRadius': '8px', 'marginTop': '8px',
        'background': 'rgba(124,58,237,0.06)', 'border': '1px solid rgba(124,58,237,0.2)'
    })


def _region_priority_card(i: int, region: str, stats: dict, lang: str = 'fr'):
    """Carte région prioritaire avec recommandations IA."""
    risk = get_risk_level(stats['aqi_avg'], lang)
    ai_text = ""
    try:
        from ai_commentary import ai_policy_region
        dominant = "PM2.5" if stats['pm25_avg'] > stats.get('pm10_avg', 0) * 0.6 else "PM10"
        ai_text = ai_policy_region(region, stats['aqi_avg'], stats['pm25_avg'],
                                   stats['cities'][:4], dominant, lang=lang)
    except Exception:
            pass
    return html.Div([
        html.Div([
            html.Span(f"{i+1}", style={
                'width': '32px', 'height': '32px', 'borderRadius': '50%',
                'background': f"{risk['color']}20", 'color': risk['color'],
                'fontWeight': '800', 'display': 'flex', 'alignItems': 'center',
                'justifyContent': 'center', 'fontSize': '14px'
            }),
            html.Div([
                html.Span(region, style={'fontWeight': '800', 'fontSize': '16px'}),
                html.Span(f"AQI {stats['aqi_avg']:.0f} — {risk['level']}",
                          style={'fontSize': '12px', 'color': risk['color'], 'marginLeft': '10px'})
            ], style={'flex': '1'})
        ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '12px'}),
        html.Div([
            html.I(className="fas fa-city", style={'marginRight': '6px', 'fontSize': '11px'}),
            html.Span(f"{'Cities' if lang=='en' else 'Villes'}: {', '.join(stats['cities'][:3])}{'...' if len(stats['cities']) > 3 else ''}",
                      style={'fontSize': '11px'})
        ], style={'marginBottom': '6px'}),
        html.Div([
            html.I(className="fas fa-smog", style={'marginRight': '6px', 'fontSize': '11px', 'color': '#ff1744'}),
            html.Span(f"PM2.5: {stats['pm25_avg']:.1f} µg/m³ — {stats['pm25_avg']/15:.1f}× {'WHO' if lang=='en' else 'OMS'}",
                      style={'fontSize': '11px'})
        ], style={'marginBottom': '10px'}),
        # Recommandations IA
        html.Div([
            html.Div([
                html.I(className="fas fa-robot",
                       style={'color': '#7c3aed', 'marginRight': '6px', 'fontSize': '11px'}),
                html.Span('AI Recommendations' if lang=='en' else 'Recommandations IA',
                          style={'fontWeight': '700', 'fontSize': '10px', 'color': '#7c3aed'})
            ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '5px'}),
            html.P(ai_text if ai_text else ('Analysis in progress…' if lang=='en' else 'Analyse en cours…'),
                   style={'fontSize': '10px', 'lineHeight': '1.6',
                          'color': 'var(--text-primary)', 'margin': '0', 'whiteSpace': 'pre-wrap'})
        ], style={
            'padding': '8px 10px', 'borderRadius': '8px',
            'background': 'rgba(124,58,237,0.06)', 'border': '1px solid rgba(124,58,237,0.2)'
        }) if ai_text else html.Div([
            html.I(className="fas fa-clipboard-list",
                   style={'marginRight': '6px', 'fontSize': '11px', 'color': '#00d4ff'}),
            html.Span('Recommended actions:' if lang=='en' else 'Actions recommandées:', style={'fontWeight': '600', 'fontSize': '11px'}),
            html.Ul([
                html.Li('Low emission zone (LEZ) city center' if lang=='en' else 'Zone à faibles émissions (ZFE) centre-ville',
                        style={'fontSize': '10px', 'marginLeft': '20px'}),
                html.Li('Stricter vehicle technical inspection' if lang=='en' else 'Contrôle technique renforcé pour véhicules',
                        style={'fontSize': '10px', 'marginLeft': '20px'}),
                html.Li('Protection of sensitive populations' if lang=='en' else 'Protection des populations sensibles',
                        style={'fontSize': '10px', 'marginLeft': '20px'}),
            ], style={'margin': '4px 0 0 0'})
        ])
    ], style={
        'padding': '16px', 'borderRadius': '16px',
        'background': f"{risk['color']}08", 'border': f'2px solid {risk["color"]}50',
        'boxShadow': f'0 0 8px {risk["color"]}30', 'flex': '1'
    })


def get_region_stats():
    """Calcule les statistiques par région à partir des données."""
    CITIES_DATA = _CITIES()
    region_stats = {}

    if not CITIES_DATA:
        return {
            'Centre': {'cities': ['Yaoundé', 'Bafia', 'Mbalmayo'], 'aqi_avg': 178, 'pm25_avg': 72.3, 'pm10_avg': 118.5, 'no2_avg': 42.8, 'so2_avg': 28.1, 'o3_avg': 38.2, 'count': 3},
            'Littoral': {'cities': ['Douala', 'Edéa'], 'aqi_avg': 165, 'pm25_avg': 68.2, 'pm10_avg': 112.5, 'no2_avg': 38.5, 'so2_avg': 25.2, 'o3_avg': 35.5, 'count': 2},
            'Nord': {'cities': ['Garoua', 'Guider'], 'aqi_avg': 145, 'pm25_avg': 58.9, 'pm10_avg': 97.3, 'no2_avg': 35.2, 'so2_avg': 24.5, 'o3_avg': 32.5, 'count': 2},
            'Extrême-Nord': {'cities': ['Maroua', 'Kousséri'], 'aqi_avg': 132, 'pm25_avg': 54.3, 'pm10_avg': 89.7, 'no2_avg': 32.1, 'so2_avg': 22.3, 'o3_avg': 34.2, 'count': 2},
            'Est': {'cities': ['Bertoua'], 'aqi_avg': 88, 'pm25_avg': 37.2, 'pm10_avg': 61.5, 'no2_avg': 22.5, 'so2_avg': 14.8, 'o3_avg': 39.5, 'count': 1},
            'Ouest': {'cities': ['Bafoussam', 'Dschang'], 'aqi_avg': 103, 'pm25_avg': 42.5, 'pm10_avg': 70.0, 'no2_avg': 27.0, 'so2_avg': 17.3, 'o3_avg': 42.5, 'count': 2},
            'Adamaoua': {'cities': ['Ngaoundéré', 'Tibati'], 'aqi_avg': 103, 'pm25_avg': 43.1, 'pm10_avg': 71.2, 'no2_avg': 27.2, 'so2_avg': 18.0, 'o3_avg': 38.5, 'count': 2},
            'Sud': {'cities': ['Kribi', 'Ebolowa'], 'aqi_avg': 45, 'pm25_avg': 18.5, 'pm10_avg': 30.8, 'no2_avg': 12.0, 'so2_avg': 6.8, 'o3_avg': 43.6, 'count': 2},
            'Sud-Ouest': {'cities': ['Buea', 'Limbe'], 'aqi_avg': 45, 'pm25_avg': 18.4, 'pm10_avg': 30.6, 'no2_avg': 12.3, 'so2_avg': 6.7, 'o3_avg': 47.1, 'count': 2},
            'Nord-Ouest': {'cities': ['Bamenda', 'Kumbo'], 'aqi_avg': 41, 'pm25_avg': 16.9, 'pm10_avg': 28.2, 'no2_avg': 11.3, 'so2_avg': 6.1, 'o3_avg': 48.8, 'count': 2},
        }
    
    for city in CITIES_DATA:
        region = city['region']
        if region not in region_stats:
            region_stats[region] = {
                'cities': [], 'aqi_sum': 0, 'pm25_sum': 0, 'pm10_sum': 0,
                'no2_sum': 0, 'so2_sum': 0, 'o3_sum': 0, 'count': 0
            }
        region_stats[region]['cities'].append(city['city'])
        region_stats[region]['aqi_sum'] += city['aqi']
        region_stats[region]['pm25_sum'] += city['pm25']
        region_stats[region]['pm10_sum'] += city['pm10']
        region_stats[region]['no2_sum'] += city['no2']
        region_stats[region]['so2_sum'] += city.get('so2', 0)
        region_stats[region]['o3_sum'] += city.get('o3', 0)
        region_stats[region]['count'] += 1
    
    for region, stats in region_stats.items():
        stats['aqi_avg'] = round(stats['aqi_sum'] / stats['count'], 1)
        stats['pm25_avg'] = round(stats['pm25_sum'] / stats['count'], 1)
        stats['pm10_avg'] = round(stats['pm10_sum'] / stats['count'], 1)
        stats['no2_avg'] = round(stats['no2_sum'] / stats['count'], 1)
        stats['so2_avg'] = round(stats['so2_sum'] / stats['count'], 1) if stats['so2_sum'] else 0
        stats['o3_avg'] = round(stats['o3_sum'] / stats['count'], 1) if stats['o3_sum'] else 0
        stats['risk_level'] = get_risk_level(stats['aqi_avg'])
    
    return region_stats


def get_risk_level(aqi, lang='fr'):
    """Détermine le niveau de risque en fonction de l'AQI."""
    en = (lang == 'en')
    if aqi <= 50:
        return {'level': 'Low' if en else 'Faible',
                'color': '#00e676', 'icon': 'fa-check-circle',
                'action': 'Normal monitoring' if en else 'Surveillance normale'}
    elif aqi <= 100:
        return {'level': 'Moderate' if en else 'Modéré',
                'color': '#eab308', 'icon': 'fa-exclamation-circle',
                'action': 'Inform sensitive groups' if en else 'Information populations sensibles'}
    elif aqi <= 150:
        return {'level': 'High' if en else 'Élevé',
                'color': '#ff9100', 'icon': 'fa-exclamation-triangle',
                'action': 'Recommendations for at-risk groups' if en else 'Recommandations groupes à risque'}
    elif aqi <= 200:
        return {'level': 'Very high' if en else 'Très élevé',
                'color': '#ff1744', 'icon': 'fa-skull',
                'action': 'Restrictions — Health alert' if en else 'Restrictions - Alerte sanitaire'}
    else:
        return {'level': 'Critical' if en else 'Critique',
                'color': '#d500f9', 'icon': 'fa-biohazard',
                'action': 'EMERGENCY — Activate crisis plan' if en else 'URGENCE - Activation plan ORSEC'}


def create_strategic_map(theme='dark', lang='fr'):
    """Crée la carte stratégique avec zones à risque."""
    CITIES_DATA = _CITIES()
    tile_url = "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png" if theme == 'dark' else "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
    en = (lang == 'en')

    markers = []
    for city in CITIES_DATA:
        col = aqi_color(city['aqi'])
        is_critical = city['aqi'] > 150
        is_alert = city['aqi'] > 100

        popup_html = html.Div([
            html.Strong(city['city'], style={'fontSize': '16px', 'color': col}),
            html.Div([html.Span("AQI: ", style={'fontWeight': '600'}),
                      html.Span(f"{city['aqi']}", style={'fontWeight': '800', 'color': col})]),
            html.Div([html.Span(f"PM2.5: {city['pm25']} µg/m³", style={'fontSize': '12px'})]),
            html.Div([
                html.I(className="fas fa-exclamation-triangle", style={'marginRight': '4px'}),
                html.Span(
                    ("PRIORITY ACTION" if is_critical else "MONITORING" if is_alert else "NORMAL")
                    if en else
                    ("ACTION PRIORITAIRE" if is_critical else "SURVEILLANCE" if is_alert else "NORMAL"),
                    style={'color': '#ff1744' if is_critical else '#ff9100' if is_alert else '#00e676'}
                )
            ])
        ], style={'minWidth': '160px', 'padding': '8px'})
        
        markers.append(dl.CircleMarker(
            center=[city['lat'], city['lon']],
            radius=12 if is_critical else 8 if is_alert else 5,
            color=col, fillColor=col, fillOpacity=0.8 if is_critical else 0.6, weight=2 if is_critical else 1.5,
            children=dl.Popup(popup_html)
        ))
    
    return dl.Map(
        children=[dl.TileLayer(url=tile_url, attribution='&copy; OpenStreetMap'), dl.LayerGroup(markers), dl.ScaleControl()],
        center=[5.5, 12.3], zoom=6,
        style={'height': '400px', 'width': '100%', 'borderRadius': '16px', 'border': f'1px solid var(--border)'}
    )


def create_dashboard_page(city_name, lang='fr', theme='dark'):
    """Page Tableau de bord stratégique du décideur."""
    CITIES_DATA = _CITIES()
    NATIONAL = _NAT()
    REGIONS = _REGIONS()
    region_stats = get_region_stats()
    
    # Calcul des KPIs
    alert_cities = [c for c in CITIES_DATA if c['aqi'] > 100]
    critical_cities = [c for c in CITIES_DATA if c['aqi'] > 150]
    moderate_cities = [c for c in CITIES_DATA if 50 < c['aqi'] <= 100]
    national_risk = get_risk_level(sum(s['aqi_avg'] for s in region_stats.values()) / len(region_stats))
    
    # Polluants nationaux
    national_pm25 = round(sum(c['pm25'] for c in CITIES_DATA) / len(CITIES_DATA), 1)
    national_no2 = round(sum(c['no2'] for c in CITIES_DATA) / len(CITIES_DATA), 1)
    national_so2 = round(sum(c.get('so2', 0) for c in CITIES_DATA) / len(CITIES_DATA), 1)
    national_o3 = round(sum(c.get('o3', 0) for c in CITIES_DATA) / len(CITIES_DATA), 1)
    
    # Top 10 villes
    top_cities = sorted(CITIES_DATA, key=lambda x: x['aqi'], reverse=True)[:10]
    
    # Classement régions
    sorted_regions = sorted(region_stats.items(), key=lambda x: x[1]['aqi_avg'], reverse=True)
    
    # Régions prioritaires (top 3)
    top_regions = sorted_regions[:3]

    # Jauge AQI national
    national_aqi = round(sum(c['aqi'] for c in CITIES_DATA) / len(CITIES_DATA), 1)

    header_color = national_risk['color']

    # Listes de villes pour l'affichage détaillé dans les KPI
    critical_names = ', '.join([c['city'] for c in critical_cities[:5]]) or '—'
    alert_names    = ', '.join([c['city'] for c in alert_cities if c['aqi'] <= 150][:5]) or '—'
    moderate_names = ', '.join([c['city'] for c in moderate_cities[:4]]) or '—'


    return html.Div([
        # En-tête
        html.Div([
            html.Div([
                html.I(className="fas fa-landmark", style={'color': header_color, 'fontSize': '32px', 'marginRight': '14px'}),
                html.Div([
                    html.H1(t('tab_dashboard', lang), style={'fontSize': '24px', 'fontWeight': '800', 'margin': '0'}),
                    html.P(t('dashboard_desc', lang), style={'fontSize': '12px', 'color': 'var(--text-secondary)'})
                ])
            ], style={'display': 'flex', 'alignItems': 'center'})
        ], style={'padding': '20px', 'borderRadius': '20px', 'marginBottom': '24px', 'background': f"{header_color}08", 'border': f'2px solid {header_color}60', 'boxShadow': f'0 0 20px {header_color}20'}),
        
        # KPI STRATÉGIQUES (8 cartes avec détail des villes)
        html.Div([
            # Alerte rouge — villes critiques avec détail
            html.Div([
                html.I(className="fas fa-bell", style={'color': '#ff1744', 'fontSize': '24px', 'marginBottom': '6px'}),
                html.H3(f"{len(critical_cities)}", style={'fontSize': '32px', 'fontWeight': '800', 'margin': '0', 'color': '#ff1744'}),
                html.Span(t('critical_cities_lbl', lang) if t else "villes critiques",
                          style={'fontSize': '11px', 'color': 'var(--text-secondary)', 'display': 'block'}),
                html.Small("AQI > 150", style={'fontSize': '9px', 'color': '#ff1744', 'display': 'block', 'margin': '2px 0'}),
                html.Div(critical_names,
                         style={'fontSize': '9px', 'color': '#ff174499', 'marginTop': '6px',
                                'padding': '4px 8px', 'background': '#ff174410',
                                'borderRadius': '8px', 'lineHeight': '1.4'}) if len(critical_cities) > 0 else None,
            ], className='kpi-card-hover', style={'textAlign': 'center', 'padding': '14px', 'borderRadius': '16px', 'background': 'var(--bg-surface)', 'border': '2px solid #ff174460', 'boxShadow': '0 0 8px #ff174430'}),

            # Alerte orange — avec détail
            html.Div([
                html.I(className="fas fa-exclamation-triangle", style={'color': '#ff9100', 'fontSize': '24px', 'marginBottom': '6px'}),
                html.H3(f"{len(alert_cities) - len(critical_cities)}", style={'fontSize': '32px', 'fontWeight': '800', 'margin': '0', 'color': '#ff9100'}),
                html.Span(t('alert_cities_lbl', lang) if t else "villes en alerte",
                          style={'fontSize': '11px', 'color': 'var(--text-secondary)', 'display': 'block'}),
                html.Small("AQI 100–150", style={'fontSize': '9px', 'color': '#ff9100', 'display': 'block', 'margin': '2px 0'}),
                html.Div(alert_names,
                         style={'fontSize': '9px', 'color': '#ff910099', 'marginTop': '6px',
                                'padding': '4px 8px', 'background': '#ff910010',
                                'borderRadius': '8px', 'lineHeight': '1.4'}) if (len(alert_cities) - len(critical_cities)) > 0 else None,
            ], className='kpi-card-hover', style={'textAlign': 'center', 'padding': '14px', 'borderRadius': '16px', 'background': 'var(--bg-surface)', 'border': '2px solid #ff910060', 'boxShadow': '0 0 8px #ff910030'}),

            # Surveillance — avec détail
            html.Div([
                html.I(className="fas fa-eye", style={'color': '#eab308', 'fontSize': '24px', 'marginBottom': '6px'}),
                html.H3(f"{len(moderate_cities)}", style={'fontSize': '32px', 'fontWeight': '800', 'margin': '0', 'color': '#eab308'}),
                html.Span(t('monitored_cities_lbl', lang) if t else "villes surveillées",
                          style={'fontSize': '11px', 'color': 'var(--text-secondary)', 'display': 'block'}),
                html.Small("AQI 50–100", style={'fontSize': '9px', 'color': '#eab308', 'display': 'block', 'margin': '2px 0'}),
                html.Div(moderate_names,
                         style={'fontSize': '9px', 'color': '#eab30899', 'marginTop': '6px',
                                'padding': '4px 8px', 'background': '#eab30810',
                                'borderRadius': '8px', 'lineHeight': '1.4'}) if len(moderate_cities) > 0 else None,
            ], className='kpi-card-hover', style={'textAlign': 'center', 'padding': '14px', 'borderRadius': '16px', 'background': 'var(--bg-surface)', 'border': '2px solid #eab30860', 'boxShadow': '0 0 8px #eab30830'}),
            
            # AQI national avec jauge
            html.Div([
                html.I(className="fas fa-chart-line", style={'color': header_color, 'fontSize': '28px', 'marginBottom': '8px'}),
                html.H3(f"{national_aqi:.0f}", style={'fontSize': '32px', 'fontWeight': '800', 'margin': '0', 'color': header_color}),
                html.Span(t('nat_aqi_label', lang), style={'fontSize': '12px', 'color': 'var(--text-secondary)'}),
                html.Small("+8.3% vs 2024", style={'fontSize': '9px', 'color': '#ff1744'})
            ], className='kpi-card-hover', style={'textAlign': 'center', 'padding': '16px', 'borderRadius': '16px', 'background': 'var(--bg-surface)', 'border': f'2px solid {header_color}60', 'boxShadow': f'0 0 8px {header_color}30'}),
            
            # PM2.5
            html.Div([
                html.I(className="fas fa-smog", style={'color': '#ff1744', 'fontSize': '28px', 'marginBottom': '8px'}),
                html.H3(f"{national_pm25:.1f}", style={'fontSize': '32px', 'fontWeight': '800', 'margin': '0', 'color': '#ff1744'}),
                html.Span("PM2.5 µg/m³", style={'fontSize': '12px', 'color': 'var(--text-secondary)'}),
                html.Small(f"{national_pm25/25:.1f}× {'WHO' if lang=='en' else 'OMS'}", style={'fontSize': '9px', 'color': '#ff1744'})
            ], className='kpi-card-hover', style={'textAlign': 'center', 'padding': '16px', 'borderRadius': '16px', 'background': 'var(--bg-surface)', 'border': '2px solid #ff174460', 'boxShadow': '0 0 8px #ff174430'}),
            
            # NO₂
            html.Div([
                html.I(className="fas fa-industry", style={'color': '#00d4ff', 'fontSize': '28px', 'marginBottom': '8px'}),
                html.H3(f"{national_no2:.1f}", style={'fontSize': '32px', 'fontWeight': '800', 'margin': '0', 'color': '#00d4ff'}),
                html.Span("NO₂ µg/m³", style={'fontSize': '12px', 'color': 'var(--text-secondary)'}),
                html.Small(f"{national_no2/40:.1f}× {'WHO' if lang=='en' else 'OMS'}", style={'fontSize': '9px', 'color': '#00d4ff'})
            ], className='kpi-card-hover', style={'textAlign': 'center', 'padding': '16px', 'borderRadius': '16px', 'background': 'var(--bg-surface)', 'border': '2px solid #00d4ff60', 'boxShadow': '0 0 8px #00d4ff30'}),
            
            # SO₂
            html.Div([
                html.I(className="fas fa-flask", style={'color': '#a855f7', 'fontSize': '28px', 'marginBottom': '8px'}),
                html.H3(f"{national_so2:.1f}", style={'fontSize': '32px', 'fontWeight': '800', 'margin': '0', 'color': '#a855f7'}),
                html.Span("SO₂ µg/m³", style={'fontSize': '12px', 'color': 'var(--text-secondary)'}),
                html.Small(f"{national_so2/20:.1f}× {'WHO' if lang=='en' else 'OMS'}", style={'fontSize': '9px', 'color': '#a855f7'})
            ], className='kpi-card-hover', style={'textAlign': 'center', 'padding': '16px', 'borderRadius': '16px', 'background': 'var(--bg-surface)', 'border': '2px solid #a855f760', 'boxShadow': '0 0 8px #a855f730'}),
            
            # O₃
            html.Div([
                html.I(className="fas fa-sun", style={'color': '#00e676', 'fontSize': '28px', 'marginBottom': '8px'}),
                html.H3(f"{national_o3:.1f}", style={'fontSize': '32px', 'fontWeight': '800', 'margin': '0', 'color': '#00e676'}),
                html.Span("O₃ µg/m³", style={'fontSize': '12px', 'color': 'var(--text-secondary)'}),
                html.Small(f"{national_o3/100:.1f}× {'WHO' if lang=='en' else 'OMS'}", style={'fontSize': '9px', 'color': '#00e676'})
            ], className='kpi-card-hover', style={'textAlign': 'center', 'padding': '16px', 'borderRadius': '16px', 'background': 'var(--bg-surface)', 'border': '2px solid #00e67660', 'boxShadow': '0 0 8px #00e67630'}),
            
        ], style={'display': 'grid', 'gridTemplateColumns': 'repeat(4, 1fr)', 'gap': '12px', 'marginBottom': '24px'}),
        
        # Ligne: Top 10 villes + Carte
        html.Div([
            # Top 10 villes
            html.Div([
                html.Div([
                    html.I(className="fas fa-ranking-star", style={'color': '#ff9100', 'marginRight': '10px'}),
                    html.Span(t('top_polluted', lang), style={'fontWeight': '700', 'fontSize': '14px'})
                ], style={'marginBottom': '16px'}),
                html.Div([
                    *[html.Div([
                        html.Span(f"{i+1:02d}", style={'width': '32px', 'fontWeight': '800', 'color': aqi_color(c['aqi'])}),
                        html.Span(c['city'], style={'flex': '1', 'fontWeight': '600'}),
                        html.Span(c['region'], style={'fontSize': '11px', 'color': 'var(--text-secondary)', 'width': '90px'}),
                        html.Div(html.Div(style={'width': f"{min(100, c['aqi']/3)}%", 'height': '100%', 'background': aqi_color(c['aqi']), 'borderRadius': '2px'}), style={'width': '100px', 'height': '6px', 'background': 'var(--border)', 'borderRadius': '2px', 'margin': '0 8px'}),
                        html.Span(str(c['aqi']), style={'fontWeight': '800', 'color': aqi_color(c['aqi']), 'width': '35px', 'textAlign': 'right'})
                    ], style={'display': 'flex', 'alignItems': 'center', 'gap': '8px', 'padding': '8px 0', 'borderBottom': '1px solid var(--border)'}) for i, c in enumerate(top_cities)]
                ])
            ], className='card', style={'gridColumn': 'span 5', 'border': '2px solid #ff910060', 'boxShadow': '0 0 10px #ff910030'}),
            
            # Carte
            html.Div([
                html.Div([
                    html.I(className="fas fa-map-marked-alt", style={'color': '#00d4ff', 'marginRight': '10px'}),
                    html.Span(t('risk_zones_map', lang), style={'fontWeight': '700', 'fontSize': '14px'})
                ], style={'marginBottom': '12px'}),
                create_strategic_map(theme, lang),
                html.Div([
                    html.Div([html.Div(style={'width': '12px', 'height': '12px', 'borderRadius': '50%', 'background': '#ff1744', 'marginRight': '6px'}), html.Span('Critical (AQI>150)' if lang=='en' else 'Critique (AQI>150)', style={'fontSize': '10px'})], style={'display': 'inline-flex', 'alignItems': 'center', 'marginRight': '16px'}),
                    html.Div([html.Div(style={'width': '12px', 'height': '12px', 'borderRadius': '50%', 'background': '#ff9100', 'marginRight': '6px'}), html.Span('Alert (100-150)' if lang=='en' else 'Alerte (100-150)', style={'fontSize': '10px'})], style={'display': 'inline-flex', 'alignItems': 'center', 'marginRight': '16px'}),
                    html.Div([html.Div(style={'width': '12px', 'height': '12px', 'borderRadius': '50%', 'background': '#00e676', 'marginRight': '6px'}), html.Span('Normal (<100)' if lang=='en' else 'Normal (<100)', style={'fontSize': '10px'})], style={'display': 'inline-flex', 'alignItems': 'center'})
                ], style={'marginTop': '12px', 'padding': '10px', 'background': 'var(--bg-surface)', 'borderRadius': '10px', 'display': 'flex', 'justifyContent': 'center'})
            ], className='card', style={'gridColumn': 'span 7', 'border': '2px solid #00d4ff60', 'boxShadow': '0 0 10px #00d4ff30'}),
            
        ], style={'display': 'grid', 'gridTemplateColumns': 'repeat(12,1fr)', 'gap': '16px', 'marginBottom': '24px'}),
        
        # Classement par région (barres horizontales)
        html.Div([
            html.Div([
                html.I(className="fas fa-chart-simple", style={'color': '#ff9100', 'marginRight': '10px'}),
                html.Span(t('region_ranking', lang), style={'fontWeight': '700', 'fontSize': '14px'})
            ], style={'marginBottom': '16px'}),
            html.Div([
                *[html.Div([
                    html.Span(region, style={'width': '120px', 'fontWeight': '600'}),
                    html.Div(html.Div(style={'width': f"{min(100, stats['aqi_avg']/3)}%", 'height': '100%', 'background': aqi_color(stats['aqi_avg']), 'borderRadius': '2px'}), style={'flex': '1', 'height': '8px', 'background': 'var(--border)', 'borderRadius': '2px', 'margin': '0 12px'}),
                    html.Span(f"{stats['aqi_avg']:.0f}", style={'fontWeight': '800', 'color': aqi_color(stats['aqi_avg']), 'width': '45px'}),
                    html.Span(risk['action'], style={'fontSize': '10px', 'color': risk['color'], 'width': '140px'})
                ], style={'display': 'flex', 'alignItems': 'center', 'padding': '10px 0', 'borderBottom': '1px solid var(--border)'}) for region, stats in sorted_regions for risk in [get_risk_level(stats['aqi_avg'])]]
            ])
        ], className='card', style={'marginBottom': '24px', 'border': '2px solid #ff910060', 'boxShadow': '0 0 10px #ff910030'}),
        
        # Régions prioritaires (3 cartes détaillées)
        html.Div([
            html.Div([
                html.I(className="fas fa-triangle-exclamation", style={'color': '#ff1744', 'marginRight': '10px'}),
                html.Span(t('priority_regions', lang), style={'fontWeight': '700', 'fontSize': '14px'})
            ], style={'marginBottom': '16px'}),
            html.Div([
                *[_region_priority_card(i, region, stats, lang=lang) for i, (region, stats) in enumerate(top_regions)]
            ], style={'display': 'flex', 'gap': '16px'})
        ], className='card', style={'marginBottom': '24px', 'border': '2px solid #ff174460', 'boxShadow': '0 0 10px #ff174430'})
        
    ], className='anim-fade-up')


def create_combined_page(city_name, lang='fr', theme='dark'):
    """Page fusionnée: Évolution + Saisonnalité + Prévisions - Design Premium"""
    CITIES_DATA = _CITIES()
    region_stats = get_region_stats()
    
    # Données pour l'évolution 7 jours
    dates_7j = [(datetime.now() - timedelta(days=i)).strftime('%d/%m') for i in range(6, -1, -1)]
    
    # Vue nationale ou ville spécifique
    is_national = not city_name or city_name == 'all'
    default_city = None if is_national else city_name
    ctx_label = (t('view_national', lang) + ' — Cameroun') if is_national else default_city

    # Données de la ville (ou moyenne nationale)
    if is_national:
        from api_client import load_national_stats
        nat = load_national_stats() or {}
        city_data = {
            'city': 'National', 'aqi': nat.get('national_avg_aqi', 80),
            'pm25': nat.get('national_avg_pm25', 30), 'no2': nat.get('national_avg_no2', 15),
            'region': 'Cameroun',
        }
        city_data.update({'pm10': 0, 'o3': 0, 'so2': 0, 'trend': nat.get('trend_aqi', 0),
                          'temperature_2m_mean': 26.5, 'humidity': 65, 'wind_speed_10m_max': 12})
    else:
        city_data = next((c for c in CITIES_DATA if c['city'] == default_city), CITIES_DATA[0])
    sim_values = {
        'temp': city_data.get('temperature_2m_mean', 26.5),
        'pm25': city_data['pm25'],
        'humidity': city_data.get('humidity', 65),
        'wind': city_data.get('wind_speed_10m_max', 12)
    }
    
    # Graphique évolution 7 jours (passé) — API
    try:
        import pandas as pd
        if is_national:
            from api_client import load_national_timeseries
            hist_raw = load_national_timeseries(7)
            if hist_raw:
                hist_raw = sorted(hist_raw, key=lambda x: x.get('date', ''))
                dates_7j = [pd.Timestamp(r['date']).strftime('%d/%m') for r in hist_raw]
                city_7j  = [r.get('aqi', city_data['aqi']) for r in hist_raw]
            else:
                raise ValueError("vide")
        else:
            from api_client import load_city_history
            hist7 = load_city_history(default_city, 7)
            if hist7:
                hist7 = sorted(hist7, key=lambda x: x['pred_date'])
                dates_7j = [pd.Timestamp(r['pred_date']).strftime('%d/%m') for r in hist7]
                city_7j  = [r['aqi'] for r in hist7]
            else:
                raise ValueError("vide")
    except Exception:
        base = city_data['aqi']
        city_7j = [max(20, min(300, base + (i - 3) * 2)) for i in range(7)]
    
    # Conversion de la couleur hex en rgba pour Plotly
    color_hex = aqi_color(city_data['aqi'])
    r = int(color_hex[1:3], 16)
    g = int(color_hex[3:5], 16)
    b = int(color_hex[5:7], 16)
    fillcolor_rgba = f'rgba({r}, {g}, {b}, 0.2)'
    
    fig_7j = go.Figure()
    fig_7j.add_trace(go.Scatter(
        x=dates_7j, y=city_7j, mode='lines+markers', name=default_city,
        line=dict(color=color_hex, width=3),
        marker=dict(size=8, color=color_hex),
        fill='tozeroy', fillcolor=fillcolor_rgba,
        hovertemplate='<b>%{x}</b><br>AQI: %{y:.0f}<extra></extra>'
    ))
    fig_7j.add_hline(y=100, line_dash='dot', line_color='#ff9100', line_width=1.5,
                     annotation_text="Seuil OMS", annotation_position='top right',
                     annotation_font_size=9, annotation_font_color='#ff9100')
    _fc = '#e8f0fe' if theme == 'dark' else '#0f1f35'
    _gc = 'rgba(30,48,88,0.25)' if theme == 'dark' else 'rgba(100,120,150,0.2)'
    fig_7j.update_layout(
        height=280, margin=dict(l=40, r=20, t=30, b=40),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color=_fc, family='Inter'),
        xaxis=dict(tickangle=-45, tickfont=dict(size=9, color=_fc), gridcolor=_gc),
        yaxis=dict(title='AQI', tickfont=dict(size=9, color=_fc), gridcolor=_gc),
        hovermode='x unified', showlegend=False
    )
    
    # Saisonnalité (12 mois) — API
    months = (['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'] if lang == 'en'
              else ['Jan','Fév','Mar','Avr','Mai','Jun','Jul','Aoû','Sep','Oct','Nov','Déc'])
    monthly_aqi = [None] * 12
    try:
        if is_national:
            from api_client import load_national_seasonal
            seasonal = load_national_seasonal()
        else:
            from api_client import load_city_seasonal
            seasonal = load_city_seasonal(default_city)
        for entry in seasonal.get('seasonal', []):
            m = entry.get('month')
            if m and 1 <= m <= 12:
                monthly_aqi[m - 1] = entry.get('aqi')
    except Exception:
        pass
    # Remplacer None par 0 (mois sans données)
    monthly_aqi = [v if v is not None else 0 for v in monthly_aqi]
    fig_seasonal = go.Figure()
    fig_seasonal.add_trace(go.Bar(
        x=months, y=monthly_aqi,
        marker_color=[aqi_color(v) for v in monthly_aqi],
        text=[str(v) for v in monthly_aqi], textposition='outside',
        textfont=dict(size=9),
        hovertemplate='<b>%{x}</b><br>' + ('Avg AQI' if lang=='en' else 'AQI moyen') + ': %{y}<extra></extra>'
    ))
    fig_seasonal.update_layout(
        height=280, margin=dict(l=40, r=20, t=30, b=40),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color=_fc, family='Inter'),
        xaxis=dict(tickfont=dict(size=9, color=_fc), gridcolor=_gc),
        yaxis=dict(title='Avg AQI' if lang=='en' else 'AQI moyen', tickfont=dict(size=9, color=_fc), gridcolor=_gc),
        showlegend=False
    )
    
    # PRÉVISIONS 7 JOURS (à partir d'aujourd'hui) — API
    base_aqi = city_data['aqi']
    try:
        from api_client import load_forecast
        import pandas as pd
        _en_fc = (lang == 'en')
        day_names = (['Mon','Tue','Wed','Thu','Fri','Sat','Sun'] if _en_fc
                     else ['Lun','Mar','Mer','Jeu','Ven','Sam','Dim'])
        _fc_city = default_city if not is_national else 'Yaoundé'
        fc7 = load_forecast(_fc_city, 7)
        if fc7:
            fc7 = sorted(fc7, key=lambda x: x['pred_date'])
            forecast_days   = [day_names[pd.Timestamp(r['pred_date']).weekday()] for r in fc7]
            forecast_values = [r['aqi'] for r in fc7]
        else:
            raise ValueError("vide")
    except Exception:
        from datetime import datetime as _dt
        _en_fc = (lang == 'en')
        day_names = (['Mon','Tue','Wed','Thu','Fri','Sat','Sun'] if _en_fc
                     else ['Lun','Mar','Mer','Jeu','Ven','Sam','Dim'])
        _today = _dt.now().weekday()
        forecast_days = [('Today' if _en_fc else 'Auj.')] + [day_names[(_today + i) % 7] for i in range(1, 7)]
        forecast_values = [max(20, min(300, base_aqi + (hash(default_city + str(i)) % 40) - 15)) for i in range(7)]
    
    # Calcul de la moyenne des prévisions
    avg_forecast = sum(forecast_values) / len(forecast_values)
    
    # Déterminer la tendance et le commentaire
    first_val = forecast_values[0]
    last_val = forecast_values[-1]
    
    if last_val > first_val:
        trend_icon = "fa-arrow-trend-up"
        trend_color = "#ff1744"
        if last_val - first_val > 20:
            comment = f" Augmentation significative prévue (+{last_val - first_val:.0f} points). Anticipez des mesures."
        else:
            comment = f" Légère hausse prévue sur les 7 prochains jours."
    elif last_val < first_val:
        trend_icon = "fa-arrow-trend-down"
        trend_color = "#00e676"
        if first_val - last_val > 20:
            comment = f" Amélioration significative prévue (-{first_val - last_val:.0f} points). Bonne nouvelle !"
        else:
            comment = f" Légère baisse prévue, la qualité de l'air devrait s'améliorer."
    else:
        trend_icon = "fa-chart-line"
        trend_color = "#ff9100"
        comment = f" Tendance stable prévue sur les 7 prochains jours."
    
    # Ajouter une précision sur le pic attendu
    max_val = max(forecast_values)
    max_idx = forecast_days[forecast_values.index(max_val)]
    if max_val > 150:
        comment += f" Attention: pic attendu à {max_idx} avec AQI {max_val:.0f}."
    elif max_val > 100:
        comment += f" Pic modéré attendu à {max_idx} (AQI {max_val:.0f})."
    
    # Créer les cartes de prévisions
    forecast_cards = []
    for i, (day, val) in enumerate(zip(forecast_days, forecast_values)):
        col = aqi_color(val)
        icon_cls, _ = aqi_icon(val)
        forecast_cards.append(html.Div([
            html.Div(day, style={'fontSize': '11px', 'fontWeight': '700', 'color': 'var(--text-secondary)', 'marginBottom': '6px'}),
            html.I(className=f"fas {icon_cls}", style={'fontSize': '22px', 'color': col, 'marginBottom': '6px'}),
            html.Div(f"{val:.0f}", style={'fontSize': '20px', 'fontWeight': '800', 'color': col}),
            html.Div(aqi_label(val)[:4] if len(aqi_label(val)) > 4 else aqi_label(val), 
                     style={'fontSize': '9px', 'color': 'var(--text-muted)'})
        ], style={
            'textAlign': 'center', 'padding': '10px 4px', 'borderRadius': '10px',
            'background': f"{col}10", 'border': f'1px solid {col}30',
            'flex': '1', 'transition': 'all 0.2s ease'
        }, className='forecast-card-hover'))
    
    return html.Div([
        # Filtre pour l'évolution
        html.Div([
            html.Div([
                html.I(className="fas fa-city", style={'color': '#ff9100', 'marginRight': '8px', 'fontSize': '14px'}),
                html.Span("Ville", style={'fontWeight': '600', 'fontSize': '12px', 'color': 'var(--text-secondary)'})
            ]),
            dcc.Dropdown(
                id='trend-city-selector',
                options=[{'label': t('view_national', lang), 'value': 'all'}] + [{'label': c['city'], 'value': c['city']} for c in CITIES_DATA],
                value='all',
                style={'width': '220px', 'marginTop': '4px'},
                className='ac-dropdown',
                clearable=False
            )
        ], style={'display': 'flex', 'alignItems': 'center', 'gap': '16px', 'marginBottom': '24px', 
                  'padding': '12px 20px', 'background': 'var(--bg-surface)', 'borderRadius': '14px', 
                  'border': f'1px solid var(--border)'}),
        
        # Ligne: Évolution 7 jours + Saisonnalité + Prévisions (3 blocs côte à côte)
        html.Div([
            # Bloc Évolution 7 jours (passé)
            html.Div([
                html.Div([
                    html.I(className="fas fa-chart-line", style={'color': '#ff9100', 'marginRight': '8px', 'fontSize': '14px'}),
                    html.Span(t('evolution_7d', lang), style={'fontWeight': '700', 'fontSize': '12px', 'letterSpacing': '0.05em'}),
                    html.Span(ctx_label, id='trend-evo-label', style={'marginLeft': 'auto', 'fontSize': '9px', 'color': '#ff9100', 'fontWeight': '600'})
                ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '12px'}),
                dcc.Graph(figure=fig_7j, config={'displayModeBar': False}, id='trend-evolution-graph', style={'height': '280px'}),
                html.Div(_graph_ai_block(city_data, forecast_values, kind='history'), id='trend-evolution-ai')
            ], className='card', style={'gridColumn': 'span 4', 'padding': '14px', 'border': '2px solid #ff910060', 'boxShadow': '0 0 10px #ff910030'}),

            # Bloc Saisonnalité
            html.Div([
                html.Div([
                    html.I(className="fas fa-calendar-alt", style={'color': '#00e676', 'marginRight': '8px', 'fontSize': '14px'}),
                    html.Span(t('seasonality', lang), style={'fontWeight': '700', 'fontSize': '12px', 'letterSpacing': '0.05em'}),
                    html.Span(ctx_label, id='trend-seas-label', style={'marginLeft': 'auto', 'fontSize': '9px', 'color': '#00e676', 'fontWeight': '600'})
                ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '12px'}),
                dcc.Graph(figure=fig_seasonal, config={'displayModeBar': False}, id='trend-seasonal-graph', style={'height': '280px'}),
                html.Div(_graph_ai_block(city_data, monthly_aqi, kind='seasonal'), id='trend-seasonal-ai')
            ], className='card', style={'gridColumn': 'span 4', 'padding': '14px', 'border': '2px solid #00e67660', 'boxShadow': '0 0 10px #00e67630'}),

            # Bloc Prévisions 7 jours
            html.Div([
                html.Div([
                    html.I(className="fas fa-cloud-sun", style={'color': '#00d4ff', 'marginRight': '8px', 'fontSize': '14px'}),
                    html.Span(t('forecast_7d', lang), style={'fontWeight': '700', 'fontSize': '12px', 'letterSpacing': '0.05em'}),
                    html.Span(ctx_label, style={'marginLeft': 'auto', 'fontSize': '9px', 'color': '#00d4ff', 'fontWeight': '600'})
                ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '12px'}),
                
                # Cartes de prévisions
                html.Div(forecast_cards, style={'display': 'flex', 'gap': '6px', 'marginBottom': '12px'}),
                
                # Moyenne et commentaire
                html.Div([
                    html.Div([
                        html.I(className="fas fa-chart-simple", style={'color': aqi_color(avg_forecast), 'marginRight': '8px', 'fontSize': '14px'}),
                        html.Span(f"{'7-day average' if lang=='en' else 'Moyenne sur 7 jours'}: {avg_forecast:.0f} AQI",
                                  style={'fontWeight': '700', 'fontSize': '12px', 'color': aqi_color(avg_forecast)})
                    ], style={'marginBottom': '8px'}),
                    html.Div([
                        html.I(className=f"fas {trend_icon}", style={'color': trend_color, 'marginRight': '8px', 'fontSize': '12px'}),
                        html.Span(comment, style={'fontSize': '11px', 'color': 'var(--text-secondary)', 'lineHeight': '1.4'})
                    ]),
                    # Analyse IA
                    _ai_trend_block(default_city, city_data['aqi'], forecast_values, city_data['pm25'])
                ], style={
                    'padding': '14px',
                    'background': f"{aqi_color(avg_forecast)}15",
                    'borderRadius': '12px',
                    'border': f"2px solid {aqi_color(avg_forecast)}80",
                    'boxShadow': f"0 0 15px {aqi_color(avg_forecast)}30",
                    'marginTop': '12px',
                    'transition': 'all 0.3s ease'
                })
                
            ], className='card', id='trend-forecast-container', style={'gridColumn': 'span 4', 'padding': '14px', 'display': 'flex', 'flexDirection': 'column', 'border': '2px solid #00d4ff60', 'boxShadow': '0 0 10px #00d4ff30'})
            
        ], style={'display': 'grid', 'gridTemplateColumns': 'repeat(12,1fr)', 'gap': '16px', 'marginBottom': '24px'}),
        
        # Ligne 2: Comparaison + Simulation (2 blocs côte à côte)
        html.Div([
            # Bloc Comparaison
            html.Div([
                html.Div([
                    html.I(className="fas fa-scale-balanced", style={'color': '#a855f7', 'marginRight': '8px', 'fontSize': '14px'}),
                    html.Span(t('city_comparison', lang), style={'fontWeight': '700', 'fontSize': '13px', 'letterSpacing': '0.05em'})
                ], style={'marginBottom': '16px'}),
                
                # Sélecteurs de villes
                html.Div([
                    html.Div([
                        html.Div([
                            html.I(className="fas fa-location-dot", style={'color': '#ff1744', 'marginRight': '6px', 'fontSize': '12px'}),
                            html.Span(t('city1_label', lang), style={'fontSize': '11px', 'fontWeight': '600', 'color': 'var(--text-secondary)'})
                        ], style={'marginBottom': '6px'}),
                        dcc.Dropdown(
                            id='compare-city1',
                            options=[{'label': c['city'], 'value': c['city']} for c in CITIES_DATA],
                            value='Yaoundé',
                            className='ac-dropdown',
                            clearable=False
                        )
                    ], style={'flex': '1'}),
                    html.Div([
                        html.Div([
                            html.I(className="fas fa-location-dot", style={'color': '#00d4ff', 'marginRight': '6px', 'fontSize': '12px'}),
                            html.Span(t('city2_label', lang), style={'fontSize': '11px', 'fontWeight': '600', 'color': 'var(--text-secondary)'})
                        ], style={'marginBottom': '6px'}),
                        dcc.Dropdown(
                            id='compare-city2',
                            options=[{'label': c['city'], 'value': c['city']} for c in CITIES_DATA],
                            value='Douala',
                            className='ac-dropdown',
                            clearable=False
                        )
                    ], style={'flex': '1'})
                ], style={'display': 'flex', 'gap': '16px', 'marginBottom': '20px'}),
                
                # Bouton Comparer
                html.Button(
                    [html.I(className="fas fa-chart-simple", style={'marginRight': '8px'}), t('compare_btn', lang)],
                    id='compare-btn',
                    style={
                        'width': '100%', 'padding': '12px', 'borderRadius': '12px',
                        'border': 'none', 'background': 'linear-gradient(135deg, #a855f7, #7c3aed)',
                        'color': 'white', 'fontWeight': '600', 'cursor': 'pointer',
                        'transition': 'all 0.2s ease', 'marginBottom': '20px'
                    }
                ),
                
                # Résultats de comparaison avec loading
                dcc.Loading(
                    type='circle', color='#a855f7',
                    children=html.Div(id='comparison-results', style={'display': 'none'})
                )
                
            ], className='card', style={'gridColumn': 'span 6', 'padding': '20px', 'display': 'flex', 'flexDirection': 'column', 'border': '2px solid #a855f760', 'boxShadow': '0 0 10px #a855f730'}),
            
            # Bloc Simulation
            html.Div([
                html.Div([
                    html.I(className="fas fa-sliders-h", style={'color': '#ff9100', 'marginRight': '8px', 'fontSize': '14px'}),
                    html.Span("SIMULATEUR — ANTICIPER L'IMPACT", style={'fontWeight': '700', 'fontSize': '13px', 'letterSpacing': '0.05em'})
                ], style={'marginBottom': '16px'}),
                
                html.Div([
                    html.P(t('sim_instruction', lang),
                           style={'fontSize': '11px', 'color': 'var(--text-muted)', 'marginBottom': '20px'})
                ]),
                
                # Sliders stylisés
                html.Div([
                    html.Div([
                        html.Div([
                            html.I(className="fas fa-thermometer-half", style={'color': '#ff1744', 'marginRight': '8px', 'fontSize': '12px'}),
                            html.Span(t('temperature_label', lang), style={'fontSize': '12px', 'fontWeight': '500'}),
                            html.Span(id='sim-temp-value', style={'marginLeft': 'auto', 'fontSize': '12px', 'fontWeight': '600', 'color': '#ff1744'})
                        ], style={'display': 'flex', 'marginBottom': '8px'}),
                        dcc.Slider(
                            id='sim-temp', min=15, max=40, step=0.5, value=sim_values['temp'],
                            marks={15: '15°', 25: '25°', sim_values['temp']: f"{sim_values['temp']:.0f}°", 35: '35°', 40: '40°'},
                            tooltip={'placement': 'bottom', 'always_visible': False}
                        )
                    ], style={'marginBottom': '20px'}),
                    
                    html.Div([
                        html.Div([
                            html.I(className="fas fa-smog", style={'color': '#ff1744', 'marginRight': '8px', 'fontSize': '12px'}),
                            html.Span("PM2.5 (µg/m³)", style={'fontSize': '12px', 'fontWeight': '500'}),
                            html.Span(id='sim-pm25-value', style={'marginLeft': 'auto', 'fontSize': '12px', 'fontWeight': '600', 'color': '#ff1744'})
                        ], style={'display': 'flex', 'marginBottom': '8px'}),
                        dcc.Slider(
                            id='sim-pm25', min=0, max=150, step=1, value=sim_values['pm25'],
                            marks={0: '0', 50: '50', sim_values['pm25']: f"{sim_values['pm25']:.0f}", 100: '100', 150: '150'},
                            tooltip={'placement': 'bottom', 'always_visible': False}
                        )
                    ], style={'marginBottom': '20px'}),
                    
                    html.Div([
                        html.Div([
                            html.I(className="fas fa-tint", style={'color': '#00d4ff', 'marginRight': '8px', 'fontSize': '12px'}),
                            html.Span(f"{t('humidity_label', lang)} (%)", style={'fontSize': '12px', 'fontWeight': '500'}),
                            html.Span(id='sim-humidity-value', style={'marginLeft': 'auto', 'fontSize': '12px', 'fontWeight': '600', 'color': '#00d4ff'})
                        ], style={'display': 'flex', 'marginBottom': '8px'}),
                        dcc.Slider(
                            id='sim-humidity', min=20, max=100, step=1, value=sim_values['humidity'],
                            marks={20: '20%', 50: '50%', sim_values['humidity']: f"{sim_values['humidity']:.0f}%", 80: '80%', 100: '100%'},
                            tooltip={'placement': 'bottom', 'always_visible': False}
                        )
                    ], style={'marginBottom': '20px'}),
                    
                    html.Div([
                        html.Div([
                            html.I(className="fas fa-wind", style={'color': '#00e676', 'marginRight': '8px', 'fontSize': '12px'}),
                            html.Span("Vent (km/h)", style={'fontSize': '12px', 'fontWeight': '500'}),
                            html.Span(id='sim-wind-value', style={'marginLeft': 'auto', 'fontSize': '12px', 'fontWeight': '600', 'color': '#00e676'})
                        ], style={'display': 'flex', 'marginBottom': '8px'}),
                        dcc.Slider(
                            id='sim-wind', min=0, max=30, step=1, value=sim_values['wind'],
                            marks={0: '0', 10: '10', sim_values['wind']: f"{sim_values['wind']:.0f}", 20: '20', 30: '30'},
                            tooltip={'placement': 'bottom', 'always_visible': False}
                        )
                    ], style={'marginBottom': '24px'})
                ]),
                
                # Bouton Calculer
                html.Button(
                    [html.I(className="fas fa-calculator", style={'marginRight': '8px'}), "CALCULER L'IMPACT"],
                    id='sim-calc-btn',
                    style={
                        'width': '100%', 'padding': '12px', 'borderRadius': '12px',
                        'border': 'none', 'background': 'linear-gradient(135deg, #ff9100, #ea580c)',
                        'color': 'white', 'fontWeight': '600', 'cursor': 'pointer',
                        'transition': 'all 0.2s ease', 'marginBottom': '20px'
                    }
                ),
                
                # Résultat simulation
                html.Div(id='sim-result', style={'display': 'none'})
                
            ], className='card', style={'gridColumn': 'span 6', 'padding': '20px', 'display': 'flex', 'flexDirection': 'column', 'border': '2px solid #ff910060', 'boxShadow': '0 0 10px #ff910030'})
            
        ], style={'display': 'grid', 'gridTemplateColumns': 'repeat(12,1fr)', 'gap': '20px', 'marginBottom': '24px'})
        
    ], className='anim-fade-up')


def create_policies_page(city_name, lang='fr', theme='dark'):
    """Page Recommandations politiques pour le décideur."""
    CITIES_DATA = _CITIES()
    region_stats = get_region_stats()
    sorted_regions = sorted(region_stats.items(), key=lambda x: x[1]['aqi_avg'], reverse=True)

    # Données pour le rapport PDF
    national_aqi = round(sum(c['aqi'] for c in CITIES_DATA) / len(CITIES_DATA), 1)
    alert_cities = [c for c in CITIES_DATA if c['aqi'] > 100]
    critical_cities = [c for c in CITIES_DATA if c['aqi'] > 150]
    moderate_cities = [c for c in CITIES_DATA if 50 < c['aqi'] <= 100]
    en = (lang == 'en')

    policies = [
        {
            'priority': 'URGENT',
            'color': '#ff1744',
            'icon': 'fa-bell',
            'title': 'Emergency plan activation' if en else "Activation du plan d'urgence",
            'regions': ['Centre', 'Littoral'],
            'cities': ['Yaoundé', 'Douala', 'Bafia'],
            'actions': (
                ['Closure of schools in critical zones',
                 'Ban on polluting industrial activities',
                 'Distribution of FFP2 masks to vulnerable populations',
                 'Setting up air-conditioned reception centres']
                if en else
                ['Fermeture des établissements scolaires dans les zones critiques',
                 'Interdiction des activités industrielles polluantes',
                 'Distribution de masques FFP2 aux populations vulnérables',
                 "Mise en place de centres d'accueil climatisés"]
            ),
            'impact': '-15% PM2.5, -12% AQI',
            'deadline': '48h'
        },
        {
            'priority': 'HIGH' if en else 'ÉLEVÉ',
            'color': '#ff9100',
            'icon': 'fa-car',
            'title': 'Traffic restrictions — LEZ' if en else 'Restrictions de circulation — ZFE',
            'regions': ['Centre', 'Littoral'],
            'cities': ['Yaoundé', 'Douala'],
            'actions': (
                ['Low Emission Zone (LEZ) in city centres',
                 'Enhanced mandatory vehicle technical inspection',
                 'Development of electric public transport',
                 'Deterrent parking on the outskirts']
                if en else
                ['Zone à faibles émissions (ZFE) en centre-ville',
                 'Contrôle technique renforcé pour véhicules',
                 'Développement des transports en commun électriques',
                 'Stationnement dissuasif en périphérie']
            ),
            'impact': '-18% NO₂, -12% PM2.5',
            'deadline': '3 months' if en else '3 mois'
        },
        {
            'priority': 'MODERATE' if en else 'MODÉRÉ',
            'color': '#eab308',
            'icon': 'fa-industry',
            'title': 'Stricter industrial standards' if en else 'Normes industrielles renforcées',
            'regions': ['Littoral', 'Centre'],
            'cities': ['Douala', 'Yaoundé', 'Edéa'],
            'actions': (
                ['Mandatory quarterly emission controls',
                 'Installation of particulate filters',
                 'Financial penalties for exceedances',
                 'Bi-annual environmental audits']
                if en else
                ['Contrôle trimestriel obligatoire des émissions',
                 'Installation de filtres à particules',
                 'Sanctions financières pour dépassements',
                 'Audits environnementaux semestriels']
            ),
            'impact': '-25% SO₂, -15% PM10',
            'deadline': '6 months' if en else '6 mois'
        },
        {
            'priority': 'INFORMATION',
            'color': '#00e676',
            'icon': 'fa-tree',
            'title': 'Urban reforestation programme' if en else 'Programme de reboisement urbain',
            'regions': ['Nord', 'Extrême-Nord', 'Centre'],
            'cities': ['Garoua', 'Maroua', 'Yaoundé'],
            'actions': (
                ['Planting 50,000 trees in urban areas',
                 'Creation of green corridors',
                 'Citizen awareness campaigns',
                 'Community nurseries']
                if en else
                ['Plantation de 50 000 arbres en zones urbaines',
                 'Création de corridors verts',
                 'Sensibilisation citoyenne',
                 'Pépinières communautaires']
            ),
            'impact': '-5 AQI, -8% PM10',
            'deadline': '12 months' if en else '12 mois'
        },
        {
            'priority': 'PREVENTION' if en else 'PRÉVENTION',
            'color': '#00d4ff',
            'icon': 'fa-solar-panel',
            'title': 'Energy transition' if en else 'Transition énergétique',
            'regions': ['National'],
            'cities': ['All cities' if en else 'Toutes les villes'],
            'actions': (
                ['Subsidies for solar panels',
                 'Electrification of public transport',
                 'Energy standards for buildings',
                 '"Zero waste" campaign']
                if en else
                ['Subventions pour panneaux solaires',
                 'Électrification des transports publics',
                 'Normes énergétiques pour bâtiments',
                 'Campagne "Zéro déchet"']
            ),
            'impact': '-40% CO, -20% SO₂',
            'deadline': '24 months' if en else '24 mois'
        }
    ]
    
    header_color = '#00d4ff'

    # Données dynamiques depuis l'API
    from city_utils import get_cities_data as _get_cities
    _cities_dyn = _get_cities()
    national_aqi = round(sum(c['aqi'] for c in _cities_dyn) / max(len(_cities_dyn), 1), 1)
    alert_cities = [c for c in _cities_dyn if c['aqi'] > 100]
    critical_cities = [c for c in _cities_dyn if c['aqi'] > 150]
    worst = sorted(_cities_dyn, key=lambda x: x['aqi'], reverse=True)[0]

    # ── Appels IA parallèles (national + 5 politiques) ────────────────────────
    def _fetch_ai_national():
        try:
            from ai_commentary import ai_dashboard_alert
            return ai_dashboard_alert(worst['city'], worst['aqi'], len(alert_cities), len(critical_cities), lang=lang)
        except Exception:
            return ""

    def _fetch_policy_ai(p):
        try:
            from ai_commentary import ai_policy_region
            return ai_policy_region(
                p['regions'][0] if p['regions'] else 'Cameroun',
                national_aqi,
                sorted_regions[0][1]['pm25_avg'] if sorted_regions else 30,
                p['cities'][:3], lang=lang)
        except Exception:
            return ""

    with ThreadPoolExecutor(max_workers=6) as _ex:
        _fut_nat = _ex.submit(_fetch_ai_national)
        _fut_pol = [_ex.submit(_fetch_policy_ai, p) for p in policies]
        ai_national = _fut_nat.result()
        _policy_ai_texts = [f.result() for f in _fut_pol]

    # Bloc IA national
    ai_national_block = html.Div([
        html.Div([
            html.I(className="fas fa-robot",
                   style={'color': '#7c3aed', 'marginRight': '8px', 'fontSize': '14px'}),
            html.Span(t('ia_analysis_nat', lang),
                      style={'fontWeight': '700', 'fontSize': '13px', 'color': '#7c3aed'})
        ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '8px'}),
        html.P(ai_national if ai_national else (
            f"Situation: {len(alert_cities)} cities on alert, national AQI {national_aqi:.0f}." if lang=='en'
            else f"Situation : {len(alert_cities)} villes en alerte, AQI national {national_aqi:.0f}."),
               style={'fontSize': '12px', 'lineHeight': '1.7', 'color': 'var(--text-primary)',
                      'margin': '0', 'whiteSpace': 'pre-wrap'})
    ], style={
        'padding': '14px', 'borderRadius': '12px', 'marginBottom': '24px',
        'background': 'rgba(124,58,237,0.06)', 'border': '1.5px solid rgba(124,58,237,0.3)'
    })

    def _policy_ai_block(p: dict, idx: int = 0) -> html.Div:
        ai_txt = _policy_ai_texts[idx] if idx < len(_policy_ai_texts) else ""
        return html.Div([
            html.Div([
                html.I(className="fas fa-robot",
                       style={'color': '#7c3aed', 'marginRight': '6px', 'fontSize': '11px'}),
                html.Span('AI Analysis' if lang=='en' else 'Analyse IA',
                          style={'fontWeight': '700', 'fontSize': '10px', 'color': '#7c3aed'})
            ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '5px'}),
            html.P(ai_txt, style={
                'fontSize': '11px', 'lineHeight': '1.65', 'color': 'var(--text-primary)',
                'margin': '0', 'whiteSpace': 'pre-wrap'
            })
        ], style={
            'padding': '10px 12px', 'borderRadius': '8px', 'marginTop': '10px',
            'background': 'rgba(124,58,237,0.06)', 'border': '1px solid rgba(124,58,237,0.2)'
        })

    # Créer les blocs de politiques pour la colonne gauche (3 premiers)
    left_policies = []
    for _pi, p in enumerate(policies[:3]):
        policy_card = html.Div([
            html.Div([
                html.Div([
                    html.I(className=f"fas {p['icon']}", style={'color': p['color'], 'fontSize': '24px', 'marginRight': '12px'}),
                    html.Div([
                        html.Span(p['title'], style={'fontWeight': '800', 'fontSize': '16px', 'color': 'var(--text-primary)'}),
                        html.Span(p['priority'], style={
                            'marginLeft': '12px', 'fontSize': '10px', 'fontWeight': '700',
                            'backgroundColor': f"{p['color']}20", 'color': p['color'],
                            'padding': '2px 10px', 'borderRadius': '20px'
                        })
                    ])
                ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '12px'}),
                html.Div([
                    html.Div([
                        html.I(className="fas fa-map-marker-alt", style={'color': p['color'], 'marginRight': '8px', 'fontSize': '12px'}),
                        html.Span(f"{'Regions' if lang=='en' else 'Régions'}: {', '.join(p['regions'])}", style={'fontSize': '12px', 'color': 'var(--text-secondary)'})
                    ], style={'marginBottom': '8px'}),
                    html.Div([
                        html.I(className="fas fa-city", style={'color': p['color'], 'marginRight': '8px', 'fontSize': '12px'}),
                        html.Span(f"{'Priority cities' if lang=='en' else 'Villes prioritaires'}: {', '.join(p['cities'])}", style={'fontSize': '12px', 'color': 'var(--text-secondary)'})
                    ], style={'marginBottom': '12px'}),
                    html.Div([
                        html.I(className="fas fa-clipboard-list", style={'color': p['color'], 'marginRight': '8px', 'fontSize': '12px'}),
                        html.Span('Actions:' if lang=='en' else 'Actions :', style={'fontWeight': '600', 'fontSize': '12px'})
                    ], style={'marginBottom': '8px'}),
                    html.Ul([
                        html.Li(action, style={'fontSize': '11px', 'marginBottom': '4px', 'color': 'var(--text-secondary)', 'marginLeft': '24px'})
                        for action in p['actions']
                    ]),
                    html.Div([
                        html.Div([
                            html.I(className="fas fa-chart-line", style={'color': p['color'], 'marginRight': '6px', 'fontSize': '11px'}),
                            html.Span(f"{'Estimated impact' if lang=='en' else 'Impact estimé'}: {p['impact']}", style={'fontSize': '11px'})
                        ], style={'marginBottom': '6px'}),
                        html.Div([
                            html.I(className="fas fa-clock", style={'color': p['color'], 'marginRight': '6px', 'fontSize': '11px'}),
                            html.Span(f"{'Implementation timeline' if lang=='en' else 'Délai de mise en œuvre'}: {p['deadline']}", style={'fontSize': '11px'})
                        ])
                    ], style={'padding': '10px', 'background': 'var(--bg-surface)', 'borderRadius': '8px', 'marginTop': '8px'}),
                    _policy_ai_block(p, _pi)
                ])
            ], style={
                'padding': '20px', 'borderRadius': '16px', 'background': f"{p['color']}08",
                'border': f'2px solid {p["color"]}50', 'boxShadow': f'0 0 8px {p["color"]}30',
                'transition': 'all 0.2s ease', 'height': '100%', 'display': 'flex', 'flexDirection': 'column',
                'marginBottom': '20px'
            }, className='policy-card-hover')
        ])
        left_policies.append(policy_card)

    # Créer les blocs de politiques pour la colonne droite (2 derniers)
    right_policies = []
    for _pi, p in enumerate(policies[3:], start=3):
        policy_card = html.Div([
            html.Div([
                html.Div([
                    html.I(className=f"fas {p['icon']}", style={'color': p['color'], 'fontSize': '24px', 'marginRight': '12px'}),
                    html.Div([
                        html.Span(p['title'], style={'fontWeight': '800', 'fontSize': '16px', 'color': 'var(--text-primary)'}),
                        html.Span(p['priority'], style={
                            'marginLeft': '12px', 'fontSize': '10px', 'fontWeight': '700',
                            'backgroundColor': f"{p['color']}20", 'color': p['color'],
                            'padding': '2px 10px', 'borderRadius': '20px'
                        })
                    ])
                ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '12px'}),
                html.Div([
                    html.Div([
                        html.I(className="fas fa-map-marker-alt", style={'color': p['color'], 'marginRight': '8px', 'fontSize': '12px'}),
                        html.Span(f"{'Regions' if lang=='en' else 'Régions'}: {', '.join(p['regions'])}", style={'fontSize': '12px', 'color': 'var(--text-secondary)'})
                    ], style={'marginBottom': '8px'}),
                    html.Div([
                        html.I(className="fas fa-city", style={'color': p['color'], 'marginRight': '8px', 'fontSize': '12px'}),
                        html.Span(f"{'Priority cities' if lang=='en' else 'Villes prioritaires'}: {', '.join(p['cities'])}", style={'fontSize': '12px', 'color': 'var(--text-secondary)'})
                    ], style={'marginBottom': '12px'}),
                    html.Div([
                        html.I(className="fas fa-clipboard-list", style={'color': p['color'], 'marginRight': '8px', 'fontSize': '12px'}),
                        html.Span('Actions:' if lang=='en' else 'Actions :', style={'fontWeight': '600', 'fontSize': '12px'})
                    ], style={'marginBottom': '8px'}),
                    html.Ul([
                        html.Li(action, style={'fontSize': '11px', 'marginBottom': '4px', 'color': 'var(--text-secondary)', 'marginLeft': '24px'})
                        for action in p['actions']
                    ]),
                    html.Div([
                        html.Div([
                            html.I(className="fas fa-chart-line", style={'color': p['color'], 'marginRight': '6px', 'fontSize': '11px'}),
                            html.Span(f"{'Estimated impact' if lang=='en' else 'Impact estimé'}: {p['impact']}", style={'fontSize': '11px'})
                        ], style={'marginBottom': '6px'}),
                        html.Div([
                            html.I(className="fas fa-clock", style={'color': p['color'], 'marginRight': '6px', 'fontSize': '11px'}),
                            html.Span(f"{'Implementation timeline' if lang=='en' else 'Délai de mise en œuvre'}: {p['deadline']}", style={'fontSize': '11px'})
                        ])
                    ], style={'padding': '10px', 'background': 'var(--bg-surface)', 'borderRadius': '8px', 'marginTop': '8px'}),
                    _policy_ai_block(p, _pi)
                ])
            ], style={
                'padding': '20px', 'borderRadius': '16px', 'background': f"{p['color']}08",
                'border': f'2px solid {p["color"]}50', 'boxShadow': f'0 0 8px {p["color"]}30',
                'transition': 'all 0.2s ease', 'height': '100%', 'display': 'flex', 'flexDirection': 'column',
                'marginBottom': '20px'
            }, className='policy-card-hover')
        ])
        right_policies.append(policy_card)
    
    # ── Panneau Alertes Décideur (avant le PDF) ──────────────────────
    alert_panel = html.Div([
        html.Div([
            html.I(className="fas fa-bell-ring", style={'color': '#facc15', 'marginRight': '10px', 'fontSize': '18px'}),
            html.Span(t('weekly_alerts_title', lang),
                      style={'fontWeight': '700', 'fontSize': '14px'})
        ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '10px'}),
        html.P(t('weekly_alerts_desc', lang),
               style={'fontSize': '11px', 'color': 'var(--text-secondary)',
                      'marginBottom': '14px', 'lineHeight': '1.5'}),
        # Email
        dcc.Input(
            id='decision-alert-email',
            type='email',
            placeholder="votre.email@institution.cm",
            style={
                'width': '100%', 'padding': '9px 12px', 'borderRadius': '10px',
                'border': '1px solid var(--border)', 'background': 'var(--bg-input)',
                'color': 'var(--text-primary)', 'fontSize': '12px',
                'marginBottom': '10px', 'boxSizing': 'border-box', 'outline': 'none',
            }
        ),
        # Scope selector
        html.Div([
            html.Span(t('scope_label', lang), style={'fontSize': '11px', 'fontWeight': '600',
                                             'color': 'var(--text-secondary)', 'marginBottom': '6px',
                                             'display': 'block'}),
            dcc.Dropdown(
                id='decision-alert-scope',
                options=[
                    {'label': f"🇨🇲 {'National — all regions' if lang=='en' else 'National — toutes les régions'}", 'value': 'national'},
                ] + [
                    {'label': f"📍 {r}", 'value': f"region:{r}"}
                    for r in sorted(set(c['region'] for c in CITIES_DATA))
                ] + [
                    {'label': f"🏙️ {c['city']}", 'value': f"city:{c['city']}"}
                    for c in sorted(CITIES_DATA, key=lambda x: x['city'])
                ],
                value='national',
                clearable=False,
                className='ac-dropdown',
                style={'marginBottom': '10px'}
            )
        ]),
        # Activate button
        html.Button(
            [html.I(className="fas fa-bell", style={'marginRight': '8px'}),
             "Activer les alertes hebdomadaires (lundi)"],
            id='btn-decision-alert',
            n_clicks=0,
            style={
                'width': '100%', 'padding': '10px', 'borderRadius': '10px',
                'border': 'none',
                'background': 'linear-gradient(135deg, #facc15, #f59e0b)',
                'color': '#0f1f35', 'fontWeight': '700', 'cursor': 'pointer',
                'fontSize': '12px', 'marginBottom': '8px',
                'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center',
            }
        ),
        html.Div(id='decision-alert-result',
                 style={'fontSize': '11px', 'textAlign': 'center', 'marginTop': '6px'}),
    ], style={
        'padding': '18px 20px', 'borderRadius': '16px', 'marginBottom': '16px',
        'background': '#facc1508', 'border': '2px solid #facc1540',
        'boxShadow': '0 0 12px #facc1520'
    })

    # Ajouter le bouton PDF à la colonne droite (sous le dernier bloc)
    pdf_button = html.Div([
        alert_panel,
        html.Button(
            [html.I(className="fas fa-file-pdf", style={'marginRight': '10px', 'fontSize': '16px'}),
             html.Span(t('download_pdf', lang), style={'fontWeight': '700', 'fontSize': '12px'})],
            id='btn-export-pdf',
            style={
                'width': '100%', 'padding': '12px', 'borderRadius': '12px',
                'border': 'none', 'background': '#ff1744',
                'color': 'white', 'cursor': 'pointer', 'fontWeight': '600',
                'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center',
                'transition': 'all 0.2s ease', 'marginTop': '8px'
            }
        ),
        html.P([
            html.I(className="fas fa-info-circle", style={'marginRight': '6px'}),
            ("Report includes: national synthesis, ranking, recommendations and economic impacts" if lang=='en'
             else "Rapport inclut: synthèse nationale, classement, recommandations et impacts économiques")
        ], style={'fontSize': '10px', 'color': 'var(--text-muted)', 'textAlign': 'center', 'marginTop': '10px'})
    ])
    
    # Ajouter le bouton à la colonne droite
    right_policies.append(pdf_button)
    
    # Listes de villes pour l'affichage détaillé dans les KPI
    critical_names = ', '.join([c['city'] for c in critical_cities[:5]]) or '—'
    alert_names    = ', '.join([c['city'] for c in alert_cities if c['aqi'] <= 150][:5]) or '—'
    moderate_names = ', '.join([c['city'] for c in moderate_cities[:4]]) or '—'

    return html.Div([
        # En-tête
        html.Div([
            html.Div([
                html.I(className="fas fa-file-contract", style={'color': header_color, 'fontSize': '28px', 'marginRight': '14px'}),
                html.Div([
                    html.H1(t('policies_title', lang), style={'fontSize': '24px', 'fontWeight': '800', 'margin': '0', 'color': 'var(--text-primary)'}),
                    html.P('Priority actions based on air quality data' if lang=='en' else "Actions prioritaires basées sur les données de qualité de l'air", style={'fontSize': '12px', 'color': 'var(--text-secondary)'})
                ])
            ])
        ], style={'padding': '20px', 'borderRadius': '20px', 'marginBottom': '24px',
                  'background': f"{header_color}08", 'border': f'2px solid {header_color}60',
                  'boxShadow': f'0 0 20px {header_color}20'}),

        # Analyse IA nationale
        ai_national_block,

        # Grille responsive des politiques (2 colonnes)
        html.Div([
            # Colonne gauche
            html.Div(left_policies, style={'display': 'flex', 'flexDirection': 'column', 'flex': '1', 'marginRight': '10px'}),
            
            # Colonne droite (avec synthèse, politiques et bouton PDF)
            html.Div([
                # Synthèse nationale
                html.Div([
                    html.Div([
                        html.I(className="fas fa-chart-line", style={'color': '#ff9100', 'marginRight': '10px', 'fontSize': '18px'}),
                        html.Span(t('national_summary', lang), style={'fontWeight': '700', 'fontSize': '15px', 'color': 'var(--text-primary)'})
                    ], style={'marginBottom': '16px', 'display': 'flex', 'alignItems': 'center'}),
                    html.Div([
                        html.Div([
                            html.Span(t('nat_aqi_label', lang) + ':', style={'fontSize': '12px', 'color': 'var(--text-secondary)'}),
                            html.Span(f"{national_aqi:.0f}", style={'fontSize': '28px', 'fontWeight': '800', 'color': aqi_color(national_aqi), 'display': 'block'})
                        ], style={'textAlign': 'center', 'flex': '1'}),
                        html.Div([
                            html.Span(t('alert_cities_lbl', lang) + ':', style={'fontSize': '12px', 'color': 'var(--text-secondary)'}),
                            html.Span(f"{len(alert_cities)}", style={'fontSize': '28px', 'fontWeight': '800', 'color': '#ff9100', 'display': 'block'})
                        ], style={'textAlign': 'center', 'flex': '1'}),
                        html.Div([
                            html.Span(t('critical_cities_lbl', lang) + ':', style={'fontSize': '12px', 'color': 'var(--text-secondary)'}),
                            html.Span(f"{len(critical_cities)}", style={'fontSize': '28px', 'fontWeight': '800', 'color': '#ff1744', 'display': 'block'})
                        ], style={'textAlign': 'center', 'flex': '1'})
                    ], style={'display': 'flex', 'justifyContent': 'space-around', 'marginBottom': '20px', 'flexWrap': 'wrap', 'gap': '16px'})
                ], style={
                    'padding': '20px', 'borderRadius': '16px', 'background': f"{header_color}08",
                    'border': f'2px solid {header_color}60', 'boxShadow': f'0 0 10px {header_color}40',
                    'marginBottom': '20px'
                }),
                # Politiques de la colonne droite
                html.Div(right_policies, style={'display': 'flex', 'flexDirection': 'column'})
            ], style={'display': 'flex', 'flexDirection': 'column', 'flex': '1', 'marginLeft': '10px'})
            
        ], style={'display': 'flex', 'flexWrap': 'wrap', 'gap': '20px', 'marginBottom': '24px'})
        
    ], className='anim-fade-up')


def get_decision_tab_content(tab_id, city, lang, theme):
    """Dispatch pour les onglets décideur."""
    city_name = city if city and city != 'all' else 'Yaoundé'
    
    if tab_id == 'dashboard':
        return create_dashboard_page(city_name, lang, theme)
    elif tab_id == 'analysis':
        return create_combined_page(city_name, lang, theme)
    elif tab_id == 'policies':
        return create_policies_page(city_name, lang, theme)
    else:
        return html.Div("Page en construction...")