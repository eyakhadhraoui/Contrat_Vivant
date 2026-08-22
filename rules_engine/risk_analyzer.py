"""
Moteur d'analyse de risque sinistres — score 0-100, alerte contextualisee.
"""

from __future__ import annotations

from datetime import datetime

from config.constants import (
    ANCIENNETE_FRAUDE_JOURS,
    DELAI_ESPACE_JOURS,
    DELAI_RAPPROCHE_JOURS,
    RISK_WEIGHTS,
    SEVERITY_CRITIQUE,
    SEVERITY_ELEVE,
    SEVERITY_FAIBLE,
    SEVERITY_MOYEN,
    URGENCY_THRESHOLDS,
)
from tools.risk_data_loader import _parse_date, enrich_contrat_context


def _score_to_level(score: float) -> str:
    if score >= URGENCY_THRESHOLDS['critique']:
        return SEVERITY_CRITIQUE
    if score >= URGENCY_THRESHOLDS['eleve']:
        return SEVERITY_ELEVE
    if score >= URGENCY_THRESHOLDS['moyen']:
        return SEVERITY_MOYEN
    return SEVERITY_FAIBLE


def _confidence(missing: list) -> str:
    n = len(missing)
    if n == 0:
        return 'haute'
    if n <= 2:
        return 'moyenne'
    return 'faible'


def _score_recurrence(sinistres: list) -> tuple[float, str]:
    n = len(sinistres)
    if n == 0:
        return 0.0, 'Aucun sinistre declare sur le contrat.'
    if n == 1:
        return 15.0, 'Un seul sinistre isole — correlation faible, pas de recurrence.'

    causes = [s.get('cause_declaree') or s.get('type_sinistre') or s.get('type') or '' for s in sinistres]
    causes_norm = [c.strip().lower() for c in causes if c]
    same_cause = len(set(causes_norm)) == 1 and len(causes_norm) > 1

    base = min(100.0, 35.0 + (n - 1) * 22.0)
    if same_cause:
        base = min(100.0, base + 20.0)
        detail = f'{n} sinistres avec la meme cause ({causes_norm[0]}) — signal fort de recurrence.'
    else:
        detail = f'{n} sinistres aux causes differentes — correlation moderee, malchance possible.'

    return base, detail


def _score_delai(sinistres: list) -> tuple[float, str]:
    if len(sinistres) < 2:
        return 20.0, 'Delai inter-sinistres non applicable (moins de 2 sinistres).'

    dates = sorted(d for s in sinistres if (d := _parse_date(s.get('date') or s.get('date_declaration'))))
    if len(dates) < 2:
        return 40.0, 'Donnees manquantes : dates sinistres incompletes pour calculer les delais.'

    gaps = [(dates[i + 1] - dates[i]).days for i in range(len(dates) - 1)]
    min_gap = min(gaps)

    if min_gap < DELAI_RAPPROCHE_JOURS:
        return min(100.0, 85.0 + (DELAI_RAPPROCHE_JOURS - min_gap) / 10), (
            f'Sinistres rapproches ({min_gap} jours entre deux declarations) — signal fort.'
        )
    if min_gap < DELAI_ESPACE_JOURS:
        return 45.0, f'Delai intermediaire ({min_gap} jours) — surveillance recommandee.'
    return 15.0, f'Sinistres espaces ({min_gap} jours) — signal faible.'


def _score_montant(contrat: dict, sinistres: list, benchmark: dict) -> tuple[float, str]:
    garantie = float(contrat.get('garantie_max') or 0)
    montants = [float(s.get('montant_declare') or 0) for s in sinistres]
    total = sum(montants)

    if not sinistres or garantie <= 0:
        return 10.0, 'Montants ou plafond indisponibles — score neutre.'

    ratio_plafond = total / garantie
    score = min(100.0, ratio_plafond * 80.0)

    croissant = len(montants) >= 2 and montants == sorted(montants) and montants[-1] > montants[0]
    if croissant:
        score = min(100.0, score + 15.0)

    moy_portefeuille = benchmark.get('moyenne_sinistres_par_contrat', 1)
    outlier = len(sinistres) > moy_portefeuille * 2
    if outlier:
        score = min(100.0, score + 10.0)

    detail = (
        f'Montant cumule {total:,.0f} DT vs plafond {garantie:,.0f} DT '
        f'({ratio_plafond * 100:.0f}%). '
    )
    if croissant:
        detail += 'Montants croissants detectes. '
    if outlier:
        detail += f'Outlier portefeuille (moyenne {moy_portefeuille} sinistres/contrat).'

    return score, detail.strip()


def _score_anciennete(contrat: dict, sinistres: list, missing: list) -> tuple[float, str]:
    souscription = _parse_date(contrat.get('date_souscription') or contrat.get('date_creation'))
    if not souscription:
        missing.append('date_souscription')
        return 50.0, 'Donnee manquante : date_souscription — score prudent applique.'

    first_dates = [_parse_date(s.get('date') or s.get('date_declaration')) for s in sinistres]
    first_dates = [d for d in first_dates if d]
    if not first_dates:
        return 10.0, 'Aucun sinistre — anciennete non significative.'

    first = min(first_dates)
    jours = (first - souscription).days

    if jours < 0:
        return 30.0, 'Sinistre declare avant la souscription enregistree — verification requise.'
    if jours <= ANCIENNETE_FRAUDE_JOURS:
        return min(100.0, 90.0 - jours / 3), (
            f'Premier sinistre {jours} jours apres souscription — fraude potentielle a verifier.'
        )
    if jours <= 365:
        return 40.0, f'Premier sinistre a {jours} jours — vigilance moderee.'
    return 10.0, f'Contrat mature ({jours} jours avant premier sinistre) — signal faible.'


def _score_patterns(contrat: dict, sinistres: list) -> tuple[float, str, list]:
    flags = []
    score = 0.0

    types = [s.get('type_sinistre') or s.get('type') or '' for s in sinistres]
    if len(sinistres) >= 2 and len(set(t.strip().lower() for t in types if t)) == 1:
        score += 35.0
        flags.append('circonstances_similaires')

    derniere_modif = _parse_date(contrat.get('date_derniere_modif'))
    for s in sinistres:
        d = _parse_date(s.get('date') or s.get('date_declaration'))
        if derniere_modif and d and abs((d - derniere_modif).days) <= 30:
            score += 30.0
            flags.append('sinistre_apres_avenant')
            break

    if len(sinistres) >= 3:
        score += 20.0
        flags.append('frequence_elevee')

    score = min(100.0, score)
    if flags:
        detail = 'Patterns suspects : ' + ', '.join(flags) + ' — fraude a verifier (sans accusation).'
    else:
        detail = 'Aucun pattern suspect detecte.'
    return score, detail, flags


def _graduated_recommendation(score: float, flags: list) -> dict:
    if score >= URGENCY_THRESHOLDS['critique']:
        return {
            'action': 'escalader_anti_fraude_resiliation',
            'label': 'Escalader vers l\'unite anti-fraude',
            'detail': (
                'Score critique. Escalade anti-fraude recommandee et evaluation de resiliation '
                'ou exclusion a envisager. Decision finale humaine requise.'
            ),
        }
    if score >= URGENCY_THRESHOLDS['eleve']:
        return {
            'action': 'escalader_anti_fraude',
            'label': 'Escalader vers l\'unite anti-fraude',
            'detail': (
                'Signaux de risque eleves. Transmission au referent anti-fraude et controle renforce '
                'des pieces justificatives.'
            ),
        }
    if score >= URGENCY_THRESHOLDS['moyen']:
        return {
            'action': 'reviser_contrat',
            'label': 'Reviser le contrat',
            'detail': (
                'Envisager revision contractuelle : franchise, surprime ou exclusion specifique. '
                'Documenter la decision gestionnaire.'
            ),
        }
    return {
        'action': 'surveiller',
        'label': 'Surveiller',
        'detail': 'Revue planifiee a 90 jours. Aucune action immediate requise.',
    }


def _build_anomalies(factors: list, flags: list) -> list:
    anomalies = []
    for factor in factors:
        if factor['subscore'] >= 60:
            anomalies.append({
                'rule': factor['key'],
                'message': factor['detail'],
                'severity': SEVERITY_ELEVE if factor['subscore'] >= 80 else SEVERITY_MOYEN,
            })
    if 'sinistre_apres_avenant' in flags:
        anomalies.append({
            'rule': 'pattern_post_avenant',
            'message': 'Sinistre declare peu apres modification contractuelle — a verifier.',
            'severity': SEVERITY_ELEVE,
        })
    return anomalies


def analyze_risk(contrat: dict, sinistres: list) -> dict:
    """Analyse complete d'un dossier sinistres. Retourne score, alerte et anomalies."""
    context = enrich_contrat_context(contrat, sinistres)
    missing = list(context['missing_data'])
    benchmark = context['benchmark']

    subscores = {
        'recurrence': _score_recurrence(sinistres),
        'delai': _score_delai(sinistres),
        'montant_plafond': _score_montant(contrat, sinistres, benchmark),
        'anciennete': _score_anciennete(contrat, sinistres, missing),
    }
    pattern_score, pattern_detail, flags = _score_patterns(contrat, sinistres)
    subscores['pattern_suspect'] = (pattern_score, pattern_detail)

    factors = []
    total = 0.0
    for key, weight in RISK_WEIGHTS.items():
        subscore, detail = subscores[key]
        contribution = round(subscore * weight, 1)
        total += contribution
        factors.append({
            'key': key,
            'label': {
                'recurrence': 'Recurrence',
                'delai': 'Delai inter-sinistres',
                'montant_plafond': 'Montant vs plafond',
                'anciennete': 'Anciennete contrat',
                'pattern_suspect': 'Patterns suspects',
            }[key],
            'subscore': round(subscore, 1),
            'weight_pct': int(weight * 100),
            'contribution': contribution,
            'detail': detail,
        })

    factors.sort(key=lambda f: f['contribution'], reverse=True)
    score = round(min(100.0, total), 1)
    level = _score_to_level(score)
    confidence = _confidence(sorted(set(missing)))
    recommendation = _graduated_recommendation(score, flags)
    top_factors = factors[:3]
    anomalies = _build_anomalies(factors, flags)

    missing_labels = [f'donnee manquante : {m}' for m in sorted(set(missing))]

    alert_card = {
        'score': score,
        'urgency_level': level,
        'confidence': confidence,
        'top_factors': top_factors,
        'recommendation': recommendation,
        'missing_data': missing_labels,
        'data_sources': context['data_sources'],
        'gestionnaire_cible': 'sinistres',
        'flags': flags,
        'disclaimer': (
            'Analyse automatique — correlation != causalite. '
            'Fraude signalee comme "a verifier", jamais affirmee. Decision finale humaine.'
        ),
    }

    return {
        'score': score,
        'urgency_level': level,
        'urgency_score': score,
        'confidence': confidence,
        'top_factors': top_factors,
        'urgency_breakdown': factors,
        'dominant_rule': top_factors[0]['key'] if top_factors else None,
        'recommendation': recommendation,
        'anomalies': anomalies,
        'missing_data': missing_labels,
        'alert_card': alert_card,
        'context': context,
    }
