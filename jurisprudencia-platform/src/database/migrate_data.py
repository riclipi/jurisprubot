"""
Script para migrar dados processados para o PostgreSQL
Lê os JSONs e textos já extraídos e popula o banco
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List

from database_manager import get_db_manager
from models import Case, Document

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataMigrator:
    """Migra dados existentes para PostgreSQL"""
    
    def __init__(self, processed_dir: str = 'data/processed'):
        self.processed_dir = Path(processed_dir)
        self.text_dir = self.processed_dir / 'texts'
        self.metadata_dir = self.processed_dir / 'metadata'
        self.db = get_db_manager()
        
        # Estatísticas
        self.stats = {
            'total_files': 0,
            'migrated': 0,
            'skipped': 0,
            'errors': 0
        }
    
    def migrate_all(self):
        """Migra todos os dados processados para o banco"""
        logger.info("Iniciando migração de dados para PostgreSQL")
        
        # Listar todos os arquivos de metadados
        metadata_files = list(self.metadata_dir.glob('*_metadata.json'))
        self.stats['total_files'] = len(metadata_files)
        
        logger.info(f"Encontrados {len(metadata_files)} arquivos para migrar")
        
        for metadata_file in metadata_files:
            try:
                self._migrate_single_case(metadata_file)
            except Exception as e:
                logger.error(f"Erro ao migrar {metadata_file.name}: {e}")
                self.stats['errors'] += 1
        
        # Relatório final
        logger.info("="*60)
        logger.info("MIGRAÇÃO CONCLUÍDA")
        logger.info(f"Total de arquivos: {self.stats['total_files']}")
        logger.info(f"Migrados com sucesso: {self.stats['migrated']}")
        logger.info(f"Ignorados (já existem): {self.stats['skipped']}")
        logger.info(f"Erros: {self.stats['errors']}")
        logger.info("="*60)
    
    def _migrate_single_case(self, metadata_file: Path):
        """Migra um único caso para o banco"""
        # Ler metadados
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        # Extrair número do processo
        case_number = metadata.get('numero_processo')
        if not case_number:
            logger.warning(f"Sem número de processo em {metadata_file.name}")
            self.stats['errors'] += 1
            return
        
        # Verificar se já existe
        if self.db.case_exists(case_number):
            logger.debug(f"Caso {case_number} já existe no banco")
            self.stats['skipped'] += 1
            return
        
        # Preparar dados do caso
        case_data = {
            'case_number': case_number,
            'judge_rapporteur': metadata.get('relator'),
            'chamber': metadata.get('turma_camara'),
            'county': metadata.get('comarca'),
            'court_division': metadata.get('vara'),
            'pdf_path': metadata.get('caminho'),
            'pdf_size': metadata.get('tamanho_bytes'),
            'pdf_pages': metadata.get('numero_paginas'),
            'status': 'processed',
            'is_valid_negativation': metadata.get('validado', False),
            'negativation_mentions': metadata.get('mencoes_negativacao', 0),
            'process_date': datetime.utcnow()
        }
        
        # Extrair data de julgamento
        data_str = metadata.get('data_julgamento')
        if data_str:
            try:
                # Tentar diferentes formatos
                for fmt in ['%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d']:
                    try:
                        case_data['judgment_date'] = datetime.strptime(data_str, fmt)
                        break
                    except:
                        continue
            except Exception as e:
                logger.warning(f"Erro ao parsear data {data_str}: {e}")
        
        # Extrair valor de indenização
        valor_str = metadata.get('valor_indenizacao')
        if valor_str:
            try:
                # Remover R$ e converter vírgula para ponto
                valor_limpo = valor_str.replace('R$', '').replace('.', '').replace(',', '.').strip()
                case_data['compensation_amount'] = float(valor_limpo)
            except:
                logger.warning(f"Erro ao parsear valor {valor_str}")
        
        # Categorizar caso
        if case_data['is_valid_negativation']:
            case_data['case_category'] = 'negativação indevida'
        
        # Criar caso no banco
        case = self.db.create_case(case_data)
        logger.info(f"Caso criado: {case_number}")
        
        # Ler e adicionar texto do documento
        texto_file = self.text_dir / metadata['arquivo'].replace('.pdf', '.txt')
        if texto_file.exists():
            with open(texto_file, 'r', encoding='utf-8') as f:
                texto = f.read()
            
            # Criar documento
            doc_metadata = {
                'pdf_metadata': metadata.get('pdf_metadata', {}),
                'resumo': metadata.get('resumo', '')
            }
            
            document = self.db.create_document(
                case_id=case.id,
                text=texto,
                metadata=doc_metadata
            )
            logger.info(f"Documento criado para caso {case_number}")
        
        self.stats['migrated'] += 1
    
    def verify_migration(self):
        """Verifica integridade da migração"""
        stats = self.db.get_statistics()
        
        print("\nESTATÍSTICAS DO BANCO:")
        print(f"Total de casos: {stats['total_cases']}")
        print(f"Casos processados: {stats['processed_cases']}")
        print(f"Total de documentos: {stats['total_documents']}")
        
        if stats['by_category']:
            print("\nPor categoria:")
            for cat, count in stats['by_category'].items():
                print(f"  - {cat}: {count}")
        
        if stats['avg_compensation'] > 0:
            print(f"\nMédia de indenizações: R$ {stats['avg_compensation']:,.2f}")


def main():
    """Executa a migração"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Migra dados para PostgreSQL')
    parser.add_argument('--verify', action='store_true', help='Apenas verifica estatísticas')
    parser.add_argument('--processed-dir', default='data/processed', help='Diretório dos dados processados')
    
    args = parser.parse_args()
    
    migrator = DataMigrator(args.processed_dir)
    
    if args.verify:
        migrator.verify_migration()
    else:
        migrator.migrate_all()
        print("\nVerificando migração...")
        migrator.verify_migration()


if __name__ == "__main__":
    main()