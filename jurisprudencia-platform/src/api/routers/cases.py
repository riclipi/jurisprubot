"""
Router para endpoints de casos
CRUD e operações com casos individuais
"""

from fastapi import APIRouter, HTTPException, Query, Depends, Path
from typing import List, Optional
import logging
from datetime import datetime

from ..models import Case, CaseDetail, CaseCreate, CaseUpdate, PaginatedResponse
from ...database.database_manager import get_db_manager

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_model=PaginatedResponse)
async def list_cases(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    category: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    order_by: str = Query("judgment_date", regex="^(judgment_date|created_at|compensation_amount)$"),
    order_dir: str = Query("desc", regex="^(asc|desc)$")
):
    """
    Lista casos com paginação e filtros
    """
    try:
        db = get_db_manager()
        
        with db.get_session() as session:
            query = session.query(db.Case)
            
            # Aplicar filtros
            if status:
                query = query.filter(db.Case.status == status)
            if category:
                query = query.filter(db.Case.case_category == category)
            if date_from:
                query = query.filter(db.Case.judgment_date >= date_from)
            if date_to:
                query = query.filter(db.Case.judgment_date <= date_to)
            
            # Total antes da paginação
            total = query.count()
            
            # Ordenação
            order_field = getattr(db.Case, order_by)
            if order_dir == "desc":
                query = query.order_by(order_field.desc())
            else:
                query = query.order_by(order_field.asc())
            
            # Paginação
            cases = query.offset(skip).limit(limit).all()
            
            # Converter para Pydantic
            cases_data = [Case.from_orm(case) for case in cases]
            
            return PaginatedResponse(
                data=cases_data,
                total=total,
                skip=skip,
                limit=limit,
                has_more=(skip + limit) < total
            )
            
    except Exception as e:
        logger.error(f"Erro ao listar casos: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{case_id}", response_model=CaseDetail)
async def get_case(
    case_id: str = Path(..., description="ID do caso")
):
    """
    Retorna detalhes completos de um caso
    """
    try:
        db = get_db_manager()
        
        with db.get_session() as session:
            # Buscar caso
            case = session.query(db.Case).filter_by(id=case_id).first()
            if not case:
                raise HTTPException(status_code=404, detail="Caso não encontrado")
            
            # Buscar documento
            document = session.query(db.Document).filter_by(case_id=case_id).first()
            
            # Converter para dict
            case_dict = Case.from_orm(case).dict()
            
            # Adicionar documento se existir
            if document:
                case_dict['document'] = {
                    'id': str(document.id),
                    'text_size': document.text_size,
                    'summary': document.summary,
                    'processed': document.processed,
                    'extracted_metadata': document.extracted_metadata
                }
            
            # Buscar casos similares
            similar = session.query(db.Case).filter(
                db.Case.id != case_id,
                db.Case.chamber == case.chamber,
                db.Case.case_category == case.case_category
            ).limit(5).all()
            
            case_dict['similar_cases'] = [
                {
                    'id': str(c.id),
                    'case_number': c.case_number,
                    'judge': c.judge_rapporteur,
                    'compensation_amount': float(c.compensation_amount) if c.compensation_amount else None,
                    'judgment_date': c.judgment_date.isoformat() if c.judgment_date else None
                }
                for c in similar
            ]
            
            return CaseDetail(**case_dict)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao buscar caso {case_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=Case)
async def create_case(
    case_data: CaseCreate
):
    """
    Cria um novo caso (usado pelo pipeline)
    """
    try:
        db = get_db_manager()
        
        # Verificar se já existe
        if db.case_exists(case_data.case_number):
            raise HTTPException(
                status_code=409,
                detail=f"Caso {case_data.case_number} já existe"
            )
        
        # Criar caso
        case = db.create_case(case_data.dict())
        
        return Case.from_orm(case)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao criar caso: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{case_id}", response_model=Case)
async def update_case(
    case_id: str,
    updates: CaseUpdate
):
    """
    Atualiza dados de um caso
    """
    try:
        db = get_db_manager()
        
        with db.get_session() as session:
            case = session.query(db.Case).filter_by(id=case_id).first()
            if not case:
                raise HTTPException(status_code=404, detail="Caso não encontrado")
            
            # Aplicar atualizações
            update_data = updates.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(case, field, value)
            
            case.updated_at = datetime.utcnow()
            session.commit()
            
            return Case.from_orm(case)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao atualizar caso {case_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{case_id}")
async def delete_case(
    case_id: str
):
    """
    Remove um caso e todos os dados relacionados
    """
    try:
        db = get_db_manager()
        
        with db.get_session() as session:
            case = session.query(db.Case).filter_by(id=case_id).first()
            if not case:
                raise HTTPException(status_code=404, detail="Caso não encontrado")
            
            # Deletar (cascata remove documentos, chunks e embeddings)
            session.delete(case)
            session.commit()
            
            return {
                "success": True,
                "message": f"Caso {case.case_number} removido com sucesso"
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao deletar caso {case_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{case_id}/document")
async def get_case_document(
    case_id: str
):
    """
    Retorna o texto completo do documento do caso
    """
    try:
        db = get_db_manager()
        
        with db.get_session() as session:
            document = session.query(db.Document).filter_by(case_id=case_id).first()
            if not document:
                raise HTTPException(status_code=404, detail="Documento não encontrado")
            
            return {
                "case_id": case_id,
                "document_id": str(document.id),
                "full_text": document.full_text,
                "text_size": document.text_size,
                "summary": document.summary,
                "extracted_metadata": document.extracted_metadata
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao buscar documento: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{case_id}/reprocess")
async def reprocess_case(
    case_id: str
):
    """
    Agenda reprocessamento de um caso
    """
    try:
        from ...pipeline.tasks.processing import process_pdf
        
        db = get_db_manager()
        
        # Verificar se caso existe
        with db.get_session() as session:
            case = session.query(db.Case).filter_by(id=case_id).first()
            if not case:
                raise HTTPException(status_code=404, detail="Caso não encontrado")
            
            if not case.pdf_path:
                raise HTTPException(
                    status_code=400,
                    detail="Caso não tem PDF associado"
                )
        
        # Agendar reprocessamento
        task = process_pdf.delay(case_id)
        
        # Atualizar status
        db.update_case_status(case_id, 'processing')
        
        return {
            "success": True,
            "message": "Reprocessamento agendado",
            "task_id": task.id,
            "case_number": case.case_number
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao agendar reprocessamento: {e}")
        raise HTTPException(status_code=500, detail=str(e))