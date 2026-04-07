"""
AirEka Monitor — Pages pour le rôle Citoyen
"""
from dash import html, dcc
import plotly.graph_objects as go
import numpy as np
from datetime import datetime, timedelta
import random
import dash_leaflet as dl
from dash import dcc
from app import make_overview_fallback
from app import aqi_color, aqi_label, aqi_icon, aqi_bg, t, fa
from city_utils import get_cities_data as _get_cities_dyn

def _weather_comment(weather, lang='fr'):
    """Génère un commentaire météo contextuel et humain."""
    temp = weather.get('temperature', 26)
    humidity = weather.get('humidity', 65)
    wind = weather.get('wind_speed', 8)
    precip = weather.get('precipitation', 0)

    if lang == 'fr':
        # Température
        if temp >= 32:
            temp_msg = f"Il fait très chaud ({temp:.1f}°C) — hydratez-vous bien."
        elif temp >= 28:
            temp_msg = f"Journée chaude à {temp:.1f}°C, pensez à vous protéger du soleil."
        elif temp >= 22:
            temp_msg = f"Température agréable de {temp:.1f}°C, bonne journée en perspective !"
        else:
            temp_msg = f"Il fait frais aujourd'hui ({temp:.1f}°C), prévoyez une veste."
        # Humidité
        if humidity >= 80:
            hum_msg = "L'humidité est élevée, la sensation de chaleur est renforcée."
        elif humidity >= 60:
            hum_msg = "Humidité modérée, confort correct."
        else:
            hum_msg = "Air sec aujourd'hui, pensez à vous hydrater."
        # Vent
        wind_msg = f"Vent {'fort' if wind >= 20 else 'modéré' if wind >= 10 else 'faible'} à {wind:.0f} km/h." if wind > 0 else ""
        # Pluie
        rain_msg = f" Précipitations prévues ({precip:.0f} mm)." if precip > 0 else ""
        return f"{temp_msg} {hum_msg} {wind_msg}{rain_msg}".strip()
    else:
        if temp >= 32:
            temp_msg = f"Very hot day ({temp:.1f}°C) — stay hydrated."
        elif temp >= 28:
            temp_msg = f"Warm day at {temp:.1f}°C, protect yourself from the sun."
        elif temp >= 22:
            temp_msg = f"Pleasant temperature of {temp:.1f}°C, enjoy your day!"
        else:
            temp_msg = f"Cool today ({temp:.1f}°C), bring a jacket."
        if humidity >= 80:
            hum_msg = "High humidity makes it feel hotter."
        elif humidity >= 60:
            hum_msg = "Moderate humidity, comfortable conditions."
        else:
            hum_msg = "Dry air today, remember to drink water."
        wind_msg = f"{'Strong' if wind >= 20 else 'Moderate' if wind >= 10 else 'Light'} wind at {wind:.0f} km/h." if wind > 0 else ""
        rain_msg = f" Precipitation expected ({precip:.0f} mm)." if precip > 0 else ""
        return f"{temp_msg} {hum_msg} {wind_msg}{rain_msg}".strip()


def _bar_color(ratio):
    """Couleur de la barre selon le ratio valeur/seuil OMS."""
    if ratio >= 1.0:   return '#ff1744'   # dépassé  → rouge
    if ratio >= 0.75:  return '#ff6b35'   # proche   → rouge-orange
    if ratio >= 0.5:   return '#ff9100'   # modéré   → orange
    return '#00e676'                       # OK       → vert


def _oms_bar_row(p, lang='fr'):
    """Ligne polluant avec barre colorée dynamiquement."""
    ratio = p['value'] / max(p['threshold'], 0.1)
    bar_col = _bar_color(ratio)
    pct = min(100, ratio * 100)
    val_col = bar_col if ratio >= 0.75 else 'var(--text-secondary)'
    if ratio >= 1.0:
        label = "⚠ EXCEEDED" if lang == 'en' else "⚠ DÉPASSÉ"
    else:
        limit_word = "× limit" if lang == 'en' else "× seuil"
        label = f"{ratio:.2f}{limit_word}"
    who_word = "WHO limit" if lang == 'en' else "Seuil OMS"
    return html.Div([
        html.Div([
            html.I(className=f"fas {p['icon']}", style={'color': p['color'], 'marginRight': '6px', 'fontSize': '12px'}),
            html.Span(p['name'], style={'fontWeight': '600', 'fontSize': '12px'}),
            html.Span(f"{p['value']:.0f}", style={'marginLeft': 'auto', 'fontWeight': '700', 'fontSize': '12px', 'color': val_col}),
        ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '4px'}),
        html.Div([
            html.Div(style={
                'width': f"{pct}%", 'height': '6px',
                'background': f'linear-gradient(90deg, {bar_col}99, {bar_col})',
                'borderRadius': '3px', 'transition': 'width 0.4s ease'
            })
        ], style={'background': 'var(--border)', 'borderRadius': '3px', 'marginBottom': '4px'}),
        html.Div([
            html.Span(f"{who_word} : {p['threshold']} {p['unit']}", style={'fontSize': '9px', 'color': 'var(--text-muted)'}),
            html.Span(label, style={'fontSize': '9px', 'color': bar_col, 'marginLeft': '8px', 'fontWeight': '600'}),
        ], style={'display': 'flex', 'marginBottom': '12px'}),
    ])


def _weather_ai_comment(city, aqi, pm25, temp, humidity, wind, rain, lang='fr'):
    """Commentaire météo + qualité air via LLM, retourne '' en cas d'erreur."""
    try:
        from ai_commentary import ai_weather_air_comment
        return ai_weather_air_comment(city, aqi, pm25, temp, humidity, wind, rain, lang=lang) or ""
    except Exception:
        return ""


def create_today_page(city_name, lang='fr'):
    """Page Aujourd'hui - Conditions en temps réel"""
    _cd = _get_cities_dyn()
    c = next((x for x in _cd if x['city'] == city_name), next((x for x in _cd if x['city'] == 'Yaoundé'), _cd[0]))
    
    # Déterminer le statut AQI
    if c['aqi'] <= 50:
        status = {'text': 'Bonne', 'icon': 'fa-face-smile', 'color': '#00e676', 'advice': 'Profitez de l\'extérieur !'}
    elif c['aqi'] <= 100:
        status = {'text': 'Modérée', 'icon': 'fa-face-meh', 'color': '#ffee58', 'advice': 'Personnes sensibles : soyez prudents'}
    elif c['aqi'] <= 150:
        status = {'text': 'Mauvaise pour sensibles', 'icon': 'fa-face-frown-open', 'color': '#ff9100', 'advice': 'Limitez les sorties prolongées'}
    elif c['aqi'] <= 200:
        status = {'text': 'Mauvaise', 'icon': 'fa-face-sad-tear', 'color': '#ff1744', 'advice': 'Évitez les activités extérieures'}
    else:
        status = {'text': 'Dangereuse', 'icon': 'fa-skull', 'color': '#d500f9', 'advice': 'Restez à l\'intérieur !'}
    
    # Jauge simple
    fig_gauge = go.Figure(go.Indicator(
        mode='gauge+number',
        value=c['aqi'],
        domain={'x': [0, 1], 'y': [0, 1]},
        number={'font': {'size': 48, 'color': aqi_color(c['aqi'])}},
        gauge={
            'axis': {'range': [0, 300]},
            'bar': {'color': aqi_color(c['aqi'])},
            'steps': [
                {'range': [0, 50], 'color': 'rgba(0,230,118,0.2)'},
                {'range': [50, 100], 'color': 'rgba(255,238,88,0.2)'},
                {'range': [100, 150], 'color': 'rgba(255,145,0,0.2)'},
                {'range': [150, 200], 'color': 'rgba(255,23,68,0.2)'},
                {'range': [200, 300], 'color': 'rgba(213,0,249,0.2)'},
            ]
        }
    ))
    fig_gauge.update_layout(height=250, margin=dict(t=30, b=20), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    
    return html.Div([
        # Bannière temps réel
        html.Div([
            html.Span(className='live-dot', style={'marginRight': '8px'}),
            html.Span(f"{city_name} · {datetime.now().strftime('%H:%M')}", style={'fontWeight': '600'}),
        ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '16px', 'padding': '8px 12px', 'background': 'var(--bg-surface)', 'borderRadius': '8px'}),
        
        # Jauge
        dcc.Graph(figure=fig_gauge, config={'displayModeBar': False}),
        
        # Statut
        html.Div([
            html.I(className=f"fas {status['icon']}", style={'fontSize': '32px', 'color': status['color']}),
            html.H3(f"AQI {c['aqi']} — {status['text']}", style={'margin': '8px 0', 'color': status['color']}),
            html.P(status['advice'], style={'color': 'var(--text-secondary)'}),
        ], className='text-center', style={'padding': '16px', 'background': f"{status['color']}10", 'borderRadius': '12px', 'margin': '16px 0'}),
        
        # Polluants
        html.Div([
            html.H4("Polluants", style={'marginBottom': '12px'}),
            html.Div([
                html.Div([html.Span("PM2.5", style={'fontWeight': '600'}), html.Span(f"{c['pm25']} µg/m³", style={'float': 'right'})], style={'marginBottom': '4px'}),
                html.Div(html.Div(style={'width': f"{min(100, c['pm25']/150*100)}%", 'height': '6px', 'background': 'var(--red)', 'borderRadius': '3px'}), style={'background': 'var(--border)', 'borderRadius': '3px', 'marginBottom': '12px'}),
                html.Div([html.Span("PM10", style={'fontWeight': '600'}), html.Span(f"{c['pm10']} µg/m³", style={'float': 'right'})], style={'marginBottom': '4px'}),
                html.Div(html.Div(style={'width': f"{min(100, c['pm10']/200*100)}%", 'height': '6px', 'background': 'var(--orange)', 'borderRadius': '3px'}), style={'background': 'var(--border)', 'borderRadius': '3px', 'marginBottom': '12px'}),
                html.Div([html.Span("NO₂", style={'fontWeight': '600'}), html.Span(f"{c['no2']} µg/m³", style={'float': 'right'})], style={'marginBottom': '4px'}),
                html.Div(html.Div(style={'width': f"{min(100, c['no2']/80*100)}%", 'height': '6px', 'background': 'var(--cyan)', 'borderRadius': '3px'}), style={'background': 'var(--border)', 'borderRadius': '3px'}),
            ])
        ], className='card', style={'marginTop': '16px'}),
    ])

def create_my_city_page(city_name, lang='fr', theme='dark'):
    """Page Ma Ville - Design premium avec jauge, recommandations"""
    import dash_leaflet as dl
    from dash import dcc
    
    _cd = _get_cities_dyn()
    c = next((x for x in _cd if x['city'] == city_name), next((x for x in _cd if x['city'] == 'Yaoundé'), _cd[0]))
    
    # Récupération des vraies données météo
    weather = {
        'temperature': c.get('temperature_2m_mean', round(26 + np.random.randn() * 3, 1)),
        'temp_min': c.get('temperature_2m_min', round(22 + np.random.randn() * 2, 1)),
        'temp_max': c.get('temperature_2m_max', round(30 + np.random.randn() * 2, 1)),
        'humidity': c.get('humidity', round(65 + np.random.randn() * 15, 0)),
        'wind_speed': c.get('wind_speed_10m_max', round(8 + np.random.randn() * 4, 1)),
        'precipitation': c.get('precipitation_sum', 0),
        'sunrise': c.get('sunrise', '06:15')[:5] if isinstance(c.get('sunrise'), str) else '06:15',
        'sunset': c.get('sunset', '18:30')[:5] if isinstance(c.get('sunset'), str) else '18:30',
    }
    
    # Calcul de la tendance
    trend = c.get('trend', random.uniform(-15, 20))
    trend_color = '#ff1744' if trend > 0 else '#00e676'
    trend_icon = 'fa-arrow-trend-up' if trend > 0 else 'fa-arrow-trend-down'
    trend_text = f"{'+' if trend > 0 else ''}{trend:.1f}%"
    
    # Couleur de la ville selon AQI
    if c['aqi'] <= 50:
        city_color = '#fbbf24'
        glow_color = 'rgba(251,191,36,0.3)'
    else:
        city_color = aqi_color(c['aqi'])
        glow_color = f"{city_color}40"
    
    # Déterminer le message de qualité
    if c['aqi'] <= 50:
        quality_msg = "excellente ! Profitez pleinement des activités extérieures."
        quality_icon = "fa-face-smile"
        recommendation = "Activités extérieures normales - Ouvrez les fenêtres pour aérer"
        rec_icon = "fa-check-circle"
    elif c['aqi'] <= 100:
        quality_msg = "acceptable. Personnes sensibles : soyez prudentes."
        quality_icon = "fa-face-meh"
        recommendation = "Personnes sensibles : limitez les efforts prolongés - Masque conseillé"
        rec_icon = "fa-exclamation-triangle"
    elif c['aqi'] <= 150:
        quality_msg = "mauvaise pour les personnes sensibles. Limitez les sorties."
        quality_icon = "fa-face-frown"
        recommendation = "Masque FFP2 recommandé - Évitez les activités physiques intenses"
        rec_icon = "fa-mask-face"
    elif c['aqi'] <= 200:
        quality_msg = "mauvaise. Évitez les activités extérieures."
        quality_icon = "fa-face-sad-tear"
        recommendation = "Restez à l'intérieur - Fermez les fenêtres - Purificateur d'air conseillé"
        rec_icon = "fa-house-circle-exclamation"
    else:
        quality_msg = "dangereuse ! Urgence sanitaire, restez chez vous."
        quality_icon = "fa-skull"
        recommendation = "URGENCE : Restez absolument à l'intérieur - Contactez le 1510 en cas de symptômes"
        rec_icon = "fa-truck-medical"
    
    # Polluants
    pollutants = [
        ('PM2.5', c['pm25'], 35, '#ff1744', 'fa-smog'),
        ('PM10', c['pm10'], 50, '#ff9100', 'fa-dust'),
        ('NO₂', c['no2'], 40, '#00d4ff', 'fa-industry'),
        ('O₃', c['o3'], 100, '#00e676', 'fa-sun'),
        ('SO₂', c['so2'], 20, '#a855f7', 'fa-flask'),
    ]
    dominant = max(pollutants, key=lambda x: x[1] / x[2])
    
    # Prévisions 7 jours — API
    base = c['aqi']
    _en = (lang == 'en')
    day_names = (['Mon','Tue','Wed','Thu','Fri','Sat','Sun'] if _en
                 else ['Lun','Mar','Mer','Jeu','Ven','Sam','Dim'])
    try:
        from api_client import load_forecast, load_city_history
        import pandas as pd
        fc_raw = load_forecast(city_name, 7)
        if fc_raw:
            fc_sorted = sorted(fc_raw, key=lambda x: x['pred_date'])
            forecast_values = [r['aqi'] for r in fc_sorted]
            forecast_days = [day_names[pd.Timestamp(r['pred_date']).weekday()] for r in fc_sorted]
        else:
            raise ValueError("vide")
    except Exception:
        from datetime import datetime as _dt
        _today = _dt.now().weekday()
        forecast_days = [('Today' if _en else 'Auj.')] + [day_names[(_today + i) % 7] for i in range(1, 7)]
        forecast_values = [max(20, min(300, base + (hash(city_name + str(i)) % 50) - 20)) for i in range(7)]

    # Graphique d'évolution (30 jours) — API
    try:
        hist_raw = load_city_history(city_name, 30)
        if hist_raw:
            hist_sorted = sorted(hist_raw, key=lambda x: x['pred_date'])
            dates_30  = [pd.Timestamp(r['pred_date']).strftime('%d/%m') for r in hist_sorted]
            values_30 = [r['aqi'] for r in hist_sorted]
        else:
            raise ValueError("vide")
    except Exception:
        random.seed(hash(city_name) % 1000)
        dates_30  = [(datetime.now() - timedelta(days=i)).strftime('%d/%m') for i in range(29, -1, -1)]
        values_30 = [max(20, min(300, base + random.randint(-35, 45) + (29 - i) * 0.3)) for i in range(30)]
    
    # Couleurs selon thème
    grid_color = '#1e3058' if theme == 'dark' else '#c8d8ea'
    text_color = '#7a90b5' if theme == 'dark' else '#4a6080'
    
    # Graphique d'évolution
    fig_evolution = go.Figure()
    fig_evolution.add_trace(go.Scatter(
        x=dates_30, y=values_30, mode='lines',
        line=dict(color=city_color, width=3, shape='spline'),
        fill='tozeroy',
        fillcolor=f"rgba({int(city_color[1:3],16)}, {int(city_color[3:5],16)}, {int(city_color[5:7],16)}, 0.2)",
        name='AQI'
    ))
    fig_evolution.update_layout(
        height=280, margin=dict(t=20, b=30, l=40, r=20),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Inter', color=text_color),
        xaxis=dict(tickangle=-45, tickfont=dict(size=9, color=text_color),
                   gridcolor=grid_color, tickvals=dates_30[::5]),
        yaxis=dict(title='AQI', tickfont=dict(size=10, color=text_color),
                   gridcolor=grid_color, range=[0, max(values_30) + 30],
                   title_font=dict(color=text_color)),
        hovermode='x unified', showlegend=False,
    )
    
    # Graphique comparaison polluants
    fig_pollutants = go.Figure()
    for name, val, threshold, color, icon in pollutants:
        fig_pollutants.add_trace(go.Bar(
            x=[val], y=[name], orientation='h',
            marker=dict(color=color, line=dict(width=0)),
            text=[f"{val:.1f} µg/m³"], textposition='outside',
            textfont=dict(size=10, color=color),
            showlegend=False
        ))
    fig_pollutants.update_layout(
        height=280, margin=dict(l=60, r=50, t=20, b=20),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Inter', color=text_color),
        xaxis=dict(title='Concentration (µg/m³)', tickfont=dict(size=10, color=text_color),
                   gridcolor=grid_color, title_font=dict(color=text_color)),
        yaxis=dict(tickfont=dict(size=11, color=text_color), gridcolor='rgba(0,0,0,0)'),
        showlegend=False
    )
    
    # Carte
    tile_url = "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png" if theme == 'dark' else "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
    
    popup_html = html.Div([
        html.Strong(c['city'], style={'fontSize': '16px', 'color': city_color, 'display': 'block', 'marginBottom': '6px'}),
        html.Div([html.Span("AQI: ", style={'fontWeight': '600'}), html.Span(f"{c['aqi']}", style={'fontWeight': '800', 'color': city_color, 'fontSize': '18px'})]),
        html.Div([html.Span(f"PM2.5: {c['pm25']} µg/m³", style={'fontSize': '12px'})]),
        html.Div([html.Span(aqi_label(c['aqi'], lang), style={'fontSize': '11px', 'color': city_color})], style={'marginTop': '4px'}),
        html.Div([
            html.I(className="fas fa-thermometer-half", style={'marginRight': '4px', 'fontSize': '10px'}),
            html.Span(f"{weather['temperature']}°C", style={'marginRight': '12px'}),
            html.I(className="fas fa-wind", style={'marginRight': '4px', 'fontSize': '10px'}),
            html.Span(f"{weather['wind_speed']} km/h")
        ], style={'marginTop': '8px', 'fontSize': '11px', 'color': 'var(--text-secondary)'})
    ], style={'minWidth': '180px', 'padding': '8px'})
    
    city_map = dl.Map(
        children=[
            dl.TileLayer(url=tile_url, attribution='&copy; OpenStreetMap & CartoDB'),
            dl.CircleMarker(
                center=[c['lat'], c['lon']], radius=14, color=city_color,
                fillColor=city_color, fillOpacity=0.85, weight=3,
                children=dl.Popup(popup_html)
            ),
            dl.ScaleControl(position='bottomleft'),
        ],
        center=[c['lat'], c['lon']], zoom=10,
        style={'height': '280px', 'width': '100%', 'borderRadius': '16px', 'border': f'1px solid var(--border)'}
    )
    
    # Jauge AQI
    gauge_chart = go.Figure(go.Indicator(
        mode='gauge+number',
        value=c['aqi'],
        domain={'x': [0, 1], 'y': [0, 1]},
        number={'font': {'size': 44, 'color': city_color, 'family': 'Inter'}},
        gauge={
            'axis': {'range': [0, 300], 'tickwidth': 1, 'tickcolor': '#7a90b5', 'tickfont': {'size': 9, 'color': '#7a90b5'}},
            'bar': {'color': city_color, 'thickness': 0.25},
            'bgcolor': 'rgba(0,0,0,0)', 'borderwidth': 0,
            'steps': [
                {'range': [0, 50], 'color': 'rgba(0,230,118,0.15)'},
                {'range': [50, 100], 'color': 'rgba(255,238,88,0.15)'},
                {'range': [100, 150], 'color': 'rgba(255,145,0,0.15)'},
                {'range': [150, 200], 'color': 'rgba(255,23,68,0.15)'},
                {'range': [200, 300], 'color': 'rgba(213,0,249,0.15)'},
            ],
            'threshold': {'line': {'color': city_color, 'width': 4}, 'thickness': 0.75, 'value': c['aqi']}
        }
    ))
    gauge_chart.update_layout(height=170, margin=dict(l=20, r=20, t=20, b=20), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    
    # ============= PAGE PRINCIPALE (SANS CHATBOT INTÉGRÉ) =============
    return html.Div([
        # Bloc ville avec bordure
        html.Div([
            html.Div([
                html.I(className="fas fa-location-dot", style={'color': city_color, 'fontSize': '22px', 'marginRight': '12px'}),
                html.Div([
                    html.H1(c['city'], style={'fontSize': '28px', 'fontWeight': '800', 'margin': '0', 'color': city_color}),
                    html.Div([
                        html.I(className=f"fas {quality_icon}", style={'marginRight': '6px', 'fontSize': '12px', 'color': city_color}),
                        html.Span(f"Votre ville a une qualité d'air {quality_msg}", style={'fontSize': '12px', 'color': 'var(--text-secondary)'})
                    ]),
                ])
            ], style={'display': 'flex', 'alignItems': 'center'}),
            html.Div([
                html.I(className=f"fas {trend_icon}", style={'marginRight': '6px'}),
                html.Span(trend_text, style={'fontWeight': '700'})
            ], style={
                'backgroundColor': f"{trend_color}20", 'color': trend_color,
                'padding': '6px 14px', 'borderRadius': '40px', 'fontSize': '13px', 'fontWeight': '700',
                'display': 'inline-flex', 'alignItems': 'center'
            })
        ], style={
            'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center',
            'marginBottom': '24px', 'padding': '20px', 'borderRadius': '20px',
            'background': f"{city_color}10", 'border': f'2px solid {city_color}60',
            'boxShadow': f'0 0 20px {glow_color}', 'flexWrap': 'wrap'
        }),
        
        # Ligne 1: Météo + Jauge AQI + Prévisions
        html.Div([
            # Météo du jour
            html.Div([
                html.Div([
                    html.I(className="fas fa-cloud-sun", style={'color': '#ff9100', 'marginRight': '10px'}),
                    html.Span(t('today_weather', lang), style={'fontSize': '11px', 'fontWeight': '700', 'color': 'var(--text-secondary)', 'letterSpacing': '0.1em'}),
                ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '16px'}),
                html.Div([
                    html.Div([
                        html.H2(f"{weather['temperature']}°C", style={'fontSize': '42px', 'fontWeight': '800', 'margin': '0'}),
                        html.Div([
                            html.I(className="fas fa-thermometer-half", style={'marginRight': '4px', 'fontSize': '10px'}),
                            html.Span(f"Min: {weather['temp_min']}°", style={'fontSize': '12px'}),
                            html.I(className="fas fa-thermometer-full", style={'marginLeft': '12px', 'marginRight': '4px', 'fontSize': '10px'}),
                            html.Span(f"Max: {weather['temp_max']}°", style={'fontSize': '12px'})
                        ], style={'color': 'var(--text-secondary)'})
                    ], style={'textAlign': 'center', 'padding': '16px', 'background': 'var(--bg-surface)', 'borderRadius': '20px', 'marginBottom': '16px'}),
                    html.Div([
                        html.Div([
                            html.I(className="fas fa-tint", style={'color': '#00d4ff', 'fontSize': '18px', 'marginBottom': '6px'}),
                            html.H4(f"{weather['humidity']}%", style={'margin': '0', 'fontSize': '18px', 'fontWeight': '700'}),
                            html.Span(t('humidity_label', lang), style={'fontSize': '10px', 'color': 'var(--text-secondary)'})
                        ], style={'textAlign': 'center', 'padding': '12px', 'background': 'var(--bg-surface)', 'borderRadius': '16px'}),
                        html.Div([
                            html.I(className="fas fa-wind", style={'color': '#00e676', 'fontSize': '18px', 'marginBottom': '6px'}),
                            html.H4(f"{weather['wind_speed']}", style={'margin': '0', 'fontSize': '18px', 'fontWeight': '700'}),
                            html.Span("km/h", style={'fontSize': '10px', 'color': 'var(--text-secondary)'})
                        ], style={'textAlign': 'center', 'padding': '12px', 'background': 'var(--bg-surface)', 'borderRadius': '16px'}),
                        html.Div([
                            html.I(className="fas fa-cloud-rain", style={'color': '#a855f7', 'fontSize': '18px', 'marginBottom': '6px'}),
                            html.H4(f"{weather['precipitation']}", style={'margin': '0', 'fontSize': '18px', 'fontWeight': '700'}),
                            html.Span("mm", style={'fontSize': '10px', 'color': 'var(--text-secondary)'})
                        ], style={'textAlign': 'center', 'padding': '12px', 'background': 'var(--bg-surface)', 'borderRadius': '16px'}),
                    ], style={'display': 'grid', 'gridTemplateColumns': 'repeat(3,1fr)', 'gap': '12px', 'marginBottom': '16px'}),
                    html.Div([
                        html.Div([
                            html.I(className="fas fa-sunrise", style={'marginRight': '8px', 'color': '#ff9100'}),
                            html.Span(f"{t('sunrise_label', lang)}: {weather['sunrise']}", style={'fontSize': '12px'})
                        ]),
                        html.Div([
                            html.I(className="fas fa-sunset", style={'marginRight': '8px', 'color': '#ff9100'}),
                            html.Span(f"{t('sunset_label', lang)}: {weather['sunset']}", style={'fontSize': '12px'})
                        ]),
                    ], style={'display': 'flex', 'gap': '24px', 'padding': '12px', 'background': 'var(--bg-surface)', 'borderRadius': '12px', 'justifyContent': 'center'}),
                    
                    # ── Commentaire météo + qualité air IA ──────────
                    html.Div([
                        html.Div([
                            html.I(className="fas fa-robot",
                                   style={'color': '#7c3aed', 'fontSize': '13px', 'marginRight': '8px'}),
                            html.Span(t('today_weather', lang),
                                      style={'fontSize': '11px', 'fontWeight': '700',
                                             'color': 'var(--text-secondary)',
                                             'textTransform': 'uppercase', 'letterSpacing': '0.08em'}),
                        ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '8px'}),
                        html.P(
                            _weather_ai_comment(c['city'], c['aqi'], c['pm25'],
                                                weather['temperature'], weather['humidity'],
                                                weather['wind_speed'], weather['precipitation'],
                                                lang) or _weather_comment(weather, lang),
                            style={'fontSize': '12px', 'color': 'var(--text-primary)',
                                   'lineHeight': '1.6', 'margin': '0'}
                        ),
                    ], style={
                        'marginTop': '14px', 'padding': '14px 16px', 'borderRadius': '14px',
                        'background': 'var(--bg-surface)', 'border': '1px solid rgba(124,58,237,0.3)',
                        'boxShadow': '0 0 12px rgba(124,58,237,0.08)',
                    }),
                ])
            ], className='card', style={'gridColumn': 'span 6'}),
            
            # Jauge AQI + Recommandations + Prévisions
            html.Div([
                html.Div([
                    html.I(className="fas fa-gauge-high", style={'color': '#ff9100', 'marginRight': '10px'}),
                    html.Span(t('today_quality', lang), style={'fontSize': '11px', 'fontWeight': '700', 'color': 'var(--text-secondary)', 'letterSpacing': '0.1em'})
                ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '16px'}),
                
                dcc.Graph(figure=gauge_chart, config={'displayModeBar': False}, style={'height': '170px'}),
                
                html.Div([
                    html.I(className=f"fas {rec_icon}", style={'color': city_color, 'marginRight': '8px', 'fontSize': '14px'}),
                    html.Span(recommendation, style={'fontSize': '12px', 'fontWeight': '500'})
                ], style={
                    'padding': '12px', 'background': f"{city_color}15", 'borderRadius': '12px',
                    'margin': '12px 0', 'borderLeft': f'3px solid {city_color}'
                }),
                
                html.Hr(style={'margin': '12px 0', 'borderColor': 'var(--border)'}),
                
                html.Div([
                    html.Div([
                        html.I(className=f"fas {dominant[4]}", style={'color': dominant[3], 'marginRight': '8px'}),
                        html.Span(t('dominant_pollutant', lang), style={'fontWeight': '600', 'fontSize': '12px'})
                    ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '8px'}),
                    html.Div([
                        html.Span(dominant[0], style={'fontWeight': '800', 'fontSize': '22px', 'color': dominant[3]}),
                        html.Span(f" {dominant[1]:.1f} µg/m³", style={'fontSize': '16px', 'fontWeight': '600'})
                    ]),
                    html.Div([
                        html.Div(style={'width': f"{min(100, (dominant[1]/dominant[2])*100)}%", 'height': '6px', 'background': dominant[3], 'borderRadius': '3px'})
                    ], style={'background': 'var(--border)', 'borderRadius': '3px', 'margin': '8px 0'}),
                ]),
                
                html.Div([
                    html.Div([
                        html.I(className="fas fa-calendar-week", style={'color': '#00d4ff', 'marginRight': '8px'}),
                        html.Span(t('today_forecast', lang), style={'fontSize': '10px', 'fontWeight': '700', 'color': 'var(--text-secondary)', 'letterSpacing': '0.08em'})
                    ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '12px', 'marginTop': '12px'}),
                    html.Div([
                        *[html.Div([
                            html.Span(day, style={'fontSize': '10px', 'fontWeight': '600', 'color': 'var(--text-secondary)'}),
                            html.H4(f"{val:.0f}", style={'margin': '4px 0', 'fontSize': '16px', 'fontWeight': '800', 'color': aqi_color(val)}),
                            html.I(className=f"fas {'fa-face-smile' if val <= 50 else 'fa-face-meh' if val <= 100 else 'fa-face-frown' if val <= 150 else 'fa-face-sad-tear'}", 
                                   style={'fontSize': '12px', 'color': aqi_color(val)})
                        ], style={'textAlign': 'center', 'padding': '8px 4px', 'background': f"{aqi_color(val)}10", 'borderRadius': '10px', 'flex': '1'}) 
                          for day, val in zip(forecast_days, forecast_values)]
                    ], style={'display': 'flex', 'gap': '4px'})
                ])
                
            ], className='card', style={'gridColumn': 'span 6'}),
            
        ], style={'display': 'grid', 'gridTemplateColumns': 'repeat(12,1fr)', 'gap': '16px', 'marginBottom': '16px'}),
        
        # Ligne 2: Graphique évolution + Comparaison polluants + Carte
        html.Div([
            html.Div([
                html.Div([
                    html.I(className="fas fa-chart-line", style={'color': '#00d4ff', 'marginRight': '10px'}),
                    html.Span(t('evolution_30d', lang), style={'fontSize': '11px', 'fontWeight': '700', 'color': 'var(--text-secondary)', 'letterSpacing': '0.1em'})
                ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '12px'}),
                dcc.Graph(figure=fig_evolution, config={'displayModeBar': False}, style={'height': '280px'})
            ], className='card', style={'gridColumn': 'span 5'}),
            
            html.Div([
                html.Div([
                    html.I(className="fas fa-chart-simple", style={'color': '#a855f7', 'marginRight': '10px'}),
                    html.Span(t('pollutant_comparison', lang), style={'fontSize': '11px', 'fontWeight': '700', 'color': 'var(--text-secondary)', 'letterSpacing': '0.1em'})
                ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '12px'}),
                dcc.Graph(figure=fig_pollutants, config={'displayModeBar': False}, style={'height': '280px'})
            ], className='card', style={'gridColumn': 'span 4'}),
            
            html.Div([
                html.Div([
                    html.I(className="fas fa-map-location-dot", style={'color': '#00d4ff', 'marginRight': '10px'}),
                    html.Span(t('location', lang), style={'fontSize': '11px', 'fontWeight': '700', 'color': 'var(--text-secondary)', 'letterSpacing': '0.1em'})
                ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '12px'}),
                city_map,
                html.P(
                    html.I(className="fas fa-info-circle", style={'marginRight': '6px'}),
                    t('click_marker', lang),
                    style={'fontSize': '10px', 'color': 'var(--text-muted)', 'marginTop': '10px', 'textAlign': 'center'}
                )
            ], className='card', style={'gridColumn': 'span 3'}),
            
        ], style={'display': 'grid', 'gridTemplateColumns': 'repeat(12,1fr)', 'gap': '16px'}),
        
    ], className='anim-fade-up')

def get_citizen_tab_content_page(city_name, lang='fr'):
    """Page Alertes - Alertes actives"""
    _cd = _get_cities_dyn()
    c = next((x for x in _cd if x['city'] == city_name), next((x for x in _cd if x['city'] == 'Yaoundé'), _cd[0]))
    
    alerts = []
    
    # Alerte principale si AQI élevé
    if c['aqi'] > 150:
        alerts.append({
            'level': 'CRITIQUE',
            'color': '#ff1744',
            'icon': 'fa-triangle-exclamation',
            'title': f'Qualité de l\'air critique - {city_name}',
            'desc': f'AQI {c["aqi"]} - {aqi_label(c["aqi"])}. Populations vulnérables : restez à l\'intérieur.'
        })
    
    # Alerte PM2.5
    if c['pm25'] > 35:
        alerts.append({
            'level': 'ÉLEVÉ',
            'color': '#ff9100',
            'icon': 'fa-smog',
            'title': 'PM2.5 à des niveaux élevés',
            'desc': f'Concentration de {c["pm25"]} µg/m³. Portez un masque FFP2 en extérieur.'
        })
    
    # Alerte NO2 pour Douala
    if city_name == 'Douala' and c['no2'] > 30:
        alerts.append({
            'level': 'MOYEN',
            'color': '#ff9100',
            'icon': 'fa-car',
            'title': 'Pic de pollution automobile',
            'desc': 'NO₂ en hausse aux heures de pointe (17h-19h). Évitez les grands axes.'
        })
    
    # Alerte par défaut si aucune
    if not alerts:
        alerts.append({
            'level': 'INFO',
            'color': '#00e676',
            'icon': 'fa-circle-info',
            'title': 'Aucune alerte active',
            'desc': f'La qualité de l\'air à {city_name} est actuellement {aqi_label(c["aqi"]).lower()}.'
        })

    return html.Div([
        html.H2(t('alerts_current', lang), style={'marginBottom': '16px'}),
        
        # Liste des alertes
        *[html.Div([
            html.Div([
                html.I(className=f"fas {alert['icon']}", style={'color': alert['color']}),
                html.Span(alert['level'], style={'marginLeft': '8px', 'color': alert['color'], 'fontWeight': '700'}),
            ], style={'marginBottom': '8px'}),
            html.H4(alert['title'], style={'marginBottom': '4px'}),
            html.P(alert['desc'], style={'color': 'var(--text-secondary)', 'margin': '0'}),
        ], style={'padding': '16px', 'background': f"{alert['color']}10", 'borderRadius': '12px', 'borderLeft': f"4px solid {alert['color']}", 'marginBottom': '12px'}) for alert in alerts],
        
        # Top villes polluées
        html.H4(f"🏭 {t('most_polluted_cities', lang)}", style={'marginTop': '24px', 'marginBottom': '12px'}),
        html.Div([
            *[html.Div([
                html.Span(f"{i+1}", style={'width': '30px', 'fontWeight': '700', 'color': 'var(--text-secondary)'}),
                html.Span(v['city'], style={'flex': '1'}),
                html.Span(str(v['aqi']), style={'fontWeight': '700', 'color': aqi_color(v['aqi'])}),
            ], style={'display': 'flex', 'alignItems': 'center', 'gap': '12px', 'padding': '10px 0', 'borderBottom': '1px solid var(--border)'}) 
              for i, v in enumerate(sorted(_get_cities_dyn(), key=lambda x: x['aqi'], reverse=True)[:5])]
        ]),
        
        # Seuil personnalisable
        html.H4(t('my_alerts', lang), style={'marginTop': '24px', 'marginBottom': '12px'}),
        html.Div([
            html.P(t('alert_notify_when', lang), style={'marginBottom': '12px'}),
            dcc.Slider(
                id='alert-threshold',
                min=50, max=200, step=50, value=100,
                marks={50: '50', 100: '100', 150: '150', 200: '200'},
                tooltip={'placement': 'bottom'}
            ),
            html.Div([
                html.I(className="fas fa-bell", style={'marginRight': '8px'}),
                html.Span(("You will be alerted when AQI > 100" if lang=='en' else "Vous serez alerté quand AQI > 100"), id='threshold-display')
            ], style={'marginTop': '12px', 'padding': '10px', 'background': 'var(--bg-surface)', 'borderRadius': '8px', 'textAlign': 'center'})
        ], className='card'),
        
    ])

def get_citizen_tab_content(tab_id, city, lang, theme='dark'):
    """Dispatch pour les onglets citoyen"""
    from app import make_overview_fallback
    from alerts_tab import create_alerts_page
    
    # Récupérer la ville de l'utilisateur
    user_city = city if city and city != 'all' else 'Yaoundé'
    
    if tab_id == 'today':
        # Vue globale - ne pas filtrer par ville
        return make_overview_fallback(None, lang, theme)
    elif tab_id == 'my_city':
        return create_my_city_page(user_city, lang, theme)
    elif tab_id == 'health':
        return create_health_page(user_city, lang, theme)
    elif tab_id == 'alerts':
        # ⚠️ CORRECTION : importer et appeler la bonne fonction
        from city_utils import get_regions
        return create_alerts_page(
            user_city, lang, theme,
            CITIES_DATA=_get_cities_dyn(),
            aqi_color=aqi_color,
            aqi_label=aqi_label,
            t=t,
            fa=fa,
            REGIONS=get_regions(_get_cities_dyn())
        )
    else:
        return html.Div("Page en construction...")

def create_health_page(city_name, lang='fr', theme='dark'):
    """Page Santé - Recommandations médicales avec design premium"""
    
    _cd = _get_cities_dyn()
    c = next((x for x in _cd if x['city'] == city_name), next((x for x in _cd if x['city'] == 'Yaoundé'), _cd[0]))
    en = (lang == 'en')

    # Bilingual severity labels
    _sev = {
        'Critique': 'Critical', 'Élevé': 'High', 'Modéré': 'Moderate', 'Faible': 'Low'
    } if en else {}
    def _s(fr): return _sev.get(fr, fr)

    # Bilingual pollutant risk texts
    def _pr(pm25_hi, pm25_mid, low_text):
        return pm25_hi if not en else {'Pénétration profonde dans les poumons, risque cardiovasculaire et respiratoire': 'Deep lung penetration, cardiovascular and respiratory risk', 'Irritation des voies respiratoires, exacerbation de l\'asthme': 'Airway irritation, asthma exacerbation', 'Inflammation des voies respiratoires, diminution de la fonction pulmonaire': 'Airway inflammation, reduced lung function', 'Irritation des yeux et du nez, toux, aggravation de l\'asthme': 'Eye and nose irritation, cough, worsened asthma', 'Irritation des voies respiratoires, bronchite chronique': 'Respiratory irritation, chronic bronchitis', 'Risque modéré pour personnes sensibles': 'Moderate risk for sensitive groups', 'Risque faible': 'Low risk'}.get(pm25_hi, pm25_hi)

    # Déterminer le niveau de risque et les recommandations
    if c['aqi'] <= 50:
        risk_level = "Low" if en else "Faible"
        risk_color = "#00e676"
        risk_bg = "rgba(0,230,118,0.15)"
        risk_icon = "fa-face-smile"
        risk_desc = "Excellent air quality. No particular risk." if en else "Qualité de l'air excellente. Aucun risque particulier."
        main_advice = "Enjoy outdoor activities freely. Open your windows to ventilate." if en else "Profitez pleinement des activités extérieures. Ouvrez vos fenêtres pour aérer."
        recommendations = [
            ("fa-person-walking", "Normal outdoor activities" if en else "Activités extérieures normales", "No restrictions" if en else "Aucune restriction"),
            ("fa-window-maximize", "Ventilation recommended" if en else "Aération recommandée", "All day" if en else "Toute la journée"),
            ("fa-mask-face", "Mask", "Not necessary" if en else "Non nécessaire"),
            ("fa-heart-pulse", "Sensitive groups" if en else "Populations sensibles", "No special precautions" if en else "Aucune précaution particulière")
        ]
        ai_comment = "✅ Excellent air quality! Pollutant concentrations are well below WHO limits. Enjoy outdoor sports and ventilate your home." if en else "✅ Excellente qualité de l'air ! Profitez de cette journée pour faire du sport en extérieur et aérer votre logement."

    elif c['aqi'] <= 100:
        risk_level = "Moderate" if en else "Modéré"
        risk_color = "#ffee58"
        risk_bg = "rgba(255,238,88,0.15)"
        risk_icon = "fa-face-meh"
        risk_desc = "Acceptable air quality. Moderate risk for sensitive groups." if en else "Qualité de l'air acceptable. Risque modéré pour les personnes sensibles."
        main_advice = "Sensitive groups: limit prolonged outdoor exertion." if en else "Personnes sensibles : limitez les efforts prolongés en extérieur."
        recommendations = [
            ("fa-person-walking", "Outdoor activities" if en else "Activités extérieures", "Normal for healthy people" if en else "Normales pour personnes en bonne santé"),
            ("fa-mask-face", "Mask advised" if en else "Masque conseillé", "For sensitive groups" if en else "Pour personnes sensibles"),
            ("fa-clock", "Times to avoid" if en else "Horaires à éviter", "12pm–4pm (pollution peak)" if en else "12h-16h (pic de pollution)"),
            ("fa-heart-pulse", "Monitoring" if en else "Surveillance", "Enhanced for asthmatics" if en else "Renforcée pour asthmatiques")
        ]
        ai_comment = "⚠️ Moderate air quality. Sensitive groups (children, elderly, asthmatics) may experience respiratory discomfort. Limit intense outdoor physical activity." if en else "⚠️ Qualité de l'air modérée. Les personnes sensibles peuvent ressentir des gênes respiratoires."

    elif c['aqi'] <= 150:
        risk_level = "High" if en else "Élevé"
        risk_color = "#ff9100"
        risk_bg = "rgba(255,145,0,0.15)"
        risk_icon = "fa-face-frown"
        risk_desc = "Degraded air quality. High risk for vulnerable populations." if en else "Qualité de l'air dégradée. Risque élevé pour les populations vulnérables."
        main_advice = "Avoid intense physical activity. Wear an FFP2 mask outdoors." if en else "Évitez les activités physiques intenses. Portez un masque FFP2 si vous devez sortir."
        recommendations = [
            ("fa-house-circle-exclamation", "Stay indoors" if en else "Rester à l'intérieur", "Priority for sensitive groups" if en else "Priorité pour personnes sensibles"),
            ("fa-mask-face", "FFP2 mask", "Recommended for all outings" if en else "Recommandé pour toute sortie"),
            ("fa-window-maximize", "Keep windows closed" if en else "Fenêtres fermées", "During peak hours" if en else "Aux heures de pointe"),
            ("fa-lungs", "Respiratory symptoms" if en else "Symptômes respiratoires", "Enhanced monitoring" if en else "Surveillance accrue")
        ]
        ai_comment = "😷 Degraded air quality. Sensitive groups should avoid prolonged outings. Wear an FFP2 mask outdoors. Asthmatics should keep their treatment within reach." if en else "😷 Qualité de l'air dégradée. Portez un masque FFP2 si vous devez vous déplacer."

    elif c['aqi'] <= 200:
        risk_level = "Very high" if en else "Très élevé"
        risk_color = "#ff1744"
        risk_bg = "rgba(255,23,68,0.15)"
        risk_icon = "fa-face-sad-tear"
        risk_desc = "Poor air quality. Risk for the entire population." if en else "Qualité de l'air mauvaise. Risque pour toute la population."
        main_advice = "Stay indoors. Close windows. Use an air purifier." if en else "Restez à l'intérieur. Fermez les fenêtres. Utilisez un purificateur d'air."
        recommendations = [
            ("fa-house-chimney", "Confinement", "Recommended for all" if en else "Recommandé pour tous"),
            ("fa-mask-face", "FFP2/FFP3 mask", "Mandatory outdoors" if en else "Obligatoire en extérieur"),
            ("fa-wind", "Air purifier" if en else "Purificateur d'air", "Advised indoors" if en else "Conseillé à l'intérieur"),
            ("fa-phone-alt", "Medical emergency" if en else "Urgence médicale", "SAMU 15 / MINSANTE 1510")
        ]
        ai_comment = "HEALTH ALERT! Poor air quality for the entire population. Stay indoors as much as possible. Vulnerable groups must avoid all outings. Contact a doctor if you experience respiratory distress." if en else "ALERTE SANITAIRE ! Restez à l'intérieur. Personnes vulnérables : évitez toute sortie."

    else:
        risk_level = "Critical" if en else "Critique"
        risk_color = "#d500f9"
        risk_bg = "rgba(213,0,249,0.15)"
        risk_icon = "fa-skull"
        risk_desc = "Dangerous air quality. Health emergency." if en else "Qualité de l'air dangereuse. Urgence sanitaire."
        main_advice = "EMERGENCY: Stay home. Avoid all outings. Call emergency services if symptomatic." if en else "URGENCE : Restez chez vous. Évitez toute sortie. Contactez le SAMU en cas de symptômes."
        recommendations = [
            ("fa-truck-medical", "HEALTH EMERGENCY" if en else "URGENCE SANITAIRE", "Call 15 immediately" if en else "Contactez immédiatement le 15"),
            ("fa-house-chimney", "FULL CONFINEMENT" if en else "CONFINEMENT TOTAL", "Do not go out under any circumstances" if en else "Ne sortez sous aucun prétexte"),
            ("fa-mask-face", "FFP3 mask", "Mandatory for vital outings" if en else "Obligatoire si sortie vitale"),
            ("fa-heart-broken", "Symptômes graves", "Consultez sans attendre")
        ]
        
        ai_comment = "ALERTE MAXIMALE ! La qualité de l'air est dangereuse pour toute la population. Des risques sanitaires graves sont possibles. Restez confiné, portez un masque FFP3 en cas de sortie absolument nécessaire. En cas de difficultés respiratoires, contactez le SAMU (15) ou le MINSANTE (1510) immédiatement."
    
    # Données des polluants avec leurs risques sanitaires
    pollutants_with_risks = [
        {
            "name": "PM2.5",
            "value": c['pm25'],
            "threshold": 25,
            "unit": "μg/m³",
            "color": "#ff1744",
            "icon": "fa-smog",
            "risk": ("Deep lung penetration, cardiovascular and respiratory risk" if c['pm25'] > 25 else "Moderate risk for sensitive groups" if c['pm25'] > 12 else "Low risk") if en else ("Pénétration profonde dans les poumons, risque cardiovasculaire et respiratoire" if c['pm25'] > 25 else "Risque modéré pour personnes sensibles" if c['pm25'] > 12 else "Risque faible"),
            "severity": _s("Critique" if c['pm25'] > 50 else "Élevé" if c['pm25'] > 35 else "Modéré" if c['pm25'] > 25 else "Faible")
        },
        {
            "name": "PM10",
            "value": c['pm10'],
            "threshold": 45,
            "unit": "μg/m³",
            "color": "#ff9100",
            "icon": "fa-dust",
            "risk": ("Airway irritation, asthma exacerbation" if c['pm10'] > 45 else "Moderate risk for sensitive groups" if c['pm10'] > 30 else "Low risk") if en else ("Irritation des voies respiratoires, exacerbation de l'asthme" if c['pm10'] > 45 else "Risque modéré pour personnes sensibles" if c['pm10'] > 30 else "Risque faible"),
            "severity": _s("Critique" if c['pm10'] > 90 else "Élevé" if c['pm10'] > 60 else "Modéré" if c['pm10'] > 45 else "Faible")
        },
        {
            "name": "NO₂",
            "value": c['no2'],
            "threshold": 40,
            "unit": "μg/m³",
            "color": "#00d4ff",
            "icon": "fa-industry",
            "risk": ("Airway inflammation, reduced lung function" if c['no2'] > 40 else "Moderate risk for sensitive groups" if c['no2'] > 25 else "Low risk") if en else ("Inflammation des voies respiratoires, diminution de la fonction pulmonaire" if c['no2'] > 40 else "Risque modéré pour personnes sensibles" if c['no2'] > 25 else "Risque faible"),
            "severity": _s("Critique" if c['no2'] > 80 else "Élevé" if c['no2'] > 50 else "Modéré" if c['no2'] > 40 else "Faible")
        },
        {
            "name": "O₃",
            "value": c['o3'],
            "threshold": 100,
            "unit": "μg/m³",
            "color": "#00e676",
            "icon": "fa-sun",
            "risk": ("Eye and nose irritation, cough, worsened asthma" if c['o3'] > 100 else "Moderate risk for sensitive groups" if c['o3'] > 70 else "Low risk") if en else ("Irritation des yeux et du nez, toux, aggravation de l'asthme" if c['o3'] > 100 else "Risque modéré pour personnes sensibles" if c['o3'] > 70 else "Risque faible"),
            "severity": _s("Critique" if c['o3'] > 150 else "Élevé" if c['o3'] > 120 else "Modéré" if c['o3'] > 100 else "Faible")
        },
        {
            "name": "SO₂",
            "value": c['so2'],
            "threshold": 20,
            "unit": "μg/m³",
            "color": "#a855f7",
            "icon": "fa-flask",
            "risk": ("Respiratory irritation, chronic bronchitis" if c['so2'] > 20 else "Moderate risk for sensitive groups" if c['so2'] > 10 else "Low risk") if en else ("Irritation des voies respiratoires, bronchite chronique" if c['so2'] > 20 else "Risque modéré pour personnes sensibles" if c['so2'] > 10 else "Risque faible"),
            "severity": _s("Critique" if c['so2'] > 40 else "Élevé" if c['so2'] > 30 else "Modéré" if c['so2'] > 20 else "Faible")
        },
    ]
    
    # Commentaire IA santé global (override le texte statique)
    try:
        from ai_commentary import ai_health_gauge as _ai_hg, ai_pollutant_risks as _ai_pr
        _dom = max(pollutants_with_risks, key=lambda p: p['value'] / max(p['threshold'], 1))
        _ai = _ai_hg(city_name, c['aqi'], c['pm25'], c['pm10'], c['no2'], _dom['name'], lang=lang)
        if _ai:
            ai_comment = _ai
        # Risques IA par polluant
        _risks_ai = _ai_pr(city_name, [
            (p['name'], p['value'], p['threshold'], p['unit']) for p in pollutants_with_risks
        ], lang=lang)
        for p in pollutants_with_risks:
            if p['name'] in _risks_ai:
                p['risk'] = _risks_ai[p['name']]
    except Exception:
        pass

    # Contacts urgence
    emergency_contacts = [
        ("fa-phone-alt", "SAMU", "1519", "Medical emergencies 24/7" if en else "Urgences médicales 24/7", "#ff1744"),
        ("fa-hospital", "MINSANTE", "1510", "Ministry of Health" if en else "Ministère de la Santé", "#ff9100"),
        ("fa-ambulance", "Red Cross" if en else "Croix-Rouge", "(+237) 222 22 41 77", "Humanitarian assistance" if en else "Assistance humanitaire", "#00d4ff"),
        ("fa-leaf", "MINEPDED", "(+237) 222 22 94 92", "Report pollution" if en else "Signalement pollution", "#00e676"),
    ]
    
    # Couleur de la carte d'en-tête selon l'AQI
    header_color = risk_color
    header_bg = f"{risk_color}08"
    
    return html.Div([
        # Bloc en-tête coloré avec radius
        html.Div([
            html.Div([
                html.I(className="fas fa-heart-pulse", style={'color': header_color, 'fontSize': '28px', 'marginRight': '14px'}),
                html.Div([
                    html.H1(t('health_reco_title', lang), style={'fontSize': '24px', 'fontWeight': '800', 'margin': '0', 'color': 'var(--text-primary)'}),
                    html.P(t('health_reco_sub', lang), style={'fontSize': '12px', 'color': 'var(--text-secondary)', 'margin': '4px 0 0 0'})
                ])
            ], style={'display': 'flex', 'alignItems': 'center'})
        ], style={
            'padding': '20px', 'borderRadius': '20px', 'marginBottom': '24px',
            'background': header_bg, 'border': f'2px solid {header_color}60',
            'boxShadow': f'0 0 20px {header_color}20'
        }),
        
        # Niveau de risque (carte principale)
        html.Div([
            html.Div([
                html.I(className=f"fas {risk_icon}", style={'fontSize': '48px', 'color': risk_color, 'marginBottom': '12px'}),
                html.H2(f"{'Risk level' if lang=='en' else 'Niveau de risque'} : {risk_level}", style={'fontSize': '28px', 'fontWeight': '800', 'color': risk_color, 'margin': '0 0 8px 0'}),
                html.P(risk_desc, style={'fontSize': '14px', 'color': 'var(--text-secondary)', 'margin': '0 0 16px 0'}),
                html.Div([
                    html.I(className="fas fa-circle-info", style={'marginRight': '8px', 'color': risk_color}),
                    html.Span(main_advice, style={'fontWeight': '500'})
                ], style={'padding': '12px', 'background': risk_bg, 'borderRadius': '12px', 'borderLeft': f'3px solid {risk_color}'})
            ], style={'textAlign': 'center', 'padding': '24px'})
        ], className='card', style={'marginBottom': '24px', 'border': f'2px solid {risk_color}40', 'boxShadow': f'0 0 20px {risk_color}20'}),
        
        # Grille des recommandations (4 colonnes)
        html.Div([
            html.Div([
                html.I(className=f"fas {rec[0]}", style={'fontSize': '28px', 'color': risk_color, 'marginBottom': '12px'}),
                html.H4(rec[1], style={'fontSize': '16px', 'fontWeight': '700', 'margin': '0 0 8px 0', 'color': 'var(--text-primary)'}),
                html.P(rec[2], style={'fontSize': '12px', 'color': 'var(--text-secondary)', 'margin': '0'})
            ], style={'textAlign': 'center', 'padding': '20px', 'background': f"{risk_color}08", 'borderRadius': '16px', 'border': f'1px solid {risk_color}30'})
            for rec in recommendations
        ], style={'display': 'grid', 'gridTemplateColumns': 'repeat(4, 1fr)', 'gap': '16px', 'marginBottom': '24px'}),
        
        # Commentaire IA
        html.Div([
            html.Div([
                html.I(className="fas fa-robot", style={'color': '#7c3aed', 'fontSize': '20px', 'marginRight': '12px'}),
                html.Span(t('ai_analysis', lang), style={'fontWeight': '700', 'fontSize': '14px', 'color': 'var(--text-primary)'})
            ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '12px'}),
            html.P(ai_comment, style={'fontSize': '13px', 'color': 'var(--text-secondary)', 'lineHeight': '1.6', 'margin': '0'}),
            html.Div([
                html.I(className="fas fa-chart-line", style={'marginRight': '6px', 'fontSize': '11px'}),
                html.Span(t('data_realtime', lang), style={'fontSize': '11px', 'color': 'var(--text-muted)'})
            ], style={'marginTop': '12px', 'display': 'flex', 'alignItems': 'center'})
        ], className='card', style={'marginBottom': '24px', 'background': 'rgba(124,58,237,0.05)', 'borderLeft': '3px solid #7c3aed', 'border': '1px solid rgba(124,58,237,0.25)'}),
        
        # DEUX BLOCS CÔTE À CÔTE (gauche étroit 35% / droit large 65%)
        html.Div([
            # Bloc GAUCHE - Comparaison OMS (plus étroit)
            html.Div([
                html.Div([
                    html.I(className="fas fa-scale-balanced", style={'color': '#ff9100', 'marginRight': '10px'}),
                    html.Span(t('oms_thresholds', lang), style={'fontWeight': '700', 'fontSize': '14px'})
                ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '16px'}),
                html.Div([
                    *[_oms_bar_row(p, lang) for p in pollutants_with_risks]
                ])
            ], style={
                'background': 'var(--bg-card)', 'borderRadius': '16px', 'padding': '16px',
                'border': f'1px solid var(--border)', 'width': '32%', 'display': 'inline-block',
                'verticalAlign': 'top'
            }),
            
            # Bloc DROIT - Risques sanitaires (plus large)
            html.Div([
                html.Div([
                    html.I(className="fas fa-brain", style={'color': '#a855f7', 'marginRight': '10px'}),
                    html.Span(t('health_risks', lang), style={'fontWeight': '700', 'fontSize': '14px'})
                ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '16px'}),
                html.Div([
                    *[html.Div([
                        html.Div([
                            html.I(className=f"fas {p['icon']}", style={'color': p['color'], 'marginRight': '10px', 'fontSize': '14px'}),
                            html.Span(p['name'], style={'fontWeight': '700', 'fontSize': '13px', 'marginRight': '10px'}),
                            html.Span(p['severity'], style={
                                'fontSize': '9px', 'fontWeight': '700',
                                'backgroundColor': f"{p['color']}20", 'color': p['color'],
                                'padding': '2px 8px', 'borderRadius': '20px'
                            })
                        ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '6px'}),
                        html.P(p['risk'], style={'fontSize': '11px', 'color': 'var(--text-secondary)', 'margin': '0 0 8px 0', 'lineHeight': '1.4'}),
                        html.Div(style={'height': '1px', 'background': 'var(--border)', 'margin': '8px 0'}) if idx < len(pollutants_with_risks) - 1 else None
                    ]) for idx, p in enumerate(pollutants_with_risks)]
                ])
            ], style={
                'background': 'var(--bg-card)', 'borderRadius': '16px', 'padding': '16px',
                'border': f'1px solid var(--border)', 'width': '66%', 'display': 'inline-block',
                'verticalAlign': 'top', 'marginLeft': '2%'
            })
            
        ], style={'display': 'flex', 'marginBottom': '24px', 'justifyContent': 'space-between'}),
        
        # Populations vulnérables
        html.Div([
            html.Div([
                html.I(className="fas fa-users", style={'color': '#a855f7', 'marginRight': '10px'}),
                html.Span(t('vulnerable_pop', lang), style={'fontWeight': '700', 'fontSize': '14px'})
            ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '16px'}),
            html.Div([
                html.Div([
                    html.I(className="fas fa-baby", style={'color': '#ff9100', 'fontSize': '24px', 'marginBottom': '8px'}),
                    html.H4("Children" if en else "Enfants", style={'fontSize': '14px', 'fontWeight': '700', 'margin': '0 0 4px 0'}),
                    html.P("More sensitive to pollution. Limit outdoor play." if en else "Plus sensibles à la pollution. Limitez les jeux extérieurs.", style={'fontSize': '11px', 'color': 'var(--text-secondary)', 'margin': '0'})
                ], style={'textAlign': 'center', 'padding': '16px', 'background': 'var(--bg-surface)', 'borderRadius': '16px'}),
                html.Div([
                    html.I(className="fas fa-person-cane", style={'color': '#ff9100', 'fontSize': '24px', 'marginBottom': '8px'}),
                    html.H4("Elderly" if en else "Personnes âgées", style={'fontSize': '14px', 'fontWeight': '700', 'margin': '0 0 4px 0'}),
                    html.P("Increased cardiovascular risk. Stay indoors." if en else "Risque cardiovasculaire accru. Restez en intérieur.", style={'fontSize': '11px', 'color': 'var(--text-secondary)', 'margin': '0'})
                ], style={'textAlign': 'center', 'padding': '16px', 'background': 'var(--bg-surface)', 'borderRadius': '16px'}),
                html.Div([
                    html.I(className="fas fa-lungs", style={'color': '#ff9100', 'fontSize': '24px', 'marginBottom': '8px'}),
                    html.H4("Asthmatics" if en else "Asthmatiques", style={'fontSize': '14px', 'fontWeight': '700', 'margin': '0 0 4px 0'}),
                    html.P("Keep your medication within reach. Avoid exertion." if en else "Ayez votre traitement à portée de main. Évitez l'effort.", style={'fontSize': '11px', 'color': 'var(--text-secondary)', 'margin': '0'})
                ], style={'textAlign': 'center', 'padding': '16px', 'background': 'var(--bg-surface)', 'borderRadius': '16px'}),
                html.Div([
                    html.I(className="fas fa-person-pregnant", style={'color': '#ff9100', 'fontSize': '24px', 'marginBottom': '8px'}),
                    html.H4("Pregnant women" if en else "Femmes enceintes", style={'fontSize': '14px', 'fontWeight': '700', 'margin': '0 0 4px 0'}),
                    html.P("Avoid heavy traffic areas. Night ventilation." if en else "Évitez les zones de fort trafic. Ventilation nocturne.", style={'fontSize': '11px', 'color': 'var(--text-secondary)', 'margin': '0'})
                ], style={'textAlign': 'center', 'padding': '16px', 'background': 'var(--bg-surface)', 'borderRadius': '16px'}),
            ], style={'display': 'grid', 'gridTemplateColumns': 'repeat(4, 1fr)', 'gap': '16px'})
        ], className='card', style={'marginBottom': '24px'}),
        
        # Contacts d'urgence
        html.Div([
            html.Div([
                html.I(className="fas fa-phone-alt", style={'color': '#ff1744', 'marginRight': '10px'}),
                html.Span(t('emergency_contacts', lang), style={'fontWeight': '700', 'fontSize': '14px'})
            ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '16px'}),
            html.Div([
                *[html.Div([
                    html.I(className=f"fas {contact[0]}", style={'color': contact[4], 'fontSize': '24px', 'marginBottom': '8px'}),
                    html.H4(contact[1], style={'fontSize': '14px', 'fontWeight': '700', 'margin': '0 0 4px 0'}),
                    html.H3(contact[2], style={'fontSize': '20px', 'fontWeight': '800', 'color': contact[4], 'margin': '0 0 4px 0'}),
                    html.P(contact[3], style={'fontSize': '10px', 'color': 'var(--text-secondary)', 'margin': '0'})
                ], style={'textAlign': 'center', 'padding': '16px', 'background': f"{contact[4]}08", 'borderRadius': '16px', 'border': f'1px solid {contact[4]}30'}) 
                  for contact in emergency_contacts]
            ], style={'display': 'grid', 'gridTemplateColumns': 'repeat(4, 1fr)', 'gap': '16px'})
        ], className='card'),
        
        # Footer informatif
        html.Div([
            html.I(className="fas fa-database", style={'marginRight': '8px', 'color': 'var(--text-muted)'}),
            html.Span("WHO 2021 data • AQI-based recommendations • Real-time updates" if en else "Données OMS 2021 • Recommandations adaptées selon l'AQI • Mise à jour en temps réel",
                      style={'fontSize': '10px', 'color': 'var(--text-muted)'})
        ], style={'marginTop': '24px', 'textAlign': 'center', 'padding': '12px'})
        
    ], className='anim-fade-up')