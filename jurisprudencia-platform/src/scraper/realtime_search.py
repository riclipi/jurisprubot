"""
Sistema de busca em tempo real no TJSP com estratégias anti-detecção
Busca diretamente no site oficial e aplica busca semântica
"""

import requests
from bs4 import BeautifulSoup
import time
import logging
from urllib.parse import urljoin, urlparse
import re
import random
import json
from typing import List, Dict, Optional
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AdvancedRealtimeSearch:
    """
    Sistema avançado de busca em tempo real no TJSP com anti-detecção
    Combina web scraping stealth com busca semântica
    """
    
    def __init__(self, max_results=20):
        """
        Inicializa o sistema de busca avançado
        
        Args:
            max_results: Número máximo de resultados por busca
        """
        logger.info("🚀 Inicializando sistema avançado de busca em tempo real...")
        
        self.max_results = max_results
        self.base_url = "https://esaj.tjsp.jus.br"
        self.search_url = f"{self.base_url}/cjsg/consultaCompleta.do"
        
        # Pool de User-Agents realistas
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:120.0) Gecko/20100101 Firefox/120.0',
            'Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0'
        ]
        
        # Configurar sessão
        self.session = requests.Session()
        self.setup_realistic_headers()
        
        # Configurações de timing
        self.min_delay = 3
        self.max_delay = 7
        self.request_timeout = 30
        
        # Estatísticas de tentativas
        self.stats = {
            'total_attempts': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'anti_bot_blocks': 0,
            'fallback_usage': 0
        }
        
        # Carregar modelo de embeddings
        logger.info("📥 Carregando modelo de embeddings...")
        try:
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("✅ Modelo carregado com sucesso!")
        except Exception as e:
            logger.error(f"❌ Erro ao carregar modelo: {e}")
            self.embedding_model = None
        
        # Cache para resultados
        self.cache = {}
        
        logger.info("✅ Sistema avançado de busca inicializado!")

    def setup_realistic_headers(self):
        """Configura headers realistas para simular navegador real"""
        user_agent = random.choice(self.user_agents)
        
        # Headers que simulam comportamento humano real
        headers = {
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        }
        
        # Adicionar headers baseados no User-Agent
        if 'Chrome' in user_agent:
            headers.update({
                'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"' if 'Windows' in user_agent else '"macOS"' if 'Mac' in user_agent else '"Linux"'
            })
        
        self.session.headers.update(headers)
        logger.info(f"🔧 Headers configurados com User-Agent: {user_agent[:50]}...")

    def simulate_human_delay(self, base_delay=None):
        """Simula delay humano com variação natural"""
        if base_delay is None:
            delay = random.uniform(self.min_delay, self.max_delay)
        else:
            # Adicionar variação de ±20% ao delay base
            variation = base_delay * 0.2
            delay = random.uniform(base_delay - variation, base_delay + variation)
        
        logger.info(f"⏳ Aguardando {delay:.1f}s para simular comportamento humano...")
        time.sleep(delay)

    def warm_up_session(self):
        """Aquece a sessão acessando a página inicial primeiro"""
        try:
            logger.info("🌡️ Aquecendo sessão - acessando página inicial...")
            
            # Acessar página inicial para obter cookies
            warm_up_url = f"{self.base_url}/cjsg/consultaCompleta.do"
            
            response = self.session.get(warm_up_url, timeout=self.request_timeout)
            
            if response.status_code == 200:
                logger.info("✅ Sessão aquecida com sucesso!")
                # Extrair cookies importantes
                cookies = self.session.cookies.get_dict()
                if cookies:
                    logger.info(f"🍪 Cookies obtidos: {len(cookies)} itens")
                return True
            else:
                logger.warning(f"⚠️ Aquecimento retornou status {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro no aquecimento da sessão: {e}")
            return False

    def search_with_stealth(self, query: str, max_retries=3) -> List[Dict]:
        """
        Realiza busca com técnicas stealth anti-detecção
        
        Args:
            query: Termo de busca
            max_retries: Máximo de tentativas
            
        Returns:
            Lista de acórdãos encontrados
        """
        self.stats['total_attempts'] += 1
        
        logger.info(f"🕵️ Iniciando busca stealth para: '{query}'")
        
        # Verificar cache primeiro
        cache_key = f"stealth_{query}"
        if cache_key in self.cache:
            logger.info("📋 Resultado encontrado no cache")
            return self.cache[cache_key]
        
        for attempt in range(max_retries):
            try:
                logger.info(f"🎯 Tentativa {attempt + 1}/{max_retries}")
                
                # Reconfigurar headers para cada tentativa
                self.setup_realistic_headers()
                
                # Aquecer sessão se primeira tentativa
                if attempt == 0:
                    if not self.warm_up_session():
                        logger.warning("⚠️ Falha no aquecimento, continuando mesmo assim...")
                    
                    # Delay adicional após aquecimento
                    self.simulate_human_delay(2)
                
                # Parâmetros de busca mais simples e realistas
                search_params = self.build_search_params(query)
                
                # Fazer request
                logger.info("🌐 Enviando request para TJSP...")
                response = self.session.get(
                    self.search_url,
                    params=search_params,
                    timeout=self.request_timeout
                )
                
                # Analisar resposta
                status_code = response.status_code
                logger.info(f"📡 Status HTTP: {status_code}")
                
                if status_code == 200:
                    # Sucesso! Extrair resultados
                    self.stats['successful_requests'] += 1
                    
                    acordaos = self.extract_from_search_results(response.text)
                    
                    if acordaos:
                        self.cache[cache_key] = acordaos
                        logger.info(f"✅ Busca bem-sucedida! {len(acordaos)} acórdãos encontrados")
                        return acordaos
                    else:
                        logger.warning("⚠️ Nenhum resultado encontrado no HTML")
                        
                elif status_code == 400:
                    self.stats['anti_bot_blocks'] += 1
                    logger.warning(f"🚫 Possível detecção anti-bot (400). Tentativa {attempt + 1}")
                    
                    if attempt < max_retries - 1:
                        # Delay maior antes de tentar novamente
                        logger.info("🔄 Aguardando antes de nova tentativa...")
                        self.simulate_human_delay(random.uniform(10, 20))
                        
                elif status_code == 403:
                    self.stats['anti_bot_blocks'] += 1
                    logger.error("🚫 Acesso negado (403) - possível IP bloqueado")
                    break
                    
                elif status_code == 429:
                    self.stats['anti_bot_blocks'] += 1
                    logger.warning("🚫 Rate limit detectado (429)")
                    
                    if attempt < max_retries - 1:
                        wait_time = random.uniform(30, 60)
                        logger.info(f"⏰ Aguardando {wait_time:.1f}s devido ao rate limit...")
                        time.sleep(wait_time)
                        
                else:
                    logger.error(f"❌ Status HTTP inesperado: {status_code}")
                
                # Log da resposta para debug
                self.log_response_details(response, attempt)
                
            except requests.exceptions.RequestException as e:
                logger.error(f"❌ Erro de request na tentativa {attempt + 1}: {e}")
                self.stats['failed_requests'] += 1
                
                if attempt < max_retries - 1:
                    self.simulate_human_delay(5)
            
            except Exception as e:
                logger.error(f"❌ Erro inesperado na tentativa {attempt + 1}: {e}")
                self.stats['failed_requests'] += 1
        
        # Se chegou aqui, todas as tentativas falharam
        logger.error("❌ Todas as tentativas de busca stealth falharam")
        return []

    def build_search_params(self, query: str) -> Dict:
        """Constrói parâmetros de busca mais realistas"""
        return {
            'conversationId': '',
            'dadosConsulta.valorConsultaLivre': query,
            'dadosConsulta.valorConsulta': query,
            'dadosConsulta.tipoNuProcesso': 'UNIFICADO',
            'dadosConsulta.segredoJustica': 'false',
            'dadosConsulta.pesquisarComSinonimos': 'false',
            'dadosConsulta.tipoPesquisa': 'LIVRE',
            'dadosConsulta.ordenacao': 'RELEVANCIA',
            'contadoragente': '0',
            'contadorMagistrdo': '0',
            'dadosConsulta.tipoPagina': 'CONSULTA',
            'numeroRegistros': str(min(self.max_results, 20)),
        }

    def extract_from_search_results(self, html: str) -> List[Dict]:
        """Extrai resultados da página de busca de forma mais robusta"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            acordaos = []
            
            # Procurar por diferentes estruturas de resultados
            result_selectors = [
                '.unj-resultado-pesquisa',
                '.resultado-pesquisa',
                '.resultado',
                '[class*="resultado"]',
                'tr[id*="resultado"]',
                '.fundocinza1'
            ]
            
            results_found = False
            
            for selector in result_selectors:
                items = soup.select(selector)
                
                if items:
                    logger.info(f"🎯 Encontrados {len(items)} itens com seletor: {selector}")
                    results_found = True
                    
                    for i, item in enumerate(items[:self.max_results]):
                        try:
                            acordao = self.extract_acordao_data(item, i)
                            if acordao:
                                acordaos.append(acordao)
                        except Exception as e:
                            logger.warning(f"⚠️ Erro ao extrair item {i}: {e}")
                    
                    break  # Usar o primeiro seletor que funcionar
            
            if not results_found:
                logger.warning("⚠️ Nenhum seletor de resultado funcionou")
                # Log do HTML para debug (apenas primeiros 1000 chars)
                logger.debug(f"HTML recebido (preview): {html[:1000]}...")
            
            return acordaos
            
        except Exception as e:
            logger.error(f"❌ Erro ao extrair resultados: {e}")
            return []

    def extract_acordao_data(self, item_soup, index: int) -> Dict:
        """Extrai dados de um item de acórdão"""
        acordao = {
            'numero_processo': '',
            'relator': '',
            'data_julgamento': '',
            'ementa': '',
            'url_detalhes': '',
            'index': index
        }
        
        try:
            # Extrair número do processo
            processo_patterns = [
                'a[href*="processo"]',
                'a[href*="numprocesso"]',
                '.numero-processo',
                '[class*="processo"]'
            ]
            
            for pattern in processo_patterns:
                link = item_soup.select_one(pattern)
                if link:
                    acordao['numero_processo'] = link.get_text(strip=True)
                    href = link.get('href', '')
                    if href:
                        acordao['url_detalhes'] = urljoin(self.base_url, href)
                    break
            
            # Extrair relator
            relator_text = item_soup.find(text=re.compile(r'(Relator|Des\.|Desembargador)', re.I))
            if relator_text:
                # Pegar o texto próximo
                parent = relator_text.parent
                if parent:
                    acordao['relator'] = parent.get_text(strip=True)
            
            # Extrair data
            date_pattern = re.compile(r'\d{1,2}[/.-]\d{1,2}[/.-]\d{4}')
            date_match = item_soup.find(text=date_pattern)
            if date_match:
                acordao['data_julgamento'] = date_match.strip()
            
            # Extrair ementa/resumo
            ementa_selectors = [
                '.ementa',
                '.resumo',
                '.texto-resumo',
                '[class*="ementa"]',
                '[class*="resumo"]'
            ]
            
            for selector in ementa_selectors:
                ementa_elem = item_soup.select_one(selector)
                if ementa_elem:
                    acordao['ementa'] = ementa_elem.get_text(strip=True)
                    break
            
            # Se não encontrou ementa específica, pegar texto geral
            if not acordao['ementa']:
                full_text = item_soup.get_text(strip=True)
                # Pegar os primeiros 300 caracteres como ementa
                acordao['ementa'] = full_text[:300] + "..." if len(full_text) > 300 else full_text
            
            return acordao if acordao['numero_processo'] or acordao['ementa'] else None
            
        except Exception as e:
            logger.warning(f"⚠️ Erro ao extrair dados do acórdão {index}: {e}")
            return None

    def log_response_details(self, response, attempt: int):
        """Registra detalhes da resposta para debug"""
        details = {
            'attempt': attempt + 1,
            'status_code': response.status_code,
            'headers': dict(response.headers),
            'content_length': len(response.text),
            'url': response.url,
            'final_url': response.url != self.search_url
        }
        
        logger.info(f"📋 Detalhes da resposta: {json.dumps(details, indent=2, default=str)}")
        
        # Verificar por indicadores de bloqueio
        content_lower = response.text.lower()
        block_indicators = [
            'access denied',
            'blocked',
            'captcha',
            'robot',
            'bot detected',
            'security check',
            'unusual traffic'
        ]
        
        found_indicators = [indicator for indicator in block_indicators if indicator in content_lower]
        if found_indicators:
            logger.warning(f"🚫 Indicadores de bloqueio encontrados: {found_indicators}")

    def get_stats(self) -> Dict:
        """Retorna estatísticas de uso"""
        return {
            **self.stats,
            'success_rate': (self.stats['successful_requests'] / max(self.stats['total_attempts'], 1)) * 100,
            'cache_size': len(self.cache)
        }

    def search_tjsp_live(self, query: str) -> List[Dict]:
        """
        Realiza busca diretamente no site do TJSP (método compatível)
        
        Args:
            query: Termo de busca
            
        Returns:
            Lista de dicionários com informações dos acórdãos
        """
        return self.search_with_stealth(query)

    def get_relevant_chunks(self, query: str) -> List[Dict]:
        """
        Método principal: busca TJSP + extração + busca semântica (método compatível)
        
        Args:
            query: Consulta de busca
            
        Returns:
            Top 5 trechos mais relevantes
        """
        logger.info(f"🎯 Iniciando busca completa avançada para: '{query}'")
        
        try:
            # 1. Buscar no TJSP com stealth
            acordaos = self.search_with_stealth(query)
            
            if not acordaos:
                logger.warning("⚠️ Nenhum acórdão encontrado no TJSP")
                return self._fallback_to_local_data(query)
            
            # 2. Extrair textos completos (limitado para não sobrecarregar)
            max_extractions = min(3, len(acordaos))  # Reduzido para 3
            logger.info(f"📄 Extraindo texto de {max_extractions} acórdãos...")
            
            for i in range(max_extractions):
                acordao = acordaos[i]
                if acordao.get('url_detalhes'):
                    # Simular delay humano antes de cada extração
                    if i > 0:
                        self.simulate_human_delay()
                    
                    texto_completo = self.get_acordao_full_text(acordao['url_detalhes'])
                    acordao['texto_completo'] = texto_completo
            
            # 3. Aplicar busca semântica
            ranked_acordaos = self.semantic_search(query, acordaos)
            
            # 4. Dividir em chunks e retornar top 5
            relevant_chunks = self._create_chunks_from_acordaos(ranked_acordaos, query)
            
            logger.info(f"✅ Busca avançada concluída. Retornando {len(relevant_chunks)} chunks")
            return relevant_chunks[:5]
            
        except Exception as e:
            logger.error(f"❌ Erro na busca completa avançada: {e}")
            return self._fallback_to_local_data(query)

    def get_acordao_full_text(self, acordao_url: str) -> str:
        """
        Extrai texto completo de um acórdão com técnicas stealth
        
        Args:
            acordao_url: URL do acórdão
            
        Returns:
            Texto extraído do acórdão
        """
        if not acordao_url:
            return ""
        
        try:
            logger.info(f"📄 Extraindo texto stealth de: {acordao_url}")
            
            # Configurar headers para simular navegação humana
            self.setup_realistic_headers()
            
            # Fazer request com delay humano
            response = self.session.get(acordao_url, timeout=self.request_timeout)
            
            if response.status_code != 200:
                logger.warning(f"⚠️ Status {response.status_code} para {acordao_url}")
                return ""
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remover scripts e styles
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            # Extrair texto das seções relevantes
            text_sections = []
            
            # Procurar por seções específicas de acórdão (múltiplos seletores)
            selectors = [
                '.acordao-texto',
                '.texto-acordao', 
                '.conteudo-acordao',
                '#divImprimivel',
                '.documento-texto',
                '.integra-acordao',
                '.texto-completo',
                '[class*="texto"]',
                '[class*="acordao"]',
                '.conteudo'
            ]
            
            for selector in selectors:
                sections = soup.select(selector)
                for section in sections:
                    text = section.get_text(separator=' ', strip=True)
                    if len(text) > 100:  # Só incluir seções com conteúdo substancial
                        text_sections.append(text)
            
            # Se não encontrou seções específicas, pegar corpo geral
            if not text_sections:
                body = soup.find('body')
                if body:
                    text_sections.append(body.get_text(separator=' ', strip=True))
            
            # Combinar e limpar texto
            full_text = ' '.join(text_sections)
            full_text = re.sub(r'\s+', ' ', full_text)  # Normalizar espaços
            full_text = full_text.strip()
            
            logger.info(f"✅ Extraído: {len(full_text)} caracteres")
            return full_text
            
        except Exception as e:
            logger.error(f"❌ Erro ao extrair texto de {acordao_url}: {e}")
            return ""

    def semantic_search(self, query: str, extracted_texts: List[Dict]) -> List[Dict]:
        """
        Aplica busca semântica nos textos extraídos (método compatível)
        
        Args:
            query: Consulta de busca
            extracted_texts: Lista de textos extraídos
            
        Returns:
            Lista ordenada por relevância semântica
        """
        if not self.embedding_model or not extracted_texts:
            logger.warning("⚠️ Modelo não disponível ou sem textos")
            return extracted_texts
        
        logger.info(f"🧠 Aplicando busca semântica avançada para: '{query}'")
        
        try:
            # Preparar textos para embedding
            texts_for_embedding = []
            valid_texts = []
            
            for item in extracted_texts:
                # Combinar ementa + texto completo para busca
                combined_text = f"{item.get('ementa', '')} {item.get('texto_completo', '')}".strip()
                
                if combined_text:
                    texts_for_embedding.append(combined_text)
                    valid_texts.append(item)
            
            if not texts_for_embedding:
                logger.warning("⚠️ Nenhum texto válido para embedding")
                return extracted_texts
            
            # Criar embeddings
            logger.info("🔢 Criando embeddings avançados...")
            query_embedding = self.embedding_model.encode([query])
            text_embeddings = self.embedding_model.encode(texts_for_embedding)
            
            # Calcular similaridades
            similarities = cosine_similarity(query_embedding, text_embeddings)[0]
            
            # Adicionar scores aos textos
            for i, similarity in enumerate(similarities):
                valid_texts[i]['similarity_score'] = float(similarity)
            
            # Ordenar por relevância
            sorted_texts = sorted(valid_texts, key=lambda x: x['similarity_score'], reverse=True)
            
            logger.info(f"✅ Busca semântica avançada concluída. Top score: {sorted_texts[0]['similarity_score']:.3f}")
            return sorted_texts
            
        except Exception as e:
            logger.error(f"❌ Erro na busca semântica avançada: {e}")
            return extracted_texts

    def _create_chunks_from_acordaos(self, acordaos: List[Dict], query: str) -> List[Dict]:
        """Cria chunks relevantes a partir dos acórdãos (método compatível)"""
        chunks = []
        
        for i, acordao in enumerate(acordaos[:5]):  # Top 5 acórdãos
            # Chunk da ementa
            if acordao.get('ementa'):
                chunks.append({
                    'rank': len(chunks) + 1,
                    'score': acordao.get('similarity_score', 0),
                    'text': acordao['ementa'],
                    'source': 'ementa',
                    'processo': acordao.get('numero_processo', 'N/A'),
                    'relator': acordao.get('relator', 'N/A'),
                    'data': acordao.get('data_julgamento', 'N/A'),
                    'url': acordao.get('url_detalhes', '')
                })
            
            # Chunks do texto completo
            if acordao.get('texto_completo'):
                texto = acordao['texto_completo']
                
                # Dividir em chunks de ~500 caracteres
                chunk_size = 500
                for j in range(0, len(texto), chunk_size):
                    chunk_text = texto[j:j+chunk_size]
                    
                    # Verificar se chunk contém palavras da query
                    query_words = query.lower().split()
                    chunk_lower = chunk_text.lower()
                    relevance = sum(1 for word in query_words if word in chunk_lower)
                    
                    if relevance > 0:  # Só incluir chunks relevantes
                        chunks.append({
                            'rank': len(chunks) + 1,
                            'score': acordao.get('similarity_score', 0) * relevance / len(query_words),
                            'text': chunk_text,
                            'source': 'texto_completo',
                            'processo': acordao.get('numero_processo', 'N/A'),
                            'relator': acordao.get('relator', 'N/A'),
                            'data': acordao.get('data_julgamento', 'N/A'),
                            'url': acordao.get('url_detalhes', '')
                        })
        
        # Ordenar por score
        chunks.sort(key=lambda x: x['score'], reverse=True)
        
        # Reordenar ranks
        for i, chunk in enumerate(chunks):
            chunk['rank'] = i + 1
        
        return chunks

    def _fallback_to_local_data(self, query: str) -> List[Dict]:
        """Fallback para dados locais se TJSP indisponível (método compatível)"""
        logger.info("🔄 Usando fallback para dados locais...")
        self.stats['fallback_usage'] += 1
        
        try:
            # Importar sistema local
            import sys
            sys.path.append('.')
            from ..rag.simple_search import SimpleSearchEngine
            
            # Usar sistema local
            local_search = SimpleSearchEngine()
            results = local_search.search(query, top_k=5)
            
            # Converter formato
            fallback_chunks = []
            for result in results:
                fallback_chunks.append({
                    'rank': result['rank'],
                    'score': result['score'],
                    'text': result['text'],
                    'source': 'local_data',
                    'processo': 'N/A',
                    'relator': 'N/A',
                    'data': 'N/A',
                    'url': '',
                    'arquivo_local': result['metadata']['file']
                })
            
            logger.info(f"✅ Fallback: {len(fallback_chunks)} resultados locais")
            return fallback_chunks
            
        except Exception as e:
            logger.error(f"❌ Erro no fallback: {e}")
            return []

    def test_search(self):
        """Testa o sistema avançado com consulta específica"""
        query = "dano moral negativação indevida"
        
        print("\n" + "=" * 60)
        print("🧪 TESTE DE BUSCA AVANÇADA EM TEMPO REAL - TJSP")
        print("=" * 60)
        print(f"🔍 Consulta: '{query}'")
        print("-" * 60)
        
        # Mostrar estatísticas iniciais
        stats = self.get_stats()
        print(f"📊 Estatísticas iniciais: {json.dumps(stats, indent=2)}")
        
        # Executar busca
        chunks = self.get_relevant_chunks(query)
        
        if chunks:
            print(f"\n✅ Encontrados {len(chunks)} chunks relevantes:")
            
            for chunk in chunks:
                print(f"\n📄 #{chunk['rank']} - Score: {chunk['score']:.3f}")
                print(f"📁 Fonte: {chunk['source']}")
                print(f"⚖️ Processo: {chunk['processo']}")
                print(f"👨‍⚖️ Relator: {chunk['relator']}")
                print(f"📅 Data: {chunk['data']}")
                
                if chunk.get('url'):
                    print(f"🔗 URL: {chunk['url']}")
                
                print(f"📝 Trecho: {chunk['text'][:300]}...")
                
        else:
            print("❌ Nenhum resultado encontrado")
        
        # Mostrar estatísticas finais
        final_stats = self.get_stats()
        print(f"\n📊 Estatísticas finais:")
        print(f"   🎯 Taxa de sucesso: {final_stats['success_rate']:.1f}%")
        print(f"   🚫 Bloqueios anti-bot: {final_stats['anti_bot_blocks']}")
        print(f"   🔄 Uso de fallback: {final_stats['fallback_usage']}")
        print(f"   📋 Itens em cache: {final_stats['cache_size']}")
        
        print("\n" + "=" * 60)


# Wrapper para compatibilidade com código existente
class RealtimeJurisprudenceSearch(AdvancedRealtimeSearch):
    """Wrapper para manter compatibilidade com código existente"""
    pass


def main():
    """Função principal para teste"""
    try:
        # Criar sistema de busca
        search_system = RealtimeJurisprudenceSearch(max_results=10)
        
        # Executar teste
        search_system.test_search()
        
    except Exception as e:
        logger.error(f"❌ Erro no teste: {e}")


if __name__ == "__main__":
    main()