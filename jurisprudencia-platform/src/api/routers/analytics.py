"""
Router para endpoints de análise e estatísticas
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional
from datetime import datetime, timedelta
import logging

from src.api.models import TrendRequest, TrendResponse, CaseAnalytics
from src.database.database_manager import get_db_manager
from src.pipeline.tasks.reporting import generate_case_analytics, generate_trend_analysis

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/dashboard")
async def get_dashboard_stats():
    """
    Retorna estatísticas para o dashboard principal
    """
    try:
        db = get_db_manager()
        
        with db.get_session() as session:
            # Estatísticas gerais
            stats = db.get_statistics()
            
            # Casos recentes (últimos 7 dias)
            week_ago = datetime.utcnow() - timedelta(days=7)
            recent_cases = session.query(db.Case).filter(
                db.Case.created_at >= week_ago
            ).count()
            
            # Top câmaras
            top_chambers = session.execute("""
                SELECT chamber, COUNT(*) as count, AVG(compensation_amount) as avg_amount
                FROM cases
                WHERE chamber IS NOT NULL
                GROUP BY chamber
                ORDER BY count DESC
                LIMIT 5
            """).fetchall()
            
            # Distribuição por categoria
            categories = session.execute("""
                SELECT case_category, COUNT(*) as count
                FROM cases
                WHERE case_category IS NOT NULL
                GROUP BY case_category
                ORDER BY count DESC
            """).fetchall()
            
            # Evolução mensal
            monthly_evolution = session.execute("""
                SELECT 
                    DATE_TRUNC('month', created_at) as month,
                    COUNT(*) as cases,
                    AVG(compensation_amount) as avg_compensation
                FROM cases
                WHERE created_at >= NOW() - INTERVAL '12 months'
                GROUP BY month
                ORDER BY month
            """).fetchall()
            
            return {
                "success": True,
                "general_stats": stats,
                "recent_cases": recent_cases,
                "top_chambers": [
                    {
                        "chamber": c.chamber,
                        "count": c.count,
                        "avg_compensation": float(c.avg_amount) if c.avg_amount else 0
                    }
                    for c in top_chambers
                ],
                "categories": [
                    {"category": c.case_category, "count": c.count}
                    for c in categories
                ],
                "monthly_evolution": [
                    {
                        "month": m.month.isoformat(),
                        "cases": m.cases,
                        "avg_compensation": float(m.avg_compensation) if m.avg_compensation else 0
                    }
                    for m in monthly_evolution
                ]
            }
            
    except Exception as e:
        logger.error(f"Erro ao gerar dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trends", response_model=TrendResponse)
async def analyze_trends(
    request: TrendRequest
):
    """
    Analisa tendências temporais nos dados
    """
    try:
        # Executar análise (pode ser síncrono ou assíncrono via Celery)
        result = generate_trend_analysis(request.days)
        
        return TrendResponse(**result)
        
    except Exception as e:
        logger.error(f"Erro ao analisar tendências: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/case/{case_id}", response_model=CaseAnalytics)
async def analyze_case(
    case_id: str
):
    """
    Gera análise detalhada de um caso específico
    """
    try:
        # Executar análise
        result = generate_case_analytics(case_id)
        
        return CaseAnalytics(**result)
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Erro ao analisar caso: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/compensation-distribution")
async def get_compensation_distribution():
    """
    Retorna distribuição de valores de indenização
    """
    try:
        db = get_db_manager()
        
        with db.get_session() as session:
            # Faixas de valores
            ranges = [
                (0, 1000, "Até R$ 1.000"),
                (1000, 5000, "R$ 1.000 - R$ 5.000"),
                (5000, 10000, "R$ 5.000 - R$ 10.000"),
                (10000, 20000, "R$ 10.000 - R$ 20.000"),
                (20000, 50000, "R$ 20.000 - R$ 50.000"),
                (50000, None, "Acima de R$ 50.000")
            ]
            
            distribution = []
            
            for min_val, max_val, label in ranges:
                query = session.query(db.Case).filter(
                    db.Case.compensation_amount >= min_val
                )
                
                if max_val:
                    query = query.filter(db.Case.compensation_amount < max_val)
                
                count = query.count()
                
                # Estatísticas da faixa
                stats = query.with_entities(
                    db.func.avg(db.Case.compensation_amount),
                    db.func.min(db.Case.compensation_amount),
                    db.func.max(db.Case.compensation_amount)
                ).first()
                
                distribution.append({
                    "range": label,
                    "min": min_val,
                    "max": max_val,
                    "count": count,
                    "average": float(stats[0]) if stats[0] else 0,
                    "min_found": float(stats[1]) if stats[1] else 0,
                    "max_found": float(stats[2]) if stats[2] else 0
                })
            
            return {
                "success": True,
                "distribution": distribution,
                "total_cases_with_compensation": sum(d["count"] for d in distribution)
            }
            
    except Exception as e:
        logger.error(f"Erro ao calcular distribuição: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/judge-statistics")
async def get_judge_statistics(
    limit: int = Query(20, ge=1, le=100)
):
    """
    Estatísticas por relator/desembargador
    """
    try:
        db = get_db_manager()
        
        with db.get_session() as session:
            judges = session.execute("""
                SELECT 
                    judge_rapporteur,
                    COUNT(*) as total_cases,
                    AVG(compensation_amount) as avg_compensation,
                    MIN(compensation_amount) as min_compensation,
                    MAX(compensation_amount) as max_compensation,
                    COUNT(CASE WHEN compensation_amount > 0 THEN 1 END) as cases_with_compensation
                FROM cases
                WHERE judge_rapporteur IS NOT NULL
                GROUP BY judge_rapporteur
                HAVING COUNT(*) >= 5
                ORDER BY total_cases DESC
                LIMIT :limit
            """, {"limit": limit}).fetchall()
            
            return {
                "success": True,
                "judges": [
                    {
                        "judge": j.judge_rapporteur,
                        "total_cases": j.total_cases,
                        "cases_with_compensation": j.cases_with_compensation,
                        "avg_compensation": float(j.avg_compensation) if j.avg_compensation else 0,
                        "min_compensation": float(j.min_compensation) if j.min_compensation else 0,
                        "max_compensation": float(j.max_compensation) if j.max_compensation else 0
                    }
                    for j in judges
                ]
            }
            
    except Exception as e:
        logger.error(f"Erro ao calcular estatísticas por juiz: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search-analytics")
async def get_search_analytics(
    days: int = Query(30, ge=1, le=365)
):
    """
    Análise de queries de busca mais frequentes
    """
    try:
        db = get_db_manager()
        
        with db.get_session() as session:
            since = datetime.utcnow() - timedelta(days=days)
            
            # Top queries
            top_queries = session.execute("""
                SELECT 
                    query_text,
                    COUNT(*) as count,
                    AVG(result_count) as avg_results,
                    AVG(execution_time) as avg_time
                FROM search_queries
                WHERE created_at >= :since
                GROUP BY query_text
                ORDER BY count DESC
                LIMIT 20
            """, {"since": since}).fetchall()
            
            # Queries sem resultados
            no_results = session.execute("""
                SELECT query_text, COUNT(*) as count
                FROM search_queries
                WHERE created_at >= :since AND result_count = 0
                GROUP BY query_text
                ORDER BY count DESC
                LIMIT 10
            """, {"since": since}).fetchall()
            
            # Performance por tipo
            performance = session.execute("""
                SELECT 
                    query_type,
                    COUNT(*) as count,
                    AVG(execution_time) as avg_time,
                    MIN(execution_time) as min_time,
                    MAX(execution_time) as max_time
                FROM search_queries
                WHERE created_at >= :since
                GROUP BY query_type
            """, {"since": since}).fetchall()
            
            return {
                "success": True,
                "period_days": days,
                "top_queries": [
                    {
                        "query": q.query_text,
                        "count": q.count,
                        "avg_results": float(q.avg_results),
                        "avg_execution_time": float(q.avg_time)
                    }
                    for q in top_queries
                ],
                "queries_without_results": [
                    {"query": q.query_text, "count": q.count}
                    for q in no_results
                ],
                "performance_by_type": [
                    {
                        "type": p.query_type,
                        "count": p.count,
                        "avg_time": float(p.avg_time),
                        "min_time": float(p.min_time),
                        "max_time": float(p.max_time)
                    }
                    for p in performance
                ]
            }
            
    except Exception as e:
        logger.error(f"Erro ao analisar buscas: {e}")
        raise HTTPException(status_code=500, detail=str(e))