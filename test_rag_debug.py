from agent_tools.rag_tool import search_procedures

question = "Quelles sont les données obligatoires pour ouvrir un contrat d'assurance?"
resultat = search_procedures(question)
print('=== CONTEXTE BRUT RETROUVE PAR LE RAG ===')
print(resultat)
