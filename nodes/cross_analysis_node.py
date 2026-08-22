"""
Noeud cross_analysis : combine le moteur de regles deterministe (rules_engine)
ET une analyse LLM complementaire (build_cross_analysis_prompt).

CORRECTIF 1 : le LLM n'etait jusqu'ici jamais appele (prompt defini mais mort).
CORRECTIF 2 (critique) : meme apres avoir fusionne les anomalies dans
state["anomalies"], le dict `risk` conserve dans state["risk_analysis"]
gardait risk["anomalies"] = UNIQUEMENT les anomalies du moteur de regles.
Or urgency_node.py lit risk["anomalies"] (pas state["anomalies"]) et
ECRASE state["anomalies"] avec cette version tronquee -> les anomalies LLM
disparaissaient silencieusement. On met donc a jour risk["anomalies"]
en place avant de le stocker dans le state.
"""

import json
from datetime import date

from llm.gemini_client import ask_gemini
from llm.prompts.cross_analysis_prompt import build_cross_analysis_prompt
from tools.audit_log_tool import log_decision
from tools.analysis_helpers import run_cross_analysis


def _parse_llm_anomalies(raw_text: str) -> list:
    """Parse la reponse Gemini en tolerant les fences ```json ... ``` eventuelles.
    Retourne une liste vide (jamais une exception) si le parsing echoue —
    une erreur LLM ne doit jamais casser le pipeline."""
    if not raw_text:
        return []

    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`").strip()
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].strip()

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        return []

    anomalies = data.get("anomalies", []) if isinstance(data, dict) else []
    return [
        a for a in anomalies
        if isinstance(a, dict) and a.get("rule") and a.get("message") and a.get("severity")
    ]


def cross_analysis(state):
    contrat = state.get("contrat_data", {})
    sinistres = state.get("sinistres_data", [])

    # 1. Analyse deterministe (moteur de regles) — inchangee, source de verite du score.
    risk = run_cross_analysis(contrat, sinistres)
    rule_based_anomalies = risk.get("anomalies", [])
    existing_rule_names = {a["rule"] for a in rule_based_anomalies}

    # 2. Analyse LLM complementaire — signale des anomalies que les regles fixes ne couvrent pas.
    llm_anomalies = []
    llm_error = None
    try:
        prompt = build_cross_analysis_prompt(contrat, sinistres, date.today().isoformat())
        raw_response = ask_gemini(prompt)
        llm_anomalies = [
            a for a in _parse_llm_anomalies(raw_response)
            if a["rule"] not in existing_rule_names  # evite les doublons avec le moteur de regles
        ]
    except Exception as exc:  # une panne LLM ne doit jamais bloquer le dossier
        llm_error = str(exc)

    combined_anomalies = rule_based_anomalies + llm_anomalies

    # CORRECTIF CRITIQUE : mettre a jour le dict risk lui-meme, pas seulement state["anomalies"],
    # car urgency_node.py relit risk["anomalies"] depuis state["risk_analysis"] et ecraserait
    # sinon la fusion qu'on vient de faire.
    risk["anomalies"] = combined_anomalies

    state["risk_analysis"] = risk
    state["anomalies"] = combined_anomalies
    state["alert_card"] = risk.get("alert_card", {})
    state["missing_data"] = risk.get("missing_data", [])

    log_decision("cross_analysis", {
        "score": risk.get("score"),
        "urgency_level": risk.get("urgency_level"),
        "confidence": risk.get("confidence"),
        "nb_anomalies_regles": len(rule_based_anomalies),
        "nb_anomalies_llm": len(llm_anomalies),
        "llm_error": llm_error,
        "source": "risk_analyzer+llm",
    })
    return state
