"""
Tasks de processamento de PDFs para o pipeline Celery
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from celery import Task, group, chain
from src.pipeline.celery_app import app
from src.processing.pdf_processor import PDFProcessor
from src.database.database_manager import get_db_manager

logger = logging.getLogger(__name__)


class ProcessingTask(Task):
    """Classe base para tasks de processamento"""
    autoretry_for = (Exception,)
    retry_kwargs = {'max_retries': 3}
    retry_backoff = True


@app.task(base=ProcessingTask, bind=True)
def process_pdf(self, case_id: str):
    """
    Processa um PDF extraindo texto e metadados
    
    Args:
        case_id: ID do caso no banco
    """
    logger.info(f"Processando PDF do caso {case_id} - Task ID: {self.request.id}")
    
    db = get_db_manager()
    processor = PDFProcessor()
    
    try:
        # Buscar caso no banco
        with db.get_session() as session:
            case = session.query(db.Case).filter_by(id=case_id).first()
            if not case:
                raise ValueError(f"Caso {case_id} não encontrado")
            
            pdf_path = Path(case.pdf_path)
            if not pdf_path.exists():
                raise FileNotFoundError(f"PDF não encontrado: {pdf_path}")
        
        # Processar o PDF
        logger.info(f"Extraindo texto de: {pdf_path.name}")
        texto = processor.extract_text_from_pdf(pdf_path)
        
        if not texto or len(texto) < 100:
            raise ValueError("Texto extraído muito curto ou vazio")
        
        # Extrair metadados
        metadata = processor.extract_metadata(pdf_path, texto)
        
        # Criar documento no banco
        doc = db.create_document(
            case_id=case_id,
            text=texto,
            metadata=metadata
        )
        
        # Atualizar caso com metadados extraídos
        update_data = {
            'status': 'processed',
            'process_date': datetime.utcnow(),
            'is_valid_negativation': metadata.get('validado', False),
            'negativation_mentions': metadata.get('mencoes_negativacao', 0)
        }
        
        # Adicionar campos extraídos se disponíveis
        if metadata.get('relator'):
            update_data['judge_rapporteur'] = metadata['relator']
        if metadata.get('turma_camara'):
            update_data['chamber'] = metadata['turma_camara']
        if metadata.get('comarca'):
            update_data['county'] = metadata['comarca']
        if metadata.get('vara'):
            update_data['court_division'] = metadata['vara']
        
        # Extrair data de julgamento
        if metadata.get('data_julgamento'):
            try:
                for fmt in ['%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d']:
                    try:
                        update_data['judgment_date'] = datetime.strptime(
                            metadata['data_julgamento'], fmt
                        )
                        break
                    except:
                        continue
            except:
                pass
        
        # Extrair valor de indenização
        if metadata.get('valor_indenizacao'):
            try:
                valor_str = metadata['valor_indenizacao']
                valor_limpo = valor_str.replace('R$', '').replace('.', '').replace(',', '.').strip()
                update_data['compensation_amount'] = float(valor_limpo)
            except:
                pass
        
        # Categorizar caso
        if update_data.get('is_valid_negativation'):
            update_data['case_category'] = 'negativação indevida'
        
        db.update_case_status(case_id, 'processed', **update_data)
        
        # Agendar criação de chunks
        create_text_chunks.delay(str(doc.id), case_id)
        
        logger.info(f"PDF processado com sucesso: {case.case_number}")
        
        return {
            'status': 'success',
            'case_id': case_id,
            'document_id': str(doc.id),
            'text_size': len(texto),
            'is_valid': metadata.get('validado', False),
            'metadata': metadata
        }
        
    except Exception as e:
        logger.error(f"Erro ao processar caso {case_id}: {e}")
        db.update_case_status(case_id, 'error')
        raise


@app.task(base=ProcessingTask)
def create_text_chunks(document_id: str, case_id: str):
    """
    Cria chunks de texto para embeddings
    
    Args:
        document_id: ID do documento
        case_id: ID do caso
    """
    logger.info(f"Criando chunks para documento {document_id}")
    
    db = get_db_manager()
    
    try:
        # Buscar documento
        with db.get_session() as session:
            doc = session.query(db.Document).filter_by(id=document_id).first()
            if not doc:
                raise ValueError(f"Documento {document_id} não encontrado")
            
            texto = doc.full_text
        
        # Criar chunks (simples por enquanto - melhorar com langchain)
        chunk_size = 1000
        overlap = 200
        chunks = []
        
        for i in range(0, len(texto), chunk_size - overlap):
            chunk_text = texto[i:i + chunk_size]
            if len(chunk_text) > 100:  # Ignorar chunks muito pequenos
                chunks.append({
                    'text': chunk_text,
                    'start': i,
                    'end': i + len(chunk_text)
                })
        
        # Salvar chunks no banco
        chunk_objects = db.create_text_chunks(document_id, chunks)
        
        logger.info(f"Criados {len(chunk_objects)} chunks para documento {document_id}")
        
        # Agendar geração de embeddings
        for chunk in chunk_objects:
            generate_embedding.delay(str(chunk.id), case_id)
        
        return {
            'status': 'success',
            'document_id': document_id,
            'chunks_created': len(chunk_objects)
        }
        
    except Exception as e:
        logger.error(f"Erro ao criar chunks para documento {document_id}: {e}")
        raise


@app.task(base=ProcessingTask)
def process_pending_pdfs():
    """
    Processa todos os PDFs pendentes (executado periodicamente)
    """
    logger.info("Buscando PDFs pendentes para processar")
    
    db = get_db_manager()
    
    # Buscar casos com status 'downloaded'
    pending_cases = db.get_cases_to_process('downloaded', limit=10)
    
    if not pending_cases:
        logger.info("Nenhum PDF pendente encontrado")
        return {
            'status': 'no_pending',
            'count': 0
        }
    
    logger.info(f"Encontrados {len(pending_cases)} PDFs para processar")
    
    # Criar grupo de tasks
    job = group(
        process_pdf.s(str(case.id)) for case in pending_cases
    )
    
    # Executar em paralelo
    result = job.apply_async()
    
    return {
        'status': 'processing',
        'count': len(pending_cases),
        'group_id': result.id
    }


@app.task
def validate_processed_documents():
    """
    Valida documentos processados e marca casos inválidos
    """
    logger.info("Validando documentos processados")
    
    db = get_db_manager()
    
    with db.get_session() as session:
        # Buscar documentos não validados
        invalid_docs = session.query(db.Document).join(db.Case).filter(
            db.Case.is_valid_negativation == False,
            db.Case.status == 'processed'
        ).limit(100).all()
        
        validated = 0
        for doc in invalid_docs:
            # Re-validar com critérios mais flexíveis
            texto_lower = doc.full_text.lower()
            keywords = ['negativ', 'serasa', 'spc', 'inadimplente', 'restri']
            
            if any(keyword in texto_lower for keyword in keywords):
                doc.case.is_valid_negativation = True
                doc.case.case_category = 'negativação indevida'
                validated += 1
        
        session.commit()
    
    logger.info(f"Validados {validated} documentos adicionais")
    
    return {
        'status': 'completed',
        'validated_count': validated
    }


# Importar task de embedding para evitar importação circular
from .embedding import generate_embedding