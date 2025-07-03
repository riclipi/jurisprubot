"""
Router para endpoints de busca
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional, Dict
import logging

from ..models import SearchRequest, SearchResponse, SearchResult
from ...rag.search_engine import SearchEngine
from ...database.database_manager import get_db_manager
from ...auth.auth import get_current_active_user, User

logger = logging.getLogger(__name__)
router = APIRouter()

# Instância global do search engine
_search_engine = None

def get_search_engine() -> SearchEngine:
    """Dependency para obter search engine"""
    global _search_engine
    if _search_engine is None:
        _search_engine = SearchEngine()
    return _search_engine


@router.post("/", response_model=SearchResponse)
async def search(
    request: SearchRequest,
    engine: SearchEngine = Depends(get_search_engine),
    current_user: User = Depends(get_current_active_user)
):
    """
    Realiza busca na base de jurisprudência
    
    Tipos de busca:
    - **semantic**: Busca por similaridade usando embeddings
    - **keyword**: Busca por palavras-chave com PostgreSQL FTS
    - **hybrid**: Combina busca semântica e por palavras-chave
    
    Filtros disponíveis:
    - date_from, date_to: Filtro por data de julgamento
    - county: Filtro por comarca
    - chamber: Filtro por câmara
    - judge: Filtro por relator
    - min_amount, max_amount: Filtro por valor de indenização
    """
    try:
        # Executar busca
        result = engine.search(
            query=request.query,
            filters=request.filters,
            limit=request.limit,
            search_type=request.search_type.value
        )
        
        # Adicionar facetas se não houver erro
        if not result.get('error'):
            result['facets'] = engine.get_facets(request.query)
        
        # Converter para modelo de resposta
        return SearchResponse(
            success=not bool(result.get('error')),
            **result
        )
        
    except Exception as e:
        logger.error(f"Erro na busca: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/suggestions")
async def get_suggestions(
    q: str = Query(..., min_length=2, description="Texto parcial para sugestões"),
    limit: int = Query(5, ge=1, le=10),
    engine: SearchEngine = Depends(get_search_engine)
):
    """
    Retorna sugestões de busca baseadas em queries anteriores
    """
    try:
        suggestions = engine.get_suggestions(q, limit)
        return {
            "query": q,
            "suggestions": suggestions
        }
    except Exception as e:
        logger.error(f"Erro ao obter sugestões: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/facets")
async def get_search_facets(
    engine: SearchEngine = Depends(get_search_engine)
):
    """
    Retorna facetas disponíveis para filtros de busca
    
    Inclui:
    - Câmaras mais frequentes
    - Comarcas disponíveis
    - Faixas de valores de indenização
    """
    try:
        facets = engine.get_facets()
        return {
            "success": True,
            "facets": facets
        }
    except Exception as e:
        logger.error(f"Erro ao obter facetas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/related/{case_id}")
async def get_related_cases(
    case_id: str,
    limit: int = Query(10, ge=1, le=50),
    engine: SearchEngine = Depends(get_search_engine)
):
    """
    Busca casos relacionados/similares a um caso específico
    """
    try:
        db = get_db_manager()
        
        # Buscar caso original
        with db.get_session() as session:
            case = session.query(db.Case).filter_by(id=case_id).first()
            if not case:
                raise HTTPException(status_code=404, detail="Caso não encontrado")
            
            # Buscar documento
            doc = session.query(db.Document).filter_by(case_id=case_id).first()
            if not doc:
                raise HTTPException(status_code=404, detail="Documento não encontrado")
        
        # Usar resumo ou primeiras palavras como query
        query_text = doc.summary or doc.full_text[:500]
        
        # Busca semântica excluindo o próprio caso
        results = engine.search(
            query=query_text,
            limit=limit + 1,
            search_type="semantic"
        )
        
        # Filtrar o próprio caso
        related = [
            r for r in results.get('results', [])
            if r['case_id'] != case_id
        ][:limit]
        
        return {
            "success": True,
            "case_id": case_id,
            "case_number": case.case_number,
            "related_cases": related,
            "total_found": len(related)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao buscar casos relacionados: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export")
async def export_search_results(
    request: SearchRequest,
    format: str = Query("json", regex="^(json|csv|xlsx)$"),
    engine: SearchEngine = Depends(get_search_engine)
):
    """
    Exporta resultados de busca em diferentes formatos
    
    Formatos suportados:
    - json: JSON completo
    - csv: Arquivo CSV
    - xlsx: Planilha Excel
    """
    try:
        # Aumentar limite para exportação
        request.limit = min(request.limit * 10, 1000)
        
        # Executar busca
        result = engine.search(
            query=request.query,
            filters=request.filters,
            limit=request.limit,
            search_type=request.search_type.value
        )
        
        if format == "json":
            return result
        
        # TODO: Implementar exportação CSV e XLSX
        raise HTTPException(
            status_code=501,
            detail=f"Formato {format} ainda não implementado"
        )
        
    except Exception as e:
        logger.error(f"Erro ao exportar resultados: {e}")
        raise HTTPException(status_code=500, detail=str(e))