# layout.py

from dash import html, dcc
import dash_bootstrap_components as dbc

# Função do stepper
def create_stepper(current_step: int = 1):
    steps = [
        {"icon": "fas fa-file-upload", "label": "1. R01"},
        {"icon": "fas fa-file-upload", "label": "2. R03"},
        {"icon": "fas fa-gears",       "label": "3. Gerar TXT"},
        {"icon": "fas fa-download",    "label": "4. Baixar TXT"},
    ]

    dots = []
    for idx, step in enumerate(steps, start=1):
        if current_step > idx:
            cls = "step step-completed"
        elif current_step == idx:
            cls = "step step-active"
        else:
            cls = "step"
        dots.append(
            html.Div(
                className=cls,
                children=[
                    html.Div(html.I(className=step["icon"]), className="step-icon"),
                    html.Div(step["label"], className="step-label")
                ]
            )
        )

    return html.Div(dots, className="stepper mb-4")

# ============================================================
# LAYOUT PRINCIPAL
# ============================================================

def create_layout(app):
    """Layout principal com card de upload e preview."""
    # --------------------------- NAVBAR ---------------------------
    navbar = dbc.Navbar(
        dbc.Container([
            dbc.NavbarBrand(
                html.Span([
                    html.I(className="fas fa-file-code me-2"),
                    "Gerador TXT - DIMOB 2025"
                ], className="navbar-title fw-bold text-light"),
                href="#"
            ),
            dbc.Nav([
                dbc.NavItem(dbc.NavLink("Upload & Geração", href="#upload")),
                dbc.NavItem(dbc.NavLink("Preview", href="#preview")),
            ], className="ms-auto", navbar=True),
        ]),
        color="dark", dark=True, fixed="top", className="glass-navbar shadow"
    )

    spacer = html.Div(style={"height": "64px"})

    # --------------------------- HERO ---------------------------
    hero = dbc.Container(
        dbc.Row(
            dbc.Col(
                html.Div(
                    [
                        html.H1(
                            "Transforme planilhas em TXT DIMOB",
                            className="display-5 text-light mb-3"
                        ),
                        html.P(
                            "Processo rápido, seguro e 100% no navegador — nenhuma instalação extra necessária.",
                            className="text-light mb-4"
                        ),
                        dbc.Button(
                            "Baixar Modelos R01/R03", id="btn-modelos",
                            color="success", className="btn-cta"
                        ),
                        dcc.Download(id="download-modelos")
                    ],
                    className="p-5 rounded-4 hero-card"
                ),
                width=10, className="mx-auto text-center"
            ),
            align="center"
        ),
        fluid=True, className="hero-section py-5"
    )

    # ---------------------- CARD – UPLOAD -----------------------
    card_uploads = dbc.Card(
        className="upload-card shadow-lg glass mx-auto",
        children=[
            html.Div(id="stepper", children=create_stepper(1)),
            dbc.CardHeader(
                [html.I(className="fas fa-cloud-upload-alt me-2"), "Enviar Arquivos"],
                className="upload-header text-center text-white"
            ),
            dbc.CardBody(
                className="upload-body p-4",
                children=[
                    # Uploads R01 / R03
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.Label(
                                        [html.I(className="fas fa-file-upload me-2"), "R01 (.xlsx)"],
                                        className="upload-label fw-semibold text-center d-block mb-2 bg-light rounded px-2 py-1"
                                    ),
                                    dcc.Upload(
                                        id="upload-tipo-r01",
                                        children=html.Div(
                                            [html.I(className="fas fa-cloud-arrow-up fa-2x mb-2"),
                                            html.Div("Clique ou arraste aqui")],
                                            className="upload-placeholder text-center text-white"
                                        ),
                                        className="upload-zone upload-zone-modern"
                                    ),
                                    html.Div(id="msg-tipo-r01", className="msg-upload text-success mt-2 text-center")
                                ],
                                lg=6, md=8, xs=12, className="mb-4"
                            ),
                            dbc.Col(
                                [
                                    html.Label(
                                        [html.I(className="fas fa-file-upload me-2"), "R03 (.xlsx)"],
                                        className="upload-label fw-semibold text-center d-block mb-2 bg-light rounded px-2 py-1"
                                    ),
                                    dcc.Upload(
                                        id="upload-tipo-r03",
                                        children=html.Div(
                                            [html.I(className="fas fa-cloud-arrow-up fa-2x mb-2"),
                                            html.Div("Clique ou arraste aqui")],
                                            className="upload-placeholder text-center text-white"
                                        ),
                                        className="upload-zone upload-zone-modern"
                                    ),
                                    html.Div(id="msg-tipo-r03", className="msg-upload text-success mt-2 text-center")
                                ],
                                lg=6, md=8, xs=12, className="mb-4"
                            ),
                        ],
                        className="gx-4 justify-content-center mb-4"
                    ),

                    # Botões Gerar / Baixar
                    dbc.Row(
                        [
                            dbc.Col(
                                dbc.Button(
                                    [html.I(className="fas fa-gears me-2"), "Gerar TXT"],
                                    id="botao-gerar-txt",
                                    color="primary",
                                    className="btn-action w-100"
                                ),
                                lg=3, md=4, xs=12, className="mb-2"
                            ),
                            dbc.Col(
                                dbc.Button(
                                    [html.I(className="fas fa-download me-2"), "Baixar TXT"],
                                    id="botao-download-txt",
                                    color="secondary",
                                    disabled=True,
                                    className="btn-action w-100"
                                ),
                                lg=3, md=4, xs=12
                            ),
                        ],
                        justify="center",
                        className="mt-4"
                    ),

                    # Mensagem de confirmação
                    html.Div(id="msg-gerar-txt", className="text-success small mt-2 text-center"),
                ]
            ),
        ]
    )

    # ---------------------- CARD – PREVIEW ----------------------
    card_preview = dbc.Card(
    [
        dbc.CardHeader(
            html.H4("Preview", className="fw-bold mb-0"),
            className="bg-transparent border-0 text-center"
        ),
        dbc.CardBody(
            [
                dbc.Row(
                    dbc.Col(
                        dbc.Button("Copiar", id="btn-copy-preview",
                                   color="info", className="btn-action mb-2"),
                        width="auto"
                    ),
                    justify="end"
                ),
                html.Div(id="clipboard-output", style={"display": "none"}),
                dbc.Spinner(
                    html.Pre(id="output-gerar-txt", className="text-monospace mb-3"),
                    color="primary"
                ),
                dcc.Download(id="download-text-file"),
                dcc.Store(id="store-txt-data"),
            ],
            className="p-3"
        )
    ],
    className="preview-card shadow-lg mx-auto"
)

    # --------------------------- TABS ---------------------------
    tabs = dbc.Tabs(
        [
            dbc.Tab(card_uploads, label="Upload & Geração", tab_id="upload-tab"),
            dbc.Tab(card_preview, label="Preview", tab_id="preview-tab"),
        ],
        active_tab="upload-tab",
        className="mt-4 mb-5 justify-content-center"
    )

    # --------------------------- LAYOUT -------------------------
    return html.Div([
        navbar,
        spacer,
        hero,
        dbc.Container(tabs, fluid=True),
        html.Div(style={"height": "3rem"})
    ])
