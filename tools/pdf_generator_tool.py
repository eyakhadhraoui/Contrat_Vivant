import io
import logging
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY

logger = logging.getLogger(__name__)

def draw_pdf_header_footer(canvas, doc, title_text="CONTRAT VIVANT — DOCUMENT OFFICIEL"):
    canvas.saveState()
    # Header
    canvas.setFont("Helvetica-Bold", 8)
    canvas.setFillColor(colors.HexColor("#64748b"))
    canvas.drawString(1.8 * cm, 28.5 * cm, title_text)
    canvas.setStrokeColor(colors.HexColor("#e54838"))
    canvas.setLineWidth(1)
    canvas.line(1.8 * cm, 28.2 * cm, 19.2 * cm, 28.2 * cm)

    # Footer
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#94a3b8"))
    canvas.drawString(1.8 * cm, 1.2 * cm, f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')} — Plateforme d'Assurance Multi-Agents")
    page_text = f"Page {doc.page}"
    canvas.drawRightString(19.2 * cm, 1.2 * cm, page_text)
    canvas.setStrokeColor(colors.HexColor("#cbd5e1"))
    canvas.setLineWidth(0.5)
    canvas.line(1.8 * cm, 1.6 * cm, 19.2 * cm, 1.6 * cm)
    canvas.restoreState()

def generate_contrat_pdf(contrat_data: dict) -> bytes:
    """Génère le PDF professionnel d'une attestation de contrat d'assurance."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=1.8 * cm,
        rightMargin=1.8 * cm,
        topMargin=2.2 * cm,
        bottomMargin=2.2 * cm,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ContratTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=4,
    )

    subtitle_style = ParagraphStyle(
        "ContratSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        textColor=colors.HexColor("#e54838"),
        spaceAfter=15,
    )

    h2_style = ParagraphStyle(
        "SectionH2",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#1e293b"),
        spaceBefore=10,
        spaceAfter=6,
    )

    body_style = ParagraphStyle(
        "BodyText",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor("#334155"),
        spaceAfter=6,
    )

    cell_bold = ParagraphStyle("CellBold", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=9, textColor=colors.HexColor("#0f172a"))
    cell_norm = ParagraphStyle("CellNorm", parent=styles["Normal"], fontName="Helvetica", fontSize=9, textColor=colors.HexColor("#334155"))

    elements = []

    # En-tête du document
    elements.append(Paragraph(f"ATTESTATION D'ASSURANCE — {str(contrat_data.get('type_contrat') or contrat_data.get('type') or 'AUTO').upper()}", title_style))
    elements.append(Paragraph(f"N° de Contrat : <b>{contrat_data.get('id', 'N/A')}</b> | Agence : {contrat_data.get('agence_id', 'AG01')}", subtitle_style))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#e54838"), spaceBefore=0, spaceAfter=12))

    # Tableau résumé
    table_info = [
        [Paragraph("Titulaire du contrat", cell_bold), Paragraph(str(contrat_data.get("client") or contrat_data.get("client_id") or "Client Assuré"), cell_norm)],
        [Paragraph("Formule souscrite", cell_bold), Paragraph(str(contrat_data.get("type_contrat") or contrat_data.get("type") or "Auto").capitalize(), cell_norm)],
        [Paragraph("Plafond de Garantie Max", cell_bold), Paragraph(f"{Number(contrat_data.get('garantie_max', 0)):,.2f} DT".replace(',', ' '), cell_bold)],
        [Paragraph("Franchise applicable", cell_bold), Paragraph(f"{Number(contrat_data.get('franchise', 0)):,.2f} DT".replace(',', ' '), cell_norm)],
        [Paragraph("Prime Mensuelle / Annuelle", cell_bold), Paragraph(f"{contrat_data.get('prime_mensuelle', 0)} DT / {contrat_data.get('prime_annuelle', 0)} DT", cell_norm)],
        [Paragraph("Période de Couverture", cell_bold), Paragraph(f"Du {contrat_data.get('date_debut', 'N/A')} au {contrat_data.get('date_fin', 'N/A')} ({contrat_data.get('duree_mois', 12)} mois)", cell_norm)],
        [Paragraph("Mode & Fréquence Paiement", cell_bold), Paragraph(f"{contrat_data.get('mode_paiement', 'Virement')} ({contrat_data.get('frequence_paiement', 'Mensuel')})", cell_norm)],
        [Paragraph("Statut actuel", cell_bold), Paragraph(str(contrat_data.get("statut", "actif")).upper(), cell_bold)],
        [Paragraph("Gestionnaire Créateur", cell_bold), Paragraph(str(contrat_data.get("gestionnaire_createur_id", "G123")), cell_norm)],
    ]

    t = Table(table_info, colWidths=[6 * cm, 11.4 * cm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor("#f8fafc")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 14))

    # Détails Garanties & Exclusions
    elements.append(Paragraph("Garanties & Extendue de la Couverture", h2_style))
    elements.append(Paragraph(contrat_data.get("couverture") or "Garantie Responsabilité Civile, Incendie, Vol et Bris de Glace.", body_style))

    elements.append(Spacer(1, 8))
    elements.append(Paragraph("Exclusions de Garantie", h2_style))
    elements.append(Paragraph(contrat_data.get("exclusions") or "Usure normale, faute intentionnelle, conduite sous l'emprise d'un état alcoolique.", body_style))

    elements.append(Spacer(1, 8))
    elements.append(Paragraph("Observations du Gestionnaire", h2_style))
    elements.append(Paragraph(contrat_data.get("observations") or "Contrat conforme et validé par le pôle gestion des assurances.", body_style))

    # Tampon de validation
    elements.append(Spacer(1, 20))
    signature_data = [
        [Paragraph("<b>Pour la Compagnie d'Assurance</b>", cell_norm), Paragraph("<b>Signature du Gestionnaire</b>", cell_norm)],
        [Paragraph("Plateforme Contrat Vivant<br/>Cachet Officiel Agence", cell_norm), Paragraph(f"Identifiant : {contrat_data.get('gestionnaire_createur_id', 'G123')}<br/>Validé électroniquement", cell_norm)]
    ]
    t_sig = Table(signature_data, colWidths=[8.7 * cm, 8.7 * cm])
    t_sig.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f1f5f9")),
        ('PADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(t_sig)

    doc.build(elements, onFirstPage=lambda c, d: draw_pdf_header_footer(c, d, "ATTESTATION OFFICIELLE DE CONTRAT"), onLaterPages=lambda c, d: draw_pdf_header_footer(c, d, "ATTESTATION OFFICIELLE DE CONTRAT"))
    return buffer.getvalue()


def generate_sinistre_pdf(sinistre_data: dict) -> bytes:
    """Génère le PDF professionnel d'un rapport de déclaration de sinistre."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=1.8 * cm,
        rightMargin=1.8 * cm,
        topMargin=2.2 * cm,
        bottomMargin=2.2 * cm,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "SinistreTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=4,
    )

    subtitle_style = ParagraphStyle(
        "SinistreSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        textColor=colors.HexColor("#dc2626"),
        spaceAfter=15,
    )

    h2_style = ParagraphStyle(
        "SectionH2",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#1e293b"),
        spaceBefore=10,
        spaceAfter=6,
    )

    body_style = ParagraphStyle(
        "BodyText",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor("#334155"),
        spaceAfter=6,
    )

    cell_bold = ParagraphStyle("CellBold", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=9, textColor=colors.HexColor("#0f172a"))
    cell_norm = ParagraphStyle("CellNorm", parent=styles["Normal"], fontName="Helvetica", fontSize=9, textColor=colors.HexColor("#334155"))

    elements = []

    # En-tête du document
    elements.append(Paragraph(f"RAPPORT DE DÉCLARATION DE SINISTRE — {str(sinistre_data.get('type_sinistre') or sinistre_data.get('type') or 'SINISTRE').upper()}", title_style))
    elements.append(Paragraph(f"N° Sinistre : <b>{sinistre_data.get('id', 'N/A')}</b> | Contrat Rattaché : <b>{sinistre_data.get('contrat_id', 'N/A')}</b>", subtitle_style))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#dc2626"), spaceBefore=0, spaceAfter=12))

    # Tableau résumé
    table_info = [
        [Paragraph("Client Assuré", cell_bold), Paragraph(str(sinistre_data.get("client") or "Client Assuré"), cell_norm)],
        [Paragraph("Type de Sinistre", cell_bold), Paragraph(str(sinistre_data.get("type_sinistre") or sinistre_data.get("type") or "Auto"), cell_norm)],
        [Paragraph("Montant Déclaré (Estimé)", cell_bold), Paragraph(f"{Number(sinistre_data.get('montant_declare', 0)):,.2f} DT".replace(',', ' '), cell_bold)],
        [Paragraph("Lieu de Survenance", cell_bold), Paragraph(str(sinistre_data.get("lieu") or sinistre_data.get("lieu_sinistre") or "Non précisé"), cell_norm)],
        [Paragraph("Date du Sinistre / Déclaration", cell_bold), Paragraph(f"Survenu le : {sinistre_data.get('date_sinistre', 'N/A')} | Déclaré le : {sinistre_data.get('date') or sinistre_data.get('date_declaration', 'N/A')}", cell_norm)],
        [Paragraph("Responsabilité Estimée", cell_bold), Paragraph(str(sinistre_data.get("responsabilite", "Indéterminée")).capitalize(), cell_norm)],
        [Paragraph("Statut du Dossier", cell_bold), Paragraph(str(sinistre_data.get("statut", "en_cours")).upper(), cell_bold)],
        [Paragraph("Gestionnaire Traitant", cell_bold), Paragraph(str(sinistre_data.get("gestionnaire_traitant_id", "G123")), cell_norm)],
        [Paragraph("Agence Rattachée", cell_bold), Paragraph(str(sinistre_data.get("agence_id", "AG01")), cell_norm)],
    ]

    t = Table(table_info, colWidths=[6 * cm, 11.4 * cm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor("#fef2f2")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#fca5a5")),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 14))

    # Description des faits
    elements.append(Paragraph("Description Détallée des Faits", h2_style))
    elements.append(Paragraph(sinistre_data.get("description") or "Circonstances du sinistre enregistrées par le déclarant.", body_style))

    elements.append(Spacer(1, 8))
    elements.append(Paragraph("Observations & Remarques d'Expertise", h2_style))
    elements.append(Paragraph(sinistre_data.get("observations") or "Dossier en cours d'instruction et d'évaluation des indemnités.", body_style))

    # Tampon de validation
    elements.append(Spacer(1, 20))
    signature_data = [
        [Paragraph("<b>Pôle Gestion des Sinistres</b>", cell_norm), Paragraph("<b>Signature & Validation</b>", cell_norm)],
        [Paragraph("Rapport officiel transmis au pôle Assurances<br/>Plateforme Contrat Vivant", cell_norm), Paragraph(f"Gestionnaire ID : {sinistre_data.get('gestionnaire_traitant_id', 'G123')}<br/>Certifié conforme", cell_norm)]
    ]
    t_sig = Table(signature_data, colWidths=[8.7 * cm, 8.7 * cm])
    t_sig.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ('PADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(t_sig)

    doc.build(elements, onFirstPage=lambda c, d: draw_pdf_header_footer(c, d, "RAPPORT DÉCLARATION SINISTRE"), onLaterPages=lambda c, d: draw_pdf_header_footer(c, d, "RAPPORT DÉCLARATION SINISTRE"))
    return buffer.getvalue()

def generate_audit_report_pdf(logs: list, agence_id: str = None) -> bytes:
    """Génère le PDF professionnel d'un rapport de synthèse périodique du journal d'audit."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
        topMargin=2.2 * cm,
        bottomMargin=2.2 * cm,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "AuditTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=4,
    )

    subtitle_style = ParagraphStyle(
        "AuditSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#2563eb"),
        spaceAfter=12,
    )

    cell_bold = ParagraphStyle("CellBold", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=8, textColor=colors.HexColor("#0f172a"))
    cell_norm = ParagraphStyle("CellNorm", parent=styles["Normal"], fontName="Helvetica", fontSize=8, textColor=colors.HexColor("#334155"))

    elements = []

    # En-tête
    agence_str = agence_id or "Toutes les agences"
    elements.append(Paragraph("RAPPORT DE SYNTHÈSE PÉRIODIQUE — JOURNAL D'AUDIT", title_style))
    elements.append(Paragraph(f"Pôle Gestion Assurance | Agence : <b>{agence_str}</b> | Nombre d'événements : {len(logs)}", subtitle_style))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#2563eb"), spaceBefore=0, spaceAfter=10))

    # En-tête du tableau
    table_data = [
        [
            Paragraph("<b>Horodatage</b>", cell_bold),
            Paragraph("<b>Étape / Agent</b>", cell_bold),
            Paragraph("<b>Dossier</b>", cell_bold),
            Paragraph("<b>Acteur</b>", cell_bold),
            Paragraph("<b>Détails de l'Action</b>", cell_bold),
            Paragraph("<b>Statut</b>", cell_bold),
        ]
    ]

    for l in logs[:100]:  # Limiter aux 100 plus récents pour lisibilité PDF
        table_data.append([
            Paragraph(str(l.get("timestamp", ""))[:19], cell_norm),
            Paragraph(str(l.get("step") or l.get("agent") or "System"), cell_bold),
            Paragraph(str(l.get("dossier") or l.get("contrat_id") or "N/A"), cell_norm),
            Paragraph(str(l.get("actor") or l.get("gestionnaire_id") or "G123"), cell_norm),
            Paragraph(str(l.get("details") or l.get("message") or l.get("action") or "")[:120], cell_norm),
            Paragraph(str(l.get("status", "OK")), cell_bold),
        ])

    t = Table(table_data, colWidths=[3.2 * cm, 3.0 * cm, 2.3 * cm, 2.5 * cm, 5.5 * cm, 1.5 * cm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('PADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(t)

    doc.build(
        elements,
        onFirstPage=lambda c, d: draw_pdf_header_footer(c, d, "RAPPORT D'AUDIT ET DE DÉCISION — CONTRAT VIVANT"),
        onLaterPages=lambda c, d: draw_pdf_header_footer(c, d, "RAPPORT D'AUDIT ET DE DÉCISION — CONTRAT VIVANT")
    )
    return buffer.getvalue()


def Number(val):
    try:
        return float(val or 0)
    except Exception:
        return 0.0