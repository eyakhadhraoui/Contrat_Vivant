import re
import io
import json
import logging
from PIL import Image

logger = logging.getLogger(__name__)

PRENOM_KEYWORDS = [
    "prenom", "prénom", "first name", "given name",
    "forename", "nombre", "vorname",
    "الاسم", "الإسم", "الاسم الشخصي",
]

NOM_KEYWORDS = [
    "nom", "last name", "surname", "family name",
    "apellido", "nachname",
    "اللقب", "اسم العائلة",
]

ADRESSE_KEYWORDS = [
    "adresse", "address", "residence", "residential address",
    "street", "road", "avenue", "rue",
    "العنوان", "عنوان",
]

ID_NUMBER_KEYWORDS = [
    "cin",
    "id",
    "id number",
    "id no",
    "id no.",
    "identity number",
    "identity no",
    "national id",
    "national identification number",
    "document number",
    "document no",
    "document no.",
    "card number",
    "card no",
    "passport number",
    "passport no",
    "numero",
    "numéro",
    "n°",
    "رقم",
    "رقم البطاقة",
    "رقم التعريف",
]


def _extract_value(line: str, keywords: list[str]) -> str:
    """
    Retire les mots-clés d'une ligne et récupère la valeur restante.
    """
    value = line

    # Trier les mots-clés du plus long au plus court
    # pour éviter qu'un petit mot soit supprimé avant un mot composé.
    for keyword in sorted(keywords, key=len, reverse=True):
        pattern = re.compile(re.escape(keyword), re.IGNORECASE)
        value = pattern.sub("", value)

    value = re.sub(r"[:\-]+", " ", value)
    value = re.sub(r"\s+", " ", value)

    return value.strip()


def _normalize_text(text: str) -> str:
    """
    Normalisation légère du texte OCR.
    """
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _extract_id_number(text: str) -> str:
    """
    Extrait un numéro de document d'identité de manière générique.

    Contrairement à l'ancienne version :
    - ne demande PAS 8 chiffres
    - accepte lettres + chiffres
    - accepte différents formats internationaux
    """

    lines = [line.strip() for line in text.split("\n") if line.strip()]

    # 1. Chercher d'abord un numéro placé après une étiquette connue.
    for line in lines:

        line_lower = line.lower()

        for keyword in ID_NUMBER_KEYWORDS:

            pattern = re.compile(
                rf"{re.escape(keyword)}\s*[:#\-]?\s*([A-Z0-9][A-Z0-9\-\/\s]{{3,25}})",
                re.IGNORECASE
            )

            match = pattern.search(line)

            if match:
                value = match.group(1).strip()

                # Nettoyage
                value = re.sub(r"\s+", " ", value)

                # Éviter de récupérer toute la ligne
                if len(value) >= 4:
                    return value

    # 2. Fallback : chercher des séquences alphanumériques
    # pouvant correspondre à un numéro de document.
    candidates = re.findall(
        r"\b[A-Z0-9][A-Z0-9\-\/]{4,20}\b",
        text.upper()
    )

    # Éliminer les valeurs trop communes
    ignored = {
        "IDENTITY",
        "NATIONAL",
        "PASSPORT",
        "DOCUMENT",
        "NUMBER",
        "NUMERO",
        "CARTE",
        "CARD",
    }

    for candidate in candidates:
        if candidate not in ignored:
            return candidate

    return ""


def extract_cin_info(image_bytes: bytes) -> dict:

    extracted_text = ""

    # ==========================================================
    # 1. OUVERTURE IMAGE
    # ==========================================================

    try:
        img = Image.open(
            io.BytesIO(image_bytes)
        )

        # Vérifier que l'image est valide
        img.verify()

        # Il faut rouvrir l'image après verify()
        img = Image.open(
            io.BytesIO(image_bytes)
        )

    except Exception as e:

        logger.error(
            f"Image invalide : {e}"
        )

        raise ValueError(
            "L'image fournie est invalide ou corrompue."
        )

    # ==========================================================
    # 2. OCR TESSERACT
    # ==========================================================

    try:

        import pytesseract

        languages = [
            "fra+eng+ara",
            "fra+eng",
            "eng"
        ]

        for lang in languages:

            try:

                text = pytesseract.image_to_string(
                    img,
                    lang=lang
                ).strip()

                if text:

                    extracted_text = text

                    logger.info(
                        f"OCR réussi avec {lang}"
                    )

                    break

            except Exception as e:

                logger.warning(
                    f"OCR {lang} échoué : {e}"
                )

    except Exception as e:

        logger.warning(
            f"Tesseract indisponible : {e}"
        )

    # ==========================================================
    # 3. GEMINI VISION
    # ==========================================================

    try:

        from llm.gemini_client import get_client

        client = get_client()

        if not client:

            raise Exception(
                "Client Gemini indisponible"
            )

        prompt = """
Tu es un système professionnel de reconnaissance
de documents d'identité internationaux.

Analyse attentivement l'image.

IMPORTANT :

La pièce d'identité peut provenir de N'IMPORTE QUEL PAYS.

Ne limite surtout pas la détection à la Tunisie.

Accepte par exemple :

- carte nationale tunisienne
- carte nationale française
- carte nationale marocaine
- carte nationale algérienne
- carte nationale italienne
- carte nationale allemande
- carte nationale espagnole
- carte nationale belge
- carte nationale portugaise
- etc.

Le numéro d'identité peut avoir n'importe quel format :

- chiffres
- lettres + chiffres
- tirets
- espaces
- longueur variable.

Ne suppose jamais qu'il doit contenir 8 chiffres.

Ta première tâche est de déterminer si l'image
montre réellement une pièce d'identité officielle.

Une photo quelconque, une facture, un document administratif,
un écran d'ordinateur ou une image sans pièce d'identité
doit être refusé.

Retourne UNIQUEMENT ce JSON :

{
    "document_valide": true,
    "pays": "",
    "type_document": "",
    "nom": "",
    "prenom": "",
    "id_number": "",
    "adresse": ""
}

Si ce n'est pas une pièce d'identité :

{
    "document_valide": false,
    "pays": "",
    "type_document": "",
    "nom": "",
    "prenom": "",
    "id_number": "",
    "adresse": ""
}

Ne devine aucune information.
Si une information n'est pas lisible, laisse-la vide.
"""

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[
                prompt,
                img
            ]
        )

        if not response:

            raise Exception(
                "Gemini n'a retourné aucune réponse"
            )

        if not response.text:

            raise Exception(
                "Gemini a retourné une réponse vide"
            )

        logger.info(
            f"Réponse Gemini : {response.text}"
        )

        # ======================================================
        # EXTRACTION JSON
        # ======================================================

        match = re.search(
            r"\{.*\}",
            response.text,
            re.DOTALL
        )

        if not match:

            raise Exception(
                "Gemini n'a pas retourné de JSON valide"
            )

        data = json.loads(
            match.group(0)
        )

        # ======================================================
        # VALIDATION DOCUMENT
        # ======================================================

        if not data.get(
            "document_valide",
            False
        ):

            raise ValueError(
                "L'image ne semble pas être une "
                "pièce d'identité officielle."
            )

        # ======================================================
        # RETOUR
        # ======================================================

        return {
            "nom": data.get(
                "nom",
                ""
            ),

            "prenom": data.get(
                "prenom",
                ""
            ),

            "id_number": data.get(
                "id_number",
                ""
            ),

            "adresse": data.get(
                "adresse",
                ""
            ),

            "pays": data.get(
                "pays",
                ""
            ),

            "type_document": data.get(
                "type_document",
                ""
            ),

            "raw_text": extracted_text[:300]
        }

    except ValueError:
        raise

    except Exception as e:

        logger.exception(
            f"Erreur Gemini Vision : {e}"
        )

    # ==========================================================
    # 4. FALLBACK OCR
    # ==========================================================

    if extracted_text:

        logger.info(
            "Utilisation du résultat OCR local."
        )

        lines = [
            line.strip()
            for line in extracted_text.split("\n")
            if line.strip()
        ]

        nom = ""
        prenom = ""
        adresse = ""

        for line in lines:

            line_lower = line.lower()

            if not prenom:

                if any(
                    k.lower() in line_lower
                    or k in line
                    for k in PRENOM_KEYWORDS
                ):

                    prenom = _extract_value(
                        line,
                        PRENOM_KEYWORDS
                    )

            if not nom:

                if any(
                    k.lower() in line_lower
                    or k in line
                    for k in NOM_KEYWORDS
                ):

                    nom = _extract_value(
                        line,
                        NOM_KEYWORDS
                    )

            if not adresse:

                if any(
                    k.lower() in line_lower
                    or k in line
                    for k in ADRESSE_KEYWORDS
                ):

                    adresse = _extract_value(
                        line,
                        ADRESSE_KEYWORDS
                    )

        id_number = _extract_id_number(
            extracted_text
        )

        if nom or prenom or id_number:

            return {
                "nom": nom,
                "prenom": prenom,
                "id_number": id_number,
                "adresse": adresse,
                "pays": "",
                "type_document": "",
                "raw_text": extracted_text[:300]
            }

    # ==========================================================
    # 5. ÉCHEC TOTAL
    # ==========================================================

    raise ValueError(
        "Impossible d'extraire les informations du document. "
        "Vérifiez que l'image contient bien une pièce "
        "d'identité et qu'elle est suffisamment lisible."
    )