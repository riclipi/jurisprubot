"""
Cliente Google Gemini para análises jurídicas
Modelo: gemini-2.5-flash-lite (mais barato e rápido)
"""

import os
import time
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime, timedelta

try:
    import google.generativeai as genai
except ImportError:
    genai = None

logger = logging.getLogger(__name__)


@dataclass
class GeminiConfig:
    """Configuração do cliente Gemini"""
    api_key: str
    model_name: str = "gemini-2.5-flash-lite"
    temperature: float = 0.7
    max_output_tokens: int = 4096
    top_p: float = 0.9
    top_k: int = 40
    max_retries: int = 3
    retry_delay: float = 1.0
    request_timeout: int = 60
    
    # Rate limiting
    requests_per_minute: int = 60
    requests_per_day: int = 50000  # Limite generoso do Flash Lite
    

class RateLimiter:
    """Controle de rate limiting para Gemini"""
    
    def __init__(self, requests_per_minute: int, requests_per_day: int):
        self.requests_per_minute = requests_per_minute
        self.requests_per_day = requests_per_day
        self.minute_requests: List[datetime] = []
        self.daily_requests: List[datetime] = []
        
    def can_make_request(self) -> bool:
        """Verifica se pode fazer uma requisição"""
        now = datetime.now()
        
        # Limpa requisições antigas
        self.minute_requests = [
            req for req in self.minute_requests 
            if req > now - timedelta(minutes=1)
        ]
        self.daily_requests = [
            req for req in self.daily_requests 
            if req > now - timedelta(days=1)
        ]
        
        # Verifica limites
        if len(self.minute_requests) >= self.requests_per_minute:
            return False
        if len(self.daily_requests) >= self.requests_per_day:
            return False
            
        return True
        
    def add_request(self):
        """Registra uma requisição"""
        now = datetime.now()
        self.minute_requests.append(now)
        self.daily_requests.append(now)
        
    def time_until_next_request(self) -> float:
        """Tempo até poder fazer próxima requisição"""
        if not self.minute_requests:
            return 0.0
            
        oldest_minute = min(self.minute_requests)
        time_passed = (datetime.now() - oldest_minute).total_seconds()
        
        if time_passed < 60:
            return 60 - time_passed
            
        return 0.0


class GeminiClient:
    """Cliente otimizado para Google Gemini 2.5 Flash Lite"""
    
    def __init__(self, config: Optional[GeminiConfig] = None):
        """Inicializa o cliente Gemini"""
        if genai is None:
            raise ImportError(
                "google-generativeai não está instalado. "
                "Execute: pip install google-generativeai"
            )
            
        # Configuração padrão ou customizada
        if config is None:
            api_key = os.getenv("GOOGLE_API_KEY", os.getenv("GEMINI_API_KEY"))
            if not api_key:
                raise ValueError(
                    "API key do Google não encontrada. "
                    "Configure GOOGLE_API_KEY ou GEMINI_API_KEY"
                )
            config = GeminiConfig(api_key=api_key)
            
        self.config = config
        
        # Configura API
        genai.configure(api_key=self.config.api_key)
        
        # Inicializa modelo
        self.model = genai.GenerativeModel(
            model_name=self.config.model_name,
            generation_config={
                "temperature": self.config.temperature,
                "top_p": self.config.top_p,
                "top_k": self.config.top_k,
                "max_output_tokens": self.config.max_output_tokens,
            }
        )
        
        # Rate limiter
        self.rate_limiter = RateLimiter(
            self.config.requests_per_minute,
            self.config.requests_per_day
        )
        
        # Cache de conversas
        self.conversations: Dict[str, Any] = {}
        
        logger.info(f"Gemini Client inicializado com modelo: {self.config.model_name}")
        
    def _wait_if_needed(self):
        """Aguarda se necessário para respeitar rate limits"""
        if not self.rate_limiter.can_make_request():
            wait_time = self.rate_limiter.time_until_next_request()
            logger.warning(f"Rate limit atingido. Aguardando {wait_time:.1f}s...")
            time.sleep(wait_time + 0.1)
            
    def generate(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> Optional[str]:
        """
        Gera resposta usando Gemini
        
        Args:
            prompt: Prompt do usuário
            system_prompt: Instruções do sistema (será incluído no prompt)
            **kwargs: Parâmetros adicionais para geração
            
        Returns:
            Resposta gerada ou None em caso de erro
        """
        # Aguarda se necessário
        self._wait_if_needed()
        
        # Prepara prompt completo
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
            
        # Parâmetros de geração
        generation_config = {
            "temperature": kwargs.get("temperature", self.config.temperature),
            "top_p": kwargs.get("top_p", self.config.top_p),
            "top_k": kwargs.get("top_k", self.config.top_k),
            "max_output_tokens": kwargs.get("max_tokens", self.config.max_output_tokens),
        }
        
        # Tentativas com retry
        for attempt in range(self.config.max_retries):
            try:
                # Registra requisição
                self.rate_limiter.add_request()
                
                # Gera resposta
                response = self.model.generate_content(
                    full_prompt,
                    generation_config=generation_config,
                    request_options={"timeout": self.config.request_timeout}
                )
                
                # Retorna texto da resposta
                if response.text:
                    return response.text
                else:
                    logger.warning("Resposta vazia do Gemini")
                    return None
                    
            except Exception as e:
                logger.error(f"Erro na tentativa {attempt + 1}: {str(e)}")
                
                if attempt < self.config.max_retries - 1:
                    time.sleep(self.config.retry_delay * (attempt + 1))
                else:
                    logger.error("Todas as tentativas falharam")
                    return None
                    
        return None
        
    def generate_with_conversation(
        self,
        prompt: str,
        conversation_id: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> Optional[str]:
        """
        Gera resposta mantendo contexto da conversa
        
        Args:
            prompt: Prompt do usuário
            conversation_id: ID único da conversa
            system_prompt: Instruções do sistema
            **kwargs: Parâmetros adicionais
            
        Returns:
            Resposta gerada ou None
        """
        # Aguarda se necessário
        self._wait_if_needed()
        
        # Recupera ou cria conversa
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = self.model.start_chat(history=[])
            
        chat = self.conversations[conversation_id]
        
        # Prepara mensagem
        message = prompt
        if system_prompt and not chat.history:
            message = f"{system_prompt}\n\n{prompt}"
            
        # Parâmetros de geração
        generation_config = {
            "temperature": kwargs.get("temperature", self.config.temperature),
            "top_p": kwargs.get("top_p", self.config.top_p),
            "top_k": kwargs.get("top_k", self.config.top_k),
            "max_output_tokens": kwargs.get("max_tokens", self.config.max_output_tokens),
        }
        
        # Tentativas com retry
        for attempt in range(self.config.max_retries):
            try:
                # Registra requisição
                self.rate_limiter.add_request()
                
                # Envia mensagem
                response = chat.send_message(
                    message,
                    generation_config=generation_config,
                    request_options={"timeout": self.config.request_timeout}
                )
                
                # Retorna resposta
                if response.text:
                    return response.text
                else:
                    logger.warning("Resposta vazia do Gemini")
                    return None
                    
            except Exception as e:
                logger.error(f"Erro na tentativa {attempt + 1}: {str(e)}")
                
                if attempt < self.config.max_retries - 1:
                    time.sleep(self.config.retry_delay * (attempt + 1))
                else:
                    logger.error("Todas as tentativas falharam")
                    return None
                    
        return None
        
    def clear_conversation(self, conversation_id: str):
        """Limpa histórico de uma conversa"""
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
            
    def analyze_legal_document(
        self,
        document: str,
        analysis_type: str = "completa",
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Análise especializada para documentos jurídicos
        
        Args:
            document: Texto do documento
            analysis_type: Tipo de análise (completa, resumo, riscos, etc)
            **kwargs: Parâmetros adicionais
            
        Returns:
            Dicionário com análise ou None
        """
        # Prompts especializados por tipo
        prompts = {
            "completa": """Analise este documento jurídico e forneça:
1. Resumo executivo (3-5 linhas)
2. Partes envolvidas
3. Objeto principal
4. Pontos críticos e riscos
5. Próximas ações recomendadas
6. Prazos importantes

Documento:
{document}""",
            
            "resumo": """Faça um resumo executivo deste documento jurídico em no máximo 5 linhas, 
destacando apenas os pontos mais importantes:

Documento:
{document}""",
            
            "riscos": """Identifique e analise os principais riscos jurídicos neste documento:
1. Riscos contratuais
2. Riscos processuais
3. Riscos de compliance
4. Recomendações para mitigação

Documento:
{document}""",
            
            "prazos": """Identifique todos os prazos mencionados neste documento jurídico:
1. Prazos processuais
2. Prazos contratuais
3. Prazos regulatórios
4. Ordem cronológica de vencimento

Documento:
{document}"""
        }
        
        # Seleciona prompt
        prompt_template = prompts.get(analysis_type, prompts["completa"])
        prompt = prompt_template.format(document=document[:8000])  # Limita tamanho
        
        # Sistema prompt jurídico
        system_prompt = """Você é um especialista em direito brasileiro com profundo conhecimento 
em todas as áreas do direito. Sua análise deve ser precisa, objetiva e fundamentada na 
legislação brasileira vigente. Use linguagem técnica quando apropriado, mas mantenha 
clareza para compreensão."""
        
        # Gera análise
        response = self.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.3,  # Mais determinístico para análises
            **kwargs
        )
        
        if not response:
            return None
            
        # Estrutura resposta
        return {
            "tipo_analise": analysis_type,
            "data_analise": datetime.now().isoformat(),
            "modelo": self.config.model_name,
            "analise": response,
            "tokens_estimados": len(prompt.split()) + len(response.split())
        }
        
    def generate_legal_document(
        self,
        document_type: str,
        context: Dict[str, Any],
        **kwargs
    ) -> Optional[str]:
        """
        Gera documentos jurídicos baseado em templates
        
        Args:
            document_type: Tipo do documento (petição, contrato, parecer, etc)
            context: Contexto com informações necessárias
            **kwargs: Parâmetros adicionais
            
        Returns:
            Documento gerado ou None
        """
        # Templates por tipo
        templates = {
            "peticao_inicial": """Redija uma petição inicial com base nas seguintes informações:

Autor: {autor}
Réu: {reu}
Tipo de ação: {tipo_acao}
Fatos: {fatos}
Fundamentos jurídicos: {fundamentos}
Pedidos: {pedidos}
Valor da causa: {valor_causa}

A petição deve seguir a estrutura formal, com endereçamento ao juízo competente, 
qualificação completa das partes, exposição clara dos fatos e fundamentos, 
pedidos específicos e valor da causa.""",
            
            "contrato": """Elabore um contrato de {tipo_contrato} com as seguintes especificações:

Partes: {partes}
Objeto: {objeto}
Valor: {valor}
Prazo: {prazo}
Condições especiais: {condicoes}

O contrato deve conter todas as cláusulas essenciais e seguir as melhores 
práticas jurídicas para este tipo de instrumento.""",
            
            "parecer": """Elabore um parecer jurídico sobre a seguinte questão:

Consulente: {consulente}
Questão: {questao}
Fatos relevantes: {fatos}
Documentos analisados: {documentos}

O parecer deve conter análise fundamentada, citação de legislação e 
jurisprudência pertinentes, e conclusão objetiva."""
        }
        
        # Seleciona template
        template = templates.get(document_type)
        if not template:
            logger.error(f"Tipo de documento não suportado: {document_type}")
            return None
            
        # Preenche template
        try:
            prompt = template.format(**context)
        except KeyError as e:
            logger.error(f"Contexto incompleto para {document_type}: {e}")
            return None
            
        # Sistema prompt para documentos
        system_prompt = """Você é um advogado experiente especializado em redação de documentos 
jurídicos. Seus documentos devem ser tecnicamente perfeitos, seguindo todas as 
formalidades legais e usando linguagem jurídica apropriada. Cite legislação e 
jurisprudência quando relevante."""
        
        # Gera documento
        return self.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.5,  # Balanço entre criatividade e precisão
            **kwargs
        )
        
    def estimate_cost(self, text: str) -> Dict[str, float]:
        """
        Estima custo da operação com Gemini Flash Lite
        
        Args:
            text: Texto para processar
            
        Returns:
            Dicionário com estimativas de custo
        """
        # Conta tokens aproximadamente (1 token ≈ 4 caracteres)
        char_count = len(text)
        token_estimate = char_count / 4
        
        # Preços do Gemini 2.5 Flash Lite (valores exemplificativos)
        # Verificar preços atuais na documentação do Google
        price_per_1k_input = 0.000075  # $0.075 por milhão de tokens
        price_per_1k_output = 0.0003   # $0.30 por milhão de tokens
        
        # Estima tokens de saída (geralmente 50-200% do input)
        output_estimate = token_estimate * 1.0
        
        # Calcula custos
        input_cost = (token_estimate / 1000) * price_per_1k_input
        output_cost = (output_estimate / 1000) * price_per_1k_output
        total_cost = input_cost + output_cost
        
        return {
            "tokens_entrada_estimados": int(token_estimate),
            "tokens_saida_estimados": int(output_estimate),
            "custo_entrada_usd": round(input_cost, 6),
            "custo_saida_usd": round(output_cost, 6),
            "custo_total_usd": round(total_cost, 6),
            "custo_total_brl": round(total_cost * 5.0, 4),  # Taxa aproximada
            "modelo": self.config.model_name
        }
        
    def get_usage_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas de uso"""
        return {
            "requests_ultimo_minuto": len(self.rate_limiter.minute_requests),
            "requests_ultimas_24h": len(self.rate_limiter.daily_requests),
            "limite_por_minuto": self.rate_limiter.requests_per_minute,
            "limite_diario": self.rate_limiter.requests_per_day,
            "conversas_ativas": len(self.conversations),
            "modelo": self.config.model_name
        }


# Cliente singleton para uso global
_gemini_client: Optional[GeminiClient] = None


def get_gemini_client() -> GeminiClient:
    """Retorna instância singleton do cliente Gemini"""
    global _gemini_client
    if _gemini_client is None:
        _gemini_client = GeminiClient()
    return _gemini_client


# Funções de conveniência
def analyze_with_gemini(
    text: str,
    analysis_type: str = "completa",
    **kwargs
) -> Optional[Dict[str, Any]]:
    """Analisa documento com Gemini"""
    client = get_gemini_client()
    return client.analyze_legal_document(text, analysis_type, **kwargs)


def generate_with_gemini(
    prompt: str,
    system_prompt: Optional[str] = None,
    **kwargs
) -> Optional[str]:
    """Gera texto com Gemini"""
    client = get_gemini_client()
    return client.generate(prompt, system_prompt, **kwargs)