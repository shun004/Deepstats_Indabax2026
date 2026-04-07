"""
AirEka — Page de connexion/inscription premium
IndabaX Cameroon 2026
"""

from dash import html, dcc


def create_login_layout(theme='dark'):
    """Retourne le layout complet de la page de connexion/inscription."""

    # ------------------------------------------------------------------ #
    # Styles selon le thème (clair/sombre)
    # ------------------------------------------------------------------ #
    if theme == 'dark':
        bg_color = '#0f172a'
        card_bg = '#1e293b'
        border_color = '#334155'
        text_color = '#f1f5f9'
        text_secondary = '#94a3b8'
        input_bg = '#0f172a'
        badge_bg = '#334155'
        badge_color = '#94a3b8'
        btn_primary = 'linear-gradient(135deg, #16a34a 0%, #0d9488 100%)'
        btn_secondary = 'linear-gradient(135deg, #00d4ff 0%, #0084cc 100%)'
        active_tab_color = '#00d4ff'
        inactive_tab_color = '#94a3b8'
        inactive_tab_border = '#334155'
    else:
        bg_color = '#f0f4f8'
        card_bg = '#ffffff'
        border_color = '#c8d8ea'
        text_color = '#0f1f35'
        text_secondary = '#4a6080'
        input_bg = '#f8fafc'
        badge_bg = '#e2e8f0'
        badge_color = '#64748b'
        btn_primary = 'linear-gradient(135deg, #16a34a 0%, #0d9488 100%)'
        btn_secondary = 'linear-gradient(135deg, #0284c7 0%, #0369a1 100%)'
        active_tab_color = '#0284c7'
        inactive_tab_color = '#64748b'
        inactive_tab_border = '#cbd5e1'

    CARD_STYLE = {
        'position': 'relative',
        'maxWidth': '480px',
        'width': '100%',
        'backgroundColor': card_bg,
        'borderRadius': '24px',
        'padding': '32px',
        'border': f'1px solid {border_color}',
        'boxShadow': '0 24px 64px rgba(0,0,0,0.4), 0 0 0 1px rgba(255,255,255,0.04)',
        'transition': 'all 0.3s ease',
    }

    INPUT_STYLE = {
        'width': '100%',
        'backgroundColor': input_bg,
        'color': text_color,
        'border': f'1px solid {border_color}',
        'borderRadius': '10px',
        'padding': '13px 16px',
        'fontSize': '15px',
        'fontFamily': 'DM Sans, sans-serif',
        'outline': 'none',
        'boxSizing': 'border-box',
        'transition': 'all 0.2s ease',
        'height': '48px',
        'lineHeight': '1.4',
    }

    BUTTON_STYLE = {
        'width': '100%',
        'padding': '12px',
        'borderRadius': '10px',
        'border': 'none',
        'fontSize': '14px',
        'fontWeight': '700',
        'cursor': 'pointer',
        'fontFamily': 'DM Sans, sans-serif',
        'letterSpacing': '0.02em',
        'display': 'flex',
        'alignItems': 'center',
        'justifyContent': 'center',
        'gap': '8px',
        'transition': 'all 0.2s ease',
    }

    # ------------------------------------------------------------------ #
    # Badge "IndabaX 2026"
    # ------------------------------------------------------------------ #
    indabax_badge = html.Div(
        "Hackaton IndabaX Cmr 2026",
        style={
            'position': 'absolute',
            'top': '16px',
            'right': '16px',
            'backgroundColor': badge_bg,
            'color': badge_color,
            'fontSize': '10px',
            'fontWeight': '600',
            'padding': '3px 8px',
            'borderRadius': '99px',
            'letterSpacing': '0.04em',
        }
    )

    # ------------------------------------------------------------------ #
    # Logo + titre (centré)
    # ------------------------------------------------------------------ #
    logo_section = html.Div([
        html.Div([
            html.Img(
                src='/assets/AirEka.jpeg',
                style={
                    'width': '72px',
                    'height': '72px',
                    'borderRadius': '20px',
                    'objectFit': 'cover',
                    'border': '2px solid #166534',
                    'boxShadow': '0 0 20px rgba(22,163,74,0.30)',
                    'display': 'block',
                    'margin': '0 auto 16px auto',
                }
            ),
        ]),
        html.Div("AirEka Cameroun", style={
            'fontSize': '28px', 'fontWeight': '800', 'color': text_color,
            'letterSpacing': '-0.03em', 'textAlign': 'center',
        }),
        html.Div("Deepstats Consulting", style={
            'fontSize': '14px', 'fontWeight': '500', 'color': '#16a34a',
            'letterSpacing': '0.08em', 'textAlign': 'center', 'marginBottom': '8px',
        }),
        html.Div(
            "Surveillance qualité de l'air · 40 villes · 10 régions",
            style={'fontSize': '12px', 'color': text_secondary, 'textAlign': 'center', 'marginTop': '4px'}
        ),
    ], style={'marginBottom': '32px'})

    # ------------------------------------------------------------------ #
    # Onglets Connexion / Inscription
    # ------------------------------------------------------------------ #
    tabs = html.Div([
        html.Button(
            "Se connecter",
            id='login-tab-btn',
            n_clicks=0,
            style={
                'flex': '1', 'padding': '12px', 'background': 'transparent',
                'border': 'none', 'borderBottom': f'2px solid {active_tab_color}',
                'color': active_tab_color, 'fontWeight': '700', 'fontSize': '14px',
                'cursor': 'pointer', 'fontFamily': 'DM Sans, sans-serif',
                'transition': 'all 0.2s ease',
            }
        ),
        html.Button(
            "S'inscrire",
            id='signup-tab-btn',
            n_clicks=0,
            style={
                'flex': '1', 'padding': '12px', 'background': 'transparent',
                'border': 'none', 'borderBottom': f'2px solid {inactive_tab_border}',
                'color': inactive_tab_color, 'fontWeight': '700', 'fontSize': '14px',
                'cursor': 'pointer', 'fontFamily': 'DM Sans, sans-serif',
                'transition': 'all 0.2s ease',
            }
        ),
    ], style={'display': 'flex', 'marginBottom': '24px', 'borderBottom': f'1px solid {border_color}'})

    # ------------------------------------------------------------------ #
    # Formulaire de Connexion
    # ------------------------------------------------------------------ #
    login_form = html.Div(
        id='login-form',
        children=[
            html.Div([
                dcc.Input(
                    id='login-email',
                    type='email',
                    placeholder="Adresse email",
                    style=INPUT_STYLE,
                    autoComplete="off",
                )
            ], style={'marginBottom': '16px'}),

            html.Div([
                html.Div([
                    dcc.Input(
                        id='login-password',
                        type='password',
                        placeholder="Mot de passe",
                        style={**INPUT_STYLE, 'paddingRight': '44px'},
                        autoComplete="off",
                    ),
                    html.Button(
                        html.I(className="fas fa-eye", id='login-toggle-icon'),
                        id='login-toggle-btn',
                        n_clicks=0,
                        style={
                            'position': 'absolute', 'right': '12px', 'top': '50%',
                            'transform': 'translateY(-50%)', 'background': 'none',
                            'border': 'none', 'color': '#64748b', 'cursor': 'pointer',
                            'fontSize': '14px', 'padding': '0', 'display': 'flex', 'alignItems': 'center',
                        }
                    ),
                ], style={'position': 'relative'}),
            ], style={'marginBottom': '20px'}),

            html.Button(
                [html.I(className="fas fa-arrow-right-to-bracket"), html.Span("Se connecter", style={'marginLeft': '8px'})],
                id='btn-login-submit',
                n_clicks=0,
                style={**BUTTON_STYLE, 'background': btn_primary, 'color': '#ffffff'}
            ),

            html.Div(id='login-message', style={'marginTop': '16px', 'fontSize': '12px', 'textAlign': 'center', 'color': '#ef4444'}),
        ]
    )

    # ------------------------------------------------------------------ #
    # Formulaire d'Inscription
    # ------------------------------------------------------------------ #
    signup_form = html.Div(
        id='signup-form',
        style={'display': 'none'},
        children=[
            html.Div([
                dcc.Input(
                    id='signup-name',
                    type='text',
                    placeholder="Nom complet",
                    style=INPUT_STYLE,
                    autoComplete="off",
                )
            ], style={'marginBottom': '16px'}),

            html.Div([
                dcc.Input(
                    id='signup-email',
                    type='email',
                    placeholder="Adresse email",
                    style=INPUT_STYLE,
                    autoComplete="off",
                )
            ], style={'marginBottom': '16px'}),

            html.Div([
                html.Div([
                    dcc.Input(
                        id='signup-password',
                        type='password',
                        placeholder="Mot de passe",
                        style={**INPUT_STYLE, 'paddingRight': '44px'},
                        autoComplete="off",
                    ),
                    html.Button(
                        html.I(className="fas fa-eye", id='signup-toggle-icon'),
                        id='signup-toggle-btn',
                        n_clicks=0,
                        style={
                            'position': 'absolute', 'right': '12px', 'top': '50%',
                            'transform': 'translateY(-50%)', 'background': 'none',
                            'border': 'none', 'color': '#64748b', 'cursor': 'pointer',
                            'fontSize': '14px', 'padding': '0', 'display': 'flex', 'alignItems': 'center',
                        }
                    ),
                ], style={'position': 'relative'}),
            ], style={'marginBottom': '16px'}),

            html.Div([
                html.Div([
                    dcc.Input(
                        id='signup-confirm-password',
                        type='password',
                        placeholder="Confirmer le mot de passe",
                        style={**INPUT_STYLE, 'paddingRight': '44px'},
                        autoComplete="off",
                    ),
                    html.Button(
                        html.I(className="fas fa-eye", id='signup-confirm-toggle-icon'),
                        id='signup-confirm-toggle-btn',
                        n_clicks=0,
                        style={
                            'position': 'absolute', 'right': '12px', 'top': '50%',
                            'transform': 'translateY(-50%)', 'background': 'none',
                            'border': 'none', 'color': '#64748b', 'cursor': 'pointer',
                            'fontSize': '14px', 'padding': '0', 'display': 'flex', 'alignItems': 'center',
                        }
                    ),
                ], style={'position': 'relative'}),
            ], style={'marginBottom': '20px'}),

            # Sélection du rôle
            html.Div([
                html.Label("Je suis :", style={'fontSize': '12px', 'color': text_secondary, 'marginBottom': '8px', 'display': 'block'}),
                html.Div([
                    html.Button(
                        [html.I(className="fas fa-person"), html.Span("Citoyen", style={'marginLeft': '8px'})],
                        id='role-citizen',
                        n_clicks=0,
                        style={
                            'flex': '1', 'padding': '10px', 'borderRadius': '8px',
                            'border': f'2px solid {border_color}', 'background': 'transparent',
                            'color': text_secondary, 'cursor': 'pointer', 'fontWeight': '600',
                            'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center',
                            'transition': 'all 0.2s ease'
                        }
                    ),
                    html.Button(
                        [html.I(className="fas fa-landmark"), html.Span("Décideur", style={'marginLeft': '8px'})],
                        id='role-decision',
                        n_clicks=0,
                        style={
                            'flex': '1', 'padding': '10px', 'borderRadius': '8px',
                            'border': f'2px solid {border_color}', 'background': 'transparent',
                            'color': text_secondary, 'cursor': 'pointer', 'fontWeight': '600',
                            'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center',
                            'transition': 'all 0.2s ease'
                        }
                    ),
                    html.Button(
                        [html.I(className="fas fa-flask"), html.Span("Chercheur", style={'marginLeft': '8px'})],
                        id='role-researcher',
                        n_clicks=0,
                        style={
                            'flex': '1', 'padding': '10px', 'borderRadius': '8px',
                            'border': f'2px solid {border_color}', 'background': 'transparent',
                            'color': text_secondary, 'cursor': 'pointer', 'fontWeight': '600',
                            'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center',
                            'transition': 'all 0.2s ease'
                        }
                    ),
                ], style={'display': 'flex', 'gap': '10px', 'marginBottom': '20px'}),
                html.Div(id='selected-role', style={'display': 'none'}),
            ]),

            # Sélection de la ville (pour citoyen)
            html.Div(
                id='city-selection',
                style={'display': 'none', 'marginBottom': '20px'},
                children=[
                    html.Label("Ma ville :", style={'fontSize': '12px', 'color': text_secondary, 'marginBottom': '8px', 'display': 'block'}),
                    dcc.Dropdown(
                        id='signup-city',
                        options=[],
                        placeholder="Sélectionnez votre ville",
                        className='ac-dropdown',
                        clearable=False,
                        style={'width': '100%'}
                    ),
                ]
            ),

            html.Button(
                [html.I(className="fas fa-user-plus"), html.Span("S'inscrire", style={'marginLeft': '8px'})],
                id='btn-signup-submit',
                n_clicks=0,
                disabled=False,
                style={**BUTTON_STYLE, 'background': btn_secondary, 'color': '#ffffff'}
            ),

            # Spinner inscription
            html.Div([
                html.Div(style={
                    'width': '16px', 'height': '16px',
                    'border': '2px solid rgba(0,212,255,0.3)',
                    'borderTop': '2px solid #00d4ff',
                    'borderRadius': '50%',
                    'animation': 'spin 0.8s linear infinite',
                    'marginRight': '8px',
                }),
                html.Span("Inscription en cours, veuillez patienter…",
                          style={'fontSize': '12px', 'color': 'var(--text-secondary)'})
            ], id='signup-loading-spinner', style={'display': 'none', 'alignItems': 'center',
                                                    'justifyContent': 'center', 'marginTop': '10px'}),

            html.Div(id='signup-message',
                     style={'marginTop': '16px', 'fontSize': '12px', 'textAlign': 'center'}),
        ]
    )

    # ------------------------------------------------------------------ #
    # Assemblage final
    # ------------------------------------------------------------------ #
    card = html.Div([
        indabax_badge,
        logo_section,
        tabs,
        login_form,
        signup_form,
    ], style=CARD_STYLE)

    return html.Div([
        card
    ], style={
        'backgroundColor': bg_color,
        'minHeight': '100vh',
        'display': 'flex',
        'alignItems': 'center',
        'justifyContent': 'center',
        'padding': '24px',
        'fontFamily': 'DM Sans, sans-serif',
        'transition': 'background 0.3s ease',
    })