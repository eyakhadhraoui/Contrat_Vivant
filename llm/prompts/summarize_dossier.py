"""
Prompt structure pour le resume de dossier destine au gestionnaire.
"""


def build_summary_prompt(contrat: dict, sinistres: list, anomalies: list, urgency: str) -> str:
    anomalies_desc = (
        "\n".join(f"- [{a.get('severity', 'moyen').upper()}] {a.get('rule', 'Anomalie')}: {a.get('message', '')}" for a in anomalies)
        if anomalies else "- Aucune anomalie critique détectée"
    )

    sinistres_details = (
        "\n".join(f"- Sinistre #{s.get('id')}: {s.get('type_sinistre', s.get('type', 'Auto'))} (Montant: {s.get('montant_declare', 0)} DT, Statut: {s.get('statut', 'en_cours')}, Date: {s.get('date', s.get('date_declaration', 'N/A'))})" for s in sinistres)
        if sinistres else "- Aucun sinistre déclaré"
    )

    total_montant_sinistres = sum(float(s.get('montant_declare', 0)) for s in sinistres)

    return f"""### RÔLE & MISSION
Tu es un Expert Analytique Senior en Assurance (Auto, Habitation, Vie, Santé).
Rédige une synthèse d'analyse de dossier d'assurance claire, exhaustive, structurée et directement actionnable pour le gestionnaire d'assurance.

### DONNÉES DU DOSSIER CLIENT
- Client : {contrat.get('client') or contrat.get('client_id') or 'Client Assuré'}
- Contrat ID : {contrat.get('id', 'N/A')} (Formule: {str(contrat.get('type_contrat', contrat.get('type', 'Auto'))).capitalize()})
- Statut du contrat : {contrat.get('statut', 'actif').upper()}
- Agence rattachée : {contrat.get('agence_nom') or contrat.get('agence_id') or 'Agence Tunis Centre'}
- Gestionnaire créateur : {contrat.get('gestionnaire_nom') or contrat.get('gestionnaire_createur_id') or 'Sarra Khelifi'}
- Garantie Maximale : {contrat.get('garantie_max', 0)} DT | Franchise : {contrat.get('franchise', 0)} DT
- Primes : Mensuelle ({contrat.get('prime_mensuelle', 0)} DT) / Annuelle ({contrat.get('prime_annuelle', 0)} DT)
- Durée : {contrat.get('duree_mois', 12)} mois (Du {contrat.get('date_debut', 'N/A')} au {contrat.get('date_fin', 'N/A')})

### SINISTRES RATTACHÉS ({len(sinistres)} dossier(s), Total Déclaré: {total_montant_sinistres:,.0f} DT)
{sinistres_details}

### ANOMALIES ET NIVEAU DE RISQUE
- Niveau d'urgence calculé : {urgency.upper()}
{anomalies_desc}

### CONSIGNES DE RÉDACTION DE LA SYNTHÈSE
Rédige le résumé structuré en 4 sections clés :
1. **📌 Synthèse Générale du Dossier** : État du contrat, garanties souscrites et sinistralité globale.
2. **⚠️ Signaux et Anomalies Détectés** : Analyse détaillée du risque et des incohérences éventuelles.
3. **💡 Recommandation Actionnable** : Décision conseillée au gestionnaire (ex: validation des pièces, révision du plafond, ou ajustement de la prime).
4. **✋ Validation Manuelle Recommandée (HITL)** : Rappel des 3 options d'action ouvertes au gestionnaire (Valider & Appliquer les modifications, Rejeter l'alerte, ou choisir Pas maintenant pour conserver le rappel).

Format : Markdown structuré avec titres en gras et puces claires. Reste précis, professionnel et sans omissions.
"""
