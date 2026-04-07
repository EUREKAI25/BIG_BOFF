"""
Tests unitaires — AI_INQUIRY_MODULE
Tous les tests utilisent dry_run=True (aucun appel IA réel).
"""
import sys
import os

# Ajouter le parent du module au path pour les imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from module import (
    run,
    norm,
    is_mentioned,
    extract_entities,
    competitors_from,
    prompt_generate,
    ask_ia,
    extract_citations,
    presence_check,
)


# ── Tests de normalisation ─────────────────────────────────────────────────────

def test_norm_basic():
    assert norm("Toit Mon Toit SARL") == "toit mon toit"
    assert norm("Couverture Bretonne SAS") == "couverture bretonne"
    assert norm("") == ""
    assert norm("RDT COUVERTURE") == "rdt couverture"


def test_norm_accents():
    assert norm("Étanchéité & Toiture") == "etancheite toiture"
    assert norm("Société Générale") == "societe generale"


def test_is_mentioned_exact():
    text = "Nous recommandons Toit Mon Toit pour votre couverture."
    assert is_mentioned(text, "Toit Mon Toit") is True


def test_is_mentioned_fuzzy():
    text = "Vous pouvez contacter Toit-Mon-Toit, une entreprise sérieuse."
    assert is_mentioned(text, "Toit Mon Toit") is True


def test_is_mentioned_not_found():
    text = "Il n'y a aucune entreprise de couverture mentionnée ici."
    assert is_mentioned(text, "Toit Breton Exclusif") is False


def test_is_mentioned_website():
    text = "Visitez toitbreton.fr pour plus d'informations."
    assert is_mentioned(text, "Toit Breton", website="https://toitbreton.fr") is True


# ── Tests d'extraction d'entités ───────────────────────────────────────────────

def test_extract_entities_company():
    text = "Nous recommandons Couverture Bretonne et Toit Breizh pour vos travaux."
    ents = extract_entities(text)
    values = [e["value"] for e in ents]
    assert any("Couverture Bretonne" in v for v in values)


def test_extract_entities_url():
    text = "Consultez https://couverture-rennes.fr pour un devis gratuit."
    ents = extract_entities(text)
    assert any(e["type"] == "url" for e in ents)
    assert any("couverture-rennes.fr" in e.get("domain", "") for e in ents)


def test_extract_entities_stopwords_filtered():
    text = "Consultez Google Maps ou Facebook pour trouver des artisans."
    ents = extract_entities(text)
    values = [e["value"].lower() for e in ents]
    assert "google" not in values
    assert "facebook" not in values


def test_extract_entities_dedup():
    text = "Toit Mon Toit est recommandé. Oui, Toit Mon Toit est bien noté."
    ents = extract_entities(text)
    values = [e["value"].lower() for e in ents]
    assert values.count("toit mon toit") <= 1


# ── Tests competitors_from ─────────────────────────────────────────────────────

def test_competitors_from_excludes_prospect():
    entities = [
        {"type": "company", "value": "Toit Mon Toit"},
        {"type": "company", "value": "Couverture Bretonne"},
    ]
    comps = competitors_from(entities, "Toit Mon Toit")
    assert "Toit Mon Toit" not in comps
    assert "Couverture Bretonne" in comps


def test_competitors_from_excludes_website():
    entities = [
        {"type": "url", "value": "https://toitbreton.fr/contact", "domain": "toitbreton.fr"},
        {"type": "url", "value": "https://concurrent.fr", "domain": "concurrent.fr"},
    ]
    comps = competitors_from(entities, "Toit Breton", website="https://toitbreton.fr")
    assert "toitbreton.fr" not in comps
    assert "concurrent.fr" in comps


# ── Tests prompt_generate ──────────────────────────────────────────────────────

def test_prompt_generate_basic():
    result = prompt_generate(
        "Meilleurs {profession}s à {city} ?",
        {"profession": "couvreur", "city": "Rennes"},
    )
    assert result["questions"] == ["Meilleurs couvreurs à Rennes ?"]
    assert result["payload"]["city"] == "Rennes"


def test_prompt_generate_with_poll():
    result = prompt_generate(
        "Meilleurs {profession}s à {city} ?",
        {"profession": "couvreur", "city": "Rennes"},
        poll_inquiry_datas={"city": "Brest"},
    )
    assert len(result["questions"]) == 2
    assert "Brest" in result["questions"][1]


def test_prompt_generate_missing_key():
    # Clé manquante → question brute (pas d'exception)
    result = prompt_generate(
        "Meilleurs {profession}s à {city} et {region} ?",
        {"profession": "couvreur", "city": "Rennes"},
    )
    assert len(result["questions"]) == 1
    assert result["questions"][0].startswith("Meilleurs")


# ── Tests ask_ia (dry_run) ─────────────────────────────────────────────────────

def test_ask_ia_dry_run():
    inquiry = {"questions": ["Meilleurs couvreurs à Rennes ?"], "payload": {}}
    answers = ask_ia(inquiry, dry_run=True)
    assert len(answers) >= 1
    assert all(a["answer"].startswith("[DRY_RUN:") for a in answers)
    assert all("model" in a and "ts" in a for a in answers)


def test_ask_ia_dry_run_multiple_questions():
    inquiry = {
        "questions": ["Question 1 ?", "Question 2 ?"],
        "payload": {},
    }
    answers = ask_ia(inquiry, dry_run=True)
    # 3 modèles × 2 questions = 6 réponses
    assert len(answers) == 6


# ── Tests extract_citations ────────────────────────────────────────────────────

def test_extract_citations_dedup_across_models():
    answers = [
        {"model": "openai", "answer": "Toit Mon Toit est excellent.", "question": "q", "ts": "t"},
        {"model": "gemini", "answer": "Recommande aussi Toit Mon Toit.", "question": "q", "ts": "t"},
    ]
    citations = extract_citations(answers)
    values = [c["value"].lower() for c in citations]
    assert values.count("toit mon toit") <= 1


def test_extract_citations_from_model_tag():
    answers = [
        {"model": "openai", "answer": "Couverture Bretonne est top.", "question": "q", "ts": "t"},
    ]
    citations = extract_citations(answers)
    assert any(c.get("from_model") == "openai" for c in citations)


# ── Tests presence_check ───────────────────────────────────────────────────────

def test_presence_check_found():
    answers = [
        {"model": "openai", "answer": "Toit Breton est le meilleur couvreur de Rennes.", "question": "q", "ts": "t"},
    ]
    citations = []
    present, comps = presence_check("Toit Breton", answers, citations)
    assert present is True


def test_presence_check_not_found():
    answers = [
        {"model": "openai", "answer": "Couverture Bretonne est recommandée.", "question": "q", "ts": "t"},
    ]
    citations = []
    present, comps = presence_check("Toit Inconnu", answers, citations)
    assert present is False


# ── Test intégration — run() dry_run ──────────────────────────────────────────

def test_run_dry_run_full():
    result = run(
        payload={
            "profession": "couvreur",
            "city": "Rennes",
            "prospect_name": "Toit Breton",
        },
        question_prompt="Quels sont les meilleurs {profession}s à {city} ?",
        dry_run=True,
    )
    assert result["success"] is True
    assert result["error"] is None
    assert "answers" in result["result"]
    assert "citations" in result["result"]
    assert "competitors" in result["result"]
    assert isinstance(result["result"]["prospect_present"], bool)
    assert "DRY_RUN" in result["message"]
    assert result["result"]["meta"]["dry_run"] is True


def test_run_dry_run_with_poll():
    result = run(
        payload={"profession": "plombier", "city": "Lyon", "prospect_name": "Plomb Sud"},
        question_prompt="Meilleurs {profession}s à {city} ?",
        poll_inquiry_datas={"city": "Marseille"},
        dry_run=True,
    )
    assert result["success"] is True
    # 2 questions (base + variante) × 3 modèles = 6 réponses
    assert len(result["result"]["answers"]) == 6


def test_run_contrat_uniforme():
    """Vérifie que le contrat de sortie est toujours respecté."""
    result = run(
        payload={"profession": "electricien", "city": "Paris"},
        question_prompt="Électriciens recommandés à {city} ?",
        dry_run=True,
    )
    assert "success" in result
    assert "result" in result
    assert "message" in result
    assert "error" in result
    # result doit avoir les 6 clés obligatoires
    r = result["result"]
    assert all(k in r for k in ["inquiry_dict", "answers", "citations", "prospect_present", "competitors", "meta"])


def test_run_erreur_gracieuse():
    """Une erreur doit retourner le contrat avec success=False."""
    # question_prompt=None provoque une AttributeError
    result = run(
        payload={"profession": "couvreur"},
        question_prompt=None,  # type: ignore
        dry_run=True,
    )
    assert result["success"] is False
    assert result["result"] is None
    assert result["error"]["code"] == "INTERNAL_ERROR"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
