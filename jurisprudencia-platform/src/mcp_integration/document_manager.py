"""
MCP Document Manager - Gestão de documentos com MCPs
Funcionalidades EXTRAS que não interferem no sistema principal
"""

import os
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import hashlib

class MCPDocumentManager:
    """
    Gerenciador de documentos integrado com MCPs
    INDEPENDENTE do sistema principal - apenas funcionalidades extras
    """
    
    def __init__(self):
        # Usar pasta separada para não conflitar com sistema principal
        self.base_path = Path("data/mcp_documents")
        self.backup_path = Path("data/mcp_backups")
        self.organized_path = Path("data/documents/juridicos")
        
        self.ensure_directories()
        self.load_metadata()
    
    def ensure_directories(self):
        """Criar diretórios necessários"""
        for path in [self.base_path, self.backup_path, self.organized_path]:
            path.mkdir(parents=True, exist_ok=True)
            
        # Subpastas organizacionais
        for subdir in ['pdf', 'txt', 'temp', 'processed']:
            (self.base_path / subdir).mkdir(exist_ok=True)
    
    def load_metadata(self):
        """Carregar metadados dos documentos"""
        self.metadata_file = self.base_path / "metadata.json"
        
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    self.metadata = json.load(f)
            except:
                self.metadata = {}
        else:
            self.metadata = {}
    
    def save_metadata(self):
        """Salvar metadados"""
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, indent=2, ensure_ascii=False, default=str)
        except Exception as e:
            print(f"Erro ao salvar metadados: {e}")
    
    def upload_document(self, file_content: bytes, filename: str, file_type: str = None) -> Dict:
        """
        Upload de documento com organização automática
        """
        try:
            # Detectar tipo se não fornecido
            if not file_type:
                file_type = 'pdf' if filename.lower().endswith('.pdf') else 'txt'
            
            # Gerar ID único
            doc_id = hashlib.md5(f"{filename}{datetime.now()}".encode()).hexdigest()[:8]
            
            # Definir caminho baseado no tipo
            if file_type == 'pdf':
                target_path = self.base_path / 'pdf' / f"{doc_id}_{filename}"
            else:
                target_path = self.base_path / 'txt' / f"{doc_id}_{filename}"
            
            # Salvar arquivo
            with open(target_path, 'wb') as f:
                f.write(file_content)
            
            # Criar metadados
            metadata = {
                'id': doc_id,
                'original_name': filename,
                'type': file_type,
                'size': len(file_content),
                'upload_date': datetime.now(),
                'path': str(target_path),
                'status': 'uploaded',
                'tags': [],
                'category': self._detect_category(filename)
            }
            
            # Salvar metadados
            self.metadata[doc_id] = metadata
            self.save_metadata()
            
            # Tentar copiar para pasta principal (sem sobrescrever)
            self._safe_copy_to_main(target_path, filename)
            
            return {
                'success': True,
                'doc_id': doc_id,
                'message': f'Documento {filename} carregado com sucesso',
                'metadata': metadata
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'Erro ao carregar {filename}'
            }
    
    def _detect_category(self, filename: str) -> str:
        """Detectar categoria do documento"""
        filename_lower = filename.lower()
        
        if any(word in filename_lower for word in ['acordao', 'acórdão']):
            return 'acordao'
        elif any(word in filename_lower for word in ['sentenca', 'sentença']):
            return 'sentenca'
        elif any(word in filename_lower for word in ['decisao', 'decisão']):
            return 'decisao'
        elif any(word in filename_lower for word in ['recurso', 'apelacao']):
            return 'recurso'
        else:
            return 'outros'
    
    def _safe_copy_to_main(self, source_path: Path, original_name: str):
        """Copiar para pasta principal sem sobrescrever"""
        try:
            main_path = self.organized_path / original_name
            
            # Se arquivo já existe, criar versão numerada
            if main_path.exists():
                base_name = main_path.stem
                extension = main_path.suffix
                counter = 1
                
                while main_path.exists():
                    main_path = self.organized_path / f"{base_name}_{counter}{extension}"
                    counter += 1
            
            shutil.copy2(source_path, main_path)
            
        except Exception as e:
            print(f"Aviso: Não foi possível copiar para pasta principal: {e}")
    
    def list_documents(self, category: str = None, file_type: str = None) -> List[Dict]:
        """Listar documentos com filtros opcionais"""
        docs = []
        
        for doc_id, metadata in self.metadata.items():
            # Aplicar filtros
            if category and metadata.get('category') != category:
                continue
            if file_type and metadata.get('type') != file_type:
                continue
            
            # Verificar se arquivo ainda existe
            if not Path(metadata['path']).exists():
                continue
            
            docs.append({
                'id': doc_id,
                'name': metadata['original_name'],
                'category': metadata.get('category', 'outros'),
                'type': metadata['type'],
                'size': metadata['size'],
                'upload_date': metadata['upload_date'],
                'tags': metadata.get('tags', [])
            })
        
        # Ordenar por data de upload (mais recente primeiro)
        docs.sort(key=lambda x: x['upload_date'], reverse=True)
        return docs
    
    def get_document_content(self, doc_id: str) -> Optional[str]:
        """Obter conteúdo de um documento"""
        if doc_id not in self.metadata:
            return None
        
        file_path = Path(self.metadata[doc_id]['path'])
        if not file_path.exists():
            return None
        
        try:
            # Se for PDF, retornar caminho (processamento seria feito por outro módulo)
            if self.metadata[doc_id]['type'] == 'pdf':
                return f"PDF: {file_path}"
            
            # Se for texto, ler conteúdo
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
                
        except Exception as e:
            return f"Erro ao ler arquivo: {e}"
    
    def add_tags(self, doc_id: str, tags: List[str]) -> bool:
        """Adicionar tags a um documento"""
        if doc_id not in self.metadata:
            return False
        
        current_tags = set(self.metadata[doc_id].get('tags', []))
        current_tags.update(tags)
        
        self.metadata[doc_id]['tags'] = list(current_tags)
        self.save_metadata()
        return True
    
    def search_by_tags(self, tags: List[str]) -> List[Dict]:
        """Buscar documentos por tags"""
        results = []
        
        for doc_id, metadata in self.metadata.items():
            doc_tags = set(metadata.get('tags', []))
            
            # Verificar se alguma tag coincide
            if any(tag.lower() in ' '.join(doc_tags).lower() for tag in tags):
                results.append({
                    'id': doc_id,
                    'name': metadata['original_name'],
                    'tags': list(doc_tags),
                    'category': metadata.get('category', 'outros')
                })
        
        return results
    
    def create_backup(self) -> Dict:
        """Criar backup dos documentos importantes"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_folder = self.backup_path / f"backup_{timestamp}"
            backup_folder.mkdir(exist_ok=True)
            
            # Copiar documentos importantes (últimos 10)
            important_docs = self.list_documents()[:10]
            
            for doc in important_docs:
                doc_id = doc['id']
                metadata = self.metadata[doc_id]
                source_path = Path(metadata['path'])
                
                if source_path.exists():
                    target_path = backup_folder / source_path.name
                    shutil.copy2(source_path, target_path)
            
            # Copiar metadados
            shutil.copy2(self.metadata_file, backup_folder / "metadata.json")
            
            return {
                'success': True,
                'backup_path': str(backup_folder),
                'files_backed_up': len(important_docs),
                'message': f'Backup criado com {len(important_docs)} documentos'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Erro ao criar backup'
            }
    
    def get_statistics(self) -> Dict:
        """Obter estatísticas dos documentos"""
        docs = self.list_documents()
        
        stats = {
            'total_documents': len(docs),
            'by_category': {},
            'by_type': {},
            'total_size': 0,
            'recent_uploads': len([d for d in docs if isinstance(d['upload_date'], datetime) and 
                                 (datetime.now() - d['upload_date']).days <= 7])
        }
        
        for doc in docs:
            # Por categoria
            category = doc['category']
            stats['by_category'][category] = stats['by_category'].get(category, 0) + 1
            
            # Por tipo
            file_type = doc['type']
            stats['by_type'][file_type] = stats['by_type'].get(file_type, 0) + 1
            
            # Tamanho total
            stats['total_size'] += doc['size']
        
        return stats