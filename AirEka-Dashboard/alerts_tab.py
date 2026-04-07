"""
AirEka Monitor — Citoyen : Alertes
Villes à risque, seuil personnalisable, notifications email automatiques
"""

from dash import html, dcc


def create_alerts_page(city_name, lang='fr', theme='dark',
                       CITIES_DATA=None, aqi_color=None, aqi_label=None,
                       t=None, fa=None, REGIONS=None):
    """Page Alertes — Villes à risque, seuil personnalisable, notifications auto."""

    if CITIES_DATA is None:
        return html.Div("Erreur: Données non disponibles" if lang == 'fr' else "Error: Data unavailable")

    risky_cities    = sorted([c for c in CITIES_DATA if c['aqi'] > 100],
                              key=lambda x: x['aqi'], reverse=True)
    top_risky       = risky_cities[:5]
    critical_cities = [c for c in risky_cities if c['aqi'] > 150]

    header_color = "#ff9100"
    header_bg    = f"{header_color}08"

    # Commentaire IA alerte
    _ai_alert_text = ""
    try:
        from ai_commentary import ai_alert_summary as _ai_al
        if risky_cities:
            _ai_alert_text = _ai_al(risky_cities[0]['city'], risky_cities[0]['aqi'],
                                    len(risky_cities), lang=lang) or ""
    except Exception:
        pass

    # Placeholder email selon la langue
    email_placeholder = (t('email_placeholder', lang)
                         if t else ("your.email@example.com" if lang == 'en'
                                    else "votre.email@exemple.com"))

    return html.Div([

        # ── En-tête ──────────────────────────────────────────────────
        html.Div([
            html.Div([
                html.I(className="fas fa-bell",
                       style={'color': header_color, 'fontSize': '28px', 'marginRight': '14px'}),
                html.Div([
                    html.H1(t('alerts_title', lang) if t else "Alertes qualité de l'air",
                            style={'fontSize': '24px', 'fontWeight': '800',
                                   'margin': '0', 'color': 'var(--text-primary)'}),
                    html.P(t('alerts_sub', lang) if t else "",
                           style={'fontSize': '12px', 'color': 'var(--text-secondary)',
                                  'margin': '4px 0 0 0'})
                ])
            ], style={'display': 'flex', 'alignItems': 'center'})
        ], style={
            'padding': '20px', 'borderRadius': '20px', 'marginBottom': '24px',
            'background': header_bg, 'border': f'2px solid {header_color}60',
            'boxShadow': f'0 0 20px {header_color}20'
        }),

        # ── Bloc IA alerte ────────────────────────────────────────────
        *([html.Div([
            html.Div([
                html.I(className="fas fa-robot",
                       style={'color': '#7c3aed', 'fontSize': '16px', 'marginRight': '10px'}),
                html.Span(t('ai_alert_national', lang) if t else "Analyse IA — Situation nationale",
                          style={'fontWeight': '700', 'fontSize': '13px',
                                 'color': 'var(--text-primary)'}),
            ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '10px'}),
            html.P(_ai_alert_text,
                   style={'fontSize': '13px', 'color': 'var(--text-secondary)',
                          'lineHeight': '1.6', 'margin': '0'}),
        ], style={
            'padding': '14px 18px', 'borderRadius': '14px', 'marginBottom': '20px',
            'background': 'rgba(124,58,237,0.06)',
            'border': '1px solid rgba(124,58,237,0.28)',
            'boxShadow': '0 0 12px rgba(124,58,237,0.08)',
        })] if _ai_alert_text else []),

        # ── Ligne 1 : Statistiques + Classement ──────────────────────
        html.Div([
            # Statistiques
            html.Div([
                html.Div([
                    html.I(className="fas fa-chart-line",
                           style={'color': '#ff9100', 'marginRight': '10px'}),
                    html.Span(t('current_situation', lang) if t else "Situation actuelle",
                              style={'fontWeight': '700', 'fontSize': '14px'})
                ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '20px'}),

                html.Div([
                    html.Div([
                        html.H3(f"{len(risky_cities)}",
                                style={'fontSize': '42px', 'fontWeight': '800',
                                       'margin': '0', 'color': '#ff9100'}),
                        html.Span(t('at_risk', lang) if t else "villes à risque",
                                  style={'fontSize': '13px', 'color': 'var(--text-secondary)'})
                    ], style={'textAlign': 'center', 'padding': '20px',
                              'background': 'var(--bg-surface)', 'borderRadius': '16px', 'flex': '1'}),
                    html.Div([
                        html.H3(f"{len(critical_cities)}",
                                style={'fontSize': '42px', 'fontWeight': '800',
                                       'margin': '0', 'color': '#ff1744'}),
                        html.Span(t('critical', lang) if t else "villes critiques",
                                  style={'fontSize': '13px', 'color': 'var(--text-secondary)'})
                    ], style={'textAlign': 'center', 'padding': '20px',
                              'background': 'var(--bg-surface)', 'borderRadius': '16px', 'flex': '1'}),
                ], style={'display': 'flex', 'gap': '16px', 'marginBottom': '20px'}),

                html.Div([
                    html.H4(t('worst_quality', lang) if t else "Pire qualité",
                            style={'fontSize': '13px', 'fontWeight': '600',
                                   'margin': '0 0 8px 0', 'color': 'var(--text-secondary)'}),
                    html.Span(f"{risky_cities[0]['city'] if risky_cities else 'N/A'}",
                              style={'fontSize': '22px', 'fontWeight': '800', 'color': '#ff1744'}),
                    html.Span(f" AQI {risky_cities[0]['aqi'] if risky_cities else 'N/A'}",
                              style={'fontSize': '18px', 'fontWeight': '600', 'marginLeft': '8px'})
                ], style={'padding': '16px', 'background': 'var(--bg-surface)', 'borderRadius': '16px'}),

                html.Div([
                    html.I(className="fas fa-exclamation-triangle",
                           style={'color': '#ff9100', 'marginRight': '8px'}),
                    html.Span(t('sensitive_pop_note', lang) if t else
                              "Les populations sensibles doivent limiter leurs déplacements",
                              style={'fontSize': '12px', 'color': 'var(--text-secondary)'})
                ], style={'marginTop': '20px', 'padding': '12px',
                          'background': '#ff910010', 'borderRadius': '12px'})
            ], className='card',
               style={'gridColumn': 'span 5', 'height': '100%',
                      'display': 'flex', 'flexDirection': 'column'}),

            # Classement top 5
            html.Div([
                html.Div([
                    html.I(className="fas fa-ranking-star",
                           style={'color': '#ff9100', 'marginRight': '10px'}),
                    html.Span(t('most_polluted_cities', lang) if t else "Villes les plus polluées",
                              style={'fontWeight': '700', 'fontSize': '14px'})
                ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '20px'}),

                html.Div([
                    *[html.Div([
                        html.Div([
                            html.Span(f"{i+1}", style={
                                'width': '36px', 'height': '36px', 'borderRadius': '50%',
                                'background': f"{aqi_color(city['aqi'])}20" if aqi_color else '#ff910020',
                                'color': aqi_color(city['aqi']) if aqi_color else '#ff9100',
                                'fontWeight': '800', 'display': 'flex',
                                'alignItems': 'center', 'justifyContent': 'center', 'fontSize': '14px'
                            }),
                            html.Div([
                                html.Span(city['city'],
                                          style={'fontWeight': '600', 'fontSize': '15px'}),
                                html.Span(city['region'],
                                          style={'fontSize': '11px', 'color': 'var(--text-secondary)',
                                                 'display': 'block'})
                            ], style={'flex': '1', 'marginLeft': '12px'}),
                            html.Span(str(city['aqi']), style={
                                'fontWeight': '800', 'fontSize': '20px',
                                'color': aqi_color(city['aqi']) if aqi_color else '#ff9100'
                            }),
                            html.Span(" AQI", style={'fontSize': '11px',
                                                      'color': 'var(--text-secondary)',
                                                      'marginLeft': '4px'})
                        ], style={'display': 'flex', 'alignItems': 'center',
                                  'padding': '12px 0', 'borderBottom': '1px solid var(--border)'})
                    ]) for i, city in enumerate(top_risky)]
                ], style={'flex': '1'})
            ], className='card',
               style={'gridColumn': 'span 7', 'height': '100%',
                      'display': 'flex', 'flexDirection': 'column'})

        ], style={'display': 'grid', 'gridTemplateColumns': 'repeat(12,1fr)',
                  'gap': '16px', 'marginBottom': '24px'}),

        # ── Ligne 2 : Alerte quotidienne auto + Email ────────────────
        html.Div([
            # Bloc alerte quotidienne automatique
            html.Div([
                html.Div([
                    html.I(className="fas fa-sun",
                           style={'color': '#ff9100', 'marginRight': '10px', 'fontSize': '18px'}),
                    html.Span(t('daily_reminder_title', lang) if t else "Rappel qualité de l'air — quotidien",
                              style={'fontWeight': '700', 'fontSize': '14px'})
                ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '12px'}),

                html.P(
                    t('daily_reminder_desc', lang) if t else "",
                    style={'fontSize': '11px', 'color': 'var(--text-secondary)',
                           'marginBottom': '16px', 'lineHeight': '1.6'}
                ),

                # Fonctionnement illustré
                html.Div([
                    *[html.Div([
                        html.Div(ico, style={
                            'width': '32px', 'height': '32px', 'borderRadius': '50%',
                            'background': f'{col}20', 'border': f'2px solid {col}50',
                            'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center',
                            'fontSize': '14px', 'marginBottom': '6px', 'flexShrink': '0'
                        }),
                        html.Div(t(label_key, lang) if t else label_key,
                                 style={'fontSize': '10px', 'color': 'var(--text-secondary)',
                                        'textAlign': 'center', 'lineHeight': '1.3'})
                    ], style={'textAlign': 'center', 'flex': '1'})
                    for ico, col, label_key in [
                        ('⏰', '#00d4ff', 'flow_step1_label'),
                        ('🔍', '#00e676', 'flow_step2_label'),
                        ('💡', '#ff9100', 'flow_step3_label'),
                        ('📧', '#a855f7', 'flow_step4_label'),
                    ]]
                ], style={'display': 'flex', 'gap': '8px', 'marginBottom': '16px',
                          'padding': '12px', 'background': 'var(--bg-surface)',
                          'borderRadius': '12px'}),

                # Seuil conservé pour compat callbacks (caché)
                dcc.Slider(id='alert-threshold-slider', min=50, max=200, step=10,
                            value=100, marks={}),
                html.Div(id='threshold-preview', style={'display': 'none'}),
                html.Button(id='save-threshold-btn', n_clicks=0, style={'display': 'none'}),
                html.Div(id='threshold-save-message', style={'display': 'none'}),

                html.Div([
                    html.Div([
                        html.I(className="fas fa-check-circle",
                               style={'color': '#00e676', 'marginRight': '8px'}),
                        html.Span(t('no_threshold_note', lang) if t else
                                  "Aucun seuil à configurer — vous recevrez l'alerte chaque jour.",
                                  style={'fontSize': '11px', 'color': 'var(--text-secondary)',
                                         'lineHeight': '1.5'})
                    ], style={'display': 'flex', 'alignItems': 'flex-start'})
                ], style={'padding': '12px', 'background': '#00e67608',
                          'borderRadius': '10px', 'border': '1px solid #00e67630'}),

            ], className='card', style={'gridColumn': 'span 6'}),

            # Email automatique
            html.Div([
                html.Div([
                    html.I(className="fas fa-envelope",
                           style={'color': '#00e676', 'marginRight': '10px'}),
                    html.Span(t('email_alerts_title', lang) if t else "Alertes email automatiques",
                              style={'fontWeight': '700', 'fontSize': '14px'}),
                    html.Span(t('badge_inactive', lang) if t else "● INACTIF",
                              id='email-status-badge', style={
                        'fontSize': '10px', 'fontWeight': '700',
                        'color': '#ff1744', 'marginLeft': '12px',
                        'backgroundColor': '#ff174415', 'padding': '3px 10px',
                        'borderRadius': '99px', 'border': '1px solid #ff174440'
                    })
                ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '12px'}),

                html.P(
                    t('email_alerts_desc', lang) if t else "",
                    style={'fontSize': '11px', 'color': 'var(--text-secondary)',
                           'marginBottom': '14px', 'lineHeight': '1.5'}
                ),

                dcc.Input(
                    id='alert-email-input',
                    type='email',
                    placeholder=email_placeholder,
                    style={
                        'width': '100%', 'padding': '10px 14px', 'borderRadius': '12px',
                        'border': '1px solid var(--border)', 'background': 'var(--bg-input)',
                        'color': 'var(--text-primary)', 'fontSize': '13px',
                        'marginBottom': '12px', 'outline': 'none', 'boxSizing': 'border-box'
                    }
                ),

                html.Div([
                    dcc.Checklist(
                        id='email-notif-active',
                        options=[{'label': f" 🔔 {t('activate_alerts', lang) if t else 'Activer les alertes email automatiques'}",
                                  'value': 'active'}],
                        value=[],
                        style={'color': 'var(--text-primary)', 'marginBottom': '12px'}
                    )
                ]),

                html.Div([
                    html.Div([
                        html.Span(t('send_hour_label', lang) if t else "Heure d'envoi :",
                                  style={'fontSize': '12px', 'fontWeight': '600',
                                         'marginBottom': '6px', 'display': 'block',
                                         'color': 'var(--text-secondary)'}),
                        dcc.Dropdown(
                            id='notif-hour',
                            options=[{'label': f"{h:02d}:00", 'value': h} for h in range(3, 22)],
                            value=8,
                            clearable=False,
                            style={'width': '100%'},
                            className='ac-dropdown'
                        )
                    ], style={'marginBottom': '12px', 'position': 'relative', 'zIndex': '10'}),

                    dcc.Checklist(
                        id='alert-options',
                        options=[
                            {'label': f' {t("daily_auto_label", lang) if t else "☀️ Récap quotidien automatique"}',
                             'value': 'daily'},
                        ],
                        value=['daily'],
                        style={'display': 'none'}
                    ),

                ], id='email-options', style={'display': 'none'}),

                html.Div([
                    html.Button(
                        [html.I(className="fas fa-floppy-disk", style={'marginRight': '8px'}),
                         t('save_alerts_btn', lang) if t else "Sauvegarder mes alertes"],
                        id='save-alert-prefs-btn',
                        style={
                            'width': '100%', 'padding': '11px', 'borderRadius': '12px',
                            'border': 'none',
                            'background': 'linear-gradient(135deg, #16a34a, #0ea5e9)',
                            'color': '#fff', 'fontWeight': '700', 'cursor': 'pointer',
                            'fontSize': '12px', 'marginBottom': '8px'
                        },
                        n_clicks=0
                    ),
                    html.Button(
                        [html.I(className="fas fa-paper-plane", style={'marginRight': '8px'}),
                         t('test_email_btn', lang) if t else "Envoyer un email de test maintenant"],
                        id='test-email-btn',
                        style={
                            'width': '100%', 'padding': '10px', 'borderRadius': '12px',
                            'border': '1px solid #00e676', 'background': 'transparent',
                            'color': '#00e676', 'fontWeight': '600', 'cursor': 'pointer',
                            'fontSize': '12px'
                        },
                        n_clicks=0
                    ),
                ]),

                html.Div(id='save-prefs-result',
                         style={'marginTop': '10px', 'fontSize': '11px', 'textAlign': 'center'}),
                html.Div(id='email-test-result',
                         style={'marginTop': '8px', 'fontSize': '11px', 'textAlign': 'center'}),

            ], className='card',
               style={'gridColumn': 'span 6', 'overflow': 'visible',
                      'position': 'relative', 'zIndex': '5'}),

        ], style={'display': 'grid', 'gridTemplateColumns': 'repeat(12,1fr)',
                  'gap': '16px', 'marginBottom': '24px'}),

        # ── Ligne 3 : Blocs info ──────────────────────────────────────
        html.Div([
            _info_block("fa-sun", "#ff9100",
                        t('info_daily_title', lang) if t else "Rappel quotidien",
                        t('info_daily_desc', lang) if t else "",
                        "daily-reminder",
                        activate_label=t('activate_label', lang) if t else "Activer"),
            _info_block("fa-chart-line", "#00d4ff",
                        t('info_spike_title', lang) if t else "Alerte de pic",
                        t('info_spike_desc', lang) if t else "",
                        "spike-alert",
                        default=['active'],
                        activate_label=t('activate_label', lang) if t else "Activer"),
            _info_block("fa-cloud-rain", "#00e676",
                        t('info_seasonal_title', lang) if t else "Alerte saisonnière",
                        t('info_seasonal_desc', lang) if t else "",
                        "seasonal-alert",
                        activate_label=t('activate_label', lang) if t else "Activer"),
        ], style={'display': 'grid', 'gridTemplateColumns': 'repeat(3,1fr)',
                  'gap': '16px', 'marginBottom': '24px'}),

        # ── Explication de configuration ──────────────────────────────
        html.Div([
            html.Div([
                html.I(className="fas fa-circle-info",
                       style={'color': '#00d4ff', 'marginRight': '10px'}),
                html.Span(t('how_it_works', lang) if t else "Comment ça marche ?",
                          style={'fontWeight': '700', 'fontSize': '14px'})
            ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '12px'}),
            html.Ol([
                html.Li(t('how_it_works_step1', lang) if t else "",
                        style={'fontSize': '12px', 'color': 'var(--text-secondary)',
                               'marginBottom': '6px', 'lineHeight': '1.5'}),
                html.Li(t('how_it_works_step2', lang) if t else "",
                        style={'fontSize': '12px', 'color': 'var(--text-secondary)',
                               'marginBottom': '6px', 'lineHeight': '1.5'}),
                html.Li(t('how_it_works_step3', lang) if t else "",
                        style={'fontSize': '12px', 'color': 'var(--text-secondary)',
                               'marginBottom': '6px', 'lineHeight': '1.5'}),
                html.Li(t('how_it_works_step4', lang) if t else "",
                        style={'fontSize': '12px', 'color': 'var(--text-secondary)',
                               'lineHeight': '1.5'}),
            ], style={'paddingLeft': '20px', 'margin': '0'})
        ], className='card', style={
            'marginBottom': '24px',
            'background': '#00d4ff08',
            'border': '1px solid #00d4ff30'
        }),

        # ── Footer ────────────────────────────────────────────────────
        html.Div([
            html.I(className="fas fa-shield-alt",
                   style={'marginRight': '8px', 'color': 'var(--text-muted)'}),
            html.Span(t('privacy_note', lang) if t else
                      "Vos alertes sont personnelles et sécurisées.",
                      style={'fontSize': '10px', 'color': 'var(--text-muted)'})
        ], style={'textAlign': 'center', 'padding': '12px'})

    ], className='anim-fade-up')


def _info_block(icon, color, title, desc, checklist_id,
                default=None, activate_label="Activer"):
    return html.Div([
        html.Div([
            html.I(className=f"fas {icon}",
                   style={'color': color, 'fontSize': '24px', 'marginBottom': '10px'}),
            html.H4(title, style={'fontSize': '15px', 'fontWeight': '700',
                                   'margin': '0 0 6px 0', 'color': 'var(--text-primary)'}),
            html.P(desc, style={'fontSize': '11px', 'color': 'var(--text-secondary)',
                                 'marginBottom': '12px', 'lineHeight': '1.4'}),
            dcc.Checklist(
                id=checklist_id,
                options=[{'label': f' ✅ {activate_label}', 'value': 'active'}],
                value=default or [],
                style={'color': 'var(--text-primary)'}
            )
        ], style={'padding': '20px', 'textAlign': 'center'})
    ], className='card')