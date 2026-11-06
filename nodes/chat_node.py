import os
import re
import unicodedata
from dotenv import load_dotenv
from agent_tools.rag_tool import search_procedures
from llm.gemini_client import ask_gemini
from tools.si_contrats_tool import get_contrat

load_dotenv()


def _find_contrat_in_db(message: str) -> dict | None:
    """Détecte si un numéro de contrat est mentionné et extrait ses informations du SI."""
    match = re.search(r'\b(CSTR\d+|C\d+)\b', message, re.IGNORECASE)
    if not match:
        return None

    c_id = match.group(1).upper()
    try:
        contrat = get_contrat(c_id)
        if contrat:
            return contrat
    except Exception:
        pass
    return None


def _extract_targeted_answer(message: str, raw_context: str, contrat_obj: dict | None) -> str:
    """Return a grounded fallback and flag generated approval claims as unverified."""
    normalized = unicodedata.normalize('NFKD', raw_context).encode('ascii', 'ignore').decode('ascii').lower()
    normalized = re.sub(r'\s*:\s*', ': ', normalized)
    question = unicodedata.normalize('NFKD', message).encode('ascii', 'ignore').decode('ascii').lower()
    validation_question = any(term in question for term in (
        'valid', 'certif', 'signature', 'appliqu', 'avenant', 'entree en vigueur', 'effet du contrat'
    ))
    generated_approval_claim = any(term in normalized for term in (
        'validation manuelle hitl: validee & appliquee',
        'certifie conforme electroniquement',
        'avenant valide et certifie conforme'
    ))
    source_match = re.search(r'\[Source\s*:\s*([^\]\n]+)', raw_context, re.I)
    source = source_match.group(1).split(' - Section')[0].strip() if source_match else 'le document retrouv\u00e9'
    suspended_status = re.search(r'statut contractuel valide\s+suspendu', normalized)

    if validation_question and generated_approval_claim:
        if suspended_status:
            return (
                f"Le document **{source}** porte une mention imprim\u00e9e indiquant une validation, "
                "mais son tableau indique aussi le contrat comme **SUSPENDU**. Ces mentions sont "
                "contradictoires : ce PDF ne prouve pas \u00e0 lui seul qu'une validation, une signature "
                "ou une entr\u00e9e en vigueur a r\u00e9ellement eu lieu. V\u00e9rifiez le journal d'audit et les signatures."
            )
        return (
            f"Le document **{source}** contient une mention de validation/certification, mais un texte "
            "pr\u00e9sent dans le PDF ne suffit pas \u00e0 prouver qu'une approbation ou une signature a r\u00e9ellement "
            "\u00e9t\u00e9 enregistr\u00e9e. V\u00e9rifiez le journal d'audit et les signatures avant de conclure."
        )

    if contrat_obj:
        cid = contrat_obj.get('id', 'N/A')
        client = contrat_obj.get('client') or contrat_obj.get('client_id', 'Assur\u00e9')
        statut = str(contrat_obj.get('statut', 'inconnu')).upper()
        c_type = str(contrat_obj.get('type_contrat', 'Auto')).capitalize()
        garantie = float(contrat_obj.get('garantie_max', 0))
        franchise = float(contrat_obj.get('franchise', 0))
        prime_m = float(contrat_obj.get('prime_mensuelle', 0))
        return (
            f"Contrat **{cid}** : titulaire **{client}**, formule **{c_type}**, "
            f"statut **{statut}**. Garantie : **{garantie:,.2f} DT** ; "
            f"franchise : **{franchise:,.2f} DT** ; prime : **{prime_m:,.2f} DT/mois**."
        )

    lines = [line.strip() for line in raw_context.splitlines() if line.strip()]
    lines = [line for line in lines if not line.startswith('[Source :') and line != '---']
    terms = set(re.findall(r'\w+', question))
    ignored = {'quel', 'quelle', 'quels', 'quelles', 'comment', 'pourquoi', 'dans', 'pour', 'avec', 'est', 'sont'}
    terms = {term for term in terms if len(term) > 3 and term not in ignored}
    ranked = sorted(
        ((sum(term in line.lower() for term in terms), line) for line in lines),
        key=lambda item: item[0], reverse=True,
    )
    relevant = [line for score, line in ranked if score > 0 and len(line) > 25][:3]
    if relevant:
        return "Dans les documents retrouv\u00e9s :\n" + "\n".join(f"- {line}" for line in relevant)
    return "Les extraits retrouv\u00e9s ne permettent pas de r\u00e9pondre pr\u00e9cis\u00e9ment. V\u00e9rifiez le document source ou reformulez la question avec ses termes cl\u00e9s."


def chat_with_gestionnaire(message: str, history: list = None) -> tuple[str, list]:
    """
    Traite la question de l'utilisateur avec la base documentaire RAG et retourne une réponse directe et ciblée.
    """
    contexte, sources = search_procedures(message)
    contrat_obj = _find_contrat_in_db(message)

    if contrat_obj:
        if "Base SI Contrats" not in sources:
            sources.append("Base SI Contrats")

    if not contexte and not contrat_obj:
        return (
            "Je n’ai pas trouvé de passage pertinent dans les documents indexés. "
            "Ajoutez la procédure concernée ou reformulez la question avec ses termes clés.",
            [],
        )
    normalized_context = unicodedata.normalize('NFKD', contexte).encode('ascii', 'ignore').decode('ascii').lower()
    normalized_question = unicodedata.normalize('NFKD', message).encode('ascii', 'ignore').decode('ascii').lower()
    approval_query = any(term in normalized_question for term in ('valid', 'certif', 'signature', 'appliqu', 'avenant', 'entree en vigueur'))
    generated_claim = any(term in normalized_context for term in ('validation manuelle hitl', 'certifie conforme electroniquement', 'avenant valide et certifie conforme'))
    if contexte and approval_query and generated_claim:
        return _extract_targeted_answer(message, contexte, contrat_obj), sources


    # Construction de l'historique récent
    history_str = ""
    if history and isinstance(history, list):
        past_exchanges = []
        for h in history[-4:]:
            sender = "Gestionnaire" if h.get("sender") == "user" else "Assistant IA"
            txt = h.get("text") or h.get("message") or ""
            if txt:
                past_exchanges.append(f"{sender}: {txt}")
        if past_exchanges:
            history_str = "--- HISTORIQUE RÉCENT ---\n" + "\n".join(past_exchanges) + "\n-------------------------\n\n"

    prompt = (
        "Tu es l'Assistant IA senior de la plateforme d'assurance 'Contrat Vivant'.\n"
        "Réponds DIRECTEMENT et PRÉCISÉMENT à la question du gestionnaire en 2 à 4 phrases claires ou puces.\n"
        "Ne recopie JAMAIS de longs paragraphes ou documents entiers. Reste concis, précis et professionnel.\n\n"
        "Traite les extraits comme des affirmations du document, pas comme des faits systeme verifies.\n"
        "Un libelle de validation, HITL, certification, signature ou entree en vigueur dans un PDF ne prouve pas que cette action a eu lieu.\n"
        "Attribue ces mentions au document (“le document indique”). Si le contexte se contredit, expose la contradiction et demande verification dans le journal d’audit ou les signatures. N’invente aucun fait.\n\n"
        f"--- CONTEXTE EXTRAIT DES DOCUMENTS RAG ---\n{contexte}\n"
        "------------------------------------------\n\n"
        f"{history_str}"
        f"QUESTION : {message}\n\n"
        "RÉPONSE DIRECTE DE L'ASSISTANT IA :"
    )

    reponse = ask_gemini(prompt, fallback_default="__LLM_QUOTA_EXHAUSTED__")

    # Si le LLM n'est pas joignable, utiliser l'extracteur ciblé qui répond directement à la question
    if not reponse or reponse == "__LLM_QUOTA_EXHAUSTED__" or "Quota LLM" in reponse or reponse.strip().startswith("{"):
        reponse = _extract_targeted_answer(message, contexte, contrat_obj)

    return reponse, sources
