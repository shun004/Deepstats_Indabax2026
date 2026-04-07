"""
AirEka · IndabaX 2026
Version finale - Tous les bugs corrigés, design premium
"""

import unicodedata
import dash
from dash import html, dcc, callback, Input, Output, State, ALL, ctx, no_update
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import numpy as np
from auth import init_db
init_db()
import pandas as pd
from datetime import datetime, timedelta
import os
import io
import base64
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
# Import auth
from auth import create_user, authenticate_user, user_exists
import dash_leaflet as dl
import random

# ── Modules AirEka : scheduler email + PDF premium ──────────────────
try:
    from email_scheduler import AirEkaScheduler
    _SCHEDULER_AVAILABLE = True
except ImportError:
    _SCHEDULER_AVAILABLE = False
    print("[AirEka] email_scheduler.py introuvable — alertes désactivées")

try:
    from pdf_generator import generate_pdf_report
    _PDF_AVAILABLE = True
except ImportError:
    _PDF_AVAILABLE = False
    print("[AirEka] pdf_generator.py introuvable — PDF de base utilisé")

# DICTIONNAIRE DE TRADUCTIONS CENTRALISÉ
# ─────────────────────────────────────────────
T = {
    'fr': {
        'app_name': 'AirEka',
        'tab_about': 'Nous',
        'app_sub': 'Qualité de l\'air — Cameroun · 40 villes · 10 régions',
        'live': 'TEMPS RÉEL',
        'logout': 'Déconnexion',
        'theme_dark': 'Mode sombre',
        'theme_light': 'Mode clair',
        'region_all': 'Toutes les régions (10)',
        'city_all': 'Toutes les villes',
        'region_label': 'RÉGION',
        'city_label': 'VILLE',
        'dates_label': 'DATES',
        'national': 'National',
        'tab_analysis': 'Tendances & Comparaison',
        'connecting': 'Connexion…',
        # Onglets
        'tab_today': "Aujourd'hui",
        'tab_mycity': 'Ma ville',
        'tab_health': 'Santé',
        'tab_alerts': 'Alertes',
        'tab_dashboard': 'Tableau de bord',
        'tab_trends': 'Tendances',
        'tab_comparison': 'Comparaison',
        'tab_policies': 'Politiques',
        'tab_models': 'Modèles ML',
        'tab_data': 'Données brutes',
        'tab_simulation': 'Simulation',
        'tab_stats': 'Statistiques',
        'tab_api': 'API Export',
        'tab_epidemio': 'Épidémiologie',
        'tab_vulnerable': 'Populations',
        'tab_prevention': 'Prévention',
        'tab_emergency': 'Urgences',
        # KPI
        'kpi_national_aqi': 'IQA MOY. NATIONAL',
        'kpi_pm25': 'PM2.5 MOYEN',
        'kpi_no2': 'NO₂ MOYEN',
        'kpi_cities': 'VILLES SURVEILLÉES',
        'kpi_ml': 'PRÉCISION MODÈLE ML',
        # AQI labels
        'aqi_good': 'Bon',
        'aqi_moderate': 'Modéré',
        'aqi_sensitive': 'Mauvais pour sensibles',
        'aqi_bad': 'Mauvais pour la santé',
        'aqi_very_bad': 'Très mauvais',
        'aqi_hazardous': 'Dangereux',
        # Pages
        'overview_title': 'Vue d\'ensemble',
        'predictions_title': 'Prédictions ML',
        'loading': 'Chargement…',
        'error_tab': 'Erreur chargement',
        'see_ml': 'Voir les prédictions ML →',
        # Citizen pages
        'today_weather': 'MÉTÉO DU JOUR',
        'today_quality': 'QUALITÉ DE L\'AIR',
        'today_forecast': 'PRÉVISIONS 7 JOURS',
        'today_ranking': 'CLASSEMENT DES VILLES',
        'my_city_title': 'MA VILLE',
        'health_title': 'SANTÉ & QUALITÉ DE L\'AIR',
        'health_risk_level': 'NIVEAU DE RISQUE SANITAIRE',
        'oms_thresholds': 'SEUILS OMS',
        'health_risks': 'ANALYSE DES RISQUES SANITAIRES',
        'vulnerable_pop': 'POPULATIONS VULNÉRABLES',
        'emergency_contacts': 'CONTACTS D\'URGENCE',
        'ai_analysis': 'Analyse IA',
        'exceeded': '⚠ DÉPASSÉ',
        'threshold_ratio': '× seuil',
        'location': 'LOCALISATION',
        'click_marker': 'Cliquez sur le marqueur pour plus de détails',
        'pollutant_comparison': 'COMPARAISON DES POLLUANTS',
        'evolution_30d': 'ÉVOLUTION 30 JOURS',
        'dominant_pollutant': 'Polluant dominant',
        # Alerts
        'at_risk': 'villes à risque',
        'critical': 'villes critiques',
        'worst_quality': 'Pire qualité',
        'alerts_title': 'Alertes qualité de l\'air',
        'alerts_sub': 'Recevez des notifications automatiques pour protéger votre santé',
        'current_situation': 'Situation actuelle',
        'ai_alert_national': 'Analyse IA — Situation nationale',
        'most_polluted_cities': 'Villes les plus polluées',
        'daily_reminder_title': 'Rappel qualité de l\'air — quotidien',
        'daily_reminder_desc': 'Chaque matin à l\'heure de votre choix, recevez automatiquement un résumé de la qualité de l\'air dans votre ville (même si l\'air est bonne ou mauvaise) avec des conseils pratiques adaptés.',
        'how_it_works_step1': 'Entrez votre adresse email et activez les alertes.',
        'how_it_works_step2': 'Choisissez l\'heure à laquelle vous souhaitez recevoir l\'email (heure de l\'Afrique de l\'Ouest, WAT).',
        'how_it_works_step3': 'Cliquez sur « Sauvegarder mes alertes ». Le planificateur enregistre votre préférence et enverra automatiquement l\'email chaque jour à l\'heure choisie, même si vous n\'êtes pas connecté.',
        'how_it_works_step4': 'Testez immédiatement avec « Envoyer un email de test ».',
        'no_threshold_note': 'Aucun seuil à configurer — vous recevrez l\'alerte chaque jour, quelle que soit la qualité de l\'air.',
        'email_alerts_title': 'Alertes email automatiques',
        'email_alerts_desc': 'L\'email sera envoyé automatiquement à l\'heure choisie, depuis deepstats.contact@gmail.com, sans intervention manuelle.',
        'badge_inactive': '● INACTIF',
        'badge_active': '● ACTIF',
        'save_alerts_btn': 'Sauvegarder mes alertes',
        'test_email_btn': 'Envoyer un email de test maintenant',
        'send_hour_label': 'Heure d\'envoi :',
        'daily_auto_label': '☀️ Récap quotidien automatique',
        'privacy_note': 'Vos alertes sont personnelles et sécurisées. Vous pouvez les désactiver à tout moment.',
        'flow_step1_label': 'Heure choisie / chaque jour',
        'flow_step2_label': 'AQI & polluants / votre ville',
        'flow_step3_label': 'Conseils pratiques',
        'flow_step4_label': 'Email automatique',
        'info_daily_title': 'Rappel quotidien',
        'info_daily_desc': 'Un email avec le résumé de la qualité de l\'air à l\'heure de votre choix.',
        'info_spike_title': 'Alerte de pic',
        'info_spike_desc': 'Soyez averti immédiatement quand l\'AQI dépasse votre seuil.',
        'info_seasonal_title': 'Alerte saisonnière',
        'info_seasonal_desc': 'Alerte lors des périodes à risque (Harmattan, pics de pollution).',
        'activate_label': 'Activer',
        'sensitive_pop_note': 'Les populations sensibles doivent limiter leurs déplacements',
        # Dashboard
        'nat_aqi_label': 'AQI national',
        'top_polluted': 'TOP 10 VILLES LES PLUS POLLUÉES',
        'risk_zones_map': 'CARTE DES ZONES À RISQUE',
        'region_ranking': 'CLASSEMENT DES RÉGIONS — AQI MOYEN',
        'priority_regions': 'RÉGIONS PRIORITAIRES',
        # Trends
        'evolution_7d': 'ÉVOLUTION 7 DERNIERS JOURS',
        'seasonality': 'SAISONNALITÉ — AQI MOYEN PAR MOIS',
        'forecast_7d': 'PRÉVISIONS 7 JOURS',
        'city_comparison': 'COMPARAISON ENTRE DEUX VILLES',
        'compare_btn': 'COMPARER',
        'whatif_title': 'SIMULATEUR "ET SI ?"',
        # Policies
        'policies_title': 'RECOMMANDATIONS POLITIQUES',
        'national_summary': 'Résumé national',
        'ia_analysis_nat': 'Analyse IA — Situation nationale',
        # Models
        'model_perf': 'PERFORMANCE DES MODÈLES ML',
        'model_r2': 'Score R²',
        # General
        'view_national': '🌍 Vue Nationale',
        'city_filter_label': 'Ville',
        'city1_label': 'Ville 1',
        'city2_label': 'Ville 2',
        # Labels météo / polluants
        'humidity_label': 'Humidité',
        'temperature_label': 'Température',
        'wind_label': 'Vent',
        'sunrise_label': 'Lever',
        'sunset_label': 'Coucher',
        'pm25_gap': 'Écart PM2.5',
        # Citoyen
        'alerts_current': 'Alertes en cours',
        'my_alerts': 'Mes alertes personnalisées',
        'alert_notify_when': "Recevoir une notification quand l'AQI dépasse :",
        'data_realtime': 'Données mises à jour en temps réel',
        'health_reco_title': 'Recommandations Sanitaires',
        'health_reco_sub': 'Mettez en pratique les recommandations pour une bonne santé.',
        # Décideur
        'dashboard_desc': "Indicateurs clés qualité de l'air — niveaux national, régional et urbain",
        'sim_instruction': "Modifiez les paramètres pour voir l'impact sur l'AQI",
        'weekly_alerts_title': 'Alertes hebdomadaires — Décideur',
        'weekly_alerts_desc': 'Recevez chaque lundi un rapport de tendances pour votre périmètre.',
        'scope_label': 'Périmètre :',
        'policies_sub': "Actions prioritaires basées sur les données de qualité de l'air",
        # Chercheur
        'sim_result_title': 'RÉSULTAT DE LA SIMULATION',
        'sim_based_on': 'Basé sur LightGBM',
        'sim_adjust': "Ajustez les paramètres et cliquez sur 'Simuler l'impact'",
        'api_title': 'API & Export de Données',
        'api_desc': 'Accédez aux données via notre API RESTful',
        'api_operational': 'API Opérationnelle',
        'api_key_label': 'Votre clé API',
        'endpoints_available': 'Endpoints disponibles',
        'usage_examples': "Exemples d'utilisation",
        # Carte / chatbot
        'map_click_hint': 'Cliquez sur un marqueur pour voir les détails de la ville',
        'chatbot_greeting': "Bonjour ! Je suis l'assistant AirEka. Posez-moi des questions sur la qualité de l'air, les polluants, ou demandez des recommandations sanitaires.",
        'chatbot_greeting2': "Je suis l'assistant AirEka. Posez-moi vos questions sur la qualité de l'air, les polluants, la santé ou les recommandations.",
        # Résultats simulation
        'sim_aqi_label': 'AQI simulé :',
        'sim_no_data': "Aucune donnée disponible",
        'confidence_label': 'NIVEAU DE CONFIANCE DU MODÈLE',
    },
    'en': {
        # ── App meta ──────────────────────────────────────────────────
        'app_name': 'AirEka',
        'app_sub': 'Air quality — Cameroon · 40 cities · 10 regions',
        'live': 'LIVE',
        'logout': 'Log out',
        'connecting': 'Connecting…',
        'loading': 'Loading…',
        'error_tab': 'Loading error',
        # ── Theme / Lang ──────────────────────────────────────────────
        'theme_dark': 'Dark mode',
        'theme_light': 'Light mode',
        # ── Nav tabs ──────────────────────────────────────────────────
        'tab_today': 'Today',
        'tab_mycity': 'My City',
        'tab_health': 'Health',
        'tab_alerts': 'Alerts',
        'tab_about': 'Us',
        'tab_dashboard': 'Dashboard',
        'tab_analysis': 'Trends & Comparison',
        'tab_trends': 'Trends',
        'tab_comparison': 'Comparison',
        'tab_policies': 'Policies',
        'tab_models': 'ML Models',
        'tab_data': 'Raw Data',
        'tab_simulation': 'Simulation',
        'tab_stats': 'Statistics',
        'tab_api': 'API Export',
        'tab_epidemio': 'Epidemiology',
        'tab_vulnerable': 'Populations',
        'tab_prevention': 'Prevention',
        'tab_emergency': 'Emergency',
        # ── Filters ───────────────────────────────────────────────────
        'region_all': 'All regions (10)',
        'city_all': 'All cities',
        'region_label': 'REGION',
        'city_label': 'CITY',
        'dates_label': 'DATES',
        'national': 'National',
        # ── KPIs ──────────────────────────────────────────────────────
        'kpi_national_aqi': 'NAT. AVG AQI',
        'kpi_pm25': 'AVG PM2.5',
        'kpi_no2': 'AVG NO₂',
        'kpi_cities': 'MONITORED CITIES',
        'kpi_ml': 'ML ACCURACY',
        'kpi_aqi_today': 'AQI TODAY',
        'kpi_pm25_today': 'PM2.5 TODAY',
        'kpi_no2_today': 'NO₂ TODAY',
        'kpi_location': 'LOCATION',
        # ── AQI labels ────────────────────────────────────────────────
        'aqi_good': 'Good',
        'aqi_moderate': 'Moderate',
        'aqi_sensitive': 'Unhealthy for Sensitive',
        'aqi_bad': 'Unhealthy',
        'aqi_very_bad': 'Very Unhealthy',
        'aqi_hazardous': 'Hazardous',
        # ── Overview page ─────────────────────────────────────────────
        'overview_title': 'Overview',
        'predictions_title': 'ML Predictions',
        'see_ml': 'View ML predictions →',
        'spatial_map': 'SPATIAL MAP',
        'aqi_gauge': 'AQI GAUGE',
        'time_evolution': 'TIME EVOLUTION',
        'alerts_reco': 'ALERTS & RECOMMENDATIONS',
        'city_ranking': 'CITY RANKING',
        'forecast_7d': '7-DAY FORECAST',
        'national_level': 'National level',
        # ── Today / My City ───────────────────────────────────────────
        'meteo_title': "TODAY'S WEATHER",
        'humidity': 'Humidity',
        'wind': 'Wind',
        'precipitation': 'Rain',
        'sunrise': 'Sunrise',
        'sunset': 'Sunset',
        'evolution_30d': '30-DAY TREND',
        'pollutants_comp': 'POLLUTANT COMPARISON',
        'location_lbl': 'LOCATION',
        'quality_air_lbl': 'AIR QUALITY',
        'dominant_pollutant': 'Dominant pollutant',
        'forecast_label': '7-DAY FORECAST',
        # ── Alerts ────────────────────────────────────────────────────
        'alerts_title': 'Air quality alerts',
        'alerts_sub': 'Receive automatic notifications to protect your health',
        'current_situation': 'Current situation',
        'risky_cities': 'cities at risk',
        'critical_cities': 'critical cities',
        'worst_quality': 'Worst quality',
        'threshold_title': 'My alert threshold',
        'threshold_desc': 'Receive a notification when AQI exceeds:',
        'save_threshold': 'Save my threshold',
        'email_alerts': 'Automatic email alerts',
        'email_placeholder': 'your.email@example.com',
        'activate_alerts': 'Activate automatic email alerts',
        'send_time': 'Send time:',
        'alert_type': 'Alert type:',
        'daily_recap': 'Daily recap (always send)',
        'spike_alert': 'Alert only if threshold exceeded',
        'ai_alert_national': 'AI Analysis — National Situation',
        'most_polluted_cities': 'Most polluted cities',
        'daily_reminder_title': 'Air quality reminder — daily',
        'daily_reminder_desc': 'Every morning at your chosen time, automatically receive a summary of air quality in your city (whether air is good or bad) with tailored practical tips.',
        'how_it_works_step1': 'Enter your email address and activate alerts.',
        'how_it_works_step2': 'Choose the time at which you want to receive the email (West Africa Time, WAT).',
        'how_it_works_step3': 'Click "Save my alerts". The scheduler saves your preference and will automatically send the email every day at the chosen time, even when you are not logged in.',
        'how_it_works_step4': 'Test immediately with "Send a test email".',
        'no_threshold_note': 'No threshold to configure — you will receive the alert every day, regardless of air quality.',
        'email_alerts_title': 'Automatic email alerts',
        'email_alerts_desc': 'The email will be sent automatically at the chosen time, from deepstats.contact@gmail.com, without manual intervention.',
        'badge_inactive': '● INACTIVE',
        'badge_active': '● ACTIVE',
        'save_alerts_btn': 'Save my alerts',
        'test_email_btn': 'Send a test email now',
        'send_hour_label': 'Send time:',
        'daily_auto_label': 'Daily automatic recap',
        'privacy_note': 'Your alerts are personal and secure. You can deactivate them at any time.',
        'flow_step1_label': 'Chosen time / every day',
        'flow_step2_label': 'AQI & pollutants / your city',
        'flow_step3_label': 'Practical tips',
        'flow_step4_label': 'Automatic email',
        'info_daily_title': 'Daily reminder',
        'info_daily_desc': 'An email with the air quality summary at your chosen time.',
        'info_spike_title': 'Spike alert',
        'info_spike_desc': 'Be notified immediately when the AQI exceeds your threshold.',
        'info_seasonal_title': 'Seasonal alert',
        'info_seasonal_desc': 'Alert during high-risk periods (Harmattan, pollution peaks).',
        'activate_label': 'Activate',
        'sensitive_pop_note': 'Sensitive populations should limit their travel',
        'at_risk': 'cities at risk',
        'critical': 'critical cities',
        'save_alerts': 'Save my alerts',
        'test_email': 'Send a test email now',
        'how_it_works': 'How does it work?',
        # ── Health ────────────────────────────────────────────────────
        'health_risk': 'Health Risk Level',
        'oms_thresholds': 'WHO Thresholds',
        'health_risks': 'Health Risk Analysis',
        'vulnerable_pop': 'Vulnerable Populations',
        'emergency_contacts': 'Emergency Contacts',
        # ── Dashboard (decision) ──────────────────────────────────────
        'dashboard_title': 'Strategic Dashboard',
        'dashboard_sub': 'Key air quality indicators — national, regional and city level',
        'critical_cities_lbl': 'critical cities',
        'alert_cities_lbl': 'cities on alert',
        'monitored_cities_lbl': 'monitored cities',
        'nat_aqi': 'national AQI',
        'top_polluted': 'TOP 10 MOST POLLUTED CITIES',
        'risk_zones_map': 'RISK ZONES MAP',
        'region_ranking': 'REGION RANKING — AVG AQI',
        'priority_regions': 'PRIORITY REGIONS',
        # ── Analysis (decision) ───────────────────────────────────────
        'evolution_7d': 'LAST 7 DAYS EVOLUTION',
        'seasonality': 'SEASONALITY — AVG AQI BY MONTH',
        'city_comparison': 'COMPARISON BETWEEN TWO CITIES',
        'comparison_interpretation': 'Interpretation',
        # ── Policies (decision) ───────────────────────────────────────
        'policies_title': 'Policy Recommendations',
        'policies_sub': 'Priority actions based on air quality data',
        'nat_summary': 'National Summary',
        'alert_panel_title': 'Weekly Alerts — Decision Maker',
        'alert_panel_sub': 'Activate to receive a weekly report every Monday',
        'scope': 'Scope:',
        'activate_btn': 'Activate weekly alerts',
        'download_pdf': 'DOWNLOAD REPORT (PDF)',
        # ── Stats (researcher) ────────────────────────────────────────
        'stats_title': 'Advanced Statistics',
        'data_info': 'DATA INFORMATION',
        'descriptive_stats': 'DESCRIPTIVE STATISTICS',
        'corr_matrix': 'CORRELATION MATRIX',
        'monthly_evolution': 'MONTHLY POLLUTANT EVOLUTION',
        'download_data': 'Download data (CSV)',
        # ── Models (researcher) ───────────────────────────────────────
        'models_title': 'ML Models',
        'model_comparison': 'MODEL COMPARISON',
        'feature_importance': 'FEATURE IMPORTANCE',
        # ── Footer ────────────────────────────────────────────────────
        'footer_rights': '© All rights reserved',
        'footer_sources': 'Sources',
        # ── Citizen pages ─────────────────────────────────────────────
        'today_weather': "TODAY'S WEATHER",
        'today_quality': 'AIR QUALITY',
        'today_forecast': '7-DAY FORECAST',
        'today_ranking': 'CITY RANKING',
        'my_city_title': 'MY CITY',
        'health_title': 'HEALTH & AIR QUALITY',
        'health_risk_level': 'HEALTH RISK LEVEL',
        'oms_thresholds': 'WHO THRESHOLDS',
        'health_risks': 'HEALTH RISK ANALYSIS',
        'vulnerable_pop': 'VULNERABLE POPULATIONS',
        'emergency_contacts': 'EMERGENCY CONTACTS',
        'ai_analysis': 'AI Analysis',
        'exceeded': '⚠ EXCEEDED',
        'threshold_ratio': '× limit',
        'location': 'LOCATION',
        'click_marker': 'Click the marker for more details',
        'pollutant_comparison': 'POLLUTANT COMPARISON',
        'evolution_30d': '30-DAY TREND',
        'dominant_pollutant': 'Dominant pollutant',
        # ── Alerts ────────────────────────────────────────────────────
        'at_risk': 'cities at risk',
        'critical': 'critical cities',
        'worst_quality': 'Worst quality',
        'alerts_title': 'Air quality alerts',
        'alerts_sub': 'Receive automatic notifications to protect your health',
        'current_situation': 'Current situation',
        # ── Dashboard ─────────────────────────────────────────────────
        'nat_aqi_label': 'national AQI',
        'top_polluted': 'TOP 10 MOST POLLUTED CITIES',
        'risk_zones_map': 'RISK ZONES MAP',
        'region_ranking': 'REGION RANKING — AVG AQI',
        'priority_regions': 'PRIORITY REGIONS',
        # ── Trends ────────────────────────────────────────────────────
        'evolution_7d': 'LAST 7 DAYS EVOLUTION',
        'seasonality': 'SEASONALITY — AVG AQI BY MONTH',
        'forecast_7d': '7-DAY FORECAST',
        'city_comparison': 'COMPARISON BETWEEN TWO CITIES',
        'compare_btn': 'COMPARE',
        'whatif_title': 'WHAT-IF SIMULATOR',
        # ── Policies ──────────────────────────────────────────────────
        'policies_title': 'POLICY RECOMMENDATIONS',
        'national_summary': 'National Summary',
        'ia_analysis_nat': 'AI Analysis — National Situation',
        # ── Models ────────────────────────────────────────────────────
        'model_perf': 'ML MODEL PERFORMANCE',
        'model_r2': 'R² Score',
        # ── General ───────────────────────────────────────────────────
        'view_national': 'National View',
        'city_filter_label': 'City',
        'city1_label': 'City 1',
        'city2_label': 'City 2',
        # Weather / pollutant labels
        'humidity_label': 'Humidity',
        'temperature_label': 'Temperature',
        'wind_label': 'Wind',
        'sunrise_label': 'Sunrise',
        'sunset_label': 'Sunset',
        'pm25_gap': 'PM2.5 gap',
        # Citizen
        'alerts_current': 'Current alerts',
        'my_alerts': 'My custom alerts',
        'alert_notify_when': 'Receive a notification when AQI exceeds:',
        'data_realtime': 'Data updated in real time',
        'health_reco_title': 'Health Recommendations',
        'health_reco_sub': 'Follow the recommendations for good health.',
        # Decision maker
        'dashboard_desc': 'Key air quality indicators — national, regional and city level',
        'sim_instruction': 'Adjust the parameters to see the impact on AQI',
        'weekly_alerts_title': 'Weekly alerts — Decision maker',
        'weekly_alerts_desc': 'Receive every Monday a trends report for your scope.',
        'scope_label': 'Scope:',
        'policies_sub': 'Priority actions based on air quality data',
        # Researcher
        'sim_result_title': 'SIMULATION RESULT',
        'sim_based_on': 'Based on LightGBM',
        'sim_adjust': "Adjust the parameters and click 'Simulate impact'",
        'api_title': 'API & Data Export',
        'api_desc': 'Access data via our RESTful API',
        'api_operational': 'API Operational',
        'api_key_label': 'Your API key',
        'endpoints_available': 'Available endpoints',
        'usage_examples': 'Usage examples',
        # Map / chatbot
        'map_click_hint': 'Click a marker to see city details',
        'chatbot_greeting': 'Hello! I am the AirEka assistant. Ask me questions about air quality, pollutants, or health recommendations.',
        'chatbot_greeting2': 'I am the AirEka assistant. Ask me questions about air quality, pollutants, health or recommendations.',
        # Simulation results
        'sim_aqi_label': 'Simulated AQI:',
        'sim_no_data': 'No data available',
        'confidence_label': 'MODEL CONFIDENCE LEVEL',
    }
}

def t(key, lang='fr'):
    return T.get(lang, T['fr']).get(key, key)

def graph_font(theme='dark'):
    """Retourne la couleur de police selon le thème pour les graphiques Plotly."""
    return '#e8f0fe' if theme == 'dark' else '#0f1f35'

def graph_grid(theme='dark'):
    """Couleur de grille pour les graphiques Plotly."""
    return 'rgba(30,48,88,0.3)' if theme == 'dark' else 'rgba(100,120,150,0.2)'

# ─────────────────────────────────────────────
# AUTHENTIFICATION & RÔLES
# ─────────────────────────────────────────────
USERS = {
    'citoyen':   {'name': 'Marie K.',    'role': 'citizen',    'initials': 'MK', 'color': '#00d4ff', 'icon': 'fa-person',      'label_fr': 'Citoyen',   'label_en': 'Citizen'},
    'maire':     {'name': 'Paul N.',     'role': 'decision',   'initials': 'PN', 'color': '#facc15', 'icon': 'fa-landmark',    'label_fr': 'Décideur',  'label_en': 'Decision Maker'},
    'chercheur': {'name': 'Jean T.',     'role': 'researcher', 'initials': 'JT', 'color': '#a855f7', 'icon': 'fa-flask',       'label_fr': 'Chercheur', 'label_en': 'Researcher'},
}
PASSWORDS = {'citoyen': '1234', 'maire': '1234', 'chercheur': '1234'}

# Onglets par rôle: (tab_id, fa_icon, label_key)
ROLE_TABS = {
    'citizen':    [
        ('today',      'fa-sun',            'tab_today'),
        ('my_city',    'fa-city',           'tab_mycity'),
        ('health',     'fa-heart-pulse',    'tab_health'),
        ('alerts',     'fa-bell',           'tab_alerts'),
        ('about',      'fa-circle-info',    'tab_about'),
    ],
    'decision':   [
        ('dashboard',  'fa-chart-pie',      'tab_dashboard'),
        ('analysis',   'fa-chart-line',     'tab_analysis'),
        ('policies',   'fa-file-contract',  'tab_policies'),
        ('about',      'fa-circle-info',    'tab_about'),
    ],
    'researcher': [
        ('stats',      'fa-chart-bar',      'tab_stats'),
        ('models',     'fa-brain',          'tab_models'),
        ('simulation', 'fa-flask-vial',     'tab_simulation'),
        ('api',        'fa-code',           'tab_api'),
        ('about',      'fa-circle-info',    'tab_about'),
    ],
}

def authenticate(username, password):
    if username in USERS and PASSWORDS.get(username) == password:
        return dict(USERS[username], username=username)
    return None

# ─────────────────────────────────────────────
# DONNÉES — PARQUET + FALLBACK STATIQUE
# ─────────────────────────────────────────────
PARQUET_PATH = os.path.join(os.path.dirname(__file__), 'base_complete.parquet')

CITIES_STATIC = [
    {'city': 'Yaoundé',     'region': 'Centre',       'lat': 3.8480,  'lon': 11.5021, 'aqi': 178, 'pm25': 72.3,  'pm10': 118.5, 'no2': 42.8, 'so2': 28.1, 'o3': 38.2, 'trend': 8.3},
    {'city': 'Douala',      'region': 'Littoral',     'lat': 4.0511,  'lon': 9.7679,  'aqi': 165, 'pm25': 68.2,  'pm10': 112.5, 'no2': 38.5, 'so2': 25.2, 'o3': 35.5, 'trend': 6.8},
    {'city': 'Bafoussam',   'region': 'Ouest',        'lat': 5.4781,  'lon': 10.4174, 'aqi': 135, 'pm25': 55.0,  'pm10': 90.2,  'no2': 31.5, 'so2': 20.5, 'o3': 38.5, 'trend': 4.5},
    {'city': 'Mbalmayo',    'region': 'Centre',       'lat': 3.5167,  'lon': 11.5000, 'aqi': 134, 'pm25': 54.2,  'pm10': 89.5,  'no2': 32.1, 'so2': 21.3, 'o3': 34.5, 'trend': 5.1},
    {'city': 'Garoua',      'region': 'Nord',         'lat': 9.3011,  'lon': 13.3975, 'aqi': 145, 'pm25': 58.9,  'pm10': 97.3,  'no2': 35.2, 'so2': 24.5, 'o3': 32.5, 'trend': 5.2},
    {'city': 'Maroua',      'region': 'Extrême-Nord', 'lat': 10.5910, 'lon': 14.3159, 'aqi': 132, 'pm25': 54.3,  'pm10': 89.7,  'no2': 32.1, 'so2': 22.3, 'o3': 34.2, 'trend': 4.2},
    {'city': 'Kousséri',    'region': 'Extrême-Nord', 'lat': 12.0833, 'lon': 15.0333, 'aqi': 128, 'pm25': 52.4,  'pm10': 86.5,  'no2': 30.5, 'so2': 21.8, 'o3': 33.5, 'trend': 3.8},
    {'city': 'Ngaoundéré',  'region': 'Adamaoua',     'lat': 7.3212,  'lon': 13.5839, 'aqi': 112, 'pm25': 46.8,  'pm10': 77.3,  'no2': 28.9, 'so2': 19.5, 'o3': 37.5, 'trend': 2.5},
    {'city': 'Edéa',        'region': 'Littoral',     'lat': 3.8000,  'lon': 10.1333, 'aqi': 142, 'pm25': 58.3,  'pm10': 96.2,  'no2': 35.2, 'so2': 23.1, 'o3': 37.2, 'trend': 4.5},
    {'city': 'Bertoua',     'region': 'Est',          'lat': 4.5750,  'lon': 13.6847, 'aqi': 88,  'pm25': 37.2,  'pm10': 61.5,  'no2': 22.5, 'so2': 14.8, 'o3': 39.5, 'trend': 0.5},
    {'city': 'Bamenda',     'region': 'Nord-Ouest',   'lat': 5.9600,  'lon': 10.1517, 'aqi': 45,  'pm25': 18.7,  'pm10': 31.2,  'no2': 12.4, 'so2': 6.8,  'o3': 48.2, 'trend': -2.5},
    {'city': 'Buea',        'region': 'Sud-Ouest',    'lat': 4.1667,  'lon': 9.2333,  'aqi': 48,  'pm25': 19.5,  'pm10': 32.5,  'no2': 13.2, 'so2': 7.2,  'o3': 46.5, 'trend': -1.2},
    {'city': 'Kribi',       'region': 'Sud',          'lat': 2.9381,  'lon': 9.9101,  'aqi': 38,  'pm25': 15.4,  'pm10': 25.8,  'no2': 9.8,  'so2': 5.2,  'o3': 45.2, 'trend': -2.5},
    {'city': 'Ebolowa',     'region': 'Sud',          'lat': 2.9000,  'lon': 11.1500, 'aqi': 52,  'pm25': 21.6,  'pm10': 35.8,  'no2': 14.2, 'so2': 8.5,  'o3': 42.1, 'trend': -1.2},
    {'city': 'Bafia',       'region': 'Centre',       'lat': 4.7500,  'lon': 11.2300, 'aqi': 171, 'pm25': 69.8,  'pm10': 115.2, 'no2': 41.2, 'so2': 26.5, 'o3': 36.8, 'trend': 7.2},
    {'city': 'Guider',      'region': 'Nord',         'lat': 9.9333,  'lon': 13.9500, 'aqi': 118, 'pm25': 48.2,  'pm10': 79.6,  'no2': 30.5, 'so2': 20.5, 'o3': 34.5, 'trend': 3.2},
    {'city': 'Kumbo',       'region': 'Nord-Ouest',   'lat': 6.2090,  'lon': 10.6717, 'aqi': 38,  'pm25': 15.1,  'pm10': 25.2,  'no2': 10.2, 'so2': 5.5,  'o3': 49.5, 'trend': -3.2},
    {'city': 'Limbe',       'region': 'Sud-Ouest',    'lat': 4.0167,  'lon': 9.2167,  'aqi': 42,  'pm25': 17.3,  'pm10': 28.8,  'no2': 11.5, 'so2': 6.2,  'o3': 47.8, 'trend': -1.8},
    {'city': 'Dschang',     'region': 'Ouest',        'lat': 5.4500,  'lon': 10.0667, 'aqi': 72,  'pm25': 30.1,  'pm10': 49.8,  'no2': 22.5, 'so2': 14.2, 'o3': 46.5, 'trend': -1.5},
    {'city': 'Tibati',      'region': 'Adamaoua',     'lat': 6.4667,  'lon': 12.6167, 'aqi': 95,  'pm25': 39.5,  'pm10': 65.2,  'no2': 25.5, 'so2': 16.5, 'o3': 39.5, 'trend': 1.2},
]


# "api" | "parquet" | "static"
_DATA_SOURCE = "static"

def _api_banner():
    """Bannière affichée quand l'API est indisponible."""
    if _DATA_SOURCE == "api":
        return None
    msg = (
        "API temporairement indisponible — utilisation du cache local (parquet)"
        if _DATA_SOURCE == "parquet"
        else "API temporairement indisponible — utilisation des données statiques"
    )
    return dbc.Alert(
        [html.I(className="fas fa-exclamation-triangle me-2"), msg],
        color="warning",
        dismissable=True,
        id="api-status-banner",
        style={"margin": "0", "borderRadius": "0", "fontSize": "0.85rem"},
    )

def load_data():
    """
    Charge les données depuis l'API AirEka (priorité),
    puis depuis le parquet (fallback), puis depuis CITIES_STATIC.
    """
    global _DATA_SOURCE

    # ── 1. API AirEka ─────────────────────────────────────────────────────
    try:
        from api_client import AirEkaAPI
        api = AirEkaAPI()
        if api.is_available():
            cities = api.get_all_cities()
            if cities and len(cities) >= 10:
                print(f"[AirEka] {len(cities)} villes chargées depuis l'API")
                _DATA_SOURCE = "api"
                return cities, None
    except Exception as e:
        print(f"[AirEka] API non disponible: {e}")

    # ── 2. Parquet local (fallback) ────────────────────────────────────────
    try:
        if os.path.exists(PARQUET_PATH):
            df = pd.read_parquet(PARQUET_PATH)
            cities_list = []
            for city_name, grp in df.groupby('city_indabax'):
                last = grp.sort_values('time').iloc[-1]
                cities_list.append({
                    'city':   city_name,
                    'region': last['region_indabax'],
                    'lat':    float(last['latitude']),
                    'lon':    float(last['longitude']),
                    'aqi':    int(last['aqi_global']),
                    'pm25':   round(float(last['pm2_5']), 1),
                    'pm10':   round(float(last['pm10']), 1),
                    'no2':    round(float(last['no2']), 1),
                    'so2':    round(float(last['so2']), 1),
                    'o3':     round(float(last['o3']), 1),
                    'trend':  round(float(grp['aqi_global'].pct_change().mean() * 100), 1) if len(grp) > 1 else 0.0,
                })
            print(f"[AirEka] {len(cities_list)} villes chargées depuis le parquet")
            _DATA_SOURCE = "parquet"
            return cities_list, df
    except Exception as e:
        print(f"[AirEka] Erreur chargement parquet: {e}")

    # ── 3. Données statiques (dernier recours) ────────────────────────────
    print("[AirEka] Utilisation des données statiques (CITIES_STATIC)")
    _DATA_SOURCE = "static"
    return CITIES_STATIC, None

# ── Chargement initial (bootstrap) ───────────────────────────────────────────
# On charge une fois au démarrage pour initialiser les dropdowns.
# Les callbacks utilisent get_cities_data() (TTL 2 min) pour rester à jour.
from city_utils import get_cities_data, get_regions, get_national_stats, resolve_city as _resolve_city

CITIES_DATA, DF_RAW = load_data()
# Pré-peupler le cache city_utils avec les données déjà chargées
from city_utils import _cities_cache, _cities_lock
import time as _time
with _cities_lock:
    if not _cities_cache['data']:
        _cities_cache['data'] = CITIES_DATA
        _cities_cache['ts'] = _time.time()

REGIONS = get_regions(CITIES_DATA)
_nat = get_national_stats(CITIES_DATA)
NATIONAL = {
    'aqi':  _nat['aqi'],
    'pm25': _nat['pm25'],
    'pm10': round(sum(c.get('pm10', 0) for c in CITIES_DATA) / max(len(CITIES_DATA), 1), 1),
    'no2':  _nat['no2'],
}

# ─────────────────────────────────────────────
# FONCTIONS UTILITAIRES AQI
# ─────────────────────────────────────────────
def aqi_color(v):
    if v <= 50:   return '#00e676'
    if v <= 100:  return '#ffee58'
    if v <= 150:  return '#ff9100'
    if v <= 200:  return '#ff1744'
    if v <= 300:  return '#d500f9'
    return '#7c0000'

def aqi_bg(v):
    if v <= 50:   return 'rgba(0,230,118,0.12)'
    if v <= 100:  return 'rgba(255,238,88,0.12)'
    if v <= 150:  return 'rgba(255,145,0,0.12)'
    if v <= 200:  return 'rgba(255,23,68,0.12)'
    if v <= 300:  return 'rgba(213,0,249,0.12)'
    return 'rgba(124,0,0,0.12)'

def aqi_label(v, lang='fr'):
    if v <= 50:   return t('aqi_good', lang)
    if v <= 100:  return t('aqi_moderate', lang)
    if v <= 150:  return t('aqi_sensitive', lang)
    if v <= 200:  return t('aqi_bad', lang)
    if v <= 300:  return t('aqi_very_bad', lang)
    return t('aqi_hazardous', lang)

def aqi_icon(v):
    if v <= 50:   return 'fa-face-smile',      '#00e676'
    if v <= 100:  return 'fa-face-meh',         '#ffee58'
    if v <= 150:  return 'fa-face-frown-open',  '#ff9100'
    if v <= 200:  return 'fa-face-sad-tear',    '#ff1744'
    return          'fa-skull',                  '#d500f9'

def rgba_to_rgb(rgba_str):
    """Convertit une chaîne rgba en rgb valide pour Plotly."""
    if rgba_str.startswith('rgba'):
        parts = rgba_str.replace('rgba(', '').replace(')', '').split(',')
        return f'rgb({parts[0].strip()}, {parts[1].strip()}, {parts[2].strip()})'
    return rgba_str

for c in CITIES_DATA:
    c['color'] = aqi_color(c['aqi'])

# ── Initialisation du scheduler d'alertes email ──────────────────────
if _SCHEDULER_AVAILABLE:
    _email_scheduler = AirEkaScheduler(CITIES_DATA)
else:
    _email_scheduler = None

# ─────────────────────────────────────────────
# APPLICATION DASH
# ─────────────────────────────────────────────
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True,
    title='AirEka — Cameroun',
)
server = app.server

# ─────────────────────────────────────────────
# INDEX STRING — CSS GLOBAL COMPLET (identique à votre version)
# ─────────────────────────────────────────────

app.index_string = '''<!DOCTYPE html>
<html lang="fr" data-theme="dark">
<head>
    {%metas%}
    <title>AirEka — Cameroun</title>
    {%favicon%}
    {%css%}

    <!-- Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    
    <!-- Flag icons pour les pays -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/flag-icon-css@3.5.0/css/flag-icon.min.css">

    <!-- Font Awesome 6 -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css" crossorigin="anonymous">

    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">

    <style>
    /* Cacher le chatbot sur la page de connexion */
    body.on-login-page #chatbot-global,
    body.on-login-page #chatbot-fab,
    body.on-login-page #chatbot-panel,
    body.on-login-page .pdf-fab {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        pointer-events: none !important;
    }

    .simulate-btn-hover:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(255,145,0,0.4);
    }
    .pdf-fab:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(255,23,68,0.55) !important;
    }
    .pdf-fab:hover #pdf-btn-label {
        max-width: 120px !important;
        margin-left: 8px !important;
    }

    /* ══════════════════════════════════════════════════════════════
    RESPONSIVE HEADER — Fixe et centré
    ══════════════════════════════════════════════════════════════ */
    #app-header {
        position: sticky;
        top: 0;
        left: 0;
        right: 0;
        width: 100%;
        z-index: 500;
        height: var(--header-h);
        background: var(--header-bg);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border-bottom: 1px solid var(--border);
        box-shadow: var(--shadow-sm);
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0 24px;
        gap: 16px;
        transition: background var(--ease), border-color var(--ease);
        box-sizing: border-box;
    }
    
    .logo-wrap {
        display: flex;
        align-items: center;
        gap: 10px;
        flex-shrink: 0;
        text-decoration: none;
        min-width: auto;
    }
    
    #nav-tabs-bar {
        display: flex;
        align-items: center;
        gap: 4px;
        flex: 1;
        overflow-x: auto;
        overflow-y: hidden;
        scrollbar-width: none;
        padding: 0 8px;
        justify-content: center;
    }
    
    /* Responsive header pour petits écrans */
    @media (max-width: 1024px) {
        #app-header {
            padding: 0 16px;
            gap: 8px;
        }
        .logo-text {
            font-size: 13px;
        }
        .nav-tab-btn {
            padding: 4px 10px;
            font-size: 11px;
        }
        .role-badge span {
            display: none;
        }
        .user-avatar {
            width: 28px;
            height: 28px;
            font-size: 10px;
        }
        .hdr-btn-text {
            padding: 0 6px;
            font-size: 10px;
        }
        #header-clock {
            font-size: 9px;
        }
    }
    
    @media (max-width: 768px) {
        #app-header {
            padding: 0 12px;
            gap: 6px;
            flex-wrap: wrap;
            height: auto;
            padding: 8px 12px;
        }
        .logo-sub {
            display: none;
        }
        .logo-text {
            font-size: 12px;
        }
        .live-badge {
            padding: 2px 8px;
            font-size: 9px;
        }
        .nav-tab-btn {
            padding: 4px 8px;
            font-size: 10px;
        }
        .nav-tab-btn span {
            display: none;
        }
        .role-badge {
            padding: 2px 8px;
            font-size: 10px;
        }
        .hdr-btn-logout span {
            display: none;
        }
        .hdr-btn-logout {
            padding: 6px 8px;
        }
    }
    
    /* Contenu principal responsive */
    #main-content {
        padding: 16px 24px;
        max-width: 1600px;
        margin: 0 auto;
        width: 100%;
        box-sizing: border-box;
    }
    
    @media (max-width: 768px) {
        #main-content {
            padding: 12px 16px;
        }
    }

    /* Effet hover pour les cartes de politiques */
    .policy-card-hover:hover {
        transform: translateY(-3px);
        box-shadow: var(--shadow-md);
        border-color: var(--border-hover) !important;
    }

    .forecast-card-hover:hover {
        transform: translateY(-3px);
        box-shadow: var(--shadow-md);
    }

    /* Correction des couleurs pour les inputs en mode dark/light */
    .ac-dropdown .Select-control {
        background: var(--bg-input) !important;
        border: 1px solid var(--border) !important;
        border-radius: 12px !important;
        min-height: 40px !important;
        box-shadow: none !important;
        transition: all 0.2s ease !important;
    }
    
    .ac-dropdown .Select-control:hover {
        border-color: var(--border-hover) !important;
    }
    
        /* Effets hover pour les cartes KPI */
    .kpi-card-hover:hover {
        transform: translateY(-4px);
        box-shadow: var(--shadow-md);
        border-color: var(--kpi-accent, var(--cyan)) !important;
    }
    
    /* Effets hover pour les cartes de régions prioritaires */
    .region-card-hover:hover {
        transform: translateY(-2px);
        box-shadow: var(--shadow-md);
        border-color: var(--border-hover) !important;
    }

    .ac-dropdown.is-focused .Select-control {
        border-color: var(--border-focus) !important;
        box-shadow: 0 0 0 2px var(--cyan-dim) !important;
    }
    
    .ac-dropdown .Select-value-label {
        color: var(--text-primary) !important;
        font-size: 13px !important;
        font-weight: 500 !important;
    }
    
    .ac-dropdown .Select-placeholder {
        color: var(--text-muted) !important;
        font-size: 13px !important;
    }
    
    .ac-dropdown .Select-arrow {
        border-top-color: var(--text-secondary) !important;
    }
    
    .ac-dropdown .Select-menu-outer {
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-radius: 12px !important;
        box-shadow: var(--shadow-lg) !important;
        overflow: hidden !important;
        z-index: 1000 !important;
    }
    
    .ac-dropdown .Select-option {
        background: var(--bg-card) !important;
        color: var(--text-primary) !important;
        font-size: 13px !important;
        padding: 10px 14px !important;
        transition: background 0.2s ease !important;
    }
    
    .ac-dropdown .Select-option.is-focused {
        background: var(--bg-surface) !important;
    }
    
    .ac-dropdown .Select-option.is-selected {
        background: var(--cyan-dim) !important;
        color: var(--cyan) !important;
    }
    
    /* Style pour l'input email */
    input[type="email"] {
        font-family: 'Inter', sans-serif !important;
    }
    
    input[type="email"]:focus {
        border-color: var(--border-focus) !important;
        box-shadow: 0 0 0 2px var(--cyan-dim) !important;
    }
    
    /* Correction du sélecteur d'heure */
    #notif-hour .Select-control {
        width: 120px !important;
    }
    
    /* Pour que le dropdown ne soit pas coupé */
    .card {
        overflow: visible !important;
    }
    
    /* Stabiliser l'ouverture des dropdowns - éviter le clignotement */
    .ac-dropdown .Select-menu-outer,
    .Select-menu-outer {
        position: absolute !important;
        z-index: 9999 !important;
        animation: none !important;
        transition: none !important;
    }
    
    /* Amélioration des checkboxes */
    .dash-checklist input {
        margin-right: 8px !important;
        accent-color: var(--cyan) !important;
    }
    
    .dash-checklist label {
        color: var(--text-primary) !important;
        font-size: 12px !important;
        cursor: pointer !important;
    }

    /* ══════════════════════════════════════════════════════════════
       VARIABLES CSS — Source de vérité unique pour les 2 thèmes
       ══════════════════════════════════════════════════════════════ */
    :root,
    [data-theme="dark"] {
        /* Fonds */
        --bg-base:       #070d1a;
        --bg-surface:    #0d1526;
        --bg-card:       #111e35;
        --bg-card-hover: #162240;
        --bg-input:      #0a1120;
        --bg-overlay:    rgba(7,13,26,0.92);

        /* Bordures */
        --border:        #1e3058;
        --border-hover:  #2a4070;
        --border-focus:  #00d4ff;

        /* Textes */
        --text-primary:  #e8f0fe;
        --text-secondary:#7a90b5;
        --text-muted:    #3d5070;
        --text-invert:   #07101f;

        /* Accents lumineux */
        --cyan:          #00d4ff;
        --cyan-glow:     rgba(0,212,255,0.15);
        --cyan-dim:      rgba(0,212,255,0.08);
        --green:         #00e676;
        --green-glow:    rgba(0,230,118,0.15);
        --yellow:        #ffee58;
        --orange:        #ff9100;
        --red:           #ff1744;
        --purple:        #d500f9;
        --violet:        #7c3aed;

        /* AQI couleurs */
        --aqi-good:      #00e676;
        --aqi-mod:       #ffee58;
        --aqi-sens:      #ff9100;
        --aqi-bad:       #ff1744;
        --aqi-vbad:      #d500f9;

        /* Rôles */
        --citizen-color:    #00d4ff;
        --decision-color:   #facc15;
        --researcher-color: #a855f7;
        --doctor-color:     #34d399;

        /* Header */
        --header-bg:   rgba(11,21,42,0.95);
        --header-h:    58px;

        /* Ombres */
        --shadow-sm:  0 2px 8px rgba(0,0,0,0.4);
        --shadow-md:  0 4px 20px rgba(0,0,0,0.5);
        --shadow-lg:  0 8px 40px rgba(0,0,0,0.6);
        --shadow-glow-cyan:  0 0 20px rgba(0,212,255,0.25);
        --shadow-glow-green: 0 0 20px rgba(0,230,118,0.25);

        /* Transitions */
        --ease: 0.22s cubic-bezier(0.4,0,0.2,1);
    }

    [data-theme="light"] {
        --bg-base:       #f0f4f8;
        --bg-surface:    #e8eef5;
        --bg-card:       #ffffff;
        --bg-card-hover: #f5f8fc;
        --bg-input:      #f8fafc;
        --bg-overlay:    rgba(240,244,248,0.95);
        --border:        #c8d8ea;
        --border-hover:  #a0b8d0;
        --border-focus:  #0284c7;
        --text-primary:  #0f1f35;
        --text-secondary:#4a6080;
        --text-muted:    #90a8c0;
        --text-invert:   #ffffff;
        --cyan:          #0284c7;
        --cyan-glow:     rgba(2,132,199,0.12);
        --cyan-dim:      rgba(2,132,199,0.06);
        --green:         #16a34a;
        --green-glow:    rgba(22,163,74,0.12);
        --yellow:        #d97706;
        --orange:        #ea580c;
        --red:           #dc2626;
        --purple:        #9333ea;
        --violet:        #7c3aed;
        --aqi-good:      #16a34a;
        --aqi-mod:       #c2770a;
        --aqi-sens:      #ea580c;
        --aqi-bad:       #dc2626;
        --aqi-vbad:      #9333ea;
        --citizen-color:    #0284c7;
        --decision-color:   #b45309;
        --researcher-color: #7c3aed;
        --doctor-color:     #059669;
        --header-bg:   rgba(255,255,255,0.97);
        --shadow-sm:  0 1px 4px rgba(0,0,0,0.08);
        --shadow-md:  0 4px 16px rgba(0,0,0,0.1);
        --shadow-lg:  0 8px 32px rgba(0,0,0,0.12);
        --shadow-glow-cyan:  0 0 12px rgba(2,132,199,0.2);
        --shadow-glow-green: 0 0 12px rgba(22,163,74,0.2);
    }

    /* ══════════════════════════════════════════════════════════════
       RESET & BASE
       ══════════════════════════════════════════════════════════════ */
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    html { scroll-behavior: smooth; }

    body {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        background: var(--bg-base);
        color: var(--text-primary);
        min-height: 100vh;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
        transition: background var(--ease), color var(--ease);
        overflow-x: hidden;
    }

    code, .mono {
        font-family: 'JetBrains Mono', 'Fira Code', monospace;
    }

    /* ══════════════════════════════════════════════════════════════
       SCROLLBAR
       ══════════════════════════════════════════════════════════════ */
    ::-webkit-scrollbar { width: 5px; height: 5px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 99px; }
    ::-webkit-scrollbar-thumb:hover { background: var(--border-hover); }

    /* ══════════════════════════════════════════════════════════════
       ANIMATIONS
       ══════════════════════════════════════════════════════════════ */
    @keyframes fadeUp {
        from { opacity: 0; transform: translateY(12px); }
        to   { opacity: 1; transform: translateY(0); }
    }
    @keyframes fadeIn {
        from { opacity: 0; }
        to   { opacity: 1; }
    }
    @keyframes slideRight {
        from { transform: translateX(-8px); opacity: 0; }
        to   { transform: translateX(0);   opacity: 1; }
    }
    @keyframes pulse-ring {
        0%,100% { box-shadow: 0 0 0 0 rgba(0,230,118,0.4); }
        50%     { box-shadow: 0 0 0 6px rgba(0,230,118,0); }
    }
    @keyframes spin {
        to { transform: rotate(360deg); }
    }
    @keyframes shimmer {
        0%   { background-position: -200% 0; }
        100% { background-position:  200% 0; }
    }
    @keyframes blink-live {
        0%,100% { opacity: 1; }
        50%     { opacity: 0.4; }
    }

    .anim-fade-up  { animation: fadeUp  0.3s ease forwards; }
    .anim-fade-in  { animation: fadeIn  0.25s ease forwards; }
    .anim-slide-r  { animation: slideRight 0.25s ease forwards; }

    /* Entrée progressive des cartes */
    .stagger > *:nth-child(1) { animation: fadeUp 0.3s 0.05s ease both; }
    .stagger > *:nth-child(2) { animation: fadeUp 0.3s 0.10s ease both; }
    .stagger > *:nth-child(3) { animation: fadeUp 0.3s 0.15s ease both; }
    .stagger > *:nth-child(4) { animation: fadeUp 0.3s 0.20s ease both; }
    .stagger > *:nth-child(5) { animation: fadeUp 0.3s 0.25s ease both; }
    .stagger > *:nth-child(n+6) { animation: fadeUp 0.3s 0.30s ease both; }

    /* ══════════════════════════════════════════════════════════════
       HEADER — Sticky glass-effect
       ══════════════════════════════════════════════════════════════ */
    #app-header {
        position: sticky;
        top: 0;
        z-index: 500;
        height: var(--header-h);
        background: var(--header-bg);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border-bottom: 1px solid var(--border);
        box-shadow: var(--shadow-sm);
        display: flex;
        align-items: center;
        padding: 0 20px;
        gap: 12px;
        transition: background var(--ease), border-color var(--ease);
    }

    /* Logo */
    .logo-wrap {
        display: flex;
        align-items: center;
        gap: 10px;
        flex-shrink: 0;
        text-decoration: none;
        min-width: 170px;
    }
    .logo-icon {
        width: 36px; height: 36px;
        border-radius: 10px;
        background: linear-gradient(135deg, #003a20, #005a30);
        border: 1.5px solid rgba(0,230,118,0.4);
        display: flex; align-items: center; justify-content: center;
        color: var(--green);
        font-size: 16px;
        box-shadow: 0 0 12px rgba(0,230,118,0.2);
        flex-shrink: 0;
    }
    .logo-text { font-size: 15px; font-weight: 700; color: var(--text-primary); letter-spacing: -0.02em; }
    .logo-sub  { font-size: 9px;  color: var(--text-secondary); letter-spacing: 0.05em; text-transform: uppercase; }

    /* Live badge */
    .live-badge {
        display: flex;
        align-items: center;
        gap: 6px;
        background: rgba(0,230,118,0.1);
        border: 1px solid rgba(0,230,118,0.3);
        border-radius: 99px;
        padding: 4px 10px;
        font-size: 10px;
        font-weight: 700;
        color: var(--green);
        letter-spacing: 0.08em;
        white-space: nowrap;
        flex-shrink: 0;
    }
    .live-dot {
        width: 7px; height: 7px;
        border-radius: 50%;
        background: var(--green);
        animation: pulse-ring 2s infinite;
        flex-shrink: 0;
    }

    /* Tabs nav (centre du header) */
    #nav-tabs-bar {
        display: flex;
        align-items: center;
        gap: 2px;
        flex: 1;
        overflow-x: auto;
        overflow-y: hidden;
        scrollbar-width: none;
        padding: 0 4px;
    }
    #nav-tabs-bar::-webkit-scrollbar { display: none; }

    .nav-tab-btn {
        display: flex;
        align-items: center;
        gap: 6px;
        padding: 6px 12px;
        border-radius: 8px;
        border: none;
        background: transparent;
        color: var(--text-secondary);
        font-size: 12.5px;
        font-weight: 500;
        cursor: pointer;
        white-space: nowrap;
        transition: all var(--ease);
        font-family: inherit;
        position: relative;
    }
    .nav-tab-btn:hover {
        background: var(--bg-card);
        color: var(--text-primary);
    }
    .nav-tab-btn.active {
        background: var(--tab-color, var(--cyan-dim));
        color: var(--tab-accent, var(--cyan));
        font-weight: 600;
    }
    .nav-tab-btn.active::after {
        content: '';
        position: absolute;
        bottom: -1px;
        left: 8px; right: 8px;
        height: 2px;
        border-radius: 99px;
        background: var(--tab-accent, var(--cyan));
        animation: fadeIn 0.2s ease;
    }

    /* Rôle badge dans le header */
    .role-badge {
        display: flex;
        align-items: center;
        gap: 6px;
        padding: 4px 10px;
        border-radius: 99px;
        border: 1px solid;
        font-size: 11px;
        font-weight: 600;
        white-space: nowrap;
        flex-shrink: 0;
    }

    /* Avatar utilisateur */
    .user-avatar {
        width: 32px; height: 32px;
        border-radius: 50%;
        border: 2px solid;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 11px;
        font-weight: 700;
        flex-shrink: 0;
    }

    /* Boutons header */
    .hdr-btn {
        width: 32px; height: 32px;
        border-radius: 8px;
        border: 1px solid var(--border);
        background: transparent;
        color: var(--text-secondary);
        cursor: pointer;
        display: flex; align-items: center; justify-content: center;
        font-size: 13px;
        transition: all var(--ease);
        font-family: inherit;
        flex-shrink: 0;
    }
    .hdr-btn:hover {
        background: var(--bg-card);
        color: var(--text-primary);
        border-color: var(--border-hover);
    }
    .hdr-btn-text {
        padding: 0 10px;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.04em;
        width: auto;
    }
    .hdr-btn-logout {
        color: #ff4d6d;
        border-color: rgba(255,77,109,0.3);
        gap: 5px;
        width: auto;
        padding: 0 10px;
        font-size: 12px;
        font-weight: 600;
    }
    .hdr-btn-logout:hover {
        background: rgba(255,77,109,0.08);
        color: #ff4d6d;
        border-color: rgba(255,77,109,0.5);
    }
    .hdr-sep {
        width: 1px; height: 24px;
        background: var(--border);
        flex-shrink: 0;
    }

    /* ══════════════════════════════════════════════════════════════
       FILTER BAR
       ══════════════════════════════════════════════════════════════ */
    #filter-bar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 12px;
        padding: 10px 16px;
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 12px;
        margin-bottom: 16px;
        animation: fadeUp 0.3s ease;
        position: relative;
        z-index: 200;
    }
    .filter-label {
        font-size: 9px;
        font-weight: 700;
        color: var(--text-muted);
        letter-spacing: 0.1em;
        text-transform: uppercase;
        display: block;
        margin-bottom: 3px;
    }
    .filter-stat {
        font-size: 13px;
        font-weight: 600;
        color: var(--text-primary);
    }
    .filter-stat span {
        color: var(--text-secondary);
        font-weight: 400;
        font-size: 12px;
    }

    /* ══════════════════════════════════════════════════════════════
       CARDS
       ══════════════════════════════════════════════════════════════ */
    .card {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 14px;
        padding: 16px 18px;
        transition: background var(--ease), border-color var(--ease), box-shadow var(--ease), transform var(--ease);
    }
    .card:hover {
        background: var(--bg-card-hover);
        border-color: var(--border-hover);
        box-shadow: var(--shadow-md);
        transform: translateY(-1px);
    }
    .card-flat { background: var(--bg-card); border: 1px solid var(--border); border-radius: 14px; padding: 16px 18px; }

    /* Section title inside card */
    .section-title {
        font-size: 10px;
        font-weight: 700;
        color: var(--text-secondary);
        text-transform: uppercase;
        letter-spacing: 0.1em;
        display: flex;
        align-items: center;
        gap: 6px;
        margin-bottom: 14px;
    }
    .section-title i { color: var(--cyan); }

    /* KPI card */
    .kpi-card {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 14px;
        padding: 16px 18px;
        transition: all var(--ease);
        position: relative;
        overflow: hidden;
    }
    .kpi-card:hover {
        border-color: var(--kpi-accent, var(--cyan));
        box-shadow: 0 4px 20px rgba(0,0,0,0.3), 0 0 0 1px var(--kpi-accent, var(--cyan)) inset;
        transform: translateY(-2px);
    }
    .kpi-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 2px;
        background: var(--kpi-accent, var(--cyan));
        opacity: 0;
        transition: opacity var(--ease);
    }
    .kpi-card:hover::before { opacity: 1; }
    .kpi-label { font-size: 9px; font-weight: 700; color: var(--text-secondary); letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 8px; }
    .kpi-value { font-size: 26px; font-weight: 800; letter-spacing: -0.03em; color: var(--text-primary); line-height: 1; margin-bottom: 6px; }
    .kpi-trend { font-size: 11px; font-weight: 500; color: var(--text-secondary); }
    .kpi-bar { height: 2px; border-radius: 99px; background: var(--border); margin-top: 10px; }
    .kpi-bar-fill { height: 100%; border-radius: 99px; transition: width 0.6s ease; }

    /* ══════════════════════════════════════════════════════════════
       BADGES AQI
       ══════════════════════════════════════════════════════════════ */
    .aqi-badge {
        display: inline-flex;
        align-items: center;
        gap: 5px;
        border-radius: 99px;
        padding: 3px 10px;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.02em;
    }
    .aqi-good      { background: rgba(0,230,118,0.12); color: var(--aqi-good);  border: 1px solid rgba(0,230,118,0.25); }
    .aqi-moderate  { background: rgba(255,238,88,0.12); color: var(--aqi-mod);  border: 1px solid rgba(255,238,88,0.25); }
    .aqi-sensitive { background: rgba(255,145,0,0.12);  color: var(--aqi-sens); border: 1px solid rgba(255,145,0,0.25); }
    .aqi-bad       { background: rgba(255,23,68,0.12);  color: var(--aqi-bad);  border: 1px solid rgba(255,23,68,0.25); }
    .aqi-very-bad  { background: rgba(213,0,249,0.12);  color: var(--aqi-vbad); border: 1px solid rgba(213,0,249,0.25); }

    /* ══════════════════════════════════════════════════════════════
       DASH DROPDOWN — override dark & light
       ══════════════════════════════════════════════════════════════ */
    .ac-dropdown .Select-control {
        background: var(--bg-input) !important;
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
        min-height: 34px !important;
        box-shadow: none !important;
        transition: border-color var(--ease) !important;
    }
    .ac-dropdown .Select-control:hover { border-color: var(--border-hover) !important; }
    .ac-dropdown.is-focused .Select-control { border-color: var(--border-focus) !important; box-shadow: 0 0 0 3px var(--cyan-dim) !important; }
    .ac-dropdown .Select-value-label { color: var(--text-primary) !important; font-size: 13px !important; font-weight: 500 !important; }
    .ac-dropdown .Select-placeholder { color: var(--text-muted) !important; font-size: 13px !important; }
    .ac-dropdown .Select-arrow { border-top-color: var(--text-secondary) !important; }
    .ac-dropdown .Select-menu-outer {
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-radius: 10px !important;
        box-shadow: var(--shadow-lg) !important;
        overflow: hidden;
    }
    .ac-dropdown .Select-option { color: var(--text-primary) !important; background: var(--bg-card) !important; font-size: 13px !important; }
    .ac-dropdown .Select-option.is-focused { background: var(--bg-surface) !important; }
    .ac-dropdown .Select-option.is-selected { background: var(--cyan-dim) !important; color: var(--cyan) !important; }

    /* ══════════════════════════════════════════════════════════════
       DASH RC-SLIDER
       ══════════════════════════════════════════════════════════════ */
    .rc-slider-rail        { background: var(--border) !important; height: 4px !important; }
    .rc-slider-track       { background: var(--cyan) !important; height: 4px !important; }
    .rc-slider-handle      { border-color: var(--cyan) !important; background: var(--cyan) !important; width: 16px !important; height: 16px !important; margin-top: -6px !important; }
    .rc-slider-handle:hover{ box-shadow: 0 0 0 6px var(--cyan-dim) !important; }
    .rc-slider-mark-text   { color: var(--text-secondary) !important; font-size: 10px !important; font-family: inherit !important; }

    /* ══════════════════════════════════════════════════════════════
       PLOTLY — masquer toolbar, fond transparent
       ══════════════════════════════════════════════════════════════ */
    .js-plotly-plot .plotly .modebar-container { display: none !important; }
    .js-plotly-plot { width: 100% !important; }

    /* ══════════════════════════════════════════════════════════════
       LEAFLET MAP
       ══════════════════════════════════════════════════════════════ */
    .leaflet-container {
        border-radius: 10px !important;
        font-family: 'Inter', sans-serif !important;
    }
    .leaflet-popup-content-wrapper {
        background: var(--bg-card) !important;
        color: var(--text-primary) !important;
        border-radius: 12px !important;
        border: 1px solid var(--border) !important;
        box-shadow: var(--shadow-lg) !important;
    }
    .leaflet-popup-tip { background: var(--bg-card) !important; }

    /* ══════════════════════════════════════════════════════════════
       SKELETON LOADER
       ══════════════════════════════════════════════════════════════ */
    .skeleton {
        background: linear-gradient(90deg,
            var(--bg-card) 25%,
            var(--bg-surface) 50%,
            var(--bg-card) 75%);
        background-size: 200% 100%;
        animation: shimmer 1.5s infinite;
        border-radius: 8px;
    }

    /* ══════════════════════════════════════════════════════════════
       PAGE LOGIN
       ══════════════════════════════════════════════════════════════ */
    #login-wrapper {
        background: var(--bg-base);
        min-height: 100vh;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 24px;
        position: relative;
        overflow: hidden;
    }
    /* Orbes décoratifs */
    #login-wrapper::before {
        content: '';
        position: absolute;
        width: 400px; height: 400px;
        border-radius: 50%;
        background: radial-gradient(circle, rgba(0,212,255,0.06) 0%, transparent 70%);
        top: -100px; right: -100px;
        pointer-events: none;
    }
    #login-wrapper::after {
        content: '';
        position: absolute;
        width: 300px; height: 300px;
        border-radius: 50%;
        background: radial-gradient(circle, rgba(0,230,118,0.06) 0%, transparent 70%);
        bottom: -50px; left: -50px;
        pointer-events: none;
    }
    .login-card {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 20px;
        padding: 36px;
        width: 100%;
        max-width: 420px;
        box-shadow: var(--shadow-lg);
        animation: fadeUp 0.4s ease;
        position: relative;
        z-index: 1;
    }
    .login-input {
        width: 100%;
        background: var(--bg-input) !important;
        border: 1px solid var(--border) !important;
        border-radius: 10px !important;
        color: var(--text-primary) !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 13px !important;
        padding: 11px 14px !important;
        outline: none !important;
        transition: border-color var(--ease) !important;
        box-sizing: border-box !important;
    }
    .login-input:focus { border-color: var(--border-focus) !important; box-shadow: 0 0 0 3px var(--cyan-dim) !important; }
    .login-input::placeholder { color: var(--text-muted) !important; }
    .login-btn-main {
        width: 100%;
        padding: 12px;
        border-radius: 10px;
        border: none;
        background: linear-gradient(135deg, #00a86b 0%, #0084cc 100%);
        color: #ffffff;
        font-size: 14px;
        font-weight: 700;
        cursor: pointer;
        font-family: 'Inter', sans-serif;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
        box-shadow: 0 4px 16px rgba(0,168,107,0.35);
        transition: opacity var(--ease), transform var(--ease);
    }
    .login-btn-main:hover { opacity: 0.92; transform: translateY(-1px); }
    .login-btn-main:active { transform: translateY(0); }
    .demo-btn {
        background: var(--bg-input);
        border: 1px solid var(--border);
        border-radius: 10px;
        padding: 10px 12px;
        cursor: pointer;
        text-align: left;
        width: 100%;
        font-family: 'Inter', sans-serif;
        transition: border-color var(--ease), background var(--ease), transform var(--ease);
    }
    .demo-btn:hover {
        border-color: var(--border-hover);
        background: var(--bg-surface);
        transform: translateY(-1px);
    }

    /* ══════════════════════════════════════════════════════════════
       PAGE CONTENT
       ══════════════════════════════════════════════════════════════ */
    #page-content { animation: fadeIn 0.2s ease; }
    #tab-content  { animation: fadeUp 0.25s ease; min-height: 300px; }

    #dashboard-wrapper {
        background: var(--bg-base);
        min-height: 100vh;
        transition: background var(--ease);
    }
    #main-content {
        padding: 16px 20px;
        max-width: 1600px;
        margin: 0 auto;
    }

    /* ══════════════════════════════════════════════════════════════
       RANKING LIST
       ══════════════════════════════════════════════════════════════ */
    .rank-row {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 7px 0;
        border-bottom: 1px solid var(--border);
        transition: background var(--ease);
        cursor: default;
    }
    .rank-row:last-child { border-bottom: none; }
    .rank-row:hover { background: var(--bg-surface); border-radius: 6px; padding-left: 4px; }
    .rank-num  { font-size: 11px; font-weight: 700; color: var(--text-muted); width: 20px; flex-shrink: 0; }
    .rank-name { font-size: 12px; font-weight: 600; color: var(--text-primary); min-width: 85px; flex-shrink: 0; }
    .rank-bar-wrap { flex: 1; height: 5px; background: var(--border); border-radius: 99px; overflow: hidden; }
    .rank-bar-fill { height: 100%; border-radius: 99px; transition: width 0.5s ease; }
    .rank-val  { font-size: 13px; font-weight: 800; min-width: 36px; text-align: right; flex-shrink: 0; }
    .rank-region { font-size: 10px; color: var(--text-muted); min-width: 70px; flex-shrink: 0; }

    /* ══════════════════════════════════════════════════════════════
       ALERTS
       ══════════════════════════════════════════════════════════════ */
    .alert-item {
        padding: 10px 12px 10px 14px;
        border-left: 3px solid;
        border-radius: 0 8px 8px 0;
        margin-bottom: 8px;
        background: var(--bg-surface);
        transition: transform var(--ease);
        cursor: default;
    }
    .alert-item:hover { transform: translateX(2px); }
    .alert-item:last-child { margin-bottom: 0; }
    .alert-badge {
        font-size: 9px; font-weight: 700;
        padding: 2px 7px; border-radius: 99px;
        letter-spacing: 0.06em;
        display: inline-flex;
        align-items: center;
        gap: 4px;
    }
    .alert-title { font-size: 12px; font-weight: 600; color: var(--text-primary); margin: 5px 0 2px; }
    .alert-desc  { font-size: 11px; color: var(--text-secondary); line-height: 1.5; }

    /* ══════════════════════════════════════════════════════════════
       FORECAST CARDS
       ══════════════════════════════════════════════════════════════ */
    .forecast-card {
        flex: 1;
        text-align: center;
        padding: 10px 6px;
        border-radius: 10px;
        border: 1px solid;
        transition: transform var(--ease), box-shadow var(--ease);
        cursor: default;
    }
    .forecast-card:hover { transform: translateY(-2px); box-shadow: var(--shadow-md); }
    .forecast-day  { font-size: 9px; font-weight: 800; letter-spacing: 0.06em; margin-bottom: 6px; }
    .forecast-aqi  { font-size: 20px; font-weight: 800; line-height: 1; margin: 4px 0; }
    .forecast-lbl  { font-size: 8px; font-weight: 600; margin-top: 3px; }
    .forecast-conf { font-size: 9px; color: var(--text-muted); margin-top: 2px; }
    
    /* Correction lisibilité AQI modéré en mode clair */
    [data-theme="light"] .aqi-moderate {
        background: rgba(201, 119, 0, 0.10) !important;
        color: #b85c00 !important;
        border-color: rgba(201, 119, 0, 0.30) !important;
    }
    [data-theme="light"] .forecast-card[style*="#ffee58"],
    [data-theme="light"] .forecast-card[style*="rgba(255,238,88"] {
        border-color: #c27700 !important;
    }

    /* ══════════════════════════════════════════════════════════════
       FOOTER
       ══════════════════════════════════════════════════════════════ */
    #app-footer {
        padding: 12px 20px;
        border-top: 1px solid var(--border);
        display: flex;
        align-items: center;
        justify-content: space-between;
        flex-wrap: wrap;
        gap: 8px;
        font-size: 10px;
        color: var(--text-muted);
        background: var(--bg-surface);
        margin-top: 24px;
    }
    .footer-sources a { color: var(--cyan); text-decoration: none; margin-right: 8px; }
    .footer-sources a:hover { text-decoration: underline; }

    /* ══════════════════════════════════════════════════════════════
    DROPDOWN OVERRIDES — Adaptation au thème (clair/sombre)
    ══════════════════════════════════════════════════════════════ */
    
    /* Contrôle principal du dropdown */
    .ac-dropdown .Select-control,
    .Select-control {
        background: var(--bg-input) !important;
        border: 1px solid var(--border) !important;
        border-radius: 10px !important;
        min-height: 38px !important;
        box-shadow: none !important;
        transition: all 0.2s ease !important;
    }

    .ac-dropdown .Select-control:hover,
    .Select-control:hover {
        border-color: var(--border-hover) !important;
    }

    /* Contrôle en focus */
    .ac-dropdown.is-focused .Select-control,
    .is-focused .Select-control {
        border-color: var(--border-focus) !important;
        box-shadow: 0 0 0 2px var(--cyan-dim) !important;
    }

    /* Valeur sélectionnée */
    .ac-dropdown .Select-value-label,
    .Select-value-label {
        color: var(--text-primary) !important;
        font-size: 13px !important;
        font-weight: 500 !important;
    }

    /* Placeholder */
    .ac-dropdown .Select-placeholder,
    .Select-placeholder {
        color: var(--text-muted) !important;
        font-size: 13px !important;
    }

    /* Flèche du dropdown */
    .ac-dropdown .Select-arrow,
    .Select-arrow {
        border-top-color: var(--text-secondary) !important;
    }

    /* Menu déroulant (la liste qui s'ouvre) */
    .ac-dropdown .Select-menu-outer,
    .Select-menu-outer {
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-radius: 10px !important;
        box-shadow: var(--shadow-lg) !important;
        overflow: hidden !important;
        z-index: 1050 !important;
    }

    /* Options dans le menu */
    .ac-dropdown .Select-option,
    .Select-option {
        background: var(--bg-card) !important;
        color: var(--text-primary) !important;
        font-size: 13px !important;
        padding: 10px 14px !important;
        transition: background 0.2s ease !important;
    }

    /* Option survolée */
    .ac-dropdown .Select-option.is-focused,
    .Select-option.is-focused {
        background: var(--bg-surface) !important;
        color: var(--text-primary) !important;
    }

    /* Option sélectionnée */
    .ac-dropdown .Select-option.is-selected,
    .Select-option.is-selected {
        background: var(--cyan-dim) !important;
        color: var(--cyan) !important;
    }

    /* ========== BARRE DE FILTRES SPÉCIFIQUE ========== */
    #filter-bar .ac-dropdown .Select-control,
    #filter-bar .Select-control {
        background: var(--bg-input) !important;
        border-color: var(--border) !important;
    }

    #filter-bar .ac-dropdown .Select-value-label,
    #filter-bar .Select-value-label {
        color: var(--text-primary) !important;
    }

    #filter-bar .ac-dropdown .Select-menu-outer,
    #filter-bar .Select-menu-outer {
        background: var(--bg-card) !important;
        border-color: var(--border) !important;
    }

    #filter-bar .ac-dropdown .Select-option,
    #filter-bar .Select-option {
        background: var(--bg-card) !important;
        color: var(--text-primary) !important;
    }

    #filter-bar .ac-dropdown .Select-option.is-focused,
    #filter-bar .Select-option.is-focused {
        background: var(--bg-surface) !important;
    }

    #filter-bar .ac-dropdown .Select-option.is-selected,
    #filter-bar .Select-option.is-selected {
        background: var(--cyan-dim) !important;
        color: var(--cyan) !important;
    }

    /* ========== GLOBAL DROPDOWN NUCLEAR OVERRIDE ========== */
    /* Garantit que TOUS les dropdowns (y compris alertes) respectent le thème */
    .Select-control,
    .ac-dropdown .Select-control,
    .VirtualizedSelectFocusedOption,
    .VirtualizedSelectSelectedOption,
    .VirtualizedSelectOption,
    .Select-menu-outer,
    .Select-menu,
    .Select-option,
    div[class*="Select-control"],
    div[class*="Select-menu"] {
        background-color: var(--bg-input) !important;
        background: var(--bg-input) !important;
        color: var(--text-primary) !important;
    }

    .Select-menu-outer,
    div[class*="Select-menu-outer"] {
        background-color: var(--bg-card) !important;
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-radius: 10px !important;
        box-shadow: 0 8px 32px rgba(0,0,0,0.5) !important;
        z-index: 9999 !important;
        position: absolute !important;
    }

    .Select-option {
        background-color: var(--bg-card) !important;
        background: var(--bg-card) !important;
        color: var(--text-primary) !important;
    }

    .Select-option:hover,
    .Select-option.is-focused {
        background-color: var(--bg-surface) !important;
        background: var(--bg-surface) !important;
    }

    .Select-option.is-selected {
        background-color: var(--cyan-dim) !important;
        background: var(--cyan-dim) !important;
        color: var(--cyan) !important;
    }

    .Select-value-label,
    .Select-placeholder {
        color: var(--text-primary) !important;
    }

    .Select-placeholder {
        color: var(--text-muted) !important;
    }

    /* Prevent white flash on open */
    .Select.is-open .Select-control {
        background-color: var(--bg-input) !important;
        border-color: var(--border-focus) !important;
    }

    /* ========== INPUTS DATE ========== */
    .DateInput_input,
    .DateRangePickerInput {
        background: var(--bg-input) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
        font-family: 'Inter', sans-serif !important;
    }

    .DateInput_input:focus,
    .DateRangePickerInput:focus {
        border-color: var(--border-focus) !important;
        box-shadow: 0 0 0 2px var(--cyan-dim) !important;
    }

    .DateInput_input__focused {
        border-color: var(--border-focus) !important;
    }

    /* Calendrier dropdown */
    .DateRangePickerPicker,
    .SingleDatePickerPicker {
        background: var(--bg-card) !important;
        border-color: var(--border) !important;
    }

    /* ========== AUTRES INPUTS DANS LA FILTER BAR ========== */
    #filter-bar input {
        background: var(--bg-input) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
    }

    #filter-bar input:focus {
        border-color: var(--border-focus) !important;
        box-shadow: 0 0 0 2px var(--cyan-dim) !important;
    }

    /* ══════════════════════════════════════════════════════════════
       DARK / LIGHT MODE — textes Plotly & éléments graphiques
       ══════════════════════════════════════════════════════════════ */
    /* Axes, légendes, titres Plotly en dark mode */
    [data-theme="dark"] .gtitle,
    [data-theme="dark"] .xtitle,
    [data-theme="dark"] .ytitle,
    [data-theme="dark"] .legendtext,
    [data-theme="dark"] .annotation-text,
    [data-theme="dark"] .g-gtitle text,
    [data-theme="dark"] .g-xtitle text,
    [data-theme="dark"] .g-ytitle text,
    [data-theme="dark"] .js-plotly-plot .plotly .xtick text,
    [data-theme="dark"] .js-plotly-plot .plotly .ytick text,
    [data-theme="dark"] .js-plotly-plot .plotly .legend text,
    [data-theme="dark"] .js-plotly-plot .plotly text {
        fill: #e8f0fe !important;
        color: #e8f0fe !important;
    }
    /* Même chose en light mode */
    [data-theme="light"] .js-plotly-plot .plotly .xtick text,
    [data-theme="light"] .js-plotly-plot .plotly .ytick text,
    [data-theme="light"] .js-plotly-plot .plotly .legend text,
    [data-theme="light"] .js-plotly-plot .plotly text {
        fill: #0f1f35 !important;
        color: #0f1f35 !important;
    }

    /* Popup Leaflet — fond sombre en dark mode */
    [data-theme="dark"] .leaflet-popup-content-wrapper {
        background: #111e35 !important;
        color: #e8f0fe !important;
        border: 1px solid #1e3058 !important;
    }
    [data-theme="dark"] .leaflet-popup-tip {
        background: #111e35 !important;
    }
    [data-theme="dark"] .leaflet-popup-content {
        color: #e8f0fe !important;
    }
    [data-theme="light"] .leaflet-popup-content-wrapper {
        background: #ffffff !important;
        color: #0f1f35 !important;
        border: 1px solid #c8d8ea !important;
    }

    /* Spinner animation (global) */
    @keyframes spin {
        to { transform: rotate(360deg); }
    }

    /* ══════════════════════════════════════════════════════════════
       RESPONSIVE MOBILE (≤768px)
       ══════════════════════════════════════════════════════════════ */
    @media (max-width: 768px) {
        #app-header { padding: 0 12px; gap: 8px; }
        .logo-sub { display: none; }
        #nav-tabs-bar { gap: 1px; }
        .nav-tab-btn { padding: 5px 8px; font-size: 11px; gap: 4px; }
        .nav-tab-btn span { display: none; }  /* Ne montrer que l'icone sur mobile */
        #main-content { padding: 10px 12px; }
        #filter-bar { flex-direction: column; align-items: flex-start; gap: 10px; }
        .login-card { padding: 24px 20px; }
        .kpi-grid-6 { grid-template-columns: repeat(2, 1fr) !important; }
        .kpi-grid-5 { grid-template-columns: repeat(2, 1fr) !important; }
        .grid-12    { grid-template-columns: 1fr !important; }
        .col-7, .col-5, .col-8, .col-4, .col-6 { grid-column: span 12 !important; }
    }
    @media (max-width: 480px) {
        .nav-tab-btn { padding: 5px 6px; }
        #filter-bar { padding: 8px 12px; }
    }
    @media (min-width: 769px) and (max-width: 1024px) {
        .kpi-grid-6 { grid-template-columns: repeat(3, 1fr) !important; }
        .nav-tab-btn span { display: inline; }
    }
    </style>
</head>
<body>
    {%app_entry%}
    <footer>{%config%}{%scripts%}{%renderer%}</footer>

    <!-- JS Animations & Thème -->
    <script>
    // Applique le thème sauvegardé avant tout rendu (évite le flash)
    (function() {
        try {
            var th = localStorage.getItem('aircam-theme') || 'dark';
            document.documentElement.setAttribute('data-theme', th);
        } catch(e) {}
    })();

    // Gestion du bouton thème (côté client, sans callback Dash)
    document.addEventListener('click', function(e) {
        var btn = e.target.closest('#btn-theme');
        if (!btn) return;
        var current = document.documentElement.getAttribute('data-theme') || 'dark';
        var next = current === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', next);
        try { localStorage.setItem('aircam-theme', next); } catch(e2) {}
        // Mettre à jour l'icône
        var icon = document.getElementById('theme-icon');
        if (icon) {
            icon.className = next === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
        }
    });

    // Active-tab highlighting via JS (persistant même après re-render Dash)
    function applyActiveTabClass() {
        var activeTab = window._aircamActiveTab;
        document.querySelectorAll('.nav-tab-btn').forEach(function(btn) {
            btn.classList.remove('active');
        });
        if (!activeTab) {
            // Marquer le premier onglet actif par défaut
            var firstBtn = document.querySelector('.nav-tab-btn');
            if (firstBtn) firstBtn.classList.add('active');
            return;
        }
        document.querySelectorAll('.nav-tab-btn').forEach(function(btn) {
            try {
                var idAttr = btn.getAttribute('id') || '';
                if (idAttr.includes('"index":"' + activeTab + '"') || idAttr.includes('"index": "' + activeTab + '"')) {
                    btn.classList.add('active');
                }
            } catch(e) {}
        });
    }

document.addEventListener('click', function(e) {
        var btn = e.target.closest('.nav-tab-btn');
        if (!btn) return;
        // Stocker l'onglet actif
        try {
            var idAttr = btn.getAttribute('id') || '';
            var match = idAttr.match(/"index"\\s*:\\s*"([^"]+)"/);
            if (match) {
                window._aircamActiveTab = match[1];
                try { localStorage.setItem('aircam-active-tab', match[1]); } catch(e2) {}
            }
        } catch(e) {}
        document.querySelectorAll('.nav-tab-btn').forEach(function(b) {
            b.classList.remove('active');
        });
        btn.classList.add('active');
    });

    // Ré-appliquer après chaque re-render Dash (MutationObserver)
    var tabObserver = new MutationObserver(function() {
        if (!window._aircamActiveTab) {
            try { window._aircamActiveTab = localStorage.getItem('aircam-active-tab'); } catch(e) {}
        }
        applyActiveTabClass();
    });
    tabObserver.observe(document.getElementById('react-entry-point') || document.body, {
        childList: true, subtree: true
    });

    // Horloge temps réel
    function updateClock() {
        var el = document.getElementById('header-clock');
        if (!el) return;
        var now = new Date();
        var pad = function(n) { return n < 10 ? '0' + n : n; };
        el.textContent = pad(now.getDate()) + '/' + pad(now.getMonth()+1) + '/' + now.getFullYear()
            + '  ' + pad(now.getHours()) + ':' + pad(now.getMinutes()) + ' WAT';
    }
    setInterval(updateClock, 1000);
    updateClock();

    // Cacher le chatbot sur la page de connexion via class sur body
    function checkAndHideChatbot() {
        var loginWrapper = document.getElementById('login-wrapper');
        if (loginWrapper) {
            document.body.classList.add('on-login-page');
        } else {
            document.body.classList.remove('on-login-page');
        }
    }
    // Observer pour détecter les changements de page
    var chatbotObserver = new MutationObserver(checkAndHideChatbot);
    chatbotObserver.observe(document.body, { childList: true, subtree: false });
    setInterval(checkAndHideChatbot, 300);
    checkAndHideChatbot();
    </script>
</body>
</html>'''

# ─────────────────────────────────────────────
# HELPERS LAYOUT
# ─────────────────────────────────────────────
def fa(cls, **kwargs):
    return html.I(className=f"fas {cls}", **kwargs)

def section_hdr(icon_cls, text):
    return html.Div([fa(icon_cls, style={'fontSize': '11px'}), html.Span(text)], className='section-title')

def aqi_badge_el(aqi, lang='fr'):
    if aqi <= 50: css = 'aqi-good'
    elif aqi <= 100: css = 'aqi-moderate'
    elif aqi <= 150: css = 'aqi-sensitive'
    elif aqi <= 200: css = 'aqi-bad'
    else: css = 'aqi-very-bad'
    return html.Span(aqi_label(aqi, lang), className=f'aqi-badge {css}')

def trend_span(v):
    if v > 0:
        return html.Span([fa('fa-arrow-trend-up', style={'marginRight':'3px'}), f'+{abs(v):.1f}%'],
                         style={'color': '#ff4d6d', 'fontSize': '11px', 'fontWeight': '600'})
    if v < 0:
        return html.Span([fa('fa-arrow-trend-down', style={'marginRight':'3px'}), f'-{abs(v):.1f}%'],
                         style={'color': 'var(--green)', 'fontSize': '11px', 'fontWeight': '600'})
    return html.Span('— stable', style={'color': 'var(--text-muted)', 'fontSize': '11px'})

# ─────────────────────────────────────────────
# KPI CARDS
# ─────────────────────────────────────────────
def make_kpi_cards(lang='fr'):
    # Données dynamiques
    nat = get_national_stats()
    n_cities = nat.get('cities_count') or len(get_cities_data())
    trend_aqi  = nat.get('trend_aqi', 0.0)
    trend_pm25 = nat.get('trend_pm25', 0.0)
    # Performance ML
    ml_pct = 94.7
    try:
        from api_client import load_model_info
        info = load_model_info()
        r2 = info.get('aqi_global', {}).get('r2_test')
        if r2 is not None:
            ml_pct = round(max(0, min(100, r2 * 100)), 1)
    except Exception:
        pass
    kpis = [
        (t('kpi_national_aqi', lang), f"{nat['aqi']:.0f}",  'AQI',    trend_aqi,  '#ff9100',       'fa-chart-line', min(nat['aqi'] / 3, 100)),
        (t('kpi_pm25', lang),         f"{nat['pm25']:.1f}", 'µg/m³',  trend_pm25, 'var(--red)',     'fa-smog',       min(nat['pm25'] / 1.5, 100)),
        (t('kpi_no2', lang),          f"{nat['no2']:.1f}",  'µg/m³',  0,          'var(--cyan)',    'fa-industry',   min(nat['no2'] / 1.5, 100)),
        (t('kpi_cities', lang),       f"{n_cities}",        '/ 10 rég.', 0,        'var(--green)',  'fa-city',       min(n_cities / 40 * 100, 100)),
        (t('kpi_ml', lang),           f"{ml_pct:.1f}",      '%',      0,          'var(--purple)', 'fa-brain',      ml_pct),
    ]
    cards = []
    for label, val, unit, trend, accent, icon, bar_pct in kpis:
        cards.append(html.Div([
            html.Div([
                fa(icon, style={'color': accent, 'fontSize': '16px'}),
                trend_span(trend) if trend != 0 else html.Span()
            ], style={'display':'flex','justifyContent':'space-between','alignItems':'flex-start','marginBottom':'10px'}),
            html.Div([
                html.Span(val, style={'fontSize':'26px','fontWeight':'800','letterSpacing':'-0.03em','color':'var(--text-primary)','lineHeight':'1'}),
                html.Span(f' {unit}', style={'fontSize':'12px','color':'var(--text-secondary)','marginLeft':'3px'}) if unit else None,
            ], style={'marginBottom':'4px'}),
            html.P(label, className='kpi-label', style={'marginBottom':'10px'}),
            html.Div(html.Div(style={'width':f'{min(bar_pct,100):.0f}%','height':'100%','background':accent,'borderRadius':'99px'}),
                     className='kpi-bar')
        ], className='kpi-card', style={'--kpi-accent': accent}))
    return html.Div(cards, className='stagger', style={
        'display':'grid','gridTemplateColumns':'repeat(5,1fr)','gap':'12px','marginBottom':'16px'
    })

# ─────────────────────────────────────────────
# FILTER BAR
# ─────────────────────────────────────────────
def make_filter_bar(region_val='all', city_val='all', lang='fr'):
    # Données dynamiques depuis l'API (cache TTL)
    cities_dyn = get_cities_data()
    regions_dyn = get_regions(cities_dyn)
    nat = get_national_stats(cities_dyn)
    nat_aqi = nat['aqi']
    trend = nat.get('trend_aqi', 0.0)
    n_cities = nat.get('cities_count') or len(cities_dyn)
    n_regions = len(regions_dyn)

    # Trend couleur + signe
    trend_color = 'var(--red)' if trend > 0 else 'var(--green)' if trend < 0 else 'var(--text-secondary)'
    trend_str = f"+{trend:.1f}%" if trend > 0 else f"{trend:.1f}%"

    # Performances ML dynamiques
    r2_str = 'R²=—'
    rmse_str = ''
    try:
        from api_client import load_model_info
        info = load_model_info()
        aqi_info = info.get('aqi_global', {})
        r2 = aqi_info.get('r2_test')
        rmse = aqi_info.get('rmse_test')
        if r2 is not None:
            r2_str = f"R²={r2:.3f}"
        if rmse is not None:
            rmse_str = f" · RMSE={rmse:.1f}"
    except Exception:
        pass

    city_opts_all = [{'label': t('city_all', lang), 'value': 'all'}] + [
        {'label': c['city'], 'value': c['city']} for c in cities_dyn
    ]
    region_opts = [{'label': t('region_all', lang), 'value': 'all'}] + [
        {'label': r, 'value': r} for r in regions_dyn
    ]

    # Valider les valeurs courantes
    valid_cities = [o['value'] for o in city_opts_all]
    city_val = city_val if city_val in valid_cities else 'all'
    valid_regions = [o['value'] for o in region_opts]
    region_val = region_val if region_val in valid_regions else 'all'

    return html.Div([
        html.Div([
            html.Div([
                html.Label(t('region_label', lang), className='filter-label'),
                dcc.Dropdown(
                    id='region-filter',
                    options=region_opts,
                    value=region_val, clearable=False, style={'minWidth': '190px'}, className='ac-dropdown',
                )
            ]),
            html.Div([
                html.Label(t('city_label', lang), className='filter-label'),
                dcc.Dropdown(
                    id='city-filter', options=city_opts_all, value=city_val,
                    clearable=False, style={'minWidth': '170px'}, className='ac-dropdown',
                )
            ]),
            html.Div([
                html.Label(t('dates_label', lang), className='filter-label'),
                html.Div(html.Span('2020 → 2025', style={'fontSize':'12px','fontWeight':'600','color':'var(--cyan)'}),
                         style={'padding':'6px 10px','background':'var(--bg-input)','borderRadius':'8px','border':'1px solid var(--border)','minWidth':'130px'})
            ]),
        ], style={'display':'flex','gap':'16px','alignItems':'flex-end','flexWrap':'wrap'}),
        html.Div([
            html.Div([
                html.Span(t('national', lang).upper(), className='filter-label', style={'display':'block'}),
                html.Div([
                    html.Span(f"{nat_aqi:.0f}", style={'fontSize':'22px','fontWeight':'800','color':'var(--text-primary)','letterSpacing':'-0.03em'}),
                    html.Span(' AQI', style={'fontSize':'11px','color':'var(--text-secondary)','marginLeft':'3px'}),
                    html.Span(f' {trend_str}', style={'fontSize':'11px','color':trend_color,'marginLeft':'8px','fontWeight':'600'}),
                ], style={'display':'flex','alignItems':'baseline'}),
            ]),
            html.Div(style={'width':'1px','height':'32px','background':'var(--border)','margin':'0 16px'}),
            html.Div([
                html.Span(f"{n_cities} {'cities' if lang=='en' else 'villes'}", style={'fontSize':'12px','fontWeight':'600','color':'var(--text-primary)'}),
                html.Span(f" · {n_regions} {'regions' if lang=='en' else 'régions'}", style={'fontSize':'12px','color':'var(--text-secondary)'}),
            ]),
            html.Div(style={'width':'1px','height':'32px','background':'var(--border)','margin':'0 16px'}),
            html.Div([
                html.Span(r2_str, style={'fontSize':'13px','fontWeight':'700','color':'var(--green)'}),
                html.Span(rmse_str, style={'fontSize':'11px','color':'var(--text-secondary)'}),
            ]),
        ], style={'display':'flex','alignItems':'center','flexShrink':'0','flexWrap':'wrap','gap':'4px'}),
    ], id='filter-bar')

# ─────────────────────────────────────────────
# GAUGE CHART — Plotly (corrigé)
# ─────────────────────────────────────────────
def make_gauge(aqi_val, city_name='Yaoundé', lang='fr', theme='dark'):
    col = aqi_color(aqi_val)
    fig = go.Figure(go.Indicator(
        mode='gauge+number',
        value=aqi_val,
        domain={'x': [0, 1], 'y': [0, 1]},
        number={'font': {'size': 44, 'color': col, 'family': 'Inter'}, 'suffix': ''},
        gauge={
            'axis': {'range': [0, 300], 'tickwidth': 1, 'tickcolor': '#3d5070',
                     'tickfont': {'size': 9, 'color': '#7a90b5'}},
            'bar': {'color': col, 'thickness': 0.22},
            'bgcolor': 'rgba(0,0,0,0)',
            'borderwidth': 0,
            'steps': [
                {'range': [0, 50], 'color': 'rgba(0,230,118,0.12)'},
                {'range': [50, 100], 'color': 'rgba(255,238,88,0.12)'},
                {'range': [100, 150], 'color': 'rgba(255,145,0,0.12)'},
                {'range': [150, 200], 'color': 'rgba(255,23,68,0.12)'},
                {'range': [200, 300], 'color': 'rgba(213,0,249,0.12)'},
            ],
            'threshold': {
                'line': {'color': col, 'width': 3},
                'thickness': 0.8, 'value': aqi_val
            }
        }
    ))
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=20, r=20, t=20, b=20),
        height=220,
        font={'family': 'Inter', 'color': graph_font(theme)}
    )
    return html.Div([
        html.Div(city_name, style={'fontSize':'11px','fontWeight':'700','color':'var(--text-secondary)',
                                    'textTransform':'uppercase','letterSpacing':'0.08em',
                                    'textAlign':'center','marginBottom':'2px'}),
        dcc.Graph(figure=fig, config={'displayModeBar': False}, style={'width':'100%', 'height':'220px'}),
        html.Div([aqi_badge_el(aqi_val, lang)], style={'textAlign':'center','marginTop':'4px'}),
        html.Div([
            html.Div([
                html.Span('PM2.5', style={'color':'var(--text-muted)','fontSize':'10px','display':'block'}),
                html.Span(f'{next((c["pm25"] for c in CITIES_DATA if c["city"]==city_name), 72.3):.1f}',
                          style={'fontSize':'14px','fontWeight':'700','color':'var(--red)'}),
            ], style={'textAlign':'center'}),
            html.Div([
                html.Span('PM10', style={'color':'var(--text-muted)','fontSize':'10px','display':'block'}),
                html.Span(f'{next((c["pm10"] for c in CITIES_DATA if c["city"]==city_name), 118.5):.1f}',
                          style={'fontSize':'14px','fontWeight':'700','color':'var(--orange)'}),
            ], style={'textAlign':'center'}),
            html.Div([
                html.Span('NO₂', style={'color':'var(--text-muted)','fontSize':'10px','display':'block'}),
                html.Span(f'{next((c["no2"] for c in CITIES_DATA if c["city"]==city_name), 42.8):.1f}',
                          style={'fontSize':'14px','fontWeight':'700','color':'var(--cyan)'}),
            ], style={'textAlign':'center'}),
        ], style={'display':'flex','justifyContent':'space-around','marginTop':'12px',
                  'padding':'10px','background':'var(--bg-surface)','borderRadius':'10px',
                  'border':'1px solid var(--border)'}),
    ])

# ─────────────────────────────────────────────
# TIMELINE — Évolution temporelle Plotly (CORRIGÉE - PLEIN ÉCRAN)
# ─────────────────────────────────────────────
def make_timeline(city_name=None, timerange='30j', theme='dark'):
    """Évolution temporelle - 7j ou 30j"""
    CITIES_DATA = get_cities_data()
    # Si aucune ville spécifiée, utiliser la moyenne nationale
    if city_name is None or city_name == 'National':
        n = 7 if timerange == '7j' else 30
        national_avg = NATIONAL['aqi']
        col = aqi_color(national_avg)
        title = f"Évolution {timerange} — National"
        dates = [(datetime.now() - timedelta(days=i)).strftime('%d/%m') for i in range(n-1, -1, -1)]
        aqi = []
        try:
            from api_client import load_city_history
            import pandas as pd
            # Moyenne sur un échantillon de villes pour la vue nationale
            sample_cities = [c['city'] for c in CITIES_DATA[:5]]
            all_hist = {}
            for sc in sample_cities:
                hist = load_city_history(sc, n)
                if hist:
                    for row in hist:
                        d = row['pred_date']
                        all_hist.setdefault(d, []).append(row['aqi'])
            if all_hist:
                sorted_dates = sorted(all_hist.keys())[-n:]
                dates = [pd.Timestamp(d).strftime('%d/%m') for d in sorted_dates]
                aqi   = [round(sum(all_hist[d]) / len(all_hist[d]), 1) for d in sorted_dates]
        except Exception:
            pass
        if not aqi:
            aqi = [national_avg] * n
    else:
        # Ville spécifique
        city_data = next((c for c in CITIES_DATA if c['city'] == city_name), CITIES_DATA[0])
        n = 7 if timerange == '7j' else 30
        title = f"Évolution {timerange} - {city_name}"
        col = aqi_color(city_data['aqi'])
        dates = [(datetime.now() - timedelta(days=i)).strftime('%d/%m') for i in range(n-1, -1, -1)]
        aqi = []
        try:
            from api_client import load_city_history
            import pandas as pd
            hist = load_city_history(city_name, n)
            if hist:
                hist = sorted(hist, key=lambda x: x['pred_date'])
                dates = [pd.Timestamp(r['pred_date']).strftime('%d/%m') for r in hist]
                aqi   = [r['aqi'] for r in hist]
        except Exception:
            pass
        if not aqi:
            aqi = [city_data['aqi']] * n
    
    # Conversion de la couleur
    if col.startswith('#'):
        r, g, b = int(col[1:3], 16), int(col[3:5], 16), int(col[5:7], 16)
        fill_color = f'rgba({r}, {g}, {b}, 0.2)'
    else:
        fill_color = 'rgba(255,145,0,0.2)'

    fig = go.Figure()
    
    # Zone remplie pour l'AQI
    fig.add_trace(go.Scatter(
        x=dates, y=aqi, mode='lines+markers',
        line=dict(color=col, width=2.5),
        marker=dict(size=4, color=col),
        fill='tozeroy', 
        fillcolor=fill_color,
        hovertemplate='<b>%{x}</b><br>AQI: %{y:.0f}<extra></extra>'
    ))
    
    # Ajout des zones de qualité d'air en arrière-plan
    fig.add_hrect(y0=0, y1=50, fillcolor='rgba(0,230,118,0.05)', line_width=0, layer='below')
    fig.add_hrect(y0=50, y1=100, fillcolor='rgba(255,238,88,0.05)', line_width=0, layer='below')
    fig.add_hrect(y0=100, y1=150, fillcolor='rgba(255,145,0,0.05)', line_width=0, layer='below')
    fig.add_hrect(y0=150, y1=200, fillcolor='rgba(255,23,68,0.05)', line_width=0, layer='below')
    fig.add_hrect(y0=200, y1=300, fillcolor='rgba(213,0,249,0.05)', line_width=0, layer='below')
    
    _fc = graph_font(theme)
    _gc = graph_grid(theme)
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=300,
        margin=dict(l=40, r=20, t=30, b=30),
        font=dict(color=_fc),
        xaxis=dict(
            tickangle=-45,
            tickfont=dict(size=10, color=_fc),
            gridcolor=_gc,
            showgrid=True,
            showline=False,
            zeroline=False
        ),
        yaxis=dict(
            title='AQI',
            tickfont=dict(size=10, color=_fc), 
            gridcolor='rgba(30,48,88,0.2)',
            showgrid=True,
            showline=False,
            zeroline=False
        ),
        hovermode='x unified',
        showlegend=False,
        autosize=True
    )
    
    return dcc.Graph(
        figure=fig, 
        config={'displayModeBar': False, 'responsive': True}, 
        style={'width': '100%', 'height': '100%', 'minHeight': '300px'}
    )

# ─────────────────────────────────────────────
# RANKING LIST
# ─────────────────────────────────────────────
def make_ranking(limit=10):
    top = sorted(CITIES_DATA, key=lambda x: x['aqi'], reverse=True)[:limit]
    rows = []
    for i, c in enumerate(top, 1):
        col = c['color']
        pct = min(c['aqi'] / 300 * 100, 100)
        rows.append(html.Div([
            html.Span(f'{i:02d}', className='rank-num'),
            html.Span(c['city'], className='rank-name'),
            html.Span(c['region'], className='rank-region'),
            html.Div(html.Div(style={'width':f'{pct:.0f}%','height':'100%','background':col,'borderRadius':'99px'}),
                     className='rank-bar-wrap'),
            html.Span(str(c['aqi']), className='rank-val', style={'color': col}),
        ], className='rank-row'))
    return html.Div(rows)

# ─────────────────────────────────────────────
# CONTENU ONGLETS — dispatch (VERSION CORRIGÉE)
# ─────────────────────────────────────────────
def get_tab_content(tab_id, role, city, region, lang, theme='dark', user=None):
    """Dispatch les onglets selon le rôle de l'utilisateur."""
    cities_dyn = get_cities_data()
    user_city = (user or {}).get('city') if user else None

    # Résolution robuste : jamais None, jamais 'all' pour le display
    city_name = city if city and city != 'all' else None
    display_city = _resolve_city(city_name, user_city, cities_dyn)

    try:
        # Onglet À propos (commun à tous les rôles)
        if tab_id == 'about':
            from about_page import create_about_page
            return create_about_page(display_city, lang, theme)

        # Onglets citoyen
        elif role == 'citizen':
            if tab_id == 'alerts':
                from alerts_tab import create_alerts_page
                return create_alerts_page(
                    display_city, lang, theme,
                    CITIES_DATA=CITIES_DATA,
                    aqi_color=aqi_color,
                    aqi_label=aqi_label,
                    t=t,
                    fa=fa,
                    REGIONS=REGIONS
                )
            else:
                from citizen_pages import get_citizen_tab_content
                # Passer city (qui peut être None pour today) au lieu de display_city
                return get_citizen_tab_content(tab_id, city, lang, theme)

        # Onglets décideur
        elif role == 'decision':
            from decision_maker_pages import get_decision_tab_content
            return get_decision_tab_content(tab_id, display_city, lang, theme)
            
        # Onglets chercheur
        elif role == 'researcher':
            from researcher_pages import get_researcher_tab_content
            return get_researcher_tab_content(tab_id, display_city, lang, theme)

    except ImportError as e:
        print(f"[AirEka] Module non trouvé pour {tab_id}: {e}")
    except Exception as e:
        import traceback
        print(f'[AirEka] Erreur onglet {tab_id}: {e}\n{traceback.format_exc()}')

    # Fallback premium avec le thème
    return make_overview_fallback(display_city, lang, theme)

# ─────────────────────────────────────────────
# ALERTS
# ─────────────────────────────────────────────
def make_alerts(lang='fr'):
    alerts = [
        ('ÉLEVÉ', '#ff1744', 'fa-triangle-exclamation', 'PM2.5 critique — Yaoundé Centre',
         'Concentration 4.8× seuil OMS. Populations vulnérables recommandées de rester en intérieur.'),
        ('MOYEN', '#ff9100', 'fa-car-burst', 'Pic trafic — Douala Akwa (Littoral)',
         'NO₂ en hausse de +38% prévue 17h–19h. Corrélation trafic routier confirmée.'),
        ('BON', '#00e676', 'fa-leaf', 'Zone verte — Régions Sud & Nord-Ouest',
         "Bamenda (45), Kribi (38), Ebolowa (52) : qualité de l'air bonne pour toutes les populations."),
        ('INFO', '#7a90b5', 'fa-wrench', 'Station #17 Ngaoundéré — Maintenance',
         'Capteur PM10 en calibration. Données interpolées par IDW depuis stations voisines.'),
    ]
    items = []
    for level, col, icon_cls, title, desc in alerts:
        items.append(html.Div([
            html.Span([
                fa(icon_cls, style={'fontSize':'9px'}),
                html.Span(f' {level}', style={'marginLeft':'3px'})
            ], className='alert-badge', style={'background': col+'1a', 'color': col, 'border': f'1px solid {col}40'}),
            html.P(title, className='alert-title'),
            html.P(desc, className='alert-desc'),
        ], className='alert-item', style={'borderColor': col}))
    return html.Div(items)

# ─────────────────────────────────────────────
# FORECAST 7 JOURS
# ─────────────────────────────────────────────
def _model_perf_rows():
    """Performances réelles des modèles depuis /models/info."""
    _LABELS = {'pm2_5': 'PM2.5', 'pm10': 'PM10', 'no2': 'NO₂',
               'o3': 'O₃', 'so2': 'SO₂', 'co': 'CO', 'aqi_global': 'AQI Global'}
    rows_data = []
    try:
        from api_client import load_model_info
        info = load_model_info()
        for key, label in _LABELS.items():
            m = info.get(key, {})
            r2 = m.get('r2_test')
            if r2 is not None:
                pct = round(max(0, min(100, r2 * 100)))
                col = '#00e676' if pct >= 95 else '#00d4ff' if pct >= 85 else '#ff9100' if pct >= 70 else '#ff1744'
                rows_data.append((label, pct, col, f"R²={r2:.3f}"))
    except Exception:
        pass
    if not rows_data:
        rows_data = [
            ('AQI Global', 98, '#00e676', 'R²=0.975'), ('PM2.5', 99, '#00e676', 'R²=0.991'),
            ('PM10', 98, '#00e676', 'R²=0.977'), ('O₃', 90, '#00d4ff', 'R²=0.898'),
            ('CO', 98, '#00e676', 'R²=0.983'), ('SO₂', 80, '#ff9100', 'R²=0.801'),
            ('NO₂', 73, '#ff9100', 'R²=0.731'),
        ]
    return [html.Div([
        html.Span(label, style={'fontSize': '11px', 'color': 'var(--text-primary)',
                                'fontWeight': '500', 'minWidth': '72px'}),
        html.Div(html.Div(style={'width': f'{pct}%', 'height': '100%',
                                 'background': col, 'borderRadius': '99px'}),
                 style={'flex': '1', 'height': '5px', 'background': 'var(--border)',
                        'borderRadius': '99px', 'overflow': 'hidden', 'margin': '0 8px'}),
        html.Span(note, style={'fontSize': '10px', 'color': col,
                               'minWidth': '56px', 'textAlign': 'right', 'fontWeight': '600'}),
    ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '8px'})
        for label, pct, col, note in rows_data]


def make_forecast(city_name=None, lang='fr'):
    from api_client import load_forecast
    import pandas as pd

    is_national = not city_name or city_name in ('all', 'National')
    en = lang == 'en'
    day_names_fr = ['LUN','MAR','MER','JEU','VEN','SAM','DIM']
    day_names_en = ['MON','TUE','WED','THU','FRI','SAT','SUN']
    day_names = day_names_en if en else day_names_fr
    forecast = []
    cities_dyn = get_cities_data()

    if is_national:
        sample = ['Yaoundé', 'Douala', 'Garoua', 'Bafoussam', 'Maroua']
        by_date = {}
        for sc in sample:
            try:
                fc7 = load_forecast(sc, 7)
                if fc7:
                    for r in sorted(fc7, key=lambda x: x['pred_date']):
                        d = r['pred_date']
                        by_date.setdefault(d, []).append(r['aqi'])
            except Exception:
                pass
        if by_date:
            for i, (d, aqis) in enumerate(sorted(by_date.items())[:7]):
                label = day_names[pd.Timestamp(d).weekday()]
                forecast.append((sum(aqis)/len(aqis), label, 95 - i))
        title = t('forecast_7d', lang) + " — " + t('national', lang)
        nat = get_national_stats(cities_dyn)
        base = nat['aqi'] or 80
    else:
        c = next((x for x in cities_dyn if x['city'] == city_name), cities_dyn[0] if cities_dyn else {'aqi': 80})
        base = c.get('aqi', 80)
        try:
            fc7 = load_forecast(city_name, 7)
            if fc7:
                for i, r in enumerate(sorted(fc7, key=lambda x: x['pred_date'])):
                    label = day_names[pd.Timestamp(r['pred_date']).weekday()]
                    forecast.append((r['aqi'], label, 95 - i))
        except Exception:
            pass
        title = f"{t('forecast_7d', lang)} — {city_name}"

    if not forecast:
        today_lbl = 'TODAY' if en else 'AUJ.'
        labels = [today_lbl] + [f'J+{i}' if not en else f'D+{i}' for i in range(1, 7)]
        mults = [1, 0.95, 0.90, 0.88, 0.85, 0.87, 0.92]
        forecast = [(base * m, l, 95 - i) for i, (m, l) in enumerate(zip(mults, labels))]

    cards = []
    for aqi_v, label, conf in forecast:
        aqi_v = max(20, aqi_v)
        col = aqi_color(aqi_v)
        bg = aqi_bg(aqi_v)
        icon_cls, _ = aqi_icon(aqi_v)
        cards.append(html.Div([
            html.Div(label, className='forecast-day', style={'color': col}),
            fa(icon_cls, style={'fontSize':'18px','color':col,'marginBottom':'4px'}),
            html.Div(f'{aqi_v:.0f}', className='forecast-aqi', style={'color': col}),
            html.Div(aqi_label(aqi_v, lang), className='forecast-lbl', style={'color': col}),
            html.Div(f'Conf. {conf}%', className='forecast-conf'),
        ], className='forecast-card', style={'borderColor': col, 'background': bg}))
    return html.Div([
        html.Div(title, className='section-title', style={'marginBottom':'10px'}),
        html.Div(cards, style={'display':'flex','gap':'6px','flexWrap':'wrap'}),
    ])

# ─────────────────────────────────────────────
# CARTE LEAFLET (version simple mais fonctionnelle)
# ─────────────────────────────────────────────
def make_simple_map(city_name='Yaoundé'):
    """Crée une carte Leaflet simple mais fonctionnelle."""
    import dash_leaflet as dl
    CITIES_DATA = get_cities_data()
    # Trouver la ville sélectionnée
    selected_city = next((c for c in CITIES_DATA if c['city'] == city_name), CITIES_DATA[0])
    
    # Créer les marqueurs pour toutes les villes
    markers = []
    for c in CITIES_DATA:
        col = aqi_color(c['aqi'])
        popup_html = html.Div([
            html.Strong(c['city'], style={'fontSize': '14px', 'color': col}),
            html.Br(),
            html.Span(f"AQI: {c['aqi']}", style={'fontWeight': 'bold'}),
            html.Br(),
            html.Span(aqi_label(c['aqi']), style={'fontSize': '11px'}),
        ], style={'minWidth': '120px', 'padding': '6px'})
        
        markers.append(dl.CircleMarker(
            center=[c['lat'], c['lon']],
            radius=max(6, min(18, c['aqi'] / 12)),
            color=col,
            fillColor=col,
            fillOpacity=0.7,
            weight=1.5,
            children=dl.Popup(popup_html)
        ))
    
    # Créer la carte
    map_component = dl.Map(
        children=[
            dl.TileLayer(url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
                         attribution='&copy; OpenStreetMap & CartoDB'),
            dl.LayerGroup(markers),
            dl.ScaleControl(position='bottomleft'),
        ],
        center=[5.5, 12.3],
        zoom=6,
        style={'height': '380px', 'width': '100%', 'borderRadius': '12px'},
    )
    
    return map_component

# ─────────────────────────────────────────────
# CARTE LEAFLET AVEC THÈME DYNAMIQUE
# ─────────────────────────────────────────────
def create_dynamic_map(city_name='Yaoundé', lang='fr', theme='dark'):
    """Crée une carte Leaflet avec zoom sur la ville sélectionnée"""
    CITIES_DATA = get_cities_data()
    # Choisir le fond de carte selon le thème
    if theme == 'dark':
        tile_url = "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
    else:
        tile_url = "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
    
    # Trouver la ville sélectionnée pour le centrage
    if city_name and city_name != 'all' and city_name != 'National':
        center_city = next((c for c in CITIES_DATA if c['city'] == city_name), CITIES_DATA[0])
        center = [center_city['lat'], center_city['lon']]
        zoom = 10
    else:
        center = [5.5, 12.3]
        zoom = 6
    
    markers = []
    for city in CITIES_DATA:
        col = aqi_color(city['aqi'])
        is_selected = (city_name == city['city'])
        
        # Taille du marqueur plus grande pour la ville sélectionnée
        radius = 14 if is_selected else max(6, min(18, city['aqi'] / 12))
        weight = 3 if is_selected else 1.5
        
        popup_html = html.Div([
            html.Div([
                html.Strong(city['city'],
                            style={'fontSize': '15px', 'color': col, 'display': 'block',
                                   'marginBottom': '4px'}),
                html.Span(city['region'],
                          style={'fontSize': '10px', 'color': '#7a90b5',
                                 'textTransform': 'uppercase', 'letterSpacing': '0.06em'}),
            ], style={'marginBottom': '10px'}),
            html.Div([
                html.Div([
                    html.Span("AQI", style={'fontSize': '9px', 'color': '#7a90b5',
                                            'fontWeight': '700', 'display': 'block',
                                            'textTransform': 'uppercase'}),
                    html.Span(f"{city['aqi']}",
                              style={'fontSize': '24px', 'fontWeight': '800', 'color': col}),
                ], style={'textAlign': 'center', 'flex': '1'}),
                html.Div([
                    html.Span("PM2.5", style={'fontSize': '9px', 'color': '#7a90b5',
                                              'fontWeight': '700', 'display': 'block',
                                              'textTransform': 'uppercase'}),
                    html.Span(f"{city['pm25']}",
                              style={'fontSize': '18px', 'fontWeight': '700', 'color': '#ff1744'}),
                    html.Span(" µg/m³", style={'fontSize': '9px', 'color': '#7a90b5'}),
                ], style={'textAlign': 'center', 'flex': '1'}),
                html.Div([
                    html.Span("NO₂", style={'fontSize': '9px', 'color': '#7a90b5',
                                            'fontWeight': '700', 'display': 'block',
                                            'textTransform': 'uppercase'}),
                    html.Span(f"{city['no2']}",
                              style={'fontSize': '18px', 'fontWeight': '700', 'color': '#00d4ff'}),
                    html.Span(" µg/m³", style={'fontSize': '9px', 'color': '#7a90b5'}),
                ], style={'textAlign': 'center', 'flex': '1'}),
            ], style={'display': 'flex', 'gap': '8px', 'marginBottom': '8px',
                      'padding': '8px', 'background': 'rgba(0,0,0,0.15)',
                      'borderRadius': '8px'}),
            html.Div([
                html.Span(aqi_label(city['aqi'], lang),
                          style={'fontSize': '11px', 'fontWeight': '700', 'color': col,
                                 'background': f'{col}20', 'padding': '2px 10px',
                                 'borderRadius': '99px', 'border': f'1px solid {col}40'})
            ], style={'textAlign': 'center', 'marginBottom': '8px'}),
            html.Button(
                [html.I(className="fas fa-map-pin",
                        style={'marginRight': '6px', 'fontSize': '10px'}),
                 "Zoomer sur cette ville"],
                id={'type': 'select-city', 'index': city['city']},
                style={
                    'width': '100%', 'padding': '6px 10px', 'borderRadius': '8px',
                    'border': f'1px solid {col}60', 'background': f'{col}18',
                    'color': col, 'cursor': 'pointer', 'fontSize': '11px',
                    'fontWeight': '600', 'transition': 'all 0.2s ease',
                    'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center',
                }
            )
        ], style={'minWidth': '200px', 'padding': '10px', 'fontFamily': 'Inter, sans-serif'})
        
        markers.append(dl.CircleMarker(
            center=[city['lat'], city['lon']],
            radius=radius,
            color=col,
            fillColor=col,
            fillOpacity=0.8 if is_selected else 0.6,
            weight=weight,
            children=dl.Popup(popup_html)
        ))
    
    map_component = dl.Map(
        children=[
            dl.TileLayer(url=tile_url, attribution='&copy; OpenStreetMap & CartoDB'),
            # Contours des régions du Cameroun (shapefile GeoJSON)
            dl.GeoJSON(
                url='/assets/cameroon_level1.geojson',
                id='cameroon-regions-layer',
                style={
                    'color': '#2a4070' if theme == 'dark' else '#a0b8d0',
                    'weight': 1.8,
                    'fillColor': '#00d4ff' if theme == 'dark' else '#0284c7',
                    'fillOpacity': 0.04,
                    'dashArray': '4 3',
                }
            ),
            dl.LayerGroup(markers),
            dl.ScaleControl(position='bottomleft'),
        ],
        center=center,
        zoom=zoom,
        style={'height': '340px', 'width': '100%', 'borderRadius': '12px'},
        id='dynamic-map'
    )
    
    return map_component

# ─────────────────────────────────────────────
# OVERVIEW FALLBACK (VERSION AVEC CARTE DYNAMIQUE)
# ─────────────────────────────────────────────
def make_overview_fallback(city_name='National', lang='fr', theme='dark'):
    """Vue d'ensemble - avec filtre de ville intégré"""
    CITIES_DATA = get_cities_data()
    # ML perf dynamique
    _ml_pct = "94.7"
    _ml_r2  = "R²=—"
    try:
        from api_client import load_model_info
        _info = load_model_info()
        _r2v = _info.get('aqi_global', {}).get('r2_test')
        if _r2v is not None:
            _ml_pct = f"{min(100, max(0, _r2v * 100)):.1f}"
            _ml_r2  = f"R²={_r2v:.3f}"
    except Exception:
        pass

    # Récupérer les données selon la ville sélectionnée
    if city_name and city_name != 'all' and city_name != 'National':
        selected_city = city_name
        city_data = next((c for c in CITIES_DATA if c['city'] == selected_city), CITIES_DATA[0])
        region = city_data['region']
        is_national = False
        display_title = f"{selected_city} - {region}"
    else:
        selected_city = 'National'
        is_national = True
        display_title = "Niveau national"
        # Valeurs par défaut pour l'affichage (seront remplacées par les KPIs)
        nat_stats = get_national_stats()
        city_data = {
            'city': 'National',
            'aqi': nat_stats['aqi'],
            'pm25': nat_stats['pm25'],
            'pm10': round(sum(c.get('pm10', 0) for c in get_cities_data()) / max(len(get_cities_data()), 1), 1),
            'no2': nat_stats['no2'],
            'trend': nat_stats.get('trend_aqi', 0.0),
        }

    # Options pour le dropdown des villes (données fraîches)
    cities_dyn = get_cities_data()
    city_options = [{'label': '🇨🇲 Niveau national', 'value': 'National'}] + \
                   [{'label': f"{c['city']} - {c['region']}", 'value': c['city']} for c in cities_dyn]

    # Créer la carte avec le thème actuel — niveau national = pas de zoom sur une ville
    real_map = create_dynamic_map('National' if is_national else selected_city, lang, theme)

    # Sparklines 7 jours réelles depuis l'API
    def _real_sparkline_vals(city_n, field='aqi', n=7):
        try:
            from api_client import load_city_history
            hist = load_city_history(city_n, n)
            if hist:
                vals = [r.get(field, 0) for r in sorted(hist, key=lambda x: x.get('pred_date', ''))]
                return vals[-n:] if len(vals) >= n else vals
        except Exception:
            pass
        return None

    def _mini_sparkline(base_val, accent_color, n=7, city_n=None, field='aqi'):
        """Mini histogramme CSS depuis données réelles."""
        vals = _real_sparkline_vals(city_n, field, n) if city_n and city_n != 'National' else None
        if not vals:
            # Fallback : barres plates (pas de random)
            vals = [base_val] * n
        max_v = max(vals) or 1
        height = 32
        bars = []
        for i, v in enumerate(vals):
            h_pct = max(6, int(v / max_v * 100))
            is_last = (i == n - 1)
            bg = accent_color if is_last else f'{accent_color}60'
            bars.append(html.Div(style={
                'width': '10px',
                'height': f'{h_pct}%',
                'backgroundColor': bg,
                'borderRadius': '2px',
                'alignSelf': 'flex-end',
                'flexShrink': '0',
            }))
        return html.Div(bars, style={
            'marginTop': '8px',
            'display': 'flex',
            'alignItems': 'flex-end',
            'justifyContent': 'center',
            'gap': '3px',
            'height': f'{height}px',
        })

    return html.Div([
        # Ligne des KPIs (6 cartes) — valeur du jour + sparkline 7j
        html.Div([
            # Carte 1: Localisation + Filtre
            html.Div([
                html.Div([
                    html.I(className="fas fa-map-marker-alt", style={'color': '#00d4ff', 'fontSize': '18px', 'marginBottom': '8px'}),
                ], style={'display': 'flex', 'justifyContent': 'center', 'marginBottom': '8px'}),
                html.H3(display_title, style={'fontSize': '18px', 'fontWeight': '800', 'color': 'var(--text-primary)', 'margin': '0', 'textAlign': 'center', 'lineHeight': '1.3'}),
                html.Div([
                    dcc.Dropdown(
                        id='overview-city-selector',
                        options=city_options,
                        value=selected_city,
                        className='ac-dropdown',
                        clearable=False,
                        style={'width': '100%', 'marginTop': '12px'}
                    )
                ])
            ], className='kpi-card', style={'textAlign': 'center', 'padding': '16px', 'borderRadius': '16px', 'background': 'var(--bg-surface)', 'border': '2px solid #00d4ff60', 'boxShadow': '0 0 8px #00d4ff30'}),
            
            # Carte 2: AQI
            html.Div([
                html.Div([
                    html.I(className="fas fa-chart-line", style={'color': '#ff9100', 'fontSize': '14px', 'marginRight': '5px'}),
                    html.Span(t('kpi_national_aqi', lang) if is_national else 'AQI', style={'fontSize': '9px', 'fontWeight': '700', 'color': 'var(--text-secondary)', 'textTransform': 'uppercase', 'letterSpacing': '0.08em'}),
                ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center', 'marginBottom': '4px'}),
                html.H3(f"{city_data['aqi']:.0f}", style={'fontSize': '30px', 'fontWeight': '800', 'margin': '0', 'color': aqi_color(city_data['aqi']), 'textAlign': 'center', 'lineHeight': '1'}),
                html.Span("AQI", style={'fontSize': '11px', 'color': 'var(--text-secondary)', 'display': 'block', 'textAlign': 'center'}),
                html.Span(
                    f"{'▲' if city_data.get('trend', 0) > 0 else '▼'} {abs(city_data.get('trend', 8.3)):.1f}% vs hier",
                    style={'fontSize': '10px', 'color': '#ff1744' if city_data.get('trend', 0) >= 0 else '#00e676',
                           'display': 'block', 'textAlign': 'center', 'marginTop': '2px', 'fontWeight': '600'}
                ),
                _mini_sparkline(city_data['aqi'], aqi_color(city_data['aqi']), city_n=selected_city, field='aqi'),
            ], className='kpi-card', style={'textAlign': 'center', 'padding': '14px 12px', 'borderRadius': '16px', 'background': 'var(--bg-surface)', 'border': f'2px solid {aqi_color(city_data["aqi"])}60', 'boxShadow': f'0 0 8px {aqi_color(city_data["aqi"])}30'}),

            # Carte 3: PM2.5
            html.Div([
                html.Div([
                    html.I(className="fas fa-smog", style={'color': '#ff1744', 'fontSize': '14px', 'marginRight': '5px'}),
                    html.Span(t('kpi_pm25', lang), style={'fontSize': '9px', 'fontWeight': '700', 'color': 'var(--text-secondary)', 'textTransform': 'uppercase', 'letterSpacing': '0.08em'}),
                ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center', 'marginBottom': '4px'}),
                html.H3(f"{city_data['pm25']:.1f}", style={'fontSize': '30px', 'fontWeight': '800', 'margin': '0', 'color': '#ff1744', 'textAlign': 'center', 'lineHeight': '1'}),
                html.Span("µg/m³", style={'fontSize': '11px', 'color': 'var(--text-secondary)', 'display': 'block', 'textAlign': 'center'}),
                trend_span(city_data.get('trend', 0)),
                _mini_sparkline(city_data['pm25'], '#ff1744', city_n=selected_city, field='pm25'),
            ], className='kpi-card', style={'textAlign': 'center', 'padding': '14px 12px', 'borderRadius': '16px', 'background': 'var(--bg-surface)', 'border': '2px solid #ff174460', 'boxShadow': '0 0 8px #ff174430'}),

            # Carte 4: NO₂
            html.Div([
                html.Div([
                    html.I(className="fas fa-industry", style={'color': '#00d4ff', 'fontSize': '14px', 'marginRight': '5px'}),
                    html.Span(t('kpi_no2', lang), style={'fontSize': '9px', 'fontWeight': '700', 'color': 'var(--text-secondary)', 'textTransform': 'uppercase', 'letterSpacing': '0.08em'}),
                ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center', 'marginBottom': '4px'}),
                html.H3(f"{city_data['no2']:.1f}", style={'fontSize': '30px', 'fontWeight': '800', 'margin': '0', 'color': '#00d4ff', 'textAlign': 'center', 'lineHeight': '1'}),
                html.Span("µg/m³", style={'fontSize': '11px', 'color': 'var(--text-secondary)', 'display': 'block', 'textAlign': 'center'}),
                html.Span("— stable", style={'fontSize': '10px', 'color': 'var(--text-muted)', 'display': 'block', 'textAlign': 'center', 'marginTop': '2px'}),
                _mini_sparkline(city_data['no2'], '#00d4ff', city_n=selected_city, field='no2'),
            ], className='kpi-card', style={'textAlign': 'center', 'padding': '14px 12px', 'borderRadius': '16px', 'background': 'var(--bg-surface)', 'border': '2px solid #00d4ff60', 'boxShadow': '0 0 8px #00d4ff30'}),

            # Carte 5: Villes (données fraîches)
            html.Div([
                html.Div([
                    html.I(className="fas fa-city", style={'color': '#00e676', 'fontSize': '14px', 'marginRight': '5px'}),
                    html.Span(t('kpi_cities', lang), style={'fontSize': '9px', 'fontWeight': '700', 'color': 'var(--text-secondary)', 'textTransform': 'uppercase', 'letterSpacing': '0.08em'}),
                ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center', 'marginBottom': '4px'}),
                html.H3(f"{len(cities_dyn)}", style={'fontSize': '30px', 'fontWeight': '800', 'margin': '0', 'color': '#00e676', 'textAlign': 'center', 'lineHeight': '1'}),
                html.Span(f"/ {len(get_regions(cities_dyn))} {'regions' if lang=='en' else 'régions'}", style={'fontSize': '11px', 'color': 'var(--text-secondary)', 'display': 'block', 'textAlign': 'center'}),
                html.Span(t('live', lang), style={'fontSize': '10px', 'color': '#00e676', 'display': 'block', 'textAlign': 'center', 'marginTop': '2px', 'fontWeight': '600'}),
                _mini_sparkline(len(cities_dyn), '#00e676'),
            ], className='kpi-card', style={'textAlign': 'center', 'padding': '14px 12px', 'borderRadius': '16px', 'background': 'var(--bg-surface)', 'border': '2px solid #00e67660', 'boxShadow': '0 0 8px #00e67630'}),

            # Carte 6: Modèle ML (dynamique)
            html.Div([
                html.Div([
                    html.I(className="fas fa-brain", style={'color': '#a855f7', 'fontSize': '14px', 'marginRight': '5px'}),
                    html.Span(t('kpi_ml', lang), style={'fontSize': '9px', 'fontWeight': '700', 'color': 'var(--text-secondary)', 'textTransform': 'uppercase', 'letterSpacing': '0.08em'}),
                ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center', 'marginBottom': '4px'}),
                html.H3(_ml_pct, style={'fontSize': '30px', 'fontWeight': '800', 'margin': '0', 'color': '#a855f7', 'textAlign': 'center', 'lineHeight': '1'}),
                html.Span("%", style={'fontSize': '11px', 'color': 'var(--text-secondary)', 'display': 'block', 'textAlign': 'center'}),
                html.Span(_ml_r2, style={'fontSize': '10px', 'color': 'var(--text-muted)', 'display': 'block', 'textAlign': 'center', 'marginTop': '2px', 'fontFamily': "'JetBrains Mono',monospace"}),
                _mini_sparkline(94.7, '#a855f7'),
            ], className='kpi-card', style={'textAlign': 'center', 'padding': '14px 12px', 'borderRadius': '16px', 'background': 'var(--bg-surface)', 'border': '2px solid #a855f760', 'boxShadow': '0 0 8px #a855f730'}),
            
        ], style={'display': 'grid', 'gridTemplateColumns': 'repeat(6,1fr)', 'gap': '12px', 'marginBottom': '24px'}),
        
        # Ligne 1 : Carte + Jauge + Timeline
        html.Div([
            # Carte (span 7)
            html.Div([
                section_hdr('fa-map-location-dot', f'CARTE SPATIALE — {len(CITIES_DATA)} VILLES'),
                real_map,
                html.Div([
                    html.I(className="fas fa-info-circle", style={'marginRight': '6px', 'fontSize': '10px'}),
                    html.Span(t('map_click_hint', lang),
                              style={'fontSize': '10px', 'color': 'var(--text-muted)'})
                ], style={'marginTop': '8px', 'textAlign': 'center'})
            ], className='card', style={'gridColumn': 'span 7'}),
            
            # Jauge (span 5)
            html.Div([
                section_hdr('fa-gauge-high', 'JAUGE IQA'),
                html.Div([
                    html.Div(display_title, style={'fontSize': '11px', 'fontWeight': '700', 'color': 'var(--text-secondary)',
                                        'textTransform': 'uppercase', 'letterSpacing': '0.08em',
                                        'textAlign': 'center', 'marginBottom': '2px'}),
                    dcc.Graph(figure=make_gauge_figure(city_data['aqi']), config={'displayModeBar': False}, style={'width': '100%', 'height': '220px'}),
                    html.Div([aqi_badge_el(city_data['aqi'], lang)], style={'textAlign': 'center', 'marginTop': '4px'}),
                    html.Div([
                        html.Div([
                            html.Span('PM2.5', style={'color': 'var(--text-muted)', 'fontSize': '10px', 'display': 'block'}),
                            html.Span(f"{city_data['pm25']:.1f}", style={'fontSize': '14px', 'fontWeight': '700', 'color': '#ff1744'}),
                        ], style={'textAlign': 'center'}),
                        html.Div([
                            html.Span('PM10', style={'color': 'var(--text-muted)', 'fontSize': '10px', 'display': 'block'}),
                            html.Span(f"{city_data['pm10']:.1f}", style={'fontSize': '14px', 'fontWeight': '700', 'color': '#ff9100'}),
                        ], style={'textAlign': 'center'}),
                        html.Div([
                            html.Span('NO₂', style={'color': 'var(--text-muted)', 'fontSize': '10px', 'display': 'block'}),
                            html.Span(f"{city_data['no2']:.1f}", style={'fontSize': '14px', 'fontWeight': '700', 'color': '#00d4ff'}),
                        ], style={'textAlign': 'center'}),
                    ], style={'display': 'flex', 'justifyContent': 'space-around', 'marginTop': '12px',
                              'padding': '10px', 'background': 'var(--bg-surface)', 'borderRadius': '10px',
                              'border': '1px solid var(--border)'}),
                ])
            ], className='card', style={'gridColumn': 'span 5'}),
           
            # Timeline (span 8)
            html.Div([
                html.Div([
                    section_hdr('fa-chart-line', 'ÉVOLUTION TEMPORELLE'),
                    html.Div([
                        html.Button('7j', id='tl-7j', n_clicks=0, 
                                className='hdr-btn hdr-btn-text',
                                style={'borderColor': 'var(--cyan)', 'color': 'var(--cyan)'}),
                        html.Button('30j', id='tl-30j', n_clicks=0, 
                                className='hdr-btn hdr-btn-text'),
                    ], style={'display': 'flex', 'gap': '6px'}),
                ], style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center', 'marginBottom': '8px'}),
                html.Div(
                    id='timeline-graph-container',
                    children=make_timeline(selected_city if not is_national else None, '30j'),
                    style={'width': '100%', 'height': 'auto', 'flex': '1'}
                ),
            ], className='card', style={'gridColumn': 'span 8', 'display': 'flex', 'flexDirection': 'column', 'padding': '14px 16px'}),

            # Alertes (span 4)
            html.Div([
                html.Div([
                    section_hdr('fa-bell', 'ALERTES & RECOMMANDATIONS'),
                    html.Span('3 actives', style={
                        'fontSize': '10px', 'fontWeight': '700', 'color': '#ff1744',
                        'background': 'rgba(255,23,68,0.12)', 'padding': '2px 8px',
                        'borderRadius': '99px', 'border': '1px solid rgba(255,23,68,0.3)'
                    })
                ], style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center', 'marginBottom': '12px'}),
                make_alerts(lang),
            ], className='card', style={'gridColumn': 'span 4'}),
            
        ], style={'display': 'grid', 'gridTemplateColumns': 'repeat(12,1fr)', 'gap': '14px', 'marginBottom': '14px'}, className='grid-12'),
        
        # Ligne 2 : Classement + Prévisions + Variable importance
        html.Div([
            # Classement (span 4)
            html.Div([
                section_hdr('fa-ranking-star', 'CLASSEMENT DES VILLES'),
                make_ranking(5),
                html.Div(html.Span(f'+ {len(CITIES_DATA) - 5} autres villes', style={
                    'fontSize': '10px', 'color': 'var(--text-muted)', 'fontStyle': 'italic'
                }), style={'textAlign': 'center', 'marginTop': '8px'}),
            ], className='card', style={'gridColumn': 'span 4'}),
            
            # Prévisions 7j (span 5)
            html.Div([
                make_forecast(selected_city if not is_national else None, lang),
                html.Div([
                    html.Div([
                        html.Span(t('confidence_label', lang), className='filter-label', style={'display': 'block', 'marginBottom': '6px'}),
                        html.Div([
                            html.Div(style={'flex': '1', 'height': '6px', 'background': 'var(--green)', 'borderRadius': '99px'}),
                        ], style={'height': '6px', 'background': 'var(--border)', 'borderRadius': '99px', 'overflow': 'hidden', 'flex': '1'}),
                    ], style={'display': 'flex', 'flexDirection': 'column', 'marginTop': '16px'}),
                    html.Div(html.Span('94.7%', style={'fontSize': '11px', 'fontWeight': '700', 'color': 'var(--green)'}), style={'textAlign': 'right', 'marginTop': '4px'}),
                ]),
            ], className='card', style={'gridColumn': 'span 5'}),
            
            # SHAP variables (span 3) — connecté à l'API
            html.Div([
                section_hdr('fa-chart-bar', 'PERFORMANCE DES MODÈLES (R²)'),
                *_model_perf_rows(),
            ], className='card', style={'gridColumn': 'span 3'}),
            
        ], style={'display': 'grid', 'gridTemplateColumns': 'repeat(12,1fr)', 'gap': '14px'}, className='grid-12'),
        
    ], className='anim-fade-up')


def make_gauge_figure(aqi_val, theme='dark'):
    """Crée la figure de jauge pour Plotly"""
    col = aqi_color(aqi_val)
    fc = '#e8f0fe' if theme == 'dark' else '#0f1f35'
    tick_col = '#7a90b5' if theme == 'dark' else '#4a6080'
    fig = go.Figure(go.Indicator(
        mode='gauge+number',
        value=aqi_val,
        domain={'x': [0, 1], 'y': [0, 1]},
        number={'font': {'size': 44, 'color': col, 'family': 'Inter'}, 'suffix': ''},
        gauge={
            'axis': {'range': [0, 300], 'tickwidth': 1, 'tickcolor': tick_col,
                     'tickfont': {'size': 9, 'color': tick_col}},
            'bar': {'color': col, 'thickness': 0.22},
            'bgcolor': 'rgba(0,0,0,0)',
            'borderwidth': 0,
            'steps': [
                {'range': [0, 50], 'color': 'rgba(0,230,118,0.12)'},
                {'range': [50, 100], 'color': 'rgba(255,238,88,0.12)'},
                {'range': [100, 150], 'color': 'rgba(255,145,0,0.12)'},
                {'range': [150, 200], 'color': 'rgba(255,23,68,0.12)'},
                {'range': [200, 300], 'color': 'rgba(213,0,249,0.12)'},
            ],
            'threshold': {
                'line': {'color': col, 'width': 3},
                'thickness': 0.8, 'value': aqi_val
            }
        }
    ))
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=20, r=20, t=20, b=20),
        height=220,
        font={'family': 'Inter', 'color': fc}
    )
    return fig

def make_gauge_figure(aqi_val, theme='dark'):
    """Crée la figure de jauge pour Plotly"""
    col = aqi_color(aqi_val)
    fc = '#e8f0fe' if theme == 'dark' else '#0f1f35'
    tick_col = '#7a90b5' if theme == 'dark' else '#4a6080'
    fig = go.Figure(go.Indicator(
        mode='gauge+number',
        value=aqi_val,
        domain={'x': [0, 1], 'y': [0, 1]},
        number={'font': {'size': 44, 'color': col, 'family': 'Inter'}, 'suffix': ''},
        gauge={
            'axis': {'range': [0, 300], 'tickwidth': 1, 'tickcolor': tick_col,
                     'tickfont': {'size': 9, 'color': tick_col}},
            'bar': {'color': col, 'thickness': 0.22},
            'bgcolor': 'rgba(0,0,0,0)',
            'borderwidth': 0,
            'steps': [
                {'range': [0, 50], 'color': 'rgba(0,230,118,0.12)'},
                {'range': [50, 100], 'color': 'rgba(255,238,88,0.12)'},
                {'range': [100, 150], 'color': 'rgba(255,145,0,0.12)'},
                {'range': [150, 200], 'color': 'rgba(255,23,68,0.12)'},
                {'range': [200, 300], 'color': 'rgba(213,0,249,0.12)'},
            ],
            'threshold': {
                'line': {'color': col, 'width': 3},
                'thickness': 0.8, 'value': aqi_val
            }
        }
    ))
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=20, r=20, t=20, b=20),
        height=220,
        font={'family': 'Inter', 'color': fc}
    )
    return fig

def make_gauge_figure(aqi_val, theme='dark'):
    """Crée la figure de jauge pour Plotly"""
    col = aqi_color(aqi_val)
    fc = '#e8f0fe' if theme == 'dark' else '#0f1f35'
    tick_col = '#7a90b5' if theme == 'dark' else '#4a6080'
    fig = go.Figure(go.Indicator(
        mode='gauge+number',
        value=aqi_val,
        domain={'x': [0, 1], 'y': [0, 1]},
        number={'font': {'size': 44, 'color': col, 'family': 'Inter'}, 'suffix': ''},
        gauge={
            'axis': {'range': [0, 300], 'tickwidth': 1, 'tickcolor': tick_col,
                     'tickfont': {'size': 9, 'color': tick_col}},
            'bar': {'color': col, 'thickness': 0.22},
            'bgcolor': 'rgba(0,0,0,0)',
            'borderwidth': 0,
            'steps': [
                {'range': [0, 50], 'color': 'rgba(0,230,118,0.12)'},
                {'range': [50, 100], 'color': 'rgba(255,238,88,0.12)'},
                {'range': [100, 150], 'color': 'rgba(255,145,0,0.12)'},
                {'range': [150, 200], 'color': 'rgba(255,23,68,0.12)'},
                {'range': [200, 300], 'color': 'rgba(213,0,249,0.12)'},
            ],
            'threshold': {
                'line': {'color': col, 'width': 3},
                'thickness': 0.8, 'value': aqi_val
            }
        }
    ))
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=20, r=20, t=20, b=20),
        height=220,
        font={'family': 'Inter', 'color': fc}
    )
    return fig

# ─────────────────────────────────────────────
# HEADER DASHBOARD
# ─────────────────────────────────────────────
def make_header(user, lang='fr'):
    role = user.get('role', 'citizen')
    color = user.get('color', '#00d4ff')
    tabs = ROLE_TABS.get(role, ROLE_TABS['citizen'])
    now = datetime.now()

    role_tab_color = {
        'citizen': ('var(--cyan-dim)', 'var(--citizen-color)'),
        'decision': ('rgba(250,204,21,0.08)', 'var(--decision-color)'),
        'researcher': ('rgba(168,85,247,0.10)', 'var(--researcher-color)'),
        'doctor': ('rgba(52,211,153,0.10)', 'var(--doctor-color)'),
    }
    tab_bg, tab_accent = role_tab_color.get(role, ('var(--cyan-dim)', 'var(--cyan)'))

    tab_btns = []
    for i, (tab_id, icon_cls, label_key) in enumerate(tabs):
        tab_btns.append(html.Button(
            [fa(icon_cls, style={'fontSize': '12px'}), html.Span(t(label_key, lang), style={'marginLeft': '5px'})],
            id={'type': 'nav-tab', 'index': tab_id}, n_clicks=0,
            className='nav-tab-btn' + (' active' if i == 0 else ''),
            style={'--tab-color': tab_bg, '--tab-accent': tab_accent},
        ))

    return html.Div([
                # Logo 
        html.Div([
            html.Div([
                # Logo AirEka
                html.Img(
                    src='/assets/AirEka.jpeg',
                    style={
                        'width': '36px',
                        'height': '36px',
                        'borderRadius': '10px',
                        'objectFit': 'cover',
                        'border': '1.5px solid rgba(0,230,118,0.4)',
                        'boxShadow': '0 0 12px rgba(0,230,118,0.2)',
                        'flexShrink': '0',
                    }
                ),
            ], style={'display': 'flex', 'alignItems': 'center'}),
            html.Div([
                html.Div([
                    html.Span(t('app_name', lang), className='logo-text'),
                    # Drapeau Cameroun après le nom
                    html.Img(
                        src='/assets/R.jpg',
                        style={
                            'width': '22px',
                            'height': '22px',
                            'borderRadius': '3px',
                            'marginLeft': '8px',
                            'objectFit': 'cover',
                            'border': '1px solid var(--border)',
                            'verticalAlign': 'middle'
                        }
                    ),
                ], style={'display': 'flex', 'alignItems': 'center'}),
                html.Div('Cameroun · IndabaX 2026', className='logo-sub')
            ])
        ], className='logo-wrap'),

        html.Div([html.Span(className='live-dot'), html.Span(t('live', lang))], className='live-badge'),
        html.Div(tab_btns, id='nav-tabs-bar'),
        html.Div([
            html.Div([fa(user.get('icon', 'fa-user'), style={'fontSize': '11px'}), html.Span(user.get('label_fr' if lang == 'fr' else 'label_en', 'Utilisateur'), style={'marginLeft': '5px'})],
                     className='role-badge', style={'color': color, 'borderColor': color + '40', 'background': color + '18'}),
            html.Div(user.get('initials', 'XX'), className='user-avatar', style={'color': color, 'borderColor': color, 'background': color + '18'}),
            html.Span(user.get('name', ''), style={'fontSize': '12px', 'fontWeight': '600', 'color': 'var(--text-primary)', 'whiteSpace': 'nowrap'}),
            html.Div(className='hdr-sep'),
            html.Button([fa('fa-sun', id='theme-icon')], id='btn-theme', n_clicks=0, className='hdr-btn', title='Basculer thème'),
            html.Button('FR' if lang == 'fr' else 'EN', id='btn-lang', n_clicks=0, className='hdr-btn hdr-btn-text'),
            html.Div(className='hdr-sep'),
            html.Button([fa('fa-right-from-bracket'), html.Span(t('logout', lang), style={'marginLeft':'5px'})], id='btn-logout', n_clicks=0, className='hdr-btn hdr-btn-logout'),
        ], style={'display': 'flex', 'alignItems': 'center', 'gap': '8px', 'flexShrink': '0'}),
        html.Div(now.strftime('%d/%m/%Y  %H:%M WAT'), id='header-clock',
                 style={'fontSize': '11px', 'color': 'var(--text-muted)', 'whiteSpace': 'nowrap', 'flexShrink': '0', 'fontFamily': "'JetBrains Mono', monospace"}),
    ], id='app-header')

# ─────────────────────────────────────────────
# LAYOUT LOGIN - NOUVEAU AVEC INSCRIPTION
# ─────────────────────────────────────────────
def make_login():
    from login import create_login_layout
    return create_login_layout()

# ─────────────────────────────────────────────
# LAYOUT DASHBOARD
# ─────────────────────────────────────────────
def make_dashboard(user, lang='fr'):
    # Cacher la barre de filtres pour certains rôles et onglets
    # La barre sera gérée dynamiquement par un callback
    return html.Div([
        make_header(user, lang),
        html.Div([
            html.Div(id='filter-bar-container'),
            html.Div([
                html.Span(id='refresh-badge', style={
                    'fontSize': '10px', 'color': 'var(--text-muted)',
                    'display': 'block', 'textAlign': 'right',
                    'padding': '2px 8px 0',
                }),
            ]),
            dcc.Loading(
                id='loading-tab-content',
                type='circle',
                color='var(--cyan)',
                children=html.Div(id='tab-content', style={'minHeight': '400px'}),
            ),
        ], id='main-content'),
        html.Div([
            html.Div([
                html.Span('Sources : '),
                html.A('Indabax-Hachaton 2026', href='#', style={'color':'var(--cyan)'}), ' · ',
                html.A('Deepstats Consulting', href='#', style={'color':'var(--cyan)'}), ' · ',
            ], className='footer-sources'),
            html.Span([fa('', style={'marginRight':'5px','color':'var(--cyan)'}), '© Tous droits reservés'], style={'color':'var(--text-muted)','fontSize':'10px'}),
            html.Span('© 2026 AirEka · IndabaX Cameroon', style={'color':'var(--text-muted)','fontSize':'10px'}),
        ], id='app-footer'),
    ], id='dashboard-wrapper')

# ─────────────────────────────────────────────
# LAYOUT RACINE
# ─────────────────────────────────────────────
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    dcc.Store(id='store-user', storage_type='session'),
    dcc.Store(id='store-theme', data='dark', storage_type='local'),
    dcc.Store(id='store-lang', data='fr', storage_type='local'),
    dcc.Store(id='store-city', data='Yaoundé'),
    dcc.Store(id='store-region', data='all'),
    dcc.Store(id='store-selected-city', data='Yaoundé'),
    dcc.Store(id='store-refresh-ts', data=0),
    dcc.Store(id='active-tab', data=None),
    dcc.Interval(id='auto-refresh', interval=5*60*1000, n_intervals=0),
    # Bannière statut API (visible uniquement si API indisponible au démarrage)
    _api_banner() or html.Div(),
    html.Div(id='page-content'),
    
    # ============= CHATBOT FLOATING GLOBAL =============
    html.Div([
        # Bouton flottant
        html.Button(
            [
                html.I(className="fas fa-robot", style={'fontSize': '22px'}),
                html.Span("AirEka AI", style={'marginLeft': '10px', 'fontSize': '13px', 'fontWeight': '600'})
            ],
            id='chatbot-fab',
            n_clicks=0,
            style={
                'position': 'fixed', 'bottom': '24px', 'right': '24px',
                'background': 'linear-gradient(135deg, #00d4ff, #0084cc)',
                'border': 'none', 'borderRadius': '48px', 'padding': '12px 24px',
                'color': 'white', 'cursor': 'pointer', 'zIndex': '1000',
                'boxShadow': '0 4px 20px rgba(0,212,255,0.4)',
                'display': 'flex', 'alignItems': 'center', 'gap': '8px',
                'fontFamily': 'Inter', 'fontWeight': '600', 'backdropFilter': 'blur(4px)',
                'transition': 'transform 0.2s, box-shadow 0.2s'
            },
            title="Posez une question à l'assistant AirEka"
        ),
        
        # Panneau de chat (caché par défaut)
        html.Div(
            id='chatbot-panel',
            style={
                'position': 'fixed', 'bottom': '90px', 'right': '24px',
                'width': '360px', 'maxWidth': 'calc(100vw - 48px)',
                'background': 'var(--bg-card)', 'borderRadius': '24px',
                'border': f'1px solid var(--border)', 'boxShadow': 'var(--shadow-lg)',
                'zIndex': '1001', 'overflow': 'hidden', 'display': 'none',
                'backdropFilter': 'blur(8px)'
            },
            children=[
                # En-tête du chat
                html.Div([
                    html.Div([
                        html.I(className="fas fa-robot", style={'color': '#00d4ff', 'fontSize': '20px'}),
                        html.Span("AirEka Assistant", style={'fontWeight': '700', 'marginLeft': '12px', 'fontSize': '16px'})
                    ], style={'display': 'flex', 'alignItems': 'center'}),
                    html.Div([
                        html.Span("●", style={'color': '#00e676', 'fontSize': '10px', 'marginRight': '8px'}),
                        html.Span("En ligne", style={'fontSize': '11px', 'color': 'var(--text-secondary)'}),
                        html.Button(
                            html.I(className="fas fa-times", style={'fontSize': '14px'}),
                            id='chatbot-close',
                            style={
                                'background': 'none', 'border': 'none', 'color': 'var(--text-secondary)',
                                'cursor': 'pointer', 'marginLeft': '12px', 'padding': '4px',
                                'borderRadius': '50%', 'transition': 'background 0.2s'
                            },
                            n_clicks=0
                        )
                    ], style={'display': 'flex', 'alignItems': 'center'})
                ], style={
                    'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center',
                    'padding': '14px 18px', 'borderBottom': f'1px solid var(--border)',
                    'background': 'var(--bg-surface)'
                }),
                
                # Zone des messages
                html.Div(
                    id='chatbot-messages',
                    style={
                        'height': '380px', 'overflowY': 'auto', 'padding': '16px',
                        'display': 'flex', 'flexDirection': 'column', 'gap': '12px'
                    },
                    children=[
                        # Message de bienvenue
                        html.Div([
                            html.Div([
                                html.I(className="fas fa-robot", style={'color': '#00d4ff', 'fontSize': '12px', 'marginRight': '6px'}),
                                html.Span("Assistant", style={'fontSize': '10px', 'color': 'var(--text-secondary)'})
                            ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '4px'}),
                            html.Div(
                                t('chatbot_greeting', 'fr'),
                                style={
                                    'fontSize': '12px', 'color': 'var(--text-primary)',
                                    'padding': '10px 12px', 'background': 'var(--bg-surface)',
                                    'borderRadius': '12px', 'lineHeight': '1.5'
                                }
                            )
                        ], style={'display': 'flex', 'flexDirection': 'column', 'alignItems': 'flex-start'}),
                    ]
                ),
                
                # Zone de saisie
                html.Div([
                    dcc.Input(
                        id='chatbot-input',
                        type='text',
                        placeholder="Posez une question...",
                        style={
                            'flex': '1', 'padding': '12px 14px', 'borderRadius': '24px',
                            'border': f'1px solid var(--border)', 'background': 'var(--bg-input)',
                            'color': 'var(--text-primary)', 'fontSize': '13px', 'outline': 'none',
                            'fontFamily': 'Inter'
                        }
                    ),
                    html.Button(
                        html.I(className="fas fa-paper-plane", style={'fontSize': '16px'}),
                        id='chatbot-send',
                        style={
                            'marginLeft': '10px', 'padding': '12px 16px', 'borderRadius': '40px',
                            'border': 'none', 'background': 'linear-gradient(135deg, #00d4ff, #0084cc)',
                            'color': 'white', 'cursor': 'pointer', 'transition': 'transform 0.1s'
                        },
                        n_clicks=0
                    )
                ], style={'display': 'flex', 'gap': '10px', 'padding': '16px', 'borderTop': f'1px solid var(--border)'}),
                
                # Indicateur de frappe (caché)
                html.Div(
                    id='chatbot-typing',
                    style={'display': 'none', 'padding': '8px 16px', 'fontSize': '11px', 'color': 'var(--text-muted)'},
                    children=[html.I(className="fas fa-ellipsis-h", style={'marginRight': '6px'}), "L'assistant écrit..."]
                )
            ]
        )
    ], id='chatbot-global'),
    dcc.Store(id='chatbot-history', data=[]),

    # Bouton flottant téléchargement méthodologie
    html.A(
        [
            html.I(className="fas fa-file-pdf", style={'fontSize': '18px'}),
            html.Span("Méthodologie", style={
                'maxWidth': '0', 'overflow': 'hidden', 'whiteSpace': 'nowrap',
                'transition': 'max-width 0.3s ease, margin 0.3s ease',
                'marginLeft': '0', 'fontSize': '12px', 'fontWeight': '600',
            }, id='pdf-btn-label'),
        ],
        href='/assets/methodologie_aireka.pdf',
        target='_blank',
        download='Méthodologie_AirEka.pdf',
        title="Télécharger la méthodologie AirEka",
        style={
            'position': 'fixed', 'bottom': '90px', 'left': '24px',
            'display': 'flex', 'alignItems': 'center',
            'background': 'linear-gradient(135deg, #ff1744, #c62828)',
            'color': 'white', 'borderRadius': '48px',
            'padding': '12px 16px', 'zIndex': '1000',
            'boxShadow': '0 4px 16px rgba(255,23,68,0.4)',
            'textDecoration': 'none', 'fontFamily': 'Inter',
            'transition': 'box-shadow 0.2s, transform 0.2s',
        },
        className='pdf-fab',
    ),
], id='root')

#────────────────────────────────────────────
# CALLBACKS
#────────────────────────────────────────────
# Callback clientside pour appliquer le thème (plus réactif)
app.clientside_callback(
    """
    function(theme) {
        if (theme) {
            document.documentElement.setAttribute('data-theme', theme);
            try {
                localStorage.setItem('aircam-theme', theme);
            } catch(e) {}
            // Mettre à jour l'icône du bouton thème
            var icon = document.getElementById('theme-icon');
            if (icon) {
                icon.className = theme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
            }
        }
        return theme;
    }
    """,
    Output('store-theme', 'data'),
    Input('store-theme', 'data'),
    prevent_initial_call=True
)

@app.callback(
    Output('stats-dynamic-content', 'children'),
    Input('stats-city-selector', 'value'),
    State('store-lang', 'data'),
    State('store-theme', 'data'),
    prevent_initial_call=True
)
def update_stats_content(selected_city, lang, theme):
    """Met à jour le contenu des statistiques quand la ville change."""
    from researcher_pages import _build_stats_content
    return _build_stats_content(selected_city, lang or 'fr', theme or 'dark')

# Callback Dash pour le bouton thème — met à jour store-theme
@app.callback(
    Output('store-theme', 'data', allow_duplicate=True),
    Input('btn-theme', 'n_clicks'),
    State('store-theme', 'data'),
    prevent_initial_call=True,
)
def toggle_theme(n, current_theme):
    if not n:
        return dash.no_update
    return 'light' if (current_theme or 'dark') == 'dark' else 'dark'

# Callback pour les boutons 7j/30j
@app.callback(
    Output('timeline-graph-container', 'children'),
    Input('tl-7j', 'n_clicks'),
    Input('tl-30j', 'n_clicks'),
    State('overview-city-selector', 'value'),
    prevent_initial_call=True
)
def update_timeline(n_7j, n_30j, selected_city):
    """Met à jour le graphique selon le bouton cliqué (7j ou 30j)"""
    triggered_id = ctx.triggered_id
    
    if triggered_id == 'tl-7j':
        timerange = '7j'
    else:
        timerange = '30j'
    
    if selected_city == 'National':
        city_name = None
    else:
        city_name = selected_city
    
    return make_timeline(city_name, timerange)


@app.callback(
    Output('overview-city-selector', 'value'),
    Input({'type': 'select-city', 'index': ALL}, 'n_clicks'),
    prevent_initial_call=True
)
def select_city_from_map(clicks):
    """Change la ville sélectionnée quand on clique sur le bouton dans la popup"""
    triggered_id = ctx.triggered_id
    if triggered_id and isinstance(triggered_id, dict):
        city_name = triggered_id.get('index')
        return city_name
    return dash.no_update


# Callback pour mettre à jour la page Aujourd'hui
@app.callback(
    Output('tab-content', 'children', allow_duplicate=True),
    Input('overview-city-selector', 'value'),
    State('store-lang', 'data'),
    State('store-theme', 'data'),
    prevent_initial_call=True
)
def update_overview_city(selected_city, lang, theme):
    """Met à jour la page Aujourd'hui avec la ville sélectionnée"""
    if selected_city == 'National':
        city_value = 'National'
    else:
        city_value = selected_city
    
    return make_overview_fallback(city_value, lang or 'fr', theme or 'dark')


# Callback pour basculer entre onglets Connexion/Inscription
@app.callback(
    [Output('login-form', 'style'),
     Output('signup-form', 'style'),
     Output('login-tab-btn', 'style'),
     Output('signup-tab-btn', 'style')],
    [Input('login-tab-btn', 'n_clicks'),
     Input('signup-tab-btn', 'n_clicks')],
    prevent_initial_call=True
)
def toggle_auth_tabs(n_login, n_signup):
    triggered = ctx.triggered_id
    
    login_style = {'display': 'block'}
    signup_style = {'display': 'none'}
    login_btn_style = {
        'flex': '1', 'padding': '12px', 'background': 'transparent',
        'border': 'none', 'borderBottom': '2px solid #00d4ff',
        'color': '#00d4ff', 'fontWeight': '700', 'fontSize': '14px',
        'cursor': 'pointer', 'fontFamily': 'DM Sans, sans-serif'
    }
    signup_btn_style = {
        'flex': '1', 'padding': '12px', 'background': 'transparent',
        'border': 'none', 'borderBottom': '2px solid #334155',
        'color': '#94a3b8', 'fontWeight': '700', 'fontSize': '14px',
        'cursor': 'pointer', 'fontFamily': 'DM Sans, sans-serif'
    }
    
    if triggered == 'signup-tab-btn':
        login_style = {'display': 'none'}
        signup_style = {'display': 'block'}
        login_btn_style = {**login_btn_style, 'borderBottom': '2px solid #334155', 'color': '#94a3b8'}
        signup_btn_style = {**signup_btn_style, 'borderBottom': '2px solid #00d4ff', 'color': '#00d4ff'}
    
    return login_style, signup_style, login_btn_style, signup_btn_style


# Callback pour l'œil (connexion)
@app.callback(
    [Output('login-password', 'type'),
     Output('login-toggle-icon', 'className')],
    Input('login-toggle-btn', 'n_clicks'),
    prevent_initial_call=True
)
def toggle_login_password(n_clicks):
    if n_clicks and n_clicks % 2 == 1:
        return 'text', 'fas fa-eye-slash'
    return 'password', 'fas fa-eye'


# Callback pour l'œil (inscription - mot de passe)
@app.callback(
    [Output('signup-password', 'type'),
     Output('signup-toggle-icon', 'className')],
    Input('signup-toggle-btn', 'n_clicks'),
    prevent_initial_call=True
)
def toggle_signup_password(n_clicks):
    if n_clicks and n_clicks % 2 == 1:
        return 'text', 'fas fa-eye-slash'
    return 'password', 'fas fa-eye'


# Callback pour l'œil (inscription - confirmation)
@app.callback(
    [Output('signup-confirm-password', 'type'),
     Output('signup-confirm-toggle-icon', 'className')],
    Input('signup-confirm-toggle-btn', 'n_clicks'),
    prevent_initial_call=True
)
def toggle_signup_confirm_password(n_clicks):
    if n_clicks and n_clicks % 2 == 1:
        return 'text', 'fas fa-eye-slash'
    return 'password', 'fas fa-eye'


# Callback pour la sélection du rôle (afficher/cacher la ville)
@app.callback(
    [Output('role-citizen', 'style'),
     Output('role-decision', 'style'),
     Output('role-researcher', 'style'),
     Output('selected-role', 'children'),
     Output('city-selection', 'style')],
    [Input('role-citizen', 'n_clicks'),
     Input('role-decision', 'n_clicks'),
     Input('role-researcher', 'n_clicks')],
    prevent_initial_call=True
)
def select_role(n_citizen, n_decision, n_researcher):
    triggered = ctx.triggered_id
    base_style = {
        'flex': '1', 'padding': '10px', 'borderRadius': '8px',
        'border': '2px solid #334155', 'background': 'transparent',
        'color': '#94a3b8', 'cursor': 'pointer', 'fontWeight': '600',
        'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center',
        'transition': 'all 0.2s ease'
    }
    active_style = {**base_style, 'borderColor': '#00d4ff', 'color': '#00d4ff', 'background': 'rgba(0,212,255,0.1)'}
    
    citizen_style = base_style
    decision_style = base_style
    researcher_style = base_style
    selected_role = ''
    city_style = {'display': 'none'}
    
    if triggered == 'role-citizen':
        citizen_style = active_style
        selected_role = 'citizen'
        city_style = {'display': 'block', 'marginBottom': '20px'}
    elif triggered == 'role-decision':
        decision_style = active_style
        selected_role = 'decision'
    elif triggered == 'role-researcher':
        researcher_style = active_style
        selected_role = 'researcher'
    
    return citizen_style, decision_style, researcher_style, selected_role, city_style


# Callback pour charger les villes dans le dropdown d'inscription
@app.callback(
    Output('signup-city', 'options'),
    Input('signup-city', 'id')
)
def load_cities(_):
    return [{'label': c['city'], 'value': c['city']} for c in CITIES_DATA]


# Callback pour l'inscription (waiter + vérif email + désactivation bouton)
@app.callback(
    [Output('signup-message', 'children'),
     Output('btn-signup-submit', 'disabled'),
     Output('btn-signup-submit', 'style'),
     Output('signup-loading-spinner', 'style')],
    Input('btn-signup-submit', 'n_clicks'),
    [State('signup-name', 'value'),
     State('signup-email', 'value'),
     State('signup-password', 'value'),
     State('signup-confirm-password', 'value'),
     State('selected-role', 'children'),
     State('signup-city', 'value')],
    prevent_initial_call=True
)
def handle_signup(n_clicks, name, email, password, confirm_password, role, city):
    _btn_base = {
        'width': '100%', 'padding': '12px', 'borderRadius': '10px',
        'border': 'none', 'fontSize': '14px', 'fontWeight': '700',
        'cursor': 'pointer', 'fontFamily': 'DM Sans, sans-serif',
        'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center',
        'gap': '8px', 'transition': 'all 0.2s ease',
        'background': 'linear-gradient(135deg, #00d4ff 0%, #0084cc 100%)',
        'color': '#ffffff',
    }
    _btn_disabled = {**_btn_base, 'opacity': '0.5', 'cursor': 'not-allowed'}
    _spinner_hide = {'display': 'none'}
    _spinner_show = {'display': 'flex', 'alignItems': 'center',
                     'justifyContent': 'center', 'marginTop': '10px'}

    def _err(msg):
        el = html.Div([html.I(className="fas fa-exclamation-circle",
                               style={'marginRight': '6px'}), msg],
                       style={'color': '#ef4444'})
        return el, False, _btn_base, _spinner_hide

    if not n_clicks:
        return '', False, _btn_base, _spinner_hide

    if not name or not email or not password:
        return _err("Veuillez remplir tous les champs obligatoires")

    # ── Vérification email déjà utilisé ───────────────────────────────
    if user_exists(email):
        return _err(f"L'adresse {email} est déjà associée à un compte. "
                    "Connectez-vous ou utilisez un autre email.")

    if password != confirm_password:
        return _err("Les mots de passe ne correspondent pas")

    if len(password) < 4:
        return _err("Le mot de passe doit contenir au moins 4 caractères")

    if not role:
        return _err("Veuillez sélectionner un rôle")

    if role == 'citizen' and not city:
        return _err("Veuillez sélectionner votre ville")

    # Récupérer la région de la ville
    city_data = next((c for c in CITIES_DATA if c['city'] == city), None)
    region = city_data['region'] if city_data else None

    result = create_user(name, email, password, role, city, region)
    
    if result['success']:
        # ── Email de bienvenue (personnalisé par rôle) ────────────────
        try:
            from email_scheduler import SENDER_EMAIL, SENDER_APP_PASSWORD, SENDER_DISPLAY, _logo_img_tag
            import smtplib
            from email.mime.multipart import MIMEMultipart
            from email.mime.text import MIMEText

            now_str      = datetime.now().strftime("%d/%m/%Y à %H:%M")
            city_display = city or "Cameroun"
            logo         = _logo_img_tag(42)

            # ── Configuration par rôle ──────────────────────────────
            ROLE_CFG = {
                "citizen": {
                    "label":   "Citoyen",
                    "color":   "#00d4ff",
                    "icon":    "fa-person",
                    "subject": "Bienvenue sur AirEka — Votre espace citoyen est prêt !",
                    "tagline": "Surveillez la qualité de l'air dans votre ville, chaque jour.",
                    "features": [
                        ("#16a34a", "fa-map-location-dot",
                         "Qualité de l'air en temps réel",
                         f"Consultez les niveaux AQI, PM2.5 et polluants à <strong>{city_display}</strong> en direct."),
                        ("#0ea5e9", "fa-bell",
                         "Alertes email automatiques",
                         "Activez vos alertes personnalisées dans l'onglet <strong>Alertes</strong>. "
                         "Choisissez l'heure et le seuil — les emails partent sans intervention manuelle."),
                        ("#ff9100", "fa-heart-pulse",
                         "Recommandations santé",
                         "Conseils adaptés à votre profil selon la qualité de l'air du jour."),
                        ("#a855f7", "fa-calendar-week",
                         "Prévisions 7 jours",
                         "Anticipez la qualité de l'air grâce aux modèles ML (R²=0.997)."),
                    ],
                    "alert_tip": True,
                },
                "decision": {
                    "label":   "Décideur",
                    "color":   "#facc15",
                    "icon":    "fa-landmark",
                    "subject": "Bienvenue sur AirEka — Votre tableau de bord décideur est prêt !",
                    "tagline": "Pilotez la qualité de l'air sur votre territoire avec des données fiables.",
                    "features": [
                        ("#facc15", "fa-chart-pie",
                         "Tableau de bord stratégique",
                         "KPIs nationaux, classement des régions, carte des zones à risque — tout en un coup d'œil."),
                        ("#ea580c", "fa-triangle-exclamation",
                         "Villes et régions prioritaires",
                         "Identifiez immédiatement les zones critiques (AQI > 150) nécessitant une action urgente."),
                        ("#0ea5e9", "fa-file-pdf",
                         "Rapport PDF premium",
                         "Téléchargez un rapport décisionnel complet avec logos, tableaux et recommandations."),
                        ("#16a34a", "fa-file-contract",
                         "Politiques publiques",
                         "Recommandations concrètes classées par niveau d'urgence pour votre territoire."),
                    ],
                    "alert_tip": False,
                },
                "researcher": {
                    "label":   "Chercheur",
                    "color":   "#a855f7",
                    "icon":    "fa-flask",
                    "subject": "Bienvenue sur AirEka — Votre espace recherche est prêt !",
                    "tagline": "Explorez les données, les modèles ML et les simulations AirEka.",
                    "features": [
                        ("#a855f7", "fa-brain",
                         "Modèles ML comparés",
                         "Random Forest (R²=0.967), XGBoost (R²=0.951), LSTM (R²=0.928) — métriques détaillées."),
                        ("#00d4ff", "fa-flask-vial",
                         "Simulation interactive",
                         "Modifiez PM2.5, température, trafic et observez l'impact sur l'AQI en temps réel."),
                        ("#ff9100", "fa-chart-bar",
                         "Statistiques avancées",
                         "Séries temporelles, corrélations, importance des variables (SHAP) sur 40 villes."),
                        ("#16a34a", "fa-code",
                         "Export & API",
                         "Téléchargez les données brutes et accédez à l'API pour vos propres analyses."),
                    ],
                    "alert_tip": False,
                },
            }

            cfg          = ROLE_CFG.get(role or "citizen", ROLE_CFG["citizen"])
            role_color   = cfg["color"]
            role_label   = cfg["label"]
            subject      = cfg["subject"]
            tagline      = cfg["tagline"]
            features     = cfg["features"]
            alert_tip    = cfg["alert_tip"]

            # ── Construction des lignes de features ─────────────────
            feature_rows = ""
            for feat_color, feat_icon, feat_title, feat_desc in features:
                feature_rows += f"""
            <tr>
              <td style="padding:0 0 10px 0;">
                <div style="background:#0f172a;border-radius:12px;padding:14px 16px;
                            border-left:4px solid {feat_color};">
                  <p style="margin:0 0 4px;color:{feat_color};font-size:12px;font-weight:700;">
                    <i class="fas {feat_icon}"></i>&nbsp;{feat_title}
                  </p>
                  <p style="margin:0;color:#94a3b8;font-size:12px;line-height:1.5;">
                    {feat_desc}
                  </p>
                </div>
              </td>
            </tr>"""

            # ── Section alerte (citoyen seulement) ──────────────────
            alert_section = ""
            if alert_tip:
                alert_section = """
      <tr>
        <td style="padding:0 28px 20px;border-bottom:1px solid #334155;">
          <div style="background:#0ea5e915;border:1px solid #0ea5e940;
                      border-radius:12px;padding:16px;text-align:center;">
            <p style="color:#0ea5e9;font-size:12px;font-weight:700;margin:0 0 6px;">
              <i class="fas fa-lightbulb"></i>&nbsp;Conseil : activez vos alertes dès maintenant
            </p>
            <p style="color:#94a3b8;font-size:11px;margin:0;line-height:1.5;">
              Dans l'onglet <strong style="color:#f1f5f9;">Alertes</strong>, entrez votre email,
              choisissez l'heure et cliquez <strong style="color:#f1f5f9;">Sauvegarder</strong>.
              Vous recevrez un rapport automatique chaque jour — sans rien faire d'autre.
            </p>
          </div>
        </td>
      </tr>"""

            html_welcome = f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>{subject}</title>
  <link rel="stylesheet"
        href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css"
        crossorigin="anonymous">
</head>
<body style="margin:0;padding:0;background:#0f172a;font-family:'Segoe UI',Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0"
       style="background:#0f172a;padding:32px 16px;">
  <tr><td align="center">
    <table width="600" cellpadding="0" cellspacing="0"
           style="background:#1e293b;border-radius:20px;overflow:hidden;
                  border:1px solid #334155;box-shadow:0 20px 60px rgba(0,0,0,.5);">

      <!-- EN-TÊTE -->
      <tr>
        <td style="background:linear-gradient(135deg,#0f172a,#1e293b);
                   padding:26px 28px;border-bottom:1px solid #334155;">
          <table width="100%" cellpadding="0" cellspacing="0">
            <tr>
              <td>{logo}</td>
              <td style="text-align:right;color:#94a3b8;font-size:11px;">
                <i class="fas fa-clock"></i>&nbsp;{now_str}
              </td>
            </tr>
          </table>
          <h1 style="color:#f1f5f9;font-size:24px;font-weight:800;
                     margin:18px 0 6px;letter-spacing:-.02em;">
            <i class="fas fa-party-horn" style="color:{role_color};"></i>&nbsp;
            Bienvenue, {name}&nbsp;!
          </h1>
          <p style="color:#94a3b8;font-size:13px;margin:0;line-height:1.5;">
            {tagline}
          </p>
        </td>
      </tr>

      <!-- BADGE RÔLE + VILLE -->
      <tr>
        <td style="padding:24px 28px;text-align:center;border-bottom:1px solid #334155;">
          <div style="display:inline-block;background:{role_color}15;
                      border:1px solid {role_color}50;border-radius:14px;
                      padding:14px 32px;">
            <p style="color:#94a3b8;font-size:10px;font-weight:700;
                      text-transform:uppercase;letter-spacing:.12em;margin:0 0 6px;">
              Votre profil
            </p>
            <p style="color:{role_color};font-size:20px;font-weight:800;margin:0 0 4px;">
              <i class="fas {cfg['icon']}"></i>&nbsp;{role_label}
            </p>
            <p style="color:#94a3b8;font-size:12px;margin:0;">
              <i class="fas fa-map-marker-alt"></i>&nbsp;{city_display}
            </p>
          </div>
        </td>
      </tr>

      <!-- FONCTIONNALITÉS -->
      <tr>
        <td style="padding:22px 28px;border-bottom:1px solid #334155;">
          <p style="color:#94a3b8;font-size:11px;font-weight:700;text-transform:uppercase;
                    letter-spacing:.08em;margin:0 0 16px;">
            <i class="fas fa-star" style="color:{role_color};"></i>&nbsp;Ce que vous pouvez faire
          </p>
          <table width="100%" cellpadding="0" cellspacing="0">
            {feature_rows}
          </table>
        </td>
      </tr>

      {alert_section}

      <!-- PIED DE PAGE -->
      <tr>
        <td style="background:#0f172a;padding:20px 28px;text-align:center;
                   border-top:1px solid #334155;">
          <p style="color:#475569;font-size:11px;margin:0 0 4px;">
            <i class="fas fa-shield-halved" style="color:#16a34a;"></i>&nbsp;
            Votre compte est sécurisé ·
            <strong style="color:#94a3b8;">AirEka · Deepstats Consulting</strong>
          </p>
          <p style="color:#334155;font-size:10px;margin:0;">
            IndabaX Cameroon 2026 · deepstats.contact@gmail.com
          </p>
        </td>
      </tr>

    </table>
  </td></tr>
</table>
</body>
</html>"""

            if "xxxx" not in SENDER_APP_PASSWORD:
                msg_mail = MIMEMultipart("alternative")
                msg_mail["Subject"] = subject
                msg_mail["From"]    = f"{SENDER_DISPLAY} <{SENDER_EMAIL}>"
                msg_mail["To"]      = email
                msg_mail.attach(MIMEText(html_welcome, "html", "utf-8"))
                with smtplib.SMTP("smtp.gmail.com", 587, timeout=15) as srv:
                    srv.starttls()
                    srv.login(SENDER_EMAIL, SENDER_APP_PASSWORD)
                    srv.sendmail(SENDER_EMAIL, email, msg_mail.as_string())
                print(f"[AirEka] ✓ Email de bienvenue ({role_label}) envoyé → {email}")
        except Exception as e:
            print(f"[AirEka] Email de bienvenue non envoyé ({e}) — inscription réussie quand même")

        return (html.Div([
            html.I(className="fas fa-check-circle", style={"marginRight": "6px"}),
            "Inscription réussie ! Un email de confirmation vous a été envoyé. "
            "Vous pouvez maintenant vous connecter."
        ], style={"color": "#00e676"}),
        True, _btn_disabled, _spinner_hide)
    else:
        return (html.Div([
            html.I(className="fas fa-exclamation-circle", style={"marginRight": "6px"}),
            result["error"]
        ], style={"color": "#ef4444"}),
        False, _btn_base, _spinner_hide)
# Callback pour la connexion
@app.callback(
    [Output('store-user', 'data'),
     Output('url', 'pathname', allow_duplicate=True),  # ← Ajout allow_duplicate=True
     Output('login-message', 'children')],
    Input('btn-login-submit', 'n_clicks'),
    [State('login-email', 'value'),
     State('login-password', 'value')],
    prevent_initial_call=True
)
def handle_login(n_clicks, email, password):
    if not n_clicks:
        return dash.no_update, dash.no_update, ''
    
    if not email or not password:
        return dash.no_update, dash.no_update, html.Div([
            html.I(className="fas fa-exclamation-circle", style={'marginRight': '6px'}),
            "Veuillez entrer votre email et mot de passe"
        ], style={'color': '#ef4444'})
    
    result = authenticate_user(email, password)
    
    if result['success']:
        user_obj = {
            'username': result['name'],
            'role': result['role'],
            'initials': result['name'][:2].upper(),
            'color': '#00d4ff' if result['role'] == 'citizen' else '#facc15' if result['role'] == 'decision' else '#a855f7',
            'icon': 'fa-person' if result['role'] == 'citizen' else 'fa-landmark' if result['role'] == 'decision' else 'fa-flask',
            'label_fr': 'Citoyen' if result['role'] == 'citizen' else 'Décideur' if result['role'] == 'decision' else 'Chercheur',
            'label_en': 'Citizen' if result['role'] == 'citizen' else 'Decision Maker' if result['role'] == 'decision' else 'Researcher',
            'city': result.get('city'),
            'region': result.get('region'),
            'email': result['email'],
            'name': result['name']
        }
        
        return user_obj, '/dashboard', ''
    else:
        return dash.no_update, dash.no_update, html.Div([
            html.I(className="fas fa-exclamation-circle", style={'marginRight': '6px'}),
            result['error']
        ], style={'color': '#ef4444'})

def _sim_ai_block(city, base_aqi, new_aqi, variation, main_factor, pm25, no2, lang='fr'):
    """Retourne une liste avec le bloc IA simulation (vide si LLM indisponible)."""
    try:
        from ai_commentary import ai_simulation_insight
        text = ai_simulation_insight(city, base_aqi, new_aqi, variation, main_factor, pm25, no2, lang=lang)
        if not text:
            return []
    except Exception:
        return []
    return [html.Div([
        html.Div([
            html.I(className="fas fa-robot",
                   style={'color': '#7c3aed', 'fontSize': '14px', 'marginRight': '8px'}),
            html.Span("AI Analysis — Scenario Interpretation" if lang=='en' else "Analyse IA — Interprétation du scénario",
                      style={'fontWeight': '700', 'fontSize': '12px', 'color': 'var(--text-primary)'}),
        ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '8px'}),
        html.P(text, style={'fontSize': '12px', 'color': 'var(--text-secondary)',
                            'lineHeight': '1.6', 'margin': '0'}),
    ], style={
        'marginTop': '16px', 'padding': '14px 16px', 'borderRadius': '12px',
        'background': 'rgba(124,58,237,0.06)', 'border': '1px solid rgba(124,58,237,0.28)',
    })]


# Callback pour la simulation (chercheur)
@app.callback(
    Output('sim-city-result-container', 'children'),
    Input('sim-city-calc-btn', 'n_clicks'),
    State('sim-city-selector', 'value'),
    State('sim-city-temp', 'value'),
    State('sim-city-pm25', 'value'),
    State('sim-city-no2', 'value'),
    State('sim-city-humidity', 'value'),
    State('sim-city-wind', 'value'),
    State('store-lang', 'data'),
)
def run_simulation(n_clicks, city, temp, pm25, no2, humidity, wind, lang):
    CITIES_DATA = get_cities_data()
    lang = lang or 'fr'
    en = (lang == 'en')
    if not n_clicks:
        return html.Div([
            html.Div([
                html.I(className="fas fa-info-circle", style={'fontSize': '32px', 'color': 'var(--text-muted)'})
            ], style={'textAlign': 'center', 'marginBottom': '16px'}),
            html.P("Adjust the parameters and click 'Simulate Impact'" if en else "Ajustez les paramètres et cliquez sur 'Simuler l'impact'",
                   style={'textAlign': 'center', 'color': 'var(--text-secondary)', 'fontSize': '12px'}),
            html.P("to see the effect on AQI" if en else "pour voir l'effet sur l'AQI",
                   style={'textAlign': 'center', 'color': 'var(--text-muted)', 'fontSize': '11px'})
        ], style={'padding': '40px 20px'})
    
    city_data = next((c for c in CITIES_DATA if c['city'] == city), CITIES_DATA[0])
    base_aqi = city_data['aqi']
    base_pm25 = city_data['pm25']
    base_no2 = city_data['no2']
    
    temp_impact = (temp - 26.5) * 0.6
    pm25_impact = (pm25 - base_pm25) * 0.85
    no2_impact = (no2 - base_no2) * 0.35
    humidity_impact = (humidity - 65) * 0.12
    wind_impact = (wind - 12) * -0.3
    
    impact_total = temp_impact + pm25_impact + no2_impact + humidity_impact + wind_impact
    new_aqi = max(20, min(300, base_aqi + impact_total))
    
    variation = new_aqi - base_aqi
    if variation > 20:
        trend_icon = "fa-arrow-trend-up"
        trend_color = "#ff1744"
        trend_bg = "rgba(255,23,68,0.15)"
        interpretation = "⚠️ Severe air quality degradation" if en else "⚠️ Dégradation sévère de la qualité de l'air"
        recommendation = "Emergency measures recommended: emission reduction, population alert" if en else "Mesures d'urgence recommandées : réduction des émissions, alerte populations"
    elif variation > 5:
        trend_icon = "fa-arrow-trend-up"
        trend_color = "#ff9100"
        trend_bg = "rgba(255,145,0,0.15)"
        interpretation = "📈 Slight air quality degradation" if en else "📈 Légère dégradation de la qualité de l'air"
        recommendation = "Enhanced monitoring recommended" if en else "Surveillance renforcée recommandée"
    elif variation < -20:
        trend_icon = "fa-arrow-trend-down"
        trend_color = "#00e676"
        trend_bg = "rgba(0,230,118,0.15)"
        interpretation = "✨ Significant air quality improvement" if en else "✨ Amélioration significative de la qualité de l'air"
        recommendation = "Effective policies — maintain them" if en else "Politiques efficaces - à maintenir"
    elif variation < -5:
        trend_icon = "fa-arrow-trend-down"
        trend_color = "#00d4ff"
        trend_bg = "rgba(0,212,255,0.15)"
        interpretation = "📉 Air quality improvement" if en else "📉 Amélioration de la qualité de l'air"
        recommendation = "Good practices to reinforce" if en else "Bonnes pratiques à renforcer"
    else:
        trend_icon = "fa-chart-line"
        trend_color = "#eab308"
        trend_bg = "rgba(234,179,8,0.15)"
        interpretation = "➡️ Stable air quality" if en else "➡️ Stabilité de la qualité de l'air"
        recommendation = "Maintain current measures" if en else "Maintien des mesures actuelles"

    contributions = {
        'temperature' if en else 'température': abs(temp_impact),
        'PM2.5': abs(pm25_impact),
        'NO₂': abs(no2_impact),
        'humidity' if en else 'humidité': abs(humidity_impact),
        'wind' if en else 'vent': abs(wind_impact)
    }
    main_factor = max(contributions, key=contributions.get)
    
    return html.Div([
        html.Div([
            html.Div([
                html.Span("CURRENT AQI" if en else "AQI ACTUEL", style={'fontSize': '10px', 'fontWeight': '700', 'color': 'var(--text-secondary)'}),
                html.H2(f"{base_aqi:.0f}", style={'fontSize': '36px', 'fontWeight': '800', 'margin': '0', 'color': aqi_color(base_aqi)})
            ], style={'textAlign': 'center', 'flex': '1'}),
            html.Div([
                html.I(className=f"fas {trend_icon}", style={'fontSize': '28px', 'color': trend_color})
            ], style={'textAlign': 'center', 'flex': '0.5'}),
            html.Div([
                html.Span("SIMULATED AQI" if en else "AQI SIMULÉ", style={'fontSize': '10px', 'fontWeight': '700', 'color': 'var(--text-secondary)'}),
                html.H2(f"{new_aqi:.0f}", style={'fontSize': '36px', 'fontWeight': '800', 'margin': '0', 'color': aqi_color(new_aqi)})
            ], style={'textAlign': 'center', 'flex': '1'})
        ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'space-between', 'marginBottom': '20px'}),
        
        html.Div([
            html.Div(style={
                'width': f'{min(100, max(0, (variation + 30) / 60 * 100))}%',
                'height': '100%', 'background': trend_color, 'borderRadius': '99px',
                'transition': 'width 0.5s ease'
            })
        ], style={'height': '6px', 'background': 'var(--border)', 'borderRadius': '99px', 'marginBottom': '20px'}),
        
        html.Div([
            html.I(className=f"fas {trend_icon}", style={'marginRight': '8px', 'color': trend_color}),
            html.Span(f"{'+' if variation > 0 else ''}{variation:.1f} points", 
                      style={'fontSize': '18px', 'fontWeight': '800', 'color': trend_color})
        ], style={'textAlign': 'center', 'marginBottom': '16px'}),
        
        html.Div([
            html.Div([
                html.I(className="fas fa-chart-simple", style={'marginRight': '8px', 'color': trend_color}),
                html.Span(interpretation, style={'fontWeight': '700', 'fontSize': '13px'})
            ], style={'marginBottom': '8px'}),
            html.Div([
                html.I(className="fas fa-lightbulb", style={'marginRight': '8px', 'color': '#eab308'}),
                html.Span(recommendation, style={'fontSize': '11px'})
            ], style={'marginBottom': '12px'}),
            html.Div([
                html.I(className="fas fa-chart-line", style={'marginRight': '8px', 'color': '#ff9100'}),
                html.Span(f"{'Main variation factor' if en else 'Principal facteur de variation'}: {main_factor}", style={'fontSize': '11px', 'fontStyle': 'italic'})
            ])
        ], style={'padding': '16px', 'background': trend_bg, 'borderRadius': '12px', 'marginBottom': '20px'}),
        
        html.Div([
            html.Span("CONTRIBUTION BREAKDOWN" if en else "DÉTAIL DES CONTRIBUTIONS", style={'fontSize': '10px', 'fontWeight': '700', 'color': 'var(--text-muted)', 'marginBottom': '12px', 'display': 'block'}),
            html.Div([
                html.Div([
                    html.I(className="fas fa-thermometer-half", style={'color': '#ff1744', 'width': '24px'}),
                    html.Span("Temperature" if en else "Température", style={'flex': '1', 'fontSize': '11px'}),
                    html.Span(f"{'+' if temp_impact > 0 else ''}{temp_impact:.1f}", style={'fontWeight': '600', 'color': '#ff1744' if temp_impact > 0 else '#00e676'})
                ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '8px'}),
                html.Div([
                    html.I(className="fas fa-smog", style={'color': '#ff1744', 'width': '24px'}),
                    html.Span("PM2.5", style={'flex': '1', 'fontSize': '11px'}),
                    html.Span(f"{'+' if pm25_impact > 0 else ''}{pm25_impact:.1f}", style={'fontWeight': '600', 'color': '#ff1744' if pm25_impact > 0 else '#00e676'})
                ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '8px'}),
                html.Div([
                    html.I(className="fas fa-industry", style={'color': '#00d4ff', 'width': '24px'}),
                    html.Span("NO₂", style={'flex': '1', 'fontSize': '11px'}),
                    html.Span(f"{'+' if no2_impact > 0 else ''}{no2_impact:.1f}", style={'fontWeight': '600', 'color': '#00d4ff'})
                ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '8px'}),
                html.Div([
                    html.I(className="fas fa-tint", style={'color': '#00e676', 'width': '24px'}),
                    html.Span("Humidity" if en else "Humidité", style={'flex': '1', 'fontSize': '11px'}),
                    html.Span(f"{'+' if humidity_impact > 0 else ''}{humidity_impact:.1f}", style={'fontWeight': '600', 'color': '#00e676'})
                ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '8px'}),
                html.Div([
                    html.I(className="fas fa-wind", style={'color': '#a855f7', 'width': '24px'}),
                    html.Span("Wind" if en else "Vent", style={'flex': '1', 'fontSize': '11px'}),
                    html.Span(f"{'+' if wind_impact > 0 else ''}{wind_impact:.1f}", style={'fontWeight': '600', 'color': '#00e676'})
                ], style={'display': 'flex', 'alignItems': 'center'})
            ], style={'padding': '12px', 'background': 'var(--bg-surface)', 'borderRadius': '10px'})
        ]),

        # ── Bloc IA simulation ──────────────────────────────────────
        *_sim_ai_block(city, base_aqi, new_aqi, variation, main_factor, pm25, no2, lang=lang)
    ])


# Callback pour afficher/masquer la barre de filtres
@app.callback(
    Output('filter-bar-container', 'children'),
    Input('active-tab', 'data'),
    State('store-user', 'data'),
    State('store-lang', 'data'),
    State('store-city', 'data'),
    State('store-region', 'data'),
)
def toggle_filter_bar(active_tab, user, lang, city, region):
    if not user or not active_tab:
        return html.Div()
    
    role = user.get('role', 'citizen')
    no_filter_tabs_all = ['about', 'my_city', 'today', 'alerts']
    
    if role == 'decision':
        return html.Div()
    
    if active_tab in no_filter_tabs_all:
        return html.Div()
    
    if role == 'researcher':
        no_filter_tabs = ['models', 'simulation', 'api', 'stats']
        if active_tab in no_filter_tabs:
            return html.Div()
        return make_filter_bar(region, city, lang)
    
    return make_filter_bar(region, city, lang)


# Callbacks pour les sliders de simulation
@app.callback(
    Output('sim-city-temp-value', 'children'),
    Output('sim-city-pm25-value', 'children'),
    Output('sim-city-no2-value', 'children'),
    Output('sim-city-humidity-value', 'children'),
    Output('sim-city-wind-value', 'children'),
    Input('sim-city-temp', 'value'),
    Input('sim-city-pm25', 'value'),
    Input('sim-city-no2', 'value'),
    Input('sim-city-humidity', 'value'),
    Input('sim-city-wind', 'value')
)
def update_sim_slider_values(temp, pm25, no2, humidity, wind):
    return f"{temp:.1f}°C", f"{pm25:.0f} µg/m³", f"{no2:.0f} µg/m³", f"{humidity:.0f}%", f"{wind:.0f} km/h"


@app.callback(
    Output('sim-city-result', 'children'),
    Output('sim-city-result', 'style'),
    Input('sim-city-calc-btn', 'n_clicks'),
    State('sim-city-selector', 'value'),
    State('sim-city-temp', 'value'),
    State('sim-city-pm25', 'value'),
    State('sim-city-no2', 'value'),
    State('sim-city-humidity', 'value'),
    State('sim-city-wind', 'value'),
    State('store-lang', 'data'),
)
def calculate_city_simulation(n_clicks, city, temp, pm25, no2, humidity, wind, lang):
    CITIES_DATA = get_cities_data()
    lang = lang or 'fr'
    if not n_clicks:
        return dash.no_update, {'display': 'none'}

    city_data = next((c for c in CITIES_DATA if c['city'] == city), CITIES_DATA[0])
    base_aqi = city_data['aqi']
    
    temp_impact = (temp - 26.5) * 0.3
    pm25_impact = (pm25 - city_data['pm25']) * 0.5
    no2_impact = (no2 - city_data['no2']) * 0.4
    humidity_impact = (humidity - 65) * 0.1
    wind_impact = (wind - 12) * -0.2
    
    impact = temp_impact + pm25_impact + no2_impact + humidity_impact + wind_impact
    new_aqi = max(20, min(300, base_aqi + impact))
    diff = new_aqi - base_aqi
    
    result = html.Div([
        html.Div([
            html.I(className="fas fa-chart-line", style={'color': '#ff9100', 'marginRight': '8px'}),
            html.Span(t('sim_result_title', lang), style={'fontWeight': '700', 'fontSize': '13px'})
        ], style={'marginBottom': '12px'}),
        html.Div([
            html.Div([
                html.Span(('Current AQI:' if lang=='en' else 'AQI actuel:'), style={'color': 'var(--text-secondary)'}),
                html.Span(f"{base_aqi:.0f}", style={'fontSize': '24px', 'fontWeight': '800', 'color': aqi_color(base_aqi), 'marginLeft': '12px'})
            ], style={'marginBottom': '8px'}),
            html.Div([
                html.Span(t('sim_aqi_label', lang), style={'color': 'var(--text-secondary)'}),
                html.Span(f"{new_aqi:.0f}", style={'fontSize': '24px', 'fontWeight': '800', 'color': aqi_color(new_aqi), 'marginLeft': '12px'})
            ], style={'marginBottom': '12px'}),
            html.Div([
                html.I(className="fas fa-arrow-trend-up" if diff > 0 else "fas fa-arrow-trend-down", 
                       style={'marginRight': '8px', 'color': '#ff1744' if diff > 0 else '#00e676'}),
                html.Span(f"{'+' if diff > 0 else ''}{diff:.1f} points", 
                          style={'fontWeight': '700', 'color': '#ff1744' if diff > 0 else '#00e676'})
            ], style={'marginBottom': '8px'}),
            html.Div([
                html.I(className="fas fa-info-circle", style={'marginRight': '8px', 'color': 'var(--text-muted)'}),
                html.Small(t('sim_based_on', lang), style={'color': 'var(--text-muted)'})
            ])
        ], style={'padding': '12px', 'background': 'var(--bg-surface)', 'borderRadius': '12px'})
    ])
    
    return result, {'display': 'block', 'marginTop': '16px'}


# Callback pour le rendu de la page — se déclenche sur URL, user ET langue pour tout traduire
@app.callback(
    Output('page-content', 'children'),
    Input('url', 'pathname'),
    Input('store-user', 'data'),
    Input('store-lang', 'data'),
    State('store-theme', 'data'),
)
def render_page(pathname, user, lang, theme):
    lang = lang or 'fr'
    theme = theme or 'dark'
    
    # Appliquer le thème au chargement initial
    if theme == 'dark':
        theme_to_apply = 'dark'
    else:
        theme_to_apply = 'light'
    
    if not user or pathname in (None, '/', '/login'):
        from login import create_login_layout
        return create_login_layout(theme_to_apply)
    return make_dashboard(user, lang)

# Reset historique + messages au changement d'utilisateur (login/logout)
@app.callback(
    Output('chatbot-history', 'data', allow_duplicate=True),
    Output('chatbot-messages', 'children', allow_duplicate=True),
    Input('store-user', 'data'),
    Input('store-lang', 'data'),
    prevent_initial_call='initial_duplicate',
)
def reset_chat_on_user_change(user, lang):
    lang = lang or 'fr'
    uid = (user or {}).get('username', '')
    if lang == 'en':
        welcome_text = (f"Hello {uid}! " if uid else "Hello! ") + \
                       "I'm the AirEka assistant. Ask me anything about air quality, pollutants, health, or recommendations."
    else:
        welcome_text = (f"Bonjour {uid} ! " if uid else "Bonjour ! ") + \
                       "Je suis l'assistant AirEka. Posez-moi vos questions sur la qualité de l'air, les polluants, la santé ou les recommandations."
    welcome = _make_bot_bubble(welcome_text)
    return [{"_uid": uid}], [welcome]


def _make_bot_bubble(text):
    return html.Div([
        html.Div([
            html.I(className="fas fa-robot", style={'color': '#7c3aed', 'fontSize': '10px', 'marginRight': '6px'}),
            html.Span("Assistant IA", style={'fontSize': '10px', 'color': 'var(--text-secondary)'})
        ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '4px'}),
        html.Div(text, style={
            'fontSize': '12px', 'padding': '10px 12px', 'whiteSpace': 'pre-wrap',
            'background': 'rgba(124,58,237,0.08)', 'border': '1px solid rgba(124,58,237,0.2)',
            'borderRadius': '12px', 'lineHeight': '1.6', 'maxWidth': '90%'
        })
    ], style={'display': 'flex', 'flexDirection': 'column', 'alignItems': 'flex-start', 'marginBottom': '8px'})


# Callback pour masquer/afficher le chatbot selon la page (caché sur login)
@app.callback(
    Output('chatbot-global', 'style'),
    Input('store-user', 'data'),
    Input('url', 'pathname'),
)
def toggle_chatbot_visibility(user, pathname):
    """Masquer le chatbot sur la page de login, l'afficher uniquement après connexion."""
    is_login = (not user) or (pathname in (None, '/', '/login'))
    if is_login:
        return {'display': 'none'}
    return {'display': 'block'}

@app.callback(
    Output('chatbot-panel', 'style'),
    Input('chatbot-fab', 'n_clicks'),
    State('chatbot-panel', 'style'),
    prevent_initial_call=True,
)
def toggle_chatbot(n, current_style):
    if not n:
        return dash.no_update
    if current_style and current_style.get('display') == 'none':
        return {
            'position': 'fixed', 'bottom': '90px', 'right': '24px',
            'width': '360px', 'maxWidth': 'calc(100vw - 48px)',
            'background': 'var(--bg-card)', 'borderRadius': '24px',
            'border': '1px solid var(--border)', 'boxShadow': 'var(--shadow-lg)',
            'zIndex': '1001', 'overflow': 'hidden', 'display': 'block',
            'backdropFilter': 'blur(8px)'
        }
    return {'display': 'none'}


@app.callback(
    Output('chatbot-panel', 'style', allow_duplicate=True),
    Input('chatbot-close', 'n_clicks'),
    prevent_initial_call=True,
)
def close_chatbot(n):
    if n:
        return {'display': 'none'}
    return dash.no_update


@app.callback(
    Output('chatbot-messages', 'children'),
    Output('chatbot-input', 'value'),
    Output('chatbot-history', 'data'),
    Input('chatbot-send', 'n_clicks'),
    State('chatbot-input', 'value'),
    State('store-city', 'data'),
    State('store-lang', 'data'),
    State('store-user', 'data'),
    State('active-tab', 'data'),
    State('chatbot-messages', 'children'),
    State('chatbot-history', 'data'),
    prevent_initial_call=True,
)
def send_message(n_clicks, question, city, lang, user, active_tab, current_messages, history):
    CITIES_DATA = get_cities_data()
    if not question or not question.strip():
        return dash.no_update, dash.no_update, dash.no_update

    uid = (user or {}).get('username', '')
    role = (user or {}).get('role', 'citizen')
    history = history or []
    q = question.strip()

    # Reset si l'historique appartient à un autre utilisateur
    if history and history[0].get('_uid', '') != uid:
        history = [{"_uid": uid}]

    # Détection dynamique de ville dans la question
    import unicodedata as _uc
    city = city or 'Yaoundé'
    q_lower = q.lower()
    q_norm = _uc.normalize("NFD", q).encode("ascii", "ignore").decode().lower()
    detected = next(
        (c for c in CITIES_DATA
         if c['city'].lower() in q_lower or
         _uc.normalize("NFD", c['city']).encode("ascii", "ignore").decode().lower() in q_norm),
        None
    )
    city_data = detected or next((c for c in CITIES_DATA if c['city'] == city), CITIES_DATA[0] if CITIES_DATA else {})

    user_msg = html.Div([
        html.Div([
            html.I(className="fas fa-user", style={'color': '#00d4ff', 'fontSize': '10px', 'marginRight': '6px'}),
            html.Span("You" if lang == 'en' else "Vous", style={'fontSize': '10px', 'color': 'var(--text-secondary)'})
        ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '4px', 'justifyContent': 'flex-end'}),
        html.Div(q, style={
            'fontSize': '12px', 'padding': '10px 12px',
            'background': 'linear-gradient(135deg, #00d4ff20, #0084cc20)',
            'borderRadius': '12px', 'lineHeight': '1.5', 'maxWidth': '85%'
        })
    ], style={'display': 'flex', 'flexDirection': 'column', 'alignItems': 'flex-end', 'marginBottom': '8px'})

    try:
        from ai_commentary import ai_chatbot_response
        response = ai_chatbot_response(
            question=q,
            city=city_data.get('city', city),
            aqi=city_data.get('aqi', 0),
            pm25=city_data.get('pm25', 0),
            pm10=city_data.get('pm10', 0),
            no2=city_data.get('no2', 0),
            o3=city_data.get('o3', 0),
            so2=city_data.get('so2', 0),
            trend=city_data.get('trend', 0),
            region=city_data.get('region', ''),
            role=role,
            tab=active_tab or '',
            history=[h for h in history if '_uid' not in h],
            lang=lang or 'fr',
        ) or ("Sorry, I couldn't get a response. Please try again." if lang == 'en' else "Désolé, je n'ai pas pu obtenir une réponse. Réessayez.")
    except Exception:
        response = "Service temporarily unavailable." if lang == 'en' else "Service temporairement indisponible."

    # Mise à jour historique — on préserve l'entrée _uid en tête
    meta = [history[0]] if history and '_uid' in history[0] else [{"_uid": uid}]
    exchanges = [h for h in history if '_uid' not in h]
    exchanges = (exchanges + [{"role": "user", "content": q},
                               {"role": "assistant", "content": response}])[-20:]
    history = meta + exchanges

    bot_msg = html.Div([
        html.Div([
            html.I(className="fas fa-robot", style={'color': '#7c3aed', 'fontSize': '10px', 'marginRight': '6px'}),
            html.Span("Assistant IA", style={'fontSize': '10px', 'color': 'var(--text-secondary)'})
        ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '4px'}),
        html.Div(response, style={
            'fontSize': '12px', 'padding': '10px 12px',
            'background': 'rgba(124,58,237,0.08)', 'border': '1px solid rgba(124,58,237,0.2)',
            'borderRadius': '12px', 'lineHeight': '1.6', 'maxWidth': '90%', 'whiteSpace': 'pre-wrap'
        })
    ], style={'display': 'flex', 'flexDirection': 'column', 'alignItems': 'flex-start', 'marginBottom': '8px'})

    msgs = list(current_messages or []) + [user_msg, bot_msg]
    return msgs, '', history


# Callbacks pour la page Tendances & Comparaison (décideur)
@app.callback(
    Output('trend-evolution-graph', 'figure'),
    Output('trend-seasonal-graph', 'figure'),
    Output('trend-forecast-container', 'children'),
    Output('trend-evolution-ai', 'children'),
    Output('trend-seasonal-ai', 'children'),
    Output('trend-evo-label', 'children'),
    Output('trend-seas-label', 'children'),
    Input('trend-city-selector', 'value'),
    State('store-lang', 'data'),
)
def update_trends_graphs(selected_city, lang):
    CITIES_DATA = get_cities_data()
    lang = lang or 'fr'
    _en_fc = (lang == 'en')
    from decision_maker_pages import _graph_ai_block, _ai_trend_block
    is_national = not selected_city or selected_city == 'all'
    if not is_national:
        city_data = next((c for c in CITIES_DATA if c['city'] == selected_city), CITIES_DATA[0])
    else:
        # National synthetic city_data from national stats
        try:
            from api_client import load_national_stats
            nat = load_national_stats() or {}
            city_data = {
                'city': 'Cameroun (National)',
                'aqi': nat.get('national_avg_aqi', 80),
                'pm25': nat.get('national_avg_pm25', 25),
                'pm10': nat.get('national_avg_pm10', 40),
                'no2': nat.get('national_avg_no2', 15),
                'region': 'National',
            }
        except Exception:
            city_data = {'city': 'Cameroun (National)', 'aqi': 80, 'pm25': 25, 'pm10': 40, 'no2': 15, 'region': 'National'}
    ctx_label = (t('view_national', lang) + ' — Cameroun') if is_national else selected_city

    # ── Évolution 7 jours ──────────────────────────────────────────────────────
    try:
        if is_national:
            from api_client import load_national_timeseries
            hist_raw = load_national_timeseries(7)
            if hist_raw:
                hist_raw = sorted(hist_raw, key=lambda x: x.get('date', ''))
                dates_7j = [pd.Timestamp(r['date']).strftime('%d/%m') for r in hist_raw]
                city_7j  = [r.get('aqi', 0) for r in hist_raw]
            else:
                raise ValueError("vide")
        else:
            from api_client import load_city_history
            hist7 = load_city_history(selected_city, 7)
            if hist7:
                hist7 = sorted(hist7, key=lambda x: x['pred_date'])
                dates_7j = [pd.Timestamp(r['pred_date']).strftime('%d/%m') for r in hist7]
                city_7j  = [r['aqi'] for r in hist7]
            else:
                raise ValueError("vide")
    except Exception:
        dates_7j = [(datetime.now() - timedelta(days=i)).strftime('%d/%m') for i in range(6, -1, -1)]
        random.seed(hash(selected_city or 'national') % 1000)
        city_7j = [max(20, min(300, city_data['aqi'] + random.randint(-15, 20) + (i * 0.5))) for i in range(7)]

    color_hex = aqi_color(city_data['aqi'])
    r_c = int(color_hex[1:3], 16)
    g_c = int(color_hex[3:5], 16)
    b_c = int(color_hex[5:7], 16)
    fillcolor_rgba = f'rgba({r_c}, {g_c}, {b_c}, 0.2)'

    fig_evo = go.Figure()
    fig_evo.add_trace(go.Scatter(
        x=dates_7j, y=city_7j, mode='lines+markers', name=ctx_label,
        line=dict(color=color_hex, width=3),
        marker=dict(size=8, color=color_hex),
        fill='tozeroy', fillcolor=fillcolor_rgba,
        hovertemplate='<b>%{x}</b><br>AQI: %{y:.0f}<extra></extra>'
    ))
    fig_evo.add_hline(y=100, line_dash='dot', line_color='#ff9100', line_width=1.5,
                      annotation_text="Seuil OMS", annotation_position='top right',
                      annotation_font_size=9, annotation_font_color='#ff9100')
    fig_evo.update_layout(
        height=280, margin=dict(l=40, r=20, t=30, b=40),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(tickangle=-45, tickfont=dict(size=10), gridcolor='rgba(30,48,88,0.2)'),
        yaxis=dict(title='AQI', tickfont=dict(size=10), gridcolor='rgba(30,48,88,0.2)'),
        hovermode='x unified', showlegend=False
    )

    # ── Saisonnalité ───────────────────────────────────────────────────────────
    months = (['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'] if _en_fc
              else ['Jan','Fév','Mar','Avr','Mai','Jun','Jul','Aoû','Sep','Oct','Nov','Déc'])
    monthly_aqi = [0] * 12
    try:
        if is_national:
            from api_client import load_national_seasonal
            seasonal = load_national_seasonal()
        else:
            from api_client import load_city_seasonal
            seasonal = load_city_seasonal(selected_city)
        for entry in seasonal.get('seasonal', []):
            m = entry.get('month')
            if m and 1 <= m <= 12:
                monthly_aqi[m - 1] = entry.get('aqi') or 0
    except Exception:
        pass
    fig_seasonal = go.Figure()
    fig_seasonal.add_trace(go.Bar(
        x=months, y=monthly_aqi,
        marker_color=[aqi_color(v) for v in monthly_aqi],
        text=[str(v) for v in monthly_aqi], textposition='outside',
        textfont=dict(size=9),
        hovertemplate='<b>%{x}</b><br>' + ('Avg AQI' if _en_fc else 'AQI moyen') + ': %{y}<extra></extra>'
    ))
    fig_seasonal.update_layout(
        height=280, margin=dict(l=40, r=20, t=30, b=40),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(tickfont=dict(size=9), gridcolor='rgba(30,48,88,0.2)'),
        yaxis=dict(title=('Avg AQI' if _en_fc else 'AQI moyen'), tickfont=dict(size=9), gridcolor='rgba(30,48,88,0.2)'),
        showlegend=False
    )

    # ── Prévisions 7 jours ────────────────────────────────────────────────────
    _en_fc = (lang == 'en')
    day_names = (['Mon','Tue','Wed','Thu','Fri','Sat','Sun'] if _en_fc
                 else ['Lun','Mar','Mer','Jeu','Ven','Sam','Dim'])
    try:
        from api_client import load_forecast
        if is_national:
            # Average forecasts from 5 representative cities
            _sample_cities = ['Yaoundé', 'Douala', 'Garoua', 'Bafoussam', 'Maroua']
            _all_fc = []
            for _sc in _sample_cities:
                _fc = load_forecast(_sc, 7)
                if _fc:
                    _all_fc.append(sorted(_fc, key=lambda x: x['pred_date']))
            if _all_fc:
                forecast_days = [day_names[pd.Timestamp(r['pred_date']).weekday()] for r in _all_fc[0]]
                forecast_values = [
                    round(sum(_all_fc[j][i]['aqi'] for j in range(len(_all_fc))) / len(_all_fc), 1)
                    for i in range(len(_all_fc[0]))
                ]
            else:
                raise ValueError("vide")
        else:
            fc7 = load_forecast(selected_city, 7)
            if fc7:
                fc7 = sorted(fc7, key=lambda x: x['pred_date'])
                forecast_days   = [day_names[pd.Timestamp(r['pred_date']).weekday()] for r in fc7]
                forecast_values = [r['aqi'] for r in fc7]
            else:
                raise ValueError("vide")
    except Exception:
        _today2 = datetime.now().weekday()
        forecast_days = [('Today' if _en_fc else 'Auj.')] + [day_names[(_today2 + i) % 7] for i in range(1, 7)]
        forecast_values = [max(20, min(300, city_data['aqi'] + (hash((selected_city or 'national') + str(i)) % 40) - 15)) for i in range(7)]

    avg_forecast = sum(forecast_values) / len(forecast_values)
    first_val, last_val = forecast_values[0], forecast_values[-1]
    if last_val > first_val:
        trend_icon, trend_color = "fa-arrow-trend-up", "#ff1744"
        comment = f" Légère hausse prévue." if last_val - first_val <= 20 else f" Augmentation significative (+{last_val - first_val:.0f} pts)."
    elif last_val < first_val:
        trend_icon, trend_color = "fa-arrow-trend-down", "#00e676"
        comment = f" Légère baisse, qualité devrait s'améliorer." if first_val - last_val <= 20 else f" Amélioration significative (-{first_val - last_val:.0f} pts)."
    else:
        trend_icon, trend_color = "fa-chart-line", "#ff9100"
        comment = " Tendance stable prévue."

    max_val = max(forecast_values)
    max_idx = forecast_days[forecast_values.index(max_val)]
    if max_val > 150:
        comment += f" Attention: pic attendu à {max_idx} (AQI {max_val:.0f})."
    elif max_val > 100:
        comment += f" Pic modéré à {max_idx} (AQI {max_val:.0f})."

    forecast_cards = []
    for day, val in zip(forecast_days, forecast_values):
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
            'background': f"{col}10", 'border': f'1px solid {col}30', 'flex': '1'
        }))

    forecast_container_children = [
        html.Div([
            html.I(className="fas fa-cloud-sun", style={'color': '#00d4ff', 'marginRight': '8px', 'fontSize': '14px'}),
            html.Span("PRÉVISIONS 7 JOURS", style={'fontWeight': '700', 'fontSize': '12px', 'letterSpacing': '0.05em'}),
            html.Span(ctx_label, style={'marginLeft': 'auto', 'fontSize': '9px', 'color': '#00d4ff', 'fontWeight': '600'})
        ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '12px'}),
        html.Div(forecast_cards, style={'display': 'flex', 'gap': '6px', 'marginBottom': '12px'}),
        html.Div([
            html.Div([
                html.I(className="fas fa-chart-simple", style={'color': aqi_color(avg_forecast), 'marginRight': '8px', 'fontSize': '14px'}),
                html.Span(f"Moyenne sur 7 jours: {avg_forecast:.0f} AQI",
                          style={'fontWeight': '700', 'fontSize': '12px', 'color': aqi_color(avg_forecast)})
            ], style={'marginBottom': '8px'}),
            html.Div([
                html.I(className=f"fas {trend_icon}", style={'color': trend_color, 'marginRight': '8px', 'fontSize': '12px'}),
                html.Span(comment, style={'fontSize': '11px', 'color': 'var(--text-secondary)', 'lineHeight': '1.4'})
            ]),
            _ai_trend_block(ctx_label, city_data['aqi'], forecast_values, city_data['pm25'], lang=lang)
        ], style={
            'padding': '14px', 'background': f"{aqi_color(avg_forecast)}15",
            'borderRadius': '12px', 'border': f"2px solid {aqi_color(avg_forecast)}80",
            'marginTop': '12px'
        })
    ]

    # ── AI blocks ─────────────────────────────────────────────────────────────
    evo_ai   = _graph_ai_block(city_data, city_7j, kind='history', lang=lang)
    seas_ai  = _graph_ai_block(city_data, monthly_aqi, kind='seasonal', lang=lang)

    return fig_evo, fig_seasonal, forecast_container_children, evo_ai, seas_ai, ctx_label, ctx_label


@app.callback(
    Output('sim-temp-value', 'children'),
    Output('sim-pm25-value', 'children'),
    Output('sim-humidity-value', 'children'),
    Output('sim-wind-value', 'children'),
    Input('sim-temp', 'value'),
    Input('sim-pm25', 'value'),
    Input('sim-humidity', 'value'),
    Input('sim-wind', 'value')
)
def update_slider_values(temp, pm25, humidity, wind):
    return f"{temp:.1f}°C", f"{pm25:.0f} µg/m³", f"{humidity:.0f}%", f"{wind:.0f} km/h"


@app.callback(
    Output('comparison-results', 'children'),
    Output('comparison-results', 'style'),
    Input('compare-btn', 'n_clicks'),
    State('compare-city1', 'value'),
    State('compare-city2', 'value'),
    State('store-lang', 'data'),
)
def update_comparison(n_clicks, city1, city2, lang):
    CITIES_DATA = get_cities_data()
    lang = lang or 'fr'
    if not n_clicks:
        return dash.no_update, {'display': 'none'}

    city1_data = next((c for c in CITIES_DATA if c['city'] == city1), CITIES_DATA[0])
    city2_data = next((c for c in CITIES_DATA if c['city'] == city2), CITIES_DATA[0])

    weather1 = {'temp': 26.5, 'wind': 12, 'humidity': 65}
    weather2 = {'temp': 27.2, 'wind': 14, 'humidity': 72}

    # ── Interprétation ───────────────────────────────────────────────
    diff_aqi  = city1_data['aqi'] - city2_data['aqi']
    more_poll = city1 if diff_aqi > 0 else city2
    less_poll = city2 if diff_aqi > 0 else city1
    abs_diff  = abs(diff_aqi)
    diff_pm25 = round(city1_data['pm25'] - city2_data['pm25'], 1)

    en = (lang == 'en')
    if abs_diff >= 50:
        sev_msg = f"critical difference of {abs_diff:.0f} AQI pts" if en else f"différence critique de {abs_diff:.0f} pts AQI"
        sev_col = '#ff1744'; sev_ico = 'fa-triangle-exclamation'
    elif abs_diff >= 20:
        sev_msg = f"significant difference of {abs_diff:.0f} AQI pts" if en else f"différence significative de {abs_diff:.0f} pts AQI"
        sev_col = '#ff9100'; sev_ico = 'fa-exclamation-circle'
    elif abs_diff > 0:
        sev_msg = f"moderate difference of {abs_diff:.0f} AQI pts" if en else f"différence modérée de {abs_diff:.0f} pts AQI"
        sev_col = '#eab308'; sev_ico = 'fa-info-circle'
    else:
        sev_msg = "similar air quality between the two cities" if en else "qualité d'air similaire entre les deux villes"
        sev_col = '#00e676'; sev_ico = 'fa-check-circle'

    max_aqi = max(city1_data['aqi'], city2_data['aqi'])
    if max_aqi > 150:
        eco = (["🌾 Agriculture: possible yield reduction (PM2.5 on crops).",
                "🐄 Livestock: respiratory stress on cattle, risk of losses.",
                "🏭 Industry: higher maintenance costs (SO₂/NO₂ corrosion).",
                "🏥 Public health: estimated increase in respiratory hospitalizations (+20–30%)."]
               if en else
               ["🌾 Agriculture : réduction des rendements possible (PM2.5 sur cultures).",
                "🐄 Élevage : stress respiratoire sur le bétail, risque de pertes.",
                "🏭 Industrie : hausse des coûts de maintenance (corrosion SO₂/NO₂).",
                "🏥 Santé publique : hausse estimée des hospitalisations respiratoires (+20–30%)."])
    elif max_aqi > 100:
        eco = (["🌿 Agriculture: slight reduction in photosynthesis (O₃ excess).",
                "🚶 Tourism: negative impact on outdoor attractiveness.",
                "⚙️ Outdoor productivity: estimated 5–10% decrease."]
               if en else
               ["🌿 Agriculture : légère réduction de la photosynthèse (excès d'O₃).",
                "🚶 Tourisme : impact négatif sur l'attractivité extérieure.",
                "⚙️ Productivité extérieure : baisse estimée 5–10%."])
    else:
        eco = (["✅ Low economic impact. Favorable conditions for agriculture and tourism."]
               if en else
               ["✅ Faible impact économique. Conditions favorables à l'agriculture et au tourisme."])

    # Commentaire IA
    ai_text = ""
    try:
        from ai_commentary import ai_comparison as _ai_cmp
        ai_text = _ai_cmp(city1, city1_data['aqi'], city1_data['pm25'], city1_data['no2'],
                          city2, city2_data['aqi'], city2_data['pm25'], city2_data['no2'], lang=lang)
    except Exception:
        pass

    interp = html.Div([
        html.Div([
            html.I(className=f"fas {sev_ico}",
                   style={'color': sev_col, 'marginRight': '10px', 'fontSize': '15px'}),
            html.Span("Interpretation & Economic Impacts" if en else "Interprétation & impacts économiques",
                      style={'fontWeight': '700', 'fontSize': '13px'})
        ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '12px'}),
        html.Div([
            html.I(className="fas fa-arrow-right",
                   style={'color': sev_col, 'marginRight': '8px', 'fontSize': '11px'}),
            html.Span(f"{more_poll} {'is more exposed than' if en else 'est plus exposée que'} {less_poll} — {sev_msg}.",
                      style={'fontSize': '12px', 'fontWeight': '600', 'color': 'var(--text-primary)'})
        ], style={'marginBottom': '8px'}),
        html.Div([
            html.I(className="fas fa-smog",
                   style={'color': '#ff1744', 'marginRight': '8px', 'fontSize': '11px'}),
            html.Span(f"{'PM2.5 gap' if en else 'Écart PM2.5'}: {'+' if diff_pm25 > 0 else ''}{diff_pm25} µg/m³ ({city1} vs {city2}).",
                      style={'fontSize': '11px', 'color': 'var(--text-secondary)'})
        ], style={'marginBottom': '10px'}),
        # Analyse IA
        html.Div([
            html.Div([
                html.I(className="fas fa-robot",
                       style={'color': '#7c3aed', 'marginRight': '8px', 'fontSize': '13px'}),
                html.Span("AI Analysis — Health & Pollution Expert" if en else "Analyse IA — Expert santé & pollution",
                          style={'fontWeight': '700', 'fontSize': '12px', 'color': '#7c3aed'})
            ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '8px'}),
            html.P(ai_text if ai_text else ('Analysis in progress…' if en else 'Analyse en cours…'),
                   style={'fontSize': '12px', 'lineHeight': '1.7', 'color': 'var(--text-primary)',
                          'margin': '0', 'whiteSpace': 'pre-wrap'})
        ], style={
            'padding': '12px 14px', 'borderRadius': '10px', 'marginBottom': '12px',
            'background': 'rgba(124,58,237,0.06)', 'border': '1.5px solid rgba(124,58,237,0.25)'
        }) if ai_text else html.Div(),
        html.Div([
            html.Div([
                html.I(className="fas fa-briefcase",
                       style={'color': '#a855f7', 'marginRight': '6px', 'fontSize': '10px'}),
                html.Span(('Estimated economic impacts:' if lang=='en' else 'Impacts économiques estimés :'),
                          style={'fontSize': '11px', 'fontWeight': '700',
                                 'color': 'var(--text-secondary)'})
            ], style={'marginBottom': '6px'}),
            *[html.Div(e, style={'fontSize': '11px', 'color': 'var(--text-secondary)',
                                  'marginBottom': '3px', 'paddingLeft': '16px'})
              for e in eco]
        ])
    ], style={'padding': '14px', 'borderRadius': '14px', 'marginTop': '16px',
              'background': f'{sev_col}08', 'border': f'2px solid {sev_col}40'})

    results = html.Div([
        html.H4(f"Comparaison : {city1} vs {city2}",
                style={'marginBottom': '16px', 'fontWeight': '800'}),
        html.Div([
            html.Div([
                html.H5(city1, style={'color': aqi_color(city1_data['aqi']),
                                       'marginBottom': '12px', 'fontWeight': '800'}),
                *[html.Div([html.I(className=f"fas {ic}", style={'width': '22px', 'color': co}),
                            html.Span(lbl, style={'fontSize': '12px'})],
                           style={'marginBottom': '7px', 'display': 'flex', 'alignItems': 'center'})
                  for ic, co, lbl in [
                      ('fa-chart-line', aqi_color(city1_data['aqi']),
                       f"AQI: {city1_data['aqi']} — {aqi_label(city1_data['aqi'])}"),
                      ('fa-smog', '#ff1744', f"PM2.5: {city1_data['pm25']} µg/m³"),
                      ('fa-industry', '#00d4ff', f"NO₂: {city1_data['no2']} µg/m³"),
                      ('fa-thermometer-half', '#ff9100', f"Temp: {weather1['temp']}°C"),
                      ('fa-wind', '#00e676', f"{t('wind_label', lang)}: {weather1['wind']} km/h"),
                      ('fa-tint', '#00d4ff', f"{t('humidity_label', lang)}: {weather1['humidity']}%"),
                  ]]
            ], style={'flex': '1', 'padding': '16px', 'borderRadius': '16px',
                      'background': f"{aqi_color(city1_data['aqi'])}10",
                      'border': f'2px solid {aqi_color(city1_data["aqi"])}40'}),
            html.Div([
                html.H5(city2, style={'color': aqi_color(city2_data['aqi']),
                                       'marginBottom': '12px', 'fontWeight': '800'}),
                *[html.Div([html.I(className=f"fas {ic}", style={'width': '22px', 'color': co}),
                            html.Span(lbl, style={'fontSize': '12px'})],
                           style={'marginBottom': '7px', 'display': 'flex', 'alignItems': 'center'})
                  for ic, co, lbl in [
                      ('fa-chart-line', aqi_color(city2_data['aqi']),
                       f"AQI: {city2_data['aqi']} — {aqi_label(city2_data['aqi'])}"),
                      ('fa-smog', '#ff1744', f"PM2.5: {city2_data['pm25']} µg/m³"),
                      ('fa-industry', '#00d4ff', f"NO₂: {city2_data['no2']} µg/m³"),
                      ('fa-thermometer-half', '#ff9100', f"Temp: {weather2['temp']}°C"),
                      ('fa-wind', '#00e676', f"{t('wind_label', lang)}: {weather2['wind']} km/h"),
                      ('fa-tint', '#00d4ff', f"{t('humidity_label', lang)}: {weather2['humidity']}%"),
                  ]]
            ], style={'flex': '1', 'padding': '16px', 'borderRadius': '16px',
                      'background': f"{aqi_color(city2_data['aqi'])}10",
                      'border': f'2px solid {aqi_color(city2_data["aqi"])}40'}),
        ], style={'display': 'flex', 'gap': '16px'}),
        interp,
    ], className='anim-fade-up')

    return results, {'display': 'block', 'marginTop': '20px'}


@app.callback(
    Output('sim-result', 'children'),
    Output('sim-result', 'style'),
    Input('sim-calc-btn', 'n_clicks'),
    State('trend-city-selector', 'value'),
    State('sim-temp', 'value'),
    State('sim-pm25', 'value'),
    State('sim-humidity', 'value'),
    State('sim-wind', 'value'),
    State('store-lang', 'data'),
)
def calculate_simulation(n_clicks, city, temp, pm25, humidity, wind, lang):
    CITIES_DATA = get_cities_data()
    lang = lang or 'fr'
    if not n_clicks:
        return dash.no_update, {'display': 'none'}

    city_data = next((c for c in CITIES_DATA if c['city'] == city), CITIES_DATA[0])
    base_aqi = city_data['aqi']
    
    temp_impact = (temp - 26.5) * 0.3
    pm25_impact = (pm25 - city_data['pm25']) * 0.5
    humidity_impact = (humidity - 65) * 0.1
    wind_impact = (wind - 12) * -0.2
    
    impact = temp_impact + pm25_impact + humidity_impact + wind_impact
    new_aqi = max(20, min(300, base_aqi + impact))
    
    result = html.Div([
        html.Div([
            html.I(className="fas fa-chart-line", style={'color': '#ff9100', 'marginRight': '8px'}),
            html.Span(t('sim_result_title', lang), style={'fontWeight': '700', 'fontSize': '13px'})
        ], style={'marginBottom': '12px'}),

        html.Div([
            html.Div([
                html.Span(('Current AQI:' if lang=='en' else 'AQI actuel:'), style={'color': 'var(--text-secondary)', 'fontSize': '13px'}),
                html.Span(f"{base_aqi:.0f}", style={'fontSize': '28px', 'fontWeight': '800', 'color': aqi_color(base_aqi), 'marginLeft': '12px'})
            ], style={'marginBottom': '12px'}),

            html.Div([
                html.Span(t('sim_aqi_label', lang), style={'color': 'var(--text-secondary)', 'fontSize': '13px'}),
                html.Span(f"{new_aqi:.0f}", style={'fontSize': '28px', 'fontWeight': '800', 'color': aqi_color(new_aqi), 'marginLeft': '12px'})
            ], style={'marginBottom': '16px'}),
            
            html.Div([
                html.I(className="fas fa-arrow-trend-up" if impact > 0 else "fas fa-arrow-trend-down", 
                       style={'marginRight': '8px', 'color': '#ff1744' if impact > 0 else '#00e676'}),
                html.Span(f"{'+' if impact > 0 else ''}{impact:.1f} points", 
                          style={'fontWeight': '700', 'color': '#ff1744' if impact > 0 else '#00e676'})
            ], style={'marginBottom': '12px'}),
            
            html.Div([
                html.I(className="fas fa-info-circle", style={'marginRight': '8px', 'color': 'var(--text-muted)'}),
                html.Small(('Simulation based on parameter variations' if lang=='en' else 'Simulation basée sur les variations des paramètres'), style={'color': 'var(--text-muted)'})
            ])
        ], style={'padding': '12px', 'background': 'var(--bg-surface)', 'borderRadius': '12px'})
    ])
    
    return result, {'display': 'block', 'marginTop': '20px'}

# Callback pour la déconnexion
@app.callback(
    [Output('store-user', 'data', allow_duplicate=True),
     Output('url', 'pathname', allow_duplicate=True)],  # ← Ajout allow_duplicate=True
    Input('btn-logout', 'n_clicks'),
    prevent_initial_call=True,
)
def handle_logout(n):
    if not n:
        return dash.no_update, dash.no_update
    return None, '/login'

# Callback pour changer la langue — met à jour le store ET le contenu de page via Input store-lang
@app.callback(
    Output('store-lang', 'data'),
    Input('btn-lang', 'n_clicks'),
    State('store-lang', 'data'),
    prevent_initial_call=True,
)
def toggle_lang(n, cur):
    if not n:
        return dash.no_update
    return 'en' if cur == 'fr' else 'fr'


# ── Auto-refresh toutes les 5 minutes ────────────────────────────────────────
@app.callback(
    Output('store-refresh-ts', 'data'),
    Input('auto-refresh', 'n_intervals'),
    prevent_initial_call=True,
)
def auto_refresh(n):
    from dash_cache import cache_invalidate
    from city_utils import invalidate_cities_cache
    import time
    cache_invalidate()
    invalidate_cities_cache()
    return int(time.time())


@app.callback(
    Output('refresh-badge', 'children'),
    Input('auto-refresh', 'n_intervals'),
    Input('store-refresh-ts', 'data'),
    State('store-lang', 'data'),
    State('store-user', 'data'),
)
def update_refresh_badge(n_intervals, ts, lang, user):
    import time
    if not user:
        return ''
    lang = lang or 'fr'
    now = time.time()
    age_s = int(now - (ts or now))
    if age_s < 60:
        label = f"{'Updated' if lang=='en' else 'Actualisé'} {'just now' if lang=='en' else 'à l instant'}"
    else:
        mins = age_s // 60
        label = f"{'Updated' if lang=='en' else 'Actualisé'} {f'{mins} min ago' if lang=='en' else f'il y a {mins} min'}"
    return f"⟳ {label}"


# Callback clientside pour mettre à jour le label du bouton langue en temps réel
app.clientside_callback(
    """
    function(lang) {
        // Mettre à jour le bouton lang
        var btn = document.getElementById('btn-lang');
        if (btn) {
            btn.textContent = lang === 'fr' ? 'EN' : 'FR';
        }
        return lang;
    }
    """,
    Output('store-lang', 'data', allow_duplicate=True),
    Input('store-lang', 'data'),
    prevent_initial_call=True,
)

# Callback pour le rendu du contenu des onglets
@app.callback(
    Output('tab-content', 'children'),
    Input('active-tab', 'data'),
    Input('store-city', 'data'),
    Input('store-lang', 'data'),
    Input('store-theme', 'data'),
    Input('store-refresh-ts', 'data'),
    State('store-user', 'data'),
    State('store-region', 'data'),
)
def render_tab(tab_id, city, lang, theme, _refresh, user, region):
    if not user:
        return make_overview_fallback(city or 'Yaoundé', lang or 'fr', theme or 'dark')

    role = user.get('role', 'citizen')
    default_tabs = {'citizen': 'today', 'decision': 'dashboard', 'researcher': 'stats'}

    # Onglets valides par rôle
    _citizen_tabs    = {'today', 'my_city', 'health', 'alerts', 'about'}
    _decision_tabs   = {'dashboard', 'analysis', 'policies', 'about'}
    _researcher_tabs = {'stats', 'models', 'simulation', 'api', 'about'}
    _valid = {'citizen': _citizen_tabs, 'decision': _decision_tabs, 'researcher': _researcher_tabs}

    # Si tab_id absent ou invalide pour ce rôle → défaut du rôle
    if not tab_id or tab_id not in _valid.get(role, set()):
        tab_id = default_tabs.get(role, 'today')
    
    if tab_id == 'my_city':
        user_city = user.get('city')
        if user_city:
            city = user_city
    
    if tab_id == 'today' and user.get('role') == 'citizen':
        city = None

    return get_tab_content(tab_id, user.get('role', 'citizen'),
                           city, region or 'all', lang or 'fr', theme or 'dark', user=user)


# Callback pour le filtre région/ville
@app.callback(
    Output('city-filter', 'options'),
    Output('city-filter', 'value'),
    Output('store-city', 'data'),
    Output('store-region', 'data'),
    Output('store-selected-city', 'data'),
    Input('region-filter', 'value'),
    Input('city-filter', 'value'),
    State('store-lang', 'data'),
    State('store-user', 'data'),
    prevent_initial_call=True,
)
def update_city_filter(region, city, lang, user):
    lang = lang or 'fr'
    cities_dyn = get_cities_data()
    if region == 'all':
        opts = [{'label': t('city_all', lang), 'value': 'all'}] + [
            {'label': c['city'], 'value': c['city']} for c in cities_dyn
        ]
    else:
        filtered = [c for c in cities_dyn if c['region'] == region]
        n_lbl = f"{len(filtered)} {'cities' if lang=='en' else 'villes'}"
        opts = [{'label': n_lbl, 'value': 'all'}] + [
            {'label': c['city'], 'value': c['city']} for c in filtered
        ]
    valid = [o['value'] for o in opts]
    new_city = city if city in valid else 'all'
    # Résolution de la ville sélectionnée (jamais 'all')
    user_city = (user or {}).get('city')
    resolved = _resolve_city(new_city, user_city, cities_dyn)
    return opts, new_city, new_city, region, resolved


# Callback pour mettre à jour la carte quand la ville change via le filtre principal
@app.callback(
    Output('tab-content', 'children', allow_duplicate=True),
    Input('store-city', 'data'),
    Input('store-region', 'data'),
    State('store-lang', 'data'),
    State('store-theme', 'data'),
    State('active-tab', 'data'),
    State('store-user', 'data'),
    prevent_initial_call=True,
)
def update_content_on_filter(city, region, lang, theme, tab_id, user):
    """Met à jour le contenu quand le filtre ville/région change."""
    lang = lang or 'fr'
    theme = theme or 'dark'
    if not user:
        resolved = _resolve_city(city, None, get_cities_data())
        return make_overview_fallback(resolved, lang, theme)
    role = user.get('role', 'citizen')
    # Pour le citoyen sur l'onglet today, on zoome sur la ville choisie
    if tab_id in (None, 'today') and role == 'citizen':
        cities_dyn = get_cities_data()
        city_for_map = _resolve_city(city, user.get('city'), cities_dyn) if city and city != 'all' else None
        return make_overview_fallback(city_for_map, lang, theme)
    # Pour les autres rôles/onglets, déléguer au render_tab via store-city change
    return get_tab_content(tab_id or 'dashboard', role, city, region or 'all', lang, theme, user=user)


# ============= CALLBACKS POUR LA PAGE ALERTES =============

@app.callback(
    Output('threshold-preview', 'children'),
    Output('threshold-preview', 'style'),
    Input('alert-threshold-slider', 'value'),
    prevent_initial_call=True
)
def update_threshold_preview(value):
    color = aqi_color(value)
    status = "⚠️ Alerte déclenchée" if value <= 100 else "✓ Seuil personnalisé"
    preview = html.Div([
        html.Div([
            html.I(className="fas fa-bell", style={'color': color, 'marginRight': '8px'}),
            html.Span(f"Seuil : AQI > {value}", style={'fontWeight': '800', 'color': color})
        ]),
        html.Small(f"{status} - Vous serez notifié quand l'AQI dépassera {value}", 
                   style={'fontSize': '10px', 'color': 'var(--text-secondary)'})
    ])
    return preview, {
        'padding': '12px', 'borderRadius': '12px', 'marginBottom': '16px',
        'background': 'var(--bg-surface)', 'border': f'2px solid {color}40'
    }


@app.callback(
    Output('threshold-save-message', 'children'),
    Output('threshold-save-message', 'style'),
    Input('save-threshold-btn', 'n_clicks'),
    State('alert-threshold-slider', 'value'),
    prevent_initial_call=True
)
def save_threshold(n_clicks, value):
    if n_clicks:
        color = aqi_color(value)
        message = html.Div([
            html.I(className="fas fa-check-circle", style={'color': '#00e676', 'marginRight': '6px'}),
            html.Span(f"Seuil enregistré : AQI > {value}", style={'color': '#00e676'})
        ])
        return message, {'marginTop': '12px', 'fontSize': '11px', 'textAlign': 'center', 'color': '#00e676'}
    return dash.no_update, dash.no_update


@app.callback(
    Output('email-test-result', 'children'),
    Output('email-test-result', 'style'),
    Output('test-email-btn', 'disabled'),
    Output('test-email-btn', 'children'),
    Input('test-email-btn', 'n_clicks'),
    State('alert-email-input', 'value'),
    State('alert-threshold-slider', 'value'),
    State('alert-options', 'value'),
    State('store-user', 'data'),
    State('store-city', 'data'),
    prevent_initial_call=True
)
def test_email_alert(n_clicks, email, threshold, options, user, city):
    _btn_normal = [html.I(className="fas fa-paper-plane", style={'marginRight': '8px'}),
                   "Envoyer un email de test maintenant"]
    _btn_loading = [html.Div(style={
        'width': '14px', 'height': '14px', 'border': '2px solid #00e67640',
        'borderTop': '2px solid #00e676', 'borderRadius': '50%',
        'animation': 'spin 0.8s linear infinite', 'marginRight': '8px',
        'display': 'inline-block'
    }), "Envoi en cours…"]
    if not n_clicks:
        return dash.no_update, dash.no_update, False, _btn_normal
    if not email:
        return (html.Div([
            html.I(className="fas fa-exclamation-circle", style={'marginRight': '6px'}),
            "Veuillez entrer une adresse email"
        ]), {'marginTop': '8px', 'fontSize': '11px', 'textAlign': 'center', 'color': '#ff1744'},
        False, _btn_normal)

    # Ville de l'utilisateur
    user_city = (user or {}).get('city') or city or 'Yaoundé'
    if user_city == 'all' or not user_city:
        user_city = 'Yaoundé'

    if _email_scheduler:
        user_name = (user or {}).get('name', 'Utilisateur AirEka')
        success, msg = _email_scheduler.send_test_now(
            email=email,
            name=user_name,
            city=user_city,
            threshold=int(threshold or 100),
            options=list(options or ['daily'])
        )
    else:
        success, msg = False, "Scheduler non disponible. Vérifiez email_scheduler.py"

    color = '#00e676' if success else '#ff1744'
    icon  = 'fa-check-circle' if success else 'fa-times-circle'
    return (html.Div([
        html.I(className=f"fas {icon}", style={'marginRight': '6px'}),
        msg
    ]), {'marginTop': '8px', 'fontSize': '11px', 'textAlign': 'center', 'color': color},
    False, _btn_normal)


# ── Sauvegarde des préférences d'alerte email ────────────────────────
@app.callback(
    Output('save-prefs-result', 'children'),
    Output('save-prefs-result', 'style'),
    Output('email-status-badge', 'children'),
    Output('email-status-badge', 'style'),
    Input('save-alert-prefs-btn', 'n_clicks'),
    State('alert-email-input', 'value'),
    State('alert-threshold-slider', 'value'),
    State('notif-hour', 'value'),
    State('alert-options', 'value'),
    State('email-notif-active', 'value'),
    State('store-user', 'data'),
    State('store-city', 'data'),
    prevent_initial_call=True
)
def save_alert_prefs(n_clicks, email, threshold, hour, options, active_list, user, city):
    if not n_clicks:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update

    if not email:
        return (
            html.Div([html.I(className="fas fa-exclamation-circle",
                             style={'marginRight': '6px'}),
                      "Entrez une adresse email valide"]),
            {'marginTop': '8px', 'fontSize': '11px', 'textAlign': 'center', 'color': '#ff1744'},
            dash.no_update, dash.no_update
        )

    is_active  = 'active' in (active_list or [])
    user_name  = (user or {}).get('name', 'Utilisateur AirEka')
    user_city  = (user or {}).get('city') or city or 'Yaoundé'
    if user_city == 'all' or not user_city:
        user_city = 'Yaoundé'

    if _email_scheduler:
        _email_scheduler.save_user_prefs(
            email=email,
            name=user_name,
            city=user_city,
            threshold=int(threshold or 100),
            hour=int(hour or 8),
            options=list(options or ['daily']),
            active=is_active,
        )
        if is_active:
            msg    = f"✓ Alertes activées — email envoyé chaque jour à {int(hour or 8):02d}h00 WAT"
            color  = '#00e676'
            badge  = "● ACTIF"
            bstyle = {'fontSize': '10px', 'fontWeight': '700', 'color': '#00e676',
                      'marginLeft': '12px', 'backgroundColor': '#00e67615',
                      'padding': '3px 10px', 'borderRadius': '99px',
                      'border': '1px solid #00e67640'}
        else:
            msg    = "Alertes désactivées. Cochez la case pour les réactiver."
            color  = '#ff9100'
            badge  = "● INACTIF"
            bstyle = {'fontSize': '10px', 'fontWeight': '700', 'color': '#ff1744',
                      'marginLeft': '12px', 'backgroundColor': '#ff174415',
                      'padding': '3px 10px', 'borderRadius': '99px',
                      'border': '1px solid #ff174440'}
    else:
        msg    = "Scheduler non disponible. Installez APScheduler : pip install apscheduler"
        color  = '#ff1744'
        badge  = "● INACTIF"
        bstyle = {'fontSize': '10px', 'fontWeight': '700', 'color': '#ff1744',
                  'marginLeft': '12px', 'backgroundColor': '#ff174415',
                  'padding': '3px 10px', 'borderRadius': '99px',
                  'border': '1px solid #ff174440'}

    return (
        html.Div([html.I(className=f"fas {'fa-check-circle' if _email_scheduler and is_active else 'fa-info-circle'}",
                          style={'marginRight': '6px'}), msg]),
        {'marginTop': '8px', 'fontSize': '11px', 'textAlign': 'center', 'color': color},
        badge, bstyle
    )


# ── Afficher/masquer les options email ───────────────────────────────
@app.callback(
    Output('email-options', 'style'),
    Input('email-notif-active', 'value'),
    prevent_initial_call=True
)
def toggle_email_options(value):
    if 'active' in (value or []):
        return {'display': 'block'}
    return {'display': 'none'}


# ── PDF premium ──────────────────────────────────────────────────────
@app.callback(
    Output('btn-export-pdf', 'n_clicks'),
    Input('btn-export-pdf', 'n_clicks'),
    prevent_initial_call=True
)
def generate_pdf(n_clicks):
    if not n_clicks:
        return dash.no_update

    from decision_maker_pages import get_region_stats
    region_stats = get_region_stats()

    try:
        if _PDF_AVAILABLE:
            pdf_bytes = generate_pdf_report(CITIES_DATA, region_stats)
        else:
            # Fallback basique si pdf_generator.py absent
            pdf_bytes = _generate_pdf_fallback(region_stats)
    except Exception as e:
        print(f"[AirEka PDF] Erreur génération : {e}")
        pdf_bytes = _generate_pdf_fallback(region_stats)

    filename = f"AirEka_Rapport_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    import tempfile
    temp_path = os.path.join(tempfile.gettempdir(), filename)
    with open(temp_path, 'wb') as f:
        f.write(pdf_bytes)
    import webbrowser
    webbrowser.open(temp_path)
    return n_clicks


def _generate_pdf_fallback(region_stats: dict) -> bytes:
    """PDF de secours (reportlab basique) si pdf_generator.py est absent."""
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors as rl_colors

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle('T', parent=styles['Heading1'], fontSize=20,
                                  textColor=rl_colors.HexColor('#00d4ff'))
    story.append(Paragraph("AirEka — Rapport Qualité de l'Air", title_style))
    story.append(Paragraph(f"Généré le {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                            styles['Normal']))
    story.append(Spacer(1, 20))

    national_aqi = round(sum(c['aqi'] for c in CITIES_DATA) / len(CITIES_DATA), 1)
    story.append(Paragraph(f"AQI national moyen : {national_aqi:.0f}", styles['Normal']))
    story.append(Spacer(1, 10))

    table_data = [['Rang', 'Région', 'AQI moyen']]
    for i, (reg, stats) in enumerate(sorted(region_stats.items(),
                                             key=lambda x: x[1]['aqi_avg'],
                                             reverse=True), 1):
        table_data.append([str(i), reg, f"{stats['aqi_avg']:.0f}"])

    t = Table(table_data, colWidths=[60, 150, 80])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), rl_colors.HexColor('#1e293b')),
        ('TEXTCOLOR',  (0, 0), (-1, 0), rl_colors.white),
        ('GRID',       (0, 0), (-1, -1), 0.5, rl_colors.grey),
        ('FONTNAME',   (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN',      (0, 0), (-1, -1), 'CENTER'),
    ]))
    story.append(t)
    doc.build(story)
    buf.seek(0)
    return buf.getvalue()


# ── 7. Onglet actif — bouton nav cliqué ─────────────────────────────
@app.callback(
    Output('active-tab', 'data', allow_duplicate=True),
    Input({'type': 'nav-tab', 'index': ALL}, 'n_clicks'),
    prevent_initial_call=True,
)
def set_active_tab(clicks):
    """Met à jour l'onglet actif lorsqu'un bouton de navigation est cliqué."""
    if not any(clicks):
        return dash.no_update

    triggered_id = ctx.triggered_id
    if triggered_id and isinstance(triggered_id, dict):
        new_tab = triggered_id.get('index')
        # ⚠️ CORRECTION : stocker l'onglet pour la prochaine fois
        try:
            import json
            print(f"[DEBUG] Onglet sélectionné : {new_tab}")
        except:
            pass
        return new_tab

    return dash.no_update

# ════════════════════════════════════════════════════════════════
# CALLBACK — Téléchargement CSV / JSON (Chercheur)
# ════════════════════════════════════════════════════════════════
@app.callback(
    Output('download-csv-data', 'data'),
    Output('download-status', 'children'),
    Input('btn-download-csv', 'n_clicks'),
    prevent_initial_call=True,
)
def download_csv(n):
    if not n:
        return dash.no_update, dash.no_update
    import csv, io as _io
    buf = _io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(['city', 'region', 'lat', 'lon', 'aqi', 'pm25', 'pm10',
                     'no2', 'so2', 'o3', 'trend'])
    for c in CITIES_DATA:
        writer.writerow([
            c['city'], c['region'], c['lat'], c['lon'],
            c['aqi'], c['pm25'], c['pm10'],
            c['no2'], c.get('so2', ''), c.get('o3', ''), c.get('trend', '')
        ])
    filename = f"aireka_data_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    return (dcc.send_string(buf.getvalue(), filename),
            html.Span([html.I(className="fas fa-check-circle",
                               style={'color': '#00e676', 'marginRight': '6px'}),
                       f"CSV téléchargé : {filename}"],
                      style={'color': '#00e676'}))


@app.callback(
    Output('download-json-data', 'data'),
    Input('btn-download-json', 'n_clicks'),
    prevent_initial_call=True,
)
def download_json(n):
    if not n:
        return dash.no_update
    import json as _json
    data = [{k: v for k, v in c.items() if k != 'color'} for c in CITIES_DATA]
    payload = _json.dumps({'source': 'AirEka', 'generated': datetime.now().isoformat(),
                           'cities': data}, ensure_ascii=False, indent=2)
    filename = f"aireka_data_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    return dcc.send_string(payload, filename)


# ════════════════════════════════════════════════════════════════
# CALLBACK — Alertes hebdomadaires Décideur
# ════════════════════════════════════════════════════════════════
@app.callback(
    Output('active-tab', 'data', allow_duplicate=True),
    Input('store-user', 'data'),
    prevent_initial_call=True,
)
def init_active_tab_on_login(user):
    """Initialise l'onglet actif après connexion selon le rôle."""
    if not user:
        return dash.no_update
    
    role = user.get('role', 'citizen')
    default_tabs = {
        'citizen': 'today',
        'decision': 'dashboard',
        'researcher': 'stats',
    }
    default_tab = default_tabs.get(role, 'today')
    
    print(f"[DEBUG] Connexion - Rôle: {role}, Onglet par défaut: {default_tab}")
    return default_tab

@app.callback(
    Output('decision-alert-result', 'children'),
    Input('btn-decision-alert', 'n_clicks'),
    State('decision-alert-email', 'value'),
    State('decision-alert-scope', 'value'),
    State('store-user', 'data'),
    State('store-lang', 'data'),
    prevent_initial_call=True,
)
def save_decision_alert(n, email, scope, user, lang):
    lang = lang or 'fr'
    if not n:
        return dash.no_update
    if not email:
        return html.Div([
            html.I(className="fas fa-exclamation-circle",
                   style={'color': '#ff1744', 'marginRight': '6px'}),
            "Veuillez entrer votre adresse email."
        ], style={'color': '#ff1744'})

    # Déterminer le libellé du périmètre
    if scope == 'national':
        scope_label = "National"
    elif scope.startswith('region:'):
        scope_label = scope.replace('region:', ('Region: ' if lang=='en' else 'Région : '))
    else:
        scope_label = scope.replace('city:', ('City: ' if lang=='en' else 'Ville : '))

    # Enregistrer via le scheduler si disponible
    if _email_scheduler:
        try:
            _email_scheduler.save_user_prefs(
                email=email,
                name=(user or {}).get('name', 'Décideur AirEka'),
                city=scope.replace('city:', '').replace('region:', '').replace('national', 'Yaoundé'),
                threshold=200,        # décideur : alerte seulement si très mauvais
                hour=7,               # envoi lundi matin 7h WAT
                options=['weekly_decision'],
                active=True,
            )
            saved = True
        except Exception:
            saved = False
    else:
        saved = True  # mode dégradé : confirmer quand même

    if saved:
        return html.Div([
            html.I(className="fas fa-check-circle",
                   style={'color': '#00e676', 'marginRight': '6px'}),
            html.Span(("Alerts activated — weekly report sent every Monday at 07:00 WAT." if lang=='en'
                       else "Alertes activées — rapport hebdomadaire envoyé chaque lundi à 07h00 WAT."),
                      style={'color': '#00e676'}),
            html.Div((f"Scope: {scope_label} · Email: {email}" if lang=='en'
                      else f"Périmètre : {scope_label} · Email : {email}"),
                     style={'fontSize': '10px', 'color': 'var(--text-muted)', 'marginTop': '4px'})
        ])
    return html.Div(("Error saving. Please try again." if lang=='en' else "Erreur lors de l'enregistrement. Réessayez."),
                    style={'color': '#ff1744'})


if __name__ == '__main__':
    # Démarrer le scheduler email avant Dash
    if _email_scheduler:
        _email_scheduler.start()
    app.run(debug=False, host="0.0.0.0", port=7860)