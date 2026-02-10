"""Notifications email + SMS via API Brevo."""
import requests

from config import BREVO_API_KEY, ALERT_EMAIL, ALERT_PHONE

BREVO_EMAIL_URL = "https://api.brevo.com/v3/smtp/email"
BREVO_SMS_URL = "https://api.brevo.com/v3/transactionalSMS/sms"


def envoyer_email(sujet, corps):
    """Envoie un email transactionnel via Brevo."""
    if not BREVO_API_KEY or not ALERT_EMAIL:
        print(f"[NOTIF] Email non envoyé (config manquante) : {sujet}")
        return False

    resp = requests.post(
        BREVO_EMAIL_URL,
        headers={
            "api-key": BREVO_API_KEY,
            "content-type": "application/json"
        },
        json={
            "sender": {"name": "Pipeline Agence", "email": "pipeline@sublym.org"},
            "to": [{"email": ALERT_EMAIL}],
            "subject": sujet,
            "htmlContent": (
                "<pre style='font-family:monospace;white-space:pre-wrap'>"
                f"{corps}</pre>"
            )
        },
        timeout=30
    )
    ok = resp.status_code in (200, 201)
    print(f"[NOTIF] Email {'envoyé' if ok else 'ERREUR ' + str(resp.status_code)} : {sujet}")
    return ok


def envoyer_sms(message):
    """Envoie un SMS via Brevo."""
    if not BREVO_API_KEY or not ALERT_PHONE:
        print(f"[NOTIF] SMS non envoyé (config manquante) : {message[:50]}")
        return False

    resp = requests.post(
        BREVO_SMS_URL,
        headers={
            "api-key": BREVO_API_KEY,
            "content-type": "application/json"
        },
        json={
            "type": "transactional",
            "unicodeEnabled": True,
            "sender": "Pipeline",
            "recipient": ALERT_PHONE,
            "content": message[:160]
        },
        timeout=30
    )
    ok = resp.status_code in (200, 201)
    print(f"[NOTIF] SMS {'envoyé' if ok else 'ERREUR ' + str(resp.status_code)} : {message[:50]}")
    return ok


def notifier(projet, etape, message=""):
    """Notification combinée email + SMS pour une GATE."""
    sujet = f"[PIPELINE] {projet} — {etape} prêt"
    corps = (
        f"Projet : {projet}\n"
        f"Étape : {etape}\n"
        f"{message}\n\n"
        "→ Ouvre le fichier GATE correspondant, lis le résumé,\n"
        "  et ajoute ta validation :\n\n"
        "  STATUT: GO      → on continue\n"
        "  STATUT: AJUSTER → je veux des modifications\n"
        "  STATUT: KILL    → on arrête\n\n"
        "Le pipeline reprendra automatiquement au prochain cycle."
    )

    envoyer_email(sujet, corps)
    envoyer_sms(f"{projet} — {etape} prêt. Validation requise.")
