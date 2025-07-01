"""
Modelos de dados para o banco PostgreSQL
SQLAlchemy models para jurisprudência
"""

from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey, Index, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB
import uuid

Base = declarative_base()


class Case(Base):
    """Modelo principal para casos/acórdãos"""
    __tablename__ = 'cases'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_number = Column(String(50), unique=True, nullable=False, index=True)
    court = Column(String(10), default='TJSP')
    case_type = Column(String(50))  # Apelação Cível, Agravo, etc.
    
    # Metadados do julgamento
    judge_rapporteur = Column(String(200))  # Relator
    judgment_date = Column(DateTime)
    chamber = Column(String(100))  # Câmara/Turma
    county = Column(String(100))  # Comarca
    court_division = Column(String(200))  # Vara
    
    # URLs e arquivos
    pdf_url = Column(String(500))
    pdf_path = Column(String(500))
    pdf_size = Column(Integer)
    pdf_pages = Column(Integer)
    
    # Status de processamento
    status = Column(String(20), default='downloaded')  # downloaded, processed, indexed, error
    download_date = Column(DateTime, default=datetime.utcnow)
    process_date = Column(DateTime)
    
    # Análise e categorização
    case_category = Column(String(100))  # negativação indevida, cobrança indevida, etc.
    is_valid_negativation = Column(Boolean, default=False)
    negativation_mentions = Column(Integer, default=0)
    compensation_amount = Column(Float)  # Valor da indenização
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    documents = relationship("Document", back_populates="case", cascade="all, delete-orphan")
    embeddings = relationship("Embedding", back_populates="case", cascade="all, delete-orphan")
    search_results = relationship("SearchResult", back_populates="case")
    
    # Índices
    __table_args__ = (
        Index('idx_case_judgment_date', 'judgment_date'),
        Index('idx_case_category', 'case_category'),
        Index('idx_case_status', 'status'),
        Index('idx_case_compensation', 'compensation_amount'),
    )


class Document(Base):
    """Modelo para documentos/textos extraídos"""
    __tablename__ = 'documents'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(UUID(as_uuid=True), ForeignKey('cases.id'), nullable=False)
    
    # Conteúdo
    full_text = Column(Text, nullable=False)
    summary = Column(Text)
    text_size = Column(Integer)
    language = Column(String(10), default='pt')
    
    # Metadados extraídos
    extracted_metadata = Column(JSONB)  # JSON com todos os metadados extraídos
    
    # Processamento
    processed = Column(Boolean, default=False)
    process_date = Column(DateTime)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    case = relationship("Case", back_populates="documents")
    chunks = relationship("TextChunk", back_populates="document", cascade="all, delete-orphan")


class TextChunk(Base):
    """Modelo para chunks de texto para embeddings"""
    __tablename__ = 'text_chunks'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey('documents.id'), nullable=False)
    
    # Conteúdo do chunk
    chunk_text = Column(Text, nullable=False)
    chunk_index = Column(Integer)  # Posição no documento
    chunk_size = Column(Integer)
    
    # Metadados do chunk
    start_char = Column(Integer)
    end_char = Column(Integer)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    document = relationship("Document", back_populates="chunks")
    embeddings = relationship("Embedding", back_populates="chunk", cascade="all, delete-orphan")
    
    # Índices
    __table_args__ = (
        Index('idx_chunk_document', 'document_id'),
        Index('idx_chunk_index', 'chunk_index'),
    )


class Embedding(Base):
    """Modelo para embeddings vetoriais"""
    __tablename__ = 'embeddings'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(UUID(as_uuid=True), ForeignKey('cases.id'), nullable=False)
    chunk_id = Column(UUID(as_uuid=True), ForeignKey('text_chunks.id'), nullable=False)
    
    # Vetor de embedding (usar pgvector extension)
    # vector = Column(Vector(384))  # Para sentence-transformers
    vector = Column(ARRAY(Float))  # Alternativa sem pgvector
    
    # Modelo usado para gerar o embedding
    model_name = Column(String(100), default='all-MiniLM-L6-v2')
    vector_dimension = Column(Integer, default=384)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    case = relationship("Case", back_populates="embeddings")
    chunk = relationship("TextChunk", back_populates="embeddings")
    
    # Índices
    __table_args__ = (
        Index('idx_embedding_case', 'case_id'),
        Index('idx_embedding_chunk', 'chunk_id'),
    )


class SearchQuery(Base):
    """Modelo para queries de busca"""
    __tablename__ = 'search_queries'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Query
    query_text = Column(Text, nullable=False)
    query_type = Column(String(20))  # semantic, keyword, hybrid
    
    # Filtros aplicados
    filters = Column(JSONB)
    
    # Resultados
    result_count = Column(Integer)
    execution_time = Column(Float)  # em segundos
    
    # User tracking (opcional)
    user_id = Column(String(100))
    session_id = Column(String(100))
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    results = relationship("SearchResult", back_populates="query", cascade="all, delete-orphan")


class SearchResult(Base):
    """Modelo para resultados de busca"""
    __tablename__ = 'search_results'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    query_id = Column(UUID(as_uuid=True), ForeignKey('search_queries.id'), nullable=False)
    case_id = Column(UUID(as_uuid=True), ForeignKey('cases.id'), nullable=False)
    
    # Scoring
    relevance_score = Column(Float)
    rank_position = Column(Integer)
    
    # Tipo de match
    match_type = Column(String(20))  # semantic, keyword, both
    
    # Contexto do match
    matched_chunk = Column(Text)
    highlight_positions = Column(JSONB)  # Posições para destacar
    
    # Relacionamentos
    query = relationship("SearchQuery", back_populates="results")
    case = relationship("Case", back_populates="search_results")


class ProcessingLog(Base):
    """Modelo para logs de processamento"""
    __tablename__ = 'processing_logs'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Identificação
    process_type = Column(String(50))  # download, extract, embed, index
    case_id = Column(UUID(as_uuid=True), ForeignKey('cases.id'))
    
    # Status
    status = Column(String(20))  # started, completed, failed
    error_message = Column(Text)
    
    # Métricas
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    duration_seconds = Column(Float)
    
    # Detalhes adicionais
    details = Column(JSONB)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)


# Funções auxiliares para criar/gerenciar o banco

def create_database(connection_string):
    """Cria todas as tabelas no banco"""
    engine = create_engine(connection_string)
    Base.metadata.create_all(engine)
    return engine


def get_session(engine):
    """Retorna uma sessão do banco"""
    Session = sessionmaker(bind=engine)
    return Session()


# Exemplo de connection string
# postgresql://user:password@localhost:5432/jurisprudencia_db