"""
🔌 GERENCIADOR DE CONEXÕES AVANÇADO
Sistema robusto para gerenciar conexões com tribunais
"""

import os
import ssl
import time
import yaml
import asyncio
import aiohttp
import requests
from pathlib import Path
from typing import Dict, Optional, Any, List, Tuple
from datetime import datetime, timedelta
from urllib.parse import urlparse
import certifi
import OpenSSL.crypto
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import logging
from collections import defaultdict
import random
from string import Template

logger = logging.getLogger(__name__)


class CircuitBreaker:
    """Implementa circuit breaker pattern para falhas"""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = defaultdict(int)
        self.last_failure_time = {}
        self.is_open = defaultdict(bool)
    
    def call_failed(self, service: str):
        """Registra falha em um serviço"""
        self.failure_count[service] += 1
        self.last_failure_time[service] = datetime.now()
        
        if self.failure_count[service] >= self.failure_threshold:
            self.is_open[service] = True
            logger.warning(f"Circuit breaker aberto para {service}")
    
    def call_succeeded(self, service: str):
        """Registra sucesso em um serviço"""
        self.failure_count[service] = 0
        self.is_open[service] = False
    
    def can_attempt(self, service: str) -> bool:
        """Verifica se pode tentar chamar o serviço"""
        if not self.is_open[service]:
            return True
        
        # Verificar se passou tempo suficiente para tentar novamente
        if service in self.last_failure_time:
            time_since_failure = datetime.now() - self.last_failure_time[service]
            if time_since_failure.seconds >= self.recovery_timeout:
                # Tentar meio-aberto
                self.is_open[service] = False
                self.failure_count[service] = 0
                return True
        
        return False


class RateLimiter:
    """Rate limiter inteligente com backoff exponencial"""
    
    def __init__(self):
        self.last_request_time = defaultdict(float)
        self.request_count = defaultdict(int)
        self.backoff_multiplier = defaultdict(lambda: 1.0)
    
    async def wait_if_needed(self, service: str, config: Dict[str, Any]):
        """Aguarda se necessário antes de fazer requisição"""
        current_time = time.time()
        
        # Configurações do serviço
        requests_per_minute = config.get('requests_por_minuto', 30)
        min_interval = 60.0 / requests_per_minute
        backoff_mult = config.get('backoff_multiplier', 2.0)
        jitter = config.get('jitter', False)
        
        # Calcular tempo de espera
        time_since_last = current_time - self.last_request_time[service]
        wait_time = max(0, min_interval * self.backoff_multiplier[service] - time_since_last)
        
        # Adicionar jitter se configurado
        if jitter and wait_time > 0:
            wait_time *= (0.5 + random.random())
        
        if wait_time > 0:
            logger.debug(f"Rate limiting {service}: aguardando {wait_time:.2f}s")
            await asyncio.sleep(wait_time)
        
        self.last_request_time[service] = time.time()
        self.request_count[service] += 1
    
    def increase_backoff(self, service: str, config: Dict[str, Any]):
        """Aumenta o backoff após falha"""
        max_backoff = config.get('max_backoff_multiplier', 10.0)
        backoff_mult = config.get('backoff_multiplier', 2.0)
        
        self.backoff_multiplier[service] = min(
            self.backoff_multiplier[service] * backoff_mult,
            max_backoff
        )
    
    def reset_backoff(self, service: str):
        """Reseta o backoff após sucesso"""
        self.backoff_multiplier[service] = 1.0


class ConnectionManager:
    """
    Gerenciador avançado de conexões com tribunais
    Suporta certificados digitais, rate limiting, circuit breaker e mais
    """
    
    def __init__(self, config_path: str = "config/tribunais.yaml", env_file: str = ".env.production"):
        self.config_path = Path(config_path)
        self.env_file = Path(env_file)
        self.tribunais_config = {}
        self.global_config = {}
        
        # Componentes de resiliência
        self.circuit_breaker = CircuitBreaker()
        self.rate_limiter = RateLimiter()
        
        # Sessões HTTP
        self.sessions = {}
        self.ssl_contexts = {}
        
        # Cache de certificados
        self.certificates = {}
        
        # Carregar configurações
        self._load_config()
        
        # Estatísticas
        self.stats = defaultdict(lambda: {
            'requests': 0,
            'successes': 0,
            'failures': 0,
            'total_time': 0,
            'last_success': None,
            'last_failure': None
        })
    
    def _load_config(self):
        """Carrega configurações do arquivo YAML"""
        try:
            # Carregar variáveis de ambiente
            if self.env_file.exists():
                from dotenv import load_dotenv
                load_dotenv(self.env_file)
            
            # Carregar YAML
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config_template = f.read()
            
            # Substituir variáveis de ambiente
            config_str = Template(config_template).safe_substitute(os.environ)
            
            # Parse YAML
            config = yaml.safe_load(config_str)
            
            self.tribunais_config = config.get('tribunais', {})
            self.global_config = config.get('configuracoes_globais', {})
            
            logger.info(f"Configuração carregada: {len(self.tribunais_config)} tribunais")
            
        except Exception as e:
            logger.error(f"Erro ao carregar configuração: {e}")
            self.tribunais_config = {}
            self.global_config = {}
    
    async def get_session(self, tribunal: str, tipo: str = 'rest') -> Optional[aiohttp.ClientSession]:
        """
        Obtém sessão HTTP configurada para o tribunal
        
        Args:
            tribunal: Código do tribunal
            tipo: Tipo de conexão (rest, soap, scraping)
        """
        session_key = f"{tribunal}_{tipo}"
        
        if session_key not in self.sessions:
            await self._create_session(tribunal, tipo)
        
        return self.sessions.get(session_key)
    
    async def _create_session(self, tribunal: str, tipo: str):
        """Cria nova sessão HTTP com todas as configurações"""
        try:
            config = self.tribunais_config.get(tribunal, {})
            
            # Configurar SSL
            ssl_context = await self._create_ssl_context(tribunal)
            
            # Configurar connector
            connector = aiohttp.TCPConnector(
                ssl=ssl_context,
                limit=self.global_config.get('performance', {}).get('max_connections', 100),
                ttl_dns_cache=300,
                enable_cleanup_closed=True
            )
            
            # Headers customizados
            headers = config.get('headers', {}).copy()
            
            # User agent rotation para anti-bot
            if config.get('anti_bot', {}).get('rotate_user_agents'):
                headers['User-Agent'] = self._get_random_user_agent()
            
            # Configurar timeout
            timeout_config = self.global_config.get('performance', {})
            timeout = aiohttp.ClientTimeout(
                total=timeout_config.get('timeout_leitura', 300),
                connect=timeout_config.get('timeout_conexao', 30)
            )
            
            # Configurar proxy se necessário
            proxy = None
            if self.global_config.get('proxy', {}).get('enabled') == 'true':
                proxy = self.global_config['proxy'].get('https')
            
            # Criar sessão
            session = aiohttp.ClientSession(
                connector=connector,
                headers=headers,
                timeout=timeout,
                cookie_jar=aiohttp.CookieJar() if config.get('cookies', {}).get('enabled') else None
            )
            
            session_key = f"{tribunal}_{tipo}"
            self.sessions[session_key] = session
            
            logger.info(f"Sessão criada para {tribunal} ({tipo})")
            
        except Exception as e:
            logger.error(f"Erro ao criar sessão para {tribunal}: {e}")
    
    async def _create_ssl_context(self, tribunal: str) -> ssl.SSLContext:
        """Cria contexto SSL com certificados se necessário"""
        try:
            config = self.tribunais_config.get(tribunal, {})
            cert_config = config.get('certificado', {})
            
            # Criar contexto SSL básico
            context = ssl.create_default_context(cafile=certifi.where())
            
            # Configurar versão mínima do TLS
            min_version = self.global_config.get('ssl', {}).get('min_version', 'TLSv1.2')
            if min_version == 'TLSv1.2':
                context.minimum_version = ssl.TLSVersion.TLSv1_2
            elif min_version == 'TLSv1.3':
                context.minimum_version = ssl.TLSVersion.TLSv1_3
            
            # Verificação SSL
            if not self.global_config.get('ssl', {}).get('verify', True):
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
            
            # Certificado cliente se configurado
            cert_path = cert_config.get('path')
            if cert_path and os.path.exists(cert_path):
                cert_senha = cert_config.get('senha', '')
                
                # Carregar certificado
                await self._load_client_certificate(context, cert_path, cert_senha)
                
                logger.info(f"Certificado cliente carregado para {tribunal}")
            
            return context
            
        except Exception as e:
            logger.error(f"Erro ao criar contexto SSL para {tribunal}: {e}")
            return ssl.create_default_context()
    
    async def _load_client_certificate(self, context: ssl.SSLContext, 
                                     cert_path: str, password: str = ''):
        """Carrega certificado cliente (A3/arquivo)"""
        try:
            # Detectar tipo de certificado
            if cert_path.endswith('.p12') or cert_path.endswith('.pfx'):
                # PKCS12
                with open(cert_path, 'rb') as f:
                    p12_data = f.read()
                
                # Extrair certificado e chave
                from cryptography.hazmat.primitives.serialization import pkcs12
                
                private_key, certificate, additional_certs = pkcs12.load_pkcs12(
                    p12_data, password.encode() if password else None
                )
                
                # TODO: Converter para PEM e adicionar ao contexto
                # Esta é uma implementação simplificada
                logger.warning("Certificados PKCS12 necessitam conversão adicional")
                
            else:
                # Assumir PEM
                context.load_cert_chain(cert_path, password=password if password else None)
                
        except Exception as e:
            logger.error(f"Erro ao carregar certificado cliente: {e}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError))
    )
    async def make_request(self, tribunal: str, endpoint: str, 
                          method: str = 'GET', **kwargs) -> Optional[Dict]:
        """
        Faz requisição com todas as proteções
        
        Args:
            tribunal: Código do tribunal
            endpoint: Endpoint da API
            method: Método HTTP
            **kwargs: Argumentos adicionais para a requisição
        """
        # Verificar circuit breaker
        if not self.circuit_breaker.can_attempt(tribunal):
            logger.warning(f"Circuit breaker aberto para {tribunal}")
            return None
        
        try:
            config = self.tribunais_config.get(tribunal, {})
            
            # Rate limiting
            await self.rate_limiter.wait_if_needed(tribunal, config.get('rate_limit', {}))
            
            # Obter sessão
            session = await self.get_session(tribunal)
            if not session:
                raise Exception(f"Sessão não disponível para {tribunal}")
            
            # Construir URL
            base_url = config.get('urls', {}).get('rest', '')
            url = f"{base_url}/{endpoint}".replace('//', '/')
            
            # Estatísticas
            start_time = time.time()
            self.stats[tribunal]['requests'] += 1
            
            # Fazer requisição
            async with session.request(method, url, **kwargs) as response:
                response.raise_for_status()
                
                # Sucesso
                elapsed = time.time() - start_time
                self.stats[tribunal]['successes'] += 1
                self.stats[tribunal]['total_time'] += elapsed
                self.stats[tribunal]['last_success'] = datetime.now()
                
                # Resetar backoff e circuit breaker
                self.rate_limiter.reset_backoff(tribunal)
                self.circuit_breaker.call_succeeded(tribunal)
                
                # Retornar resposta
                if response.content_type == 'application/json':
                    return await response.json()
                else:
                    return {'text': await response.text(), 'status': response.status}
                    
        except Exception as e:
            # Falha
            self.stats[tribunal]['failures'] += 1
            self.stats[tribunal]['last_failure'] = datetime.now()
            
            # Atualizar circuit breaker e backoff
            self.circuit_breaker.call_failed(tribunal)
            self.rate_limiter.increase_backoff(tribunal, config.get('rate_limit', {}))
            
            logger.error(f"Erro na requisição para {tribunal}: {e}")
            raise
    
    async def test_connectivity(self, tribunal: str) -> Dict[str, Any]:
        """Testa conectividade com um tribunal"""
        result = {
            'tribunal': tribunal,
            'timestamp': datetime.now().isoformat(),
            'endpoints': {}
        }
        
        config = self.tribunais_config.get(tribunal, {})
        urls = config.get('urls', {})
        
        for tipo, url in urls.items():
            if not url or url.startswith('${'):
                continue
                
            try:
                start = time.time()
                
                if tipo in ['rest', 'soap']:
                    response = await self.make_request(tribunal, 'health')
                    status = 'online' if response else 'error'
                else:
                    # Teste simples de conectividade
                    async with aiohttp.ClientSession() as session:
                        async with session.head(url, timeout=10) as resp:
                            status = 'online' if resp.status < 500 else 'error'
                
                elapsed = time.time() - start
                
                result['endpoints'][tipo] = {
                    'url': url,
                    'status': status,
                    'response_time': round(elapsed * 1000, 2)  # ms
                }
                
            except Exception as e:
                result['endpoints'][tipo] = {
                    'url': url,
                    'status': 'offline',
                    'error': str(e)
                }
        
        # Status geral
        statuses = [ep['status'] for ep in result['endpoints'].values()]
        if all(s == 'online' for s in statuses):
            result['overall_status'] = 'online'
        elif any(s == 'online' for s in statuses):
            result['overall_status'] = 'partial'
        else:
            result['overall_status'] = 'offline'
        
        return result
    
    def get_statistics(self, tribunal: str = None) -> Dict[str, Any]:
        """Retorna estatísticas de conexão"""
        if tribunal:
            stats = self.stats[tribunal].copy()
            
            # Calcular médias
            if stats['successes'] > 0:
                stats['avg_response_time'] = stats['total_time'] / stats['successes']
                stats['success_rate'] = stats['successes'] / stats['requests']
            else:
                stats['avg_response_time'] = 0
                stats['success_rate'] = 0
            
            return stats
        
        # Estatísticas globais
        return {
            tribunal: self.get_statistics(tribunal)
            for tribunal in self.stats.keys()
        }
    
    def _get_random_user_agent(self) -> str:
        """Retorna user agent aleatório para anti-bot"""
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101"
        ]
        return random.choice(user_agents)
    
    async def close(self):
        """Fecha todas as sessões"""
        for session in self.sessions.values():
            await session.close()
        self.sessions.clear()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


# Exemplo de uso
if __name__ == "__main__":
    async def test():
        async with ConnectionManager() as manager:
            # Testar conectividade
            result = await manager.test_connectivity('tjsp')
            print(f"Conectividade TJSP: {result}")
            
            # Fazer requisição
            try:
                response = await manager.make_request('tjsp', 'consulta/processo/123')
                print(f"Resposta: {response}")
            except Exception as e:
                print(f"Erro: {e}")
            
            # Ver estatísticas
            stats = manager.get_statistics()
            print(f"Estatísticas: {stats}")
    
    asyncio.run(test())