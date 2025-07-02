"""
Processador de PDFs com preview melhorado
Funcionalidade EXTRA opcional para PDFs
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import base64

class PDFProcessor:
    """
    Processador de PDFs com funcionalidades extras
    Opcional - só funciona se PyPDF2 estiver instalado
    """
    
    def __init__(self):
        self.pdf_available = self._check_pdf_support()
        self.cache_dir = Path("data/pdf_cache")
        self.cache_dir.mkdir(exist_ok=True)
    
    def _check_pdf_support(self) -> bool:
        """Verificar se bibliotecas PDF estão disponíveis"""
        try:
            import PyPDF2
            return True
        except ImportError:
            return False
    
    def extract_text_simple(self, pdf_path: Path) -> Dict:
        """Extração simples de texto de PDF"""
        if not self.pdf_available:
            return {
                'success': False,
                'error': 'PyPDF2 não instalado',
                'message': 'Execute: pip install PyPDF2'
            }
        
        try:
            import PyPDF2
            
            text_content = []
            metadata = {}
            
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                # Metadados
                metadata = {
                    'pages': len(pdf_reader.pages),
                    'title': pdf_reader.metadata.get('/Title', '') if pdf_reader.metadata else '',
                    'author': pdf_reader.metadata.get('/Author', '') if pdf_reader.metadata else '',
                    'size': pdf_path.stat().st_size
                }
                
                # Extrair texto de cada página
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text.strip():
                            text_content.append({
                                'page': page_num + 1,
                                'text': page_text.strip()
                            })
                    except Exception as e:
                        text_content.append({
                            'page': page_num + 1,
                            'text': f'[Erro na página {page_num + 1}: {str(e)}]'
                        })
            
            return {
                'success': True,
                'metadata': metadata,
                'text_content': text_content,
                'total_text': '\n\n'.join([p['text'] for p in text_content])
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'Erro ao processar PDF: {str(e)}'
            }
    
    def get_pdf_preview(self, pdf_path: Path, max_chars: int = 2000) -> Dict:
        """Obter preview do PDF com metadados"""
        result = self.extract_text_simple(pdf_path)
        
        if not result['success']:
            return result
        
        # Criar preview
        preview_text = result['total_text'][:max_chars]
        if len(result['total_text']) > max_chars:
            preview_text += "\n\n[... texto truncado ...]"
        
        return {
            'success': True,
            'preview': preview_text,
            'metadata': result['metadata'],
            'has_more': len(result['total_text']) > max_chars,
            'total_length': len(result['total_text'])
        }
    
    def search_in_pdf(self, pdf_path: Path, search_term: str) -> Dict:
        """Buscar termo específico no PDF"""
        result = self.extract_text_simple(pdf_path)
        
        if not result['success']:
            return result
        
        matches = []
        search_term_lower = search_term.lower()
        
        for page_data in result['text_content']:
            page_text = page_data['text']
            page_text_lower = page_text.lower()
            
            if search_term_lower in page_text_lower:
                # Encontrar contexto ao redor da palavra
                pos = page_text_lower.find(search_term_lower)
                start = max(0, pos - 100)
                end = min(len(page_text), pos + len(search_term) + 100)
                context = page_text[start:end]
                
                matches.append({
                    'page': page_data['page'],
                    'context': context,
                    'position': pos
                })
        
        return {
            'success': True,
            'search_term': search_term,
            'matches_found': len(matches),
            'matches': matches
        }
    
    def extract_legal_info(self, pdf_path: Path) -> Dict:
        """Extrair informações jurídicas específicas"""
        result = self.extract_text_simple(pdf_path)
        
        if not result['success']:
            return result
        
        text = result['total_text']
        
        legal_info = {
            'numeros_processo': self._extract_process_numbers(text),
            'valores_monetarios': self._extract_monetary_values(text),
            'datas_importantes': self._extract_dates(text),
            'partes_processo': self._extract_parties(text),
            'termos_juridicos': self._extract_legal_terms(text)
        }
        
        return {
            'success': True,
            'legal_info': legal_info,
            'metadata': result['metadata']
        }
    
    def _extract_process_numbers(self, text: str) -> List[str]:
        """Extrair números de processo"""
        import re
        
        patterns = [
            r'\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}',  # Formato CNJ
            r'\d{7}-\d{2}\.\d{4}\.\d{1}\.\d{2}\.\d{4}',  # Variação
            r'\d{4}\.\d{3}\.\d{3}-\d{1}',  # Formato mais antigo
        ]
        
        numbers = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            numbers.extend(matches)
        
        return list(set(numbers))  # Remover duplicatas
    
    def _extract_monetary_values(self, text: str) -> List[str]:
        """Extrair valores monetários"""
        import re
        
        patterns = [
            r'R\$\s?[\d.,]+',
            r'reais?\s+de\s+R\$\s?[\d.,]+',
            r'valor\s+de\s+R\$\s?[\d.,]+',
        ]
        
        values = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            values.extend(matches)
        
        return list(set(values))
    
    def _extract_dates(self, text: str) -> List[str]:
        """Extrair datas importantes"""
        import re
        
        patterns = [
            r'\d{1,2}[/.-]\d{1,2}[/.-]\d{4}',
            r'\d{1,2}\s+de\s+\w+\s+de\s+\d{4}',
        ]
        
        dates = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            dates.extend(matches)
        
        return list(set(dates))
    
    def _extract_parties(self, text: str) -> Dict[str, List[str]]:
        """Extrair partes do processo"""
        import re
        
        parties = {'autores': [], 'reus': []}
        
        # Buscar padrões típicos
        autor_patterns = [
            r'(?:Autor|Requerente|Apelante):\s*([^\n,]+)',
            r'([^,\n]+)\s*(?:autor|requerente)',
        ]
        
        reu_patterns = [
            r'(?:Réu|Requerido|Apelado):\s*([^\n,]+)',
            r'([^,\n]+)\s*(?:réu|requerido)',
        ]
        
        for pattern in autor_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            parties['autores'].extend([m.strip() for m in matches])
        
        for pattern in reu_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            parties['reus'].extend([m.strip() for m in matches])
        
        return parties
    
    def _extract_legal_terms(self, text: str) -> List[str]:
        """Extrair termos jurídicos relevantes"""
        terms = [
            'dano moral', 'dano material', 'indenização', 'responsabilidade civil',
            'nexo causal', 'culpa', 'dolo', 'boa-fé', 'má-fé',
            'código de defesa do consumidor', 'cdc', 'direito do consumidor',
            'negativação', 'serasa', 'spc', 'cadastro de inadimplentes',
            'juros', 'correção monetária', 'honorários advocatícios'
        ]
        
        found_terms = []
        text_lower = text.lower()
        
        for term in terms:
            if term.lower() in text_lower:
                found_terms.append(term)
        
        return found_terms
    
    def convert_pdf_to_text_file(self, pdf_path: Path, output_dir: Path = None) -> Dict:
        """Converter PDF para arquivo de texto"""
        if not output_dir:
            output_dir = self.cache_dir
        
        result = self.extract_text_simple(pdf_path)
        
        if not result['success']:
            return result
        
        try:
            # Definir arquivo de saída
            output_file = output_dir / f"{pdf_path.stem}.txt"
            
            # Escrever texto
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"# Texto extraído de: {pdf_path.name}\n")
                f.write(f"# Páginas: {result['metadata']['pages']}\n")
                f.write(f"# Data de extração: {result.get('extraction_date', 'N/A')}\n\n")
                f.write(result['total_text'])
            
            return {
                'success': True,
                'output_file': str(output_file),
                'original_pdf': str(pdf_path),
                'text_length': len(result['total_text'])
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Erro ao salvar arquivo de texto'
            }
    
    def get_installation_instructions(self) -> str:
        """Instruções para instalar suporte a PDF"""
        if self.pdf_available:
            return "✅ Suporte a PDF já está disponível!"
        
        return """
        📥 Para ativar o suporte completo a PDFs, execute:
        
        pip install PyPDF2
        
        Funcionalidades disponíveis após instalação:
        • Extração de texto de PDFs
        • Busca dentro de PDFs  
        • Conversão PDF → TXT
        • Extração de metadados
        • Identificação de informações jurídicas
        """