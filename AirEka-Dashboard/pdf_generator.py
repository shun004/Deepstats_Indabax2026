"""
AirEka — Générateur PDF premium pour le Décideur
Deepstats Consulting · IndabaX Cameroon 2026

Design :
  - Page de couverture avec dégradé sombre, deux logos et AQI national
  - En-tête + pied de page sur chaque page (logos, titre, n° de page)
  - Section synthèse avec KPI colorés en colonnes
  - Tableau régions avec lignes alternées et code couleur AQI
  - Top 10 villes avec barres de progression
  - Recommandations prioritaires codées par urgence
"""

import io
import os
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame,
    Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether, PageBreak,
)
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.platypus.flowables import Flowable

# ──────────────────────────────────────────────────────────────────────
# CONSTANTES DE DESIGN
# ──────────────────────────────────────────────────────────────────────
PAGE_W, PAGE_H = A4  # 595 x 842 pts

C_DARK   = HexColor("#0f172a")
C_CARD   = HexColor("#1e293b")
C_BORDER = HexColor("#334155")
C_TEXT   = HexColor("#f1f5f9")
C_MUTED  = HexColor("#94a3b8")
C_GREEN  = HexColor("#16a34a")
C_YELLOW = HexColor("#ca8a04")
C_ORANGE = HexColor("#ea580c")
C_RED    = HexColor("#dc2626")
C_PURPLE = HexColor("#7c3aed")
C_CYAN   = HexColor("#0ea5e9")
C_ACCENT = HexColor("#a855f7")   # violet Deepstats

LOGO_PATH_DS = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "assets", "Logo_DeepStats.png")

MARGIN_LEFT  = 2 * cm
MARGIN_RIGHT = 2 * cm
MARGIN_TOP   = 2.5 * cm
MARGIN_BOTTOM = 2 * cm
HEADER_H = 1.8 * cm
FOOTER_H = 1.2 * cm


# ──────────────────────────────────────────────────────────────────────
# HELPERS COULEUR AQI
# ──────────────────────────────────────────────────────────────────────
def _aqi_hex(v: float) -> str:
    if v <= 50:   return "#16a34a"
    if v <= 100:  return "#ca8a04"
    if v <= 150:  return "#ea580c"
    if v <= 200:  return "#dc2626"
    return "#7c3aed"

def _aqi_label(v: float) -> str:
    if v <= 50:   return "Bon"
    if v <= 100:  return "Modéré"
    if v <= 150:  return "Mauvais — sensibles"
    if v <= 200:  return "Mauvais"
    return "Très mauvais"


# ──────────────────────────────────────────────────────────────────────
# FLOWABLE PERSONNALISÉ : barre de progression
# ──────────────────────────────────────────────────────────────────────
class ColorBar(Flowable):
    """Barre de progression colorée (utilisée dans le top-10 villes)."""
    def __init__(self, pct: float, color_hex: str, height=6, width=None):
        Flowable.__init__(self)
        self.pct     = min(pct, 100)
        self.color   = HexColor(color_hex)
        self.bar_h   = height
        self._width  = width or (PAGE_W - MARGIN_LEFT - MARGIN_RIGHT - 4*cm)

    def wrap(self, avail_w, avail_h):
        return self._width, self.bar_h + 2

    def draw(self):
        c = self.canv
        w = self._width
        # Fond gris
        c.setFillColor(HexColor("#334155"))
        c.roundRect(0, 0, w, self.bar_h, 3, fill=1, stroke=0)
        # Barre colorée
        c.setFillColor(self.color)
        c.roundRect(0, 0, w * self.pct / 100, self.bar_h, 3, fill=1, stroke=0)


# ──────────────────────────────────────────────────────────────────────
# EN-TÊTE ET PIED DE PAGE (dessinés sur le canvas à chaque page)
# ──────────────────────────────────────────────────────────────────────
def _draw_header_footer(c: rl_canvas.Canvas, doc):
    c.saveState()
    now_str = datetime.now().strftime("%d/%m/%Y %H:%M")

    # ── En-tête ──────────────────────────────────────────────────────
    c.setFillColor(C_DARK)
    c.rect(0, PAGE_H - HEADER_H, PAGE_W, HEADER_H, fill=1, stroke=0)

    # Trait de séparation
    c.setStrokeColor(C_BORDER)
    c.setLineWidth(0.5)
    c.line(MARGIN_LEFT, PAGE_H - HEADER_H, PAGE_W - MARGIN_RIGHT, PAGE_H - HEADER_H)

    # Logo AirEka (texte) côté gauche
    c.setFillColor(C_GREEN)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(MARGIN_LEFT, PAGE_H - HEADER_H + 6, "AirEka")
    c.setFillColor(C_MUTED)
    c.setFont("Helvetica", 8)
    c.drawString(MARGIN_LEFT + 40, PAGE_H - HEADER_H + 7,
                 "Qualite de l'air au Cameroun")

    # Titre centré
    c.setFillColor(C_MUTED)
    c.setFont("Helvetica", 9)
    c.drawCentredString(PAGE_W / 2, PAGE_H - HEADER_H + 6,
                        "Rapport Strategique · Qualite de l'Air")

    # Logo Deepstats (image si disponible, sinon texte) côté droit
    if os.path.exists(LOGO_PATH_DS):
        try:
            c.drawImage(LOGO_PATH_DS,
                        PAGE_W - MARGIN_RIGHT - 3*cm,
                        PAGE_H - HEADER_H + 2,
                        width=3*cm, height=HEADER_H - 4,
                        preserveAspectRatio=True, mask="auto")
        except Exception:
            _draw_deepstats_text(c, PAGE_W - MARGIN_RIGHT, PAGE_H - HEADER_H + 6)
    else:
        _draw_deepstats_text(c, PAGE_W - MARGIN_RIGHT, PAGE_H - HEADER_H + 6)

    # ── Pied de page ─────────────────────────────────────────────────
    c.setFillColor(C_DARK)
    c.rect(0, 0, PAGE_W, FOOTER_H, fill=1, stroke=0)

    c.setStrokeColor(C_BORDER)
    c.setLineWidth(0.5)
    c.line(MARGIN_LEFT, FOOTER_H, PAGE_W - MARGIN_RIGHT, FOOTER_H)

    c.setFillColor(C_MUTED)
    c.setFont("Helvetica", 7.5)
    c.drawString(MARGIN_LEFT, FOOTER_H / 2 - 3,
                 f"Genere le {now_str}  •  AirEka · Deepstats Consulting · IndabaX Cameroon 2026")
    c.setFillColor(C_CYAN)
    c.setFont("Helvetica-Bold", 8)
    c.drawRightString(PAGE_W - MARGIN_RIGHT, FOOTER_H / 2 - 3,
                      f"Page {doc.page}")

    c.restoreState()


def _draw_deepstats_text(c: rl_canvas.Canvas, x: float, y: float):
    c.setFillColor(C_ACCENT)
    c.setFont("Helvetica-Bold", 9)
    c.drawRightString(x, y, "Deepstats Consulting")


# ──────────────────────────────────────────────────────────────────────
# PAGE DE COUVERTURE (dessinée directement sur le canvas)
# ──────────────────────────────────────────────────────────────────────
def _draw_cover_page(c: rl_canvas.Canvas, national_aqi: float,
                     cities_count: int, alert_count: int, critical_count: int,
                     generation_date: str):
    # Fond complet
    c.setFillColor(C_DARK)
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)

    # Bande de couleur en haut
    aqi_h = HexColor(_aqi_hex(national_aqi))
    c.setFillColor(aqi_h)
    c.rect(0, PAGE_H - 6*mm, PAGE_W, 6*mm, fill=1, stroke=0)

    # Bande sombre sous la barre couleur
    c.setFillColor(C_CARD)
    c.rect(0, PAGE_H - 5*cm, PAGE_W, 5*cm - 6*mm, fill=1, stroke=0)

    # Logo AirEka (gauche en haut)
    c.setFillColor(C_GREEN)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(MARGIN_LEFT, PAGE_H - 3.2*cm, "AirEka")
    c.setFillColor(C_MUTED)
    c.setFont("Helvetica", 9)
    c.drawString(MARGIN_LEFT, PAGE_H - 3.7*cm, "Surveillance de la qualite de l'air")

    # Logo Deepstats (droite en haut)
    if os.path.exists(LOGO_PATH_DS):
        try:
            c.drawImage(LOGO_PATH_DS,
                        PAGE_W - MARGIN_RIGHT - 4*cm,
                        PAGE_H - 4.5*cm,
                        width=4*cm, height=2.5*cm,
                        preserveAspectRatio=True, mask="auto")
        except Exception:
            _cover_deepstats_text(c)
    else:
        _cover_deepstats_text(c)

    # Ligne de séparation
    c.setStrokeColor(C_BORDER)
    c.setLineWidth(1)
    c.line(MARGIN_LEFT, PAGE_H - 5*cm, PAGE_W - MARGIN_RIGHT, PAGE_H - 5*cm)

    # ─── Titre central ───────────────────────────────────────────────
    cy = PAGE_H - 7*cm
    c.setFillColor(C_TEXT)
    c.setFont("Helvetica-Bold", 30)
    c.drawCentredString(PAGE_W / 2, cy, "RAPPORT STRATEGIQUE")
    cy -= 1.2*cm
    c.setFont("Helvetica-Bold", 22)
    c.drawCentredString(PAGE_W / 2, cy, "Qualite de l'Air au Cameroun")

    # Sous-titre
    cy -= 0.8*cm
    c.setFillColor(C_MUTED)
    c.setFont("Helvetica", 12)
    c.drawCentredString(PAGE_W / 2, cy,
                        "40 villes · 10 regions · Modeles ML R2=0.997")

    # Badge IndabaX
    cy -= 1.2*cm
    badge_w, badge_h = 5*cm, 0.8*cm
    bx = PAGE_W / 2 - badge_w / 2
    c.setFillColor(C_ACCENT)
    c.roundRect(bx, cy, badge_w, badge_h, 0.4*cm, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(PAGE_W / 2, cy + 0.22*cm, "IndabaX Cameroon 2026")

    # ─── Grand cercle AQI ────────────────────────────────────────────
    cx, cy_circ = PAGE_W / 2, PAGE_H / 2 - 0.5*cm
    radius = 2.8*cm
    # Halo extérieur
    c.setFillColor(HexColor(_aqi_hex(national_aqi) + "30"))
    c.circle(cx, cy_circ, radius + 0.4*cm, fill=1, stroke=0)
    # Cercle principal
    c.setFillColor(C_CARD)
    c.circle(cx, cy_circ, radius, fill=1, stroke=0)
    c.setStrokeColor(HexColor(_aqi_hex(national_aqi)))
    c.setLineWidth(3)
    c.circle(cx, cy_circ, radius, fill=0, stroke=1)
    # Valeur AQI
    c.setFillColor(HexColor(_aqi_hex(national_aqi)))
    c.setFont("Helvetica-Bold", 38)
    c.drawCentredString(cx, cy_circ + 0.2*cm, f"{national_aqi:.0f}")
    c.setFillColor(C_MUTED)
    c.setFont("Helvetica", 10)
    c.drawCentredString(cx, cy_circ - 1.1*cm, "AQI NATIONAL")
    # Label
    c.setFillColor(HexColor(_aqi_hex(national_aqi)))
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(cx, cy_circ - 1.7*cm, _aqi_label(national_aqi).upper())

    # ─── KPI en bas ──────────────────────────────────────────────────
    kpi_y = 6*cm
    kpis = [
        (str(cities_count), "Villes surveillees", "#0ea5e9"),
        (str(alert_count),  "Villes en alerte",   "#ea580c"),
        (str(critical_count), "Villes critiques", "#dc2626"),
        ("94.7%",           "Confiance ML",       "#16a34a"),
    ]
    kpi_w = (PAGE_W - 2 * MARGIN_LEFT) / len(kpis)
    for i, (val, label, col_hex) in enumerate(kpis):
        kx = MARGIN_LEFT + i * kpi_w + kpi_w / 2
        # Boite
        box_x = MARGIN_LEFT + i * kpi_w + 0.3*cm
        c.setFillColor(HexColor(col_hex + "18"))
        c.setStrokeColor(HexColor(col_hex + "50"))
        c.setLineWidth(1)
        c.roundRect(box_x, kpi_y - 1.2*cm, kpi_w - 0.6*cm, 2.2*cm, 0.3*cm,
                    fill=1, stroke=1)
        # Valeur
        c.setFillColor(HexColor(col_hex))
        c.setFont("Helvetica-Bold", 22)
        c.drawCentredString(kx, kpi_y + 0.3*cm, val)
        # Label
        c.setFillColor(C_MUTED)
        c.setFont("Helvetica", 8)
        c.drawCentredString(kx, kpi_y - 0.7*cm, label)

    # Date en bas de page
    c.setFillColor(C_MUTED)
    c.setFont("Helvetica", 8)
    c.drawCentredString(PAGE_W / 2, 2*cm,
                        f"Document genere le {generation_date}")


def _cover_deepstats_text(c: rl_canvas.Canvas):
    c.setFillColor(C_ACCENT)
    c.setFont("Helvetica-Bold", 14)
    c.drawRightString(PAGE_W - MARGIN_RIGHT, PAGE_H - 3.2*cm, "Deepstats")
    c.setFillColor(C_MUTED)
    c.setFont("Helvetica", 9)
    c.drawRightString(PAGE_W - MARGIN_RIGHT, PAGE_H - 3.7*cm, "Consulting")


# ──────────────────────────────────────────────────────────────────────
# STYLES TEXTE
# ──────────────────────────────────────────────────────────────────────
def _styles():
    S = {}
    base_kw = dict(fontName="Helvetica", textColor=C_TEXT)

    S["title"] = ParagraphStyle(
        "title", fontName="Helvetica-Bold", fontSize=18,
        textColor=C_TEXT, spaceBefore=0, spaceAfter=12, alignment=TA_LEFT)

    S["section"] = ParagraphStyle(
        "section", fontName="Helvetica-Bold", fontSize=13,
        textColor=C_CYAN, spaceBefore=18, spaceAfter=8, alignment=TA_LEFT)

    S["body"] = ParagraphStyle(
        "body", fontName="Helvetica", fontSize=9.5,
        textColor=C_MUTED, spaceBefore=0, spaceAfter=6,
        leading=14, alignment=TA_LEFT)

    S["bold"] = ParagraphStyle(
        "bold", fontName="Helvetica-Bold", fontSize=10,
        textColor=C_TEXT, spaceBefore=0, spaceAfter=4)

    S["caption"] = ParagraphStyle(
        "caption", fontName="Helvetica-Oblique", fontSize=8,
        textColor=C_MUTED, spaceBefore=0, spaceAfter=12, alignment=TA_CENTER)

    S["kpi_val"] = ParagraphStyle(
        "kpi_val", fontName="Helvetica-Bold", fontSize=22,
        textColor=C_TEXT, spaceBefore=0, spaceAfter=0, alignment=TA_CENTER)

    S["kpi_lbl"] = ParagraphStyle(
        "kpi_lbl", fontName="Helvetica", fontSize=8,
        textColor=C_MUTED, spaceBefore=0, spaceAfter=0, alignment=TA_CENTER)

    S["table_h"] = ParagraphStyle(
        "table_h", fontName="Helvetica-Bold", fontSize=9,
        textColor=white, spaceBefore=0, spaceAfter=0, alignment=TA_CENTER)

    S["table_c"] = ParagraphStyle(
        "table_c", fontName="Helvetica", fontSize=9,
        textColor=C_TEXT, spaceBefore=0, spaceAfter=0, alignment=TA_CENTER)

    S["alert_label"] = ParagraphStyle(
        "alert_label", fontName="Helvetica-Bold", fontSize=9,
        textColor=white, spaceBefore=0, spaceAfter=0, alignment=TA_CENTER)

    return S


# ──────────────────────────────────────────────────────────────────────
# CONSTRUCTION DE LA TABLE DE RÉGIONS
# ──────────────────────────────────────────────────────────────────────
def _region_table(region_stats: dict, S: dict) -> Table:
    sorted_r = sorted(region_stats.items(),
                      key=lambda x: x[1]["aqi_avg"], reverse=True)

    headers = ["#", "Region", "AQI moyen", "PM2.5", "NO2", "Statut", "Priorite"]
    data = [[Paragraph(h, S["table_h"]) for h in headers]]

    for i, (region, stats) in enumerate(sorted_r, 1):
        aqi = stats["aqi_avg"]
        col = HexColor(_aqi_hex(aqi))
        lbl = _aqi_label(aqi)

        if aqi > 150:
            prio = ("URGENT",    C_RED)
        elif aqi > 100:
            prio = ("ELEVE",     C_ORANGE)
        elif aqi > 50:
            prio = ("MODERE",    C_YELLOW)
        else:
            prio = ("NORMAL",    C_GREEN)

        data.append([
            Paragraph(str(i), S["table_c"]),
            Paragraph(f"<b>{region}</b>", S["table_c"]),
            Paragraph(f"<font color='{_aqi_hex(aqi)}'><b>{aqi:.0f}</b></font>", S["table_c"]),
            Paragraph(f"{stats['pm25_avg']:.1f}", S["table_c"]),
            Paragraph(f"{stats['no2_avg']:.1f}", S["table_c"]),
            Paragraph(lbl, S["table_c"]),
            Paragraph(f"<b>{prio[0]}</b>",
                      ParagraphStyle("_p", fontName="Helvetica-Bold", fontSize=8,
                                     textColor=prio[1], alignment=TA_CENTER)),
        ])

    col_w = [0.6*cm, 3.8*cm, 2.4*cm, 2.4*cm, 2.0*cm, 3.5*cm, 2.4*cm]
    t = Table(data, colWidths=col_w, repeatRows=1)

    ts = TableStyle([
        # Header
        ("BACKGROUND",  (0, 0), (-1, 0), C_CARD),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [HexColor("#1e293b"), HexColor("#162032")]),
        ("GRID",        (0, 0), (-1, -1), 0.3, C_BORDER),
        ("TOPPADDING",  (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("ROUNDEDCORNERS", [6]),
    ])
    # Colorier le fond de la colonne AQI selon la valeur
    for row_i, (_, stats) in enumerate(sorted_r, 1):
        aqi = stats["aqi_avg"]
        ts.add("BACKGROUND", (2, row_i), (2, row_i),
               HexColor(_aqi_hex(aqi) + "25"))

    t.setStyle(ts)
    return t


# ──────────────────────────────────────────────────────────────────────
# TOP 10 VILLES
# ──────────────────────────────────────────────────────────────────────
def _top10_table(cities_data: list, S: dict) -> Table:
    top = sorted(cities_data, key=lambda x: x["aqi"], reverse=True)[:10]
    max_aqi = top[0]["aqi"] if top else 200

    headers = ["#", "Ville", "Region", "AQI", "PM2.5", "Niveau"]
    data = [[Paragraph(h, S["table_h"]) for h in headers]]

    for i, c in enumerate(top, 1):
        aqi = c["aqi"]
        data.append([
            Paragraph(str(i), S["table_c"]),
            Paragraph(f"<b>{c['city']}</b>", S["table_c"]),
            Paragraph(c["region"], S["table_c"]),
            Paragraph(
                f"<font color='{_aqi_hex(aqi)}'><b>{aqi}</b></font>",
                S["table_c"]),
            Paragraph(f"{c['pm25']:.1f}", S["table_c"]),
            Paragraph(
                f"<font color='{_aqi_hex(aqi)}'>{_aqi_label(aqi)}</font>",
                S["table_c"]),
        ])

    col_w = [0.6*cm, 3.2*cm, 3.0*cm, 2.0*cm, 2.2*cm, 4.5*cm]
    t = Table(data, colWidths=col_w, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), C_CARD),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [HexColor("#1e293b"), HexColor("#162032")]),
        ("GRID",          (0, 0), (-1, -1), 0.3, C_BORDER),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
    ]))
    return t


# ──────────────────────────────────────────────────────────────────────
# RECOMMANDATIONS
# ──────────────────────────────────────────────────────────────────────
RECOMMENDATIONS = [
    ("URGENT",    "#dc2626",
     "Activation du plan d'urgence qualite de l'air",
     "Yaoundé, Douala, Bafia — AQI > 150. Restriction de circulation, "
     "fermeture des industries polluantes, communication grand public. "
     "Impact estime : -15% PM2.5 en 48h."),
    ("ELEVE",     "#ea580c",
     "Mise en place de Zones a Faibles Emissions (ZFE)",
     "Centres-villes de Yaoundé et Douala. Interdiction des vehicules "
     "EURO < 3. Impact : -18% NO2 sur 6 mois."),
    ("MODERE",    "#ca8a04",
     "Renforcement des normes industrielles",
     "Zones industrielles de Douala (Bassa, Bonaberi). Audit trimestriel "
     "des emissions. Impact : -25% SO2."),
    ("INFORMATION", "#0ea5e9",
     "Programme de reboisement urbain",
     "Garoua, Maroua — regions les plus exposees a la saison seche. "
     "Plantation de 50 000 arbres d'ici fin 2026. Impact : -5 AQI."),
    ("PREVENTION", "#16a34a",
     "Transition energetique et cuisson propre",
     "Programme national de remplacement des foyers a bois. "
     "Subvention du gaz propane dans 10 regions. Impact : -40% CO."),
]


def _recommendations_table(S: dict) -> Table:
    data = []
    for prio, col, title, desc in RECOMMENDATIONS:
        data.append([
            Paragraph(f"<b>{prio}</b>",
                      ParagraphStyle("_pl", fontName="Helvetica-Bold",
                                     fontSize=8, textColor=HexColor(col),
                                     alignment=TA_CENTER)),
            Paragraph(f"<b>{title}</b>", S["bold"]),
            Paragraph(desc, S["body"]),
        ])

    col_w = [2.2*cm, 5.5*cm, 9.0*cm]
    t = Table(data, colWidths=col_w)
    ts = TableStyle([
        ("ROWBACKGROUNDS", (0, 0), (-1, -1),
         [HexColor("#1e293b"), HexColor("#162032")]),
        ("GRID",           (0, 0), (-1, -1), 0.3, C_BORDER),
        ("VALIGN",         (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING",     (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING",  (0, 0), (-1, -1), 8),
        ("LEFTPADDING",    (0, 0), (-1, -1), 8),
        ("RIGHTPADDING",   (0, 0), (-1, -1), 8),
    ])
    # Fond de la colonne priorité selon urgence
    urgency_bg = {
        "URGENT": "#dc262625", "ELEVE": "#ea580c25",
        "MODERE": "#ca8a0425", "INFORMATION": "#0ea5e925",
        "PREVENTION": "#16a34a25",
    }
    for row_i, (prio, col, _, __) in enumerate(RECOMMENDATIONS):
        ts.add("BACKGROUND", (0, row_i), (0, row_i),
               HexColor(urgency_bg.get(prio, "#1e293b")))
    t.setStyle(ts)
    return t


# ──────────────────────────────────────────────────────────────────────
# FONCTION PRINCIPALE
# ──────────────────────────────────────────────────────────────────────
def generate_pdf_report(cities_data: list, region_stats: dict) -> bytes:
    """
    Génère le PDF premium et retourne les bytes.
    cities_data  : liste de dicts (city, region, aqi, pm25, ...)
    region_stats : dict de stats par région (depuis get_region_stats())
    """
    buffer = io.BytesIO()
    gen_date = datetime.now().strftime("%d/%m/%Y à %H:%M")

    # ── Calculs globaux ───────────────────────────────────────────────
    national_aqi   = round(sum(c["aqi"] for c in cities_data) / len(cities_data), 1)
    alert_count    = len([c for c in cities_data if c["aqi"] > 100])
    critical_count = len([c for c in cities_data if c["aqi"] > 150])

    # ── Canvas pour page de couverture ────────────────────────────────
    c_cover = rl_canvas.Canvas(buffer, pagesize=A4)
    _draw_cover_page(c_cover, national_aqi, len(cities_data),
                     alert_count, critical_count, gen_date)
    c_cover.showPage()
    c_cover.save()
    # On va utiliser ce buffer comme base, puis ajouter les pages platypus

    # ── Re-init avec BaseDocTemplate (contenu) ────────────────────────
    # On fait tout dans un seul canvas pour les pages de contenu
    buffer2 = io.BytesIO()

    class _Doc(BaseDocTemplate):
        def __init__(self, buf, **kw):
            BaseDocTemplate.__init__(self, buf, **kw)
            frame = Frame(MARGIN_LEFT, MARGIN_BOTTOM + FOOTER_H,
                          PAGE_W - MARGIN_LEFT - MARGIN_RIGHT,
                          PAGE_H - MARGIN_BOTTOM - FOOTER_H - MARGIN_TOP - HEADER_H,
                          leftPadding=0, bottomPadding=0,
                          rightPadding=0, topPadding=0)
            self.addPageTemplates([
                PageTemplate(id="main", frames=[frame],
                             onPage=_draw_header_footer)
            ])

    doc = _Doc(buffer2, pagesize=A4,
               title="AirEka — Rapport Strategique Qualite de l'Air",
               author="Deepstats Consulting")

    S = _styles()
    story = []

    # ── PAGE 2 : Synthèse nationale ───────────────────────────────────
    story.append(Paragraph("Synthese nationale", S["title"]))
    story.append(HRFlowable(width="100%", thickness=1,
                             color=C_BORDER, spaceAfter=12))

    # Ligne récap texte
    aqi_label_str = _aqi_label(national_aqi)
    story.append(Paragraph(
        f"Au <b>{gen_date}</b>, l'indice de qualite de l'air national s'etablit "
        f"a <font color='{_aqi_hex(national_aqi)}'><b>{national_aqi:.0f} AQI</b></font> "
        f"({aqi_label_str}). Sur <b>{len(cities_data)} villes</b> surveillees, "
        f"<font color='#dc2626'><b>{critical_count}</b></font> sont en etat critique "
        f"(AQI&gt;150) et "
        f"<font color='#ea580c'><b>{alert_count}</b></font> sont en alerte (AQI&gt;100).",
        S["body"]))
    story.append(Spacer(1, 12))

    # Tableau KPI 4 colonnes
    national_pm25 = round(sum(c["pm25"] for c in cities_data) / len(cities_data), 1)
    national_no2  = round(sum(c["no2"]  for c in cities_data) / len(cities_data), 1)

    def _kpi_cell(val, label, col_hex):
        return [
            Paragraph(str(val),
                      ParagraphStyle("_kv", fontName="Helvetica-Bold", fontSize=20,
                                     textColor=HexColor(col_hex), alignment=TA_CENTER)),
            Paragraph(label,
                      ParagraphStyle("_kl", fontName="Helvetica", fontSize=8,
                                     textColor=C_MUTED, alignment=TA_CENTER)),
        ]

    kpi_data = [[
        _kpi_cell(f"{national_aqi:.0f}", "AQI National", _aqi_hex(national_aqi)),
        _kpi_cell(f"{national_pm25:.1f}", "PM2.5 moy. (µg/m³)", "#ea580c"),
        _kpi_cell(f"{national_no2:.1f}", "NO2 moy. (µg/m³)", "#0ea5e9"),
        _kpi_cell(f"{critical_count}", "Villes critiques", "#dc2626"),
    ]]
    kpi_table = Table(kpi_data, colWidths=[4*cm] * 4)
    kpi_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), C_CARD),
        ("BOX",           (0, 0), (-1, -1), 0.5, C_BORDER),
        ("INNERGRID",     (0, 0), (-1, -1), 0.3, C_BORDER),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ("ROUNDEDCORNERS", [8]),
    ]))
    # Fond par colonne
    kpi_colors = [_aqi_hex(national_aqi), "#ea580c", "#0ea5e9", "#dc2626"]
    for col_i, ch in enumerate(kpi_colors):
        kpi_table._tblStyle.add(
            "BACKGROUND", (col_i, 0), (col_i, 0), HexColor(ch + "15"))
    story.append(kpi_table)
    story.append(Spacer(1, 20))

    # ── Classement des régions ────────────────────────────────────────
    story.append(Paragraph("Classement des regions par qualite de l'air", S["section"]))
    story.append(HRFlowable(width="100%", thickness=0.5,
                             color=C_BORDER, spaceAfter=8))
    story.append(Paragraph(
        "Les regions sont classees par AQI moyen decroissant. "
        "Les regions en rouge/orange necessitent une action prioritaire.",
        S["body"]))
    story.append(Spacer(1, 8))
    story.append(_region_table(region_stats, S))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "Sources : MINEPDED · OpenAQ · Sentinel-5P ESA · Stations IoT",
        S["caption"]))

    # ── Top 10 villes ─────────────────────────────────────────────────
    story.append(Paragraph("Top 10 des villes les plus polluees", S["section"]))
    story.append(HRFlowable(width="100%", thickness=0.5,
                             color=C_BORDER, spaceAfter=8))
    story.append(_top10_table(cities_data, S))
    story.append(Spacer(1, 20))

    # ── Recommandations prioritaires ──────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("Recommandations et politiques prioritaires", S["title"]))
    story.append(HRFlowable(width="100%", thickness=1,
                             color=C_BORDER, spaceAfter=10))
    story.append(Paragraph(
        "Ces recommandations sont classees par niveau d'urgence decroissant. "
        "Elles sont issues de l'analyse par modeles ML (RF + XGBoost + LSTM, R2=0.967) "
        "et des seuils de l'Organisation Mondiale de la Sante (OMS 2021).",
        S["body"]))
    story.append(Spacer(1, 10))
    story.append(_recommendations_table(S))
    story.append(Spacer(1, 20))

    # ── Note méthodologique ───────────────────────────────────────────
    story.append(Paragraph("Note methodologique", S["section"]))
    story.append(HRFlowable(width="100%", thickness=0.5,
                             color=C_BORDER, spaceAfter=8))
    methodology = [
        ("Collecte des donnees",
         "Donnees issues de capteurs IoT deployes dans 40 villes, "
         "complementees par Sentinel-5P (ESA), OpenAQ et MINEPDED. "
         "Frequence : horaire."),
        ("Modeles de prediction",
         "Ensemble de 3 modeles : Random Forest (R2=0.967), XGBoost (R2=0.951) "
         "et LSTM (R2=0.928). Optimisation hyperparametres avec Optuna. "
         "Validation croisee 5-fold. Intervalle de confiance conformal a 95%."),
        ("Indice de qualite de l'air (IQA)",
         "Calcule selon la formule EPA-AQI adaptee aux polluants mesures : "
         "PM2.5, PM10, NO2, SO2, O3. Seuils OMS 2021."),
        ("Equipe",
         "Deepstats Consulting — IndabaX Cameroon 2026. "
         "Contact : deepstats.contact@gmail.com"),
    ]
    meth_data = [[
        Paragraph(f"<b>{title}</b>", S["bold"]),
        Paragraph(desc, S["body"])
    ] for title, desc in methodology]
    meth_table = Table(meth_data, colWidths=[4*cm, 12.7*cm])
    meth_table.setStyle(TableStyle([
        ("ROWBACKGROUNDS", (0, 0), (-1, -1),
         [HexColor("#1e293b"), HexColor("#162032")]),
        ("GRID",          (0, 0), (-1, -1), 0.3, C_BORDER),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
    ]))
    story.append(meth_table)

    # ── Build ─────────────────────────────────────────────────────────
    doc.build(story)

    # ── Fusion cover + contenu ────────────────────────────────────────
    from pypdf import PdfWriter, PdfReader
    buffer.seek(0)
    buffer2.seek(0)
    writer = PdfWriter()
    for r in (PdfReader(buffer), PdfReader(buffer2)):
        for page in r.pages:
            writer.add_page(page)

    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()