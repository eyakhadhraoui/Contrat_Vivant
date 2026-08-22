from config import settings
from tools.auth_tool import verify_token


def resolve_gestionnaire(token: str | None) -> dict:
    """
    Résout le gestionnaire à partir d'un JWT ou d'un token worker interne.
    """
    if token and isinstance(token, str):
        if token.startswith("Bearer "):
            token = token[7:]
        if settings.INTERNAL_WORKER_TOKEN and token == settings.INTERNAL_WORKER_TOKEN:
            return {
                "gestionnaire_id": "SYSTEM",
                "nom": "Worker",
                "prenom": "Interne",
                "role": "system",
                "agence_id": "AG01",
            }
        try:
            return verify_token(token)
        except Exception as e:
            if settings.REQUIRE_AUTH:
                raise PermissionError(f"Authentification requise : {e}")

    if settings.REQUIRE_AUTH:
        raise PermissionError("Authentification requise : token JWT manquant ou invalide")

    return {
        "gestionnaire_id": "G123",
        "nom": "Khelifi",
        "prenom": "Sarra",
        "role": "assurances",
        "agence_id": "AG01",
    }
