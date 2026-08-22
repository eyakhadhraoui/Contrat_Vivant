import os
import json
import smtplib
import urllib.request
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()

EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'true').lower() in ('1', 'true', 'yes')
EMAIL_USE_SSL = os.getenv('EMAIL_USE_SSL', 'false').lower() in ('1', 'true', 'yes')
EMAIL_SENDER = os.getenv('EMAIL_SENDER')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
TEAMS_WEBHOOK_URL = os.getenv('TEAMS_WEBHOOK_URL')


def _normalize_recipients(destinataire):
    if isinstance(destinataire, (list, tuple)):
        emails = []
        for item in destinataire:
            if isinstance(item, dict):
                emails.append(item.get('email'))
            else:
                emails.append(item)
        return [e for e in emails if e]
    if isinstance(destinataire, dict):
        return [destinataire.get('email')] if destinataire.get('email') else []
    return [destinataire] if destinataire else []


def send_email(destinataire, sujet, contenu, html_contenu: str | None = None):
    # En environnement de test ou sans identifiants configurés, simuler l'envoi
    if not EMAIL_SENDER or not EMAIL_PASSWORD or EMAIL_SENDER == "votre.email@gmail.com":
        print(f"[EMAIL SIMULATION] Vers {destinataire} | Sujet: {sujet}")
        return True

    destinataires = _normalize_recipients(destinataire)
    if not destinataires:
        return False

    try:
        if EMAIL_USE_SSL:
            server = smtplib.SMTP_SSL(EMAIL_HOST, EMAIL_PORT)
        else:
            server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
        with server:
            if EMAIL_USE_TLS and not EMAIL_USE_SSL:
                server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            for email_to in destinataires:
                if html_contenu:
                    msg = MIMEMultipart('alternative')
                    msg.attach(MIMEText(contenu, 'plain', _charset='utf-8'))
                    msg.attach(MIMEText(html_contenu, 'html', _charset='utf-8'))
                else:
                    msg = MIMEText(contenu, _charset='utf-8')
                msg['Subject'] = sujet
                msg['From'] = EMAIL_SENDER
                msg['To'] = email_to
                server.send_message(msg)
        print(f"[EMAIL ENVOYÉ] Notification envoyée avec succès à {len(destinataires)} destinataire(s)")
        return True
    except Exception as e:
        print(f"Erreur envoi email : {e}")
        return False


def send_teams(sujet, message, facts: dict | None = None):
    if not TEAMS_WEBHOOK_URL or "votre-webhook" in TEAMS_WEBHOOK_URL:
        return False

    facts_list = []
    if facts:
        facts_list = [{"name": str(k), "value": str(v)} for k, v in facts.items()]

    payload = {
        "@type": "MessageCard",
        "@context": "http://schema.org/extensions",
        "themeColor": "0076D7",
        "summary": sujet,
        "sections": [{
            "activityTitle": f"📢 {sujet}",
            "text": message,
            "facts": facts_list,
            "markdown": True
        }]
    }

    try:
        req = urllib.request.Request(
            TEAMS_WEBHOOK_URL,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            return response.status in (200, 202)
    except Exception as e:
        print(f"Erreur envoi Teams : {e}")
        return False
