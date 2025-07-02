"""
Organizador automático de arquivos
Funcionalidade EXTRA para organizar documentos por categorias
"""

import os
import shutil
from pathlib import Path
from typing import Dict, List
import re
from datetime import datetime

class FileOrganizer:
    """
    Organizador automático de arquivos jurídicos
    Não interfere com o sistema principal
    """
    
    def __init__(self, source_dir: str = "data/documents/juridicos"):
        self.source_dir = Path(source_dir)
        self.organized_dir = Path("data/mcp_organized")
        self.setup_structure()
    
    def setup_structure(self):
        """Criar estrutura organizacional"""
        categories = [
            'acordaos',
            'sentencas', 
            'decisoes',
            'recursos',
            'contratos',
            'peticoes',
            'outros'
        ]
        
        for category in categories:
            (self.organized_dir / category).mkdir(parents=True, exist_ok=True)
            
        # Subpastas por ano
        current_year = datetime.now().year
        for year in range(current_year - 2, current_year + 1):
            for category in categories:
                (self.organized_dir / category / str(year)).mkdir(exist_ok=True)
    
    def classify_document(self, filename: str, content: str = None) -> str:
        """Classificar documento automaticamente"""
        filename_lower = filename.lower()
        content_lower = content.lower() if content else ""
        
        # Regras de classificação
        if any(word in filename_lower for word in ['acordao', 'acórdão']) or \
           any(word in content_lower for word in ['acórdão', 'recurso de apelação']):
            return 'acordaos'
        
        elif any(word in filename_lower for word in ['sentenca', 'sentença']) or \
             any(word in content_lower for word in ['sentença', 'dispositivo', 'julgo']):
            return 'sentencas'
        
        elif any(word in filename_lower for word in ['decisao', 'decisão']) or \
             any(word in content_lower for word in ['decisão', 'defiro', 'indefiro']):
            return 'decisoes'
        
        elif any(word in filename_lower for word in ['recurso', 'apelacao', 'embargos']) or \
             any(word in content_lower for word in ['recurso', 'apelação', 'embargos']):
            return 'recursos'
        
        elif any(word in filename_lower for word in ['contrato', 'convenio']) or \
             any(word in content_lower for word in ['contrato', 'cláusula']):
            return 'contratos'
        
        elif any(word in filename_lower for word in ['peticao', 'petição', 'inicial']) or \
             any(word in content_lower for word in ['petição', 'requer', 'vem respeitosamente']):
            return 'peticoes'
        
        return 'outros'
    
    def extract_year(self, filename: str, content: str = None) -> int:
        """Extrair ano do documento"""
        current_year = datetime.now().year
        
        # Buscar no nome do arquivo
        year_matches = re.findall(r'20\d{2}', filename)
        if year_matches:
            return int(year_matches[-1])  # Último ano encontrado
        
        # Buscar no conteúdo
        if content:
            year_matches = re.findall(r'20\d{2}', content[:500])  # Primeiros 500 chars
            if year_matches:
                return int(year_matches[-1])
        
        return current_year
    
    def organize_file(self, file_path: Path, copy_mode: bool = True) -> Dict:
        """Organizar um arquivo específico"""
        try:
            if not file_path.exists():
                return {'success': False, 'error': 'Arquivo não existe'}
            
            # Ler conteúdo se for texto
            content = ""
            if file_path.suffix.lower() == '.txt':
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                except:
                    pass
            
            # Classificar e extrair ano
            category = self.classify_document(file_path.name, content)
            year = self.extract_year(file_path.name, content)
            
            # Definir destino
            target_dir = self.organized_dir / category / str(year)
            target_path = target_dir / file_path.name
            
            # Evitar conflitos de nome
            counter = 1
            original_target = target_path
            while target_path.exists():
                name_parts = original_target.stem, counter, original_target.suffix
                target_path = target_dir / f"{name_parts[0]}_{name_parts[1]}{name_parts[2]}"
                counter += 1
            
            # Copiar ou mover arquivo
            if copy_mode:
                shutil.copy2(file_path, target_path)
                action = "copiado"
            else:
                shutil.move(str(file_path), str(target_path))
                action = "movido"
            
            return {
                'success': True,
                'action': action,
                'category': category,
                'year': year,
                'source': str(file_path),
                'target': str(target_path)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'source': str(file_path)
            }
    
    def organize_directory(self, copy_mode: bool = True) -> Dict:
        """Organizar todos os arquivos do diretório fonte"""
        results = {
            'total_files': 0,
            'organized': 0,
            'errors': 0,
            'by_category': {},
            'error_details': []
        }
        
        # Processar todos os arquivos
        for file_path in self.source_dir.glob('**/*'):
            if file_path.is_file() and file_path.suffix.lower() in ['.txt', '.pdf']:
                results['total_files'] += 1
                
                result = self.organize_file(file_path, copy_mode)
                
                if result['success']:
                    results['organized'] += 1
                    category = result['category']
                    results['by_category'][category] = results['by_category'].get(category, 0) + 1
                else:
                    results['errors'] += 1
                    results['error_details'].append(result)
        
        return results
    
    def get_organization_preview(self) -> Dict:
        """Preview da organização sem executar"""
        preview = {
            'files_to_organize': 0,
            'by_category': {},
            'by_year': {},
            'file_details': []
        }
        
        for file_path in self.source_dir.glob('**/*'):
            if file_path.is_file() and file_path.suffix.lower() in ['.txt', '.pdf']:
                preview['files_to_organize'] += 1
                
                # Ler conteúdo se for texto (só para preview)
                content = ""
                if file_path.suffix.lower() == '.txt':
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()[:1000]  # Só primeiros 1000 chars
                    except:
                        pass
                
                category = self.classify_document(file_path.name, content)
                year = self.extract_year(file_path.name, content)
                
                # Estatísticas
                preview['by_category'][category] = preview['by_category'].get(category, 0) + 1
                preview['by_year'][year] = preview['by_year'].get(year, 0) + 1
                
                # Detalhes do arquivo
                preview['file_details'].append({
                    'name': file_path.name,
                    'category': category,
                    'year': year,
                    'size': file_path.stat().st_size
                })
        
        return preview
    
    def clean_empty_folders(self):
        """Limpar pastas vazias na organização"""
        cleaned = []
        
        for root, dirs, files in os.walk(self.organized_dir, topdown=False):
            for dir_name in dirs:
                dir_path = Path(root) / dir_name
                try:
                    if not any(dir_path.iterdir()):  # Pasta vazia
                        dir_path.rmdir()
                        cleaned.append(str(dir_path))
                except:
                    pass
        
        return cleaned
    
    def get_organization_stats(self) -> Dict:
        """Estatísticas da organização atual"""
        stats = {
            'total_organized': 0,
            'by_category': {},
            'by_year': {},
            'largest_files': []
        }
        
        # Processar arquivos organizados
        for file_path in self.organized_dir.glob('**/*'):
            if file_path.is_file():
                stats['total_organized'] += 1
                
                # Categoria (pasta pai)
                category = file_path.parent.parent.name
                stats['by_category'][category] = stats['by_category'].get(category, 0) + 1
                
                # Ano (pasta atual)
                try:
                    year = int(file_path.parent.name)
                    stats['by_year'][year] = stats['by_year'].get(year, 0) + 1
                except:
                    pass
                
                # Arquivos grandes
                size = file_path.stat().st_size
                stats['largest_files'].append({
                    'name': file_path.name,
                    'size': size,
                    'category': category
                })
        
        # Ordenar por tamanho
        stats['largest_files'].sort(key=lambda x: x['size'], reverse=True)
        stats['largest_files'] = stats['largest_files'][:10]  # Top 10
        
        return stats