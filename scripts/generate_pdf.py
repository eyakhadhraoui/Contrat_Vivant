"""
Générateur de PDF pour le Cahier des Charges & Guide d'Exécution — Le Contrat Vivant.
Utilise ReportLab pour générer un document PDF professionnel et mis en page.
"""

import os
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY


class NumberedCanvas:
    """Canvas personnalisé pour ajouter les en-têtes et pieds de page numérotés."""

    def __init__(self, *args, **kwargs):
        pass


def draw_header_footer(canvas, doc):
    canvas.saveState()
    # Header (pages 2+)
    if doc.page > 1:
        canvas.setFont("Helvetica-Bold", 8)
        canvas.setFillColor(colors.HexColor("#64748b"))
        canvas.drawString(1.8 * cm, 28.5 * cm, "LE CONTRAT VIVANT — CAHIER DES CHARGES & GUIDE D'EXÉCUTION")
        canvas.setStrokeColor(colors.HexColor("#cbd5e1"))
        canvas.setLineWidth(0.5)
        canvas.line(1.8 * cm, 28.2 * cm, 19.2 * cm, 28.2 * cm)

    # Footer (all pages)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#94a3b8"))
    canvas.drawString(1.8 * cm, 1.2 * cm, "Confidentiel — Architecture Multi-Agents LangGraph")
    page_text = f"Page {doc.page}"
    canvas.drawRightString(19.2 * cm, 1.2 * cm, page_text)
    canvas.setStrokeColor(colors.HexColor("#e2e8f0"))
    canvas.setLineWidth(0.5)
    canvas.line(1.8 * cm, 1.6 * cm, 19.2 * cm, 1.6 * cm)
    canvas.restoreState()


def build_pdf(filename="Cahier_des_Charges_Contrat_Vivant.pdf"):
    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        leftMargin=1.8 * cm,
        rightMargin=1.8 * cm,
        topMargin=2.2 * cm,
        bottomMargin=2.2 * cm,
    )

    styles = getSampleStyleSheet()

    # Define custom styles
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=24,
        leading=28,
        textColor=colors.HexColor("#0f172a"),
        alignment=TA_LEFT,
        spaceAfter=6,
    )

    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#e54838"),
        alignment=TA_LEFT,
        spaceAfter=15,
    )

    h1_style = ParagraphStyle(
        "SectionH1",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=19,
        textColor=colors.HexColor("#0f172a"),
        spaceBefore=16,
        spaceAfter=10,
        keepWithNext=True,
    )

    h2_style = ParagraphStyle(
        "SectionH2",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#1e293b"),
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True,
    )

    body_style = ParagraphStyle(
        "BodyDark",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor("#334155"),
        spaceAfter=8,
        alignment=TA_JUSTIFY,
    )

    bullet_style = ParagraphStyle(
        "BulletText",
        parent=body_style,
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=5,
    )

    code_style = ParagraphStyle(
        "CodeBlock",
        parent=styles["Normal"],
        fontName="Courier",
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#0f172a"),
        backColor=colors.HexColor("#f1f5f9"),
        borderColor=colors.HexColor("#cbd5e1"),
        borderWidth=0.5,
        borderPadding=6,
        spaceBefore=6,
        spaceAfter=10,
        borderRadius=4,
    )

    callout_style = ParagraphStyle(
        "CalloutText",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#1e293b"),
        backColor=colors.HexColor("#fef2f2"),
        borderColor=colors.HexColor("#fca5a5"),
        borderWidth=0.8,
        borderPadding=8,
        spaceBefore=8,
        spaceAfter=12,
    )

    table_header_style = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=11,
        textColor=colors.white,
        alignment=TA_CENTER,
    )

    table_cell_style = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#1e293b"),
    )

    elements = []

    # Title Banner Block
    elements.append(Paragraph("CAHIER DES CHARGES TECHNIQUE & GUIDE D'EXÉCUTION", title_style))
    elements.append(Paragraph("Plateforme 'Le Contrat Vivant' — Architecture Multi-Agents Autonome (LangGraph & FastAPI)", subtitle_style))
    elements.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#e54838"), spaceBefore=0, spaceAfter=15))

    # Executive Summary Card
    summary_html = (
        "<b>RÉSUMÉ EXÉCUTIF :</b> Ce document constitue le dossier de référence et le manuel d'exploitation pour la plateforme "
        "<b>Contrat Vivant</b>. Il détaille les étapes de lancement, le fonctionnement complet de l'architecture multi-agents sous "
        "<b>LangGraph</b>, le paramétrage de l'API FastAPI, les spécifications des sous-agents métiers, les workflows de validation "
        "humaine (HITL) et les mesures de sécurité et résilience."
    )
    elements.append(Paragraph(summary_html, callout_style))

    # SECTION 1 : GUIDE D'EXÉCUTION & MANUEL TECHNIQUE
    elements.append(Paragraph("1. GUIDE D'EXÉCUTION & DÉMARRAGE RAPIDE", h1_style))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cbd5e1"), spaceBefore=0, spaceAfter=8))

    elements.append(Paragraph("<b>Préréquis Système :</b>", h2_style))
    elements.append(Paragraph("• <b>Python :</b> Version 3.10 ou supérieure.", bullet_style))
    elements.append(Paragraph("• <b>Base de données :</b> Serveur MySQL (Optionnel en mode autonome / fallback sécurisé).", bullet_style))
    elements.append(Paragraph("• <b>Variables d'environnement :</b> Clé API Gemini (<code>GEMINI_API_KEY</code>) ou Ollama local.", bullet_style))

    elements.append(Paragraph("<b>Étape 1 : Installation des dépendances</b>", h2_style))
    elements.append(Paragraph("Exécuter la commande suivante dans le terminal à la racine du projet :", body_style))
    cmd1 = "pip install -r requirements.txt"
    elements.append(Paragraph(cmd1, code_style))

    elements.append(Paragraph("<b>Étape 2 : Lancement du Serveur Backend FastAPI</b>", h2_style))
    elements.append(Paragraph("Pour démarrer le serveur API et servir l'application Web :", body_style))
    cmd2 = "python -m uvicorn api.main_api:app --reload --host 127.0.0.1 --port 8000"
    elements.append(Paragraph(cmd2, code_style))

    elements.append(Paragraph("<b>Étape 3 : Accès à l'Interface Utilisateur (UI)</b>", h2_style))
    elements.append(Paragraph("• <b>Page de connexion :</b> <code>http://127.0.0.1:8000/login</code> (Design officiel Contrat Vivant).", bullet_style))
    elements.append(Paragraph("• <b>Tableau de bord :</b> <code>http://127.0.0.1:8000/app</code> (Accessible après connexion).", bullet_style))
    elements.append(Paragraph("• <b>Identifiants de démonstration :</b> Nom d'utilisateur : <code>sarra.khelifi</code> ou <code>ahmed.trabelsi</code> | Mot de passe : <code>password123</code>.", bullet_style))

    elements.append(Paragraph("<b>Étape 4 : Exécution des Tests d'Intégration & Multi-Agents</b>", h2_style))
    elements.append(Paragraph("Pour vérifier l'intégrité globale du système multi-agents et des règles métiers :", body_style))
    cmd3 = "python -m unittest tests/test_multi_agent.py\npython -m unittest discover tests"
    elements.append(Paragraph(cmd3, code_style))

    elements.append(Spacer(1, 10))

    # SECTION 2 : CAHIER DES CHARGES FONCTIONNEL & ARCHITECTURE
    elements.append(Paragraph("2. CAHIER DES CHARGES FONCTIONNEL & ARCHITECTURE MULTI-AGENTS", h1_style))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cbd5e1"), spaceBefore=0, spaceAfter=8))

    elements.append(Paragraph(
        "La plateforme repose sur un <b>Système Multi-Agents hiérarchique avec Superviseur</b> sous <b>LangGraph</b>, "
        "subdivisant le traitement d'un dossier contractuel en compétences spécialisées :", body_style
    ))

    # Table of Agents
    agent_data = [
        [
            Paragraph("Agent", table_header_style),
            Paragraph("Module Python", table_header_style),
            Paragraph("Rôle & Responsabilités Métiers", table_header_style),
        ],
        [
            Paragraph("<b>SupervisorAgent</b>", table_cell_style),
            Paragraph("<code>agents/multi_agent_system.py</code>", table_cell_style),
            Paragraph("Orchestrateur principal du workflow. Pilote l'exécution des sous-agents, agrège les résultats dans <code>agent_metadata</code> et gère le passage à la validation humaine (HITL).", table_cell_style),
        ],
        [
            Paragraph("<b>CollectorAgent</b>", table_cell_style),
            Paragraph("<code>agents/collector_agent.py</code>", table_cell_style),
            Paragraph("Collecte et intègre les données SI (Contrats & Sinistres). Évalue la complétude (<code>missing_data</code>) et le niveau de confiance (<code>confidence</code>).", table_cell_style),
        ],
        [
            Paragraph("<b>RiskAnalysisAgent</b>", table_cell_style),
            Paragraph("<code>agents/risk_agent.py</code>", table_cell_style),
            Paragraph("Évalue les risques en croisant le moteur de règles déterministes et l'analyse LLM contextuelle (Gemini/Ollama). Calcule l'urgence (0-100) et identifie les anomalies.", table_cell_style),
        ],
        [
            Paragraph("<b>AlertNotificationAgent</b>", table_cell_style),
            Paragraph("<code>agents/alert_agent.py</code>", table_cell_style),
            Paragraph("Rédige la synthèse du dossier, construit la carte d'alerte, formule les recommandations, effectue le routage pôle Assurances/Sinistres et notifie par Email/Teams.", table_cell_style),
        ],
    ]

    t_agents = Table(agent_data, colWidths=[3.2 * cm, 4.5 * cm, 9.7 * cm])
    t_agents.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0f172a")),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor("#f8fafc")),
        ('BACKGROUND', (0, 3), (-1, 3), colors.HexColor("#f8fafc")),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(t_agents)

    elements.append(Spacer(1, 12))

    # SECTION 3 : SPÉCIFICATIONS DES ENDPOINTS API (REST FastAPI)
    elements.append(Paragraph("3. SPÉCIFICATIONS DES ENDPOINTS API (FastAPI)", h1_style))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cbd5e1"), spaceBefore=0, spaceAfter=8))

    api_data = [
        [
            Paragraph("Méthode / Route", table_header_style),
            Paragraph("Description & Comportement Multi-Agents", table_header_style),
            Paragraph("Réponse & Code Status", table_header_style),
        ],
        [
            Paragraph("<code>POST /api/login</code>", table_cell_style),
            Paragraph("Authentification des gestionnaires d'assurance et émission du jeton JWT.", table_cell_style),
            Paragraph("<code>200 OK</code> (Token) / <code>401 Unauthorized</code>", table_cell_style),
        ],
        [
            Paragraph("<code>POST /api/analyser</code>", table_cell_style),
            Paragraph("Déclenche le workflow multi-agents LangGraph (Collector -> Risk -> Alert -> HITL). Retourne l'état complet et <code>agent_metadata</code>.", table_cell_style),
            Paragraph("<code>200 OK</code> (ContratVivantState) / <code>404 Not Found</code>", table_cell_style),
        ],
        [
            Paragraph("<code>POST /api/alerts/validate</code>", table_cell_style),
            Paragraph("Soumission de la décision humaine (Valider / Ajuster / Rejeter). Applique les modifications dans le SI si autorisé.", table_cell_style),
            Paragraph("<code>200 OK</code> (Statut d'application + Revert ID)", table_cell_style),
        ],
        [
            Paragraph("<code>POST /api/alerts/rollback</code>", table_cell_style),
            Paragraph("Restauration d'une version précédente de contrat ou de sinistre via <code>revert_id</code>.", table_cell_style),
            Paragraph("<code>200 OK</code> (State Reverted) / <code>400 Bad Request</code>", table_cell_style),
        ],
    ]

    t_api = Table(api_data, colWidths=[4.2 * cm, 8.5 * cm, 4.7 * cm])
    t_api.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0f172a")),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor("#f8fafc")),
        ('BACKGROUND', (0, 3), (-1, 3), colors.HexColor("#f8fafc")),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(t_api)

    elements.append(Spacer(1, 12))

    # SECTION 4 : SÉCURITÉ, DÉFENSE EN PROFONDEUR & RÉSILIENCE
    elements.append(Paragraph("4. BOUCLE HUMAINE (HITL), SÉCURITÉ & RÉSILIENCE", h1_style))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cbd5e1"), spaceBefore=0, spaceAfter=8))

    elements.append(Paragraph("<b>Boucle de Validation Humaine (HITL) :</b>", h2_style))
    elements.append(Paragraph("Aucune écriture dans les bases SI n'est autorisée sans la validation explicite d'un gestionnaire habilité. Le statut de validation passe successivement par :", body_style))
    elements.append(Paragraph("• <code>en_attente_validation</code> : Dossier analysé et soumis au gestionnaire.", bullet_style))
    elements.append(Paragraph("• <code>en_attente_bon_gestionnaire</code> : Redirection si le rôle du gestionnaire connecté ne correspond pas au pôle concerné.", bullet_style))
    elements.append(Paragraph("• <code>escalade_aucun_gestionnaire</code> : Escalade automatique vers le superviseur si aucun gestionnaire disponible.", bullet_style))

    elements.append(Paragraph("<b>Résilience & Mode Dégradé :</b>", h2_style))
    elements.append(Paragraph("En cas d'indisponibilité des services LLM (Gemini / Ollama), le système bascule automatiquement sur le <b>Moteur de Règles Métier Déterministe</b> et génère des résumés synthétiques de secours sans jamais bloquer l'exécution du pipeline.", body_style))

    # Footer Metadata Table
    meta_data = [
        [Paragraph("<b>Projet :</b> Le Contrat Vivant", table_cell_style), Paragraph("<b>Version :</b> 2.0 (Multi-Agents)", table_cell_style)],
        [Paragraph("<b>Framework Graph :</b> LangGraph StateGraph", table_cell_style), Paragraph("<b>Framework Web :</b> FastAPI", table_cell_style)],
        [Paragraph("<b>Auteur :</b> Équipe Antigravity / Agent Assurance", table_cell_style), Paragraph("<b>Statut :</b> Approuvé & Testé", table_cell_style)]
    ]
    t_meta = Table(meta_data, colWidths=[8.7 * cm, 8.7 * cm])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f1f5f9")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(Spacer(1, 10))
    elements.append(t_meta)

    # Build PDF
    doc.build(elements, onFirstPage=draw_header_footer, onLaterPages=draw_header_footer)
    print(f"PDF généré avec succès : {filename}")


if __name__ == "__main__":
    build_pdf()
