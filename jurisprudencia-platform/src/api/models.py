"""
Modelos Pydantic para a API
Schemas de request/response
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


# Enums
class SearchType(str, Enum):
    semantic = "semantic"
    keyword = "keyword"
    hybrid = "hybrid"


class CaseStatus(str, Enum):
    downloaded = "downloaded"
    processing = "processing"
    processed = "processed"
    indexed = "indexed"
    error = "error"


# Base Models
class HealthCheck(BaseModel):
    status: str
    service: str
    version: str
    database: Optional[str] = None
    total_cases: Optional[int] = None
    total_documents: Optional[int] = None


# Search Models
class SearchRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=500, description="Texto da busca")
    search_type: SearchType = SearchType.hybrid
    limit: int = Field(20, ge=1, le=100, description="Número máximo de resultados")
    filters: Optional[Dict[str, Any]] = Field(None, description="Filtros opcionais")
    
    class Config:
        schema_extra = {
            "example": {
                "query": "negativação indevida Serasa danos morais",
                "search_type": "hybrid",
                "limit": 20,
                "filters": {
                    "date_from": "2024-01-01",
                    "county": "São Paulo",
                    "min_amount": 5000
                }
            }
        }


class SearchResult(BaseModel):
    case_id: str
    case_number: str
    score: float
    score_type: str
    highlight: str
    judge: Optional[str] = None
    chamber: Optional[str] = None
    county: Optional[str] = None
    judgment_date: Optional[datetime] = None
    compensation_amount: Optional[float] = None
    category: Optional[str] = None
    pdf_url: Optional[str] = None


class SearchResponse(BaseModel):
    success: bool = True
    query: str
    type: str
    filters: Optional[Dict[str, Any]]
    results: List[SearchResult]
    total_found: int
    execution_time: float
    timestamp: datetime
    facets: Optional[Dict[str, Any]] = None


# Case Models
class CaseBase(BaseModel):
    case_number: str
    court: str = "TJSP"
    judge_rapporteur: Optional[str] = None
    judgment_date: Optional[datetime] = None
    chamber: Optional[str] = None
    county: Optional[str] = None
    court_division: Optional[str] = None
    case_category: Optional[str] = None
    compensation_amount: Optional[float] = None


class CaseCreate(CaseBase):
    pdf_url: Optional[str] = None
    pdf_path: Optional[str] = None


class CaseUpdate(BaseModel):
    status: Optional[CaseStatus] = None
    judge_rapporteur: Optional[str] = None
    judgment_date: Optional[datetime] = None
    chamber: Optional[str] = None
    county: Optional[str] = None
    compensation_amount: Optional[float] = None


class Case(CaseBase):
    id: str
    status: CaseStatus
    download_date: datetime
    process_date: Optional[datetime] = None
    is_valid_negativation: bool = False
    negativation_mentions: int = 0
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True


class CaseDetail(Case):
    document: Optional[Dict[str, Any]] = None
    similar_cases: Optional[List[Dict[str, Any]]] = None
    analytics: Optional[Dict[str, Any]] = None


# Document Models
class DocumentBase(BaseModel):
    full_text: str
    summary: Optional[str] = None
    text_size: int
    language: str = "pt"


class Document(DocumentBase):
    id: str
    case_id: str
    processed: bool = False
    process_date: Optional[datetime] = None
    extracted_metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    
    class Config:
        orm_mode = True


# Analytics Models
class TrendRequest(BaseModel):
    days: int = Field(30, ge=1, le=365, description="Número de dias para análise")
    group_by: Optional[str] = Field(None, description="Agrupar por: chamber, county, month")


class TrendResponse(BaseModel):
    period_days: int
    start_date: datetime
    end_date: datetime
    compensation_trend: List[Dict[str, Any]]
    by_chamber: List[Dict[str, Any]]
    search_trend: List[Dict[str, Any]]


class CaseAnalytics(BaseModel):
    case_id: str
    case_number: str
    generated_at: datetime
    basic_info: Dict[str, Any]
    text_analysis: Optional[Dict[str, Any]] = None
    top_words: Optional[List[Dict[str, Any]]] = None
    similar_cases: Optional[List[Dict[str, Any]]] = None


# Admin Models
class TaskRequest(BaseModel):
    task_name: str = Field(..., description="Nome da task Celery")
    args: Optional[List[Any]] = Field(None, description="Argumentos da task")
    kwargs: Optional[Dict[str, Any]] = Field(None, description="Argumentos nomeados")
    
    class Config:
        schema_extra = {
            "example": {
                "task_name": "check_new_cases",
                "args": [["negativação indevida"], 50],
                "kwargs": {}
            }
        }


class TaskResponse(BaseModel):
    task_id: str
    task_name: str
    status: str
    submitted_at: datetime


# Pagination
class PaginationParams(BaseModel):
    skip: int = Field(0, ge=0, description="Número de registros para pular")
    limit: int = Field(20, ge=1, le=100, description="Número máximo de registros")


class PaginatedResponse(BaseModel):
    data: List[Any]
    total: int
    skip: int
    limit: int
    has_more: bool


# Error Models
class ErrorResponse(BaseModel):
    error: str
    message: str
    detail: Optional[str] = None
    path: Optional[str] = None