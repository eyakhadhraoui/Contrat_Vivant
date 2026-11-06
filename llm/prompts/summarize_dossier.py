"""
Prompt structure pour le resume de dossier destine au gestionnaire.
"""


def build_summary_prompt(contrat: dict, sinistres: list, anomalies: list, urgency: str) -> str:
    anomalies_desc = (
        "\n".join(f"  • [{a.get('severity', 'moyen').upper()}] {a.get('rule', 'Anomalie')}: {a.get('message', '')}" for a in anomalies)
        if anomalies else "  • Aucune anomalie critique détectée par le moteur de règles."
    )

    sinistres_details = (
        "\n".join(
            f"  • Sinistre #{s.get('id')}: {s.get('type_sinistre', s.get('type', 'Auto'))} | "
            f"Montant: {s.get('montant_declare', 0):,.2f} DT | Statut: {s.get('statut', 'en_cours')} | "
            f"Lieu: {s.get('lieu', s.get('lieu_sinistre', 'Non précisé'))} | Date: {s.get('date', s.get('date_declaration', 'N/A'))}"
            for s in sinistres
        )
        if sinistres else "  • Aucun sinistre déclaré sur ce contrat."
    )

    garantie_max = float(contrat.get('garantie_max', 0))
    total_montant_sinistres = sum(float(s.get('montant_declare', 0)) for s in sinistres)
    ratio_sinistralite = (total_montant_sinistres / garantie_max * 100) if garantie_max > 0 else 0.0

    return f"""### RÔLE & MISSION
Tu es un Expert Auditeur Senior en Assurances & Analyste de Risques.
Ta mission est d'effectuer une **Analyse Approfondie et Détaillée du Contrat d'Assurance**, incluant le diagnostic financier, la sinistralité, les risques détectés et les préconisations décisionnelles pour le gestionnaire.

### DONNÉES TECHNIQUES DU CONTRAT ET DU CLIENT
- **Identifiant du Contrat** : {contrat.get('id', 'N/A')}
- **Formule d'Assurance** : {str(contrat.get('type_contrat', contrat.get('type', 'Auto'))).capitalize()}
- **Nom du Client / Souscripteur** : {contrat.get('client') or contrat.get('client_id') or 'Client Assuré'}
- **Statut Juridique** : {contrat.get('statut', 'actif').upper()}
- **Agence Rattachée** : {contrat.get('agence_nom') or contrat.get('agence_id') or 'AG01 - Tunis Centre'}
- **Gestionnaire Référent** : {contrat.get('gestionnaire_nom') or contrat.get('gestionnaire_createur_id') or 'Sarra Khelifi'}
- **Garantie Maximale Accordée** : {garantie_max:,.2f} DT
- **Franchise Contractuelle** : {float(contrat.get('franchise', 0)):,.2f} DT
- **Structure des Primes** : Mensuelle: {float(contrat.get('prime_mensuelle', 0)):,.2f} DT | Annuelle: {float(contrat.get('prime_annuelle', 0)):,.2f} DT
- **Mode & Fréquence de Paiement** : {contrat.get('mode_paiement', 'Virement')} ({contrat.get('frequence_paiement', 'Mensuel')})
- **Période de Couverture** : {contrat.get('duree_mois', 12)} mois (Du {contrat.get('date_debut', 'N/A')} au {contrat.get('date_fin', 'N/A')})

### HISTORIQUE DE SINISTRALITÉ ({len(sinistres)} dossier(s) - Cumul Déclaré: {total_montant_sinistres:,.2f} DT - Ratio: {ratio_sinistralite:.1f}%)
{sinistres_details}

### DIAGNOSTIC DE SÉCURITÉ ET RÈGLES MÉTIER
- **Score/Niveau d'Urgence Qualifié** : {urgency.upper()}
- **Signaux et Incohérences Répertoriés** :
{anomalies_desc}

### CONSIGNES STRICTES DE RÉDACTION DU RAPPORT D'ANALYSE
Rédige un rapport analytique complet, fluide, direct et hautement professionnel structuré en 5 sections distinctes :

1. **📌 Fiche Synthétique & Cadre Contractuel** : Analyse du profil client, du type de souscription et du niveau de couverture.
2. **📊 Bilan Financier et Sinistralité** : Analyse détaillée de la sinistralité cumulée par rapport à la garantie max ({ratio_sinistralite:.1f}% consommés), comportement de paiement et fréquence des déclarations.
3. **⚠️ Évaluation Approfondie des Risques** : Explication claire et argumentée des anomalies détectées, du niveau d'urgence ({urgency.upper()}) et des signaux de sur-sinistralité ou de fraude éventuels.
4. **💡 Préconisations & Plan d'Action Stratégique** : Mesures concrètes recommandées au gestionnaire (ex: réajustement des primes, révision des franchises, blocage conservatoire, contrôle des pièces justificatives).
5. **✋ Procédure de Validation Humaine (HITL)** : Explication des 3 choix offerts au gestionnaire (Valider & Appliquer les recommandations, Rejeter l'alerte, ou Différer la décision).

Rédige en Markdown clair, élégant et riche avec puces et mise en valeur des termes clés.
"""
