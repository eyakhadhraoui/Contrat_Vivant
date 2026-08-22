from html import escape
from datetime import datetime


def _urgency_color(level: str) -> str:
    return {
        "critique": "#7f1d1d",
        "eleve": "#dc2626",
        "moyen": "#d97706",
        "faible": "#16a34a",
    }.get(level, "#64748b")


def _base_layout(title: str, body_html: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{escape(title)}</title>
</head>
<body style="margin:0;padding:0;background:#f1f5f9;font-family:Segoe UI,Arial,sans-serif;color:#0f172a;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#f1f5f9;padding:24px 0;">
    <tr>
      <td align="center">
        <table role="presentation" width="620" cellspacing="0" cellpadding="0" style="background:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 4px 16px rgba(15,23,42,0.08);">
          <tr>
            <td style="background:linear-gradient(135deg,#1e3a8a,#2563eb);padding:24px 32px;color:#ffffff;">
              <div style="font-size:12px;letter-spacing:1px;text-transform:uppercase;opacity:0.85;">Contrat Vivant — Agent Assurance</div>
              <div style="font-size:22px;font-weight:700;margin-top:6px;">{escape(title)}</div>
            </td>
          </tr>
          <tr>
            <td style="padding:28px 32px;">{body_html}</td>
          </tr>
          <tr>
            <td style="padding:16px 32px 24px;background:#f8fafc;border-top:1px solid #e2e8f0;font-size:12px;color:#64748b;">
              Message genere automatiquement le {datetime.now().strftime('%d/%m/%Y a %H:%M')} — Decision finale humaine requise
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


def _info_table(rows: list[tuple[str, str]]) -> str:
    cells = ""
    for label, value in rows:
        cells += f"""
        <tr>
          <td style="padding:10px 12px;border-bottom:1px solid #e2e8f0;font-weight:600;width:38%;background:#f8fafc;">{escape(label)}</td>
          <td style="padding:10px 12px;border-bottom:1px solid #e2e8f0;">{escape(str(value))}</td>
        </tr>"""
    return f"""
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="border:1px solid #e2e8f0;border-radius:8px;overflow:hidden;margin:16px 0;">
      {cells}
    </table>"""


def _score_badge(score: float, level: str) -> str:
    color = _urgency_color(level)
    return f"""
    <div style="text-align:center;margin:16px 0 20px;padding:20px;background:#f8fafc;border-radius:10px;border:1px solid #e2e8f0;">
      <div style="font-size:42px;font-weight:800;color:{color};">{score:.0f}<span style="font-size:18px;color:#64748b;">/100</span></div>
      <div style="display:inline-block;margin-top:8px;padding:6px 16px;border-radius:999px;background:{color};color:#fff;font-weight:700;text-transform:uppercase;letter-spacing:1px;">
        Urgence {escape(level)}
      </div>
    </div>"""


def _factors_block(factors: list | None) -> str:
    if not factors:
        return ""
    rows = ""
    for i, factor in enumerate(factors[:3], 1):
        rows += f"""
        <tr>
          <td style="padding:8px 10px;border-bottom:1px solid #e2e8f0;font-weight:700;width:8%;">{i}</td>
          <td style="padding:8px 10px;border-bottom:1px solid #e2e8f0;width:25%;">{escape(factor.get('label', ''))}</td>
          <td style="padding:8px 10px;border-bottom:1px solid #e2e8f0;width:12%;font-weight:700;">{factor.get('contribution', 0)} pts</td>
          <td style="padding:8px 10px;border-bottom:1px solid #e2e8f0;color:#475569;">{escape(factor.get('detail', ''))}</td>
        </tr>"""
    return f"""
    <h3 style="margin:20px 0 8px;font-size:15px;color:#1e293b;">Top 3 facteurs de risque</h3>
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="border:1px solid #e2e8f0;border-radius:8px;overflow:hidden;">
      <tr style="background:#f1f5f9;">
        <th style="padding:8px 10px;text-align:left;">#</th>
        <th style="padding:8px 10px;text-align:left;">Facteur</th>
        <th style="padding:8px 10px;text-align:left;">Score</th>
        <th style="padding:8px 10px;text-align:left;">Detail</th>
      </tr>
      {rows}
    </table>"""


def _anomalies_block(anomalies: list | None) -> str:
    if not anomalies:
        return ""
    items = ""
    for anomaly in anomalies:
        severity = anomaly.get("severity", "faible")
        color = _urgency_color(severity)
        items += f"""
        <li style="margin-bottom:10px;">
          <span style="display:inline-block;padding:2px 8px;border-radius:999px;background:{color};color:#fff;font-size:11px;font-weight:700;text-transform:uppercase;">{escape(severity)}</span>
          <strong style="margin-left:6px;">{escape(anomaly.get('rule', 'anomalie'))}</strong><br>
          <span style="color:#475569;">{escape(anomaly.get('message', ''))}</span>
        </li>"""
    return f"""
    <h3 style="margin:20px 0 8px;font-size:15px;color:#1e293b;">Signaux detectes</h3>
    <ul style="margin:0;padding-left:18px;">{items}</ul>"""


def render_notification_email(
    title: str,
    intro: str,
    rows: list[tuple[str, str]],
    action_label: str | None = None,
    action_text: str | None = None,
    urgency_level: str | None = None,
    anomalies: list | None = None,
    score: float | None = None,
    confidence: str | None = None,
    top_factors: list | None = None,
) -> tuple[str, str]:
    plain_rows = "\n".join(f"- {label}: {value}" for label, value in rows)
    plain = f"{intro}\n\n{plain_rows}"
    if score is not None:
        plain += f"\n\nScore de risque : {score}/100"
    if confidence:
        plain += f"\nConfiance : {confidence}"
    if top_factors:
        plain += "\nFacteurs principaux :"
        for i, f in enumerate(top_factors[:3], 1):
            plain += f"\n  {i}. {f.get('label')} ({f.get('contribution')} pts) — {f.get('detail')}"
    if action_text:
        plain += f"\n\n{action_label or 'Action'} : {action_text}"

    body = f'<p style="margin:0 0 8px;line-height:1.6;color:#334155;">{escape(intro)}</p>'

    if score is not None and urgency_level:
        body += _score_badge(score, urgency_level)
    elif urgency_level:
        color = _urgency_color(urgency_level)
        body += f"""
        <div style="display:inline-block;margin:12px 0 4px;padding:8px 14px;border-radius:8px;background:{color};color:#fff;font-weight:700;">
          Urgence : {escape(urgency_level.upper())}
        </div>"""

    if confidence:
        body += f'<p style="color:#64748b;font-size:13px;">Confiance de l\'analyse : <strong>{escape(confidence)}</strong></p>'

    body += _info_table(rows)
    body += _factors_block(top_factors)
    body += _anomalies_block(anomalies)

    if action_label and action_text:
        body += f"""
        <div style="margin-top:20px;padding:14px 16px;border-left:4px solid #2563eb;background:#eff6ff;border-radius:6px;">
          <div style="font-weight:700;color:#1d4ed8;margin-bottom:4px;">{escape(action_label)}</div>
          <div style="color:#334155;">{escape(action_text)}</div>
        </div>"""

    return plain, _base_layout(title, body)


def render_contrat_modification_email(
    contrat_id: str,
    client: str,
    gestionnaire_id: str,
    nb_sinistres: int = 0,
    gestionnaire_nom: str | None = None,
    formule: str | None = None,
) -> tuple[str, str]:
    gest_name = gestionnaire_nom or gestionnaire_id or "Gestionnaire Assurances"
    client_name = client or "N/A"
    formule_name = formule or "Contrat Auto"

    title = f"Modification du contrat {contrat_id}"
    intro = (
        f"Bonjour,\n\n"
        f"Le gestionnaire **{gest_name}** a modifié le contrat **{formule_name}** de votre client commun **{client_name}**."
    )
    rows = [
        ("Contrat", contrat_id),
        ("Formule", formule_name),
        ("Client", client_name),
        ("Sinistres en cours", str(nb_sinistres)),
        ("Gestionnaire auteur", gest_name),
    ]
    return render_notification_email(
        title, intro, rows,
        "Action requise",
        "Vérifier l'impact sur les sinistres liés et ajuster les plafonds si nécessaire.",
    )


def render_sinistre_email(
    event: str,
    sinistre_id: str,
    contrat_id: str,
    montant: float | int,
    gestionnaire_id: str,
    statut: str | None = None,
    risk: dict | None = None,
    client_nom: str | None = None,
    gestionnaire_nom: str | None = None,
    type_sinistre: str | None = None,
) -> tuple[str, str]:
    gest_name = gestionnaire_nom or gestionnaire_id or "Gestionnaire Sinistres"
    client_name = client_nom or "Client"
    type_s = type_sinistre or "Sinistre Auto"

    title = f"{event} — sinistre {sinistre_id}"
    event_lower = (event or "").lower()
    if any(k in event_lower for k in ["nouveau", "création", "creation", "déclaration", "declaration"]):
        intro = (
            f"Bonjour,\n\n"
            f"Un nouveau sinistre **{type_s}** a été déclaré par le gestionnaire **{gest_name}** pour le client **{client_name}**."
        )
    else:
        intro = (
            f"Bonjour,\n\n"
            f"Le sinistre **{type_s}** ({sinistre_id}) du client **{client_name}** a été mis à jour par le gestionnaire **{gest_name}**."
        )

    rows = [
        ("Sinistre", sinistre_id),
        ("Contrat", contrat_id),
        ("Client", client_name),
        ("Type de sinistre", type_s),
        ("Montant déclaré", f"{montant:,.0f} DT"),
        ("Gestionnaire sinistres", gest_name),
    ]
    if statut:
        rows.append(("Statut", statut))

    risk = risk or {}
    reco = risk.get("recommendation") or {}
    return render_notification_email(
        title, intro, rows,
        reco.get("label", "Action requise"),
        reco.get("detail", "Relancer l'analyse croisée du dossier."),
        urgency_level=risk.get("urgency_level"),
        anomalies=risk.get("anomalies"),
        score=risk.get("score"),
        confidence=risk.get("confidence"),
        top_factors=risk.get("top_factors"),
    )


def render_alert_email(state: dict) -> tuple[str, str]:
    alert = state.get("alert") or {}
    contrat = state.get("contrat_data") or {}
    risk = state.get("risk_analysis") or {}
    reco = risk.get("recommendation") or alert

    title = f"Alerte dossier {state.get('contrat_id', 'N/A')}"
    intro = alert.get("explication_llm") or "Analyse de risque sinistres disponible pour ce dossier."

    rows = [
        ("Contrat", state.get("contrat_id", "N/A")),
        ("Client", contrat.get("client", "N/A")),
        ("Type evenement", state.get("event_type", "N/A")),
        ("Gestionnaire cible", "Equipe sinistres"),
    ]

    missing = state.get("missing_data") or []
    if missing:
        rows.append(("Donnees manquantes", "; ".join(missing[:3])))

    return render_notification_email(
        title,
        intro,
        rows,
        reco.get("label", "Recommandation") if isinstance(reco, dict) else "Recommandation",
        reco.get("detail") if isinstance(reco, dict) else state.get("recommendation", ""),
        urgency_level=state.get("urgency_level"),
        anomalies=state.get("anomalies"),
        score=state.get("urgency_score"),
        confidence=state.get("confidence"),
        top_factors=state.get("top_factors"),
    )
