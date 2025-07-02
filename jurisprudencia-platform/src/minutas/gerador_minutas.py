"""
🎯 GERADOR DE MINUTAS JURÍDICAS PREMIUM
Sistema que supera o Justino Cível em funcionalidades
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path

@dataclass
class PeticaoAnalise:
    """Estrutura de dados para análise da petição"""
    autor: str
    reu: str
    tipo_acao: str
    pedidos: List[str]
    fundamentos: List[str]
    valor_causa: Optional[str]
    competencia: str
    requisitos_preenchidos: Dict[str, bool]
    provas_necessarias: List[str]
    recomendacoes: List[str]

@dataclass
class MinutaGerada:
    """Estrutura da minuta gerada"""
    tipo_documento: str
    conteudo: str
    fundamentacao_legal: List[str]
    jurisprudencia_aplicavel: List[str]
    observacoes: List[str]
    data_geracao: datetime

class GeradorMinutas:
    """
    🚀 GERADOR DE MINUTAS PREMIUM
    Funcionalidades que superam plataformas concorrentes
    """
    
    def __init__(self):
        self.templates_path = Path("data/templates")
        self.templates_path.mkdir(parents=True, exist_ok=True)
        self._carregar_templates()
        self._carregar_base_legal()
    
    def _carregar_templates(self):
        """Carrega templates de minutas"""
        self.templates = {
            "despacho_saneador": """
DESPACHO SANEADOR

Processo: {processo}
Autor: {autor}
Réu: {reu}

Vistos.

Trata-se de {tipo_acao} ajuizada por {autor} em face de {reu}.

ANÁLISE DOS REQUISITOS:
{analise_requisitos}

QUESTÕES PROCESSUAIS:
{questoes_processuais}

PROVAS NECESSÁRIAS:
{provas_necessarias}

FUNDAMENTAÇÃO LEGAL:
{fundamentacao_legal}

JURISPRUDÊNCIA APLICÁVEL:
{jurisprudencia}

DISPOSITIVO:
Ante o exposto, DEFIRO o processamento da ação e determino:

1) {determinacoes}

2) Intime-se o réu para apresentar contestação no prazo legal.

3) Após, voltem-me os autos conclusos.

{comarca}, {data}.

{magistrado}
Juiz de Direito
            """,
            
            "sentenca_procedencia": """
SENTENÇA

Processo: {processo}
Autor: {autor}  
Réu: {reu}

Vistos e examinados.

{autor} ajuizou {tipo_acao} contra {reu}, alegando {resumo_fatos}.

O réu foi devidamente citado e {situacao_defesa}.

FUNDAMENTAÇÃO:

1. DOS FATOS:
{analise_fatos}

2. DO DIREITO:
{analise_direito}

3. DA JURISPRUDÊNCIA:
{jurisprudencia_citada}

4. DO VALOR DA CONDENAÇÃO:
{calculo_condenacao}

DISPOSITIVO:

Ante o exposto, julgo PROCEDENTE o pedido para:

{dispositivo_final}

{comarca}, {data}.

{magistrado}
Juiz de Direito
            """,
            
            "despacho_diligencias": """
DESPACHO

Processo: {processo}
Requerente: {requerente}

Vistos.

Analisando os autos, verifico a necessidade das seguintes diligências:

DILIGÊNCIAS DETERMINADAS:
{lista_diligencias}

FUNDAMENTAÇÃO:
{justificativa_diligencias}

PRAZO:
{prazo_cumprimento}

Intime-se.

{comarca}, {data}.

{magistrado}
Juiz de Direito
            """
        }
    
    def _carregar_base_legal(self):
        """Base de conhecimento jurídico"""
        self.base_legal = {
            "dano_moral": {
                "artigos": ["CF/88 Art. 5º, V e X", "CC Art. 186, 927", "CDC Art. 6º, VI"],
                "valores_referencia": {
                    "negativacao_indevida": "R$ 3.000,00 a R$ 15.000,00",
                    "protesto_indevido": "R$ 5.000,00 a R$ 20.000,00",
                    "descumprimento_contratual": "R$ 2.000,00 a R$ 10.000,00"
                },
                "jurisprudencia_chave": [
                    "STJ - Súmula 385 (Negativação prévia)",
                    "STJ - REsp 1.740.868 (Quantum indenizatório)",
                    "TJSP - Súmula 67 (Dano moral bancário)"
                ]
            },
            
            "cdc": {
                "artigos": ["CDC Art. 6º", "CDC Art. 14", "CDC Art. 17", "CDC Art. 42"],
                "hipoteses": {
                    "vicio_produto": "CDC Art. 18-25",
                    "fato_produto": "CDC Art. 12-17", 
                    "cobranca_indevida": "CDC Art. 42",
                    "publicidade_enganosa": "CDC Art. 37"
                },
                "prazos": {
                    "reclamacao_vicio": "30 dias (não duráveis) / 90 dias (duráveis)",
                    "prescricao_dano": "5 anos",
                    "decadencia": "90 dias (vícios aparentes)"
                }
            },
            
            "civil": {
                "responsabilidade": ["CC Art. 186", "CC Art. 187", "CC Art. 927"],
                "contratos": ["CC Art. 421-480"],
                "familia": ["CC Art. 1511-1783"],
                "sucessoes": ["CC Art. 1784-2027"]
            }
        }
    
    def analisar_peticao(self, texto_peticao: str) -> PeticaoAnalise:
        """
        🔍 ANÁLISE INTELIGENTE DE PETIÇÕES
        Extrai informações estruturadas automaticamente
        """
        
        # Identificar partes
        autor = self._extrair_autor(texto_peticao)
        reu = self._extrair_reu(texto_peticao)
        
        # Classificar tipo de ação
        tipo_acao = self._classificar_acao(texto_peticao)
        
        # Extrair pedidos
        pedidos = self._extrair_pedidos(texto_peticao)
        
        # Extrair fundamentos
        fundamentos = self._extrair_fundamentos(texto_peticao)
        
        # Extrair valor da causa
        valor_causa = self._extrair_valor_causa(texto_peticao)
        
        # Analisar competência
        competencia = self._analisar_competencia(texto_peticao, valor_causa)
        
        # Verificar requisitos
        requisitos = self._verificar_requisitos(texto_peticao, tipo_acao)
        
        # Sugerir provas
        provas = self._sugerir_provas(tipo_acao, fundamentos)
        
        # Gerar recomendações
        recomendacoes = self._gerar_recomendacoes(tipo_acao, requisitos)
        
        return PeticaoAnalise(
            autor=autor,
            reu=reu,
            tipo_acao=tipo_acao,
            pedidos=pedidos,
            fundamentos=fundamentos,
            valor_causa=valor_causa,
            competencia=competencia,
            requisitos_preenchidos=requisitos,
            provas_necessarias=provas,
            recomendacoes=recomendacoes
        )
    
    def gerar_minuta(self, analise: PeticaoAnalise, tipo_minuta: str = "despacho_saneador") -> MinutaGerada:
        """
        📝 GERAÇÃO AUTOMÁTICA DE MINUTAS
        Cria documentos jurídicos profissionais
        """
        
        if tipo_minuta not in self.templates:
            raise ValueError(f"Tipo de minuta '{tipo_minuta}' não disponível")
        
        template = self.templates[tipo_minuta]
        
        # Preparar dados para template
        dados_template = self._preparar_dados_template(analise, tipo_minuta)
        
        # Gerar conteúdo
        conteudo = template.format(**dados_template)
        
        # Buscar fundamentação legal específica
        fundamentacao = self._buscar_fundamentacao_legal(analise.tipo_acao)
        
        # Buscar jurisprudência aplicável
        jurisprudencia = self._buscar_jurisprudencia_aplicavel(analise.tipo_acao)
        
        # Gerar observações
        observacoes = self._gerar_observacoes(analise)
        
        return MinutaGerada(
            tipo_documento=tipo_minuta,
            conteudo=conteudo,
            fundamentacao_legal=fundamentacao,
            jurisprudencia_aplicavel=jurisprudencia,
            observacoes=observacoes,
            data_geracao=datetime.now()
        )
    
    def _extrair_autor(self, texto: str) -> str:
        """Extrai nome do autor da petição"""
        patterns = [
            r"(?:autor|requerente)[:\s]+([A-ZÁÊÇÕ][a-záêçõ\s]+)",
            r"([A-ZÁÊÇÕ][a-záêçõ\s]+)[,\s]+(?:brasileir|portador)",
            r"vem\s+([A-ZÁÊÇÕ][a-záêçõ\s]+)[,\s]+"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, texto, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return "AUTOR NÃO IDENTIFICADO"
    
    def _extrair_reu(self, texto: str) -> str:
        """Extrai nome do réu"""
        patterns = [
            r"(?:réu|requerido|em face de)[:\s]+([A-ZÁÊÇÕ][a-záêçõ\s\.]+)",
            r"contra\s+([A-ZÁÊÇÕ][a-záêçõ\s\.]+)",
            r"(?:empresa|banco|pessoa jurídica)\s+([A-ZÁÊÇÕ][a-záêçõ\s\.]+)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, texto, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return "RÉU NÃO IDENTIFICADO"
    
    def _classificar_acao(self, texto: str) -> str:
        """Classifica o tipo de ação baseado no conteúdo"""
        classificacoes = {
            "indenização por danos morais": [
                "dano moral", "indenização", "negativação", "protesto",
                "constrangimento", "sofrimento", "abalo psíquico"
            ],
            "ação de cobrança": [
                "cobrança", "débito", "pagamento", "valor devido",
                "inadimplemento", "prestação"
            ],
            "ação consignatória": [
                "consignação", "depósito", "dúvida", "recusa",
                "pagamento consignado"
            ],
            "ação de obrigação de fazer": [
                "obrigação de fazer", "cumprir obrigação", "prestação de serviço",
                "execução específica"
            ],
            "ação revisional": [
                "revisão", "revisional", "juros abusivos", "spread",
                "anatocismo", "capitalização"
            ]
        }
        
        texto_lower = texto.lower()
        pontuacoes = {}
        
        for tipo, palavras_chave in classificacoes.items():
            pontuacao = sum(1 for palavra in palavras_chave if palavra in texto_lower)
            if pontuacao > 0:
                pontuacoes[tipo] = pontuacao
        
        if pontuacoes:
            return max(pontuacoes, key=pontuacoes.get)
        
        return "ação ordinária"
    
    def _extrair_pedidos(self, texto: str) -> List[str]:
        """Extrai pedidos da petição"""
        pedidos = []
        
        # Buscar seção de pedidos
        pedidos_section = re.search(r"(?:dos pedidos|requer|pede)[:\s]+(.*?)(?:termos em que|nestes termos|valor da causa)", 
                                   texto, re.IGNORECASE | re.DOTALL)
        
        if pedidos_section:
            conteudo_pedidos = pedidos_section.group(1)
            
            # Dividir por números ou letras
            itens = re.split(r'\n?\s*[a-z]\)|\n?\s*\d+[.\)]', conteudo_pedidos)
            
            for item in itens:
                item_limpo = item.strip()
                if len(item_limpo) > 10:  # Filtrar itens muito pequenos
                    pedidos.append(item_limpo[:200])  # Limitar tamanho
        
        if not pedidos:
            # Fallback: buscar padrões comuns
            pedidos_comuns = [
                "condenação ao pagamento de indenização por danos morais",
                "condenação nas custas processuais e honorários advocatícios",
                "aplicação dos benefícios da justiça gratuita"
            ]
            
            for pedido in pedidos_comuns:
                if any(palavra in texto.lower() for palavra in pedido.split()):
                    pedidos.append(pedido)
        
        return pedidos[:10]  # Máximo 10 pedidos
    
    def _extrair_fundamentos(self, texto: str) -> List[str]:
        """Extrai fundamentos jurídicos"""
        fundamentos = []
        
        # Buscar citações de leis
        leis = re.findall(r'(?:art\.?\s*\d+|artigo\s+\d+)[^.]*(?:da|do)\s+[^.]+', texto, re.IGNORECASE)
        fundamentos.extend(leis[:5])
        
        # Buscar códigos específicos
        codigos = re.findall(r'(?:CDC|CC|CF|CPC|CLT)[^.]*art[^.]*', texto, re.IGNORECASE)
        fundamentos.extend(codigos[:5])
        
        # Buscar súmulas
        sumulas = re.findall(r'súmula\s+\d+[^.]*', texto, re.IGNORECASE)
        fundamentos.extend(sumulas[:3])
        
        return fundamentos[:10]
    
    def _extrair_valor_causa(self, texto: str) -> Optional[str]:
        """Extrai valor da causa"""
        patterns = [
            r"valor da causa[:\s]+r\$?\s*([\d.,]+)",
            r"r\$\s*([\d.,]+)",
            r"reais\s*\((r\$\s*[\d.,]+)\)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, texto, re.IGNORECASE)
            if match:
                return f"R$ {match.group(1)}"
        
        return None
    
    def _analisar_competencia(self, texto: str, valor_causa: Optional[str]) -> str:
        """Analisa competência do juízo"""
        if valor_causa:
            try:
                valor_num = float(re.sub(r'[^\d,]', '', valor_causa).replace(',', '.'))
                if valor_num <= 20000:  # 20 salários mínimos
                    return "Juizado Especial Cível"
            except:
                pass
        
        # Analisar por tipo de matéria
        if any(palavra in texto.lower() for palavra in ["consumidor", "cdc", "negativação"]):
            return "Vara Cível ou JEC"
        
        if any(palavra in texto.lower() for palavra in ["família", "alimentos", "divórcio"]):
            return "Vara de Família"
        
        if any(palavra in texto.lower() for palavra in ["fazenda", "estado", "município"]):
            return "Vara da Fazenda Pública"
        
        return "Vara Cível"
    
    def _verificar_requisitos(self, texto: str, tipo_acao: str) -> Dict[str, bool]:
        """Verifica requisitos processuais"""
        requisitos = {
            "qualificacao_completa": bool(re.search(r'(?:cpf|rg|endereço)', texto, re.IGNORECASE)),
            "causa_pedir": "em razão" in texto.lower() or "porque" in texto.lower(),
            "pedido_claro": "requer" in texto.lower() or "pede" in texto.lower(),
            "valor_causa": "valor da causa" in texto.lower(),
            "documentos_anexos": "anexo" in texto.lower() or "junta" in texto.lower(),
            "fundamentacao_legal": bool(re.search(r'(?:art|lei|código)', texto, re.IGNORECASE))
        }
        
        # Requisitos específicos por tipo
        if "dano moral" in tipo_acao:
            requisitos["prova_dano"] = any(palavra in texto.lower() for palavra in ["abalo", "constrangimento", "sofrimento"])
        
        return requisitos
    
    def _sugerir_provas(self, tipo_acao: str, fundamentos: List[str]) -> List[str]:
        """Sugere provas necessárias"""
        provas_base = [
            "Documentos pessoais (RG, CPF)",
            "Comprovante de endereço",
            "Prova da relação jurídica"
        ]
        
        if "dano moral" in tipo_acao:
            provas_base.extend([
                "Comprovante de negativação/protesto",
                "Extrato dos órgãos de proteção",
                "Prova do abalo moral (testemunhas, documentos)"
            ])
        
        if "cobrança" in tipo_acao:
            provas_base.extend([
                "Contrato ou documento da dívida",
                "Comprovantes de pagamento",
                "Cálculo atualizado do débito"
            ])
        
        return provas_base
    
    def _gerar_recomendacoes(self, tipo_acao: str, requisitos: Dict[str, bool]) -> List[str]:
        """Gera recomendações processuais"""
        recomendacoes = []
        
        # Verificar requisitos não atendidos
        for req, atendido in requisitos.items():
            if not atendido:
                if req == "qualificacao_completa":
                    recomendacoes.append("⚠️ Completar qualificação das partes")
                elif req == "documentos_anexos":
                    recomendacoes.append("📎 Juntar documentos comprobatórios")
                elif req == "fundamentacao_legal":
                    recomendacoes.append("📚 Incluir fundamentação legal específica")
        
        # Recomendações por tipo de ação
        if "dano moral" in tipo_acao:
            recomendacoes.append("💰 Considerar valor adequado para dano moral")
            recomendacoes.append("📋 Juntar precedentes do TJSP")
        
        return recomendacoes
    
    def _preparar_dados_template(self, analise: PeticaoAnalise, tipo_minuta: str) -> Dict:
        """Prepara dados para preenchimento do template"""
        dados = {
            "processo": "0000000-00.0000.0.00.0000",
            "autor": analise.autor,
            "reu": analise.reu,
            "tipo_acao": analise.tipo_acao,
            "comarca": "São Paulo",
            "data": datetime.now().strftime("%d de %B de %Y"),
            "magistrado": "[NOME DO MAGISTRADO]"
        }
        
        # Dados específicos por tipo
        if tipo_minuta == "despacho_saneador":
            dados.update({
                "analise_requisitos": self._formatar_requisitos(analise.requisitos_preenchidos),
                "questoes_processuais": "Não há questões processuais pendentes.",
                "provas_necessarias": self._formatar_lista(analise.provas_necessarias),
                "fundamentacao_legal": self._formatar_fundamentacao(analise.tipo_acao),
                "jurisprudencia": self._formatar_jurisprudencia(analise.tipo_acao),
                "determinacoes": self._gerar_determinacoes(analise)
            })
        
        return dados
    
    def _formatar_requisitos(self, requisitos: Dict[str, bool]) -> str:
        """Formata análise de requisitos"""
        resultado = []
        for req, atendido in requisitos.items():
            status = "✅ ATENDIDO" if atendido else "⚠️ PENDENTE"
            nome_req = req.replace("_", " ").title()
            resultado.append(f"- {nome_req}: {status}")
        
        return "\n".join(resultado)
    
    def _formatar_lista(self, items: List[str]) -> str:
        """Formata lista de itens"""
        return "\n".join(f"- {item}" for item in items)
    
    def _formatar_fundamentacao(self, tipo_acao: str) -> str:
        """Busca fundamentação legal específica"""
        if "dano moral" in tipo_acao:
            return """
- Constituição Federal, Art. 5º, incisos V e X
- Código Civil, Arts. 186 e 927
- Código de Defesa do Consumidor, Art. 6º, VI
"""
        
        return "Legislação aplicável ao caso concreto."
    
    def _formatar_jurisprudencia(self, tipo_acao: str) -> str:
        """Busca jurisprudência aplicável"""
        if "dano moral" in tipo_acao:
            return """
- STJ, Súmula 385: "Da anotação irregular em cadastro de proteção ao crédito..."
- TJSP, Súmula 67: "O simples descumprimento do dever legal..."
"""
        
        return "Jurisprudência dos Tribunais Superiores aplicável."
    
    def _gerar_determinacoes(self, analise: PeticaoAnalise) -> str:
        """Gera determinações específicas"""
        determinacoes = []
        
        if not analise.requisitos_preenchidos.get("documentos_anexos", True):
            determinacoes.append("Junte os documentos comprobatórios necessários")
        
        if analise.valor_causa:
            determinacoes.append("Comprove o recolhimento das custas processuais")
        
        if not determinacoes:
            determinacoes.append("Cumpra as determinações legais pertinentes")
        
        return "; ".join(determinacoes) + "."
    
    def _buscar_fundamentacao_legal(self, tipo_acao: str) -> List[str]:
        """Busca fundamentação legal específica"""
        if "dano moral" in tipo_acao and "dano_moral" in self.base_legal:
            return self.base_legal["dano_moral"]["artigos"]
        
        return ["Legislação aplicável ao caso"]
    
    def _buscar_jurisprudencia_aplicavel(self, tipo_acao: str) -> List[str]:
        """Busca jurisprudência aplicável"""
        if "dano moral" in tipo_acao and "dano_moral" in self.base_legal:
            return self.base_legal["dano_moral"]["jurisprudencia_chave"]
        
        return ["Precedentes dos Tribunais Superiores"]
    
    def _gerar_observacoes(self, analise: PeticaoAnalise) -> List[str]:
        """Gera observações importantes"""
        observacoes = []
        
        if analise.valor_causa:
            observacoes.append(f"💰 Valor da causa: {analise.valor_causa}")
        
        observacoes.append(f"⚖️ Competência sugerida: {analise.competencia}")
        
        if analise.recomendacoes:
            observacoes.extend([f"📋 {rec}" for rec in analise.recomendacoes[:3]])
        
        return observacoes

    def salvar_minuta(self, minuta: MinutaGerada, caminho: str) -> str:
        """Salva minuta gerada em arquivo"""
        arquivo_path = Path(caminho)
        arquivo_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(arquivo_path, 'w', encoding='utf-8') as f:
            f.write(f"# {minuta.tipo_documento.upper()}\n")
            f.write(f"**Gerado em:** {minuta.data_geracao.strftime('%d/%m/%Y %H:%M')}\n\n")
            f.write(minuta.conteudo)
            f.write("\n\n---\n\n")
            f.write("## FUNDAMENTAÇÃO LEGAL\n")
            for fund in minuta.fundamentacao_legal:
                f.write(f"- {fund}\n")
            f.write("\n## JURISPRUDÊNCIA APLICÁVEL\n")
            for jur in minuta.jurisprudencia_aplicavel:
                f.write(f"- {jur}\n")
            f.write("\n## OBSERVAÇÕES\n")
            for obs in minuta.observacoes:
                f.write(f"- {obs}\n")
        
        return str(arquivo_path)