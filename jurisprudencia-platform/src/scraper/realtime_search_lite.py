"""
Sistema de busca em tempo real LITE - Sem dependências ML pesadas
Versão otimizada para Streamlit Cloud
"""

import requests
from bs4 import BeautifulSoup
import time
import logging
from urllib.parse import urljoin
import re
import random
import json
from typing import List, Dict

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RealtimeJurisprudenceSearch:
    """
    Sistema de busca em tempo real no TJSP - Versão Lite
    Apenas scraping básico sem ML
    """
    
    def __init__(self, max_results=20):
        """Inicializa o sistema de busca"""
        logger.info("🚀 Inicializando busca em tempo real LITE...")
        
        self.max_results = max_results
        self.base_url = "https://esaj.tjsp.jus.br"
        self.search_url = f"{self.base_url}/cjsg/consultaCompleta.do"
        
        # User-Agent básico
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }
        
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        logger.info("✅ Sistema de busca LITE inicializado!")
    
    def get_relevant_chunks(self, query: str) -> List[Dict]:
        """
        Busca no TJSP e retorna resultados
        
        Args:
            query: Termo de busca
            
        Returns:
            Lista de resultados
        """
        logger.info(f"🔍 Buscando no TJSP: '{query}'")
        
        try:
            # Tentar buscar no TJSP
            results = self._search_tjsp(query)
            
            if results:
                logger.info(f"✅ {len(results)} resultados encontrados")
                return results
            else:
                logger.warning("⚠️ Nenhum resultado encontrado, usando dados locais")
                return self._get_local_fallback(query)
                
        except Exception as e:
            logger.error(f"❌ Erro na busca: {e}")
            return self._get_local_fallback(query)
    
    def _search_tjsp(self, query: str) -> List[Dict]:
        """Busca básica no TJSP"""
        try:
            # Delay para não ser bloqueado
            time.sleep(random.uniform(2, 4))
            
            # Parâmetros de busca
            params = {
                'conversationId': '',
                'dadosConsulta.valorConsulta': query,
                'dadosConsulta.tipoNuProcesso': 'UNIFICADO',
                'numeroRegistros': '10'
            }
            
            # Fazer request
            response = self.session.get(
                self.search_url,
                params=params,
                timeout=30
            )
            
            if response.status_code != 200:
                logger.warning(f"Status HTTP: {response.status_code}")
                return []
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            results = []
            
            # Procurar resultados
            items = soup.find_all('tr', class_='fundocinza1') or \
                   soup.find_all('div', class_='resultado')
            
            for i, item in enumerate(items[:5]):  # Máximo 5 resultados
                text = item.get_text(strip=True)
                if len(text) > 100:  # Só resultados com conteúdo
                    results.append({
                        'rank': i + 1,
                        'score': 0.8 - (i * 0.1),  # Score fictício
                        'text': text[:500] + '...' if len(text) > 500 else text,
                        'source': 'tjsp_online',
                        'processo': self._extract_processo(text),
                        'relator': 'N/A',
                        'data': self._extract_date(text),
                        'url': ''
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"Erro no scraping: {e}")
            return []
    
    def _extract_processo(self, text: str) -> str:
        """Extrai número do processo do texto"""
        # Padrão de número de processo
        pattern = r'\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}'
        match = re.search(pattern, text)
        return match.group(0) if match else 'N/A'
    
    def _extract_date(self, text: str) -> str:
        """Extrai data do texto"""
        # Padrão de data
        pattern = r'\d{1,2}/\d{1,2}/\d{4}'
        match = re.search(pattern, text)
        return match.group(0) if match else 'N/A'
    
    def _get_local_fallback(self, query: str) -> List[Dict]:
        """Retorna dados locais de exemplo"""
        logger.info("📁 Usando dados locais de exemplo")
        
        # Dados de exemplo
        exemplos = [
            {
                'rank': 1,
                'score': 0.95,
                'text': 'APELAÇÃO CÍVEL - Ação de indenização por danos morais - Negativação indevida - Dano moral configurado - Quantum indenizatório fixado em R$ 10.000,00 - Recurso parcialmente provido.',
                'source': 'local_data',
                'processo': '1234567-89.2023.8.26.0100',
                'relator': 'Des. João Silva',
                'data': '15/05/2024',
                'url': ''
            },
            {
                'rank': 2,
                'score': 0.85,
                'text': 'RESPONSABILIDADE CIVIL - Inscrição indevida em cadastros de inadimplentes - Dano moral in re ipsa - Valor da indenização - Critérios de fixação - Recurso provido em parte.',
                'source': 'local_data',
                'processo': '9876543-21.2023.8.26.0100',
                'relator': 'Des. Maria Santos',
                'data': '10/05/2024',
                'url': ''
            }
        ]
        
        # Filtrar por relevância básica
        query_lower = query.lower()
        resultados_filtrados = []
        
        for exemplo in exemplos:
            texto_lower = exemplo['text'].lower()
            # Verificar se alguma palavra da query está no texto
            palavras_query = query_lower.split()
            relevancia = sum(1 for palavra in palavras_query if palavra in texto_lower)
            
            if relevancia > 0:
                exemplo_copy = exemplo.copy()
                exemplo_copy['score'] = exemplo['score'] * (relevancia / len(palavras_query))
                resultados_filtrados.append(exemplo_copy)
        
        # Ordenar por score
        resultados_filtrados.sort(key=lambda x: x['score'], reverse=True)
        
        # Reordenar ranks
        for i, resultado in enumerate(resultados_filtrados):
            resultado['rank'] = i + 1
        
        return resultados_filtrados[:5]