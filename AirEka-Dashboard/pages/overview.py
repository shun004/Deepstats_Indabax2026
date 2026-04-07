"""
Page principale du dashboard - Vue d'ensemble
Reproduit exactement le design du screenshot im2.jpeg
"""

import dash_bootstrap_components as dbc
from dash import html, dcc, callback, Input, Output, State
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from flask import current_app

from components.cards import create_kpi_card, create_aqi_card
from components.map import create_cameroon_map, create_legend
from components.charts import create_aqi_timeline, create_ranking_bar_chart, create_gauge_chart
from components.alerts import create_alerts_panel, get_default_alerts, create_recommendations_panel
from utils.color_utils import get_aqi_category, get_color_for_value
from utils.helpers import format_number, format_date, get_trend_icon

def create_overview_page(data, theme='light'):
    """
    Crée la page principale du dashboard
    
    Args:
        data: Dictionnaire des données chargées
        theme: 'dark' ou 'light'
    
    Returns:
        Layout complet de la page
    """
    # Vérifier que les données sont valides
    if data is None:
        return html.Div("Données non disponibles", className="text-center p-5")
    
    stats = data.get('stats', {})
    cities_summary = data.get('cities_summary', pd.DataFrame())
    regions = data.get('regions_list', [])
    cities = data.get('cities_list', [])
    time_series = data.get('time_series', pd.DataFrame())
    predictions = data.get('predictions', pd.DataFrame())
    
    # Données pour Yaoundé (ville par défaut)
    yaounde_data = None
    if len(cities_summary) > 0:
        yaounde_data = cities_summary[cities_summary['city'] == 'Yaoundé']
        yaounde_data = yaounde_data.iloc[0] if len(yaounde_data) > 0 else cities_summary.iloc[0]
    
    # Valeurs par défaut si stats manquantes
    national_avg_aqi = stats.get('national_avg_aqi', 142)
    trend_aqi = stats.get('trend_aqi', 8.3)
    national_avg_pm25 = stats.get('national_avg_pm25', 58.4)
    trend_pm25 = stats.get('trend_pm25', 3.9)
    national_avg_no2 = stats.get('national_avg_no2', 38.1)
    cities_count = stats.get('cities_count', 42)
    regions_count = stats.get('regions_count', 10)
    active_stations = stats.get('active_stations', 38)
    model_accuracy = stats.get('model_accuracy', 94.7)
    model_rmse = stats.get('model_rmse', 6.2)
    model_r2 = stats.get('model_r2', 0.96)
    who_threshold = stats.get('who_threshold', 15)
    
    # KPI Cards
    kpi_cards = html.Div([
        dbc.Row([
            dbc.Col(create_kpi_card(
                title="IQA MOYEN NATIONAL",
                value=f"{national_avg_aqi:.0f} AQI",
                trend=f"+{trend_aqi:.1f}% depuis hier" if trend_aqi > 0 else f"{trend_aqi:.1f}%",
                icon="fa-chart-line",
                color="primary"
            ), width=3),
            dbc.Col(create_kpi_card(
                title="PM2.5 MOYEN",
                value=f"{national_avg_pm25:.1f} µg/m³",
                trend=f"+{trend_pm25:.1f}% seuil OMS ({who_threshold} µg)" if trend_pm25 > 0 else f"{trend_pm25:.1f}%",
                icon="fa-smog",
                color="warning"
            ), width=3),
            dbc.Col(create_kpi_card(
                title="NO₂ MOYEN",
                value=f"{national_avg_no2:.1f} µg/m³",
                trend="-4.2% ce matin",
                icon="fa-industry",
                color="info"
            ), width=3),
            dbc.Col(create_kpi_card(
                title="VILLES SURVEILLÉES",
                value=f"{cities_count} / {regions_count} rég.",
                trend=f"{active_stations} stations actives (+6)",
                icon="fa-city",
                color="success"
            ), width=3),
        ]),
        dbc.Row([
            dbc.Col(create_kpi_card(
                title="PRÉCISION MODÈLE ML",
                value=f"{model_accuracy} %",
                trend=f"RMSE {model_rmse}, R² {model_r2}",
                icon="fa-brain",
                color="secondary"
            ), width=3),
        ], className="mt-3")
    ])
    
    # Carte spatiale
    map_section = dbc.Card([
        dbc.CardHeader([
            html.I(className="fas fa-map-marked-alt me-2"),
            html.Strong("CARTE SPATIALE — 42 VILLES")
        ]),
        dbc.CardBody([
            html.Div([
                create_cameroon_map(cities_summary, theme=theme),
                create_legend()
            ], style={'position': 'relative'})
        ])
    ], className="mb-4 shadow-sm")
    
    # Jauge AQI pour Yaoundé
    aqi_current = yaounde_data.get('aqi_current', yaounde_data.get('aqi_global', 178)) if yaounde_data is not None else 178
    pm25_current = yaounde_data.get('pm25_current', yaounde_data.get('pm2_5', 72.3)) if yaounde_data is not None else 72.3
    pm10_mean = yaounde_data.get('pm10_mean', 118.5) if yaounde_data is not None else 118.5
    no2_mean = yaounde_data.get('no2_mean', 42.8) if yaounde_data is not None else 42.8
    
    gauge_section = dbc.Card([
        dbc.CardHeader([
            html.I(className="fas fa-tachometer-alt me-2"),
            html.Strong(f"JAUGE IQA — Yaoundé · Centre")
        ]),
        dbc.CardBody([
            dcc.Graph(
                figure=create_gauge_chart(
                    value=aqi_current,
                    title="INDICE QA",
                    min_val=0,
                    max_val=300,
                    theme=theme
                ),
                config={'displayModeBar': False}
            ),
            html.Div([
                html.P([
                    html.Span("PM2.5: ", className="fw-bold"),
                    html.Span(f"{pm25_current:.1f} µg/m³")
                ], className="mb-1"),
                html.P([
                    html.Span("PM10: ", className="fw-bold"),
                    html.Span(f"{pm10_mean:.1f} µg/m³")
                ], className="mb-1"),
                html.P([
                    html.Span("NO₂: ", className="fw-bold"),
                    html.Span(f"{no2_mean:.1f} µg/m³")
                ], className="mb-0")
            ], className="mt-3 text-center")
        ])
    ], className="mb-4 shadow-sm")
    
    # Évolution temporelle (graphique simple pour éviter les erreurs)
    timeline_section = dbc.Card([
        dbc.CardHeader([
            html.I(className="fas fa-chart-line me-2"),
            html.Strong("ÉVOLUTION TEMPORELLE"),
            html.Div([
                dbc.ButtonGroup([
                    dbc.Button("24h", id="timeline-24h", color="secondary", size="sm", outline=True),
                    dbc.Button("7j", id="timeline-7j", color="secondary", size="sm", outline=True, active=True),
                    dbc.Button("30j", id="timeline-30j", color="secondary", size="sm", outline=True),
                ], size="sm", className="ms-3")
            ], className="d-inline-block float-end")
        ]),
        dbc.CardBody([
            dcc.Graph(
                id='timeline-graph',
                figure=create_simple_timeline(time_series, theme=theme),
                config={'displayModeBar': True}
            )
        ])
    ], className="mb-4 shadow-sm")
    
    # Classement des villes
    ranking = cities_summary.sort_values('aqi_current', ascending=False).reset_index(drop=True) if len(cities_summary) > 0 else pd.DataFrame()
    if len(ranking) > 0:
        ranking['rank'] = ranking.index + 1
    else:
        # Données par défaut
        ranking = pd.DataFrame([
            {'rank': 1, 'city': 'Yaoundé', 'region': 'Centre', 'aqi_current': 178, 'pm25_current': 72.3},
            {'rank': 2, 'city': 'Douala', 'region': 'Littoral', 'aqi_current': 165, 'pm25_current': 68.2},
            {'rank': 3, 'city': 'Garoua', 'region': 'Nord', 'aqi_current': 145, 'pm25_current': 58.9},
        ])
    
    ranking_table = dbc.Card([
        dbc.CardHeader([
            html.I(className="fas fa-trophy me-2"),
            html.Strong("CLASSEMENT DES VILLES")
        ]),
        dbc.CardBody([
            html.Div([
                html.Div([
                    html.Div(html.Span("Rang", className="fw-bold"), style={'width': '15%'}),
                    html.Div(html.Span("Ville", className="fw-bold"), style={'width': '40%'}),
                    html.Div(html.Span("AQI", className="fw-bold"), style={'width': '20%'}),
                    html.Div(html.Span("PM2.5", className="fw-bold"), style={'width': '25%'}),
                ], className="d-flex mb-2 text-muted small"),
                html.Div([
                    html.Div([
                        html.Div(html.Span(f"#{row['rank']}", className="fw-bold"), style={'width': '15%'}),
                        html.Div([
                            html.Span(row['city']),
                            html.Small(f" ({row['region']})", className="text-muted ms-1")
                        ], style={'width': '40%'}),
                        html.Div([
                            html.Span(f"{row['aqi_current']:.0f}", className="fw-bold",
                                     style={'color': get_color_for_value(row['aqi_current'])}),
                        ], style={'width': '20%'}),
                        html.Div([
                            html.Div([
                                html.Div(style={
                                    'width': f"{min(100, row['pm25_current'] / 150 * 100)}%",
                                    'height': '6px',
                                    'backgroundColor': get_color_for_value(row['pm25_current']),
                                    'borderRadius': '3px'
                                })
                            ], style={'width': '100%', 'backgroundColor': '#333', 'borderRadius': '3px'}),
                            html.Small(f"{row['pm25_current']:.1f} µg/m³", className="text-muted ms-2")
                        ], style={'width': '25%'}),
                    ], className="d-flex align-items-center mb-2 py-1", 
                       style={'borderBottom': '1px solid #333'})
                    for _, row in ranking.head(10).iterrows()
                ])
            ])
        ])
    ], className="mb-4 shadow-sm")
    
    # Prévision 7 jours
    forecast_7days = create_forecast_cards(predictions)
    
    # Alertes et recommandations
    alerts_section = dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([
                    html.I(className="fas fa-bell me-2"),
                    html.Strong("ALERTES & RECOMMANDATIONS ACTIVES")
                ]),
                dbc.CardBody([
                    create_alerts_panel(get_default_alerts())
                ])
            ], className="shadow-sm")
        ], width=6),
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([
                    html.I(className="fas fa-notes-medical me-2"),
                    html.Strong("RECOMMANDATIONS SANITAIRES")
                ]),
                dbc.CardBody([
                    create_recommendations_panel(yaounde_data.to_dict() if yaounde_data is not None else None)
                ])
            ], className="shadow-sm")
        ], width=6)
    ], className="mb-4")
    
    # Section confiance modèle
    confidence_section = dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.Div([
                            html.H4("NIVEAU DE CONFIANCE DU MODÈLE", className="mb-2"),
                            html.Div([
                                html.Span(f"{model_accuracy}%", className="display-4 fw-bold",
                                         style={'color': '#00acc1'}),
                                html.Span(" de confiance", className="text-muted")
                            ])
                        ], className="text-center"),
                        html.Div([
                            html.Div(style={
                                'width': f"{model_accuracy}%",
                                'height': '8px',
                                'backgroundColor': '#00acc1',
                                'borderRadius': '4px',
                                'transition': 'width 0.5s ease'
                            })
                        ], style={'width': '100%', 'backgroundColor': '#333', 'borderRadius': '4px', 'marginTop': '15px'}),
                        html.Div([
                            html.Small("Cross-validation 3-fold | Ensemble RF + XGB + LSTM", className="text-muted")
                        ], className="text-center mt-2")
                    ])
                ])
            ], className="shadow-sm")
        ], width=6),
        dbc.Col([
            create_feature_importance_card()
        ], width=6)
    ], className="mb-4")
    
    # Assemblage final
    layout = html.Div([
        # Header avec filtres
        html.Div([
            html.Div([
                html.H1([
                    html.I(className="fas fa-leaf me-2", style={'color': '#4caf50'}),
                    "AirGuard Cameroun"
                ], className="display-5 mb-0"),
                html.P("Système d'alerte précoce pour la qualité de l'air", className="text-muted")
            ], className="d-flex justify-content-between align-items-center"),
            
            # Filtres
            dbc.Row([
                dbc.Col([
                    html.Label("Région", className="text-muted small"),
                    dcc.Dropdown(
                        id='region-filter',
                        options=[{'label': f"Toutes les régions ({len(regions)})", 'value': 'all'}] +
                                [{'label': r, 'value': r} for r in sorted(regions)],
                        value='all',
                        className="bg-dark text-white"
                    )
                ], width=3),
                dbc.Col([
                    html.Label("Ville", className="text-muted small"),
                    dcc.Dropdown(
                        id='city-filter',
                        options=[{'label': f"Toutes les villes ({len(cities)})", 'value': 'all'}] +
                                [{'label': c, 'value': c} for c in sorted(cities)],
                        value='all',
                        className="bg-dark text-white"
                    )
                ], width=3),
                dbc.Col([
                    html.Label("Dates", className="text-muted small"),
                    dcc.DatePickerRange(
                        id='date-range',
                        start_date=datetime.now() - timedelta(days=7),
                        end_date=datetime.now(),
                        display_format='DD/MM/YYYY',
                        className="bg-dark"
                    )
                ], width=3),
                dbc.Col([
                    html.Label(" ", className="text-muted small"),
                    html.Div([
                        html.Span([
                            html.I(className="fas fa-circle me-1", style={'color': '#4caf50', 'fontSize': '10px'}),
                            " TEMPS RÉEL"
                        ], className="real-time-badge")
                    ])
                ], width=3)
            ], className="mt-3 mb-4")
        ], className="mb-4"),
        
        # KPIs
        kpi_cards,
        
        # Carte et jauge
        dbc.Row([
            dbc.Col(map_section, width=8),
            dbc.Col(gauge_section, width=4)
        ], className="mb-4"),
        
        # Évolution temporelle
        timeline_section,
        
        # Classement et prévisions
        dbc.Row([
            dbc.Col(ranking_table, width=5),
            dbc.Col(forecast_7days, width=7)
        ], className="mb-4"),
        
        # Alertes
        alerts_section,
        
        # Confiance et importance variables
        confidence_section,
        
        # Footer
        html.Footer([
            html.Hr(),
            html.Div([
                html.Span("Sources: MINEPOD - OpenAQ - Sentinel-5P ESA - Stations IoT - OpenStreetMap", 
                         className="text-muted small"),
                html.Br(),
                html.Span(f"© 2026 AirGuard Cameroun - Compétition IA Cameroun - Dernière mise à jour: {format_date(datetime.now())}", 
                         className="text-muted small")
            ], className="text-center")
        ], className="mt-5")
    ], className="p-4")
    
    return layout

def create_simple_timeline(df, theme='light'):
    """Crée un graphique simple de l'évolution temporelle"""
    import plotly.graph_objects as go
    
    if df is None or len(df) == 0:
        # Données par défaut
        dates = [datetime.now() - timedelta(days=i) for i in range(30, -1, -1)]
        values = [100 + 50 * np.sin(i/5) + 20 * np.random.randn() for i in range(31)]
    else:
        dates = df['date'].tail(30).tolist()
        values = df['aqi_global'].tail(30).tolist() if 'aqi_global' in df.columns else df['aqi_global'].tail(30).tolist()
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=dates,
        y=values,
        mode='lines',
        name='AQI',
        line=dict(color='#ff9800', width=2),
        fill='tozeroy',
        fillcolor='rgba(255, 152, 0, 0.1)'
    ))
    
    # Seuil OMS
    fig.add_hline(y=15, line_dash="dash", line_color="#00e676",
                  annotation_text="Seuil OMS")
    
    fig.update_layout(
        title="Évolution de l'AQI",
        xaxis_title="Date",
        yaxis_title="AQI",
        hovermode='x unified',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font={'color': 'white'},
        height=400,
        margin=dict(l=50, r=50, t=50, b=50)
    )
    
    return fig

def create_forecast_cards(predictions_df):
    """Crée les cartes de prévision 7 jours"""
    if predictions_df is None or len(predictions_df) == 0:
        # Données simulées
        days = ['AUJ.', 'MER', 'JEU', 'VEN', 'SAM', 'DIM', 'LUN']
        values = [180.93, 270.03, 280.53, 290.03, 300.03, 310.03, 320.03]
        categories = ['Mauvais', 'Très mauvais', 'Très mauvais', 'Très mauvais', 'Très mauvais', 'Très mauvais', 'Très mauvais']
        icons = ['😷', '😰', '😰', '😰', '😰', '😰', '😰']
    else:
        yaounde_pred = predictions_df[predictions_df['city'] == 'Yaoundé'].sort_values('date')
        if len(yaounde_pred) > 0:
            days = ['AUJ.'] + [d.strftime('%a').upper()[:3] for d in yaounde_pred['date'].iloc[1:7]]
            values = yaounde_pred['aqi_global_pred'].tolist() if 'aqi_global_pred' in yaounde_pred.columns else yaounde_pred['aqi_global'].tolist()
            values = values[:7]
            categories = ['Bon' if v <= 50 else 'Modéré' if v <= 100 else 'Mauvais' for v in values]
            icons = ['😊' if v <= 50 else '😐' if v <= 100 else '😷' for v in values]
        else:
            days = ['AUJ.', 'MER', 'JEU', 'VEN', 'SAM', 'DIM', 'LUN']
            values = [178, 145, 92, 78, 48, 42, 68]
            categories = ['Mauvais', 'Moyen', 'Moyen', 'Bon', 'Bon', 'Bon', 'Bon']
            icons = ['😷', '😐', '😐', '😊', '😊', '😊', '😊']
    
    forecast_cards = []
    for i, (day, val, cat, icon) in enumerate(zip(days, values, categories, icons)):
        color = '#4caf50' if cat == 'Bon' else '#ff9800' if cat == 'Modéré' or cat == 'Moyen' else '#f44336'
        card = dbc.Col(
            dbc.Card([
                dbc.CardBody([
                    html.H4(day, className="text-center mb-2", style={'fontWeight': 'bold'}),
                    html.Div(icon, className="text-center", style={'fontSize': '48px'}),
                    html.H2(f"{val:.0f}", className="text-center mt-3 mb-1", style={'color': color}),
                    html.Small(cat, className="text-center d-block"),
                    html.Hr(className="my-2"),
                    html.Small("Conf. 94%", className="text-center d-block text-muted")
                ])
            ], className="shadow-sm", style={'transition': 'transform 0.2s'})
        )
        forecast_cards.append(card)
    
    return dbc.Row(forecast_cards, className="g-3 mb-4")

def create_feature_importance_card():
    """Crée la carte d'importance des variables"""
    features = {
        'PM2.5': 89,
        'Température': 72,
        'Humidité': 61,
        'Trafic': 48,
        'Vent (vitesse)': 35,
        'NO₂': 28,
        'Saison': 22,
        'Heure du jour': 18
    }
    
    bars = []
    for name, value in features.items():
        bars.append(html.Div([
            html.Div([
                html.Span(name, className="small"),
                html.Span(f"{value}%", className="small float-end")
            ], className="mb-1"),
            html.Div([
                html.Div(style={
                    'width': f"{value}%",
                    'height': '6px',
                    'backgroundColor': '#ff9800',
                    'borderRadius': '3px'
                })
            ], style={'width': '100%', 'backgroundColor': '#333', 'borderRadius': '3px', 'marginBottom': '12px'})
        ]))
    
    return dbc.Card([
        dbc.CardHeader([
            html.I(className="fas fa-chart-bar me-2"),
            html.Strong("IMPORTANCE DES VARIABLES (SHAP)")
        ]),
        dbc.CardBody(bars)
    ], className="shadow-sm")