import io
import json
import logging
import re
import shutil
from pathlib import Path

from PIL import Image

logger = logging.getLogger(__name__)


def _configure_tesseract():
    import pytesseract

    if shutil.which("tesseract"):
        return pytesseract
    # Existing backend processes do not inherit Scoop's updated PATH until restarted.
    candidates = (
        Path.home() / "scoop" / "shims" / "tesseract.exe",
        Path.home() / "scoop" / "apps" / "tesseract" / "current" / "tesseract.exe",
        Path("C:/Program Files/Tesseract-OCR/tesseract.exe"),
    )
    executable = next((path for path in candidates if path.is_file()), None)
    if executable:
        pytesseract.pytesseract.tesseract_cmd = str(executable)
    return pytesseract


def _extract_text_from_image(image: Image.Image) -> str:
    """Run Tesseract with installed languages instead of assuming Arabic exists."""
    try:
        pytesseract = _configure_tesseract()
        installed = set(pytesseract.get_languages(config=""))
        languages = [name for name in ("fra", "eng", "ara") if name in installed]
        if not languages:
            logger.warning("Aucune langue Tesseract (fra/eng/ara) n'est installée")
            return ""
        return pytesseract.image_to_string(image, lang="+".join(languages), config="--psm 6")
    except Exception as exc:
        logger.warning("OCR Tesseract indisponible: %s", exc)
        return ""


def _read_document(file_bytes: bytes):
    is_pdf = file_bytes.startswith(b"%PDF")
    images = []
    extracted_text = ""
    if is_pdf:
        try:
            import pymupdf

            document = pymupdf.open(stream=file_bytes, filetype="pdf")
            if document.page_count > 10:
                raise ValueError("Le PDF doit contenir au maximum 10 pages.")
            text_pages = []
            for page in document:
                page_text = page.get_text("text")
                text_pages.append(page_text)
                if page_text.strip() or len(images) >= 3:
                    continue
                pix = page.get_pixmap(matrix=pymupdf.Matrix(2, 2), alpha=False)
                images.append(Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB"))
            extracted_text = "\n".join(text_pages).strip()
            if not extracted_text:
                extracted_text = "\n".join(_extract_text_from_image(img) for img in images).strip()
        except ValueError:
            raise
        except Exception as exc:
            logger.warning("Lecture PDF impossible, tentative OCR directe: %s", exc)
    else:
        try:
            images = [Image.open(io.BytesIO(file_bytes)).convert("RGB")]
            extracted_text = _extract_text_from_image(images[0]).strip()
        except Exception as exc:
            raise ValueError("Le fichier doit être une image JPG/PNG ou un PDF lisible.") from exc
    return extracted_text, images


def _empty_vehicle():
    return {"immatriculation": None, "souscripteur": None, "marque_modele": None, "degats_apparents": None}


def _parse_labeled_text(text: str) -> dict:
    """Small deterministic fallback for readable, explicitly labeled CAA fields."""
    def find(pattern):
        match = re.search(pattern, text, re.I | re.M)
        return match.group(1).strip(" \t:;-.") if match else None

    def vehicle(letter):
        return {
            "immatriculation": find(rf"(?:immatriculation|matricule|plaque)\s*(?:du\s*)?(?:vehicule\s*)?{letter}\s*[:=-]\s*([^\r\n]+)"),
            "souscripteur": find(rf"(?:conducteur|conductrice|assure|souscripteur)\s*{letter}\s*[:=-]\s*([^\r\n]+)"),
            "marque_modele": find(rf"(?:marque\s*/\s*modele|modele)\s*{letter}\s*[:=-]\s*([^\r\n]+)"),
            "degats_apparents": find(rf"(?:degats?|dommages?)\s*(?:visibles\s*)?{letter}\s*[:=-]\s*([^\r\n]+)"),
        }

    field_labels = r"conducteur|conductrice|souscripteur|immatriculation|matricule|plaque|marque\s*/?\s*modele|modele|degats?(?:\s+visibles)?|dommages?|circonstances?"

    def collect(pattern):
        return [value.strip(" \t:;.-") for value in re.findall(
            rf"(?:{pattern})\s*[:=-]\s*(.+?)(?=\s+(?:{field_labels})\s*[:=-]|[\r\n]|$)",
            text, re.I | re.M
        ) if value.strip(" \t:;.-")]

    vehicles = [vehicle("A"), vehicle("B")]
    for key, pattern in (
        ("immatriculation", r"immatriculation|matricule|plaque"),
        ("souscripteur", r"conducteur|conductrice|souscripteur"),
        ("marque_modele", r"marque\s*/?\s*modele|modele"),
        ("degats_apparents", r"degats?(?:\s+visibles)?|dommages?"),
    ):
        for index, value in enumerate(collect(pattern)[:2]):
            vehicles[index][key] = vehicles[index][key] or value

    date = find(r"date(?:\s+de\s+l'accident)?\s*[:=-]\s*(\d{1,2}[/-]\d{1,2}[/-]\d{4})")
    if date:
        day, month, year = re.split(r"[/-]", date)
        date = f"{year}-{int(month):02d}-{int(day):02d}"
    return {
        "date_accident": date,
        "lieu_accident": find(r"lieu\s*[:=-]\s*([^\r\n]+)"),
        "vehicule_a": vehicles[0],
        "vehicule_b": vehicles[1],
        "circonstances": collect(r"circonstances?"),
        "responsabilite_estimee": None,
        "observations_expert": None,
    }


def _ocr_engine_ready() -> bool:
    try:
        pytesseract = _configure_tesseract()
        return bool(set(pytesseract.get_languages(config="")) & {"fra", "eng"})
    except Exception:
        return False


def _vision_service_ready() -> bool:
    try:
        from llm.gemini_client import get_client

        return get_client() is not None
    except Exception:
        return False


def _ask_vision(images):
    if not images:
        return None
    try:
        from llm.gemini_client import get_client

        client = get_client()
        if not client:
            return None
        prompt = """Lis ce constat amiable et restitue uniquement un JSON strict. Ne complète jamais une information absente ou illisible: utilise null. N'attribue aucune responsabilité sans éléments explicites; sinon null.
{"date_accident":null,"lieu_accident":null,"vehicule_a":{"immatriculation":null,"souscripteur":null,"marque_modele":null,"degats_apparents":null},"vehicule_b":{"immatriculation":null,"souscripteur":null,"marque_modele":null,"degats_apparents":null},"circonstances":[],"responsabilite_estimee":null,"observations_expert":null}"""
        for model in ("gemini-2.0-flash", "gemini-1.5-flash", "gemini-flash-latest"):
            try:
                response = client.models.generate_content(model=model, contents=[prompt, *images[:3]])
                if response and response.text:
                    match = re.search(r"\{.*\}", response.text, re.S)
                    if match:
                        return json.loads(match.group(0))
            except Exception as exc:
                logger.info("Gemini vision (%s) indisponible: %s", model, exc)
    except Exception as exc:
        logger.info("Gemini vision non disponible: %s", exc)
    return None


def extract_constat_info(file_bytes: bytes) -> dict:
    """Extract a CAA from a text PDF, scanned PDF, or image without inventing fields."""
    extracted_text, images = _read_document(file_bytes)
    result = _ask_vision(images)

    if not result and extracted_text:
        labeled = _parse_labeled_text(extracted_text)
        if any((labeled.get("date_accident"), labeled.get("lieu_accident"),
                labeled["vehicule_a"].get("immatriculation"), labeled["vehicule_b"].get("immatriculation"))):
            result = labeled

    if not result and extracted_text:
        try:
            from llm.gemini_client import ask_gemini

            prompt = f"""Extrais les informations du constat depuis le texte ci-dessous. Réponds en JSON strict avec les clés date_accident, lieu_accident, vehicule_a, vehicule_b, circonstances, responsabilite_estimee, observations_expert. Les quatre champs des véhicules sont immatriculation, souscripteur, marque_modele, degats_apparents. N'invente rien: mets null si absent/illisible et [] pour circonstances inconnues. La responsabilité doit rester null sans éléments explicites.
TEXTE:\n{extracted_text[:10000]}"""
            raw = ask_gemini(prompt)
            match = re.search(r"\{.*\}", raw or "", re.S)
            if match:
                candidate = json.loads(match.group(0))
                if isinstance(candidate.get("vehicule_a"), dict) or isinstance(candidate.get("vehicule_b"), dict):
                    result = candidate
        except Exception as exc:
            logger.info("Structuration texte Gemini indisponible: %s", exc)

    if not result and images and not extracted_text and not _ocr_engine_ready() and not _vision_service_ready():
        raise ValueError("Lecture OCR indisponible sur ce serveur : installez Tesseract avec les langues fra/eng, ou configurez GOOGLE_API_KEY pour lire les scans par IA.")

    if not result or not any((result.get("date_accident"), result.get("lieu_accident"),
                              (result.get("vehicule_a") or {}).get("immatriculation"),
                              (result.get("vehicule_b") or {}).get("immatriculation"))):
        labeled = _parse_labeled_text(extracted_text) if extracted_text else None
        if labeled and any((labeled.get("date_accident"), labeled.get("lieu_accident"),
                            labeled["vehicule_a"].get("immatriculation"), labeled["vehicule_b"].get("immatriculation"))):
            result = labeled
    if not result:
        result = {
            "date_accident": None,
            "lieu_accident": None,
            "vehicule_a": _empty_vehicle(),
            "vehicule_b": _empty_vehicle(),
            "circonstances": [],
            "responsabilite_estimee": None,
            "observations_expert": "Aucune donnée exploitable n'a été reconnue. Vérifiez la qualité du scan ou saisissez les informations manuellement.",
        }
    result.setdefault("vehicule_a", _empty_vehicle())
    result.setdefault("vehicule_b", _empty_vehicle())
    for key in ("vehicule_a", "vehicule_b"):
        vehicle = result[key] if isinstance(result[key], dict) else {}
        result[key] = {**_empty_vehicle(), **vehicle}
    result.setdefault("circonstances", [])
    result.setdefault("responsabilite_estimee", None)
    result.setdefault("date_accident", None)
    result.setdefault("lieu_accident", None)
    result.setdefault("observations_expert", None)
    # OCR may report facts, but liability allocation must be reviewed by a human.
    result["responsabilite_estimee"] = None
    result["texte_extrait"] = extracted_text[:10000]
    result["nb_caracteres_extraits"] = len(extracted_text)
    return result
