"""Charge les donnees complementaires pour l'analyse de risque."""

from __future__ import annotations

import json
from datetime import datetime, date
from pathlib import Path

from database.db_connection import get_connection


def _parse_date(value) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime.combine(value, datetime.min.time())
    text = str(value).strip()
    if text.endswith('Z'):
        text = text[:-1] + '+00:00'
    for fmt in ('%Y-%m-%dT%H:%M:%S', '%Y-%m-%d'):
        try:
            return datetime.strptime(text[:19], fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def _load_json_fallback(filename: str) -> list:
    path = Path('data') / filename
    if not path.exists():
        return []
    try:
        with path.open(encoding='utf-8') as fh:
            return json.load(fh)
    except Exception:
        return []


def load_portfolio_benchmark(contrat: dict) -> dict:
    """Calcule la moyenne sinistres/an par type de contrat dans le portefeuille."""
    contrat_type = contrat.get('type_contrat') or contrat.get('type') or 'auto'
    agence_id = contrat.get('agence_id')
    missing = []

    try:
        conn = get_connection()
        if conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT COUNT(DISTINCT s.id) AS nb_sinistres,
                       COUNT(DISTINCT c.id) AS nb_contrats
                FROM contrats c
                LEFT JOIN sinistres s ON s.contrat_id = c.id
                WHERE c.agence_id = %s OR %s IS NULL
                """,
                (agence_id, agence_id),
            )
            row = cur.fetchone()
            cur.close()
            conn.close()
            if row and row[1]:
                avg_per_contract = row[0] / row[1]
                return {
                    'moyenne_sinistres_par_contrat': round(avg_per_contract, 2),
                    'type_contrat': contrat_type,
                    'source': 'mysql',
                    'missing_data': missing,
                }
    except Exception:
        pass

    contrats = _load_json_fallback('contrats.json')
    sinistres = _load_json_fallback('sinistres.json')
    nb_contrats = max(len(contrats), 1)
    avg = len(sinistres) / nb_contrats
    if not contrats and not sinistres:
        missing.append('benchmark_portefeuille')
    return {
        'moyenne_sinistres_par_contrat': round(avg, 2),
        'type_contrat': contrat_type,
        'source': 'json_fallback',
        'missing_data': missing,
    }


def load_client_history(contrat: dict) -> dict:
    """Historique global client : autres contrats et sinistres."""
    client_id = contrat.get('client_id')
    client_name = contrat.get('client')
    missing = []
    autres_contrats = []
    autres_sinistres = []

    if not client_id and not client_name:
        missing.append('historique_client_global')
        return {
            'autres_contrats': [],
            'autres_sinistres': [],
            'nb_contrats_client': 0,
            'nb_sinistres_client': 0,
            'missing_data': missing,
        }

    try:
        conn = get_connection()
        if conn:
            cur = conn.cursor()
            if client_id:
                cur.execute(
                    "SELECT id, garantie_max, statut FROM contrats WHERE client_id = %s",
                    (client_id,),
                )
            else:
                cur.execute(
                    """
                    SELECT c.id, c.garantie_max, c.statut
                    FROM contrats c
                    LEFT JOIN clients cl ON c.client_id = cl.id
                    WHERE CONCAT(cl.prenom, ' ', cl.nom) = %s OR CONCAT(cl.nom, ' ', cl.prenom) = %s
                    """,
                    (client_name, client_name),
                )
            rows = cur.fetchall()
            autres_contrats = [{'id': r[0], 'garantie_max': r[1], 'statut': r[2]} for r in rows]
            if autres_contrats:
                ids = [c['id'] for c in autres_contrats]
                placeholders = ','.join(['%s'] * len(ids))
                cur.execute(
                    f"SELECT id, contrat_id, montant_declare, date_declaration FROM sinistres WHERE contrat_id IN ({placeholders})",
                    ids,
                )
                autres_sinistres = [
                    {'id': r[0], 'contrat_id': r[1], 'montant_declare': r[2], 'date': r[3]}
                    for r in cur.fetchall()
                ]
            cur.close()
            conn.close()
            return {
                'autres_contrats': autres_contrats,
                'autres_sinistres': autres_sinistres,
                'nb_contrats_client': len(autres_contrats),
                'nb_sinistres_client': len(autres_sinistres),
                'missing_data': missing,
            }
    except Exception:
        pass

    contrats = _load_json_fallback('contrats.json')
    sinistres = _load_json_fallback('sinistres.json')
    if client_name:
        autres_contrats = [c for c in contrats if c.get('client') == client_name]
    ids = {c['id'] for c in autres_contrats}
    autres_sinistres = [s for s in sinistres if s.get('contrat_id') in ids]
    if not autres_contrats:
        missing.append('historique_client_global')

    return {
        'autres_contrats': autres_contrats,
        'autres_sinistres': autres_sinistres,
        'nb_contrats_client': len(autres_contrats),
        'nb_sinistres_client': len(autres_sinistres),
        'missing_data': missing,
    }


def enrich_contrat_context(contrat: dict, sinistres: list) -> dict:
    """Assemble le contexte complet pour l'analyse de risque."""
    missing = []

    date_souscription = contrat.get('date_souscription') or contrat.get('date_creation')
    if not date_souscription:
        missing.append('date_souscription')

    primes_payees = contrat.get('primes_payees')
    if primes_payees is None:
        missing.append('ratio_primes_sinistres')

    cause_fields = [s.get('cause_declaree') or s.get('type_sinistre') or s.get('type') for s in sinistres]
    if sinistres and all(not c for c in cause_fields):
        missing.append('cause_declaree')

    benchmark = load_portfolio_benchmark(contrat)
    client_history = load_client_history(contrat)
    missing.extend(benchmark.get('missing_data', []))
    missing.extend(client_history.get('missing_data', []))

    montant_sinistre = sum(float(s.get('montant_declare') or 0) for s in sinistres)
    ratio_primes = None
    if primes_payees and float(primes_payees) > 0:
        ratio_primes = round(montant_sinistre / float(primes_payees), 2)

    return {
        'contrat': contrat,
        'sinistres': sinistres,
        'date_souscription': date_souscription,
        'primes_payees': primes_payees,
        'ratio_primes_sinistres': ratio_primes,
        'benchmark': benchmark,
        'client_history': client_history,
        'missing_data': sorted(set(missing)),
        'data_sources': {
            'contrat': 'mysql' if contrat.get('id') else 'unknown',
            'sinistres': f"{len(sinistres)} enregistrement(s)",
            'benchmark': benchmark.get('source'),
            'client_history': 'mysql' if client_history.get('nb_contrats_client') else 'json_fallback',
        },
    }
