import faiss
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer
from rag.extract_pdf import extraire_tous_les_documents

print('Extraction des documents...')
chunks_data = extraire_tous_les_documents('rag/documents')
print(len(chunks_data), 'chunks extraits.')

print('Chargement du modele embedding...')
model = SentenceTransformer('all-MiniLM-L6-v2')

textes = [c['texte'] for c in chunks_data]
vectors = model.encode(textes, show_progress_bar=True)

index = faiss.IndexFlatL2(vectors.shape[1])
index.add(np.array(vectors).astype('float32'))

faiss.write_index(index, 'rag/faiss_index/index.faiss')
with open('rag/faiss_index/chunks.pkl', 'wb') as f:
    pickle.dump(chunks_data, f)

print('Index construit avec succes.')
