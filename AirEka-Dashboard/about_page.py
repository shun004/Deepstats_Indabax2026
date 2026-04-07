"""
AirEka — Page À propos
Deepstats Consulting - IndabaX Cameroon 2026
"""

from dash import html, dcc
from datetime import datetime


def create_about_page(city_name=None, lang='fr', theme='dark'):
    """Page À propos - Deepstats Consulting et l'équipe AirEka"""
    en = (lang == 'en')
    header_color = '#a855f7'  # Violet pour Deepstats

    # Équipe principale (4 membres comme demandé)
    team_members = [
        {
            'name': 'Manuel Gires PANDO KOMBOU',
            'country': 'Cameroun',
            'country_code': 'cm',
            'role': 'Student Statistical Analyst, 3rd year',
            'role_fr': 'Elève Analyste Statisticien, 3e année',
            'bio': 'Machine learning and data analysis, technical coordinator of the project.' if en else 'Machine learning et analyse de données, coordinateur technique du projet.',
            'icon': 'fa-chart-line',
            'color': '#00d4ff'
        },
        {
            'name': 'Reine Vertu KOKOLO MBOUSSI',
            'country': 'Congo',
            'country_code': 'cg',
            'role': 'Student Statistical Analyst, 3rd year',
            'role_fr': 'Elève Analyste Statisticien, 3e année',
            'bio': 'In charge of data visualization and interactive dashboards.' if en else 'Chargée de la visualisation de données et dashboards interactifs.',
            'icon': 'fa-chart-pie',
            'color': '#00e676'
        },
        {
            'name': 'Espoir GUIABESSA TSIA',
            'country': 'Gabon',
            'country_code': 'ga',
            'role': 'Student Statistical Analyst, 3rd year',
            'role_fr': 'Elève Analyste Statisticien, 3e année',
            'bio': 'In charge of predictive model development and API deployment.' if en else 'Chargé du développement des modèles prédictifs et déploiement d\'API.',
            'icon': 'fa-brain',
            'color': '#ff9100'
        },
        {
            'name': 'Shun Aucel MBAKOP BANKINIEN',
            'country': 'Cameroun',
            'country_code': 'cm',
            'role': 'Student Statistical Analyst, 3rd year',
            'role_fr': 'Elève Analyste Statisticien, 3e année',
            'bio': 'Interface design and frontend development for an optimal user experience.' if en else 'Design d\'interfaces et développement frontend pour une expérience utilisateur optimale.',
            'icon': 'fa-palette',
            'color': '#a855f7'
        }
    ]

    # Mentions spéciales (en blocs individuels)
    special_mentions = [
        {
            'name': 'Jonathan Patrick ZE II',
            'country': 'Cameroun',
            'country_code': 'cm',
            'contribution': 'Valuable help with ML models and data architecture' if en else 'Aide précieuse sur les modèles ML et l\'architecture des données',
            'icon': 'fa-star',
            'color': '#eab308'
        },
        {
            'name': 'Dr Brice KENFAC DONGMEZO',
            'country': 'Cameroun',
            'country_code': 'cm',
            'contribution': 'Permanent Faculty ISSEA-CEMAC — Academic supervision' if en else 'Enseignant Permanent ISSEA-CEMAC - Supervision académique',
            'icon': 'fa-user-graduate',
            'color': '#00d4ff'
        },
        {
            'name': 'KOTOKO KOMLAN Kossi',
            'country': 'Togo',
            'country_code': 'tg',
            'contribution': 'Data Advisor at HENDDU — Data strategy consulting' if en else 'Data Advisor chez HENDDU - Conseil en stratégie data',
            'icon': 'fa-chart-line',
            'color': '#ff9100'
        }
    ]

    # Contacts (uniquement LinkedIn et Email cliquables)
    contacts = [
        {'icon': 'fa-linkedin', 'name': 'LinkedIn', 'value': 'Deepstats Consulting', 'url': 'https://www.linkedin.com/company/deepstats-consulting', 'color': '#0077b5'},
        {'icon': 'fa-envelope', 'name': 'Email', 'value': 'deepstats.contact@gmail.com', 'url': 'mailto:deepstats.contact@gmail.com', 'color': '#ea4335'},
        {'icon': 'fa-whatsapp', 'name': 'WhatsApp', 'value': '+237 658 98 44 99 / +237 697 36 76 32', 'url': None, 'color': '#25D366'},
    ]
    
    # Année actuelle
    year = datetime.now().year
    
    return html.Div([
        # Logo Deepstats (hauteur réduite)
        html.Div([
            html.Div([
                html.Img(
                    src='/assets/Logo_DeepStats.png',
                    style={
                        'width': '300px',
                        'height': '120px',
                        'objectFit': 'contain',
                        'marginBottom': '12px',
                        'filter': theme == 'dark' and 'brightness(1)' or 'brightness(0.9)'
                    }
                ),
                html.Div([
                    html.I(className="fas fa-map-marker-alt", style={'fontSize': '10px', 'color': 'var(--text-secondary)', 'marginRight': '6px'}),
                    html.Span("Cameroun", style={'fontSize': '10px', 'color': 'var(--text-secondary)', 'marginRight': '16px'}),
                    html.I(className="fas fa-calendar-alt", style={'fontSize': '10px', 'color': 'var(--text-secondary)', 'marginRight': '6px'}),
                    html.Span("IndabaX 2026", style={'fontSize': '10px', 'color': 'var(--text-secondary)'})
                ], style={'marginTop': '8px'})
            ], style={'textAlign': 'center', 'padding': '16px'})
        ], className='card', style={'marginBottom': '24px', 'border': '2px solid #a855f760', 'boxShadow': '0 0 15px #a855f730'}),
        
        # Présentation du projet
        html.Div([
            html.Div([
                html.I(className="fas fa-leaf", style={'color': '#00e676', 'marginRight': '10px'}),
                html.Span("The AirEka Project" if en else "Le projet AirEka", style={'fontWeight': '700', 'fontSize': '16px'})
            ], style={'marginBottom': '12px'}),
            html.P(
                ("AirEka is an air quality monitoring platform for Cameroon, "
                 "developed for IndabaX Cameroon 2026. It covers 40 cities across "
                 "the country's 10 regions, with real-time data, LightGBM predictive models, "
                 "and recommendations tailored to each user profile.")
                if en else
                ("AirEka est une plateforme de surveillance de la qualité de l'air au Cameroun, "
                 "développée dans le cadre de l'IndabaX Cameroon 2026. Elle couvre 40 villes réparties "
                 "dans les 10 régions du pays, avec des données en temps réel, des modèles prédictifs "
                 "LightGBM, et des recommandations adaptées à chaque profil d'utilisateur."),
                style={'fontSize': '13px', 'color': 'var(--text-secondary)', 'lineHeight': '1.6', 'margin': '0 0 16px 0'}
            ),
            html.Div([
                html.Div([
                    html.I(className="fas fa-chart-line", style={'color': '#00d4ff', 'marginRight': '6px'}),
                    html.Span("40 villes", style={'fontWeight': '600'}),
                    html.Small(" monitored" if en else " surveillées", style={'color': 'var(--text-muted)'})
                ], style={'marginRight': '20px'}),
                html.Div([
                    html.I(className="fas fa-map-marker-alt", style={'color': '#ff9100', 'marginRight': '6px'}),
                    html.Span("10 régions", style={'fontWeight': '600'}),
                    html.Small(" covered" if en else " couvertes", style={'color': 'var(--text-muted)'})
                ], style={'marginRight': '20px'}),
                html.Div([
                    html.I(className="fas fa-brain", style={'color': '#a855f7', 'marginRight': '6px'}),
                    html.Span("LightGBM", style={'fontWeight': '600'}),
                    html.Small(" · R² moyen = 0.909", style={'color': 'var(--text-muted)'})
                ])
            ], style={'display': 'flex', 'flexWrap': 'wrap', 'gap': '16px', 'padding': '12px', 'background': 'var(--bg-surface)', 'borderRadius': '12px'})
        ], className='card', style={'marginBottom': '24px', 'border': '2px solid #00e67660', 'boxShadow': '0 0 10px #00e67630'}),
        
        # L'équipe
        html.Div([
            html.Div([
                html.I(className="fas fa-users", style={'color': '#ff9100', 'marginRight': '10px'}),
                html.Span("The Team" if en else "L'équipe", style={'fontWeight': '700', 'fontSize': '16px'})
            ], style={'marginBottom': '16px'}),
            html.Div([
                *[html.Div([
                    html.Div([
                        html.I(className=f"fas {m['icon']}", style={'color': m['color'], 'fontSize': '24px', 'marginBottom': '10px'}),
                        html.H3(m['name'], style={'fontSize': '13px', 'fontWeight': '800', 'color': 'var(--text-primary)', 'margin': '0 0 4px 0', 'lineHeight': '1.3'}),
                        html.Div([
                            html.Span(m['country'], style={'fontSize': '10px', 'color': 'var(--text-secondary)'}),
                            html.I(className=f"flag-icon flag-icon-{m['country_code']}", style={'marginLeft': '6px', 'fontSize': '11px'})
                        ]),
                        html.P(m['role_fr'] if lang == 'fr' else m['role'], 
                               style={'fontSize': '10px', 'color': m['color'], 'margin': '6px 0 4px 0', 'fontWeight': '600'}),
                        html.P(m['bio'], style={'fontSize': '9px', 'color': 'var(--text-secondary)', 'margin': '0', 'lineHeight': '1.3'})
                    ], style={'textAlign': 'center', 'padding': '12px', 'background': f"{m['color']}08", 'borderRadius': '16px', 'border': f'1px solid {m["color"]}30', 'height': '100%'})
                ]) for m in team_members]
            ], style={'display': 'grid', 'gridTemplateColumns': 'repeat(4, 1fr)', 'gap': '12px'})
        ], className='card', style={'marginBottom': '24px', 'border': '2px solid #ff910060', 'boxShadow': '0 0 10px #ff910030'}),
        
        # Mentions spéciales (en blocs individuels)
        html.Div([
            html.Div([
                html.I(className="fas fa-medal", style={'color': '#eab308', 'marginRight': '10px'}),
                html.Span("Acknowledgments" if en else "Remerciements", style={'fontWeight': '700', 'fontSize': '16px'})
            ], style={'marginBottom': '16px'}),
            html.Div([
                *[html.Div([
                    html.Div([
                        html.I(className=f"fas {m['icon']}", style={'color': m['color'], 'fontSize': '20px', 'marginBottom': '8px'}),
                        html.H3(m['name'], style={'fontSize': '13px', 'fontWeight': '800', 'color': 'var(--text-primary)', 'margin': '0 0 4px 0'}),
                        html.Div([
                            html.Span(m['country'], style={'fontSize': '10px', 'color': 'var(--text-secondary)'}),
                            html.I(className=f"flag-icon flag-icon-{m['country_code']}", style={'marginLeft': '6px', 'fontSize': '11px'})
                        ]),
                        html.P(m['contribution'], style={'fontSize': '10px', 'color': 'var(--text-secondary)', 'margin': '6px 0 0 0', 'lineHeight': '1.3'})
                    ], style={'textAlign': 'center', 'padding': '12px', 'background': f"{m['color']}08", 'borderRadius': '16px', 'border': f'2px solid {m["color"]}30', 'height': '100%'})
                ]) for m in special_mentions]
            ], style={'display': 'grid', 'gridTemplateColumns': 'repeat(3, 1fr)', 'gap': '12px'})
        ], className='card', style={'marginBottom': '24px', 'border': '2px solid #eab30860', 'boxShadow': '0 0 10px #eab30830'}),

        # Contacts
        html.Div([
            html.Div([
                html.I(className="fas fa-address-card", style={'color': '#00d4ff', 'marginRight': '10px'}),
                html.Span("Contact" if en else "Contacts", style={'fontWeight': '700', 'fontSize': '16px'})
            ], style={'marginBottom': '16px'}),
            html.Div([
                *[html.A(
                    html.Div([
                        html.I(className=f"fab {contact['icon']}", style={'color': contact['color'], 'fontSize': '24px', 'marginBottom': '10px'}),
                        html.H4(contact['name'], style={'fontSize': '13px', 'fontWeight': '700', 'margin': '0', 'color': 'var(--text-primary)'}),
                        html.P(contact['value'], style={'fontSize': '10px', 'color': 'var(--text-secondary)', 'margin': '6px 0 0 0', 'wordBreak': 'break-all'})
                    ], style={'textAlign': 'center', 'padding': '14px', 'background': f"{contact['color']}08", 'borderRadius': '16px', 'border': f'2px solid {contact["color"]}30', 'transition': 'all 0.2s ease', 'height': '100%'})
                ) for contact in contacts if contact['url']],
                *[html.Div(
                    html.Div([
                        html.I(className=f"fab {contact['icon']}", style={'color': contact['color'], 'fontSize': '24px', 'marginBottom': '10px'}),
                        html.H4(contact['name'], style={'fontSize': '13px', 'fontWeight': '700', 'margin': '0', 'color': 'var(--text-primary)'}),
                        html.P(contact['value'], style={'fontSize': '10px', 'color': 'var(--text-secondary)', 'margin': '6px 0 0 0', 'wordBreak': 'break-all'})
                    ], style={'textAlign': 'center', 'padding': '14px', 'background': f"{contact['color']}08", 'borderRadius': '16px', 'border': f'2px solid {contact["color"]}30', 'height': '100%'})
                ) for contact in contacts if not contact['url']]
            ], style={'display': 'grid', 'gridTemplateColumns': 'repeat(3, 1fr)', 'gap': '16px'})
        ], className='card', style={'marginBottom': '24px', 'border': '2px solid #00d4ff60', 'boxShadow': '0 0 10px #00d4ff30'}),
        
        # Footer de la page
        html.Div([
            html.Div([
                html.I(className="fas fa-copyright", style={'marginRight': '6px', 'color': 'var(--text-muted)'}),
                html.Span(f" {year} Deepstats Consulting - AirEka", style={'fontSize': '10px', 'color': 'var(--text-muted)'}),
                html.Span(" | ", style={'margin': '0 6px', 'color': 'var(--text-muted)'}),
                html.I(className="fas fa-code-branch", style={'marginRight': '6px', 'color': 'var(--text-muted)'}),
                html.Span("IndabaX Cameroon 2026", style={'fontSize': '10px', 'color': 'var(--text-muted)'})
            ], style={'textAlign': 'center', 'padding': '12px', 'background': 'var(--bg-surface)', 'borderRadius': '12px'})
        ])
        
    ], className='anim-fade-up')