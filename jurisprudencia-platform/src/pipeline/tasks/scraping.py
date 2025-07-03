"""
Tasks de scraping para o pipeline Celery
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict
import hashlib

from celery import Task
from ..celery_app import app
from ...scraper.tjsp_scraper import SimpleTJSPScraper
from ...database.database_manager import get_db_manager

logger = logging.getLogger(__name__)


class ScrapingTask(Task):
    """Classe base para tasks de scraping com rate limiting"""
    autoretry_for = (Exception,)
    retry_kwargs = {'max_retries': 3}
    retry_backoff = True
    retry_backoff_max = 600  # 10 minutos
    retry_jitter = True


@app.task(base=ScrapingTask, bind=True)
def check_new_cases(self, search_terms: List[str] = None, max_results: int = 50):
    """
    Verifica por novos casos no TJSP
    
    Args:
        search_terms: Termos de busca (default: negativação indevida)
        max_results: Número máximo de resultados
    """
    logger.info(f"Iniciando busca por novos casos - Task ID: {self.request.id}")
    
    if not search_terms:
        search_terms = [
            "negativação indevida",
            "inscrição indevida serasa",
            "cadastro inadimplentes indevido",
            "danos morais negativação"
        ]
    
    db = get_db_manager()
    scraper = SimpleTJSPScraper()
    
    new_cases = []
    
    for term in search_terms:
        try:
            # Buscar casos recentes (últimos 7 dias)
            logger.info(f"Buscando por: {term}")
            
            # Por enquanto, usar lista hardcoded
            # TODO: Implementar busca real quando tivermos Selenium
            sample_cases = [
                {
                    'numero': '1234567-89.2024.8.26.0100',
                    'url': 'https://esaj.tjsp.jus.br/cjsg/getArquivo.do?cdAcordao=17584819&cdForo=0',
                    'relator': 'Des. João Silva',
                    'data': '15/02/2024'
                }
            ]
            
            for case_info in sample_cases:
                # Verificar se já existe
                if not db.case_exists(case_info['numero']):
                    # Agendar download do PDF
                    download_case_pdf.delay(case_info)
                    new_cases.append(case_info['numero'])
                    logger.info(f"Novo caso encontrado: {case_info['numero']}")
            
        except Exception as e:
            logger.error(f"Erro ao buscar termo '{term}': {e}")
    
    logger.info(f"Busca concluída. {len(new_cases)} novos casos encontrados")
    
    # Enviar notificação se houver novos casos
    if new_cases:
        send_notification.delay(
            f"Novos casos encontrados: {len(new_cases)}",
            new_cases
        )
    
    return {
        'task_id': self.request.id,
        'timestamp': datetime.utcnow().isoformat(),
        'new_cases_count': len(new_cases),
        'new_cases': new_cases
    }


@app.task(base=ScrapingTask, bind=True)
def download_case_pdf(self, case_info: Dict):
    """
    Baixa o PDF de um caso específico
    
    Args:
        case_info: Dicionário com informações do caso
    """
    logger.info(f"Baixando PDF do caso {case_info['numero']} - Task ID: {self.request.id}")
    
    db = get_db_manager()
    scraper = SimpleTJSPScraper()
    
    try:
        # Criar registro do caso no banco
        case_data = {
            'case_number': case_info['numero'],
            'pdf_url': case_info['url'],
            'judge_rapporteur': case_info.get('relator'),
            'status': 'downloading'
        }
        
        case = db.create_case(case_data)
        
        # Baixar o PDF
        filename = f"acordao_{case_info['numero'].replace('.', '_').replace('-', '_')}.pdf"
        result = scraper.download_single_pdf(case_info['url'], filename)
        
        if result['status'] == 'sucesso':
            # Atualizar caso com informações do download
            db.update_case_status(
                case.id,
                'downloaded',
                pdf_path=result['caminho'],
                pdf_size=result['tamanho'],
                download_date=datetime.utcnow()
            )
            
            # Agendar processamento do PDF
            process_pdf.delay(str(case.id))
            
            logger.info(f"PDF baixado com sucesso: {filename}")
            return {
                'status': 'success',
                'case_id': str(case.id),
                'filename': filename,
                'size': result['tamanho']
            }
        else:
            # Marcar como erro
            db.update_case_status(case.id, 'error')
            raise Exception(f"Erro ao baixar PDF: {result['motivo']}")
            
    except Exception as e:
        logger.error(f"Erro ao baixar caso {case_info['numero']}: {e}")
        raise


@app.task(base=ScrapingTask)
def scrape_case_details(case_id: str):
    """
    Extrai detalhes adicionais de um caso (quando tivermos Selenium)
    
    Args:
        case_id: ID do caso no banco
    """
    logger.info(f"Extraindo detalhes do caso {case_id}")
    
    # TODO: Implementar quando tivermos Selenium
    # Por enquanto, apenas retornar sucesso
    
    return {
        'status': 'pending_implementation',
        'case_id': case_id
    }


@app.task
def send_notification(subject: str, content: any):
    """
    Envia notificação sobre novos casos
    
    Args:
        subject: Assunto da notificação
        content: Conteúdo da notificação
    """
    logger.info(f"Notificação: {subject}")
    
    # TODO: Implementar envio real (email, webhook, etc.)
    # Por enquanto, apenas logar
    
    return {
        'status': 'logged',
        'subject': subject,
        'timestamp': datetime.utcnow().isoformat()
    }


# Importar task de processamento para evitar importação circular
from .processing import process_pdf