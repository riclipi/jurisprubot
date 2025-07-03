"""
Tasks de geração de embeddings para busca semântica
"""

import logging
import numpy as np
from typing import List, Dict
import torch

from celery import Task, group
from sentence_transformers import SentenceTransformer
from ..celery_app import app
from ...database.database_manager import get_db_manager

logger = logging.getLogger(__name__)


class EmbeddingTask(Task):
    """Classe base para tasks de embedding com cache do modelo"""
    _model = None
    
    @property
    def model(self):
        if self._model is None:
            model_name = 'sentence-transformers/all-MiniLM-L6-v2'
            logger.info(f"Carregando modelo de embeddings: {model_name}")
            self._model = SentenceTransformer(model_name)
            
            # Usar GPU se disponível
            if torch.cuda.is_available():
                self._model = self._model.cuda()
                logger.info("Modelo carregado na GPU")
        
        return self._model


@app.task(base=EmbeddingTask, bind=True)
def generate_embedding(self, chunk_id: str, case_id: str):
    """
    Gera embedding para um chunk de texto
    
    Args:
        chunk_id: ID do chunk
        case_id: ID do caso
    """
    logger.info(f"Gerando embedding para chunk {chunk_id}")
    
    db = get_db_manager()
    
    try:
        # Buscar chunk
        with db.get_session() as session:
            chunk = session.query(db.TextChunk).filter_by(id=chunk_id).first()
            if not chunk:
                raise ValueError(f"Chunk {chunk_id} não encontrado")
            
            texto = chunk.chunk_text
        
        # Gerar embedding
        embedding = self.model.encode(texto, convert_to_numpy=True)
        
        # Normalizar vetor (para similaridade de cosseno)
        embedding = embedding / np.linalg.norm(embedding)
        
        # Salvar no banco
        with db.get_session() as session:
            emb = db.Embedding(
                case_id=case_id,
                chunk_id=chunk_id,
                vector=embedding.tolist(),  # Converter para lista
                model_name=self.model.get_config_dict()['_name_or_path'],
                vector_dimension=len(embedding)
            )
            session.add(emb)
        
        logger.info(f"Embedding gerado com sucesso para chunk {chunk_id}")
        
        return {
            'status': 'success',
            'chunk_id': chunk_id,
            'embedding_size': len(embedding)
        }
        
    except Exception as e:
        logger.error(f"Erro ao gerar embedding para chunk {chunk_id}: {e}")
        raise


@app.task(base=EmbeddingTask, bind=True)
def generate_batch_embeddings(self, chunk_ids: List[str], case_id: str):
    """
    Gera embeddings em lote (mais eficiente)
    
    Args:
        chunk_ids: Lista de IDs dos chunks
        case_id: ID do caso
    """
    logger.info(f"Gerando embeddings em lote para {len(chunk_ids)} chunks")
    
    db = get_db_manager()
    
    try:
        # Buscar todos os chunks
        texts = []
        with db.get_session() as session:
            for chunk_id in chunk_ids:
                chunk = session.query(db.TextChunk).filter_by(id=chunk_id).first()
                if chunk:
                    texts.append((chunk_id, chunk.chunk_text))
        
        if not texts:
            logger.warning("Nenhum chunk válido encontrado")
            return {
                'status': 'no_chunks',
                'count': 0
            }
        
        # Gerar embeddings em lote
        chunk_ids_ordered, texts_ordered = zip(*texts)
        embeddings = self.model.encode(
            list(texts_ordered),
            convert_to_numpy=True,
            batch_size=32,
            show_progress_bar=False
        )
        
        # Normalizar vetores
        embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
        
        # Salvar no banco
        saved_count = 0
        with db.get_session() as session:
            for chunk_id, embedding in zip(chunk_ids_ordered, embeddings):
                emb = db.Embedding(
                    case_id=case_id,
                    chunk_id=chunk_id,
                    vector=embedding.tolist(),
                    model_name=self.model.get_config_dict()['_name_or_path'],
                    vector_dimension=len(embedding)
                )
                session.add(emb)
                saved_count += 1
        
        logger.info(f"Gerados {saved_count} embeddings em lote")
        
        return {
            'status': 'success',
            'embeddings_created': saved_count
        }
        
    except Exception as e:
        logger.error(f"Erro ao gerar embeddings em lote: {e}")
        raise


@app.task(base=EmbeddingTask)
def generate_pending_embeddings():
    """
    Gera embeddings para chunks pendentes (executado periodicamente)
    """
    logger.info("Buscando chunks sem embeddings")
    
    db = get_db_manager()
    
    with db.get_session() as session:
        # Buscar chunks sem embeddings
        pending_chunks = session.execute("""
            SELECT tc.id, tc.document_id, d.case_id
            FROM text_chunks tc
            JOIN documents d ON tc.document_id = d.id
            LEFT JOIN embeddings e ON tc.id = e.chunk_id
            WHERE e.id IS NULL
            LIMIT 100
        """).fetchall()
    
    if not pending_chunks:
        logger.info("Nenhum chunk pendente encontrado")
        return {
            'status': 'no_pending',
            'count': 0
        }
    
    logger.info(f"Encontrados {len(pending_chunks)} chunks pendentes")
    
    # Agrupar por caso para processamento em lote
    chunks_by_case = {}
    for chunk_id, doc_id, case_id in pending_chunks:
        if case_id not in chunks_by_case:
            chunks_by_case[case_id] = []
        chunks_by_case[case_id].append(str(chunk_id))
    
    # Criar tasks em lote
    jobs = []
    for case_id, chunk_ids in chunks_by_case.items():
        if len(chunk_ids) > 5:
            # Processar em lote se tiver muitos chunks
            jobs.append(generate_batch_embeddings.s(chunk_ids, str(case_id)))
        else:
            # Processar individualmente se poucos chunks
            for chunk_id in chunk_ids:
                jobs.append(generate_embedding.s(chunk_id, str(case_id)))
    
    # Executar em paralelo
    job_group = group(jobs)
    result = job_group.apply_async()
    
    return {
        'status': 'processing',
        'chunks_count': len(pending_chunks),
        'cases_count': len(chunks_by_case),
        'group_id': result.id
    }


@app.task(base=EmbeddingTask, bind=True)
def search_similar_chunks(self, query: str, limit: int = 10, threshold: float = 0.7):
    """
    Busca chunks similares usando embeddings
    
    Args:
        query: Texto da consulta
        limit: Número máximo de resultados
        threshold: Threshold de similaridade (0-1)
    """
    logger.info(f"Buscando chunks similares para: {query[:50]}...")
    
    db = get_db_manager()
    
    try:
        # Gerar embedding da query
        query_embedding = self.model.encode(query, convert_to_numpy=True)
        query_embedding = query_embedding / np.linalg.norm(query_embedding)
        
        # Buscar embeddings no banco
        with db.get_session() as session:
            # Por enquanto, buscar todos (melhorar com pgvector)
            all_embeddings = session.query(
                db.Embedding.id,
                db.Embedding.vector,
                db.Embedding.chunk_id,
                db.Embedding.case_id
            ).limit(1000).all()
            
            if not all_embeddings:
                return {
                    'status': 'no_embeddings',
                    'results': []
                }
            
            # Calcular similaridades
            similarities = []
            for emb_id, vector, chunk_id, case_id in all_embeddings:
                vector_np = np.array(vector)
                similarity = np.dot(query_embedding, vector_np)
                
                if similarity >= threshold:
                    similarities.append({
                        'embedding_id': str(emb_id),
                        'chunk_id': str(chunk_id),
                        'case_id': str(case_id),
                        'similarity': float(similarity)
                    })
            
            # Ordenar por similaridade
            similarities.sort(key=lambda x: x['similarity'], reverse=True)
            results = similarities[:limit]
            
            # Buscar textos dos chunks
            for result in results:
                chunk = session.query(db.TextChunk).filter_by(
                    id=result['chunk_id']
                ).first()
                if chunk:
                    result['text'] = chunk.chunk_text[:200] + '...'
        
        logger.info(f"Encontrados {len(results)} chunks similares")
        
        return {
            'status': 'success',
            'query': query,
            'results': results,
            'total_found': len(similarities)
        }
        
    except Exception as e:
        logger.error(f"Erro na busca por similaridade: {e}")
        raise