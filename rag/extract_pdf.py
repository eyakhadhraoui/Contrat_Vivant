import os
from pypdf import PdfReader

def extraire_texte_pdf(chemin_pdf):
    reader = PdfReader(chemin_pdf)
    texte_complet = ''
    for page in reader.pages:
        texte_complet += page.extract_text() + '\n'
    return texte_complet

def decouper_en_chunks(texte, taille_chunk=150, chevauchement=30):
    mots = texte.split()
    chunks = []
    i = 0
    while i < len(mots):
        chunk = ' '.join(mots[i:i + taille_chunk])
        chunks.append(chunk)
        i += taille_chunk - chevauchement
    return chunks

def extraire_tous_les_documents(dossier='rag/documents'):
    tous_chunks = []
    for filename in os.listdir(dossier):
        chemin = os.path.join(dossier, filename)
        if filename.endswith('.pdf'):
            texte = extraire_texte_pdf(chemin)
        elif filename.endswith('.txt'):
            with open(chemin, encoding='utf-8-sig') as f:
                texte = f.read()
        else:
            continue
        chunks = decouper_en_chunks(texte)
        for chunk in chunks:
            tous_chunks.append({'source': filename, 'texte': chunk})
    return tous_chunks
