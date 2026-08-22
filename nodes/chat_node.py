import os
import re
from dotenv import load_dotenv
from agent_tools.rag_tool import search_procedures
from llm.gemini_client import ask_gemini
from tools.si_contrats_tool import get_contrat

load_dotenv()


def _find_contrat_in_db(message: str) -> str:
    """Détecte si un numéro de contrat est mentionné et extrait ses informations du SI."""
    match = re.search(r'\b(CSTR\d+)\b', message, re.IGNORECASE)
    if not match:
        return ""

    c_id = match.group(1).upper()
    try:
        contrat = get_contrat(c_id)
        if contrat:
            return (
                f"\n--- INFORMATIONS SYSTÈME DU CONTRAT ({c_id}) ---\n"
                f"• ID Contrat : {contrat.get('id')}\n"
                f"• Client : {contrat.get('client') or contrat.get('client_id')}\n"
                f"• Type : {contrat.get('type_contrat', 'auto').upper()}\n"
                f"• Statut : {contrat.get('statut', 'actif').upper()}\n"
                f"• Plafond Garantie Max : {contrat.get('garantie_max', 0)} DT\n"
                f"• Franchise : {contrat.get('franchise', 0)} DT\n"
                f"• Prime Mensuelle : {contrat.get('prime_mensuelle', 0)} DT\n"
                f"• Date Début : {contrat.get('date_debut')}\n"
                f"• Date Fin : {contrat.get('date_fin')}\n"
                f"• Agence ID : {contrat.get('agence_id')}\n"
                f"--------------------------------------------------\n"
            )
    except Exception:
        pass
    return ""


def chat_with_gestionnaire(message: str, history: list = None) -> tuple[str, list]:
    """
    Traite la question de l'utilisateur avec la base documentaire RAG et retourne (reponse, sources).
    """
    contexte, sources = search_procedures(message)
    db_contrat_info = _find_contrat_in_db(message)

    if db_contrat_info:
        contexte = db_contrat_info + "\n\n" + (contexte if contexte != 'Aucune procédure correspondante trouvée.' else "")
        if "Base SI Contrats" not in sources:
            sources.append("Base SI Contrats")

    # Construction du fil de discussion précédent si disponible
    history_str = ""
    if history and isinstance(history, list):
        past_exchanges = []
        for h in history[-4:]:
            sender = "Gestionnaire" if h.get("sender") == "user" else "Assistant IA"
            txt = h.get("text") or h.get("message") or ""
            if txt:
                past_exchanges.append(f"{sender}: {txt}")
        if past_exchanges:
            history_str = "--- HISTORIQUE RÉCENT DE LA CONVERSATION ---\n" + "\n".join(past_exchanges) + "\n--------------------------------------------\n\n"

    prompt = (
        "Tu es l'Assistant IA senior pour la plateforme 'Contrat Vivant', spécialisé dans la gestion des assurances, des sinistres et l'analyse de documents réglementaires/contractuels.\n"
        "Ta mission est d'assister les gestionnaires d'assurances et de sinistres avec précision, clarté et professionnalisme.\n\n"
        "CONSIGNES DE RÉPONSE :\n"
        "1. Appuie-toi prioritairement sur le contexte documentaire ci-dessous (PDFs et documents uploadés) pour étayer ta réponse.\n"
        "2. Formate ta réponse de manière structurée avec des puces, des sections et des mises en gras pour une lisibilité parfaite.\n"
        "3. Cite explicitement les documents ou sections sources lorsque c'est pertinent.\n"
        "4. Fournis des conseils pratiques et opérationnels de gestion du risque ou d'indemnisation.\n"
        "5. Si l'information n'est pas directement présente dans les documents RAG, réponds de façon experte selon la réglementation des assurances tout en le mentionnant courtoisement.\n\n"
        f"--- DOCUMENTS ET PROCÉDURES INTERNES (BASE DE CONNAISSANCE RAG) ---\n{contexte}\n"
        "-------------------------------------------------------------------\n\n"
        f"{history_str}"
        f"QUESTION DU GESTIONNAIRE : {message}\n\n"
        "RÉPONSE EXPERTE DE L'ASSISTANT IA (En français, structurée et précise) :"
    )

    reponse = ask_gemini(prompt, fallback_default="__LLM_QUOTA_EXHAUSTED__")

    if not reponse or reponse == "__LLM_QUOTA_EXHAUSTED__" or "Quota LLM" in reponse:
        if contexte and contexte != 'Aucune procédure correspondante trouvée.':
            # Nettoyage des balises internes pour une lisibilité parfaite
            clean_ctx = contexte.replace('%PDF-1.4', '').replace('%%EOF', '').strip()
            reponse = (
                "📋 **[Informations Extraites de la Base Documentaire RAG & SI]** :\n\n"
                f"{clean_ctx}\n\n"
                "*(Extraits précis issus directement de vos documents indexés)*"
            )
        else:
            reponse = "Aucun document ou information spécifique n'a été trouvé dans la base RAG pour cette requête."

    return reponse, sources
