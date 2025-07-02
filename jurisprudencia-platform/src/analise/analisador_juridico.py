"""
🎯 ANALISADOR JURÍDICO AVANÇADO
Sistema que supera plataformas concorrentes em análise processual
"""

import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
from pathlib import Path

class RiscoProcessual(Enum):
    BAIXO = "baixo"
    MEDIO = "medio" 
    ALTO = "alto"
    CRITICO = "critico"

class TipoRecomendacao(Enum):
    PROCESSUAL = "processual"
    SUBSTANTIVA = "substantiva"
    ESTRATEGICA = "estrategica"
    PROBATORIA = "probatoria"
    CAUTELAR = "cautelar"

@dataclass
class RequisitoLegal:
    """Requisito legal específico"""
    nome: str
    descricao: str
    obrigatorio: bool
    categoria: str  # "processual", "substantivo", "probatorio"
    atendido: bool = False
    evidencias: List[str] = field(default_factory=list)
    observacoes: str = ""

@dataclass
class AnaliseProbabilidade:
    """Análise de probabilidade de sucesso"""
    exito_total: float  # 0-1
    exito_parcial: float  # 0-1
    risco_improcedencia: float  # 0-1
    fatores_positivos: List[str] = field(default_factory=list)
    fatores_negativos: List[str] = field(default_factory=list)
    precedentes_favoraveis: List[str] = field(default_factory=list)
    precedentes_contrarios: List[str] = field(default_factory=list)

@dataclass
class RecomendacaoEstrategica:
    """Recomendação estratégica"""
    tipo: TipoRecomendacao
    prioridade: str  # "alta", "media", "baixa"
    titulo: str
    descricao: str
    prazo_sugerido: Optional[str] = None
    custo_estimado: Optional[str] = None
    impacto_probabilidade: float = 0.0  # -1 a +1
    fundamentacao: List[str] = field(default_factory=list)

@dataclass
class AnaliseEstrategica:
    """Análise estratégica do processo"""
    valor_estimado_condenacao: Optional[str]
    tempo_estimado_processo: str
    custas_estimadas: str
    probabilidade_sucesso: AnaliseProbabilidade
    estrategias_recomendadas: List[str]
    riscos_identificados: List[str]
    oportunidades: List[str]
    
@dataclass
class AnaliseJuridicaCompleta:
    """Análise jurídica completa do caso"""
    id_analise: str
    data_analise: datetime
    tipo_acao: str
    resumo_executivo: str
    
    # Análise de requisitos
    requisitos_legais: List[RequisitoLegal]
    percentual_atendimento: float
    
    # Análise de mérito
    analise_probabilidade: AnaliseProbabilidade
    
    # Recomendações
    recomendacoes: List[RecomendacaoEstrategica]
    
    # Análise estratégica
    analise_estrategica: AnaliseEstrategica
    
    # Risco geral
    nivel_risco: RiscoProcessual
    score_geral: float  # 0-10

class AnalisadorJuridico:
    """
    🚀 ANALISADOR JURÍDICO PREMIUM
    Funcionalidades que superam o Justino Cível
    """
    
    def __init__(self):
        self._carregar_base_conhecimento()
        self._inicializar_criterios_analise()
    
    def _carregar_base_conhecimento(self):
        """Carrega base de conhecimento jurídico"""
        
        self.requisitos_por_acao = {
            "indenização por danos morais": [
                RequisitoLegal("conduta_ilicita", "Comprovação de conduta ilícita", True, "substantivo"),
                RequisitoLegal("dano_moral", "Demonstração do dano moral", True, "substantivo"),
                RequisitoLegal("nexo_causal", "Nexo causal entre conduta e dano", True, "substantivo"),
                RequisitoLegal("documentos_probatorios", "Documentos que comprovem o alegado", True, "probatorio"),
                RequisitoLegal("qualificacao_partes", "Qualificação completa das partes", True, "processual"),
                RequisitoLegal("valor_indenizacao", "Valor da indenização fundamentado", False, "substantivo"),
                RequisitoLegal("precedentes_similares", "Citação de precedentes similares", False, "substantivo")
            ],
            
            "ação de cobrança": [
                RequisitoLegal("titulo_executivo", "Título executivo ou documento da dívida", True, "substantivo"),
                RequisitoLegal("valor_atualizado", "Cálculo atualizado do débito", True, "substantivo"),
                RequisitoLegal("vencimento_obrigacao", "Prova do vencimento da obrigação", True, "substantivo"),
                RequisitoLegal("notificacao_devedor", "Constituição em mora do devedor", False, "processual"),
                RequisitoLegal("juros_correção", "Especificação de juros e correção", False, "substantivo")
            ],
            
            "revisão contrato bancário": [
                RequisitoLegal("contrato_original", "Contrato bancário original", True, "probatorio"),
                RequisitoLegal("planilha_pagamentos", "Planilha de pagamentos realizados", True, "probatorio"),
                RequisitoLegal("calculo_revisional", "Cálculo revisional detalhado", True, "substantivo"),
                RequisitoLegal("clausulas_abusivas", "Identificação de cláusulas abusivas", True, "substantivo"),
                RequisitoLegal("pedido_especifico", "Pedido específico de revisão", True, "processual"),
                RequisitoLegal("pericia_contabil", "Necessidade de perícia contábil", False, "probatorio")
            ],
            
            "ação consignatória": [
                RequisitoLegal("duvida_fundamentada", "Dúvida ou recusa fundamentada", True, "substantivo"),
                RequisitoLegal("deposito_inicial", "Depósito do valor devido", True, "processual"),
                RequisitoLegal("tentativa_pagamento", "Prova da tentativa de pagamento", True, "probatorio"),
                RequisitoLegal("valor_correto", "Valor correto da obrigação", True, "substantivo")
            ]
        }
        
        self.probabilidades_sucesso = {
            "indenização por danos morais": {
                "base": 0.65,
                "fatores_positivos": {
                    "negativacao_indevida": 0.15,
                    "protesto_indevido": 0.20,
                    "erro_banco_dados": 0.10,
                    "precedentes_favoraveis": 0.10,
                    "valor_moderado": 0.05
                },
                "fatores_negativos": {
                    "negativacao_anterior": -0.25,
                    "debito_existente": -0.15,
                    "valor_excessivo": -0.10,
                    "falta_provas": -0.20
                }
            },
            
            "ação de cobrança": {
                "base": 0.70,
                "fatores_positivos": {
                    "titulo_executivo": 0.20,
                    "documento_original": 0.10,
                    "calculo_correto": 0.05
                },
                "fatores_negativos": {
                    "prescricao": -0.30,
                    "documento_irregular": -0.25,
                    "valor_incorreto": -0.15
                }
            },
            
            "revisão contrato bancário": {
                "base": 0.45,
                "fatores_positivos": {
                    "juros_abusivos": 0.20,
                    "capitalizacao_ilegal": 0.15,
                    "spread_excessivo": 0.10,
                    "pericia_favoravel": 0.15
                },
                "fatores_negativos": {
                    "contrato_claro": -0.15,
                    "juros_mercado": -0.10,
                    "quitacao_posterior": -0.20
                }
            }
        }
        
        self.custos_estimados = {
            "ação de cobrança": {"custas": "2% valor", "honorarios": "10-20%", "tempo": "12-18 meses"},
            "indenização por danos morais": {"custas": "R$ 200-500", "honorarios": "20-30%", "tempo": "18-24 meses"},
            "revisão contrato bancário": {"custas": "R$ 300-800", "honorarios": "20-30%", "tempo": "24-36 meses"},
            "ação consignatória": {"custas": "1% valor", "honorarios": "10-15%", "tempo": "6-12 meses"}
        }
        
        self.jurisprudencia_relevante = {
            "indenização por danos morais": [
                "STJ Súmula 385 - Cadastros restritivos",
                "STJ REsp 1.740.868 - Quantum indenizatório",
                "TJSP Súmula 67 - Dano moral bancário"
            ],
            "revisão contrato bancário": [
                "STJ Súmula 596 - Capitalização de juros",
                "STJ REsp 973.827 - Spread bancário",
                "TJSP - Revisional de contratos"
            ]
        }
    
    def _inicializar_criterios_analise(self):
        """Inicializa critérios de análise"""
        
        self.criterios_risco = {
            RiscoProcessual.BAIXO: {"score_min": 7.0, "atendimento_min": 0.8},
            RiscoProcessual.MEDIO: {"score_min": 5.0, "atendimento_min": 0.6},
            RiscoProcessual.ALTO: {"score_min": 3.0, "atendimento_min": 0.4},
            RiscoProcessual.CRITICO: {"score_min": 0.0, "atendimento_min": 0.0}
        }
        
        self.valores_referencia = {
            "dano_moral_negativacao": {"min": 3000, "max": 15000, "medio": 8000},
            "dano_moral_protesto": {"min": 5000, "max": 20000, "medio": 12000},
            "dano_moral_banco_dados": {"min": 2000, "max": 10000, "medio": 6000}
        }
    
    def analisar_caso_completo(self, texto_peticao: str, tipo_acao: str) -> AnaliseJuridicaCompleta:
        """
        🎯 ANÁLISE COMPLETA DO CASO JURÍDICO
        Análise profunda que supera concorrentes
        """
        
        id_analise = self._gerar_id_analise()
        
        # Análise de requisitos
        requisitos = self._analisar_requisitos_legais(texto_peticao, tipo_acao)
        percentual_atendimento = self._calcular_percentual_atendimento(requisitos)
        
        # Análise de probabilidade
        analise_prob = self._analisar_probabilidade_sucesso(texto_peticao, tipo_acao, requisitos)
        
        # Gerar recomendações
        recomendacoes = self._gerar_recomendacoes_estrategicas(texto_peticao, tipo_acao, requisitos, analise_prob)
        
        # Análise estratégica
        analise_estrategica = self._realizar_analise_estrategica(texto_peticao, tipo_acao, analise_prob)
        
        # Calcular risco e score geral
        nivel_risco = self._calcular_nivel_risco(percentual_atendimento, analise_prob.exito_total)
        score_geral = self._calcular_score_geral(percentual_atendimento, analise_prob.exito_total, len(recomendacoes))
        
        # Gerar resumo executivo
        resumo = self._gerar_resumo_executivo(tipo_acao, percentual_atendimento, analise_prob, nivel_risco)
        
        return AnaliseJuridicaCompleta(
            id_analise=id_analise,
            data_analise=datetime.now(),
            tipo_acao=tipo_acao,
            resumo_executivo=resumo,
            requisitos_legais=requisitos,
            percentual_atendimento=percentual_atendimento,
            analise_probabilidade=analise_prob,
            recomendacoes=recomendacoes,
            analise_estrategica=analise_estrategica,
            nivel_risco=nivel_risco,
            score_geral=score_geral
        )
    
    def _gerar_id_analise(self) -> str:
        """Gera ID único para análise"""
        import hashlib
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        hash_obj = hashlib.md5(timestamp.encode())
        return f"ANALISE_{timestamp}_{hash_obj.hexdigest()[:8]}"
    
    def _analisar_requisitos_legais(self, texto: str, tipo_acao: str) -> List[RequisitoLegal]:
        """Analisa requisitos legais específicos"""
        
        requisitos_base = self.requisitos_por_acao.get(tipo_acao, [])
        requisitos_analisados = []
        
        for req in requisitos_base:
            req_copy = RequisitoLegal(
                nome=req.nome,
                descricao=req.descricao,
                obrigatorio=req.obrigatorio,
                categoria=req.categoria
            )
            
            # Verificar se requisito está atendido
            req_copy.atendido, req_copy.evidencias, req_copy.observacoes = self._verificar_requisito(
                texto, req.nome, tipo_acao
            )
            
            requisitos_analisados.append(req_copy)
        
        return requisitos_analisados
    
    def _verificar_requisito(self, texto: str, nome_requisito: str, tipo_acao: str) -> Tuple[bool, List[str], str]:
        """Verifica se um requisito específico está atendido"""
        
        texto_lower = texto.lower()
        evidencias = []
        observacoes = ""
        atendido = False
        
        # Verificações específicas por requisito
        if nome_requisito == "conduta_ilicita":
            padroes = ["negativação", "protesto", "inscrição indevida", "erro", "falha"]
            evidencias = [p for p in padroes if p in texto_lower]
            atendido = len(evidencias) > 0
            observacoes = f"Encontrados {len(evidencias)} indicadores de conduta ilícita"
        
        elif nome_requisito == "dano_moral":
            padroes = ["constrangimento", "abalo", "sofrimento", "humilhação", "vexame", "transtorno"]
            evidencias = [p for p in padroes if p in texto_lower]
            atendido = len(evidencias) > 0
            observacoes = f"Identificados {len(evidencias)} elementos de dano moral"
        
        elif nome_requisito == "nexo_causal":
            padroes = ["em razão", "decorrente", "causado por", "resultado", "consequência"]
            evidencias = [p for p in padroes if p in texto_lower]
            atendido = len(evidencias) > 0
            observacoes = "Nexo causal " + ("estabelecido" if atendido else "não claramente estabelecido")
        
        elif nome_requisito == "documentos_probatorios":
            padroes = ["anexo", "junta", "documento", "comprovante", "certidão"]
            evidencias = [p for p in padroes if p in texto_lower]
            atendido = len(evidencias) > 0
            observacoes = f"Referências a {len(evidencias)} tipos de documentos"
        
        elif nome_requisito == "qualificacao_partes":
            padroes = ["cpf", "cnpj", "rg", "endereço", "brasileiro", "portador"]
            evidencias = [p for p in padroes if p in texto_lower]
            atendido = len(evidencias) >= 2
            observacoes = f"Qualificação {'completa' if atendido else 'incompleta'}"
        
        elif nome_requisito == "valor_indenizacao":
            valores = re.findall(r'r\$\s*[\d.,]+', texto_lower)
            evidencias = valores
            atendido = len(valores) > 0
            observacoes = f"{'Valor especificado' if atendido else 'Valor não especificado'}"
        
        elif nome_requisito == "titulo_executivo":
            padroes = ["contrato", "nota promissória", "duplicata", "título", "instrumento"]
            evidencias = [p for p in padroes if p in texto_lower]
            atendido = len(evidencias) > 0
            observacoes = f"{'Título identificado' if atendido else 'Título não claramente identificado'}"
        
        elif nome_requisito == "valor_atualizado":
            padroes = ["cálculo", "atualização", "correção", "juros", "índice"]
            evidencias = [p for p in padroes if p in texto_lower]
            atendido = len(evidencias) >= 2
            observacoes = f"Cálculo {'detalhado' if atendido else 'simplificado'}"
        
        elif nome_requisito == "deposito_inicial":
            padroes = ["depósito", "consignação", "valor depositado"]
            evidencias = [p for p in padroes if p in texto_lower]
            atendido = "depósito" in texto_lower or "consignação" in texto_lower
            observacoes = f"Depósito {'mencionado' if atendido else 'não mencionado'}"
        
        else:
            # Verificação genérica
            palavras_chave = nome_requisito.replace("_", " ").split()
            encontradas = sum(1 for palavra in palavras_chave if palavra in texto_lower)
            atendido = encontradas >= len(palavras_chave) // 2
            observacoes = f"Verificação genérica: {encontradas}/{len(palavras_chave)} palavras encontradas"
        
        return atendido, evidencias[:5], observacoes
    
    def _calcular_percentual_atendimento(self, requisitos: List[RequisitoLegal]) -> float:
        """Calcula percentual de atendimento dos requisitos"""
        
        if not requisitos:
            return 0.0
        
        # Separar obrigatórios e opcionais
        obrigatorios = [r for r in requisitos if r.obrigatorio]
        opcionais = [r for r in requisitos if not r.obrigatorio]
        
        # Calcular pontuação
        pontos_obrigatorios = sum(2 if r.atendido else 0 for r in obrigatorios)
        pontos_opcionais = sum(1 if r.atendido else 0 for r in opcionais)
        
        total_possivel = len(obrigatorios) * 2 + len(opcionais) * 1
        total_obtido = pontos_obrigatorios + pontos_opcionais
        
        return total_obtido / max(total_possivel, 1)
    
    def _analisar_probabilidade_sucesso(self, texto: str, tipo_acao: str, requisitos: List[RequisitoLegal]) -> AnaliseProbabilidade:
        """Analisa probabilidade de sucesso do caso"""
        
        # Probabilidade base
        config_prob = self.probabilidades_sucesso.get(tipo_acao, {"base": 0.5})
        prob_base = config_prob["base"]
        
        # Analisar fatores positivos e negativos
        fatores_pos = []
        fatores_neg = []
        ajuste_prob = 0.0
        
        texto_lower = texto.lower()
        
        # Verificar fatores específicos
        if "fatores_positivos" in config_prob:
            for fator, valor in config_prob["fatores_positivos"].items():
                if self._verificar_fator(fator, texto_lower):
                    fatores_pos.append(fator.replace("_", " ").title())
                    ajuste_prob += valor
        
        if "fatores_negativos" in config_prob:
            for fator, valor in config_prob["fatores_negativos"].items():
                if self._verificar_fator(fator, texto_lower):
                    fatores_neg.append(fator.replace("_", " ").title())
                    ajuste_prob += valor
        
        # Ajuste baseado nos requisitos
        req_obrigatorios_atendidos = sum(1 for r in requisitos if r.obrigatorio and r.atendido)
        req_obrigatorios_total = sum(1 for r in requisitos if r.obrigatorio)
        
        if req_obrigatorios_total > 0:
            ajuste_requisitos = (req_obrigatorios_atendidos / req_obrigatorios_total - 0.5) * 0.2
            ajuste_prob += ajuste_requisitos
        
        # Calcular probabilidades finais
        prob_total = max(0.05, min(0.95, prob_base + ajuste_prob))
        prob_parcial = min(0.90, prob_total + 0.15)
        prob_improcedencia = 1.0 - prob_total
        
        # Buscar precedentes
        precedentes_fav = self.jurisprudencia_relevante.get(tipo_acao, [])
        precedentes_cont = []  # Seria populado com análise mais avançada
        
        return AnaliseProbabilidade(
            exito_total=prob_total,
            exito_parcial=prob_parcial,
            risco_improcedencia=prob_improcedencia,
            fatores_positivos=fatores_pos,
            fatores_negativos=fatores_neg,
            precedentes_favoraveis=precedentes_fav,
            precedentes_contrarios=precedentes_cont
        )
    
    def _verificar_fator(self, fator: str, texto: str) -> bool:
        """Verifica presença de fator específico no texto"""
        
        mapeamento_fatores = {
            "negativacao_indevida": ["negativação indevida", "inscrição indevida", "cadastro indevido"],
            "protesto_indevido": ["protesto indevido", "protesto irregular"],
            "erro_banco_dados": ["erro", "falha sistema", "problema banco dados"],
            "negativacao_anterior": ["negativação anterior", "registro anterior", "histórico"],
            "debito_existente": ["débito", "dívida", "pendência financeira"],
            "titulo_executivo": ["título executivo", "documento assinado", "confissão dívida"],
            "juros_abusivos": ["juros abusivos", "taxa excessiva", "spread alto"],
            "prescricao": ["prescrição", "prescrito", "prazo decorrido"],
            "documento_original": ["original", "via original", "documento autêntico"]
        }
        
        palavras_chave = mapeamento_fatores.get(fator, [fator.replace("_", " ")])
        return any(palavra in texto for palavra in palavras_chave)
    
    def _gerar_recomendacoes_estrategicas(self, texto: str, tipo_acao: str, 
                                        requisitos: List[RequisitoLegal], 
                                        prob: AnaliseProbabilidade) -> List[RecomendacaoEstrategica]:
        """Gera recomendações estratégicas personalizadas"""
        
        recomendacoes = []
        
        # Recomendações baseadas em requisitos não atendidos
        for req in requisitos:
            if req.obrigatorio and not req.atendido:
                rec = self._criar_recomendacao_requisito(req, tipo_acao)
                if rec:
                    recomendacoes.append(rec)
        
        # Recomendações específicas por tipo de ação
        recomendacoes.extend(self._gerar_recomendacoes_especificas(tipo_acao, texto, prob))
        
        # Recomendações probatórias
        recomendacoes.extend(self._gerar_recomendacoes_probatorias(texto, tipo_acao, prob))
        
        # Recomendações estratégicas gerais
        recomendacoes.extend(self._gerar_recomendacoes_gerais(prob, tipo_acao))
        
        return sorted(recomendacoes, key=lambda x: {"alta": 3, "media": 2, "baixa": 1}[x.prioridade], reverse=True)[:10]
    
    def _criar_recomendacao_requisito(self, requisito: RequisitoLegal, tipo_acao: str) -> Optional[RecomendacaoEstrategica]:
        """Cria recomendação baseada em requisito não atendido"""
        
        mapeamento_recomendacoes = {
            "qualificacao_partes": RecomendacaoEstrategica(
                tipo=TipoRecomendacao.PROCESSUAL,
                prioridade="alta",
                titulo="Completar Qualificação das Partes",
                descricao="Incluir CPF/CNPJ, RG, endereço completo e demais dados de qualificação conforme CPC Art. 319, II",
                prazo_sugerido="Antes da protocolização",
                fundamentacao=["CPC Art. 319, II", "Requisito essencial da petição inicial"]
            ),
            
            "documentos_probatorios": RecomendacaoEstrategica(
                tipo=TipoRecomendacao.PROBATORIA,
                prioridade="alta",
                titulo="Juntar Documentos Comprobatórios",
                descricao="Anexar todos os documentos que fundamentam os fatos alegados (CPC Art. 320)",
                prazo_sugerido="Com a petição inicial",
                fundamentacao=["CPC Art. 320", "CPC Art. 396"]
            ),
            
            "valor_indenizacao": RecomendacaoEstrategica(
                tipo=TipoRecomendacao.SUBSTANTIVA,
                prioridade="media",
                titulo="Fundamentar Valor da Indenização",
                descricao="Especificar e fundamentar o valor pleiteado com base em precedentes e critérios objetivos",
                fundamentacao=["Precedentes TJSP", "Princípio da proporcionalidade"]
            ),
            
            "titulo_executivo": RecomendacaoEstrategica(
                tipo=TipoRecomendacao.PROBATORIA,
                prioridade="alta",
                titulo="Juntar Título Executivo ou Documento da Dívida",
                descricao="Apresentar documento que comprove a existência e exigibilidade da obrigação",
                prazo_sugerido="Com a petição inicial",
                fundamentacao=["CPC Art. 320", "Prova da obrigação"]
            )
        }
        
        return mapeamento_recomendacoes.get(requisito.nome)
    
    def _gerar_recomendacoes_especificas(self, tipo_acao: str, texto: str, prob: AnaliseProbabilidade) -> List[RecomendacaoEstrategica]:
        """Gera recomendações específicas por tipo de ação"""
        
        recomendacoes = []
        
        if tipo_acao == "indenização por danos morais":
            # Valor da indenização
            if "valor" not in texto.lower():
                recomendacoes.append(RecomendacaoEstrategica(
                    tipo=TipoRecomendacao.SUBSTANTIVA,
                    prioridade="alta",
                    titulo="Definir Valor da Indenização por Dano Moral",
                    descricao="Estabelecer valor entre R$ 3.000,00 e R$ 15.000,00 para casos de negativação indevida, baseado na jurisprudência do TJSP",
                    impacto_probabilidade=0.1,
                    fundamentacao=["TJSP Súmula 67", "Precedentes recentes"]
                ))
            
            # Súmula 385 do STJ
            if "súmula 385" not in texto.lower() and any("anterior" in fator.lower() for fator in prob.fatores_negativos):
                recomendacoes.append(RecomendacaoEstrategica(
                    tipo=TipoRecomendacao.ESTRATEGICA,
                    prioridade="alta",
                    titulo="Analisar Aplicação da Súmula 385 STJ",
                    descricao="Verificar se há anotação restritiva anterior que possa impedir a indenização por dano moral",
                    impacto_probabilidade=-0.2,
                    fundamentacao=["STJ Súmula 385"]
                ))
        
        elif tipo_acao == "revisão contrato bancário":
            recomendacoes.append(RecomendacaoEstrategica(
                tipo=TipoRecomendacao.PROBATORIA,
                prioridade="alta",
                titulo="Solicitar Perícia Contábil",
                descricao="Requerer perícia para cálculo dos valores cobrados indevidamente e elaboração de planilha revisional",
                custo_estimado="R$ 2.000,00 - R$ 5.000,00",
                impacto_probabilidade=0.15,
                fundamentacao=["CPC Art. 465", "Necessidade técnica"]
            ))
        
        elif tipo_acao == "ação de cobrança":
            if prob.risco_improcedencia > 0.3:
                recomendacoes.append(RecomendacaoEstrategica(
                    tipo=TipoRecomendacao.ESTRATEGICA,
                    prioridade="media",
                    titulo="Considerar Acordo Extrajudicial",
                    descricao="Dado o risco de improcedência, avaliar possibilidade de acordo antes do ajuizamento",
                    impacto_probabilidade=0.0,
                    fundamentacao=["Economia processual", "Redução de custos"]
                ))
        
        return recomendacoes
    
    def _gerar_recomendacoes_probatorias(self, texto: str, tipo_acao: str, prob: AnaliseProbabilidade) -> List[RecomendacaoEstrategica]:
        """Gera recomendações probatórias"""
        
        recomendacoes = []
        
        # Testemunhas
        if "testemunha" not in texto.lower() and tipo_acao in ["indenização por danos morais"]:
            recomendacoes.append(RecomendacaoEstrategica(
                tipo=TipoRecomendacao.PROBATORIA,
                prioridade="media",
                titulo="Arrolar Testemunhas",
                descricao="Indicar testemunhas que possam comprovar o constrangimento e abalo moral sofrido",
                prazo_sugerido="15 dias após citação do réu",
                fundamentacao=["CPC Art. 357", "Prova testemunhal"]
            ))
        
        # Documentos específicos
        if tipo_acao == "indenização por danos morais":
            if "extrato" not in texto.lower():
                recomendacoes.append(RecomendacaoEstrategica(
                    tipo=TipoRecomendacao.PROBATORIA,
                    prioridade="alta",
                    titulo="Juntar Extratos dos Órgãos de Proteção",
                    descricao="Apresentar extratos atualizados do Serasa, SPC e SCPC comprovando a negativação",
                    fundamentacao=["Prova documental essencial"]
                ))
        
        return recomendacoes
    
    def _gerar_recomendacoes_gerais(self, prob: AnaliseProbabilidade, tipo_acao: str) -> List[RecomendacaoEstrategica]:
        """Gera recomendações estratégicas gerais"""
        
        recomendacoes = []
        
        # Tutela antecipada
        if tipo_acao in ["ação consignatória", "revisão contrato bancário"]:
            recomendacoes.append(RecomendacaoEstrategica(
                tipo=TipoRecomendacao.CAUTELAR,
                prioridade="media",
                titulo="Avaliar Pedido de Tutela Antecipada",
                descricao="Considerar pedido de tutela para suspender cobrança ou negativação durante o processo",
                fundamentacao=["CPC Art. 300", "Urgência e probabilidade do direito"]
            ))
        
        # Justiça gratuita
        if "justiça gratuita" not in tipo_acao.lower():
            recomendacoes.append(RecomendacaoEstrategica(
                tipo=TipoRecomendacao.PROCESSUAL,
                prioridade="baixa",
                titulo="Requerer Benefícios da Justiça Gratuita",
                descricao="Solicitar isenção de custas processuais se presentes os requisitos legais",
                fundamentacao=["Lei 1.060/50", "CPC Art. 98"]
            ))
        
        # Mediação/Conciliação
        if prob.risco_improcedencia > 0.4:
            recomendacoes.append(RecomendacaoEstrategica(
                tipo=TipoRecomendacao.ESTRATEGICA,
                prioridade="media",
                titulo="Priorizar Acordo em Audiência",
                descricao="Dado o risco processual, focar esforços na obtenção de acordo favorável",
                impacto_probabilidade=0.0,
                fundamentacao=["Redução de riscos", "Economia de tempo e custos"]
            ))
        
        return recomendacoes
    
    def _realizar_analise_estrategica(self, texto: str, tipo_acao: str, prob: AnaliseProbabilidade) -> AnaliseEstrategica:
        """Realiza análise estratégica completa"""
        
        # Estimar valor de condenação
        valor_estimado = self._estimar_valor_condenacao(texto, tipo_acao, prob)
        
        # Estimar tempo de processo
        tempo_estimado = self.custos_estimados.get(tipo_acao, {}).get("tempo", "18-24 meses")
        
        # Estimar custas
        custas_estimadas = self.custos_estimados.get(tipo_acao, {}).get("custas", "Variável")
        
        # Estratégias recomendadas
        estrategias = self._gerar_estrategias_processo(tipo_acao, prob)
        
        # Riscos identificados
        riscos = self._identificar_riscos_processo(tipo_acao, prob)
        
        # Oportunidades
        oportunidades = self._identificar_oportunidades(tipo_acao, prob)
        
        return AnaliseEstrategica(
            valor_estimado_condenacao=valor_estimado,
            tempo_estimado_processo=tempo_estimado,
            custas_estimadas=custas_estimadas,
            probabilidade_sucesso=prob,
            estrategias_recomendadas=estrategias,
            riscos_identificados=riscos,
            oportunidades=oportunidades
        )
    
    def _estimar_valor_condenacao(self, texto: str, tipo_acao: str, prob: AnaliseProbabilidade) -> Optional[str]:
        """Estima valor provável de condenação"""
        
        if tipo_acao == "indenização por danos morais":
            # Buscar se há valor específico no texto
            valores = re.findall(r'r\$\s*([\d.,]+)', texto.lower())
            
            if valores:
                try:
                    valor_pedido = float(valores[0].replace('.', '').replace(',', '.'))
                    # Aplicar probabilidade de sucesso
                    valor_estimado = valor_pedido * prob.exito_total
                    return f"R$ {valor_estimado:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                except:
                    pass
            
            # Valor baseado em referências
            if "negativação" in texto.lower():
                base = self.valores_referencia["dano_moral_negativacao"]["medio"]
                valor_estimado = base * prob.exito_total
                return f"R$ {valor_estimado:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        
        return None
    
    def _gerar_estrategias_processo(self, tipo_acao: str, prob: AnaliseProbabilidade) -> List[str]:
        """Gera estratégias recomendadas para o processo"""
        
        estrategias = []
        
        if prob.exito_total > 0.7:
            estrategias.append("🎯 Estratégia ofensiva - alta probabilidade de sucesso")
            estrategias.append("💪 Ser firme nas sustentações e pedidos")
        elif prob.exito_total > 0.5:
            estrategias.append("⚖️ Estratégia equilibrada - focar em pontos fortes")
            estrategias.append("🤝 Estar aberto a acordos vantajosos")
        else:
            estrategias.append("🛡️ Estratégia defensiva - minimizar riscos")
            estrategias.append("🤝 Priorizar acordo para reduzir perdas")
        
        # Estratégias específicas
        if tipo_acao == "indenização por danos morais":
            estrategias.append("📊 Fundamentar valor com base em precedentes similares")
            estrategias.append("🔍 Comprovar efetivamente o dano moral sofrido")
        
        elif tipo_acao == "revisão contrato bancário":
            estrategias.append("🧮 Investir em perícia contábil de qualidade")
            estrategias.append("📋 Demonstrar abusividade das cláusulas contestadas")
        
        return estrategias[:5]
    
    def _identificar_riscos_processo(self, tipo_acao: str, prob: AnaliseProbabilidade) -> List[str]:
        """Identifica riscos do processo"""
        
        riscos = []
        
        # Riscos gerais
        if prob.risco_improcedencia > 0.3:
            riscos.append(f"⚠️ Risco de improcedência: {prob.risco_improcedencia:.1%}")
        
        if prob.fatores_negativos:
            riscos.append(f"❌ Fatores negativos identificados: {', '.join(prob.fatores_negativos)}")
        
        # Riscos específicos
        if tipo_acao == "indenização por danos morais":
            if any("anterior" in fator.lower() for fator in prob.fatores_negativos):
                riscos.append("📋 Súmula 385 STJ pode impedir indenização")
            
            riscos.append("💰 Risco de redução do valor pleiteado pelo juízo")
        
        elif tipo_acao == "ação de cobrança":
            riscos.append("⏰ Risco de alegação de prescrição pela defesa")
            riscos.append("📄 Questionamento da validade dos documentos")
        
        elif tipo_acao == "revisão contrato bancário":
            riscos.append("🧮 Dependência de perícia contábil favorável")
            riscos.append("⚖️ Jurisprudência consolidada pró-bancos em alguns aspectos")
        
        return riscos[:6]
    
    def _identificar_oportunidades(self, tipo_acao: str, prob: AnaliseProbabilidade) -> List[str]:
        """Identifica oportunidades no caso"""
        
        oportunidades = []
        
        # Oportunidades gerais
        if prob.fatores_positivos:
            oportunidades.append(f"✅ Fatores favoráveis: {', '.join(prob.fatores_positivos)}")
        
        if prob.precedentes_favoraveis:
            oportunidades.append("📚 Precedentes favoráveis disponíveis")
        
        # Oportunidades específicas
        if tipo_acao == "indenização por danos morais":
            oportunidades.append("🎯 Tendência de valorização do dano moral na jurisprudência")
            oportunidades.append("⚡ Processo relativamente rápido em JEC")
        
        elif tipo_acao == "revisão contrato bancário":
            oportunidades.append("📈 Crescente proteção ao consumidor pelo Judiciário")
            oportunidades.append("🔍 Possibilidade de descobrir outras irregularidades na perícia")
        
        elif tipo_acao == "ação de cobrança":
            if prob.exito_total > 0.6:
                oportunidades.append("💰 Alta probabilidade de recuperação do crédito")
                oportunidades.append("⚡ Possibilidade de execução imediata após sentença")
        
        return oportunidades[:5]
    
    def _calcular_nivel_risco(self, percentual_atendimento: float, prob_sucesso: float) -> RiscoProcessual:
        """Calcula nível de risco geral do processo"""
        
        score_combinado = (percentual_atendimento + prob_sucesso) / 2
        
        if score_combinado >= 0.8:
            return RiscoProcessual.BAIXO
        elif score_combinado >= 0.6:
            return RiscoProcessual.MEDIO
        elif score_combinado >= 0.4:
            return RiscoProcessual.ALTO
        else:
            return RiscoProcessual.CRITICO
    
    def _calcular_score_geral(self, percentual_atendimento: float, prob_sucesso: float, num_recomendacoes: int) -> float:
        """Calcula score geral do caso (0-10)"""
        
        # Score base (60% peso)
        score_base = (percentual_atendimento * 0.4 + prob_sucesso * 0.6) * 6
        
        # Bonus por baixo número de recomendações (caso bem estruturado)
        bonus_estrutura = max(0, (10 - num_recomendacoes) * 0.2)
        
        # Score final
        score_final = min(10.0, score_base + bonus_estrutura)
        
        return round(score_final, 1)
    
    def _gerar_resumo_executivo(self, tipo_acao: str, percentual_atendimento: float, 
                              prob: AnaliseProbabilidade, nivel_risco: RiscoProcessual) -> str:
        """Gera resumo executivo da análise"""
        
        # Determinar tom do resumo
        if prob.exito_total >= 0.7:
            perspectiva = "FAVORÁVEL"
            emoji = "✅"
        elif prob.exito_total >= 0.5:
            perspectiva = "MODERADA"
            emoji = "⚖️"
        else:
            perspectiva = "DESFAVORÁVEL"
            emoji = "⚠️"
        
        resumo = f"""
{emoji} **PERSPECTIVA {perspectiva}** para {tipo_acao}

**Probabilidade de Êxito:** {prob.exito_total:.1%}
**Requisitos Atendidos:** {percentual_atendimento:.1%}
**Nível de Risco:** {nivel_risco.value.upper()}

**Principais Fatores:**
"""
        
        if prob.fatores_positivos:
            resumo += f"✅ Favoráveis: {', '.join(prob.fatores_positivos[:2])}\n"
        
        if prob.fatores_negativos:
            resumo += f"❌ Desfavoráveis: {', '.join(prob.fatores_negativos[:2])}\n"
        
        # Recomendação principal
        if prob.exito_total >= 0.6:
            resumo += "\n**RECOMENDAÇÃO:** Prosseguir com o processo, observando as sugestões técnicas."
        elif prob.exito_total >= 0.4:
            resumo += "\n**RECOMENDAÇÃO:** Avaliar cuidadosamente custos x benefícios. Considerar acordo."
        else:
            resumo += "\n**RECOMENDAÇÃO:** Alto risco. Reavaliar estratégia ou buscar acordo."
        
        return resumo.strip()
    
    def exportar_relatorio_completo(self, analise: AnaliseJuridicaCompleta, caminho: str) -> str:
        """Exporta relatório completo da análise"""
        
        relatorio = f"""
# ANÁLISE JURÍDICA COMPLETA
**ID da Análise:** {analise.id_analise}
**Data:** {analise.data_analise.strftime('%d/%m/%Y %H:%M')}
**Tipo de Ação:** {analise.tipo_acao}

## RESUMO EXECUTIVO
{analise.resumo_executivo}

**Score Geral:** {analise.score_geral}/10
**Nível de Risco:** {analise.nivel_risco.value.upper()}

## ANÁLISE DE REQUISITOS LEGAIS
**Percentual de Atendimento:** {analise.percentual_atendimento:.1%}

### Requisitos Obrigatórios
"""
        
        for req in analise.requisitos_legais:
            if req.obrigatorio:
                status = "✅ ATENDIDO" if req.atendido else "❌ PENDENTE"
                relatorio += f"- **{req.nome.replace('_', ' ').title()}:** {status}\n"
                if req.observacoes:
                    relatorio += f"  - {req.observacoes}\n"
        
        relatorio += "\n### Requisitos Opcionais\n"
        
        for req in analise.requisitos_legais:
            if not req.obrigatorio:
                status = "✅ ATENDIDO" if req.atendido else "⭕ OPCIONAL"
                relatorio += f"- **{req.nome.replace('_', ' ').title()}:** {status}\n"
        
        relatorio += f"""
## ANÁLISE DE PROBABILIDADE
**Êxito Total:** {analise.analise_probabilidade.exito_total:.1%}
**Êxito Parcial:** {analise.analise_probabilidade.exito_parcial:.1%}
**Risco de Improcedência:** {analise.analise_probabilidade.risco_improcedencia:.1%}

### Fatores Favoráveis
"""
        
        for fator in analise.analise_probabilidade.fatores_positivos:
            relatorio += f"- ✅ {fator}\n"
        
        relatorio += "\n### Fatores Desfavoráveis\n"
        
        for fator in analise.analise_probabilidade.fatores_negativos:
            relatorio += f"- ❌ {fator}\n"
        
        relatorio += f"""
## ANÁLISE ESTRATÉGICA
**Valor Estimado:** {analise.analise_estrategica.valor_estimado_condenacao or 'Não aplicável'}
**Tempo Estimado:** {analise.analise_estrategica.tempo_estimado_processo}
**Custas Estimadas:** {analise.analise_estrategica.custas_estimadas}

### Estratégias Recomendadas
"""
        
        for estrategia in analise.analise_estrategica.estrategias_recomendadas:
            relatorio += f"- {estrategia}\n"
        
        relatorio += "\n### Riscos Identificados\n"
        
        for risco in analise.analise_estrategica.riscos_identificados:
            relatorio += f"- {risco}\n"
        
        relatorio += "\n### Oportunidades\n"
        
        for oportunidade in analise.analise_estrategica.oportunidades:
            relatorio += f"- {oportunidade}\n"
        
        relatorio += f"""
## RECOMENDAÇÕES ESTRATÉGICAS ({len(analise.recomendacoes)})
"""
        
        for i, rec in enumerate(analise.recomendacoes, 1):
            prioridade_emoji = {"alta": "🔴", "media": "🟡", "baixa": "🟢"}[rec.prioridade]
            
            relatorio += f"""
### {i}. {rec.titulo} {prioridade_emoji}
**Prioridade:** {rec.prioridade.upper()}
**Tipo:** {rec.tipo.value.title()}
**Descrição:** {rec.descricao}
"""
            
            if rec.prazo_sugerido:
                relatorio += f"**Prazo:** {rec.prazo_sugerido}\n"
            
            if rec.custo_estimado:
                relatorio += f"**Custo:** {rec.custo_estimado}\n"
            
            if rec.fundamentacao:
                relatorio += "**Fundamentação:**\n"
                for fund in rec.fundamentacao:
                    relatorio += f"- {fund}\n"
        
        relatorio += f"""
## PRECEDENTES APLICÁVEIS
"""
        
        for precedente in analise.analise_probabilidade.precedentes_favoraveis:
            relatorio += f"- ✅ {precedente}\n"
        
        relatorio += """
---
*Relatório gerado pelo Sistema de Análise Jurídica Avançada*
*Esta análise é baseada em algoritmos e deve ser complementada pela análise humana especializada*
"""
        
        # Salvar arquivo
        caminho_arquivo = Path(caminho)
        caminho_arquivo.parent.mkdir(parents=True, exist_ok=True)
        
        with open(caminho_arquivo, 'w', encoding='utf-8') as f:
            f.write(relatorio)
        
        return str(caminho_arquivo)