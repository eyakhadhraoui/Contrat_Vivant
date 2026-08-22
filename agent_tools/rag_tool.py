import os
import io
import json
import logging
from datetime import datetime
from database.db_connection import get_connection, ensure_rag_and_chat_tables

logger = logging.getLogger(__name__)

# Assurer l'existence des tables RAG
ensure_rag_and_chat_tables()

_model = None
_index = None
_chunks_data = None
_DOCS_DIR = 'data/rag_documents'
_dynamic_chunks_file = 'data/rag_documents/dynamic_chunks.json'
_dynamic_chunks = []


def _load_dynamic_chunks():
    """Charge les chunks dynamiques depuis le fichier JSON et synchronise avec MySQL."""
    global _dynamic_chunks
    os.makedirs(_DOCS_DIR, exist_ok=True)
    os.makedirs('rag/faiss_index', exist_ok=True)

    loaded = []
    # 1. Chargement depuis le fichier local
    if os.path.exists(_dynamic_chunks_file):
        try:
            with open(_dynamic_chunks_file, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
        except Exception:
            loaded = []
    elif os.path.exists('rag/faiss_index/dynamic_chunks.json'):
        try:
            with open('rag/faiss_index/dynamic_chunks.json', 'r', encoding='utf-8') as f:
                loaded = json.load(f)
        except Exception:
            loaded = []

    # 2. Synchronisation / Restauration depuis MySQL si des documents existent en base
    try:
        conn = get_connection()
        if conn:
            cur = conn.cursor(dictionary=True)
            cur.execute("SELECT id, filename, content_text FROM rag_documents")
            db_docs = cur.fetchall()
            cur.close()
            conn.close()

            existing_filenames = {c.get('filename') for c in loaded}
            for d in db_docs:
                fname = d.get('filename')
                if fname and fname not in existing_filenames:
                    content = d.get('content_text') or ''
                    if content:
                        chunks = _split_text_into_chunks(content)
                        for i, ch in enumerate(chunks):
                            loaded.append({
                                "doc_id": d.get('id'),
                                "filename": fname,
                                "chunk_id": f"{fname}_{i}",
                                "texte": f"Document: {fname}\n{ch}"
                            })
                        existing_filenames.add(fname)
    except Exception as e:
        logger.warning(f"Note: Synchronisation DB RAG: {e}")

    _dynamic_chunks = loaded
    _save_dynamic_chunks()


def _save_dynamic_chunks():
    """Sauvegarde les chunks sur le disque persistant."""
    global _dynamic_chunks
    os.makedirs(_DOCS_DIR, exist_ok=True)
    try:
        with open(_dynamic_chunks_file, 'w', encoding='utf-8') as f:
            json.dump(_dynamic_chunks, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Erreur sauvegarde dynamic chunks: {e}")


def _split_text_into_chunks(texte: str, max_words: int = 150, overlap: int = 30) -> list:
    """Découpe un texte en paragraphes ou fenêtres de mots glissantes."""
    if not texte:
        return []
    
    # Découpage prioritaire par paragraphes
    raw_paras = [p.strip() for p in texte.split('\n\n') if p.strip()]
    chunks = []
    
    for p in raw_paras:
        words = p.split()
        if len(words) <= max_words:
            chunks.append(p)
        else:
            i = 0
            while i < len(words):
                chunk = ' '.join(words[i:i + max_words])
                chunks.append(chunk)
                i += max_words - overlap

    return chunks if chunks else [texte.strip()]


def _get_rag_resources():
    """Initialise le modèle d'embedding et l'index FAISS de base s'ils sont disponibles."""
    global _model, _index, _chunks_data
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _model = SentenceTransformer('all-MiniLM-L6-v2', local_files_only=True)
        except Exception:
            try:
                from sentence_transformers import SentenceTransformer
                _model = SentenceTransformer('all-MiniLM-L6-v2')
            except Exception:
                _model = None

    if _index is None:
        try:
            import faiss
            import pickle
            if os.path.exists('rag/faiss_index/index.faiss') and os.path.exists('rag/faiss_index/chunks.pkl'):
                _index = faiss.read_index('rag/faiss_index/index.faiss')
                with open('rag/faiss_index/chunks.pkl', 'rb') as f:
                    _chunks_data = pickle.load(f)
        except Exception:
            pass

    return _model, _index, _chunks_data


def extract_text_from_bytes(file_bytes: bytes, filename: str) -> str:
    """Extrait le texte d'un fichier PDF, TXT ou JSON."""
    fname_lower = filename.lower()
    
    if fname_lower.endswith('.pdf'):
        try:
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(file_bytes))
            text = ""
            for page_idx, page in enumerate(reader.pages):
                page_text = page.extract_text() or ""
                if page_text:
                    text += f"\n--- Page {page_idx + 1} ---\n" + page_text
            return text.strip()
        except Exception as e:
            logger.error(f"Erreur extraction PDF {filename}: {e}")
            raise ValueError(f"Impossible de lire le fichier PDF '{filename}' : {e}")
            
    elif fname_lower.endswith('.txt') or fname_lower.endswith('.md') or fname_lower.endswith('.json'):
        try:
            return file_bytes.decode('utf-8')
        except UnicodeDecodeError:
            return file_bytes.decode('latin-1', errors='ignore')
    else:
        # Tentative texte générique
        try:
            return file_bytes.decode('utf-8', errors='ignore')
        except Exception as e:
            raise ValueError(f"Format de fichier non pris en charge pour '{filename}'. Formats acceptés: PDF, TXT, MD, JSON.")


def ingest_document(filename: str, file_bytes_or_text, uploaded_by: str = 'system') -> dict:
    """
    Ingère un document (PDF / texte) dans MySQL et met à jour l'index RAG persistant.
    Persiste même après déconnexion ou redémarrage du serveur.
    """
    global _dynamic_chunks
    os.makedirs(_DOCS_DIR, exist_ok=True)

    if isinstance(file_bytes_or_text, bytes):
        file_bytes = file_bytes_or_text
        text_content = extract_text_from_bytes(file_bytes, filename)
    else:
        text_content = str(file_bytes_or_text)
        file_bytes = text_content.encode('utf-8')

    if not text_content or not text_content.strip():
        raise ValueError(f"Le document '{filename}' ne contient aucun texte extractible.")

    file_size = len(file_bytes)
    chunks = _split_text_into_chunks(text_content)
    chunks_count = len(chunks)

    # 1. Sauvegarde locale du fichier physique
    save_path = os.path.join(_DOCS_DIR, filename)
    try:
        with open(save_path, 'wb') as f:
            f.write(file_bytes)
    except Exception as e:
        logger.warning(f"Erreur sauvegarde fichier local: {e}")

    # 2. Enregistrement en base MySQL
    doc_id = None
    try:
        conn = get_connection()
        if conn:
            cur = conn.cursor()
            sql = """
                INSERT INTO rag_documents (filename, file_type, file_size, chunks_count, content_text, uploaded_by, uploaded_at)
                VALUES (%s, %s, %s, %s, %s, %s, NOW())
            """
            file_ext = filename.split('.')[-1].lower() if '.' in filename else 'txt'
            cur.execute(sql, (filename, file_ext, file_size, chunks_count, text_content, uploaded_by))
            conn.commit()
            doc_id = cur.lastrowid
            cur.close()
            conn.close()
    except Exception as e:
        logger.error(f"Erreur enregistrement MySQL rag_documents: {e}")

    # 3. Ajout des chunks dans l'index mémoire
    # Supprimer les anciens chunks du même fichier si ré-uploadé
    _dynamic_chunks = [c for c in _dynamic_chunks if c.get('filename') != filename]

    for i, ch in enumerate(chunks):
        _dynamic_chunks.append({
            "doc_id": doc_id,
            "filename": filename,
            "chunk_id": f"{filename}_{i}",
            "texte": f"📄 [Source: {filename} - Section {i + 1}]\n{ch}"
        })

    # Sauvegarde sur disque
    _save_dynamic_chunks()

    return {
        "status": "success",
        "doc_id": doc_id,
        "filename": filename,
        "file_size": file_size,
        "chunks_added": chunks_count,
        "total_documents": len(get_all_documents()),
        "total_chunks": len(_dynamic_chunks),
        "message": f"Document '{filename}' indexé avec succès dans le RAG ({chunks_count} sections extractibles)."
    }


def get_all_documents() -> list:
    """Retourne la liste complète des documents indexés dans la base RAG."""
    docs = []
    try:
        conn = get_connection()
        if conn:
            cur = conn.cursor(dictionary=True)
            cur.execute("""
                SELECT id, filename, file_type, file_size, chunks_count, uploaded_by, uploaded_at
                FROM rag_documents
                ORDER BY uploaded_at DESC
            """)
            rows = cur.fetchall()
            cur.close()
            conn.close()
            for r in rows:
                dt = r.get('uploaded_at')
                docs.append({
                    "id": r.get('id'),
                    "filename": r.get('filename'),
                    "file_type": r.get('file_type', 'pdf'),
                    "file_size": r.get('file_size', 0),
                    "chunks_count": r.get('chunks_count', 0),
                    "uploaded_by": r.get('uploaded_by', 'system'),
                    "uploaded_at": dt.strftime('%d/%m/%Y %H:%M') if isinstance(dt, datetime) else str(dt)
                })
            return docs
    except Exception as e:
        logger.warning(f"Erreur lecture MySQL rag_documents: {e}")

    # Fallback depuis les chunks locaux si MySQL indisponible
    seen = {}
    for c in _dynamic_chunks:
        fn = c.get('filename', 'Document')
        if fn not in seen:
            seen[fn] = {"filename": fn, "chunks_count": 1}
        else:
            seen[fn]["chunks_count"] += 1

    return [{"id": idx + 1, "filename": k, "chunks_count": v["chunks_count"], "uploaded_at": "Enregistré"} for idx, (k, v) in enumerate(seen.items())]


def delete_document(doc_id_or_filename) -> bool:
    """Supprime un document de MySQL, du système de fichiers et réindexe le RAG."""
    global _dynamic_chunks
    filename_to_remove = str(doc_id_or_filename)

    try:
        conn = get_connection()
        if conn:
            cur = conn.cursor()
            if str(doc_id_or_filename).isdigit():
                cur.execute("SELECT filename FROM rag_documents WHERE id = %s", (int(doc_id_or_filename),))
                row = cur.fetchone()
                if row:
                    filename_to_remove = row[0]
                cur.execute("DELETE FROM rag_documents WHERE id = %s", (int(doc_id_or_filename),))
            else:
                cur.execute("DELETE FROM rag_documents WHERE filename = %s", (filename_to_remove,))
            conn.commit()
            cur.close()
            conn.close()
    except Exception as e:
        logger.error(f"Erreur suppression document MySQL: {e}")

    # Suppression du fichier physique
    file_path = os.path.join(_DOCS_DIR, filename_to_remove)
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception:
            pass

    # Suppression des chunks
    _dynamic_chunks = [c for c in _dynamic_chunks if c.get('filename') != filename_to_remove]
    _save_dynamic_chunks()
    return True


def search_procedures(query: str, top_k: int = 4) -> tuple[str, list]:
    """
    Recherche les sections les plus pertinentes dans tous les documents RAG enregistrés.
    Retourne (texte_contexte_formatte, liste_des_sources).
    """
    if not query or not query.strip():
        return "", []

    resultats = []
    sources = []
    q_words = [w.lower() for w in query.split() if len(w) > 2]

    # 1. Score de pertinence sur les chunks dynamiques ingérés
    scored_chunks = []
    for chunk in _dynamic_chunks:
        txt = chunk.get('texte', '')
        txt_lower = txt.lower()
        filename = chunk.get('filename', 'Document')

        score = 0
        for w in q_words:
            if w in txt_lower:
                score += 2
        # Bonus si correspondance exacte de phrase
        if query.lower() in txt_lower:
            score += 5

        if score > 0 or not q_words:
            scored_chunks.append((score, txt, filename))

    scored_chunks.sort(key=lambda x: x[0], reverse=True)

    for _, txt, fname in scored_chunks[:top_k]:
        resultats.append(txt)
        if fname not in sources:
            sources.append(fname)

    # 2. Recherche vectorielle FAISS complémentaire
    model, index, chunks_data = _get_rag_resources()
    if model and index and chunks_data:
        try:
            vector = model.encode([query])
            distances, indices = index.search(vector, k=min(top_k, len(chunks_data)))
            for idx in indices[0]:
                if idx < len(chunks_data):
                    chunk = chunks_data[idx]
                    t = chunk.get('texte', '')
                    src = chunk.get('source', 'Base FAISS')
                    if t and t not in resultats:
                        resultats.append(t)
                        if src not in sources:
                            sources.append(src)
        except Exception as e:
            logger.warning(f"Erreur recherche FAISS: {e}")

    context_str = '\n\n---\n\n'.join(resultats) if resultats else 'Aucune procédure correspondante trouvée.'
    return context_str, sources


# Initialisation au chargement du module
_load_dynamic_chunks()
