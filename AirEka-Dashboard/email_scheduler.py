"""
AirEka — Système d'alertes email automatiques
Deepstats Consulting · IndabaX Cameroon 2026

Fonctionnement :
  - APScheduler tourne en arrière-plan, sans intervention manuelle
  - À l'heure choisie, il vérifie l'AQI de la ville de l'utilisateur
  - Si les conditions sont remplies (seuil dépassé OU récap quotidien),
    un email HTML soigné est envoyé depuis deepstats.contact@gmail.com

Configuration REQUISE (à faire une seule fois) :
  1. Sur le compte Google deepstats.contact@gmail.com :
       → Activer la validation en deux étapes
       → Sécurité → Mots de passe des applications → Créer
       → Choisir "Autre (nom personnalisé)" → taper "AirEka"
       → Copier le mot de passe de 16 caractères généré
  2. Remplacer SENDER_APP_PASSWORD ci-dessous par ce mot de passe
"""

import smtplib
import json
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

# ──────────────────────────────────────────────────────────────────────
# CONFIGURATION — À REMPLIR
# ──────────────────────────────────────────────────────────────────────
SENDER_EMAIL        = os.environ.get("GMAIL_SENDER", "")
SENDER_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")
SENDER_DISPLAY      = "AirEka · Deepstats"

# Fichier local de stockage des préférences utilisateurs
PREFS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "alert_prefs.json")


# ──────────────────────────────────────────────────────────────────────
# PERSISTANCE DES PRÉFÉRENCES
# ──────────────────────────────────────────────────────────────────────
def load_prefs() -> dict:
    if os.path.exists(PREFS_FILE):
        try:
            with open(PREFS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_prefs(prefs: dict):
    with open(PREFS_FILE, "w", encoding="utf-8") as f:
        json.dump(prefs, f, ensure_ascii=False, indent=2)


# ──────────────────────────────────────────────────────────────────────
# LOGIQUE AQI : niveaux et recommandations
# ──────────────────────────────────────────────────────────────────────
def _aqi_info(aqi: float) -> dict:
    if aqi <= 50:
        return {
            "level":  "Bon",
            "emoji":  "🟢",
            "color":  "#16a34a",
            "bg":     "#f0fdf4",
            "advice": "La qualité de l'air est excellente. Profitez librement des activités extérieures !",
            "health": "Aucune restriction. Bonne journée à toutes et tous !",
        }
    if aqi <= 100:
        return {
            "level":  "Modéré",
            "emoji":  "🟡",
            "color":  "#ca8a04",
            "bg":     "#fefce8",
            "advice": "Qualité de l'air acceptable. Les personnes sensibles doivent rester prudentes.",
            "health": "Asthmatiques, enfants et personnes âgées : limitez les efforts prolongés en extérieur.",
        }
    if aqi <= 150:
        return {
            "level":  "Mauvais pour les personnes sensibles",
            "emoji":  "🟠",
            "color":  "#ea580c",
            "bg":     "#fff7ed",
            "advice": "Limitez les activités extérieures prolongées. Portez un masque FFP2 si vous sortez.",
            "health": "Enfants, personnes âgées, asthmatiques : restez de préférence à l'intérieur.",
        }
    if aqi <= 200:
        return {
            "level":  "Mauvais",
            "emoji":  "🔴",
            "color":  "#dc2626",
            "bg":     "#fef2f2",
            "advice": "Évitez les activités extérieures. Fermez les fenêtres et utilisez un purificateur d'air.",
            "health": "Toute la population : réduisez au maximum les sorties. Purificateur d'air recommandé.",
        }
    return {
        "level":  "Très mauvais / Dangereux",
        "emoji":  "🟣",
        "color":  "#7c3aed",
        "bg":     "#faf5ff",
        "advice": "⚠️ URGENCE SANITAIRE — Restez absolument à l'intérieur !",
        "health": "Contactez le SAMU (1510) si vous ressentez des symptômes respiratoires.",
    }


# ──────────────────────────────────────────────────────────────────────
# LOGO BASE64 (embarqué pour s'afficher sans serveur externe)
# ──────────────────────────────────────────────────────────────────────
def _logo_img_tag(height: int = 38) -> str:
    import base64 as _b64
    logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "assets", "Logo_DeepStats.png")
    try:
        with open(logo_path, "rb") as f:
            b64 = _b64.b64encode(f.read()).decode("utf-8")
        return (f'<img src="data:image/png;base64,{b64}" height="{height}" '
                f'style="max-height:{height}px;object-fit:contain;" alt="AirEka · Deepstats">')
    except Exception:
        return '<span style="color:#a855f7;font-size:14px;font-weight:800;">AirEka · Deepstats</span>'


# ──────────────────────────────────────────────────────────────────────
# CONSTRUCTION DU TEMPLATE EMAIL HTML — ALERTES AQI
# Font Awesome via CDN + logo embarqué en base64
# ──────────────────────────────────────────────────────────────────────
def build_email_html(name: str, city: str, aqi: float,
                     pm25: float, pm10: float, no2: float, so2: float,
                     threshold: int, options: list) -> str:
    info  = _aqi_info(aqi)
    now   = datetime.now().strftime("%d/%m/%Y à %H:%M")
    color = info["color"]
    logo  = _logo_img_tag(38)

    def _poll_row(pol_name, val, limit, unit):
        over        = val > limit
        badge_color = "#dc2626" if over else "#16a34a"
        badge_icon  = "fa-triangle-exclamation" if over else "fa-circle-check"
        badge_text  = "Dépasse OMS" if over else "Sous le seuil"
        return f"""
        <tr style="border-bottom:1px solid #334155;">
          <td style="padding:9px 14px;color:#94a3b8;font-size:12px;">
            <i class="fas fa-circle" style="color:{badge_color};font-size:7px;
               vertical-align:middle;margin-right:6px;"></i>{pol_name}
          </td>
          <td style="padding:9px 14px;color:#f1f5f9;font-weight:700;font-size:13px;">
            {val:.1f} {unit}
          </td>
          <td style="padding:9px 14px;">
            <span style="color:{badge_color};font-size:11px;font-weight:600;">
              <i class="fas {badge_icon}"></i>&nbsp;{badge_text}
            </span>
          </td>
        </tr>"""

    spike_section = ""
    if 'spike' in options and aqi > threshold:
        spike_section = f"""
    <tr>
      <td style="padding:0 28px 20px;">
        <div style="background:{color}12;border:1px solid {color}50;
                    border-radius:12px;padding:16px;border-left:4px solid {color};">
          <p style="color:{color};font-weight:700;font-size:13px;margin:0 0 6px;">
            <i class="fas fa-bolt"></i>&nbsp; Votre seuil d'alerte a été dépassé !
          </p>
          <p style="color:#94a3b8;font-size:12px;margin:0;">
            AQI actuel&nbsp;: <strong style="color:{color};">{aqi:.0f}</strong>
            &nbsp;/&nbsp;Votre seuil&nbsp;: <strong style="color:#f1f5f9;">{threshold}</strong>
          </p>
        </div>
      </td>
    </tr>"""

    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>AirEka — Alerte qualité de l'air · {city}</title>
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
        <td style="background:linear-gradient(135deg,#0f172a,#1e293b,#0f172a);
                   padding:24px 28px;border-bottom:1px solid #334155;">
          <table width="100%" cellpadding="0" cellspacing="0">
            <tr>
              <td>{logo}</td>
              <td style="text-align:right;color:#94a3b8;font-size:11px;">
                <i class="fas fa-clock"></i>&nbsp;{now}
              </td>
            </tr>
          </table>
          <h1 style="color:#f1f5f9;font-size:21px;font-weight:800;
                     margin:16px 0 4px;letter-spacing:-.02em;">
            <i class="fas fa-leaf" style="color:#16a34a;"></i>&nbsp;
            Rapport qualité de l'air — {city}
          </h1>
          <p style="color:#94a3b8;font-size:12px;margin:0;">
            <i class="fas fa-map-marker-alt"></i>&nbsp;Cameroun · AirEka · Deepstats Consulting
          </p>
        </td>
      </tr>

      <!-- AQI -->
      <tr>
        <td style="padding:28px 28px 20px;text-align:center;
                   background:{color}06;border-bottom:1px solid #334155;">
          <div style="width:110px;height:110px;border-radius:50%;
                      background:{color}18;border:3px solid {color}60;
                      margin:0 auto 16px;display:table;">
            <div style="display:table-cell;vertical-align:middle;text-align:center;">
              <div style="font-size:38px;font-weight:800;color:{color};line-height:1.1;">{aqi:.0f}</div>
              <div style="font-size:10px;color:#94a3b8;letter-spacing:.1em;">AQI</div>
            </div>
          </div>
          <div style="display:inline-block;background:{color}20;color:{color};
                      font-size:13px;font-weight:700;padding:5px 18px;
                      border-radius:99px;margin:0 0 14px;border:1px solid {color}40;">
            <i class="fas fa-gauge-high"></i>&nbsp;{info['level']}
          </div>
          <p style="color:#f1f5f9;font-size:14px;line-height:1.6;
                    margin:0 auto;max-width:420px;">{info['advice']}</p>
        </td>
      </tr>

      <!-- SANTÉ -->
      <tr>
        <td style="padding:20px 28px;border-bottom:1px solid #334155;">
          <div style="background:#0f172a;border-radius:12px;padding:16px;
                      border-left:4px solid #a855f7;">
            <p style="color:#a855f7;font-size:11px;font-weight:700;
                      text-transform:uppercase;letter-spacing:.08em;margin:0 0 6px;">
              <i class="fas fa-kit-medical"></i>&nbsp;Recommandation santé
            </p>
            <p style="color:#f1f5f9;font-size:13px;line-height:1.5;margin:0;">
              {info['health']}
            </p>
          </div>
        </td>
      </tr>

      <!-- POLLUANTS -->
      <tr>
        <td style="padding:20px 28px;border-bottom:1px solid #334155;">
          <p style="color:#94a3b8;font-size:11px;font-weight:700;
                    text-transform:uppercase;letter-spacing:.08em;margin:0 0 12px;">
            <i class="fas fa-smog"></i>&nbsp;Concentrations des polluants
          </p>
          <table width="100%" cellpadding="0" cellspacing="0"
                 style="border-radius:10px;overflow:hidden;border:1px solid #334155;">
            <thead>
              <tr style="background:#334155;">
                <th style="padding:8px 14px;color:#94a3b8;font-size:11px;
                           text-align:left;font-weight:600;">Polluant</th>
                <th style="padding:8px 14px;color:#94a3b8;font-size:11px;
                           text-align:left;font-weight:600;">Valeur</th>
                <th style="padding:8px 14px;color:#94a3b8;font-size:11px;
                           text-align:left;font-weight:600;">Seuil OMS</th>
              </tr>
            </thead>
            <tbody>
              {_poll_row("PM2.5", pm25, 15, "µg/m³")}
              {_poll_row("PM10",  pm10, 45, "µg/m³")}
              {_poll_row("NO2",   no2,  40, "µg/m³")}
              {_poll_row("SO2",   so2,  40, "µg/m³")}
            </tbody>
          </table>
        </td>
      </tr>

      {spike_section}

      <!-- PIED DE PAGE -->
      <tr>
        <td style="background:#0f172a;padding:20px 28px;text-align:center;
                   border-top:1px solid #334155;">
          <p style="color:#475569;font-size:11px;margin:0 0 4px;">
            <i class="fas fa-envelope"></i>&nbsp;Envoyé automatiquement par
            <strong style="color:#94a3b8;">AirEka · Deepstats Consulting</strong>
          </p>
          <p style="color:#334155;font-size:10px;margin:0 0 4px;">
            IndabaX Cameroon 2026 · {SENDER_EMAIL}
          </p>
          <p style="color:#334155;font-size:10px;margin:0;">
            <i class="fas fa-gear"></i>&nbsp;Modifiez vos alertes dans votre espace AirEka.
          </p>
        </td>
      </tr>

    </table>
  </td></tr>
</table>
</body>
</html>"""
# ──────────────────────────────────────────────────────────────────────
# ENVOI SMTP
# ──────────────────────────────────────────────────────────────────────
def send_alert_email(recipient_email: str, name: str, city: str,
                     aqi: float, pm25: float, pm10: float, no2: float,
                     so2: float, threshold: int, options: list) -> tuple[bool, str]:
    """Envoie l'email d'alerte. Retourne (succès, message)."""
    if not recipient_email:
        return False, "Adresse email manquante"
    if not SENDER_EMAIL or not SENDER_APP_PASSWORD:
        return False, "Variables d'environnement GMAIL_SENDER ou GMAIL_APP_PASSWORD manquantes"
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"🌿 AirEka · Qualité de l'air à {city} — AQI {aqi:.0f}"
        msg["From"]    = f"{SENDER_DISPLAY} <{SENDER_EMAIL}>"
        msg["To"]      = recipient_email

        html = build_email_html(name, city, aqi, pm25, pm10, no2, so2, threshold, options)
        msg.attach(MIMEText(html, "html", "utf-8"))

        with smtplib.SMTP("smtp.gmail.com", 587, timeout=15) as srv:
            srv.starttls()
            srv.login(SENDER_EMAIL, SENDER_APP_PASSWORD)
            srv.sendmail(SENDER_EMAIL, recipient_email, msg.as_string())

        print(f"[AirEka Mail] ✓ Email envoyé → {recipient_email} ({city}, AQI={aqi:.0f})")
        return True, "Email envoyé avec succès !"
    except smtplib.SMTPAuthenticationError:
        msg_err = ("Erreur d'authentification Gmail. Vérifiez l'App Password dans email_scheduler.py. "
                   "Rappel : utilisez un mot de passe d'application (16 caractères), "
                   "pas le mot de passe normal du compte.")
        print(f"[AirEka Mail] ✗ Auth error")
        return False, msg_err
    except smtplib.SMTPException as e:
        print(f"[AirEka Mail] ✗ SMTP error: {e}")
        return False, f"Erreur SMTP : {e}"
    except Exception as e:
        print(f"[AirEka Mail] ✗ Unexpected error: {e}")
        return False, f"Erreur inattendue : {e}"


# ──────────────────────────────────────────────────────────────────────
# SCHEDULER PRINCIPAL
# ──────────────────────────────────────────────────────────────────────
class AirEkaScheduler:
    """
    Gestionnaire de planification des alertes email.

    Usage typique dans app.py :
        scheduler = AirEkaScheduler(CITIES_DATA)
        scheduler.start()
    """

    def __init__(self, cities_data: list):
        self.cities_data = cities_data
        self._scheduler = BackgroundScheduler(timezone="Africa/Douala")
        self._started = False

    # ── Démarrage ─────────────────────────────────────────────────────
    def start(self):
        if not self._started:
            self._scheduler.start()
            self._started = True
            self._reload_jobs()
            print("[AirEka Scheduler] ✓ Démarré — fuseau horaire : Africa/Douala")

    def stop(self):
        if self._started:
            self._scheduler.shutdown(wait=False)
            self._started = False

    # ── Rechargement des jobs sauvegardés ─────────────────────────────
    def _reload_jobs(self):
        prefs = load_prefs()
        count = 0
        for email, pref in prefs.items():
            if pref.get("active"):
                self._register_job(email, pref)
                count += 1
        print(f"[AirEka Scheduler] {count} alerte(s) rechargée(s) depuis {PREFS_FILE}")

    # ── ID unique par email ────────────────────────────────────────────
    @staticmethod
    def _job_id(email: str) -> str:
        return "aeka_" + email.replace("@", "_at_").replace(".", "_dot_")

    # ── Enregistrement / mise à jour d'un job ─────────────────────────
    def _register_job(self, email: str, pref: dict):
        hour      = int(pref.get("hour", 8))
        city      = pref.get("city", "Yaoundé")
        threshold = int(pref.get("threshold", 100))
        options   = pref.get("options", ["daily"])
        name      = pref.get("name", "Utilisateur AirEka")
        job_id    = self._job_id(email)

        # Supprimer l'ancien job si présent
        existing = self._scheduler.get_job(job_id)
        if existing:
            self._scheduler.remove_job(job_id)

        # Clôture : capturer les variables dans la closure
        def _run(em=email, nm=name, ct=city, th=threshold, opts=options):
            city_data = next((c for c in self.cities_data if c["city"] == ct), None)
            if not city_data:
                print(f"[AirEka Scheduler] Ville inconnue : {ct}")
                return
            aqi = city_data["aqi"]
            # Envoyer si : récap quotidien actif OU pic dépassé
            should_send = ("daily" in opts) or ("spike" in opts and aqi > th)
            if should_send:
                send_alert_email(
                    recipient_email=em,
                    name=nm,
                    city=ct,
                    aqi=aqi,
                    pm25=city_data.get("pm25", 0),
                    pm10=city_data.get("pm10", 0),
                    no2=city_data.get("no2", 0),
                    so2=city_data.get("so2", 0),
                    threshold=th,
                    options=opts,
                )

        self._scheduler.add_job(
            _run,
            trigger=CronTrigger(hour=hour, minute=0),
            id=job_id,
            name=f"AirEka · {email} · {city}",
            replace_existing=True,
        )
        print(f"[AirEka Scheduler] Job enregistré : {email} → {city} à {hour:02d}h00")

    # ── API publique : sauvegarder les préférences ─────────────────────
    def save_user_prefs(self, email: str, name: str, city: str,
                        threshold: int, hour: int,
                        options: list, active: bool) -> bool:
        """Sauvegarde en JSON et (re)planifie ou supprime le job."""
        prefs = load_prefs()
        prefs[email] = {
            "name":       name,
            "city":       city,
            "threshold":  threshold,
            "hour":       hour,
            "options":    options,
            "active":     active,
            "updated_at": datetime.now().isoformat(),
        }
        save_prefs(prefs)

        if active and self._started:
            self._register_job(email, prefs[email])
        elif not active and self._started:
            job_id = self._job_id(email)
            if self._scheduler.get_job(job_id):
                self._scheduler.remove_job(job_id)
                print(f"[AirEka Scheduler] Job supprimé : {email}")
        return True

    # ── API publique : test immédiat ──────────────────────────────────
    def send_test_now(self, email: str, name: str, city: str,
                      threshold: int, options: list) -> tuple[bool, str]:
        """Envoie un email de test immédiatement (sans attendre l'heure planifiée)."""
        city_data = next((c for c in self.cities_data if c["city"] == city), None)
        if not city_data:
            return False, f"Ville '{city}' introuvable dans la base de données."
        return send_alert_email(
            recipient_email=email,
            name=name,
            city=city,
            aqi=city_data["aqi"],
            pm25=city_data.get("pm25", 0),
            pm10=city_data.get("pm10", 0),
            no2=city_data.get("no2", 0),
            so2=city_data.get("so2", 0),
            threshold=threshold,
            options=options if options else ["daily"],
        )