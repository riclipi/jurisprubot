"""
Tasks de relatórios e estatísticas
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List
import json

from celery import Task
from src.pipeline.celery_app import app
from src.database.database_manager import get_db_manager

logger = logging.getLogger(__name__)


@app.task
def generate_daily_report():
    """
    Gera relatório diário de atividades
    """
    logger.info("Gerando relatório diário")
    
    db = get_db_manager()
    
    try:
        # Período do relatório (últimas 24h)
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=1)
        
        report = {
            'report_date': end_date.isoformat(),
            'period_start': start_date.isoformat(),
            'period_end': end_date.isoformat()
        }
        
        with db.get_session() as session:
            # Novos casos
            new_cases = session.query(db.Case).filter(
                db.Case.created_at >= start_date,
                db.Case.created_at < end_date
            ).count()
            
            # Casos processados
            processed_cases = session.query(db.Case).filter(
                db.Case.process_date >= start_date,
                db.Case.process_date < end_date
            ).count()
            
            # Buscas realizadas
            searches = session.query(db.SearchQuery).filter(
                db.SearchQuery.created_at >= start_date,
                db.SearchQuery.created_at < end_date
            ).count()
            
            # Estatísticas de processamento
            processing_stats = session.execute("""
                SELECT 
                    status,
                    COUNT(*) as count
                FROM cases
                WHERE updated_at >= :start_date
                    AND updated_at < :end_date
                GROUP BY status
            """, {'start_date': start_date, 'end_date': end_date}).fetchall()
            
            # Top termos de busca
            top_searches = session.execute("""
                SELECT 
                    query_text,
                    COUNT(*) as count
                FROM search_queries
                WHERE created_at >= :start_date
                    AND created_at < :end_date
                GROUP BY query_text
                ORDER BY count DESC
                LIMIT 10
            """, {'start_date': start_date, 'end_date': end_date}).fetchall()
            
            # Valores de indenização
            compensation_stats = session.execute("""
                SELECT 
                    COUNT(*) as total,
                    AVG(compensation_amount) as avg_amount,
                    MIN(compensation_amount) as min_amount,
                    MAX(compensation_amount) as max_amount
                FROM cases
                WHERE compensation_amount > 0
                    AND process_date >= :start_date
                    AND process_date < :end_date
            """, {'start_date': start_date, 'end_date': end_date}).fetchone()
        
        # Montar relatório
        report['summary'] = {
            'new_cases': new_cases,
            'processed_cases': processed_cases,
            'total_searches': searches
        }
        
        report['processing_stats'] = {
            status: count for status, count in processing_stats
        }
        
        report['top_searches'] = [
            {'query': query, 'count': count}
            for query, count in top_searches
        ]
        
        if compensation_stats and compensation_stats.total > 0:
            report['compensation_stats'] = {
                'total_cases': compensation_stats.total,
                'average': float(compensation_stats.avg_amount or 0),
                'minimum': float(compensation_stats.min_amount or 0),
                'maximum': float(compensation_stats.max_amount or 0)
            }
        
        # Estatísticas gerais
        general_stats = db.get_statistics()
        report['general_stats'] = general_stats
        
        # Salvar relatório
        report_path = f"reports/daily_report_{end_date.strftime('%Y%m%d')}.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Relatório diário salvo em: {report_path}")
        
        # Enviar notificação
        from .scraping import send_notification
        send_notification.delay(
            "Relatório Diário de Jurisprudência",
            report['summary']
        )
        
        return report
        
    except Exception as e:
        logger.error(f"Erro ao gerar relatório diário: {e}")
        raise


@app.task
def generate_case_analytics(case_id: str) -> Dict:
    """
    Gera análise detalhada de um caso específico
    
    Args:
        case_id: ID do caso
    """
    logger.info(f"Gerando análise do caso {case_id}")
    
    db = get_db_manager()
    
    try:
        with db.get_session() as session:
            case = session.query(db.Case).filter_by(id=case_id).first()
            if not case:
                raise ValueError(f"Caso {case_id} não encontrado")
            
            analytics = {
                'case_id': str(case.id),
                'case_number': case.case_number,
                'generated_at': datetime.utcnow().isoformat()
            }
            
            # Informações básicas
            analytics['basic_info'] = {
                'judge': case.judge_rapporteur,
                'chamber': case.chamber,
                'county': case.county,
                'judgment_date': case.judgment_date.isoformat() if case.judgment_date else None,
                'compensation': float(case.compensation_amount) if case.compensation_amount else None
            }
            
            # Análise de texto
            doc = session.query(db.Document).filter_by(case_id=case_id).first()
            if doc:
                analytics['text_analysis'] = {
                    'text_size': doc.text_size,
                    'chunks_count': session.query(db.TextChunk).filter_by(
                        document_id=doc.id
                    ).count(),
                    'embeddings_count': session.query(db.Embedding).filter_by(
                        case_id=case_id
                    ).count()
                }
                
                # Palavras mais frequentes (simples)
                text = doc.full_text.lower()
                words = text.split()
                word_freq = {}
                for word in words:
                    if len(word) > 5:  # Palavras relevantes
                        word_freq[word] = word_freq.get(word, 0) + 1
                
                top_words = sorted(
                    word_freq.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:20]
                
                analytics['top_words'] = [
                    {'word': word, 'count': count}
                    for word, count in top_words
                ]
            
            # Casos similares (baseado em metadados)
            similar_cases = session.query(db.Case).filter(
                db.Case.id != case_id,
                db.Case.chamber == case.chamber,
                db.Case.case_category == case.case_category
            ).limit(5).all()
            
            analytics['similar_cases'] = [
                {
                    'case_number': c.case_number,
                    'judge': c.judge_rapporteur,
                    'compensation': float(c.compensation_amount) if c.compensation_amount else None
                }
                for c in similar_cases
            ]
        
        logger.info(f"Análise gerada para caso {case.case_number}")
        
        return analytics
        
    except Exception as e:
        logger.error(f"Erro ao gerar análise do caso {case_id}: {e}")
        raise


@app.task
def generate_trend_analysis(days: int = 30) -> Dict:
    """
    Analisa tendências nos últimos N dias
    
    Args:
        days: Número de dias para análise
    """
    logger.info(f"Gerando análise de tendências dos últimos {days} dias")
    
    db = get_db_manager()
    
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        trends = {
            'period_days': days,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        }
        
        with db.get_session() as session:
            # Tendência de valores de indenização
            compensation_trend = session.execute("""
                SELECT 
                    DATE(judgment_date) as date,
                    COUNT(*) as count,
                    AVG(compensation_amount) as avg_amount
                FROM cases
                WHERE judgment_date >= :start_date
                    AND judgment_date < :end_date
                    AND compensation_amount > 0
                GROUP BY DATE(judgment_date)
                ORDER BY date
            """, {'start_date': start_date, 'end_date': end_date}).fetchall()
            
            trends['compensation_trend'] = [
                {
                    'date': str(date),
                    'count': count,
                    'average': float(avg or 0)
                }
                for date, count, avg in compensation_trend
            ]
            
            # Tendência por câmara
            chamber_stats = session.execute("""
                SELECT 
                    chamber,
                    COUNT(*) as total,
                    AVG(compensation_amount) as avg_amount
                FROM cases
                WHERE created_at >= :start_date
                    AND created_at < :end_date
                GROUP BY chamber
                ORDER BY total DESC
                LIMIT 10
            """, {'start_date': start_date, 'end_date': end_date}).fetchall()
            
            trends['by_chamber'] = [
                {
                    'chamber': chamber,
                    'cases': total,
                    'avg_compensation': float(avg or 0)
                }
                for chamber, total, avg in chamber_stats
            ]
            
            # Tendência de buscas
            search_trend = session.execute("""
                SELECT 
                    DATE(created_at) as date,
                    COUNT(*) as searches,
                    AVG(result_count) as avg_results
                FROM search_queries
                WHERE created_at >= :start_date
                    AND created_at < :end_date
                GROUP BY DATE(created_at)
                ORDER BY date
            """, {'start_date': start_date, 'end_date': end_date}).fetchall()
            
            trends['search_trend'] = [
                {
                    'date': str(date),
                    'searches': searches,
                    'avg_results': float(avg or 0)
                }
                for date, searches, avg in search_trend
            ]
        
        logger.info("Análise de tendências concluída")
        
        return trends
        
    except Exception as e:
        logger.error(f"Erro ao gerar análise de tendências: {e}")
        raise