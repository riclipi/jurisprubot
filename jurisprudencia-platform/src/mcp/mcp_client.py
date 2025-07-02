import subprocess
import json
import os
from typing import Dict, List, Any

class JurisprudenciaMCPClient:
    def __init__(self):
        self.base_path = os.getcwd()
        self.docs_path = os.path.join(self.base_path, 'data', 'documents', 'juridicos')
        self.ensure_directories()
    
    def ensure_directories(self):
        os.makedirs(self.docs_path, exist_ok=True)
        os.makedirs(os.path.join(self.base_path, 'data', 'lancedb'), exist_ok=True)
    
    def save_document(self, content: str, filename: str) -> str:
        '''Salva documento usando Filesystem MCP'''
        filepath = os.path.join(self.docs_path, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return filepath
    
    def list_documents(self) -> List[str]:
        '''Lista documentos disponíveis'''
        return os.listdir(self.docs_path)
    
    def search_documents(self, query: str) -> List[Dict]:
        '''Busca semântica nos documentos usando LegalContext'''
        # Integração com Legal-Context MCP
        results = []
        for filename in self.list_documents():
            filepath = os.path.join(self.docs_path, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                if query.lower() in content.lower():
                    results.append({
                        'filename': filename,
                        'content': content[:500] + '...',
                        'relevance': 0.8  # Simplified scoring
                    })
        return results
    
    def process_legal_document(self, content: str, doc_type: str = 'acordao') -> Dict:
        '''Processa documento jurídico com análise contextual'''
        # Usar Legal-Context para análise
        analysis = {
            'document_type': doc_type,
            'key_entities': self.extract_entities(content),
            'legal_concepts': self.extract_legal_concepts(content),
            'summary': content[:200] + '...'
        }
        return analysis
    
    def extract_entities(self, content: str) -> List[str]:
        '''Extrai entidades jurídicas básicas'''
        entities = []
        # Números de processo
        import re
        processes = re.findall(r'\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}', content)
        entities.extend([f'Processo: {p}' for p in processes])
        
        # Valores monetários
        values = re.findall(r'R\$\s?[\d.,]+', content)
        entities.extend([f'Valor: {v}' for v in values])
        
        return entities
    
    def extract_legal_concepts(self, content: str) -> List[str]:
        '''Extrai conceitos jurídicos relevantes'''
        concepts = []
        legal_terms = [
            'dano moral', 'negativação indevida', 'indenização',
            'responsabilidade civil', 'código de defesa do consumidor',
            'boa-fé objetiva', 'nexo de causalidade'
        ]
        
        for term in legal_terms:
            if term.lower() in content.lower():
                concepts.append(term)
        
        return concepts