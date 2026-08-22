def peut_acceder_au_contrat(gestionnaire_role: str, contrat: dict, gestionnaire_agence_id: str | None = None) -> bool:
    """
    Contrôle l'accès au contrat selon le rôle et l'agence.
    - Un gestionnaire assurances voit les contrats de son agence.
    - Un gestionnaire sinistres peut consulter un contrat de son agence pour l'analyse croisée.
    """
    if not contrat:
        return False

    contrat_agence_id = contrat.get("agence_id")
    if gestionnaire_agence_id and contrat_agence_id and gestionnaire_agence_id != contrat_agence_id:
        return False

    return gestionnaire_role in {"assurances", "sinistres"}


def peut_valider_alerte(gestionnaire_role: str, event_type: str) -> bool:
    """
    Vérifie si CE gestionnaire a le droit de valider CETTE alerte,
    selon le type d'événement détecté (BF08 + BNF06).
    """
    mapping = {
        "contrat": "assurances",
        "sinistre": "sinistres",
        "risque": "sinistres",  # les cas "risque" sont pilotés par sinistres par défaut
    }
    role_requis = mapping.get(event_type)
    return gestionnaire_role == role_requis


def peut_ajouter_contrat(gestionnaire_role: str) -> bool:
    """Seul un gestionnaire ASSURANCES peut ajouter un contrat."""
    return gestionnaire_role == "assurances"


def peut_modifier_contrat(gestionnaire_role: str) -> bool:
    """Seul un gestionnaire ASSURANCES peut modifier un contrat."""
    return gestionnaire_role == "assurances"


def peut_ajouter_sinistre(gestionnaire_role: str) -> bool:
    """Seul un gestionnaire SINISTRES peut ajouter un sinistre."""
    return gestionnaire_role == "sinistres"


def peut_modifier_sinistre(gestionnaire_role: str) -> bool:
    """Un gestionnaire SINISTRES et le gestionnaire ASSURANCES créateur du contrat peuvent modifier un sinistre.

    Dans ce prototype, on autorise à la fois les rôles 'sinistres' et 'assurances' à modifier un sinistre
    (la logique fine d'autorisation par gestionnaire créateur peut être ajoutée plus tard).
    """
    return gestionnaire_role in {"sinistres", "assurances"}

