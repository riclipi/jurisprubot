"""
🤖 GERADOR DE MINUTAS INTELIGENTE - IA AVANÇADA
Sistema inteligente para geração automática de minutas jurídicas
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
import random

# Integração com outros módulos
from .analise_processual_ia import AnaliseProcessualCompleta, ParteProcessual, PedidoJudicial

class TipoMinuta(Enum):
    DESPACHO_SANEADOR = "despacho_saneador"
    DECISAO_INTERLOCUTORIA = "decisao_interlocutoria"
    SENTENCA = "sentenca"
    ACORDAO = "acordao"
    MANIFESTACAO = "manifestacao"
    PARECER = "parecer"
    PETICAO = "peticao"
    CONTESTACAO = "contestacao"
    RECURSO = "recurso"
    EMBARGOS = "embargos"

class NivelComplexidade(Enum):
    SIMPLES = "simples"
    MEDIO = "medio"
    COMPLEXO = "complexo"
    MUITO_COMPLEXO = "muito_complexo"

class EstiloRedacao(Enum):
    FORMAL = "formal"
    TECNICO = "tecnico"
    DIDATICO = "didatico"
    PERSUASIVO = "persuasivo"
    OBJETIVO = "objetivo"

@dataclass
class ConfiguracaoMinuta:
    """Configuração para geração de minuta"""
    tipo: TipoMinuta
    estilo: EstiloRedacao = EstiloRedacao.FORMAL
    complexidade: NivelComplexidade = NivelComplexidade.MEDIO
    incluir_jurisprudencia: bool = True
    incluir_doutrina: bool = False
    limite_paginas: int = 10
    usar_templates_personalizados: bool = False
    metadados_extras: Dict[str, Any] = field(default_factory=dict)

@dataclass
class FundamentacaoJuridica:
    """Fundamentação jurídica para a minuta"""
    dispositivos_legais: List[str] = field(default_factory=list)
    jurisprudencia: List[str] = field(default_factory=list)
    doutrina: List[str] = field(default_factory=list)
    precedentes: List[str] = field(default_factory=list)
    principios: List[str] = field(default_factory=list)

@dataclass
class MinutaGerada:
    """Resultado da geração de minuta"""
    id_minuta: str
    tipo: TipoMinuta
    titulo: str
    conteudo: str
    fundamentacao: FundamentacaoJuridica
    numero_processo: str
    data_geracao: datetime
    tempo_geracao: float
    qualidade_score: float
    observacoes: List[str] = field(default_factory=list)
    metadados: Dict[str, Any] = field(default_factory=dict)

class GeradorMinutasInteligente:
    """
    🤖 GERADOR INTELIGENTE DE MINUTAS JURÍDICAS
    
    Funcionalidades avançadas:
    - Geração automática baseada em análise processual
    - Templates inteligentes adaptativos
    - Fundamentação jurídica automática
    - Integração com jurisprudência em tempo real
    - Múltiplos estilos de redação
    - Controle de qualidade automático
    - Personalização por área do direito
    - Geração massiva de minutas
    """
    
    def __init__(self):
        self.setup_logging()
        self._inicializar_templates()
        self._inicializar_fundamentos()
        self._inicializar_ia()
        self._inicializar_cache()
    
    def setup_logging(self):
        """Configura sistema de logs"""
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def _inicializar_templates(self):
        """Inicializa templates de minutas"""
        
        self.templates = {
            TipoMinuta.DESPACHO_SANEADOR: {
                'estrutura': [
                    'cabecalho',
                    'relatório',
                    'fundamentacao',
                    'dispositivo',
                    'assinatura'
                ],
                'template': """
{cabecalho}

{relatorio}

É o relatório.

FUNDAMENTO e DECIDO.

{fundamentacao}

{dispositivo}

{local_data}

{assinatura}
                """.strip()
            },
            
            TipoMinuta.SENTENCA: {
                'estrutura': [
                    'cabecalho',
                    'relatório',
                    'fundamentacao',
                    'dispositivo',
                    'assinatura'
                ],
                'template': """
{cabecalho}

{relatorio}

É o relatório. Decido.

{fundamentacao}

DISPOSITIVO

{dispositivo}

{custas_honorarios}

{local_data}

{assinatura}
                """.strip()
            },
            
            TipoMinuta.DECISAO_INTERLOCUTORIA: {
                'estrutura': [
                    'cabecalho',
                    'breve_relato',
                    'fundamentacao',
                    'dispositivo'
                ],
                'template': """
{cabecalho}

{breve_relato}

{fundamentacao}

{dispositivo}

{local_data}

{assinatura}
                """.strip()
            },
            
            TipoMinuta.MANIFESTACAO: {
                'estrutura': [
                    'cabecalho',
                    'introducao',
                    'argumentacao',
                    'pedidos',
                    'fecho'
                ],
                'template': """
{cabecalho}

{introducao}

{argumentacao}

{pedidos}

{fecho}

{local_data}

{assinatura}
                """.strip()
            },
            
            TipoMinuta.RECURSO: {
                'estrutura': [
                    'cabecalho',
                    'preliminares',
                    'merito',
                    'pedidos',
                    'fecho'
                ],
                'template': """
{cabecalho}

PRELIMINARES

{preliminares}

MÉRITO

{merito}

PEDIDOS

{pedidos}

{fecho}

{local_data}

{assinatura}
                """.strip()
            }
        }
        
        self.logger.info(f"Templates inicializados: {len(self.templates)} tipos")
    
    def _inicializar_fundamentos(self):
        """Inicializa base de fundamentação jurídica"""
        
        self.base_fundamentos = {
            'responsabilidade_civil': {
                'dispositivos': [
                    'CC, art. 186',
                    'CC, art. 927',
                    'CC, art. 944'
                ],
                'jurisprudencia': [
                    'STJ, REsp 1.740.868/RS',
                    'STJ, Súmula 385',
                    'STF, RE 636.331/RJ'
                ],
                'principios': [
                    'Princípio da reparação integral',
                    'Princípio da proporcionalidade'
                ]
            },
            
            'consumidor': {
                'dispositivos': [
                    'CDC, art. 6º',
                    'CDC, art. 14',
                    'CDC, art. 42'
                ],
                'jurisprudencia': [
                    'STJ, Súmula 297',
                    'STJ, REsp 1.568.855/RJ',
                    'STJ, AgInt no AREsp 1.293.356/SP'
                ],
                'principios': [
                    'Princípio da proteção do consumidor',
                    'Princípio da boa-fé objetiva'
                ]
            },
            
            'trabalhista': {
                'dispositivos': [
                    'CLT, art. 7º',
                    'CLT, art. 59',
                    'CF/88, art. 7º'
                ],
                'jurisprudencia': [
                    'TST, Súmula 291',
                    'TST, OJ 342',
                    'TST, Súmula 428'
                ],
                'principios': [
                    'Princípio da proteção do trabalhador',
                    'Princípio da primazia da realidade'
                ]
            },
            
            'processual_civil': {
                'dispositivos': [
                    'CPC, art. 139',
                    'CPC, art. 330',
                    'CPC, art. 355'
                ],
                'jurisprudencia': [
                    'STJ, REsp 1.235.717/RS',
                    'STJ, Súmula 318',
                    'STF, RE 631.240/MG'
                ],
                'principios': [
                    'Princípio da duração razoável do processo',
                    'Princípio do contraditório'
                ]
            }
        }
        
        self.logger.info("Base de fundamentação inicializada")
    
    def _inicializar_ia(self):
        """Inicializa componentes de IA"""
        
        # Vocabulário jurídico
        self.vocabulario_juridico = {
            'conectivos_formais': [
                'destarte', 'outrossim', 'ademais', 'nesse sentido',
                'por conseguinte', 'dessa forma', 'assim sendo',
                'nessa esteira', 'nesse diapasão', 'portanto'
            ],
            
            'expressoes_decisorias': [
                'defiro', 'indefiro', 'homologo', 'julgo procedente',
                'julgo improcedente', 'julgo parcialmente procedente',
                'reconheço', 'declaro', 'determino'
            ],
            
            'vocabulario_tecnico': [
                'configurado', 'caracterizado', 'evidenciado',
                'comprovado', 'demonstrado', 'consolidado',
                'pacificado', 'sedimentado', 'cristalino'
            ]
        }
        
        # Padrões de redação por estilo
        self.estilos_redacao = {
            EstiloRedacao.FORMAL: {
                'conectivos_preferidos': ['destarte', 'outrossim', 'ademais'],
                'tratamento': 'Vossa Excelência',
                'tempo_verbal': 'presente',
                'pessoa': 'terceira'
            },
            
            EstiloRedacao.TECNICO: {
                'conectivos_preferidos': ['portanto', 'assim', 'dessa forma'],
                'tratamento': 'o Juízo',
                'tempo_verbal': 'presente',
                'pessoa': 'terceira'
            },
            
            EstiloRedacao.DIDATICO: {
                'conectivos_preferidos': ['assim', 'dessa forma', 'por isso'],
                'tratamento': 'Vossa Excelência',
                'tempo_verbal': 'presente',
                'pessoa': 'primeira'
            },
            
            EstiloRedacao.PERSUASIVO: {
                'conectivos_preferidos': ['nesse sentido', 'por conseguinte'],
                'tratamento': 'Vossa Excelência',
                'tempo_verbal': 'presente',
                'pessoa': 'primeira'
            }
        }
        
        self.logger.info("Componentes de IA inicializados")
    
    def _inicializar_cache(self):
        """Inicializa sistema de cache"""
        self.cache_minutas = {}
        self.cache_fundamentacao = {}
        self.historico_geracoes = []
    
    async def gerar_minuta_automatica(self, 
                                    analise_processual: AnaliseProcessualCompleta,
                                    configuracao: ConfiguracaoMinuta) -> MinutaGerada:
        """
        🤖 GERAÇÃO AUTOMÁTICA DE MINUTA
        Gera minuta baseada na análise processual
        """
        
        inicio = datetime.now()
        id_minuta = f"minuta_{analise_processual.numero_processo}_{int(inicio.timestamp())}"
        
        self.logger.info(f"Gerando minuta {configuracao.tipo.value} para {analise_processual.numero_processo}")
        
        try:
            # 1. Preparar contexto
            contexto = await self._preparar_contexto(analise_processual, configuracao)
            
            # 2. Gerar fundamentação jurídica
            fundamentacao = await self._gerar_fundamentacao(analise_processual, configuracao)
            
            # 3. Selecionar template
            template_info = self.templates.get(configuracao.tipo)
            if not template_info:
                raise ValueError(f"Template não encontrado para {configuracao.tipo.value}")
            
            # 4. Gerar seções da minuta
            secoes = await self._gerar_secoes(analise_processual, configuracao, contexto, fundamentacao)
            
            # 5. Montar minuta final
            conteudo = self._montar_minuta(template_info, secoes, configuracao)
            
            # 6. Controle de qualidade
            qualidade_score = await self._avaliar_qualidade(conteudo, configuracao)
            
            # 7. Criar resultado
            fim = datetime.now()
            minuta = MinutaGerada(
                id_minuta=id_minuta,
                tipo=configuracao.tipo,
                titulo=self._gerar_titulo(analise_processual, configuracao),
                conteudo=conteudo,
                fundamentacao=fundamentacao,
                numero_processo=analise_processual.numero_processo,
                data_geracao=fim,
                tempo_geracao=(fim - inicio).total_seconds(),
                qualidade_score=qualidade_score
            )
            
            # 8. Salvar no cache
            self.cache_minutas[id_minuta] = minuta
            self.historico_geracoes.append({
                'id': id_minuta,
                'tipo': configuracao.tipo.value,
                'processo': analise_processual.numero_processo,
                'timestamp': inicio,
                'qualidade': qualidade_score
            })
            
            self.logger.info(f"Minuta gerada: {id_minuta} (qualidade: {qualidade_score:.2f})")
            return minuta
            
        except Exception as e:
            self.logger.error(f"Erro na geração de minuta: {e}")
            raise
    
    async def _preparar_contexto(self, analise: AnaliseProcessualCompleta, 
                               config: ConfiguracaoMinuta) -> Dict[str, Any]:
        """Prepara contexto para geração"""
        
        # Identificar área do direito
        area_direito = self._identificar_area_direito(analise)
        
        # Extrair partes principais
        autor = self._obter_parte_por_tipo(analise.partes, 'autor')
        reu = self._obter_parte_por_tipo(analise.partes, 'reu')
        
        contexto = {
            'numero_processo': analise.numero_processo,
            'area_direito': area_direito,
            'autor': autor.nome if autor else 'PARTE AUTORA',
            'reu': reu.nome if reu else 'PARTE RÉ',
            'classe_processual': analise.classe_processual or 'Ação',
            'assunto_principal': analise.assunto_principal or 'matéria em questão',
            'valor_causa': analise.valor_causa or 'valor estimado',
            'tribunal': analise.tribunal or 'Juízo',
            'comarca': analise.comarca or 'comarca competente',
            'data_atual': datetime.now().strftime('%d de %B de %Y'),
            'ano_atual': datetime.now().year
        }
        
        return contexto
    
    async def _gerar_fundamentacao(self, analise: AnaliseProcessualCompleta,
                                 config: ConfiguracaoMinuta) -> FundamentacaoJuridica:
        """Gera fundamentação jurídica automática"""
        
        area_direito = self._identificar_area_direito(analise)
        
        fundamentacao = FundamentacaoJuridica()
        
        # Buscar fundamentos na base
        if area_direito in self.base_fundamentos:
            base = self.base_fundamentos[area_direito]
            
            # Dispositivos legais
            fundamentacao.dispositivos_legais = base.get('dispositivos', [])[:5]
            
            # Jurisprudência
            if config.incluir_jurisprudencia:
                fundamentacao.jurisprudencia = base.get('jurisprudencia', [])[:3]
            
            # Princípios
            fundamentacao.principios = base.get('principios', [])[:2]
        
        # Adicionar fundamentos específicos baseados na análise
        if analise.pedidos:
            fundamentacao = await self._enriquecer_fundamentacao(
                fundamentacao, analise.pedidos, area_direito
            )
        
        return fundamentacao
    
    async def _gerar_secoes(self, analise: AnaliseProcessualCompleta,
                          config: ConfiguracaoMinuta,
                          contexto: Dict[str, Any],
                          fundamentacao: FundamentacaoJuridica) -> Dict[str, str]:
        """Gera seções específicas da minuta"""
        
        secoes = {}
        
        # Cabeçalho
        secoes['cabecalho'] = self._gerar_cabecalho(analise, contexto, config)
        
        # Relatório
        if config.tipo in [TipoMinuta.DESPACHO_SANEADOR, TipoMinuta.SENTENCA]:
            secoes['relatorio'] = self._gerar_relatorio(analise, contexto, config)
        
        # Breve relato (para decisões)
        if config.tipo == TipoMinuta.DECISAO_INTERLOCUTORIA:
            secoes['breve_relato'] = self._gerar_breve_relato(analise, contexto)
        
        # Fundamentação
        secoes['fundamentacao'] = await self._gerar_fundamentacao_textual(
            analise, fundamentacao, config
        )
        
        # Dispositivo
        secoes['dispositivo'] = self._gerar_dispositivo(analise, config, contexto)
        
        # Custas e honorários (para sentenças)
        if config.tipo == TipoMinuta.SENTENCA:
            secoes['custas_honorarios'] = self._gerar_custas_honorarios(analise, contexto)
        
        # Seções específicas para manifestações/recursos
        if config.tipo in [TipoMinuta.MANIFESTACAO, TipoMinuta.RECURSO]:
            secoes.update(self._gerar_secoes_especiais(analise, config, contexto))
        
        # Elementos finais
        secoes['local_data'] = f"São Paulo, {contexto['data_atual']}."
        secoes['assinatura'] = self._gerar_assinatura(config)
        
        return secoes
    
    def _gerar_cabecalho(self, analise: AnaliseProcessualCompleta, 
                        contexto: Dict, config: ConfiguracaoMinuta) -> str:
        """Gera cabeçalho da minuta"""
        
        if config.tipo == TipoMinuta.SENTENCA:
            return f"""
PROCESSO Nº {contexto['numero_processo']}

{contexto['classe_processual'].upper()}

AUTOR: {contexto['autor']}
RÉU: {contexto['reu']}
            """.strip()
        
        elif config.tipo == TipoMinuta.DESPACHO_SANEADOR:
            return f"""
Processo nº {contexto['numero_processo']}
{contexto['classe_processual']}
Autor: {contexto['autor']}
Réu: {contexto['reu']}

DESPACHO SANEADOR
            """.strip()
        
        else:
            return f"""
Processo nº {contexto['numero_processo']}
{contexto['classe_processual']}
            """.strip()
    
    def _gerar_relatorio(self, analise: AnaliseProcessualCompleta,
                        contexto: Dict, config: ConfiguracaoMinuta) -> str:
        """Gera relatório da minuta"""
        
        estilo_cfg = self.estilos_redacao[config.estilo]
        conectivo = random.choice(estilo_cfg['conectivos_preferidos'])
        
        relatorio = f"""
Trata-se de {contexto['classe_processual']} ajuizada por {contexto['autor']} em face de {contexto['reu']}.
        """.strip()
        
        # Adicionar informações sobre pedidos
        if analise.pedidos:
            pedido_principal = analise.pedidos[0]
            relatorio += f"\n\nO autor postula {pedido_principal.descricao[:100]}."
        
        # Adicionar valor da causa
        if contexto['valor_causa']:
            relatorio += f"\n\nDá-se à causa o valor de {contexto['valor_causa']}."
        
        # Adicionar movimentações importantes
        if analise.movimentacoes and len(analise.movimentacoes) > 0:
            relatorio += f"\n\n{conectivo.capitalize()}, o processo encontra-se em regular tramitação."
        
        return relatorio
    
    def _gerar_breve_relato(self, analise: AnaliseProcessualCompleta, 
                           contexto: Dict) -> str:
        """Gera breve relato para decisões"""
        
        return f"""
Cuida-se de {contexto['classe_processual']} em que {contexto['autor']} postula em face de {contexto['reu']} {contexto['assunto_principal']}.
        """.strip()
    
    async def _gerar_fundamentacao_textual(self, analise: AnaliseProcessualCompleta,
                                         fundamentacao: FundamentacaoJuridica,
                                         config: ConfiguracaoMinuta) -> str:
        """Gera fundamentação em texto"""
        
        estilo_cfg = self.estilos_redacao[config.estilo]
        conectivos = estilo_cfg['conectivos_preferidos']
        
        texto_fundamentacao = []
        
        # Análise do mérito
        if analise.pedidos:
            texto_fundamentacao.append("A análise do mérito revela que:")
            
            for i, pedido in enumerate(analise.pedidos[:3]):
                if pedido.fundamentacao:
                    fund_texto = ', '.join(pedido.fundamentacao[:2])
                    texto_fundamentacao.append(f"- {fund_texto}")
        
        # Dispositivos legais
        if fundamentacao.dispositivos_legais:
            conectivo = random.choice(conectivos)
            texto_fundamentacao.append(f"\n{conectivo.capitalize()}, aplicam-se à espécie:")
            
            for dispositivo in fundamentacao.dispositivos_legais:
                texto_fundamentacao.append(f"- {dispositivo}")
        
        # Jurisprudência
        if fundamentacao.jurisprudencia:
            conectivo = random.choice(conectivos)
            texto_fundamentacao.append(f"\n{conectivo.capitalize()}, a jurisprudência é pacífica:")
            
            for jurisprudencia in fundamentacao.jurisprudencia:
                texto_fundamentacao.append(f"- {jurisprudencia}")
        
        # Princípios
        if fundamentacao.principios:
            conectivo = random.choice(conectivos)
            texto_fundamentacao.append(f"\n{conectivo.capitalize()}, aplicam-se os seguintes princípios:")
            
            for principio in fundamentacao.principios:
                texto_fundamentacao.append(f"- {principio}")
        
        # Análise preditiva (se disponível)
        if analise.probabilidade_sucesso is not None:
            if analise.probabilidade_sucesso > 0.7:
                texto_fundamentacao.append("\nA pretensão mostra-se procedente, considerando os elementos dos autos.")
            elif analise.probabilidade_sucesso < 0.3:
                texto_fundamentacao.append("\nA pretensão apresenta óbices que impedem seu acolhimento.")
            else:
                texto_fundamentacao.append("\nA matéria demanda análise cuidadosa dos elementos probatórios.")
        
        return '\n'.join(texto_fundamentacao)
    
    def _gerar_dispositivo(self, analise: AnaliseProcessualCompleta,
                          config: ConfiguracaoMinuta, contexto: Dict) -> str:
        """Gera dispositivo da minuta"""
        
        if config.tipo == TipoMinuta.DESPACHO_SANEADOR:
            dispositivo = [
                "Ante o exposto, DETERMINO:",
                "1. A citação da parte requerida;",
                "2. Após, venham os autos conclusos para sentença."
            ]
            
        elif config.tipo == TipoMinuta.SENTENCA:
            # Baseado na análise preditiva
            if analise.probabilidade_sucesso and analise.probabilidade_sucesso > 0.6:
                dispositivo = [
                    "Ante o exposto, JULGO PROCEDENTE o pedido formulado na inicial.",
                    f"Condeno {contexto['reu']} ao cumprimento da obrigação pleiteada."
                ]
            else:
                dispositivo = [
                    "Ante o exposto, JULGO IMPROCEDENTE o pedido formulado na inicial.",
                    "Fica extinto o processo com resolução do mérito, nos termos do art. 487, I, do CPC."
                ]
                
        elif config.tipo == TipoMinuta.DECISAO_INTERLOCUTORIA:
            dispositivo = [
                "Ante o exposto, DEFIRO o pedido formulado.",
                "Intime-se."
            ]
            
        else:
            dispositivo = ["Requer deferimento."]
        
        return '\n'.join(dispositivo)
    
    def _gerar_custas_honorarios(self, analise: AnaliseProcessualCompleta, 
                                contexto: Dict) -> str:
        """Gera seção de custas e honorários"""
        
        if analise.probabilidade_sucesso and analise.probabilidade_sucesso > 0.6:
            return f"""
Condeno {contexto['reu']} ao pagamento das custas e despesas processuais, bem como honorários advocatícios que fixo em 10% sobre o valor da condenação.
            """.strip()
        else:
            return f"""
Condeno {contexto['autor']} ao pagamento das custas e despesas processuais, bem como honorários advocatícios que fixo em R$ 1.000,00.
            """.strip()
    
    def _gerar_secoes_especiais(self, analise: AnaliseProcessualCompleta,
                               config: ConfiguracaoMinuta, contexto: Dict) -> Dict[str, str]:
        """Gera seções especiais para manifestações e recursos"""
        
        secoes = {}
        
        if config.tipo == TipoMinuta.MANIFESTACAO:
            secoes['introducao'] = f"""
{contexto['autor']}, nos autos do processo em epígrafe, vem respeitosamente à presença de Vossa Excelência apresentar manifestação.
            """.strip()
            
            secoes['argumentacao'] = "A presente manifestação se justifica pelos argumentos que passa a expor."
            
            secoes['pedidos'] = "Diante do exposto, requer seja a presente manifestação recebida e processada."
            
            secoes['fecho'] = "Termos em que pede deferimento."
        
        elif config.tipo == TipoMinuta.RECURSO:
            secoes['preliminares'] = "Não há preliminares a suscitar."
            
            secoes['merito'] = "A decisão recorrida merece reforma pelos fundamentos que seguem."
            
            secoes['pedidos'] = """
Ante o exposto, requer:
a) O recebimento do presente recurso;
b) A reforma da decisão recorrida.
            """.strip()
            
            secoes['fecho'] = "Nestes termos, pede e espera deferimento."
        
        return secoes
    
    def _gerar_assinatura(self, config: ConfiguracaoMinuta) -> str:
        """Gera assinatura conforme o tipo"""
        
        if config.tipo in [TipoMinuta.SENTENCA, TipoMinuta.DESPACHO_SANEADOR, TipoMinuta.DECISAO_INTERLOCUTORIA]:
            return """

[Nome do Magistrado]
Juiz de Direito
            """.strip()
        else:
            return """

[Nome do Advogado]
OAB/SP [número]
            """.strip()
    
    def _montar_minuta(self, template_info: Dict, secoes: Dict[str, str], 
                      config: ConfiguracaoMinuta) -> str:
        """Monta minuta final usando template"""
        
        template = template_info['template']
        
        # Substituir seções no template
        conteudo = template.format(**secoes)
        
        # Ajustes finais de formatação
        conteudo = self._ajustar_formatacao(conteudo, config)
        
        return conteudo
    
    def _ajustar_formatacao(self, conteudo: str, config: ConfiguracaoMinuta) -> str:
        """Ajusta formatação final"""
        
        # Remover linhas vazias excessivas
        conteudo = re.sub(r'\n{3,}', '\n\n', conteudo)
        
        # Ajustar espaçamento
        conteudo = conteudo.strip()
        
        # Aplicar estilo específico
        if config.estilo == EstiloRedacao.FORMAL:
            # Aumentar formalidade
            conteudo = conteudo.replace('assim', 'destarte')
            conteudo = conteudo.replace('portanto', 'outrossim')
        
        return conteudo
    
    async def _avaliar_qualidade(self, conteudo: str, config: ConfiguracaoMinuta) -> float:
        """Avalia qualidade da minuta gerada"""
        
        score = 0.5  # Base
        
        # Verificar estrutura
        if '{' not in conteudo and '}' not in conteudo:
            score += 0.2  # Template preenchido corretamente
        
        # Verificar tamanho adequado
        palavras = len(conteudo.split())
        if 100 <= palavras <= 2000:
            score += 0.1
        
        # Verificar presença de elementos jurídicos
        elementos_juridicos = ['art.', 'lei', 'código', 'jurisprudência', 'precedente']
        elementos_encontrados = sum(1 for elemento in elementos_juridicos if elemento.lower() in conteudo.lower())
        score += (elementos_encontrados / len(elementos_juridicos)) * 0.2
        
        return min(1.0, score)
    
    # MÉTODOS AUXILIARES
    
    def _identificar_area_direito(self, analise: AnaliseProcessualCompleta) -> str:
        """Identifica área do direito predominante"""
        
        if not analise.assunto_principal:
            return 'processual_civil'
        
        assunto = analise.assunto_principal.lower()
        
        if any(termo in assunto for termo in ['consumidor', 'banco', 'negativação', 'cdc']):
            return 'consumidor'
        elif any(termo in assunto for termo in ['dano', 'moral', 'responsabilidade', 'indenização']):
            return 'responsabilidade_civil'
        elif any(termo in assunto for termo in ['trabalho', 'emprego', 'clt', 'horas extras']):
            return 'trabalhista'
        else:
            return 'processual_civil'
    
    def _obter_parte_por_tipo(self, partes: List[ParteProcessual], tipo: str) -> Optional[ParteProcessual]:
        """Obtém parte processual por tipo"""
        for parte in partes:
            if parte.tipo.lower() == tipo.lower():
                return parte
        return None
    
    def _gerar_titulo(self, analise: AnaliseProcessualCompleta, config: ConfiguracaoMinuta) -> str:
        """Gera título da minuta"""
        
        tipo_nome = {
            TipoMinuta.DESPACHO_SANEADOR: "Despacho Saneador",
            TipoMinuta.SENTENCA: "Sentença",
            TipoMinuta.DECISAO_INTERLOCUTORIA: "Decisão Interlocutória",
            TipoMinuta.MANIFESTACAO: "Manifestação",
            TipoMinuta.RECURSO: "Recurso"
        }
        
        nome = tipo_nome.get(config.tipo, "Minuta")
        return f"{nome} - Processo {analise.numero_processo}"
    
    async def _enriquecer_fundamentacao(self, fundamentacao: FundamentacaoJuridica,
                                       pedidos: List[PedidoJudicial], 
                                       area_direito: str) -> FundamentacaoJuridica:
        """Enriquece fundamentação com base nos pedidos"""
        
        # Adicionar dispositivos específicos baseados nos pedidos
        for pedido in pedidos:
            if 'indenização' in pedido.descricao.lower():
                if 'CC, art. 186' not in fundamentacao.dispositivos_legais:
                    fundamentacao.dispositivos_legais.append('CC, art. 186')
            
            if 'dano moral' in pedido.descricao.lower():
                if 'CC, art. 927' not in fundamentacao.dispositivos_legais:
                    fundamentacao.dispositivos_legais.append('CC, art. 927')
        
        return fundamentacao
    
    # MÉTODOS PÚBLICOS
    
    async def gerar_lote_minutas(self, analises: List[AnaliseProcessualCompleta],
                                configuracao: ConfiguracaoMinuta) -> List[MinutaGerada]:
        """Gera lote de minutas em paralelo"""
        
        self.logger.info(f"Gerando lote de {len(analises)} minutas")
        
        tarefas = [
            self.gerar_minuta_automatica(analise, configuracao)
            for analise in analises
        ]
        
        minutas = await asyncio.gather(*tarefas, return_exceptions=True)
        
        minutas_validas = [m for m in minutas if isinstance(m, MinutaGerada)]
        erros = [m for m in minutas if isinstance(m, Exception)]
        
        self.logger.info(f"Lote concluído: {len(minutas_validas)} sucessos, {len(erros)} erros")
        
        return minutas_validas
    
    def obter_estatisticas(self) -> Dict[str, Any]:
        """Obtém estatísticas do gerador"""
        
        if not self.historico_geracoes:
            return {'total_geracoes': 0}
        
        qualidades = [g['qualidade'] for g in self.historico_geracoes]
        tempos = [g.get('tempo_processamento', 0) for g in self.historico_geracoes]
        
        tipos_gerados = {}
        for geracao in self.historico_geracoes:
            tipo = geracao['tipo']
            tipos_gerados[tipo] = tipos_gerados.get(tipo, 0) + 1
        
        return {
            'total_geracoes': len(self.historico_geracoes),
            'qualidade_media': sum(qualidades) / len(qualidades),
            'tempo_medio': sum(tempos) / len(tempos) if tempos else 0,
            'tipos_gerados': tipos_gerados,
            'minutas_em_cache': len(self.cache_minutas)
        }

# Função de conveniência
async def gerar_minuta_ia(analise: AnaliseProcessualCompleta, 
                         tipo: TipoMinuta = TipoMinuta.DESPACHO_SANEADOR) -> MinutaGerada:
    """
    🤖 FUNÇÃO DE CONVENIÊNCIA
    Gera minuta de forma simples
    """
    gerador = GeradorMinutasInteligente()
    config = ConfiguracaoMinuta(tipo=tipo)
    return await gerador.gerar_minuta_automatica(analise, config)

# Exemplo de uso
if __name__ == "__main__":
    async def testar_gerador_minutas():
        """🧪 TESTE DO GERADOR DE MINUTAS"""
        
        print("🤖 TESTANDO GERADOR DE MINUTAS INTELIGENTE")
        print("=" * 60)
        
        # Criar análise de teste
        from .analise_processual_ia import AnaliseProcessualCompleta, ParteProcessual, PedidoJudicial
        
        analise_teste = AnaliseProcessualCompleta(
            id_analise="teste_001",
            numero_processo="1234567-89.2023.8.26.0001",
            data_analise=datetime.now(),
            classe_processual="Ação de Indenização por Danos Morais",
            assunto_principal="dano moral por negativação indevida",
            valor_causa="R$ 15.000,00",
            tribunal="TJSP",
            comarca="São Paulo",
            partes=[
                ParteProcessual(nome="João da Silva", tipo="autor", documento="123.456.789-00"),
                ParteProcessual(nome="Banco Premium S.A.", tipo="reu", documento="12.345.678/0001-99")
            ],
            pedidos=[
                PedidoJudicial(
                    descricao="condenação ao pagamento de R$ 15.000,00 a título de danos morais",
                    tipo="principal",
                    valor_monetario="R$ 15.000,00"
                )
            ],
            probabilidade_sucesso=0.8
        )
        
        gerador = GeradorMinutasInteligente()
        
        # Teste 1: Despacho Saneador
        print("📝 Gerando despacho saneador...")
        config_despacho = ConfiguracaoMinuta(
            tipo=TipoMinuta.DESPACHO_SANEADOR,
            estilo=EstiloRedacao.FORMAL
        )
        
        minuta_despacho = await gerador.gerar_minuta_automatica(analise_teste, config_despacho)
        
        print(f"✅ Despacho gerado:")
        print(f"   ID: {minuta_despacho.id_minuta}")
        print(f"   Qualidade: {minuta_despacho.qualidade_score:.2f}")
        print(f"   Tempo: {minuta_despacho.tempo_geracao:.2f}s")
        print(f"   Tamanho: {len(minuta_despacho.conteudo)} chars")
        
        # Teste 2: Sentença
        print(f"\n⚖️ Gerando sentença...")
        config_sentenca = ConfiguracaoMinuta(
            tipo=TipoMinuta.SENTENCA,
            estilo=EstiloRedacao.TECNICO,
            incluir_jurisprudencia=True
        )
        
        minuta_sentenca = await gerador.gerar_minuta_automatica(analise_teste, config_sentenca)
        
        print(f"✅ Sentença gerada:")
        print(f"   ID: {minuta_sentenca.id_minuta}")
        print(f"   Qualidade: {minuta_sentenca.qualidade_score:.2f}")
        print(f"   Fundamentação: {len(minuta_sentenca.fundamentacao.dispositivos_legais)} dispositivos")
        print(f"   Jurisprudência: {len(minuta_sentenca.fundamentacao.jurisprudencia)} precedentes")
        
        # Teste 3: Manifestação
        print(f"\n💼 Gerando manifestação...")
        config_manifestacao = ConfiguracaoMinuta(
            tipo=TipoMinuta.MANIFESTACAO,
            estilo=EstiloRedacao.PERSUASIVO
        )
        
        minuta_manifestacao = await gerador.gerar_minuta_automatica(analise_teste, config_manifestacao)
        
        print(f"✅ Manifestação gerada:")
        print(f"   ID: {minuta_manifestacao.id_minuta}")
        print(f"   Qualidade: {minuta_manifestacao.qualidade_score:.2f}")
        
        # Estatísticas
        print(f"\n📊 ESTATÍSTICAS DO GERADOR")
        stats = gerador.obter_estatisticas()
        print(f"Total gerações: {stats['total_geracoes']}")
        print(f"Qualidade média: {stats['qualidade_media']:.2f}")
        print(f"Tempo médio: {stats['tempo_medio']:.2f}s")
        print(f"Tipos gerados: {stats['tipos_gerados']}")
        
        # Exemplo de conteúdo gerado
        print(f"\n📄 EXEMPLO DE CONTEÚDO GERADO:")
        print("-" * 50)
        print(minuta_despacho.conteudo[:500] + "...")
        
        print(f"\n🎉 TESTE CONCLUÍDO!")
        print("🤖 GERADOR DE MINUTAS INTELIGENTE FUNCIONAL!")
    
    # Executar teste
    asyncio.run(testar_gerador_minutas())