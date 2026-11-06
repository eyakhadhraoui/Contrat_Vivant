"""Cominty-powered insurance contract analysis workflow."""
from __future__ import annotations

import json
import os
import re
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, File, Header, HTTPException, Query, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel, Field
from pypdf import PdfReader

router = APIRouter(prefix="/contract-analysis", tags=["Cominty contract analysis"])
DATA_DIR = Path(__file__).resolve().parents[1] / "data"
DB_PATH = DATA_DIR / "contract_analyses.sqlite3"
MAX_PDF_BYTES = 20 * 1024 * 1024

AGENTS = {
    "extraction": ("InsurAgent — Extraction documentaire", "Analyse le contrat d'assurance fourni et retourne uniquement un JSON valide avec contract_type, client, policy_number, effective_date, expiry_date, coverage (liste), exclusions (liste), conditions (liste), premium, deductible, currency, confidence. N'invente aucune donnée; utilise null ou une liste vide si absent. Réponds en français."),
    "anomalies": ("InsurAgent — Détection d'anomalies", "Tu es spécialiste du contrôle de contrats d'assurance. Examine les données extraites et retourne uniquement un JSON valide: anomalies (liste d'objets {title, description, severity [Low|Medium|High], evidence, recommendation}). Recherche clauses manquantes, incohérences, doublons et valeurs suspectes. Distingue fait et incertitude. Réponds en français."),
    "risk": ("InsurAgent — Analyse des risques", "Évalue le contrat et les anomalies fournis. Retourne uniquement un JSON valide: overall_priority [Low|Medium|High], risks (liste d'objets {title, description, priority [Low|Medium|High], clause, recommendation}), recommendations (liste de chaînes). Signale l'ambiguïté et les enjeux de conformité sans prétendre donner un avis juridique définitif. Réponds en français."),
    "report": ("InsurAgent — Rapport de synthèse", "Consolide les résultats d'analyse d'un contrat. Retourne uniquement un JSON valide: executive_summary (chaîne), key_findings (liste), conclusion (chaîne). N'ajoute pas de faits absents des données fournies. Réponds en français."),
    "compare": ("InsurAgent — Comparaison de contrats", "Compare les deux versions PDF jointes du même contrat. Retourne uniquement du JSON: summary (texte), changes (liste d'objets {clause, change [added|removed|modified|unchanged], before, after, impact, priority [Low|Medium|High]}), important_changes (liste). Compare les clauses, garanties, exclusions, franchises, dates et primes. Si les documents ne sont pas comparables, précise-le."),
    "qa": ("InsurAgent — Questions sur contrat", "Réponds aux questions en te fondant uniquement sur le PDF joint. Retourne un JSON: answer, evidence (citation courte ou numéro de page si possible), confidence [Low|Medium|High], not_found (bool). Si l'information est absente, dis-le explicitement. Réponds en français."),
    "priority": ("InsurAgent — Priorisation du portefeuille", "Classe les contrats transmis selon le niveau de risque et l'urgence de revue. Retourne du JSON: rankings (liste d'objets {id, priority [High|Medium|Low], score (0-100), rationale, next_action}), sorted_ids (ids du plus urgent au moins urgent). N'invente pas d'information."),
    "clarification": ("InsurAgent — Brouillon de clarification", "Prépare un brouillon de demande de clarification adressé à l'assureur ou au rédacteur du contrat à partir des ambiguïtés et anomalies. Retourne du JSON: subject, recipient_role, body, questions (liste). Reste professionnel et neutre; ne l'envoie jamais."),
    "compliance": ("InsurAgent — Checklist de conformité", "Crée une checklist de revue à partir du type de contrat et du texte fourni. Retourne du JSON: contract_type, jurisdiction_detected, jurisdiction_basis, checklist (liste d'objets {item, status [Present|Missing|Unclear|Not applicable], evidence, action}), limitations. N'affirme pas la conformité juridique; indique les inconnues et demande une validation humaine. Réponds en français."),
}


def _init_db():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as con:
        con.execute("CREATE TABLE IF NOT EXISTS analyses (id TEXT PRIMARY KEY, owner TEXT NOT NULL, filename TEXT NOT NULL, created_at TEXT NOT NULL, result TEXT NOT NULL, pdf BLOB NOT NULL)")
        columns = {row[1] for row in con.execute("PRAGMA table_info(analyses)")}
        if "source_pdf" not in columns:
            con.execute("ALTER TABLE analyses ADD COLUMN source_pdf BLOB")


def _agents_env():
    return {key: os.getenv(f"COMINTY_AGENT_{key.upper()}_ID", "").strip() for key in AGENTS}


async def _resolve_agents(client):
    configured = _agents_env()
    missing = [k for k, value in configured.items() if not value]
    if missing:
        existing = await client.agents.list()
        by_name = {agent.name: agent.id for agent in existing}
        for key in missing:
            name, instructions = AGENTS[key]
            agent_id = by_name.get(name)
            if not agent_id:
                agent = await client.agents.create(name=name, instructions=instructions, scope="private")
                agent_id = agent.id
            configured[key] = agent_id
    return configured


def _parse_json(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned, flags=re.I)
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        start, end = cleaned.find("{"), cleaned.rfind("}")
        if start < 0 or end < start:
            raise ValueError("L'agent n'a pas renvoyé un objet JSON valide")
        parsed = json.loads(cleaned[start:end + 1])
    if not isinstance(parsed, dict):
        raise ValueError("La réponse de l'agent doit être un objet JSON")
    return parsed


def _extract_pdf(content: bytes) -> str:
    from io import BytesIO
    reader = PdfReader(BytesIO(content))
    text = "\n".join((page.extract_text() or "") for page in reader.pages).strip()
    if len(text) < 80:
        try:
            import fitz
            import pytesseract
            from PIL import Image
            import io
            doc = fitz.open(stream=content, filetype="pdf")
            pages = [pytesseract.image_to_string(Image.open(io.BytesIO(page.get_pixmap(matrix=fitz.Matrix(2, 2)).tobytes("png"))), lang="fra+eng") for page in doc]
            text = "\n".join(pages).strip() or text
        except Exception:
            pass
    if not text:
        raise ValueError("Aucun texte détecté dans le PDF; vérifiez que l'OCR Tesseract est installé")
    return text[:100_000]


def _make_report(result: dict[str, Any]) -> bytes:
    from io import BytesIO
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    out = BytesIO()
    doc = SimpleDocTemplate(out, pagesize=A4, rightMargin=18*mm, leftMargin=18*mm, topMargin=16*mm, bottomMargin=16*mm)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Navy", parent=styles["Heading1"], textColor=colors.HexColor("#142b4a")))
    story = [Paragraph("Rapport d'analyse de contrat", styles["Navy"]), Paragraph(f"Document : {result['filename']} · {result['created_at']}", styles["Normal"]), Spacer(1, 8*mm)]
    def add_section(title, value):
        story.append(Paragraph(title, styles["Heading2"]))
        if isinstance(value, list):
            rows = [[Paragraph(str(item).replace("&", "&amp;"), styles["BodyText"])] for item in value] or [[Paragraph("Aucun élément signalé", styles["BodyText"])]]
            tbl = Table(rows, colWidths=[170*mm]); tbl.setStyle(TableStyle([("BACKGROUND", (0,0),(-1,-1), colors.HexColor("#f3f6fa")),("BOX",(0,0),(-1,-1),.3,colors.HexColor("#dce3eb")),("LEFTPADDING",(0,0),(-1,-1),8),("RIGHTPADDING",(0,0),(-1,-1),8),("TOPPADDING",(0,0),(-1,-1),6),("BOTTOMPADDING",(0,0),(-1,-1),6)])); story.extend([tbl, Spacer(1, 3*mm)])
        elif isinstance(value, dict):
            story.append(Paragraph(json.dumps(value, ensure_ascii=False, indent=2).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br/>"), styles["BodyText"]))
        else:
            story.append(Paragraph(str(value or "—").replace("&", "&amp;"), styles["BodyText"]))
        story.append(Spacer(1, 3*mm))
    add_section("Synthèse", result.get("report", {}).get("executive_summary", ""))
    add_section("Informations extraites", result.get("extraction", {}))
    add_section("Anomalies", result.get("anomalies", {}).get("anomalies", []))
    add_section("Risques", result.get("risk", {}).get("risks", []))
    add_section("Recommandations", result.get("risk", {}).get("recommendations", []))
    add_section("Conclusion", result.get("report", {}).get("conclusion", ""))
    doc.build(story)
    return out.getvalue()


def _owner(authorization: str | None, token: str | None):
    from api.main_api import _extract_gestionnaire
    user = _extract_gestionnaire(authorization, token)
    return str(user.get("id") or user.get("username") or "unknown")


@router.post("")
async def analyze_contract(file: UploadFile = File(...), authorization: str | None = Header(None), token: str | None = Query(None)):
    owner = _owner(authorization, token)
    if not file.filename or not file.filename.lower().endswith(".pdf") or file.content_type not in ("application/pdf", "application/octet-stream"):
        raise HTTPException(400, "Veuillez téléverser un fichier PDF")
    content = await file.read(MAX_PDF_BYTES + 1)
    if len(content) > MAX_PDF_BYTES:
        raise HTTPException(413, "Le PDF dépasse la limite de 20 Mo")
    if not content.startswith(b"%PDF-"):
        raise HTTPException(400, "Le fichier fourni n'est pas un PDF valide")
    try:
        document_text = _extract_pdf(content)
    except Exception as exc:
        raise HTTPException(422, f"Extraction PDF impossible : {exc}") from exc
    if not os.getenv("COMINTY_API_KEY") or not os.getenv("COMINTY_USER_ID"):
        raise HTTPException(503, "Configurez COMINTY_API_KEY et COMINTY_USER_ID côté backend pour lancer les agents.")
    try:
        from cominty_sdk import AsyncCominty
        async with AsyncCominty() as client:
            agents = await _resolve_agents(client)
            uploaded = await client.chat.upload_file(content, filename=Path(file.filename).name, mimetype="application/pdf")
            activities = []
            async def run_agent(key, task, prompt):
                activities.append({"agent": AGENTS[key][0], "status": "running", "task": task})
                run = await client.chat.start(agent_id=agents[key], message=prompt[:30_000], file_ids=[uploaded.id] if key == "extraction" else None, name=f"InsurAgent {key} — {Path(file.filename).name}")
                result = _parse_json(await run.text())
                activities[-1]["status"] = "completed"
                activities[-1]["result"] = "Résultat structuré reçu"
                return result
            extraction = await run_agent("extraction", "Extraction des clauses et données du contrat", f"Extrais les champs demandés du PDF joint. Texte OCR/extrait pour contexte :\n{document_text}")
            anomalies = await run_agent("anomalies", "Détection des omissions et incohérences", f"Données extraites :\n{json.dumps(extraction, ensure_ascii=False)}\n\nTexte du contrat :\n{document_text}")
            risk = await run_agent("risk", "Évaluation des risques et recommandations", f"Extraction :\n{json.dumps(extraction, ensure_ascii=False)}\nAnomalies :\n{json.dumps(anomalies, ensure_ascii=False)}\nTexte :\n{document_text}")
            report = await run_agent("report", "Synthèse finale de l'analyse", f"Extraction :\n{json.dumps(extraction, ensure_ascii=False)}\nAnomalies :\n{json.dumps(anomalies, ensure_ascii=False)}\nRisques :\n{json.dumps(risk, ensure_ascii=False)}")
        result = {"id": str(uuid.uuid4()), "filename": Path(file.filename).name, "created_at": datetime.now(timezone.utc).isoformat(), "extraction": extraction, "anomalies": anomalies, "risk": risk, "report": report, "activities": activities}
        pdf = _make_report(result)
        _init_db()
        with sqlite3.connect(DB_PATH) as con:
            con.execute("INSERT INTO analyses (id, owner, filename, created_at, result, pdf, source_pdf) VALUES (?, ?, ?, ?, ?, ?, ?)", (result["id"], owner, result["filename"], result["created_at"], json.dumps(result, ensure_ascii=False), pdf, content))
        return result
    except HTTPException:
        raise
    except Exception as exc:
        # Avoid logging secrets or exposing SDK internals to the caller.
        raise HTTPException(502, f"Échec de l'exécution Cominty : {type(exc).__name__}: {exc}") from exc


@router.get("")
def list_analyses(authorization: str | None = Header(None), token: str | None = Query(None)):
    owner = _owner(authorization, token); _init_db()
    with sqlite3.connect(DB_PATH) as con:
        rows = con.execute("SELECT result FROM analyses WHERE owner=? ORDER BY created_at DESC", (owner,)).fetchall()
    return [json.loads(row[0]) for row in rows]


@router.get("/{analysis_id}/report.pdf")
def download_report(analysis_id: str, authorization: str | None = Header(None), token: str | None = Query(None)):
    owner = _owner(authorization, token); _init_db()
    with sqlite3.connect(DB_PATH) as con:
        row = con.execute("SELECT filename, pdf FROM analyses WHERE id=? AND owner=?", (analysis_id, owner)).fetchone()
    if not row:
        raise HTTPException(404, "Rapport introuvable")
    return Response(row[1], media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="Analyse_{Path(row[0]).stem}.pdf"'})


class QuestionRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2000)


class PrioritizeRequest(BaseModel):
    analysis_ids: list[str] = Field(default_factory=list, max_length=100)


def _check_cominty_config():
    if not os.getenv("COMINTY_API_KEY") or not os.getenv("COMINTY_USER_ID"):
        raise HTTPException(503, "Configurez COMINTY_API_KEY et COMINTY_USER_ID côté backend.")


async def _task(client, agents, key: str, prompt: str, file_ids: list[str] | None = None):
    run = await client.chat.start(
        agent_id=agents[key],
        message=prompt[:30_000],
        file_ids=file_ids,
        name=f"InsurAgent {key} — {uuid.uuid4().hex[:8]}",
    )
    response_text = (await run.text()).strip()
    try:
        return _parse_json(response_text)
    except (ValueError, json.JSONDecodeError):
        # Some managed agents return useful prose despite explicit JSON instructions.
        # Preserve that real output in the feature's primary text field instead of
        # turning a usable answer into a 502; never synthesize missing findings.
        if not response_text:
            raise ValueError("L'agent a renvoyé une réponse vide")
        fallbacks = {
            "qa": {"answer": response_text, "evidence": "", "confidence": "Non précisée", "not_found": False, "format_warning": "Réponse fournie en texte libre par l'agent."},
            "clarification": {"subject": "Demande de clarification", "recipient_role": "Rédacteur du contrat", "body": response_text, "questions": [], "format_warning": "Brouillon fourni en texte libre par l'agent."},
            "compare": {"summary": response_text, "changes": [], "important_changes": [], "format_warning": "Comparaison fournie en texte libre; aucun changement structuré n'a pu être extrait."},
            "priority": {"rankings": [], "sorted_ids": [], "summary": response_text, "format_warning": "Classement fourni en texte libre; aucun ordre structuré n'a pu être extrait."},
            "compliance": {"contract_type": "", "jurisdiction_detected": "Non précisée", "jurisdiction_basis": "", "checklist": [], "limitations": response_text, "format_warning": "Checklist fournie en texte libre; aucun élément structuré n'a pu être extrait."},
        }
        if key not in fallbacks:
            raise
        return fallbacks[key]


def _get_owned_analysis(owner: str, analysis_id: str, with_pdf: bool = False):
    _init_db()
    with sqlite3.connect(DB_PATH) as con:
        if with_pdf:
            row = con.execute("SELECT filename, result, source_pdf FROM analyses WHERE id=? AND owner=?", (analysis_id, owner)).fetchone()
        else:
            row = con.execute("SELECT filename, result FROM analyses WHERE id=? AND owner=?", (analysis_id, owner)).fetchone()
    if not row:
        raise HTTPException(404, "Analyse introuvable")
    return row


async def _read_pdf_upload(upload: UploadFile):
    if not upload.filename or not upload.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Veuillez fournir un fichier PDF.")
    content = await upload.read(MAX_PDF_BYTES + 1)
    if len(content) > MAX_PDF_BYTES:
        raise HTTPException(413, "Le PDF dépasse la limite de 20 Mo.")
    if not content.startswith(b"%PDF-"):
        raise HTTPException(400, "Le fichier fourni n'est pas un PDF valide.")
    try:
        text = _extract_pdf(content)
    except Exception as exc:
        raise HTTPException(422, f"Extraction PDF impossible : {exc}") from exc
    return content, text


@router.post("/compare")
async def compare_contract_versions(
    version_a: UploadFile = File(...),
    version_b: UploadFile = File(...),
    authorization: str | None = Header(None),
    token: str | None = Query(None),
):
    _owner(authorization, token)
    content_a, text_a = await _read_pdf_upload(version_a)
    content_b, text_b = await _read_pdf_upload(version_b)
    _check_cominty_config()
    try:
        from cominty_sdk import AsyncCominty
        async with AsyncCominty() as client:
            agents = await _resolve_agents(client)
            file_a = await client.chat.upload_file(content_a, filename=Path(version_a.filename).name, mimetype="application/pdf")
            file_b = await client.chat.upload_file(content_b, filename=Path(version_b.filename).name, mimetype="application/pdf")
            comparison = await _task(
                client, agents, "compare",
                f"Compare la version A ({version_a.filename}) et la version B ({version_b.filename}).\nTexte A:\n{text_a}\n\nTexte B:\n{text_b}",
                [file_a.id, file_b.id],
            )
        return {"version_a": Path(version_a.filename).name, "version_b": Path(version_b.filename).name, **comparison}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(502, f"Échec de la comparaison Cominty : {type(exc).__name__}: {exc}") from exc


@router.post("/{analysis_id}/ask")
async def ask_about_contract(
    analysis_id: str,
    request: QuestionRequest,
    authorization: str | None = Header(None),
    token: str | None = Query(None),
):
    owner = _owner(authorization, token)
    filename, raw_result, source_pdf = _get_owned_analysis(owner, analysis_id, with_pdf=True)
    if not source_pdf:
        raise HTTPException(409, "Le PDF original n'est pas disponible pour cette ancienne analyse. Réanalysez le document pour activer les questions.")
    _check_cominty_config()
    try:
        from cominty_sdk import AsyncCominty
        async with AsyncCominty() as client:
            agents = await _resolve_agents(client)
            uploaded = await client.chat.upload_file(source_pdf, filename=filename, mimetype="application/pdf")
            answer = await _task(client, agents, "qa", f"Question de l'utilisateur : {request.question}\nDonnées déjà extraites : {raw_result}", [uploaded.id])
        return answer
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(502, f"Échec de la réponse Cominty : {type(exc).__name__}: {exc}") from exc


@router.post("/prioritize")
async def prioritize_portfolio(
    request: PrioritizeRequest,
    authorization: str | None = Header(None),
    token: str | None = Query(None),
):
    owner = _owner(authorization, token)
    _init_db()
    with sqlite3.connect(DB_PATH) as con:
        rows = con.execute("SELECT id, filename, created_at, result FROM analyses WHERE owner=? ORDER BY created_at DESC", (owner,)).fetchall()
    chosen = set(request.analysis_ids)
    if chosen:
        rows = [row for row in rows if row[0] in chosen]
    if not rows:
        raise HTTPException(404, "Aucune analyse disponible à classer.")
    portfolio = []
    for analysis_id, filename, created_at, raw in rows:
        result = json.loads(raw)
        portfolio.append({"id": analysis_id, "filename": filename, "created_at": created_at, "risk": result.get("risk", {}), "anomalies": result.get("anomalies", {})})
    _check_cominty_config()
    try:
        from cominty_sdk import AsyncCominty
        async with AsyncCominty() as client:
            agents = await _resolve_agents(client)
            ranking = await _task(client, agents, "priority", "Classe ces analyses pour la prochaine revue humaine, du plus urgent au moins urgent :\n" + json.dumps(portfolio, ensure_ascii=False))
        return ranking
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(502, f"Échec du classement Cominty : {type(exc).__name__}: {exc}") from exc


async def _analysis_action(analysis_id: str, key: str, action_label: str, authorization: str | None, token: str | None):
    owner = _owner(authorization, token)
    filename, raw_result, source_pdf = _get_owned_analysis(owner, analysis_id, with_pdf=True)
    _check_cominty_config()
    try:
        from cominty_sdk import AsyncCominty
        async with AsyncCominty() as client:
            agents = await _resolve_agents(client)
            file_ids = None
            if key == "compliance" and source_pdf:
                uploaded = await client.chat.upload_file(source_pdf, filename=filename, mimetype="application/pdf")
                file_ids = [uploaded.id]
            return await _task(client, agents, key, f"{action_label} pour le contrat {filename}.\nRésultats d'analyse :\n{raw_result}\nBase-toi sur le PDF original joint s'il est disponible.", file_ids)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(502, f"Échec de l'agent Cominty : {type(exc).__name__}: {exc}") from exc


@router.post("/{analysis_id}/clarification")
async def draft_clarification(analysis_id: str, authorization: str | None = Header(None), token: str | None = Query(None)):
    return await _analysis_action(analysis_id, "clarification", "Rédige un brouillon de demande de clarification à partir des clauses ambiguës ou anomalies", authorization, token)


@router.post("/{analysis_id}/compliance")
async def compliance_checklist(analysis_id: str, authorization: str | None = Header(None), token: str | None = Query(None)):
    return await _analysis_action(analysis_id, "compliance", "Prépare une checklist de conformité de revue humaine. Déduis la juridiction seulement si le document l'établit, sinon indique inconnue", authorization, token)
