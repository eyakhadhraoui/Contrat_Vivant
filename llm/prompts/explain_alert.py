def build_explain_prompt(contrat: dict, sinistres: list, anomalies: list) -> str:
    anomalies_texte = "\n".join(
        f"- {a['rule']} : {a['message']} (sévérité : {a['severity']})"
        for a in anomalies
    ) or "Aucune anomalie."

    montants = ", ".join(str(s.get("montant_declare")) for s in sinistres)

    return f"""Tu es un assistant pour les gestionnaires d'assurance.

Contrat :
- Client : {contrat.get('client')}
- Garantie maximale : {contrat.get('garantie_max')} DT
- Statut : {contrat.get('statut')}

Sinistres déclarés : {montants} DT

Anomalies détectées par le moteur de règles :
{anomalies_texte}

Explique clairement le problème détecté et propose une recommandation d'action concrète. Reste factuel, 5 lignes maximum."""