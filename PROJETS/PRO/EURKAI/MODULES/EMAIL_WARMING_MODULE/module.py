"""
EMAIL_WARMING_MODULE — Core Engine
Warming bidirectionnel : envoi depuis senders Brevo/SMTP + réponse auto depuis receivers IMAP.
Project-agnostic, pluggable dans tout scheduler APScheduler.

Usage minimal :
    from email_warming_module.module import WarmingEngine
    engine = WarmingEngine(db_session, brevo_api_key="...")
    engine.run_session(pool_id="my-pool")
"""
import imaplib
import json
import logging
import random
import re
from datetime import datetime, timedelta
from typing import Optional

log = logging.getLogger("warming.engine")

# ── Contenu des emails de warming ─────────────────────────────────────────

_SUBJECTS = [
    "Bonjour, une question rapide",
    "Retour sur notre échange",
    "Quelques informations utiles",
    "Suite à notre conversation",
    "Point rapide",
    "Question concernant votre activité",
    "Votre présence en ligne",
    "Un sujet qui pourrait vous intéresser",
]

_BODIES = [
    "Bonjour,\n\nJ'espère que vous allez bien. Je voulais vous contacter concernant votre visibilité en ligne.\n\nN'hésitez pas à me répondre si vous souhaitez en savoir plus.\n\nCordialement",
    "Bonjour,\n\nFaisant suite à notre échange précédent, je me permets de vous recontacter.\n\nJe reste disponible pour toute question.\n\nBonne journée",
    "Bonjour,\n\nJe vous fais parvenir quelques informations qui pourraient vous intéresser concernant votre activité en ligne.\n\nÀ votre disposition,\nCordialement",
    "Bonjour,\n\nUne question rapide : avez-vous eu l'occasion de consulter les informations que je vous ai transmises ?\n\nJe reste à votre disposition.\n\nCordialement",
    "Bonjour,\n\nJe me permets de revenir vers vous pour faire un point rapide sur nos échanges.\n\nBien à vous",
    "Bonjour,\n\nJ'espère que cette semaine se passe bien pour vous. Je souhaitais vous partager quelques éléments concernant votre activité.\n\nCordialement",
]

_REPLIES = [
    "Bonjour,\n\nMerci pour votre message, je l'ai bien reçu.\n\nJe vous recontacte dès que possible.\n\nCordialement",
    "Bonjour,\n\nBien reçu, merci.\n\nJe reviendrai vers vous prochainement.\n\nBonne journée",
    "Bonjour,\n\nMerci de votre retour. Je prends note et vous réponds dans les meilleurs délais.\n\nCordialement",
    "Bonjour,\n\nMessage bien reçu. Je vous confirme que je traiterai votre demande très prochainement.\n\nBien à vous",
    "Bonjour,\n\nMerci pour ces informations. Je reviens vers vous rapidement.\n\nCordialement",
    "Bonjour,\n\nBien noté, merci. Je reste disponible si vous avez des questions.\n\nCordialement",
]


class WarmingEngine:
    """
    Moteur de warming email bidirectionnel.

    :param db: SQLAlchemy Session
    :param brevo_api_key: Clé API Brevo (envoi via API REST)
    :param smtp_credentials: dict {email: {host, port, user, password}} pour envoi SMTP direct
    """

    def __init__(self, db, brevo_api_key: str = "", smtp_credentials: dict = None):
        self.db = db
        self.brevo_key = brevo_api_key
        self.smtp_creds = smtp_credentials or {}

    def _warming_day(self, pool) -> int:
        if not pool.start_date:
            return 1
        return (datetime.utcnow().date() - pool.start_date.date()).days + 1

    def _emails_per_session(self, pool) -> int:
        """Nombre d'emails à envoyer par session selon le ramp-up schedule."""
        day = self._warming_day(pool)
        try:
            schedule = json.loads(pool.ramp_schedule)
            schedule.sort(key=lambda x: x["day"], reverse=True)
            for step in schedule:
                if day >= step["day"]:
                    return step["eps"]
        except Exception:
            pass
        return 4  # défaut

    def _send_via_brevo(self, sender_email: str, sender_name: str,
                        to_email: str, subject: str, body: str,
                        extra_headers: dict = None) -> bool:
        try:
            import requests
            headers_payload = {"X-Warming": "1"}
            if extra_headers:
                headers_payload.update(extra_headers)
            resp = requests.post(
                "https://api.brevo.com/v3/smtp/email",
                headers={"api-key": self.brevo_key, "Content-Type": "application/json"},
                json={
                    "sender":      {"name": sender_name, "email": sender_email},
                    "to":          [{"email": to_email}],
                    "subject":     subject,
                    "textContent": body,
                    "headers":     headers_payload,
                },
                timeout=10,
            )
            return resp.status_code in (200, 201, 202)
        except Exception as e:
            log.warning("brevo send %s→%s: %s", sender_email, to_email, e)
            return False

    def _process_receiver_imap(self, receiver, brevo_key: str = None) -> tuple[int, int]:
        """
        Connecte à la boîte IMAP du receiver :
        1. Cherche les emails de warming non lus (header X-Warming)
        2. Marque comme lus
        3. Si auto_reply=True, envoie une réponse vers l'expéditeur original
        Retourne (received, replied).
        """
        import email as _email_lib
        received = 0
        replied = 0
        key = brevo_key or self.brevo_key

        try:
            conn = imaplib.IMAP4_SSL(receiver.imap_host, receiver.imap_port)
            conn.login(receiver.email, receiver.imap_password)
            conn.select("INBOX")

            _, data = conn.search(None, '(UNSEEN HEADER X-Warming 1)')
            if not data or not data[0]:
                conn.logout()
                return 0, 0

            uids = data[0].split()
            received = len(uids)

            for uid in uids:
                try:
                    if receiver.auto_reply and key:
                        _, msg_data = conn.fetch(uid, "(RFC822)")
                        raw = msg_data[0][1]
                        msg = _email_lib.message_from_bytes(raw)
                        from_addr = msg.get("From", "")
                        m = re.search(r"<([^>]+)>", from_addr)
                        reply_to = m.group(1) if m else from_addr.strip()
                        orig_subject = msg.get("Subject", "Message")
                        reply_subject = orig_subject if orig_subject.startswith("Re:") else f"Re: {orig_subject}"

                        if reply_to and "@" in reply_to:
                            ok = self._send_via_brevo(
                                sender_email=receiver.email,
                                sender_name=receiver.display_name or receiver.email.split("@")[0].capitalize(),
                                to_email=reply_to,
                                subject=reply_subject,
                                body=random.choice(_REPLIES),
                                extra_headers={"X-Warming-Reply": "1"},
                            )
                            if ok:
                                replied += 1
                except Exception as e:
                    log.debug("warming reply uid=%s: %s", uid, e)

            # Marquer tous comme lus
            conn.store(",".join(u.decode() for u in uids), "+FLAGS", "\\Seen")
            conn.logout()

        except Exception as e:
            log.warning("warming IMAP %s: %s", receiver.email, e)

        return received, replied

    def run_session(self, pool_id: str) -> dict:
        """
        Exécute une session de warming pour un pool donné.
        Retourne les stats de la session {sent, received, replied, errors, day}.
        """
        from .database import (db_get_pool, db_list_senders, db_list_receivers,
                               db_log_session, db_update_pool)

        pool = db_get_pool(self.db, pool_id)
        if not pool or pool.status != "active":
            return {"ok": False, "reason": "pool inactif ou inexistant"}

        # Initialiser start_date si première session
        if not pool.start_date:
            pool.start_date = datetime.utcnow()
            self.db.commit()

        day = self._warming_day(pool)
        eps = self._emails_per_session(pool)

        senders   = db_list_senders(self.db, pool_id)
        receivers = db_list_receivers(self.db, pool_id)

        if not senders or not receivers:
            return {"ok": False, "reason": "pas de senders ou receivers configurés"}

        # Sélectionner un sous-ensemble aléatoire de senders
        selected = random.sample(senders, min(eps * 2, len(senders)))

        sent = 0
        errors = 0

        for sender in selected:
            receiver = random.choice(receivers)
            subject  = random.choice(_SUBJECTS)
            body     = random.choice(_BODIES)
            name     = sender.display_name or sender.email.split("@")[0].capitalize()

            ok = self._send_via_brevo(
                sender_email=sender.email,
                sender_name=name,
                to_email=receiver.email,
                subject=subject,
                body=body,
            )
            if ok:
                sent += 1
                sender.sent_total += 1
            else:
                errors += 1

        self.db.commit()

        # Traiter les réponses IMAP
        total_received = 0
        total_replied  = 0
        for receiver in receivers:
            rcv, rpl = self._process_receiver_imap(receiver)
            total_received += rcv
            total_replied  += rpl
            receiver.received_total += rcv
            receiver.replied_total  += rpl

        # Mettre à jour le pool
        pool.last_session_at = datetime.utcnow()
        pool.total_sent    += sent
        pool.total_replied += total_replied
        self.db.commit()

        # Logger la session
        db_log_session(self.db, pool_id, day, sent, total_received, total_replied, errors)

        log.info("warming [%s] day=%d eps=%d → sent=%d received=%d replied=%d errors=%d",
                 pool.name, day, eps, sent, total_received, total_replied, errors)

        return {
            "ok": True, "day": day, "eps": eps,
            "sent": sent, "received": total_received,
            "replied": total_replied, "errors": errors,
        }

    @staticmethod
    def scheduler_job(pool_id: str, db_url: str, brevo_api_key: str):
        """
        Wrapper statique pour intégration APScheduler.
        Usage: scheduler.add_job(WarmingEngine.scheduler_job, args=[pool_id, db_url, key])
        """
        from .database import make_session
        Session = make_session(db_url)
        db = Session()
        try:
            engine = WarmingEngine(db, brevo_api_key=brevo_api_key)
            engine.run_session(pool_id)
        finally:
            db.close()
