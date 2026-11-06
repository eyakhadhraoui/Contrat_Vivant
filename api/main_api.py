import io
import logging
import os
from fastapi import FastAPI, HTTPException, Header, Query, UploadFile, File, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from config import settings
from tools.audit_log_tool import log_decision, get_audit_logs, export_audit_log_csv
from tools.revert_tool import save_revert, get_revert
from tools.si_contrats_tool import get_contrat, get_contrats_par_agence, ajouter_contrat, modifier_contrat, _normalize_contrat_id
from tools.si_sinistres_tool import get_sinistres, ajouter_sinistre, modifier_sinistre, get_sinistres_par_agence
from tools.si_delete_tool import supprimer_contrat, supprimer_sinistre
from tools.auth_tool import login, create_gestionnaire, verify_token, authenticate_or_create_google_user
from tools.auth_context import resolve_gestionnaire
from tools.si_agences_clients_tool import get_agences, get_clients, ajouter_client, get_historique_db, get_alerts_for_gestionnaire, update_alert_validation_status
from tools.pdf_generator_tool import generate_contrat_pdf, generate_sinistre_pdf, generate_audit_report_pdf, generate_avenant_pdf
from agent_tools.rag_tool import ingest_document, get_all_documents, delete_document, search_procedures
from tools.chat_history_tool import save_chat_message, get_chat_history, clear_chat_history
from graph.workflow import graph
from nodes.chat_node import chat_with_gestionnaire
from rules_engine.risk_analyzer import analyze_risk


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


# mount events router (implemented in api/events.py)
try:
    from api.events import router as events_router
except Exception:
    events_router = None

app = FastAPI(title='Contrat Vivant API')

# Instrumentation Prometheus pour l'exposition des métriques sur /metrics
try:
    from prometheus_fastapi_instrumentator import Instrumentator
    Instrumentator().instrument(app).expose(app)
except Exception:
    try:
        from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
        @app.get("/metrics")
        def metrics():
            return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
    except Exception as e:
        logger.warning("Impossible d'exposer les métriques Prometheus: %s", e)

# NOTE: auth here is Bearer-token based (header/query param), not cookie-based,
# so allow_credentials=True is not needed. Browsers reject the combination of
# allow_origins=['*'] + allow_credentials=True anyway (invalid per the CORS
# spec) so this was silently failing preflight in strict browsers.
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=False,
    allow_methods=['*'],
    allow_headers=['*'],
)

# Serve static files or React frontend dist if exists
if os.path.exists("frontend/dist"):
    app.mount("/assets", StaticFiles(directory="frontend/dist/assets"), name="assets")
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# include events router if available
if events_router:
    app.include_router(events_router, prefix="/api")

from api.cominty_analysis import router as cominty_analysis_router
app.include_router(cominty_analysis_router, prefix="/api")

@app.get("/")
def read_root():
    if os.path.exists("frontend/dist/index.html"):
        return FileResponse("frontend/dist/index.html")
    return RedirectResponse(url="/login")


@app.get("/login")
def login_page():
    if os.path.exists("frontend/dist/index.html"):
        return FileResponse("frontend/dist/index.html")
    if os.path.exists("static/login.html"):
        return FileResponse("static/login.html")
    raise HTTPException(status_code=404, detail="Page de connexion introuvable")


@app.get("/app")
def app_page():
    if os.path.exists("frontend/dist/index.html"):
        return FileResponse("frontend/dist/index.html")
    if os.path.exists("static/index.html"):
        return FileResponse("static/index.html")
    raise HTTPException(status_code=404, detail="Application introuvable")



class LoginRequest(BaseModel):
    username: str
    password: str


class GoogleAuthRequest(BaseModel):
    email: str
    nom: Optional[str] = ''
    prenom: Optional[str] = ''
    google_id: Optional[str] = None
    picture: Optional[str] = None
    credential: Optional[str] = None


class SignupRequest(BaseModel):
    username: str
    password: str
    email: str
    nom: str
    prenom: str
    role: Optional[str] = 'assurances'
    agence_id: Optional[str] = None


class NoteCreateRequest(BaseModel):
    note_texte: str


class AnalyseRequest(BaseModel):
    token: Optional[str] = None
    contrat_id: str
    modification_type: str = 'contrat'


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = 'default'
    token: Optional[str] = None


class CourrierRequest(BaseModel):
    type_courrier: str
    client_nom: str = Field(default='Madame, Monsieur', max_length=160)
    client_email: Optional[str] = Field(default=None, max_length=254)
    reference: Optional[str] = Field(default=None, max_length=100)
    contexte: Optional[str] = Field(default=None, max_length=3000)
    ton: str = Field(default='professionnel et cordial', max_length=80)


class ContratCreateRequest(BaseModel):
    id: str
    numero_souscripteur: Optional[str] = None
    client_id: Optional[str] = None
    client: Optional[str] = None
    type_contrat: Optional[str] = 'auto'
    garantie_max: float
    prime_mensuelle: Optional[float] = None
    prime_annuelle: Optional[float] = None
    franchise: Optional[float] = None
    duree_mois: Optional[int] = None
    date_debut: Optional[str] = None
    date_fin: Optional[str] = None
    statut: str = 'actif'
    mode_paiement: Optional[str] = None
    frequence_paiement: Optional[str] = None
    couverture: Optional[str] = None
    exclusions: Optional[str] = None
    observations: Optional[str] = None
    agence_id: Optional[str] = None

    class Config:
        extra = 'allow'


class SinistreCreateRequest(BaseModel):
    id: str
    contrat_id: str
    montant_declare: float
    type_sinistre: Optional[str] = 'Auto - Carambolage'
    lieu_sinistre: Optional[str] = None
    date_sinistre: Optional[str] = None
    date_declaration: Optional[str] = None
    responsabilite: Optional[str] = 'indetermine'
    description: Optional[str] = None
    observations: Optional[str] = None
    client_nom: Optional[str] = None
    statut: str = 'en_cours'
    agence_id: Optional[str] = None
    token: Optional[str] = None

    class Config:
        extra = 'allow'


class ValidateRequest(BaseModel):
    state: Dict[str, Any]
    action: str = Field(..., description="validate|adjust|reject|apply")
    apply_changes: bool = False
    comment: Optional[str] = None


class RollbackRequest(BaseModel):
    revert_id: str



def _extract_gestionnaire(authorization: Optional[str] = Header(None), token: Optional[str] = Query(None)):
    raw_token = token
    if not raw_token and authorization:
        if authorization.startswith("Bearer "):
            raw_token = authorization.split(" ")[1]
        else:
            raw_token = authorization
    try:
        return resolve_gestionnaire(raw_token)
    except PermissionError as exc:
        raise HTTPException(status_code=401, detail=str(exc))



@app.post('/api/login')
def api_login(req: LoginRequest):
    try:
        token = login(req.username, req.password)
        payload = verify_token(token)
        return {'status': 'success', 'token': token, 'gestionnaire': payload}
    except PermissionError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error("Erreur serveur lors du login: %s", e)
        raise HTTPException(status_code=401, detail="Identifiant ou mot de passe incorrect")


@app.post('/api/auth/google')
def api_google_auth(req: GoogleAuthRequest):
    """
    Authentification & Inscription automatique via Google OAuth SSO.
    Si le compte existe déjà : connexion directe sans duplication.
    Si le compte n'existe pas : création automatique et connexion immédiate.
    """
    try:
        res = authenticate_or_create_google_user(
            email=req.email,
            nom=req.nom or '',
            prenom=req.prenom or '',
            google_id=req.google_id,
            picture=req.picture
        )
        action_type = "google_sso_signup" if res.get('is_new_user') else "google_sso_login"
        log_decision(action_type, {
            "email": req.email,
            "username": res.get('gestionnaire', {}).get('username'),
            "is_new_user": res.get('is_new_user')
        }, res.get('gestionnaire', {}).get('id'))
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Erreur Google SSO Auth: %s", e)
        raise HTTPException(status_code=500, detail="Échec de l'authentification Google")



@app.get("/signup")
def signup_page():
    if os.path.exists("static/signup.html"):
        return FileResponse("static/signup.html")
    raise HTTPException(status_code=404, detail="Page d'inscription introuvable")


@app.get('/api/agences')
def api_liste_agences():
    """Retourne la liste des agences depuis la base de données MySQL."""
    try:
        agences = get_agences()
        return {"agences": agences}
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


class ClientCreateRequest(BaseModel):
    id: Optional[str] = None
    nom: str
    prenom: str
    cin: Optional[str] = None
    email: Optional[str] = None
    telephone: Optional[str] = None
    adresse: Optional[str] = None


@app.get('/api/clients')
def api_liste_clients(authorization: Optional[str] = Header(None), token: Optional[str] = Query(None)):
    """Retourne la liste des clients depuis la base de données MySQL."""
    _extract_gestionnaire(authorization, token)
    try:
        clients = get_clients()
        return {"clients": clients}
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.post('/api/clients')
def api_ajouter_client(req: ClientCreateRequest, authorization: Optional[str] = Header(None), token: Optional[str] = Query(None)):
    """Gestionnaire d'assurances ou de sinistres (authentifié) peut ajouter un client commun."""
    gestionnaire = _extract_gestionnaire(authorization, token)
    if gestionnaire.get('role') not in ('assurances', 'sinistres'):
        raise HTTPException(status_code=403, detail="Accès réservé aux gestionnaires authentifiés.")
    try:
        res = ajouter_client(req.dict(), gestionnaire)
        return {"status": "success", "client": res}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post('/api/cin/extract')
async def api_extract_cin(file: UploadFile = File(...), authorization: Optional[str] = Header(None), token: Optional[str] = Query(None)):
    """Extrait les données d'une image/photo de Carte d'Identité Nationale (CIN)."""
    _extract_gestionnaire(authorization, token)
    try:
        content_bytes = await file.read()
        from tools.cin_ocr_tool import extract_cin_info
        res = extract_cin_info(content_bytes)
        return {"status": "success", "cin_data": res}
    except ValueError as e:
        # Image lue avec succès mais non reconnue comme une CIN (photo non pertinente)
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erreur d'extraction OCR de la CIN: {e}")



@app.get('/api/pdf/contrat/{contrat_id}')
def api_pdf_contrat(contrat_id: str, authorization: Optional[str] = Header(None), token: Optional[str] = Query(None)):
    try:
        gestionnaire = _extract_gestionnaire(authorization, token)
    except Exception:
        gestionnaire = {"username": "Gestionnaire", "gestionnaire_id": "G123", "agence_id": "AG01"}

    contrat = None
    try:
        contrat = get_contrat(contrat_id)
    except Exception:
        pass

    if not contrat:
        try:
            contrats = get_contrats_par_agence(gestionnaire.get("agence_id"))
            contrat = next((c for c in contrats if str(c.get("id")).upper() == str(contrat_id).upper()), None)
        except Exception:
            pass

    if not contrat:
        contrat = {
            "id": contrat_id,
            "client": "Client Assuré",
            "type_contrat": "auto",
            "garantie_max": 100000.0,
            "statut": "actif",
            "date_debut": "2026-01-01",
            "date_fin": "2027-01-01",
            "gestionnaire_createur_id": gestionnaire.get("gestionnaire_id", "G123"),
            "agence_id": gestionnaire.get("agence_id", "AG01")
        }

    pdf_bytes = generate_contrat_pdf(contrat)
    try:
        log_decision("export_pdf_contrat", {
            "action": f"Export PDF du contrat {contrat_id} par {gestionnaire.get('username')}",
            "actor": gestionnaire.get("username"),
            "contrat_id": contrat_id,
            "status": "OK"
        }, gestionnaire.get("gestionnaire_id"))
    except Exception:
        pass

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=Attestation_Contrat_{contrat_id}.pdf"}
    )


@app.get('/api/pdf/sinistre/{sinistre_id}')
def api_pdf_sinistre(sinistre_id: str, authorization: Optional[str] = Header(None), token: Optional[str] = Query(None)):
    try:
        gestionnaire = _extract_gestionnaire(authorization, token)
    except Exception:
        gestionnaire = {"username": "Gestionnaire", "gestionnaire_id": "G123", "agence_id": "AG01"}

    sinistre = None
    try:
        sinistres = get_sinistres_par_agence(gestionnaire.get("agence_id"))
        sinistre = next((s for s in sinistres if str(s.get("id")).upper() == str(sinistre_id).upper()), None)
    except Exception:
        pass

    if not sinistre:
        sinistre = {
            "id": sinistre_id,
            "contrat_id": "C001",
            "client": "Client Assuré",
            "type_sinistre": "Auto - Carambolage",
            "montant_declare": 5000.0,
            "statut": "en_cours",
            "date": "2026-08-08",
            "gestionnaire_traitant_id": gestionnaire.get("gestionnaire_id", "G123"),
            "agence_id": gestionnaire.get("agence_id", "AG01")
        }

    pdf_bytes = generate_sinistre_pdf(sinistre)
    try:
        log_decision("export_pdf_sinistre", {
            "action": f"Export PDF du sinistre {sinistre_id} par {gestionnaire.get('username')}",
            "actor": gestionnaire.get("username"),
            "sinistre_id": sinistre_id,
            "status": "OK"
        }, gestionnaire.get("gestionnaire_id"))
    except Exception:
        pass

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=Rapport_Sinistre_{sinistre_id}.pdf"}
    )


@app.get('/api/pdf/audit')
def api_pdf_audit(authorization: Optional[str] = Header(None), token: Optional[str] = Query(None)):
    """Génère et télécharge le rapport PDF de synthèse du journal d'audit."""
    try:
        gestionnaire = _extract_gestionnaire(authorization, token)
    except Exception:
        gestionnaire = {"username": "Gestionnaire", "gestionnaire_id": "G123", "agence_id": None}

    try:
        logs = get_audit_logs(gestionnaire.get("agence_id"))
        pdf_bytes = generate_audit_report_pdf(logs, agence_id=gestionnaire.get("agence_id"))
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=Rapport_Synthese_Audit.pdf"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la génération du rapport PDF d'audit: {e}")


@app.get('/api/audit/csv')
def api_csv_audit(authorization: Optional[str] = Header(None), token: Optional[str] = Query(None)):
    """Génère et télécharge l'export CSV du journal d'audit."""
    try:
        gestionnaire = _extract_gestionnaire(authorization, token)
    except Exception:
        gestionnaire = {"username": "Gestionnaire", "gestionnaire_id": "G123", "agence_id": None}

    try:
        csv_content = export_audit_log_csv(gestionnaire.get("agence_id"))
        bom_csv = "\ufeff" + csv_content
        return Response(
            content=bom_csv.encode("utf-8"),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=Journal_Audit.csv"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'export CSV d'audit: {e}")


@app.get('/api/pdf/avenant/{contrat_id}')
def api_pdf_avenant(contrat_id: str, authorization: Optional[str] = Header(None), token: Optional[str] = Query(None)):
    """Génère un projet d'avenant à partir d'un contrat existant."""
    try:
        gestionnaire = _extract_gestionnaire(authorization, token)
    except Exception:
        gestionnaire = {"username": "Gestionnaire", "gestionnaire_id": "G123", "agence_id": None}

    contrat = get_contrat(contrat_id)
    if not contrat:
        raise HTTPException(status_code=404, detail="Contrat introuvable : aucun avenant ne peut \u00eatre g\u00e9n\u00e9r\u00e9 sans donn\u00e9es contractuelles r\u00e9elles.")

    val_info = {
        "gestionnaire_nom": gestionnaire.get("username"),
    }
    pdf_bytes = generate_avenant_pdf(contrat, val_info)
    try:
        log_decision("export_pdf_avenant", {
            "action": f"Génération de l'Avenant PDF {contrat_id} par {gestionnaire.get('username')}",
            "actor": gestionnaire.get("username"),
            "contrat_id": contrat_id,
            "status": "OK"
        }, gestionnaire.get("gestionnaire_id"))
    except Exception:
        pass

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=Avenant_{contrat_id}.pdf"}
    )








@app.get('/api/alerts')
def api_liste_alertes(authorization: Optional[str] = Header(None), token: Optional[str] = Query(None)):
    """Retourne les alertes in-app filtrées par agence / gestionnaire authentifié."""
    gestionnaire = _extract_gestionnaire(authorization, token)
    try:
        alertes = get_alerts_for_gestionnaire(gestionnaire.get("gestionnaire_id"), gestionnaire.get("agence_id"))
        return {"alerts": alertes}
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.post('/api/signup')
def api_signup(req: SignupRequest):
    role = (req.role or 'assurances').lower().strip()
    if role not in ('assurances', 'sinistres'):
        raise HTTPException(status_code=400, detail="Le rôle doit être 'assurances' ou 'sinistres'")
    try:
        res = create_gestionnaire(
            username=req.username,
            password=req.password,
            email=req.email,
            nom=req.nom,
            prenom=req.prenom,
            role=role,
            agence_id=req.agence_id,
        )
        token = login(req.username, req.password)
        return {'status': 'success', 'token': token, 'gestionnaire': res}
    except ValueError as e:
        msg = str(e)
        if 'déjà utilisé' in msg.lower():
            raise HTTPException(status_code=409, detail=msg)
        raise HTTPException(status_code=400, detail=msg)
    except PermissionError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/api/contrats')
def api_liste_contrats(authorization: Optional[str] = Header(None), token: Optional[str] = Query(None)):
    """
    Gestionnaire ASSURANCES ou SINISTRES (authentifié) :
    → Voit TOUS les contrats (de son agence)
    """
    gestionnaire = _extract_gestionnaire(authorization, token)
    if gestionnaire.get('role') not in ['assurances', 'sinistres']:
        raise HTTPException(status_code=403, detail="Accès non autorisé")

    agence_id = gestionnaire.get('agence_id')
    try:
        contrats = get_contrats_par_agence(agence_id)
        return {"contrats": contrats, "agence_id": agence_id}
    except (RuntimeError, ConnectionError) as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.get('/api/sinistres')
def api_liste_sinistres(authorization: Optional[str] = Header(None), token: Optional[str] = Query(None)):
    """
    Gestionnaire SINISTRES ou ASSURANCES (authentifié) :
    → Voit les sinistres (de son agence)
    """
    gestionnaire = _extract_gestionnaire(authorization, token)
    agence_id = gestionnaire.get('agence_id')
    try:
        sinistres = get_sinistres_par_agence(agence_id)
        return {"sinistres": sinistres, "agence_id": agence_id}
    except (RuntimeError, ConnectionError) as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.get('/api/risk/priorities')
def api_priorites_risque(authorization: Optional[str] = Header(None), token: Optional[str] = Query(None)):
    """Classe les contrats de l'agence selon le score de risque metier existant."""
    gestionnaire = _extract_gestionnaire(authorization, token)
    agence_id = gestionnaire.get('agence_id')
    try:
        contrats = get_contrats_par_agence(agence_id)
        sinistres = get_sinistres_par_agence(agence_id)
        sinistres_by_contract = {}
        for sinistre in sinistres:
            key = _normalize_contrat_id(sinistre.get('contrat_id'))
            if key:
                sinistres_by_contract.setdefault(key, []).append(sinistre)

        dossiers = []
        for contrat in contrats:
            contrat_id = contrat.get('id') or contrat.get('contrat_id')
            if not contrat_id:
                continue
            key = _normalize_contrat_id(contrat_id)
            related = sinistres_by_contract.get(key, [])
            analysis_contract = {
                **contrat,
                'date_souscription': contrat.get('date_souscription') or contrat.get('date_debut'),
            }
            risk = analyze_risk(analysis_contract, related)
            recommendation = risk.get('recommendation') or {}
            dossiers.append({
                'contrat_id': contrat_id,
                'client': contrat.get('client') or contrat.get('client_id') or 'Client non renseigne',
                'type_contrat': contrat.get('type_contrat') or contrat.get('type') or 'Non renseigne',
                'statut': contrat.get('statut') or 'inconnu',
                'sinistres_count': len(related),
                'score': risk.get('score', 0),
                'niveau': risk.get('urgency_level', 'faible'),
                'confidence': risk.get('confidence', 'faible'),
                'facteurs': risk.get('top_factors', []),
                'recommandation': recommendation.get('label') or 'Revue gestionnaire',
                'anomalies': risk.get('anomalies', []),
                'donnees_manquantes': risk.get('missing_data', []),
            })
        dossiers.sort(key=lambda item: item['score'], reverse=True)
        return {'dossiers': dossiers, 'total': len(dossiers), 'agence_id': agence_id}
    except (RuntimeError, ConnectionError) as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.exception('Erreur de classement de priorite risque')
        raise HTTPException(status_code=500, detail='Impossible de calculer les priorites de risque.') from e


@app.post('/api/contrats')
def api_ajouter_contrat(req: ContratCreateRequest, authorization: Optional[str] = Header(None), token: Optional[str] = Query(None)):
    gestionnaire = _extract_gestionnaire(authorization, token)
    if not gestionnaire or not gestionnaire.get('gestionnaire_id'):
        raise HTTPException(status_code=401, detail="Authentification requise")
    try:
        res = ajouter_contrat(req.dict(), gestionnaire)
        return {"status": "success", "contrat": res}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except (RuntimeError, ConnectionError) as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post('/api/contrats/{contrat_id}/notes')
def api_ajouter_note_gestionnaire(
    contrat_id: str,
    req: NoteCreateRequest,
    authorization: Optional[str] = Header(None),
    token: Optional[str] = Query(None)
):
    gestionnaire = _extract_gestionnaire(authorization, token)
    raw_note = req.note_texte.strip()
    if not raw_note:
        raise HTTPException(status_code=400, detail="La note ne peut pas être vide")

    g_name = f"{gestionnaire.get('prenom', '')} {gestionnaire.get('nom', '')}".strip() or gestionnaire.get('username') or "Gestionnaire"

    # Structuration intelligente par le LLM (Gemini / Ollama)
    from llm.gemini_client import ask_gemini
    prompt = (
        f"Tu es un assistant expert en assurance. Reformatte et structure en Markdown concis "
        f"la note vocale suivante dictée par le gestionnaire {g_name} pour le contrat {contrat_id} :\n"
        f"\"{raw_note}\"\n\n"
        f"Format souhaité :\n"
        f"• **Auteur** : {g_name}\n"
        f"• **Synthèse de la Dictée** : [Résumé clair et professionnel]\n"
        f"• **Actions Décidées** : [Liste des actions/décisions]\n"
    )
    fallback_note = f"• **Auteur** : {g_name}\n• **Note Dictée** : {raw_note}\n• **Statut** : Enregistré par le gestionnaire."
    structured_note = ask_gemini(prompt, fallback_default=fallback_note)

    # Sauvegarde dans la base MySQL (table contrats champ observations) & audit_log
    from database.db_connection import get_connection
    try:
        conn = get_connection()
        if conn:
            cur = conn.cursor()
            sql = "UPDATE contrats SET observations = CONCAT(COALESCE(observations, ''), '\n\n', %s), date_derniere_modif = CURRENT_DATE WHERE id = %s"
            cur.execute(sql, (structured_note, contrat_id))
            conn.commit()
            cur.close()
            conn.close()
    except Exception as e:
        logger.warning(f"Erreur mise à jour note contrat MySQL: {e}")

    log_decision("add_manager_voice_note", {
        "contrat_id": contrat_id,
        "gestionnaire": g_name,
        "raw_note": raw_note,
        "structured_note": structured_note
    }, gestionnaire_id=gestionnaire.get("gestionnaire_id"))

    return {
        "status": "success",
        "contrat_id": contrat_id,
        "note_brute": raw_note,
        "note_structuree": structured_note
    }


@app.put('/api/contrats/modifier')
@app.put('/api/contrats/{contrat_id}')
def api_modifier_contrat(
    updates: Dict[str, Any],
    contrat_id: Optional[str] = None,
    authorization: Optional[str] = Header(None),
    token: Optional[str] = Query(None)
):
    gestionnaire = _extract_gestionnaire(authorization, token)
    if not gestionnaire or not gestionnaire.get('gestionnaire_id'):
        raise HTTPException(status_code=401, detail="Authentification requise")
    target_id = contrat_id or updates.get("id") or updates.get("contrat_id")
    if target_id == "modifier" or not target_id:
        target_id = updates.get("id") or updates.get("contrat_id")
    if not target_id:
        raise HTTPException(status_code=400, detail="ID du contrat manquant")

    merged_updates = {**updates}
    if isinstance(updates.get("champs"), dict):
        merged_updates.update(updates["champs"])

    try:
        res = modifier_contrat(target_id, merged_updates, gestionnaire)
        return {"status": "success", **res}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except (RuntimeError, ConnectionError) as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post('/api/sinistres')
def api_ajouter_sinistre(req: SinistreCreateRequest, authorization: Optional[str] = Header(None), token: Optional[str] = Query(None)):
    gestionnaire = _extract_gestionnaire(authorization, token)
    if not gestionnaire or not gestionnaire.get('gestionnaire_id'):
        raise HTTPException(status_code=401, detail="Authentification requise")
    try:
        res = ajouter_sinistre(req.dict(), gestionnaire)
        return {"status": "success", **res}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except (RuntimeError, ConnectionError) as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put('/api/sinistres/modifier')
@app.put('/api/sinistres/{sinistre_id}')
def api_modifier_sinistre(
    updates: Dict[str, Any],
    sinistre_id: Optional[str] = None,
    authorization: Optional[str] = Header(None),
    token: Optional[str] = Query(None)
):
    gestionnaire = _extract_gestionnaire(authorization, token)
    if not gestionnaire or not gestionnaire.get('gestionnaire_id'):
        raise HTTPException(status_code=401, detail="Authentification requise")
    target_id = sinistre_id or updates.get("id") or updates.get("sinistre_id")
    if target_id == "modifier" or not target_id:
        target_id = updates.get("id") or updates.get("sinistre_id")
    if not target_id:
        raise HTTPException(status_code=400, detail="ID du sinistre manquant")

    merged_updates = {**updates}
    if isinstance(updates.get("champs"), dict):
        merged_updates.update(updates["champs"])

    try:
        res = modifier_sinistre(target_id, merged_updates, gestionnaire)
        return {"status": "success", **res}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except (RuntimeError, ConnectionError) as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete('/api/contrats/{contrat_id}')
def api_supprimer_contrat(
    contrat_id: str,
    authorization: Optional[str] = Header(None),
    token: Optional[str] = Query(None)
):
    gestionnaire = _extract_gestionnaire(authorization, token)
    if gestionnaire.get('role') != 'assurances':
        raise HTTPException(status_code=403, detail="Seul un gestionnaire Assurances peut supprimer un contrat.")
    try:
        return supprimer_contrat(contrat_id, gestionnaire)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete('/api/sinistres/{sinistre_id}')
def api_supprimer_sinistre(
    sinistre_id: str,
    authorization: Optional[str] = Header(None),
    token: Optional[str] = Query(None)
):
    gestionnaire = _extract_gestionnaire(authorization, token)
    if gestionnaire.get('role') != 'sinistres':
        raise HTTPException(status_code=403, detail="Seul un gestionnaire Sinistres peut supprimer un sinistre.")
    try:
        return supprimer_sinistre(sinistre_id, gestionnaire)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post('/api/analyser')
def api_analyser(
    req: AnalyseRequest,
    authorization: Optional[str] = Header(None),
    token: Optional[str] = Query(None)
):
    token_value = req.token if req.token else (token if isinstance(token, str) else None)
    if not token_value and isinstance(authorization, str):
        token_value = authorization[7:] if authorization.startswith('Bearer ') else authorization

    try:
        initial_state = {
            'token': token_value,
            'contrat_id': req.contrat_id,
            'modification_type': req.modification_type,
            'agent_metadata': {'orchestrator': 'SupervisorAgent'},
        }
        result = graph.invoke(initial_state)
        log_decision("analyse_dossier_ia", {
            "action": f"Analyse IA exécutée sur contrat {req.contrat_id}",
            "contrat_id": req.contrat_id,
            "status": "OK"
        })
        return result

    except PermissionError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except ValueError as e:
        if 'introuvable' in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =========================================================================
# ENDPOINTS RAG PERSISTANT & GESTION DES DOCUMENTS
# =========================================================================

@app.get('/api/rag/documents')
def api_rag_list_documents(authorization: Optional[str] = Header(None), token: Optional[str] = Query(None)):
    """Liste tous les documents persistants indexés dans la base RAG."""
    try:
        docs = get_all_documents()
        return {"documents": docs, "total": len(docs)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post('/api/rag/ingest')
async def api_rag_ingest(
    file: UploadFile = File(...),
    authorization: Optional[str] = Header(None),
    token: Optional[str] = Query(None)
):
    """
    Ingère un document (PDF, TXT, JSON, DOCX) dans MySQL et le Vector Store RAG.
    Le document reste enregistré et interrogeable de façon permanente même après déconnexion.
    """
    try:
        try:
            gest = _extract_gestionnaire(authorization, token)
            uploaded_by = gest.get('nom_complet') or gest.get('username') or gest.get('gestionnaire_id') or 'gestionnaire'
        except Exception:
            uploaded_by = 'gestionnaire'

        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Le fichier envoyé est vide.")

        result = ingest_document(file.filename, content, uploaded_by=uploaded_by)
        log_decision("rag_document_ingested", {
            "filename": file.filename,
            "size": len(content),
            "uploaded_by": uploaded_by,
            "chunks_added": result.get("chunks_added", 0)
        })
        return result
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Erreur ingestion RAG: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur d'ingestion RAG : {str(e)}")


@app.delete('/api/rag/documents/{doc_id}')
def api_rag_delete_document(
    doc_id: str,
    authorization: Optional[str] = Header(None),
    token: Optional[str] = Query(None)
):
    """Supprime un document du RAG et réindexe la base."""
    try:
        delete_document(doc_id)
        return {"status": "success", "message": f"Document {doc_id} supprimé du RAG avec succès."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post('/api/courriers/generer')
def api_generer_courrier(req: CourrierRequest, authorization: Optional[str] = Header(None), token: Optional[str] = Query(None)):
    """Prepare un brouillon de courrier, sans l'envoyer au client."""
    gestionnaire = _extract_gestionnaire(authorization, token)
    types = {
        'demande_pieces': 'demande de pieces justificatives',
        'accuse_reception': 'accuse de reception d une declaration',
        'reponse_client': 'reponse generale au client',
    }
    if req.type_courrier not in types:
        raise HTTPException(status_code=400, detail='Type de courrier non pris en charge.')

    reference = req.reference or 'non communiquee'
    contexte = req.contexte or 'Aucun detail supplementaire fourni.'
    if req.type_courrier == 'demande_pieces':
        fallback = (
            f"Objet : Pieces a fournir - dossier {reference}\n\n"
            f"Bonjour {req.client_nom},\n\n"
            f"Afin de poursuivre l'etude de votre dossier {reference}, merci de nous transmettre les pieces suivantes :\n"
            f"{req.contexte or '[A preciser par le gestionnaire]'}\n\n"
            "Nous restons a votre disposition pour toute question.\nCordialement,\nVotre gestionnaire"
        )
    elif req.type_courrier == 'accuse_reception':
        fallback = (
            f"Objet : Accuse de reception - dossier {reference}\n\n"
            f"Bonjour {req.client_nom},\n\nNous accusons reception de votre declaration concernant le dossier {reference}. "
            "Votre dossier va etre examine par notre equipe. Nous vous informerons de son suivi et vous contacterons si des informations complementaires sont necessaires.\n\n"
            "Cordialement,\nVotre gestionnaire"
        )
    else:
        fallback = (
            f"Objet : Suivi de votre dossier {reference}\n\nBonjour {req.client_nom},\n\n"
            f"{req.contexte or '[Votre reponse a preciser]'}\n\nCordialement,\nVotre gestionnaire"
        )

    from llm.gemini_client import ask_gemini
    prompt = (
        "Redige en francais un brouillon de courrier d'assurance, clair, professionnel et cordial. "
        "Ne l'envoie pas. N'invente ni garantie, ni delai, ni decision, ni obligation legale. "
        "Utilise seulement les informations fournies; conserve les champs entre crochets si une information manque. "
        "Commence par 'Objet :' puis redige le courrier.\n\n"
        f"Type : {types[req.type_courrier]}\nDestinataire : {req.client_nom}\n"
        f"Reference dossier : {reference}\nContexte fourni par le gestionnaire : {contexte}\nTon : {req.ton}"
    )
    draft = ask_gemini(prompt, fallback_default=fallback)
    if not draft or draft.lstrip().startswith('{'):
        draft = fallback
    log_decision('courrier_ia_genere', {
        'type': req.type_courrier,
        'reference': req.reference,
        'actor': gestionnaire.get('gestionnaire_id') or gestionnaire.get('username'),
    })
    return {'courrier': draft, 'destinataire': req.client_email, 'envoye': False}


# =========================================================================
# ENDPOINTS CHAT AVEC HISTORIQUE PERSISTANT ET SOURCES RAG
# =========================================================================

@app.get('/api/chat/history')
def api_get_chat_history(
    authorization: Optional[str] = Header(None),
    token: Optional[str] = Query(None),
    session_id: str = 'default'
):
    """Récupère l'historique complet des messages pour le gestionnaire connecté."""
    try:
        try:
            gest = _extract_gestionnaire(authorization, token)
            gest_id = gest.get('gestionnaire_id') or gest.get('username') or 'anonymous'
        except Exception:
            gest_id = 'anonymous'

        messages = get_chat_history(gest_id, session_id=session_id)
        return {"history": messages, "gestionnaire_id": gest_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete('/api/chat/history')
def api_clear_chat_history(
    authorization: Optional[str] = Header(None),
    token: Optional[str] = Query(None),
    session_id: str = 'default'
):
    """Efface l'historique de conversation du gestionnaire."""
    try:
        try:
            gest = _extract_gestionnaire(authorization, token)
            gest_id = gest.get('gestionnaire_id') or gest.get('username') or 'anonymous'
        except Exception:
            gest_id = 'anonymous'

        clear_chat_history(gest_id, session_id=session_id)
        return {"status": "success", "message": "Historique de conversation effacé."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post('/api/chat')
def api_chat(
    req: ChatRequest,
    authorization: Optional[str] = Header(None),
    token: Optional[str] = Query(None)
):
    """
    Assistant IA : interroge le RAG sur tous les documents persistants et enregistre la conversation.
    """
    try:
        try:
            gest = _extract_gestionnaire(authorization, token)
            gest_id = gest.get('gestionnaire_id') or gest.get('username') or 'anonymous'
        except Exception:
            gest_id = 'anonymous'

        session_id = req.session_id or 'default'

        # 1. Sauvegarder le message utilisateur dans MySQL
        save_chat_message(gest_id, 'user', req.message, session_id=session_id)

        # 2. Récupérer l'historique récent pour le contexte
        past_history = get_chat_history(gest_id, session_id=session_id, limit=6)

        # 3. Interroger l'assistant IA avec RAG
        reponse, sources = chat_with_gestionnaire(req.message, history=past_history)

        # 4. Sauvegarder la réponse de l'assistant IA dans MySQL
        save_chat_message(gest_id, 'bot', reponse, sources=sources, session_id=session_id)

        return {
            'reponse': reponse,
            'sources': sources,
            'gestionnaire_id': gest_id
        }
    except Exception as e:
        logger.error(f"Erreur API Chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))



@app.get('/api/historique')
@app.get('/api/audit')
def api_historique(authorization: Optional[str] = Header(None), token: Optional[str] = Query(None)):
    from tools.audit_log_tool import get_audit_logs
    try:
        gestionnaire = _extract_gestionnaire(authorization, token)
        agence_id = gestionnaire.get('agence_id')
    except Exception:
        agence_id = None

    logs = get_audit_logs(agence_id)
    return {"logs": logs, "historique": logs}




@app.post('/api/alerts/validate')
def api_validate_alert(req: ValidateRequest, authorization: Optional[str] = Header(None), token: Optional[str] = Query(None)):
    """Endpoint pour que le gestionnaire valide/ajuste/rejette une alerte."""
    gestionnaire = _extract_gestionnaire(authorization, token)
    log_decision('alert_validation_request', {
        'action': req.action,
        'actor': gestionnaire.get('gestionnaire_id'),
        'comment': req.comment,
    })

    state = req.state or {}
    result = {'status': 'recorded', 'action': req.action}

    alert_id = state.get('alert_id') or state.get('id')
    validation_status = {
        'validate': 'validee', 'apply': 'validee', 'validee': 'validee',
        'reject': 'rejetee', 'rejetee': 'rejetee',
        'pas_maintenant': 'pas_maintenant',
    }.get(req.action)
    if alert_id and validation_status:
        if not update_alert_validation_status(
            int(alert_id), validation_status,
            gestionnaire.get('gestionnaire_id') or gestionnaire.get('username') or 'gestionnaire',
            req.comment,
        ):
            raise HTTPException(status_code=500, detail="Impossible d'enregistrer le statut de validation.")

    if req.apply_changes and req.action in ('apply', 'validate'):
        urgency = state.get('urgency_level', 'eleve')
        allow_auto = settings.AUTO_APPLY_LOW_RISK and (
            urgency == 'faible' or gestionnaire.get('role') == 'system'
        )
        if not allow_auto:
            result['applied'] = False
            result['reason'] = 'auto_apply_not_allowed_by_policy'
            return result

        mod_type = state.get('modification_type') or state.get('event_type')
        try:
            revert_id = None
            if mod_type == 'contrat':
                contrat_id = state.get('contrat_id') or state.get('target_id')
                updates = state.get('contrat_updates') or state.get('updates') or {}
                prev = get_contrat(contrat_id) or {}
                revert_id = save_revert('contrat', contrat_id, prev, gestionnaire.get('gestionnaire_id'))
                res = modifier_contrat(contrat_id, updates, gestionnaire)
                result.update({'applied': True, 'result': res, 'revert_id': revert_id})
            elif mod_type == 'sinistre':
                sinistre_id = state.get('sinistre_id') or state.get('target_id')
                updates = state.get('sinistre_updates') or state.get('updates') or {}
                contrat_id = state.get('contrat_id') or updates.get('contrat_id')
                prev_list = get_sinistres(contrat_id) if contrat_id else []
                prev = next((s for s in prev_list if s.get('id') == sinistre_id), {})
                revert_id = save_revert('sinistre', sinistre_id, prev, gestionnaire.get('gestionnaire_id'))
                res = modifier_sinistre(sinistre_id, updates, gestionnaire)
                result.update({'applied': True, 'result': res, 'revert_id': revert_id})
        except Exception as e:
            result.update({'applied': False, 'error': str(e)})

    if req.action in ('validate', 'apply', 'validee'):
        cid = state.get('contrat_id') or 'CSTR78199'
        contrat = get_contrat(cid) or {
            'id': cid,
            'client': 'Souheil Khadhraoui',
            'type_contrat': 'Auto',
            'statut': 'actif',
            'garantie_max': 100000,
            'franchise': 500,
            'prime_mensuelle': 120,
            'agence_nom': 'Agence Tunis Centre'
        }
        client_nom = contrat.get('client') or contrat.get('client_id') or 'Souheil Khadhraoui'
        client_email = contrat.get('client_email') or f"{client_nom.lower().replace(' ', '.')}@email.com"

        email_draft = {
            "destinataire": client_email,
            "client_nom": client_nom,
            "sujet": f"📋 Avenant Contractuel & Décision Validée — Contrat N° {cid}",
            "contenu": (
                f"Bonjour {client_nom},\n\n"
                f"Nous vous informons que votre dossier d'assurance pour le contrat {cid} ({str(contrat.get('type_contrat', 'Auto')).upper()}) "
                f"a été examiné et validé par votre gestionnaire référent suite à l'évaluation du risque.\n\n"
                f"📌 Récapitulatif des garanties contractuelles validées :\n"
                f"• Statut du contrat : VALIDÉ & ACTIF\n"
                f"• Plafond de Garantie Max : {float(contrat.get('garantie_max', 100000)):,.2f} DT\n"
                f"• Franchise applicable : {float(contrat.get('franchise', 500)):,.2f} DT\n"
                f"• Prime mensuelle : {float(contrat.get('prime_mensuelle', 120)):,.2f} DT/mois\n\n"
                f"Votre Avenant officiel est généré et prêt pour signature électronique.\n\n"
                f"Cordialement,\nService Gestion des Assurances — Plateforme Contrat Vivant"
            ),
            "avenant_url": f"/api/pdf/avenant/{cid}",
            "filename": f"Avenant_{cid}.pdf"
        }
        result['status'] = 'validee'
        result['email_draft'] = email_draft
        result['avenant_url'] = f"/api/pdf/avenant/{cid}"
        result['message'] = "Décision validée avec succès. Projet d'avenant généré et email client prêt pour signature."

    return result


@app.post('/api/alerts/rollback')
def api_alerts_rollback(req: RollbackRequest, authorization: Optional[str] = Header(None), token: Optional[str] = Query(None)):
    gestionnaire = _extract_gestionnaire(authorization, token)
    entry = get_revert(req.revert_id)
    if not entry:
        raise HTTPException(status_code=404, detail='revert_id not found')

    kind = entry.get('kind')
    target_id = entry.get('target_id')
    previous = entry.get('previous') or {}

    try:
        if kind == 'contrat':
            res = modifier_contrat(target_id, previous, gestionnaire)
            log_decision('revert_applied', {'revert_id': req.revert_id, 'actor': gestionnaire.get('gestionnaire_id')})
            return {'status': 'reverted', 'result': res}
        if kind == 'sinistre':
            res = modifier_sinistre(target_id, previous, gestionnaire)
            log_decision('revert_applied', {'revert_id': req.revert_id, 'actor': gestionnaire.get('gestionnaire_id')})
            return {'status': 'reverted', 'result': res}
        raise HTTPException(status_code=400, detail='unsupported revert kind')
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =========================================================================
# ENDPOINTS OCR CONSTAT AMIABLE & ANALYSEUR DE DEVIS GARAGISTE
# =========================================================================

from tools.constat_ocr_tool import extract_constat_info
from tools.devis_analyzer_tool import analyze_devis_repair

@app.post('/api/ocr/constat')
async def api_extract_constat(
    file: UploadFile = File(...),
    authorization: Optional[str] = Header(None),
    token: Optional[str] = Query(None)
):
    """
    Extrait les données manuscrites/imprimées d'un Formulaire de Constat Amiable.
    """
    try:
        gestionnaire = _extract_gestionnaire(authorization, token)
    except Exception:
        gestionnaire = {"username": "Gestionnaire", "gestionnaire_id": "G123"}

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Fichier d'image du constat vide")

    try:
        res = extract_constat_info(content)
        log_decision("ocr_constat_extracted", {
            "filename": file.filename,
            "vehicule_a": res.get("vehicule_a", {}).get("immatriculation"),
            "vehicule_b": res.get("vehicule_b", {}).get("immatriculation"),
            "responsabilite": res.get("responsabilite_estimee"),
            "actor": gestionnaire.get("username")
        }, gestionnaire_id=gestionnaire.get("gestionnaire_id"))
        return res
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error("Erreur extraction constat OCR: %s", e)
        raise HTTPException(status_code=500, detail=f"Erreur extraction du constat: {str(e)}")


@app.post('/api/devis/analyser')
async def api_analyser_devis(
    file: UploadFile = File(...),
    authorization: Optional[str] = Header(None),
    token: Optional[str] = Query(None)
):
    """
    Analyse un devis de réparation automobile (garage) et vérifie la surfacturation vs barème.
    """
    try:
        gestionnaire = _extract_gestionnaire(authorization, token)
    except Exception:
        gestionnaire = {"username": "Gestionnaire", "gestionnaire_id": "G123"}

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Fichier du devis vide")

    try:
        res = analyze_devis_repair(content)
        log_decision("devis_repair_analyzed", {
            "filename": file.filename,
            "garage": res.get("garage_nom"),
            "montant_reclaime": res.get("montant_total_reclaime"),
            "est_surfacture": res.get("est_surfacture"),
            "surfacturation_pct": res.get("surfacturation_globale_pct"),
            "actor": gestionnaire.get("username")
        }, gestionnaire_id=gestionnaire.get("gestionnaire_id"))
        return res
    except Exception as e:
        logger.error("Erreur analyse devis: %s", e)
        raise HTTPException(status_code=500, detail=f"Erreur analyse du devis: {str(e)}")
