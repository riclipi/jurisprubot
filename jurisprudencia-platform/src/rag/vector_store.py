"""
Vector Store com pgvector para busca semântica
Substitui ChromaDB por solução de produção
"""

import logging
import numpy as np
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.extensions import register_adapter, AsIs
from sentence_transformers import SentenceTransformer

from ..database.database_manager import get_db_manager

logger = logging.getLogger(__name__)

# Registrar adaptador para numpy arrays
def adapt_numpy_array(numpy_array):
    return AsIs(f"'{numpy_array.tolist()}'::vector")

register_adapter(np.ndarray, adapt_numpy_array)


class PgVectorStore:
    """Vector store usando pgvector para embeddings"""
    
    def __init__(self, connection_string: Optional[str] = None, model_name: str = 'all-MiniLM-L6-v2'):
        self.connection_string = connection_string or get_db_manager().connection_string
        self.model_name = model_name
        self._model = None
        self.dimension = 384  # Para all-MiniLM-L6-v2
        
        # Inicializar pgvector
        self._init_pgvector()
    
    @property
    def model(self):
        """Lazy loading do modelo de embeddings"""
        if self._model is None:
            logger.info(f"Carregando modelo: {self.model_name}")
            self._model = SentenceTransformer(self.model_name)
        return self._model
    
    def _init_pgvector(self):
        """Inicializa pgvector no banco"""
        try:
            with psycopg2.connect(self.connection_string) as conn:
                with conn.cursor() as cur:
                    # Verificar se extensão existe
                    cur.execute("SELECT 1 FROM pg_extension WHERE extname = 'vector'")
                    if not cur.fetchone():
                        logger.info("Criando extensão pgvector...")
                        cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
                        
                        # Executar script de inicialização
                        with open('src/database/init_pgvector.sql', 'r') as f:
                            cur.execute(f.read())
                        
                        conn.commit()
                        logger.info("pgvector inicializado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao inicializar pgvector: {e}")
            raise
    
    def add_embedding(self, case_id: str, chunk_id: str, text: str) -> str:
        """
        Adiciona um embedding ao vector store
        
        Args:
            case_id: ID do caso
            chunk_id: ID do chunk
            text: Texto para gerar embedding
            
        Returns:
            ID do embedding criado
        """
        try:
            # Gerar embedding
            embedding = self.model.encode(text, convert_to_numpy=True)
            embedding = embedding / np.linalg.norm(embedding)  # Normalizar
            
            with psycopg2.connect(self.connection_string) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO embeddings_vector (case_id, chunk_id, embedding, model_name)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (chunk_id) 
                        DO UPDATE SET embedding = EXCLUDED.embedding, created_at = CURRENT_TIMESTAMP
                        RETURNING id
                    """, (case_id, chunk_id, embedding, self.model_name))
                    
                    embedding_id = cur.fetchone()[0]
                    conn.commit()
                    
            logger.debug(f"Embedding adicionado: {embedding_id}")
            return str(embedding_id)
            
        except Exception as e:
            logger.error(f"Erro ao adicionar embedding: {e}")
            raise
    
    def add_embeddings_batch(self, embeddings_data: List[Dict]) -> List[str]:
        """
        Adiciona múltiplos embeddings em lote
        
        Args:
            embeddings_data: Lista de dicts com case_id, chunk_id e text
            
        Returns:
            Lista de IDs criados
        """
        if not embeddings_data:
            return []
        
        try:
            # Extrair textos
            texts = [data['text'] for data in embeddings_data]
            
            # Gerar embeddings em lote
            embeddings = self.model.encode(
                texts,
                convert_to_numpy=True,
                batch_size=32,
                show_progress_bar=len(texts) > 100
            )
            
            # Normalizar
            embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
            
            # Inserir no banco
            created_ids = []
            with psycopg2.connect(self.connection_string) as conn:
                with conn.cursor() as cur:
                    for data, embedding in zip(embeddings_data, embeddings):
                        cur.execute("""
                            INSERT INTO embeddings_vector (case_id, chunk_id, embedding, model_name)
                            VALUES (%s, %s, %s, %s)
                            ON CONFLICT (chunk_id) 
                            DO UPDATE SET embedding = EXCLUDED.embedding, created_at = CURRENT_TIMESTAMP
                            RETURNING id
                        """, (data['case_id'], data['chunk_id'], embedding, self.model_name))
                        
                        created_ids.append(str(cur.fetchone()[0]))
                    
                    conn.commit()
            
            logger.info(f"Adicionados {len(created_ids)} embeddings em lote")
            return created_ids
            
        except Exception as e:
            logger.error(f"Erro ao adicionar embeddings em lote: {e}")
            raise
    
    def search(self, query: str, limit: int = 10, threshold: float = 0.7) -> List[Dict]:
        """
        Busca semântica por similaridade
        
        Args:
            query: Texto da busca
            limit: Número máximo de resultados
            threshold: Threshold de similaridade (0-1)
            
        Returns:
            Lista de resultados ordenados por similaridade
        """
        try:
            # Gerar embedding da query
            query_embedding = self.model.encode(query, convert_to_numpy=True)
            query_embedding = query_embedding / np.linalg.norm(query_embedding)
            
            with psycopg2.connect(self.connection_string) as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT * FROM search_similar_embeddings(%s, %s, %s)
                    """, (query_embedding, limit, threshold))
                    
                    results = cur.fetchall()
            
            logger.info(f"Busca semântica retornou {len(results)} resultados")
            return results
            
        except Exception as e:
            logger.error(f"Erro na busca semântica: {e}")
            raise
    
    def hybrid_search(self, query: str, keywords: Optional[List[str]] = None, 
                     limit: int = 20, semantic_weight: float = 0.7) -> List[Dict]:
        """
        Busca híbrida combinando semântica e palavras-chave
        
        Args:
            query: Texto para busca semântica
            keywords: Palavras-chave para busca textual
            limit: Número máximo de resultados
            semantic_weight: Peso da busca semântica (0-1)
            
        Returns:
            Lista de resultados com score combinado
        """
        try:
            # Se não houver keywords, extrair do query
            if not keywords:
                # Palavras relevantes do query (simplificado)
                keywords = [w for w in query.lower().split() if len(w) > 3]
            
            # Gerar embedding
            query_embedding = self.model.encode(query, convert_to_numpy=True)
            query_embedding = query_embedding / np.linalg.norm(query_embedding)
            
            with psycopg2.connect(self.connection_string) as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT * FROM hybrid_search(%s, %s, %s, %s)
                    """, (query_embedding, keywords, limit, semantic_weight))
                    
                    results = cur.fetchall()
            
            logger.info(f"Busca híbrida retornou {len(results)} resultados")
            return results
            
        except Exception as e:
            logger.error(f"Erro na busca híbrida: {e}")
            raise
    
    def get_statistics(self) -> Dict:
        """Retorna estatísticas do vector store"""
        try:
            with psycopg2.connect(self.connection_string) as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("SELECT * FROM embedding_statistics")
                    stats = cur.fetchone()
            
            return dict(stats) if stats else {}
            
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas: {e}")
            return {}
    
    def delete_case_embeddings(self, case_id: str) -> int:
        """Remove todos os embeddings de um caso"""
        try:
            with psycopg2.connect(self.connection_string) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        DELETE FROM embeddings_vector 
                        WHERE case_id = %s
                    """, (case_id,))
                    
                    deleted = cur.rowcount
                    conn.commit()
            
            logger.info(f"Removidos {deleted} embeddings do caso {case_id}")
            return deleted
            
        except Exception as e:
            logger.error(f"Erro ao deletar embeddings: {e}")
            raise
    
    def optimize_index(self):
        """Otimiza índices do vector store"""
        try:
            with psycopg2.connect(self.connection_string) as conn:
                with conn.cursor() as cur:
                    # Reindexar HNSW
                    cur.execute("REINDEX INDEX embeddings_vector_embedding_idx")
                    
                    # Vacuum analyze
                    cur.execute("VACUUM ANALYZE embeddings_vector")
                    
                    conn.commit()
            
            logger.info("Índices otimizados")
            
        except Exception as e:
            logger.error(f"Erro ao otimizar índices: {e}")
            raise


# Classe de compatibilidade para migração suave do ChromaDB
class VectorStore:
    """Interface unificada para vector store"""
    
    def __init__(self, use_pgvector: bool = True, **kwargs):
        if use_pgvector:
            self.backend = PgVectorStore(**kwargs)
            self.backend_type = 'pgvector'
        else:
            # Fallback para ChromaDB se necessário
            from .chroma_store import ChromaStore
            self.backend = ChromaStore(**kwargs)
            self.backend_type = 'chroma'
        
        logger.info(f"Vector store inicializado com backend: {self.backend_type}")
    
    def add_documents(self, documents: List[Dict]) -> List[str]:
        """Adiciona documentos ao vector store"""
        if self.backend_type == 'pgvector':
            return self.backend.add_embeddings_batch(documents)
        else:
            return self.backend.add_documents(documents)
    
    def search(self, query: str, **kwargs) -> List[Dict]:
        """Busca documentos similares"""
        return self.backend.search(query, **kwargs)
    
    def hybrid_search(self, query: str, **kwargs) -> List[Dict]:
        """Busca híbrida (se suportada)"""
        if hasattr(self.backend, 'hybrid_search'):
            return self.backend.hybrid_search(query, **kwargs)
        else:
            # Fallback para busca semântica simples
            return self.backend.search(query, **kwargs)