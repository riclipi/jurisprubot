"""
Sistema de busca simplificado para Streamlit Cloud
Versão leve sem dependências pesadas
"""

import os
import json
import logging
from typing import List, Dict
from pathlib import Path

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SimpleSearchEngine:
    """Motor de busca simplificado com fallback para busca por palavras-chave"""
    
    def __init__(self):
        """Inicializa o sistema de busca"""
        logger.info("🚀 Inicializando sistema de busca simplificado...")
        
        # Definir diretório de dados
        base_dir = Path(__file__).parent.parent.parent
        self.data_dir = base_dir / "data" / "simple_rag"
        
        # Carregar dados locais
        self.documents = self._load_local_documents()
        
        # Tentar carregar sentence-transformers (com fallback)
        self.embedding_model = None
        try:
            from sentence_transformers import SentenceTransformer
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("✅ Modelo de embeddings carregado!")
            self.semantic_search_available = True
        except Exception as e:
            logger.warning(f"⚠️ Modelo de embeddings não disponível: {e}")
            logger.info("📝 Usando busca por palavras-chave como fallback")
            self.semantic_search_available = False
        
        logger.info(f"✅ Sistema inicializado com {len(self.documents)} documentos")
    
    def _load_local_documents(self) -> List[Dict]:
        """Carrega documentos locais do JSON"""
        documents = []
        json_path = self.data_dir / "processed_data.json"
        
        if json_path.exists():
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # Processar cada documento
                for doc in data.get('documents', []):
                    # Cada chunk vira um documento
                    for chunk in doc.get('chunks', []):
                        documents.append({
                            'id': chunk['id'],
                            'text': chunk['text'],
                            'file': doc['file'],
                            'metadata': {
                                'file': doc['file'],
                                'chunk_index': chunk['chunk_index']
                            }
                        })
                
                logger.info(f"📚 Carregados {len(documents)} chunks de {json_path}")
            except Exception as e:
                logger.error(f"❌ Erro ao carregar dados: {e}")
        else:
            logger.warning(f"⚠️ Arquivo não encontrado: {json_path}")
        
        return documents
    
    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Busca documentos relevantes
        
        Args:
            query: Consulta de busca
            top_k: Número de resultados
            
        Returns:
            Lista de documentos relevantes
        """
        if not self.documents:
            logger.warning("⚠️ Nenhum documento disponível")
            return []
        
        if self.semantic_search_available and self.embedding_model:
            # Usar busca semântica
            return self._semantic_search(query, top_k)
        else:
            # Fallback para busca por palavras-chave
            return self._keyword_search(query, top_k)
    
    def _semantic_search(self, query: str, top_k: int) -> List[Dict]:
        """Busca semântica usando embeddings"""
        try:
            from sklearn.metrics.pairwise import cosine_similarity
            import numpy as np
            
            # Gerar embedding da query
            query_embedding = self.embedding_model.encode([query])
            
            # Gerar embeddings dos documentos
            doc_texts = [doc['text'] for doc in self.documents]
            doc_embeddings = self.embedding_model.encode(doc_texts)
            
            # Calcular similaridades
            similarities = cosine_similarity(query_embedding, doc_embeddings)[0]
            
            # Ordenar por similaridade
            top_indices = np.argsort(similarities)[::-1][:top_k]
            
            # Preparar resultados
            results = []
            for i, idx in enumerate(top_indices):
                if similarities[idx] > 0:
                    results.append({
                        'rank': i + 1,
                        'score': float(similarities[idx]),
                        'text': self.documents[idx]['text'],
                        'metadata': self.documents[idx]['metadata']
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Erro na busca semântica: {e}")
            # Fallback para busca por palavras-chave
            return self._keyword_search(query, top_k)
    
    def _keyword_search(self, query: str, top_k: int) -> List[Dict]:
        """Busca simples por palavras-chave (fallback)"""
        logger.info(f"🔍 Busca por palavras-chave: '{query}'")
        
        # Tokenizar query
        query_words = query.lower().split()
        
        # Calcular scores
        scored_docs = []
        for doc in self.documents:
            text_lower = doc['text'].lower()
            
            # Contar ocorrências de cada palavra
            score = 0
            for word in query_words:
                score += text_lower.count(word)
            
            # Adicionar bonus se todas as palavras estão presentes
            if all(word in text_lower for word in query_words):
                score *= 1.5
            
            if score > 0:
                scored_docs.append({
                    'score': score,
                    'doc': doc
                })
        
        # Ordenar por score
        scored_docs.sort(key=lambda x: x['score'], reverse=True)
        
        # Preparar resultados
        results = []
        for i, item in enumerate(scored_docs[:top_k]):
            # Normalizar score entre 0 e 1
            max_score = scored_docs[0]['score'] if scored_docs else 1
            normalized_score = item['score'] / max_score if max_score > 0 else 0
            
            results.append({
                'rank': i + 1,
                'score': normalized_score,
                'text': item['doc']['text'],
                'metadata': item['doc']['metadata']
            })
        
        return results