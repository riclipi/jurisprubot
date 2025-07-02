"""
🧠 ANÁLISE PROCESSUAL IA - EXTRAÇÃO AUTOMÁTICA INTELIGENTE
Sistema de IA para análise e extração automática de informações processuais
"""

import re
import json
import asyncio
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
from pathlib import Path
import pandas as pd
import numpy as np

# OCR e processamento de texto
try:
    import pytesseract
    from PIL import Image
    import fitz  # PyMuPDF
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

# NLP e IA
try:
    from sentence_transformers import SentenceTransformer
    import spacy
    NLP_AVAILABLE = True
except ImportError:
    NLP_AVAILABLE = False

class TipoDocumento(Enum):
    PETICAO_INICIAL = "peticao_inicial"
    CONTESTACAO = "contestacao"
    SENTENCA = "sentenca"
    DECISAO = "decisao"
    DESPACHO = "despacho"
    ACÓRDAO = "acordao"
    RECURSO = "recurso"
    MANIFESTACAO = "manifestacao"
    DOCUMENTO_ANEXO = "documento_anexo"
    CERTIDAO = "certidao"
    OUTRO = "outro"

class StatusAnalise(Enum):
    PENDENTE = "pendente"
    PROCESSANDO = "processando"
    CONCLUIDA = "concluida"
    ERRO = "erro"
    PARCIAL = "parcial"

@dataclass
class EntidadeExtração:
    """Entidade extraída do texto"""
    tipo: str
    valor: str
    confianca: float
    posicao_inicio: int
    posicao_fim: int
    contexto: str

@dataclass
class ParteProcessual:
    """Parte processual identificada"""
    nome: str
    tipo: str  # autor, reu, advogado, etc.
    documento: Optional[str] = None
    endereco: Optional[str] = None
    telefone: Optional[str] = None
    email: Optional[str] = None
    qualificacao: Optional[str] = None
    confianca: float = 0.0

@dataclass
class PedidoJudicial:
    """Pedido judicial extraído"""
    descricao: str
    tipo: str  # principal, subsidiario, alternativo
    confianca: float = 0.0
    valor_monetario: Optional[str] = None
    fundamentacao: List[str] = field(default_factory=list)

@dataclass
class MovimentacaoProcessual:
    """Movimentação processual"""
    data: datetime
    tipo: str
    descricao: str
    codigo_cnj: Optional[str] = None
    responsavel: Optional[str] = None
    documento_gerado: Optional[str] = None
    metadados: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AnaliseProcessualCompleta:
    """Resultado completo da análise processual"""
    id_analise: str
    numero_processo: str
    data_analise: datetime
    
    # Informações básicas
    classe_processual: Optional[str] = None
    assunto_principal: Optional[str] = None
    assuntos_secundarios: List[str] = field(default_factory=list)
    valor_causa: Optional[str] = None
    tribunal: Optional[str] = None
    comarca: Optional[str] = None
    vara: Optional[str] = None
    
    # Partes
    partes: List[ParteProcessual] = field(default_factory=list)
    
    # Pedidos
    pedidos: List[PedidoJudicial] = field(default_factory=list)
    
    # Movimentações
    movimentacoes: List[MovimentacaoProcessual] = field(default_factory=list)
    
    # Documentos analisados
    documentos_analisados: List[Dict] = field(default_factory=list)
    
    # Entidades extraídas
    entidades: List[EntidadeExtração] = field(default_factory=list)
    
    # Análise de sentimento e tendências
    sentimento_geral: Optional[str] = None
    probabilidade_sucesso: Optional[float] = None
    riscos_identificados: List[str] = field(default_factory=list)
    oportunidades: List[str] = field(default_factory=list)
    
    # Metadados
    tempo_processamento: Optional[float] = None
    confianca_geral: float = 0.0
    status: StatusAnalise = StatusAnalise.PENDENTE
    observacoes: List[str] = field(default_factory=list)

class AnaliseProcessualIA:
    """
    🧠 SISTEMA DE ANÁLISE PROCESSUAL COM IA
    
    Funcionalidades avançadas:
    - Extração automática de entidades jurídicas
    - OCR inteligente para documentos escaneados
    - Análise de sentimento e tendências
    - Identificação automática de partes e pedidos
    - Classificação de documentos por tipo
    - Extração de movimentações processuais
    - Análise preditiva de resultados
    - Identificação de riscos e oportunidades
    """
    
    def __init__(self):
        self.setup_logging()
        self._inicializar_modelos()
        self._inicializar_patterns()
        self._inicializar_cache()
    
    def setup_logging(self):
        """Configura sistema de logs"""
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def _inicializar_modelos(self):
        """Inicializa modelos de IA e NLP"""
        
        self.modelos_carregados = False
        
        try:
            if NLP_AVAILABLE:
                # Modelo de embeddings para análise semântica
                self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
                
                # Modelo spaCy para NER em português
                try:
                    self.nlp_model = spacy.load("pt_core_news_sm")
                except OSError:
                    self.logger.warning("Modelo spaCy pt_core_news_sm não encontrado")
                    self.nlp_model = None
                
                self.modelos_carregados = True
                self.logger.info("Modelos de IA carregados com sucesso")
            else:
                self.logger.warning("Bibliotecas NLP não disponíveis - funcionalidade limitada")
        
        except Exception as e:
            self.logger.error(f"Erro ao carregar modelos: {e}")
    
    def _inicializar_patterns(self):
        """Inicializa padrões regex para extração"""
        
        # Padrões para CPF/CNPJ
        self.pattern_cpf = re.compile(r'\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b')
        self.pattern_cnpj = re.compile(r'\b\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}\b')
        
        # Padrões para valores monetários
        self.pattern_valor = re.compile(
            r'R\$\s*[\d.,]+|'
            r'reais?\s*[\d.,]+|'
            r'valor\s*de\s*R\$\s*[\d.,]+|'
            r'quantia\s*de\s*R\$\s*[\d.,]+|'
            r'importância\s*de\s*R\$\s*[\d.,]+',
            re.IGNORECASE
        )
        
        # Padrões para datas
        self.pattern_data = re.compile(
            r'\b\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4}\b|'
            r'\b\d{1,2}\s+de\s+\w+\s+de\s+\d{4}\b',
            re.IGNORECASE
        )
        
        # Padrões para endereços
        self.pattern_endereco = re.compile(
            r'(?:rua|avenida|av|r\.|al\.|alameda|travessa|tv\.|praça|pça)\s+[^,;.]+(?:,\s*\d+)?',
            re.IGNORECASE
        )
        
        # Padrões para emails
        self.pattern_email = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        
        # Padrões para telefones
        self.pattern_telefone = re.compile(
            r'\(?\d{2}\)?\s*\d{4,5}[-.\s]?\d{4}|'
            r'\d{2}\s*\d{4,5}[-.\s]?\d{4}',
            re.IGNORECASE
        )
        
        # Padrões para números de processo
        self.pattern_processo = re.compile(r'\b\d{7}-?\d{2}\.?\d{4}\.?\d{1}\.?\d{2}\.?\d{4}\b')
        
        # Padrões jurídicos específicos
        self.patterns_juridicos = {
            'artigo_lei': re.compile(r'art\.?\s*\d+[º°]?(?:,\s*§\s*\d+[º°]?)?(?:,\s*inc\.?\s*[IVX]+)?', re.IGNORECASE),
            'codigo_legal': re.compile(r'(?:CC|CF|CDC|CPC|CLT|CP|CTN)\s*art\.?\s*\d+', re.IGNORECASE),
            'jurisprudencia': re.compile(r'(?:STF|STJ|TST|TRT|TRF|TJ)\s*[-,]?\s*\w+\s*\d+', re.IGNORECASE),
            'sumula': re.compile(r'súmula\s*(?:vinculante\s*)?\d+', re.IGNORECASE)
        }
        
        self.logger.info("Padrões regex inicializados")
    
    def _inicializar_cache(self):
        """Inicializa sistema de cache"""
        self.cache_analises = {}
        self.cache_extrações = {}
        self.historico_analises = []
    
    async def analisar_processo_completo(self, 
                                       numero_processo: str,
                                       documentos: List[Dict],
                                       incluir_ocr: bool = True,
                                       incluir_nlp: bool = True) -> AnaliseProcessualCompleta:
        """
        🎯 ANÁLISE COMPLETA DO PROCESSO
        Executa análise completa com IA
        """
        
        inicio = datetime.now()
        id_analise = f"analise_{numero_processo}_{int(inicio.timestamp())}"
        
        self.logger.info(f"Iniciando análise completa: {numero_processo}")
        
        # Criar estrutura de análise
        analise = AnaliseProcessualCompleta(
            id_analise=id_analise,
            numero_processo=numero_processo,
            data_analise=inicio,
            status=StatusAnalise.PROCESSANDO
        )
        
        try:
            # 1. Processar documentos
            await self._processar_documentos(analise, documentos, incluir_ocr)
            
            # 2. Extrair informações básicas
            await self._extrair_informacoes_basicas(analise)
            
            # 3. Identificar partes processuais
            await self._identificar_partes(analise)
            
            # 4. Extrair pedidos judiciais
            await self._extrair_pedidos(analise)
            
            # 5. Analisar movimentações
            await self._analisar_movimentacoes(analise)
            
            # 6. Análise com NLP (se disponível)
            if incluir_nlp and self.modelos_carregados:
                await self._analise_nlp_avancada(analise)
            
            # 7. Análise preditiva
            await self._analise_preditiva(analise)
            
            # 8. Calcular confiança geral
            analise.confianca_geral = self._calcular_confianca_geral(analise)
            
            # Finalizar análise
            fim = datetime.now()
            analise.tempo_processamento = (fim - inicio).total_seconds()
            analise.status = StatusAnalise.CONCLUIDA
            
            # Salvar no cache
            self.cache_analises[id_analise] = analise
            self.historico_analises.append({
                'id': id_analise,
                'numero_processo': numero_processo,
                'timestamp': inicio,
                'tempo_processamento': analise.tempo_processamento
            })
            
            self.logger.info(f"Análise concluída: {numero_processo} em {analise.tempo_processamento:.2f}s")
            return analise
            
        except Exception as e:
            analise.status = StatusAnalise.ERRO
            analise.observacoes.append(f"Erro na análise: {str(e)}")
            self.logger.error(f"Erro na análise: {e}")
            return analise
    
    async def _processar_documentos(self, analise: AnaliseProcessualCompleta, 
                                  documentos: List[Dict], incluir_ocr: bool):
        """Processa documentos do processo"""
        
        self.logger.info(f"Processando {len(documentos)} documentos")
        
        for doc_info in documentos:
            try:
                doc_processado = {
                    'nome': doc_info.get('nome', ''),
                    'tipo': doc_info.get('tipo', ''),
                    'caminho': doc_info.get('caminho', ''),
                    'texto_extraido': '',
                    'tipo_detectado': TipoDocumento.OUTRO,
                    'metadados': {}
                }
                
                # Extrair texto
                if doc_info.get('caminho'):
                    texto = await self._extrair_texto_documento(doc_info['caminho'], incluir_ocr)
                    doc_processado['texto_extraido'] = texto
                elif doc_info.get('conteudo'):
                    doc_processado['texto_extraido'] = doc_info['conteudo']
                
                # Detectar tipo do documento
                if doc_processado['texto_extraido']:
                    doc_processado['tipo_detectado'] = self._detectar_tipo_documento(doc_processado['texto_extraido'])
                
                analise.documentos_analisados.append(doc_processado)
                
            except Exception as e:
                self.logger.error(f"Erro ao processar documento {doc_info.get('nome', '')}: {e}")
    
    async def _extrair_texto_documento(self, caminho: str, incluir_ocr: bool) -> str:
        """Extrai texto de documento"""
        
        caminho_path = Path(caminho)
        if not caminho_path.exists():
            return ""
        
        texto = ""
        extensao = caminho_path.suffix.lower()
        
        try:
            if extensao == '.pdf':
                # Extrair texto de PDF
                doc = fitz.open(caminho)
                for page in doc:
                    texto += page.get_text()
                doc.close()
                
                # Se não extraiu texto e OCR está habilitado
                if not texto.strip() and incluir_ocr and OCR_AVAILABLE:
                    texto = await self._ocr_pdf(caminho)
                    
            elif extensao in ['.jpg', '.jpeg', '.png', '.tiff'] and incluir_ocr and OCR_AVAILABLE:
                # OCR em imagens
                texto = await self._ocr_imagem(caminho)
                
            elif extensao == '.txt':
                # Arquivo texto
                with open(caminho, 'r', encoding='utf-8') as f:
                    texto = f.read()
                    
        except Exception as e:
            self.logger.error(f"Erro ao extrair texto de {caminho}: {e}")
        
        return texto
    
    async def _ocr_pdf(self, caminho: str) -> str:
        """OCR em PDF"""
        try:
            doc = fitz.open(caminho)
            texto_completo = ""
            
            for page_num in range(min(10, len(doc))):  # Limitar a 10 páginas
                page = doc[page_num]
                pix = page.get_pixmap()
                img_data = pix.tobytes("png")
                
                # Converter para PIL Image
                from io import BytesIO
                img = Image.open(BytesIO(img_data))
                
                # OCR
                texto_pagina = pytesseract.image_to_string(img, lang='por')
                texto_completo += texto_pagina + "\n"
            
            doc.close()
            return texto_completo
            
        except Exception as e:
            self.logger.error(f"Erro no OCR do PDF: {e}")
            return ""
    
    async def _ocr_imagem(self, caminho: str) -> str:
        """OCR em imagem"""
        try:
            img = Image.open(caminho)
            texto = pytesseract.image_to_string(img, lang='por')
            return texto
        except Exception as e:
            self.logger.error(f"Erro no OCR da imagem: {e}")
            return ""
    
    def _detectar_tipo_documento(self, texto: str) -> TipoDocumento:
        """Detecta tipo do documento pelo conteúdo"""
        
        texto_lower = texto.lower()
        
        # Padrões para identificação
        if any(word in texto_lower for word in ['petição inicial', 'excelentíssimo', 'vem respeitosamente']):
            return TipoDocumento.PETICAO_INICIAL
        elif any(word in texto_lower for word in ['contestação', 'impugnação', 'defesa']):
            return TipoDocumento.CONTESTACAO
        elif any(word in texto_lower for word in ['sentença', 'julgo procedente', 'julgo improcedente']):
            return TipoDocumento.SENTENCA
        elif any(word in texto_lower for word in ['acórdão', 'tribunal', 'recurso conhecido']):
            return TipoDocumento.ACÓRDAO
        elif any(word in texto_lower for word in ['decisão', 'defiro', 'indefiro']):
            return TipoDocumento.DECISAO
        elif any(word in texto_lower for word in ['despacho', 'intimem-se', 'cumpra-se']):
            return TipoDocumento.DESPACHO
        elif any(word in texto_lower for word in ['recurso', 'apelação', 'agravo']):
            return TipoDocumento.RECURSO
        elif any(word in texto_lower for word in ['certidão', 'certifico']):
            return TipoDocumento.CERTIDAO
        else:
            return TipoDocumento.OUTRO
    
    async def _extrair_informacoes_basicas(self, analise: AnaliseProcessualCompleta):
        """Extrai informações básicas do processo"""
        
        texto_completo = self._obter_texto_completo(analise)
        
        # Extrair classe processual
        analise.classe_processual = self._extrair_classe_processual(texto_completo)
        
        # Extrair assunto principal
        analise.assunto_principal = self._extrair_assunto_principal(texto_completo)
        
        # Extrair valor da causa
        analise.valor_causa = self._extrair_valor_causa(texto_completo)
        
        # Extrair tribunal/comarca
        analise.tribunal = self._extrair_tribunal(texto_completo)
        analise.comarca = self._extrair_comarca(texto_completo)
        
        self.logger.info("Informações básicas extraídas")
    
    async def _identificar_partes(self, analise: AnaliseProcessualCompleta):
        """Identifica partes processuais"""
        
        texto_completo = self._obter_texto_completo(analise)
        
        # Padrões para identificar partes
        patterns_partes = {
            'autor': re.compile(r'(?:autor|requerente|impetrante).*?:?\s*([^,;\n]+)', re.IGNORECASE),
            'reu': re.compile(r'(?:réu|requerido|impetrado).*?:?\s*([^,;\n]+)', re.IGNORECASE),
            'advogado': re.compile(r'(?:advogado|dr\.|dra\.).*?([^,;\n]+)', re.IGNORECASE)
        }
        
        for tipo, pattern in patterns_partes.items():
            matches = pattern.findall(texto_completo)
            for match in matches[:5]:  # Limitar a 5 por tipo
                nome = match.strip()
                if len(nome) > 3:  # Nome mínimo
                    parte = ParteProcessual(
                        nome=nome,
                        tipo=tipo,
                        confianca=0.7
                    )
                    
                    # Extrair documento se possível
                    parte.documento = self._extrair_documento_parte(texto_completo, nome)
                    
                    analise.partes.append(parte)
        
        self.logger.info(f"Identificadas {len(analise.partes)} partes")
    
    async def _extrair_pedidos(self, analise: AnaliseProcessualCompleta):
        """Extrai pedidos judiciais"""
        
        texto_completo = self._obter_texto_completo(analise)
        
        # Padrões para pedidos
        pattern_pedidos = re.compile(
            r'(?:requer|pede|postula|pleiteia).*?(?:que|a\s*v\.?\s*ex[aª]\.?).*?([^;.\n]+)',
            re.IGNORECASE | re.DOTALL
        )
        
        matches = pattern_pedidos.findall(texto_completo)
        for match in matches[:10]:  # Limitar a 10 pedidos
            pedido_texto = match.strip()
            if len(pedido_texto) > 10:
                pedido = PedidoJudicial(
                    descricao=pedido_texto,
                    tipo='principal',
                    valor_monetario=self._extrair_valor_do_texto(pedido_texto),
                    confianca=0.6
                )
                analise.pedidos.append(pedido)
        
        self.logger.info(f"Extraídos {len(analise.pedidos)} pedidos")
    
    async def _analisar_movimentacoes(self, analise: AnaliseProcessualCompleta):
        """Analisa movimentações processuais"""
        
        # Implementação básica - em produção integraria com dados do tribunal
        texto_completo = self._obter_texto_completo(analise)
        
        # Padrão para datas de movimentação
        pattern_mov = re.compile(
            r'(\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4})\s*[-:]?\s*([^.\n]{10,100})',
            re.IGNORECASE
        )
        
        matches = pattern_mov.findall(texto_completo)
        for data_str, descricao in matches[:20]:  # Limitar a 20
            try:
                data = self._parse_data(data_str)
                if data:
                    mov = MovimentacaoProcessual(
                        data=data,
                        tipo='movimentacao_geral',
                        descricao=descricao.strip()
                    )
                    analise.movimentacoes.append(mov)
            except:
                continue
        
        self.logger.info(f"Analisadas {len(analise.movimentacoes)} movimentações")
    
    async def _analise_nlp_avancada(self, analise: AnaliseProcessualCompleta):
        """Análise avançada com NLP"""
        
        if not self.modelos_carregados:
            return
        
        texto_completo = self._obter_texto_completo(analise)
        
        try:
            # Análise de entidades com spaCy
            if self.nlp_model:
                doc = self.nlp_model(texto_completo[:1000000])  # Limitar tamanho
                
                for ent in doc.ents:
                    entidade = EntidadeExtração(
                        tipo=ent.label_,
                        valor=ent.text,
                        confianca=0.8,
                        posicao_inicio=ent.start_char,
                        posicao_fim=ent.end_char,
                        contexto=texto_completo[max(0, ent.start_char-50):ent.end_char+50]
                    )
                    analise.entidades.append(entidade)
            
            # Análise de sentimento básica
            analise.sentimento_geral = self._analisar_sentimento(texto_completo)
            
            self.logger.info("Análise NLP avançada concluída")
            
        except Exception as e:
            self.logger.error(f"Erro na análise NLP: {e}")
    
    async def _analise_preditiva(self, analise: AnaliseProcessualCompleta):
        """Análise preditiva de resultados"""
        
        # Análise básica baseada em padrões
        texto_completo = self._obter_texto_completo(analise).lower()
        
        # Fatores positivos
        fatores_positivos = [
            'jurisprudência consolidada', 'precedente favorável', 'súmula',
            'dano evidente', 'prova cabal', 'documentos comprobatórios'
        ]
        
        # Fatores negativos
        fatores_negativos = [
            'falta de provas', 'jurisprudência contrária', 'prescrição',
            'decadência', 'carência de ação'
        ]
        
        score_positivo = sum(1 for fator in fatores_positivos if fator in texto_completo)
        score_negativo = sum(1 for fator in fatores_negativos if fator in texto_completo)
        
        # Calcular probabilidade básica
        if score_positivo + score_negativo > 0:
            analise.probabilidade_sucesso = score_positivo / (score_positivo + score_negativo)
        else:
            analise.probabilidade_sucesso = 0.5  # Neutro
        
        # Identificar riscos
        if 'prescrição' in texto_completo:
            analise.riscos_identificados.append("Possível prescrição da ação")
        if 'falta de provas' in texto_completo:
            analise.riscos_identificados.append("Insuficiência de provas")
        
        # Identificar oportunidades
        if 'súmula' in texto_completo:
            analise.oportunidades.append("Súmula favorável identificada")
        if 'precedente' in texto_completo:
            analise.oportunidades.append("Precedentes favoráveis")
        
        self.logger.info("Análise preditiva concluída")
    
    # MÉTODOS AUXILIARES
    
    def _obter_texto_completo(self, analise: AnaliseProcessualCompleta) -> str:
        """Obtém texto completo de todos os documentos"""
        return "\n\n".join([doc['texto_extraido'] for doc in analise.documentos_analisados])
    
    def _extrair_classe_processual(self, texto: str) -> Optional[str]:
        """Extrai classe processual"""
        patterns = [
            r'(?:classe|ação|processo)\s*(?:de\s*)?([^,;\n]{5,50})',
            r'(?:ação|procedimento)\s+([^,;\n]{5,50})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, texto, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None
    
    def _extrair_assunto_principal(self, texto: str) -> Optional[str]:
        """Extrai assunto principal"""
        patterns = [
            r'(?:assunto|matéria|objeto).*?:?\s*([^,;\n]{10,100})',
            r'(?:trata-se|cuida-se)\s+de\s+([^,;\n]{10,100})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, texto, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None
    
    def _extrair_valor_causa(self, texto: str) -> Optional[str]:
        """Extrai valor da causa"""
        patterns = [
            r'valor\s*da\s*causa.*?R\$\s*([\d.,]+)',
            r'valor\s*atribuído.*?R\$\s*([\d.,]+)',
            r'dá-se\s*à\s*causa.*?R\$\s*([\d.,]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, texto, re.IGNORECASE)
            if match:
                return f"R$ {match.group(1)}"
        return None
    
    def _extrair_tribunal(self, texto: str) -> Optional[str]:
        """Extrai tribunal"""
        tribunais = ['STF', 'STJ', 'TST', 'TRF', 'TRT', 'TJSP', 'TJRJ', 'TJMG', 'TJRS']
        
        for tribunal in tribunais:
            if tribunal in texto.upper():
                return tribunal
        return None
    
    def _extrair_comarca(self, texto: str) -> Optional[str]:
        """Extrai comarca"""
        pattern = r'comarca\s*de\s*([^,;\n]{3,50})'
        match = re.search(pattern, texto, re.IGNORECASE)
        return match.group(1).strip() if match else None
    
    def _extrair_documento_parte(self, texto: str, nome: str) -> Optional[str]:
        """Extrai documento da parte"""
        # Buscar CPF/CNPJ próximo ao nome
        nome_pos = texto.find(nome)
        if nome_pos != -1:
            contexto = texto[nome_pos:nome_pos+500]
            
            cpf_match = self.pattern_cpf.search(contexto)
            if cpf_match:
                return cpf_match.group()
            
            cnpj_match = self.pattern_cnpj.search(contexto)
            if cnpj_match:
                return cnpj_match.group()
        
        return None
    
    def _extrair_valor_do_texto(self, texto: str) -> Optional[str]:
        """Extrai valor monetário do texto"""
        match = self.pattern_valor.search(texto)
        return match.group() if match else None
    
    def _parse_data(self, data_str: str) -> Optional[datetime]:
        """Converte string em datetime"""
        formats = ['%d/%m/%Y', '%d-%m-%Y', '%d.%m.%Y']
        
        for fmt in formats:
            try:
                return datetime.strptime(data_str, fmt)
            except ValueError:
                continue
        return None
    
    def _analisar_sentimento(self, texto: str) -> str:
        """Análise básica de sentimento"""
        palavras_positivas = ['procedente', 'deferido', 'favorável', 'sucesso', 'ganho']
        palavras_negativas = ['improcedente', 'indeferido', 'desfavorável', 'perda', 'negado']
        
        texto_lower = texto.lower()
        score_pos = sum(1 for palavra in palavras_positivas if palavra in texto_lower)
        score_neg = sum(1 for palavra in palavras_negativas if palavra in texto_lower)
        
        if score_pos > score_neg:
            return "positivo"
        elif score_neg > score_pos:
            return "negativo"
        else:
            return "neutro"
    
    def _calcular_confianca_geral(self, analise: AnaliseProcessualCompleta) -> float:
        """Calcula confiança geral da análise"""
        
        scores = []
        
        # Score baseado na quantidade de informações extraídas
        if analise.classe_processual:
            scores.append(0.8)
        if analise.partes:
            scores.append(0.9)
        if analise.pedidos:
            scores.append(0.7)
        if analise.valor_causa:
            scores.append(0.6)
        
        # Score baseado na qualidade dos documentos
        docs_com_texto = len([d for d in analise.documentos_analisados if d['texto_extraido']])
        if docs_com_texto > 0:
            scores.append(min(1.0, docs_com_texto / len(analise.documentos_analisados)))
        
        return np.mean(scores) if scores else 0.3
    
    # MÉTODOS PÚBLICOS
    
    def obter_estatisticas(self) -> Dict[str, Any]:
        """Obtém estatísticas do sistema"""
        
        return {
            'total_analises': len(self.historico_analises),
            'analises_em_cache': len(self.cache_analises),
            'modelos_carregados': self.modelos_carregados,
            'ocr_disponivel': OCR_AVAILABLE,
            'nlp_disponivel': NLP_AVAILABLE,
            'tempo_medio_processamento': np.mean([
                a['tempo_processamento'] for a in self.historico_analises 
                if a.get('tempo_processamento')
            ]) if self.historico_analises else 0
        }

# Função de conveniência
async def analisar_processo_ia(numero_processo: str, 
                             documentos: List[Dict]) -> AnaliseProcessualCompleta:
    """
    🧠 FUNÇÃO DE CONVENIÊNCIA
    Análise rápida de processo com IA
    """
    analisador = AnaliseProcessualIA()
    return await analisador.analisar_processo_completo(numero_processo, documentos)

# Exemplo de uso
if __name__ == "__main__":
    async def testar_analise_ia():
        """🧪 TESTE DA ANÁLISE PROCESSUAL IA"""
        
        print("🧠 TESTANDO ANÁLISE PROCESSUAL IA")
        print("=" * 60)
        
        analisador = AnaliseProcessualIA()
        
        # Documentos de teste
        documentos_teste = [
            {
                'nome': 'petição_inicial.txt',
                'tipo': 'peticao_inicial',
                'conteudo': """
                EXCELENTÍSSIMO SENHOR DOUTOR JUIZ DE DIREITO DA VARA CÍVEL
                
                JOÃO DA SILVA, brasileiro, solteiro, engenheiro, portador do CPF 123.456.789-00,
                residente e domiciliado na Rua das Flores, 123, São Paulo/SP,
                
                vem respeitosamente à presença de Vossa Excelência propor
                
                AÇÃO DE INDENIZAÇÃO POR DANOS MORAIS
                
                em face de BANCO PREMIUM S.A., pessoa jurídica de direito privado,
                CNPJ 12.345.678/0001-99, pelos motivos de fato e de direito que passa a expor:
                
                I - DOS FATOS
                O autor teve seu nome negativado indevidamente pelo réu.
                
                II - DOS PEDIDOS
                Requer a condenação do réu ao pagamento de R$ 15.000,00 a título de danos morais.
                
                Dá-se à causa o valor de R$ 15.000,00.
                """
            }
        ]
        
        # Executar análise
        print("🔍 Executando análise...")
        analise = await analisador.analisar_processo_completo(
            "1234567-89.2023.8.26.0001",
            documentos_teste
        )
        
        # Exibir resultados
        print(f"\n📋 RESULTADOS DA ANÁLISE")
        print("-" * 40)
        print(f"Status: {analise.status.value}")
        print(f"Confiança geral: {analise.confianca_geral:.1%}")
        print(f"Tempo processamento: {analise.tempo_processamento:.2f}s")
        
        if analise.classe_processual:
            print(f"Classe: {analise.classe_processual}")
        if analise.valor_causa:
            print(f"Valor da causa: {analise.valor_causa}")
        
        print(f"\n👥 PARTES ({len(analise.partes)})")
        for parte in analise.partes:
            print(f"  • {parte.tipo}: {parte.nome}")
            if parte.documento:
                print(f"    Doc: {parte.documento}")
        
        print(f"\n📝 PEDIDOS ({len(analise.pedidos)})")
        for pedido in analise.pedidos:
            print(f"  • {pedido.tipo}: {pedido.descricao[:80]}...")
            if pedido.valor_monetario:
                print(f"    Valor: {pedido.valor_monetario}")
        
        if analise.probabilidade_sucesso is not None:
            print(f"\n📊 ANÁLISE PREDITIVA")
            print(f"Probabilidade sucesso: {analise.probabilidade_sucesso:.1%}")
        
        if analise.riscos_identificados:
            print(f"Riscos: {len(analise.riscos_identificados)}")
        if analise.oportunidades:
            print(f"Oportunidades: {len(analise.oportunidades)}")
        
        # Estatísticas do sistema
        print(f"\n📈 ESTATÍSTICAS DO SISTEMA")
        stats = analisador.obter_estatisticas()
        print(f"Modelos carregados: {stats['modelos_carregados']}")
        print(f"OCR disponível: {stats['ocr_disponivel']}")
        print(f"NLP disponível: {stats['nlp_disponivel']}")
        
        print(f"\n🎉 TESTE CONCLUÍDO!")
        print("🧠 ANÁLISE PROCESSUAL IA FUNCIONAL!")
    
    # Executar teste
    asyncio.run(testar_analise_ia())