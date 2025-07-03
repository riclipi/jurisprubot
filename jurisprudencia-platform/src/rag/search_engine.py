"""
Motor de busca unificado com suporte a busca híbrida
Combina busca semântica (pgvector) com busca por palavras-chave (PostgreSQL FTS)
"""

import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import re

from ..database.database_manager import get_db_manager
from .vector_store import VectorStore

logger = logging.getLogger(__name__)


class SearchEngine:
    """Motor de busca híbrido para jurisprudência"""
    
    def __init__(self, use_pgvector: bool = True):
        self.db = get_db_manager()
        self.vector_store = VectorStore(use_pgvector=use_pgvector)
        
        # Pesos padrão para busca híbrida
        self.default_weights = {
            'semantic': 0.6,
            'keyword': 0.2,
            'metadata': 0.2
        }
    
    def search(self, query: str, filters: Optional[Dict] = None, 
              limit: int = 20, search_type: str = 'hybrid') -> Dict:
        """
        Busca unificada com múltiplas estratégias
        
        Args:
            query: Texto da busca
            filters: Filtros de metadados (data, comarca, valor, etc.)
            limit: Número máximo de resultados
            search_type: 'semantic', 'keyword', 'hybrid'
            
        Returns:
            Dict com resultados e metadados da busca
        """
        start_time = datetime.utcnow()
        
        try:
            if search_type == 'semantic':
                results = self._semantic_search(query, filters, limit)
            elif search_type == 'keyword':
                results = self._keyword_search(query, filters, limit)
            else:  # hybrid
                results = self._hybrid_search(query, filters, limit)
            
            # Enriquecer resultados com metadados completos
            enriched_results = self._enrich_results(results)
            
            # Calcular tempo de execução
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Registrar busca
            self._log_search(query, filters, enriched_results, execution_time)
            
            return {
                'query': query,
                'type': search_type,
                'filters': filters,
                'results': enriched_results,
                'total_found': len(enriched_results),
                'execution_time': execution_time,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erro na busca: {e}")
            return {
                'query': query,
                'error': str(e),
                'results': [],
                'total_found': 0
            }
    
    def _semantic_search(self, query: str, filters: Optional[Dict], limit: int) -> List[Dict]:
        """Busca puramente semântica usando embeddings"""
        # Buscar por similaridade
        vector_results = self.vector_store.search(query, limit=limit * 2)
        
        # Aplicar filtros se fornecidos
        if filters:
            case_ids = [r['case_id'] for r in vector_results]
            filtered_ids = self._apply_filters(case_ids, filters)
            vector_results = [r for r in vector_results if r['case_id'] in filtered_ids]
        
        # Formatar resultados
        results = []
        for r in vector_results[:limit]:
            results.append({
                'case_id': r['case_id'],
                'chunk_id': r.get('chunk_id'),
                'score': r.get('similarity', 0),
                'score_type': 'semantic',
                'highlight': r.get('chunk_text', '')[:200] + '...'
            })
        
        return results
    
    def _keyword_search(self, query: str, filters: Optional[Dict], limit: int) -> List[Dict]:
        """Busca por palavras-chave usando PostgreSQL Full Text Search"""
        with self.db.get_session() as session:
            # Preparar query para FTS
            search_query = self._prepare_fts_query(query)
            
            # Query base
            sql = """
                SELECT DISTINCT
                    c.id as case_id,
                    c.case_number,
                    ts_rank(to_tsvector('portuguese', d.full_text), 
                           plainto_tsquery('portuguese', :query)) as score,
                    ts_headline('portuguese', d.full_text, 
                               plainto_tsquery('portuguese', :query),
                               'StartSel=<mark>, StopSel=</mark>, MaxWords=30') as highlight
                FROM cases c
                JOIN documents d ON d.case_id = c.id
                WHERE to_tsvector('portuguese', d.full_text) @@ 
                      plainto_tsquery('portuguese', :query)
            """
            
            # Aplicar filtros
            conditions = []
            params = {'query': search_query}
            
            if filters:
                if filters.get('date_from'):
                    conditions.append("c.judgment_date >= :date_from")
                    params['date_from'] = filters['date_from']
                
                if filters.get('date_to'):
                    conditions.append("c.judgment_date <= :date_to")
                    params['date_to'] = filters['date_to']
                
                if filters.get('county'):
                    conditions.append("c.county ILIKE :county")
                    params['county'] = f"%{filters['county']}%"
                
                if filters.get('min_amount'):
                    conditions.append("c.compensation_amount >= :min_amount")
                    params['min_amount'] = filters['min_amount']
            
            if conditions:
                sql += " AND " + " AND ".join(conditions)
            
            sql += " ORDER BY score DESC LIMIT :limit"
            params['limit'] = limit
            
            # Executar query
            results = session.execute(sql, params).fetchall()
            
            # Formatar resultados
            return [
                {
                    'case_id': str(r.case_id),
                    'case_number': r.case_number,
                    'score': float(r.score),
                    'score_type': 'keyword',
                    'highlight': r.highlight
                }
                for r in results
            ]
    
    def _hybrid_search(self, query: str, filters: Optional[Dict], limit: int) -> List[Dict]:
        """Busca híbrida combinando múltiplas estratégias"""
        # Extrair palavras-chave da query
        keywords = self._extract_keywords(query)
        
        # Busca vetorial com pgvector
        if hasattr(self.vector_store.backend, 'hybrid_search'):
            vector_results = self.vector_store.backend.hybrid_search(
                query=query,
                keywords=keywords,
                limit=limit * 2,
                semantic_weight=self.default_weights['semantic']
            )
        else:
            # Fallback para busca semântica simples
            vector_results = self.vector_store.search(query, limit=limit * 2)
        
        # Aplicar filtros se necessário
        if filters:
            case_ids = [r['case_id'] for r in vector_results]
            filtered_ids = self._apply_filters(case_ids, filters)
            vector_results = [r for r in vector_results if r['case_id'] in filtered_ids]
        
        # Re-ranquear com scores combinados
        final_results = []
        for r in vector_results[:limit]:
            combined_score = self._calculate_combined_score(r)
            
            final_results.append({
                'case_id': r['case_id'],
                'chunk_id': r.get('chunk_id'),
                'score': combined_score,
                'score_type': 'hybrid',
                'semantic_score': r.get('semantic_score', 0),
                'keyword_score': r.get('keyword_score', 0),
                'highlight': r.get('chunk_text', '')[:200] + '...'
            })
        
        # Ordenar por score combinado
        final_results.sort(key=lambda x: x['score'], reverse=True)
        
        return final_results
    
    def _extract_keywords(self, query: str) -> List[str]:
        """Extrai palavras-chave relevantes da query"""
        # Remover stopwords simples (expandir com NLTK se necessário)
        stopwords = {'de', 'a', 'o', 'que', 'e', 'do', 'da', 'em', 'um', 'para', 
                    'é', 'com', 'não', 'uma', 'os', 'no', 'se', 'na', 'por'}
        
        # Tokenizar e filtrar
        words = re.findall(r'\b\w+\b', query.lower())
        keywords = [w for w in words if len(w) > 2 and w not in stopwords]
        
        # Adicionar termos jurídicos importantes se presentes
        juridical_terms = ['negativação', 'serasa', 'spc', 'danos', 'morais', 
                          'indenização', 'inadimplente', 'crédito']
        
        for term in juridical_terms:
            if term in query.lower() and term not in keywords:
                keywords.append(term)
        
        return keywords[:10]  # Limitar a 10 keywords
    
    def _calculate_combined_score(self, result: Dict) -> float:
        """Calcula score combinado para resultado híbrido"""
        semantic = result.get('semantic_score', 0) * self.default_weights['semantic']
        keyword = result.get('keyword_score', 0) * self.default_weights['keyword']
        
        # Bonus por metadados relevantes
        metadata_bonus = 0
        if result.get('final_score'):
            return float(result['final_score'])
        
        return semantic + keyword + metadata_bonus
    
    def _apply_filters(self, case_ids: List[str], filters: Dict) -> List[str]:
        """Aplica filtros de metadados e retorna IDs válidos"""
        filtered_cases = self.db.search_cases(filters, limit=1000)
        filtered_ids = {str(c.id) for c in filtered_cases}
        
        # Interseção com IDs da busca
        return [cid for cid in case_ids if cid in filtered_ids]
    
    def _enrich_results(self, results: List[Dict]) -> List[Dict]:
        """Enriquece resultados com metadados completos"""
        if not results:
            return []
        
        case_ids = list(set(r['case_id'] for r in results))
        
        # Buscar casos do banco
        with self.db.get_session() as session:
            cases = session.query(self.db.Case).filter(
                self.db.Case.id.in_(case_ids)
            ).all()
            
            case_map = {str(c.id): c for c in cases}
        
        # Enriquecer cada resultado
        enriched = []
        for r in results:
            case = case_map.get(r['case_id'])
            if case:
                enriched.append({
                    **r,
                    'case_number': case.case_number,
                    'judge': case.judge_rapporteur,
                    'chamber': case.chamber,
                    'county': case.county,
                    'judgment_date': case.judgment_date.isoformat() if case.judgment_date else None,
                    'compensation_amount': float(case.compensation_amount) if case.compensation_amount else None,
                    'category': case.case_category,
                    'pdf_url': case.pdf_url
                })
        
        return enriched
    
    def _prepare_fts_query(self, query: str) -> str:
        """Prepara query para Full Text Search do PostgreSQL"""
        # Remover caracteres especiais
        query = re.sub(r'[^\w\s]', ' ', query)
        
        # Adicionar operadores para termos importantes
        important_terms = ['negativação', 'indevida', 'serasa', 'spc', 'danos morais']
        
        for term in important_terms:
            if term in query.lower():
                query = query.replace(term, f"{term}:*")
        
        return query
    
    def _log_search(self, query: str, filters: Optional[Dict], 
                   results: List[Dict], execution_time: float):
        """Registra busca no banco para análise"""
        try:
            self.db.log_search(
                query_text=query,
                filters=filters or {},
                results=[{'id': r['case_id']} for r in results],
                execution_time=execution_time
            )
        except Exception as e:
            logger.error(f"Erro ao registrar busca: {e}")
    
    def get_suggestions(self, partial_query: str, limit: int = 5) -> List[str]:
        """Retorna sugestões de busca baseadas em queries anteriores"""
        with self.db.get_session() as session:
            # Buscar queries similares mais frequentes
            results = session.execute("""
                SELECT DISTINCT query_text, COUNT(*) as freq
                FROM search_queries
                WHERE LOWER(query_text) LIKE LOWER(:partial) || '%'
                GROUP BY query_text
                ORDER BY freq DESC
                LIMIT :limit
            """, {'partial': partial_query, 'limit': limit})
            
            return [r.query_text for r in results]
    
    def get_facets(self, query: Optional[str] = None) -> Dict:
        """Retorna facetas para refinamento de busca"""
        with self.db.get_session() as session:
            facets = {}
            
            # Facetas por câmara
            chambers = session.execute("""
                SELECT chamber, COUNT(*) as count
                FROM cases
                WHERE chamber IS NOT NULL
                GROUP BY chamber
                ORDER BY count DESC
                LIMIT 10
            """).fetchall()
            
            facets['chambers'] = [
                {'value': c.chamber, 'count': c.count} 
                for c in chambers
            ]
            
            # Facetas por comarca
            counties = session.execute("""
                SELECT county, COUNT(*) as count
                FROM cases
                WHERE county IS NOT NULL
                GROUP BY county
                ORDER BY count DESC
                LIMIT 10
            """).fetchall()
            
            facets['counties'] = [
                {'value': c.county, 'count': c.count} 
                for c in counties
            ]
            
            # Faixas de valor
            facets['compensation_ranges'] = [
                {'label': 'Até R$ 5.000', 'min': 0, 'max': 5000},
                {'label': 'R$ 5.000 - R$ 10.000', 'min': 5000, 'max': 10000},
                {'label': 'R$ 10.000 - R$ 20.000', 'min': 10000, 'max': 20000},
                {'label': 'Acima de R$ 20.000', 'min': 20000, 'max': None}
            ]
            
            return facets