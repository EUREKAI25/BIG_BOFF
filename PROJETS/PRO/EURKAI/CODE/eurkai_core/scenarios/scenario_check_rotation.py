"""
scenario_check_rotation
Vérifie les clés dont la rotation est échue.
Alerte par email (Brevo) et/ou SMS au responsable sécurité.
Fallback : EURKAI_EMAIL_NATHALIE + ALERT_PHONE.
À planifier en cron mensuel.
"""

import os
import sys
import json
from pathlib import Path
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

sys.path.insert(0, str(Path(__file__).parent.parent))

from catalog.load_catalog import load_catalog
from core.functions.prompt_execute import _load_env

_ENV_PATH = Path("/Users/nathalie/Dropbox/____BIG_BOFF___/.env")

NEXT_ROTATION = {
    "monthly":   lambda d: d + relativedelta(months=1),
    "quarterly": lambda d: d + relativedelta(months=3),
    "on_event":  None,
    "never":     None,
}


def run(dry_run=False, verbose=True):
    _load_env()
    catalog = load_catalog()
    storage = catalog["_storage"]
    today   = date.today()

    overdue = []
    upcoming = []  # dans les 7 prochains jours

    for key, item in storage.get_all("env_item").items():
        policy    = item.get("envitem_rotation_policy")
        rotated   = item.get("envitem_rotated_at")
        alert     = item.get("envitem_alert_on_expiry", False)
        sensitive = item.get("envitem_sensitive", False)

        if not alert or policy in (None, "never", "on_event"):
            continue
        if not rotated:
            continue

        fn = NEXT_ROTATION.get(policy)
        if fn is None:
            continue

        rotated_date = date.fromisoformat(rotated)
        next_date    = fn(rotated_date)

        days_left = (next_date - today).days

        if days_left < 0:
            overdue.append({"key": key, "policy": policy,
                            "rotated_at": rotated, "next": str(next_date),
                            "days_overdue": abs(days_left)})
        elif days_left <= 7:
            upcoming.append({"key": key, "policy": policy,
                             "rotated_at": rotated, "next": str(next_date),
                             "days_left": days_left})

    if verbose:
        print(f"=== scenario_check_rotation — {today} ===")
        print(f"  En retard     : {len(overdue)}")
        print(f"  Dans 7 jours  : {len(upcoming)}")
        for e in overdue:
            print(f"  ⚠ {e['key']} — {e['days_overdue']}j de retard (policy: {e['policy']})")
        for e in upcoming:
            print(f"  → {e['key']} — dans {e['days_left']}j (policy: {e['policy']})")

    if (overdue or upcoming) and not dry_run:
        _send_alert(overdue, upcoming, today)

    return {"overdue": overdue, "upcoming": upcoming, "checked_at": str(today)}


def _send_alert(overdue, upcoming, today):
    """Alerte email via Brevo. Fallback : EURKAI_EMAIL_NATHALIE."""
    brevo_key     = os.environ.get("BREVO_API_KEY")
    alert_emails  = os.environ.get("ALERT_EMAILS", "")
    fallback_email = os.environ.get("EURKAI_EMAIL_NATHALIE", "")
    alert_phone   = os.environ.get("ALERT_PHONE", "")

    recipients = [e.strip() for e in alert_emails.split(",") if e.strip()]
    if not recipients and fallback_email:
        recipients = [fallback_email]

    subject = f"[EURKAI SÉCURITÉ] Rotation de clés — {len(overdue)} en retard"

    lines = [f"Date : {today}", ""]
    if overdue:
        lines.append("⚠ CLÉS EN RETARD DE ROTATION :")
        for e in overdue:
            lines.append(f"  - {e['key']} ({e['policy']}) — {e['days_overdue']}j de retard")
    if upcoming:
        lines.append("")
        lines.append("→ À RENOUVELER DANS 7 JOURS :")
        for e in upcoming:
            lines.append(f"  - {e['key']} ({e['policy']}) — dans {e['days_left']}j")
    lines += ["", "Action requise : générer la nouvelle clé sur la console du provider, puis mettre à jour secrets.env."]

    body = "\n".join(lines)

    if brevo_key and recipients:
        _send_via_brevo(brevo_key, recipients, subject, body)
    else:
        print(f"[ALERTE — email non envoyé, Brevo non configuré]\n{body}")

    # SMS — coming (infrastructure SMS à connecter)
    if alert_phone:
        print(f"[SMS coming] → {alert_phone} : {len(overdue)} clé(s) en retard de rotation")


def _send_via_brevo(api_key, recipients, subject, body):
    """Envoi email via Brevo API."""
    try:
        import requests
        payload = {
            "sender": {"name": "EURKAI Sécurité", "email": "security@eurkai.com"},
            "to": [{"email": r} for r in recipients],
            "subject": subject,
            "textContent": body,
        }
        resp = requests.post(
            "https://api.brevo.com/v3/smtp/email",
            headers={"api-key": api_key, "Content-Type": "application/json"},
            json=payload,
            timeout=10,
        )
        if resp.status_code in (200, 201):
            print(f"[OK] Alerte envoyée à : {', '.join(recipients)}")
        else:
            print(f"[FAIL] Brevo {resp.status_code} : {resp.text[:200]}")
    except Exception as e:
        print(f"[FAIL] Envoi email : {e}")


if __name__ == "__main__":
    dry = "--dry" in sys.argv
    result = run(dry_run=dry)
    print(json.dumps(result, indent=2, ensure_ascii=False))
