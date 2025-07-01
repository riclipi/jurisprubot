"""
Gerenciador de banco de dados PostgreSQL
Operações CRUD e queries otimizadas
"""

import os
import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from contextlib import contextmanager

from sqlalchemy import create_engine, and_, or_, func, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import NullPool

from .models import (
    Base, Case, Document, TextChunk, Embedding, 
    SearchQuery, SearchResult, ProcessingLog
)

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Gerenciador principal do banco de dados"""
    
    def __init__(self, connection_string: Optional[str] = None):
        """
        Inicializa o gerenciador do banco
        
        Args:
            connection_string: String de conexão PostgreSQL
                             Se não fornecida, usa variável de ambiente
        """
        self.connection_string = connection_string or os.getenv(
            'DATABASE_URL',
            'postgresql://postgres:postgres@localhost:5432/jurisprudencia_db'
        )
        
        # Criar engine com pool de conexões
        self.engine = create_engine(
            self.connection_string,
            pool_pre_ping=True,  # Verifica conexões antes de usar
            pool_size=10,        # Tamanho do pool
            max_overflow=20,     # Conexões extras permitidas
            echo=False           # True para debug SQL
        )
        
        # Criar session factory
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        
        # Criar tabelas se não existirem
        self.create_tables()
    
    def create_tables(self):
        """Cria todas as tabelas no banco"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Tabelas criadas/verificadas com sucesso")
        except Exception as e:
            logger.error(f"Erro ao criar tabelas: {e}")
            raise
    
    @contextmanager
    def get_session(self):
        """Context manager para sessões do banco"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Erro na sessão: {e}")
            raise
        finally:
            session.close()
    
    # ===== OPERAÇÕES DE CASE =====
    
    def create_case(self, case_data: Dict) -> Case:
        """Cria um novo caso no banco"""
        with self.get_session() as session:
            case = Case(**case_data)
            session.add(case)
            session.flush()
            return case
    
    def get_case_by_number(self, case_number: str) -> Optional[Case]:
        """Busca caso pelo número do processo"""
        with self.get_session() as session:
            return session.query(Case).filter(
                Case.case_number == case_number
            ).first()
    
    def case_exists(self, case_number: str) -> bool:
        """Verifica se caso já existe"""
        with self.get_session() as session:
            return session.query(
                session.query(Case).filter(
                    Case.case_number == case_number
                ).exists()
            ).scalar()
    
    def update_case_status(self, case_id: str, status: str, **kwargs):
        """Atualiza status do caso"""
        with self.get_session() as session:
            case = session.query(Case).filter(Case.id == case_id).first()
            if case:
                case.status = status
                case.updated_at = datetime.utcnow()
                
                # Atualizar campos adicionais
                for key, value in kwargs.items():
                    if hasattr(case, key):
                        setattr(case, key, value)
    
    def get_cases_to_process(self, status: str = 'downloaded', limit: int = 100) -> List[Case]:
        """Retorna casos pendentes de processamento"""
        with self.get_session() as session:
            return session.query(Case).filter(
                Case.status == status
            ).limit(limit).all()
    
    # ===== OPERAÇÕES DE DOCUMENT =====
    
    def create_document(self, case_id: str, text: str, metadata: Dict) -> Document:
        """Cria documento associado a um caso"""
        with self.get_session() as session:
            doc = Document(
                case_id=case_id,
                full_text=text,
                text_size=len(text),
                extracted_metadata=metadata,
                summary=text[:500] + '...' if len(text) > 500 else text
            )
            session.add(doc)
            session.flush()
            return doc
    
    def get_document_by_case(self, case_id: str) -> Optional[Document]:
        """Retorna documento de um caso"""
        with self.get_session() as session:
            return session.query(Document).filter(
                Document.case_id == case_id
            ).first()
    
    # ===== OPERAÇÕES DE CHUNKS =====
    
    def create_text_chunks(self, document_id: str, chunks: List[Dict]) -> List[TextChunk]:
        """Cria múltiplos chunks de texto"""
        with self.get_session() as session:
            chunk_objects = []
            for i, chunk_data in enumerate(chunks):
                chunk = TextChunk(
                    document_id=document_id,
                    chunk_text=chunk_data['text'],
                    chunk_index=i,
                    chunk_size=len(chunk_data['text']),
                    start_char=chunk_data.get('start', 0),
                    end_char=chunk_data.get('end', 0)
                )
                session.add(chunk)
                chunk_objects.append(chunk)
            
            session.flush()
            return chunk_objects
    
    # ===== OPERAÇÕES DE BUSCA =====
    
    def search_cases(self, filters: Dict, limit: int = 50) -> List[Case]:
        """
        Busca casos com filtros
        
        Filtros suportados:
        - date_from, date_to: Data do julgamento
        - judge: Relator
        - chamber: Câmara
        - county: Comarca
        - category: Categoria do caso
        - min_amount, max_amount: Valor da indenização
        - keywords: Palavras no texto
        """
        with self.get_session() as session:
            query = session.query(Case)
            
            # Filtro de datas
            if filters.get('date_from'):
                query = query.filter(Case.judgment_date >= filters['date_from'])
            if filters.get('date_to'):
                query = query.filter(Case.judgment_date <= filters['date_to'])
            
            # Filtro de relator
            if filters.get('judge'):
                query = query.filter(
                    Case.judge_rapporteur.ilike(f"%{filters['judge']}%")
                )
            
            # Filtro de câmara
            if filters.get('chamber'):
                query = query.filter(
                    Case.chamber.ilike(f"%{filters['chamber']}%")
                )
            
            # Filtro de comarca
            if filters.get('county'):
                query = query.filter(
                    Case.county.ilike(f"%{filters['county']}%")
                )
            
            # Filtro de categoria
            if filters.get('category'):
                query = query.filter(Case.case_category == filters['category'])
            
            # Filtro de valor
            if filters.get('min_amount'):
                query = query.filter(Case.compensation_amount >= filters['min_amount'])
            if filters.get('max_amount'):
                query = query.filter(Case.compensation_amount <= filters['max_amount'])
            
            # Ordenar por data descendente
            query = query.order_by(Case.judgment_date.desc())
            
            return query.limit(limit).all()
    
    def log_search(self, query_text: str, filters: Dict, results: List[Case], 
                   execution_time: float, user_id: Optional[str] = None) -> SearchQuery:
        """Registra uma busca realizada"""
        with self.get_session() as session:
            search = SearchQuery(
                query_text=query_text,
                query_type='hybrid',
                filters=filters,
                result_count=len(results),
                execution_time=execution_time,
                user_id=user_id
            )
            session.add(search)
            session.flush()
            
            # Adicionar resultados
            for i, case in enumerate(results):
                result = SearchResult(
                    query_id=search.id,
                    case_id=case.id,
                    rank_position=i + 1,
                    match_type='keyword'
                )
                session.add(result)
            
            return search
    
    # ===== ESTATÍSTICAS =====
    
    def get_statistics(self) -> Dict:
        """Retorna estatísticas do banco"""
        with self.get_session() as session:
            stats = {
                'total_cases': session.query(func.count(Case.id)).scalar(),
                'processed_cases': session.query(func.count(Case.id)).filter(
                    Case.status == 'processed'
                ).scalar(),
                'total_documents': session.query(func.count(Document.id)).scalar(),
                'total_chunks': session.query(func.count(TextChunk.id)).scalar(),
                'total_searches': session.query(func.count(SearchQuery.id)).scalar(),
            }
            
            # Estatísticas por categoria
            categories = session.query(
                Case.case_category,
                func.count(Case.id)
            ).group_by(Case.case_category).all()
            
            stats['by_category'] = {cat: count for cat, count in categories if cat}
            
            # Média de indenizações
            avg_compensation = session.query(
                func.avg(Case.compensation_amount)
            ).filter(Case.compensation_amount > 0).scalar()
            
            stats['avg_compensation'] = float(avg_compensation) if avg_compensation else 0
            
            return stats
    
    # ===== MANUTENÇÃO =====
    
    def cleanup_old_logs(self, days: int = 30):
        """Remove logs antigos"""
        with self.get_session() as session:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            deleted = session.query(ProcessingLog).filter(
                ProcessingLog.created_at < cutoff_date
            ).delete()
            logger.info(f"Removidos {deleted} logs antigos")
    
    def vacuum_analyze(self):
        """Executa VACUUM ANALYZE no PostgreSQL"""
        with self.engine.connect() as conn:
            conn.execute(text("VACUUM ANALYZE"))
            logger.info("VACUUM ANALYZE executado")


# Singleton para uso global
_db_manager = None

def get_db_manager(connection_string: Optional[str] = None) -> DatabaseManager:
    """Retorna instância singleton do gerenciador"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager(connection_string)
    return _db_manager