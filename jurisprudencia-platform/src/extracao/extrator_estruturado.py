"""
🎯 EXTRAÇÃO ESTRUTURADA DE DOCUMENTOS JURÍDICOS
Sistema que supera plataformas concorrentes em precisão
"""

import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import json
from pathlib import Path
import logging

@dataclass
class EntidadeJuridica:
    """Informações de uma entidade jurídica (pessoa física/jurídica)"""
    nome: str
    tipo: str  # "pessoa_fisica", "pessoa_juridica", "orgao_publico"
    cpf_cnpj: Optional[str] = None
    endereco: Optional[str] = None
    telefone: Optional[str] = None
    email: Optional[str] = None
    representante_legal: Optional[str] = None
    qualificacao_completa: bool = False

@dataclass
class PedidoJuridico:
    """Estrutura de um pedido jurídico"""
    tipo: str  # "principal", "subsidiario", "cautelar"
    categoria: str  # "condenatorio", "declaratorio", "constitutivo"
    descricao: str
    valor_monetario: Optional[str] = None
    prazo: Optional[str] = None
    fundamentacao: List[str] = None

@dataclass
class FundamentoLegal:
    """Fundamentação legal citada"""
    tipo: str  # "lei", "decreto", "sumula", "jurisprudencia"
    referencia: str  # "CC Art. 186", "STJ Súmula 385"
    contexto: str  # Trecho onde foi citado
    categoria: str  # "civil", "consumidor", "constitucional"

@dataclass
class DocumentoEstruturado:
    """Documento jurídico completamente estruturado"""
    id_documento: str
    tipo_documento: str
    data_analise: datetime
    
    # Partes processuais
    autor: EntidadeJuridica
    reu: EntidadeJuridica
    terceiros: List[EntidadeJuridica]
    
    # Estrutura processual
    tipo_acao: str
    competencia_sugerida: str
    valor_causa: Optional[str]
    classe_processual: str
    
    # Conteúdo jurídico
    pedidos: List[PedidoJuridico]
    fundamentos_legais: List[FundamentoLegal]
    fatos_relevantes: List[str]
    
    # Análise de qualidade
    completude_score: float  # 0-1
    problemas_identificados: List[str]
    sugestoes_melhoria: List[str]
    
    # Metadados
    estatisticas: Dict[str, Any]

class ExtratorEstruturado:
    """
    🚀 EXTRATOR ESTRUTURADO PREMIUM
    Análise profunda de documentos jurídicos
    """
    
    def __init__(self):
        self.setup_logging()
        self._carregar_bases_conhecimento()
        self._inicializar_padroes()
    
    def setup_logging(self):
        """Configura sistema de logs"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def _carregar_bases_conhecimento(self):
        """Carrega bases de conhecimento jurídico"""
        
        self.tipos_acao = {
            # Direito Civil
            "indenização por danos morais": {
                "palavras_chave": ["dano moral", "indenização", "constrangimento", "abalo", "sofrimento"],
                "competencia": "civel",
                "valor_medio": "R$ 5.000,00",
                "prazo_prescricional": "3 anos (CC Art. 206)"
            },
            "ação de cobrança": {
                "palavras_chave": ["cobrança", "débito", "pagamento", "inadimplemento"],
                "competencia": "civel",
                "valor_medio": "variável",
                "prazo_prescricional": "5 anos (CC Art. 206)"
            },
            "ação consignatória": {
                "palavras_chave": ["consignação", "depósito", "recusa", "dúvida"],
                "competencia": "civel",
                "valor_medio": "valor do débito",
                "prazo_prescricional": "mesmo da obrigação principal"
            },
            
            # Direito do Consumidor
            "ação de reparação de danos - CDC": {
                "palavras_chave": ["consumidor", "fornecedor", "produto", "serviço", "vício"],
                "competencia": "consumidor",
                "valor_medio": "R$ 10.000,00",
                "prazo_prescricional": "5 anos (CDC Art. 27)"
            },
            
            # Direito Bancário
            "revisão contrato bancário": {
                "palavras_chave": ["revisão", "juros", "spread", "capitalização", "anatocismo"],
                "competencia": "civel",
                "valor_medio": "variável",
                "prazo_prescricional": "10 anos (CC Art. 205)"
            }
        }
        
        self.bases_legais = {
            "constitucional": {
                "CF": ["art. 5º", "art. 37", "art. 170"],
                "principios": ["legalidade", "moralidade", "dignidade humana"]
            },
            "civil": {
                "CC": ["art. 186", "art. 187", "art. 927", "art. 944"],
                "responsabilidade": ["culpa", "dolo", "nexo causal"]
            },
            "consumidor": {
                "CDC": ["art. 6º", "art. 12", "art. 14", "art. 17", "art. 42"],
                "principios": ["vulnerabilidade", "hipossuficiência", "boa-fé"]
            },
            "processual": {
                "CPC": ["art. 319", "art. 320", "art. 330"],
                "requisitos": ["causa de pedir", "pedido", "partes"]
            }
        }
        
        self.orgaos_conhecidos = {
            "bancos": [
                "Banco do Brasil", "Caixa Econômica", "Itaú", "Bradesco", 
                "Santander", "BTG Pactual", "Inter", "Nubank"
            ],
            "orgaos_publicos": [
                "União", "Estado", "Município", "INSS", "Receita Federal",
                "FGTS", "Detran", "Procon"
            ],
            "empresas_telefonia": [
                "Vivo", "Claro", "TIM", "Oi", "Nextel"
            ],
            "energia": [
                "Enel", "Light", "Cemig", "Copel", "Celpe"
            ]
        }
    
    def _inicializar_padroes(self):
        """Inicializa padrões regex para extração"""
        
        # Padrões para identificação de pessoas
        self.padroes_pessoa = {
            "nome_completo": r'([A-ZÁÊÍÓÚÇÕ][a-záêíóúçõ]+(?:\s+[A-ZÁÊÍÓÚÇÕ][a-záêíóúçõ]+)+)',
            "cpf": r'(?:CPF[:\s]*)?(\d{3}\.?\d{3}\.?\d{3}-?\d{2})',
            "cnpj": r'(?:CNPJ[:\s]*)?(\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2})',
            "rg": r'(?:RG[:\s]*)?(\d{1,2}\.?\d{3}\.?\d{3}-?[\dX])',
            "endereco": r'(?:endereço|reside|domiciliado)[:\s]+([^,\n]+(?:,\s*[^,\n]+)*)',
            "telefone": r'(?:tel|telefone|celular)[:\s]*\(?(\d{2})\)?\s*\d{4,5}-?\d{4}',
            "email": r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
        }
        
        # Padrões para estruturas processuais
        self.padroes_processual = {
            "numero_processo": r'(?:processo|autos)[:\s]*(\d{7}-\d{2}\.\d{4}\.\d{1}\.\d{2}\.\d{4})',
            "valor_causa": r'(?:valor da causa|atribui[^:]*valor)[:\s]*(?:de\s*)?R?\$?\s*([\d.,]+)',
            "valor_monetario": r'R\$\s*([\d.,]+)',
            "data": r'(\d{1,2}[/.-]\d{1,2}[/.-]\d{4})',
            "prazo": r'(?:prazo de|no prazo de)\s*(\d+\s*dias?|\d+\s*anos?|\d+\s*meses?)'
        }
        
        # Padrões para fundamentação legal
        self.padroes_legal = {
            "artigo": r'(?:art\.?\s*|artigo\s*)(\d+(?:[º°]|[-ºª])?)(?:[,\s]*(?:§|par[áa]grafo)\s*(\d+[º°]?))?(?:[^A-Z\n]*(?:da|do)\s+([^.;,\n]+))?',
            "lei": r'(?:Lei[^\d]*)?(\d+(?:\.\d+)*)[/.-](\d{4})',
            "decreto": r'(?:Decreto[^\d]*)?(\d+(?:\.\d+)*)[/.-](\d{4})',
            "sumula": r'(?:Súmula[^\d]*)?(\d+)(?:[^A-Z\n]*(?:do|da)\s+([A-Z]{2,}))?',
            "codigo": r'(C[ÓO]DIGO\s+[A-Z\s]+|CDC|CC|CF|CPC|CLT|CP)',
            "jurisprudencia": r'(STF|STJ|TST|TJSP|TRF|TRT)[^;.\n]*(?:RE[sp]*|AgRg|HC|MS)[^;.\n]*(\d+(?:\.\d+)*)'
        }
        
        # Padrões para pedidos
        self.padroes_pedidos = {
            "condenacao": r'(?:condena[rç][ãa]o|condenar)[^.]*?(?:ao pagamento|em)[^.]*',
            "declaracao": r'(?:declarar|declare-se)[^.]*',
            "constituicao": r'(?:constituir|constitua-se)[^.]*',
            "obrigacao_fazer": r'(?:obriga[rç][ãa]o de fazer|cumprir|executar)[^.]*',
            "tutela": r'(?:tutela|liminar|antecipa[rç][ãa]o)[^.]*'
        }
    
    def extrair_documento_completo(self, texto: str, tipo_documento: str = "peticao_inicial") -> DocumentoEstruturado:
        """
        🎯 EXTRAÇÃO COMPLETA DO DOCUMENTO
        Análise estruturada profunda
        """
        
        id_doc = self._gerar_id_documento(texto)
        self.logger.info(f"Iniciando extração do documento {id_doc}")
        
        # Extrair entidades
        autor = self._extrair_autor(texto)
        reu = self._extrair_reu(texto)
        terceiros = self._extrair_terceiros(texto)
        
        # Análise processual
        tipo_acao = self._classificar_acao_avancada(texto)
        competencia = self._analisar_competencia_detalhada(texto, tipo_acao)
        valor_causa = self._extrair_valor_causa_detalhado(texto)
        classe_processual = self._determinar_classe_processual(tipo_acao)
        
        # Extração de conteúdo jurídico
        pedidos = self._extrair_pedidos_estruturados(texto)
        fundamentos = self._extrair_fundamentos_estruturados(texto)
        fatos = self._extrair_fatos_relevantes(texto)
        
        # Análise de qualidade
        completude = self._calcular_completude(autor, reu, pedidos, fundamentos)
        problemas = self._identificar_problemas(texto, autor, reu, pedidos)
        sugestoes = self._gerar_sugestoes_melhoria(problemas, completude)
        
        # Estatísticas
        stats = self._calcular_estatisticas(texto, pedidos, fundamentos)
        
        documento = DocumentoEstruturado(
            id_documento=id_doc,
            tipo_documento=tipo_documento,
            data_analise=datetime.now(),
            autor=autor,
            reu=reu,
            terceiros=terceiros,
            tipo_acao=tipo_acao,
            competencia_sugerida=competencia,
            valor_causa=valor_causa,
            classe_processual=classe_processual,
            pedidos=pedidos,
            fundamentos_legais=fundamentos,
            fatos_relevantes=fatos,
            completude_score=completude,
            problemas_identificados=problemas,
            sugestoes_melhoria=sugestoes,
            estatisticas=stats
        )
        
        self.logger.info(f"Extração concluída. Completude: {completude:.2%}")
        return documento
    
    def _gerar_id_documento(self, texto: str) -> str:
        """Gera ID único para o documento"""
        import hashlib
        hash_texto = hashlib.md5(texto.encode()).hexdigest()[:12]
        timestamp = datetime.now().strftime("%Y%m%d%H%M")
        return f"DOC_{timestamp}_{hash_texto}"
    
    def _extrair_autor(self, texto: str) -> EntidadeJuridica:
        """Extrai informações completas do autor"""
        
        # Buscar seção de qualificação
        secao_autor = self._encontrar_secao_qualificacao(texto, "autor|requerente|impetrante")
        
        if not secao_autor:
            # Fallback: buscar no início do documento
            secao_autor = texto[:1000]
        
        nome = self._extrair_nome_entidade(secao_autor, "autor")
        tipo_entidade = self._determinar_tipo_entidade(nome, secao_autor)
        
        return EntidadeJuridica(
            nome=nome,
            tipo=tipo_entidade,
            cpf_cnpj=self._extrair_cpf_cnpj(secao_autor),
            endereco=self._extrair_endereco(secao_autor),
            telefone=self._extrair_telefone(secao_autor),
            email=self._extrair_email(secao_autor),
            representante_legal=self._extrair_representante(secao_autor),
            qualificacao_completa=self._verificar_qualificacao_completa(secao_autor)
        )
    
    def _extrair_reu(self, texto: str) -> EntidadeJuridica:
        """Extrai informações completas do réu"""
        
        # Buscar referências ao réu
        padroes_reu = [
            r'(?:em face de|contra|r[ée]u?)[:\s]+([^,\n.]+)',
            r'(?:requerido|demandado)[:\s]+([^,\n.]+)',
            r'(?:empresa|banco|pessoa jur[íi]dica)\s+([^,\n.]+)'
        ]
        
        nome_reu = "RÉU NÃO IDENTIFICADO"
        contexto_reu = ""
        
        for padrao in padroes_reu:
            match = re.search(padrao, texto, re.IGNORECASE)
            if match:
                nome_reu = match.group(1).strip()
                # Buscar mais contexto
                inicio = max(0, match.start() - 200)
                fim = min(len(texto), match.end() + 500)
                contexto_reu = texto[inicio:fim]
                break
        
        tipo_entidade = self._determinar_tipo_entidade(nome_reu, contexto_reu)
        
        return EntidadeJuridica(
            nome=nome_reu,
            tipo=tipo_entidade,
            cpf_cnpj=self._extrair_cpf_cnpj(contexto_reu),
            endereco=self._extrair_endereco(contexto_reu),
            qualificacao_completa=len(contexto_reu) > 100
        )
    
    def _extrair_terceiros(self, texto: str) -> List[EntidadeJuridica]:
        """Extrai terceiros intervenientes"""
        terceiros = []
        
        # Buscar litisconsortes, assistentes, etc.
        padroes_terceiros = [
            r'(?:litiscons[ió]rcio|em litiscons[ió]rcio)[^.]*?([A-ZÁÊÍÓÚÇÕ][a-záêíóúçõ\s]+)',
            r'(?:assistente|terceiro interessado)[:\s]+([^,\n.]+)',
            r'(?:chamamento ao processo|denunciação)[^.]*?([A-ZÁÊÍÓÚÇÕ][a-záêíóúçõ\s]+)'
        ]
        
        for padrao in padroes_terceiros:
            matches = re.finditer(padrao, texto, re.IGNORECASE)
            for match in matches:
                nome = match.group(1).strip()
                if len(nome) > 5:  # Filtrar nomes muito curtos
                    terceiros.append(EntidadeJuridica(
                        nome=nome,
                        tipo="terceiro",
                        qualificacao_completa=False
                    ))
        
        return terceiros[:5]  # Máximo 5 terceiros
    
    def _encontrar_secao_qualificacao(self, texto: str, tipo_parte: str) -> str:
        """Encontra seção de qualificação da parte"""
        
        # Buscar por padrões de qualificação
        padrao = rf'(?:{tipo_parte})[^:]*:([^,]*(?:brasileir|portador|CPF|RG)[^.]*\.?)'
        match = re.search(padrao, texto, re.IGNORECASE | re.DOTALL)
        
        if match:
            return match.group(1)
        
        return ""
    
    def _extrair_nome_entidade(self, texto: str, tipo: str = "") -> str:
        """Extrai nome da entidade"""
        
        # Padrões específicos para nomes
        padroes = [
            r'([A-ZÁÊÍÓÚÇÕ][a-záêíóúçõ]+(?:\s+[A-ZÁÊÍÓÚÇÕ][a-záêíóúçõ]+){1,4})',  # Nome pessoa física
            r'([A-ZÁÊÍÓÚÇÕ][A-ZÁÊÍÓÚÇÕ\s]+(?:S\.?A\.?|LTDA\.?|ME|EPP))',  # Pessoa jurídica
            r'(BANCO\s+[A-ZÁÊÍÓÚÇÕ\s]+)',  # Bancos
            r'([A-ZÁÊÍÓÚÇÕ\s]+(?:TELECOMUNICAÇÕES|ENERGIA|TELEFONIA))'  # Empresas específicas
        ]
        
        for padrao in padroes:
            match = re.search(padrao, texto)
            if match:
                nome = match.group(1).strip()
                if len(nome) > 3 and nome not in ["DOS", "DAS", "DE", "DA"]:
                    return nome
        
        return f"{tipo.upper()} NÃO IDENTIFICADO" if tipo else "ENTIDADE NÃO IDENTIFICADA"
    
    def _determinar_tipo_entidade(self, nome: str, contexto: str) -> str:
        """Determina tipo da entidade"""
        
        nome_upper = nome.upper()
        contexto_upper = contexto.upper()
        
        # Verificar se é órgão público
        for categoria, orgaos in self.orgaos_conhecidos.items():
            if any(orgao.upper() in nome_upper for orgao in orgaos):
                if categoria == "orgaos_publicos":
                    return "orgao_publico"
                return "pessoa_juridica"
        
        # Indicadores de pessoa jurídica
        if any(indicador in nome_upper for indicador in ["LTDA", "S.A", "S/A", "ME", "EPP", "EIRELI"]):
            return "pessoa_juridica"
        
        if any(indicador in contexto_upper for indicador in ["CNPJ", "EMPRESA", "SOCIEDADE"]):
            return "pessoa_juridica"
        
        # Indicadores de pessoa física
        if any(indicador in contexto_upper for indicador in ["CPF", "RG", "BRASILEIRO", "PORTADOR"]):
            return "pessoa_fisica"
        
        # Heurística: nomes com mais de 2 palavras = pessoa física
        if len(nome.split()) >= 2 and not any(ind in nome_upper for ind in ["BANCO", "EMPRESA", "LTDA"]):
            return "pessoa_fisica"
        
        return "pessoa_juridica"  # Default
    
    def _extrair_cpf_cnpj(self, texto: str) -> Optional[str]:
        """Extrai CPF ou CNPJ"""
        
        # CNPJ
        cnpj_match = re.search(self.padroes_pessoa["cnpj"], texto)
        if cnpj_match:
            return cnpj_match.group(1)
        
        # CPF
        cpf_match = re.search(self.padroes_pessoa["cpf"], texto)
        if cpf_match:
            return cpf_match.group(1)
        
        return None
    
    def _extrair_endereco(self, texto: str) -> Optional[str]:
        """Extrai endereço"""
        match = re.search(self.padroes_pessoa["endereco"], texto, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return None
    
    def _extrair_telefone(self, texto: str) -> Optional[str]:
        """Extrai telefone"""
        match = re.search(self.padroes_pessoa["telefone"], texto, re.IGNORECASE)
        if match:
            return match.group(0).strip()
        return None
    
    def _extrair_email(self, texto: str) -> Optional[str]:
        """Extrai email"""
        match = re.search(self.padroes_pessoa["email"], texto)
        if match:
            return match.group(1)
        return None
    
    def _extrair_representante(self, texto: str) -> Optional[str]:
        """Extrai representante legal"""
        padroes = [
            r'(?:representad[ao] por|advogado)[:\s]+([A-ZÁÊÍÓÚÇÕ][a-záêíóúçõ\s]+)',
            r'(?:procurador|causídico)[:\s]+([A-ZÁÊÍÓÚÇÕ][a-záêíóúçõ\s]+)'
        ]
        
        for padrao in padroes:
            match = re.search(padrao, texto, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _verificar_qualificacao_completa(self, texto: str) -> bool:
        """Verifica se qualificação está completa"""
        indicadores = [
            r'(?:CPF|CNPJ)',
            r'(?:RG|identidade)',
            r'(?:endere[cç]o|reside|domiciliad)',
            r'(?:brasileir|nacionalidade)'
        ]
        
        encontrados = sum(1 for padrao in indicadores if re.search(padrao, texto, re.IGNORECASE))
        return encontrados >= 2
    
    def _classificar_acao_avancada(self, texto: str) -> str:
        """Classificação avançada do tipo de ação"""
        
        texto_lower = texto.lower()
        pontuacoes = {}
        
        # Calcular pontuação para cada tipo
        for tipo, config in self.tipos_acao.items():
            pontuacao = 0
            for palavra in config["palavras_chave"]:
                # Contar ocorrências com peso
                ocorrencias = texto_lower.count(palavra.lower())
                if ocorrencias > 0:
                    pontuacao += ocorrencias * (1 + len(palavra) / 10)  # Palavras maiores têm mais peso
            
            if pontuacao > 0:
                pontuacoes[tipo] = pontuacao
        
        if pontuacoes:
            return max(pontuacoes, key=pontuacoes.get)
        
        return "ação ordinária"
    
    def _analisar_competencia_detalhada(self, texto: str, tipo_acao: str) -> str:
        """Análise detalhada de competência"""
        
        # Verificar valor da causa
        valor = self._extrair_valor_causa_detalhado(texto)
        if valor:
            try:
                valor_num = float(re.sub(r'[^\d,]', '', valor).replace(',', '.'))
                if valor_num <= 40000:  # 40 salários mínimos (2024)
                    return "Juizado Especial Cível"
            except:
                pass
        
        # Análise por tipo de ação
        if "consumidor" in tipo_acao.lower() or "cdc" in texto.lower():
            return "Vara Cível (competente para relações de consumo)"
        
        if any(palavra in texto.lower() for palavra in ["fazenda", "estado", "município", "união"]):
            return "Vara da Fazenda Pública"
        
        if any(palavra in texto.lower() for palavra in ["família", "alimentos", "divórcio", "união estável"]):
            return "Vara de Família e Sucessões"
        
        if any(palavra in texto.lower() for palavra in ["falência", "recuperação judicial", "empresarial"]):
            return "Vara Empresarial"
        
        return "Vara Cível"
    
    def _extrair_valor_causa_detalhado(self, texto: str) -> Optional[str]:
        """Extração detalhada do valor da causa"""
        
        # Buscar valor explícito da causa
        match = re.search(r'valor da causa[:\s]*(?:de\s*)?R?\$?\s*([\d.,]+)', texto, re.IGNORECASE)
        if match:
            return f"R$ {match.group(1)}"
        
        # Buscar outros valores monetários como referência
        valores = re.findall(r'R\$\s*([\d.,]+)', texto)
        if valores:
            # Pegar o maior valor encontrado
            maior_valor = max(valores, key=lambda x: float(x.replace('.', '').replace(',', '.')))
            return f"R$ {maior_valor}"
        
        return None
    
    def _determinar_classe_processual(self, tipo_acao: str) -> str:
        """Determina classe processual CPC"""
        
        mapeamento = {
            "indenização por danos morais": "Indenização por Dano Moral",
            "ação de cobrança": "Cobrança",
            "ação consignatória": "Consignação em Pagamento",
            "revisão contrato bancário": "Revisional de Contrato",
            "ação de reparação de danos - cdc": "Indenização por Dano Material"
        }
        
        return mapeamento.get(tipo_acao, "Procedimento Comum Cível")
    
    def _extrair_pedidos_estruturados(self, texto: str) -> List[PedidoJuridico]:
        """Extrai pedidos de forma estruturada"""
        
        pedidos = []
        
        # Encontrar seção de pedidos
        secao_pedidos = self._encontrar_secao_pedidos(texto)
        
        if secao_pedidos:
            # Dividir pedidos por numeração ou letras
            itens_pedidos = re.split(r'\n?\s*[a-z]\)|\n?\s*\d+[.\)]', secao_pedidos)
            
            for i, item in enumerate(itens_pedidos):
                if len(item.strip()) < 10:
                    continue
                
                pedido = self._analisar_pedido_individual(item.strip(), i)
                if pedido:
                    pedidos.append(pedido)
        
        # Se não encontrou pedidos estruturados, buscar padrões genéricos
        if not pedidos:
            pedidos = self._extrair_pedidos_genericos(texto)
        
        return pedidos[:10]  # Máximo 10 pedidos
    
    def _encontrar_secao_pedidos(self, texto: str) -> str:
        """Encontra seção específica de pedidos"""
        
        padroes = [
            r'(?:dos pedidos|requer|pede)[:\s]+(.*?)(?:termos em que|nestes termos|valor da causa|ante o exposto)',
            r'(?:diante do exposto|isto posto)[^:]*:([^.]*(?:requer|pede)[^.]*)',
            r'(?:pedidos?)[:\s]+(.*?)(?:\n\n|\r\n\r\n|valor da causa)'
        ]
        
        for padrao in padroes:
            match = re.search(padrao, texto, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1)
        
        return ""
    
    def _analisar_pedido_individual(self, texto_pedido: str, ordem: int) -> Optional[PedidoJuridico]:
        """Analisa um pedido individual"""
        
        if len(texto_pedido) < 5:
            return None
        
        # Determinar tipo do pedido
        tipo_pedido = "principal" if ordem == 0 else "subsidiario" if "subsidiariamente" in texto_pedido.lower() else "principal"
        
        # Determinar categoria
        categoria = self._classificar_categoria_pedido(texto_pedido)
        
        # Extrair valor monetário se houver
        valor = None
        valor_match = re.search(r'R\$\s*([\d.,]+)', texto_pedido)
        if valor_match:
            valor = f"R$ {valor_match.group(1)}"
        
        # Extrair prazo se houver
        prazo = None
        prazo_match = re.search(r'(?:prazo de|no prazo de)\s*(\d+\s*dias?)', texto_pedido, re.IGNORECASE)
        if prazo_match:
            prazo = prazo_match.group(1)
        
        return PedidoJuridico(
            tipo=tipo_pedido,
            categoria=categoria,
            descricao=texto_pedido[:300],  # Limitar tamanho
            valor_monetario=valor,
            prazo=prazo,
            fundamentacao=[]
        )
    
    def _classificar_categoria_pedido(self, texto: str) -> str:
        """Classifica categoria do pedido"""
        
        texto_lower = texto.lower()
        
        if any(palavra in texto_lower for palavra in ["condena", "pagamento", "indenização"]):
            return "condenatorio"
        
        if any(palavra in texto_lower for palavra in ["declarar", "reconhecer", "declaração"]):
            return "declaratorio"
        
        if any(palavra in texto_lower for palavra in ["constituir", "resolver", "desconstituir"]):
            return "constitutivo"
        
        return "condenatorio"  # Default
    
    def _extrair_pedidos_genericos(self, texto: str) -> List[PedidoJuridico]:
        """Extrai pedidos usando padrões genéricos"""
        
        pedidos = []
        
        # Pedidos comuns
        pedidos_comuns = [
            ("indenização por danos morais", "condenatorio"),
            ("condenação em custas e honorários", "condenatorio"),
            ("aplicação dos benefícios da justiça gratuita", "declaratorio")
        ]
        
        for descricao, categoria in pedidos_comuns:
            if any(palavra in texto.lower() for palavra in descricao.split()[:2]):
                pedidos.append(PedidoJuridico(
                    tipo="principal",
                    categoria=categoria,
                    descricao=descricao,
                    fundamentacao=[]
                ))
        
        return pedidos
    
    def _extrair_fundamentos_estruturados(self, texto: str) -> List[FundamentoLegal]:
        """Extrai fundamentação legal estruturada"""
        
        fundamentos = []
        
        # Extrair artigos
        for match in re.finditer(self.padroes_legal["artigo"], texto, re.IGNORECASE):
            artigo = match.group(1) if match.group(1) else ""
            paragrafo = match.group(2) if match.group(2) else ""
            lei = match.group(3) if match.group(3) else ""
            
            referencia = f"Art. {artigo}"
            if paragrafo:
                referencia += f", § {paragrafo}"
            if lei:
                referencia += f" da {lei}"
            
            fundamentos.append(FundamentoLegal(
                tipo="lei",
                referencia=referencia,
                contexto=match.group(0),
                categoria=self._classificar_categoria_legal(lei if lei else "")
            ))
        
        # Extrair súmulas
        for match in re.finditer(self.padroes_legal["sumula"], texto, re.IGNORECASE):
            numero = match.group(1)
            tribunal = match.group(2) if match.group(2) else "STJ"
            
            fundamentos.append(FundamentoLegal(
                tipo="sumula",
                referencia=f"Súmula {numero} - {tribunal}",
                contexto=match.group(0),
                categoria="jurisprudencia"
            ))
        
        # Extrair jurisprudência
        for match in re.finditer(self.padroes_legal["jurisprudencia"], texto, re.IGNORECASE):
            tribunal = match.group(1)
            numero = match.group(2)
            
            fundamentos.append(FundamentoLegal(
                tipo="jurisprudencia",
                referencia=f"{tribunal} - {numero}",
                contexto=match.group(0),
                categoria="jurisprudencia"
            ))
        
        return fundamentos[:20]  # Máximo 20 fundamentos
    
    def _classificar_categoria_legal(self, texto: str) -> str:
        """Classifica categoria da fundamentação legal"""
        
        texto_lower = texto.lower()
        
        if any(palavra in texto_lower for palavra in ["constituição", "cf"]):
            return "constitucional"
        
        if any(palavra in texto_lower for palavra in ["código civil", "cc"]):
            return "civil"
        
        if any(palavra in texto_lower for palavra in ["cdc", "consumidor"]):
            return "consumidor"
        
        if any(palavra in texto_lower for palavra in ["cpc", "processo civil"]):
            return "processual"
        
        return "geral"
    
    def _extrair_fatos_relevantes(self, texto: str) -> List[str]:
        """Extrai fatos relevantes da narrativa"""
        
        fatos = []
        
        # Buscar seção de fatos
        secao_fatos = self._encontrar_secao_fatos(texto)
        
        if secao_fatos:
            # Dividir em parágrafos
            paragrafos = [p.strip() for p in secao_fatos.split('\n') if len(p.strip()) > 50]
            fatos.extend(paragrafos[:10])  # Máximo 10 fatos
        
        return fatos
    
    def _encontrar_secao_fatos(self, texto: str) -> str:
        """Encontra seção de fatos"""
        
        padroes = [
            r'(?:dos fatos|relatório|histórico)[:\s]+(.*?)(?:do direito|fundamentos|pedidos)',
            r'(?:ocorreu que|aconteceu que|é que)[^.]*\.(.*?)(?:diante|assim|portanto)'
        ]
        
        for padrao in padroes:
            match = re.search(padrao, texto, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1)
        
        return ""
    
    def _calcular_completude(self, autor: EntidadeJuridica, reu: EntidadeJuridica, 
                           pedidos: List[PedidoJuridico], fundamentos: List[FundamentoLegal]) -> float:
        """Calcula score de completude do documento"""
        
        pontos = 0
        total = 10
        
        # Qualificação do autor (2 pontos)
        if autor.qualificacao_completa:
            pontos += 2
        elif autor.nome != "AUTOR NÃO IDENTIFICADO":
            pontos += 1
        
        # Identificação do réu (1 ponto)
        if reu.nome != "RÉU NÃO IDENTIFICADO":
            pontos += 1
        
        # Pedidos (3 pontos)
        if len(pedidos) >= 3:
            pontos += 3
        elif len(pedidos) >= 1:
            pontos += len(pedidos)
        
        # Fundamentação legal (2 pontos)
        if len(fundamentos) >= 3:
            pontos += 2
        elif len(fundamentos) >= 1:
            pontos += 1
        
        # Valor da causa (1 ponto)
        if hasattr(self, '_ultimo_valor_causa') and self._ultimo_valor_causa:
            pontos += 1
        
        # Estrutura processual (1 ponto)
        if len(pedidos) > 0 and len(fundamentos) > 0:
            pontos += 1
        
        return pontos / total
    
    def _identificar_problemas(self, texto: str, autor: EntidadeJuridica, 
                             reu: EntidadeJuridica, pedidos: List[PedidoJuridico]) -> List[str]:
        """Identifica problemas no documento"""
        
        problemas = []
        
        # Problemas de qualificação
        if not autor.qualificacao_completa:
            problemas.append("Qualificação incompleta do autor")
        
        if reu.nome == "RÉU NÃO IDENTIFICADO":
            problemas.append("Réu não identificado adequadamente")
        
        # Problemas de estrutura
        if len(pedidos) == 0:
            problemas.append("Nenhum pedido identificado")
        
        if "valor da causa" not in texto.lower():
            problemas.append("Valor da causa não especificado")
        
        # Problemas de fundamentação
        if not any(palavra in texto.lower() for palavra in ["artigo", "art.", "lei", "código"]):
            problemas.append("Fundamentação legal insuficiente")
        
        return problemas
    
    def _gerar_sugestoes_melhoria(self, problemas: List[str], completude: float) -> List[str]:
        """Gera sugestões de melhoria"""
        
        sugestoes = []
        
        # Sugestões baseadas nos problemas
        for problema in problemas:
            if "qualificação" in problema.lower():
                sugestoes.append("📝 Incluir CPF/CNPJ, RG e endereço completo das partes")
            elif "réu não identificado" in problema.lower():
                sugestoes.append("🎯 Especificar corretamente a qualificação do réu")
            elif "pedido" in problema.lower():
                sugestoes.append("📋 Estruturar pedidos de forma clara e numerada")
            elif "valor da causa" in problema.lower():
                sugestoes.append("💰 Especificar valor da causa conforme CPC Art. 292")
            elif "fundamentação" in problema.lower():
                sugestoes.append("📚 Incluir base legal específica para os pedidos")
        
        # Sugestões baseadas na completude
        if completude < 0.5:
            sugestoes.append("⚠️ Documento necessita revisão geral da estrutura")
        elif completude < 0.8:
            sugestoes.append("✨ Documento pode ser aprimorado com detalhes adicionais")
        
        return sugestoes
    
    def _calcular_estatisticas(self, texto: str, pedidos: List[PedidoJuridico], 
                             fundamentos: List[FundamentoLegal]) -> Dict[str, Any]:
        """Calcula estatísticas do documento"""
        
        palavras = len(texto.split())
        caracteres = len(texto)
        paragrafos = len([p for p in texto.split('\n') if p.strip()])
        
        return {
            "palavras": palavras,
            "caracteres": caracteres,
            "paragrafos": paragrafos,
            "pedidos_count": len(pedidos),
            "fundamentos_count": len(fundamentos),
            "densidade_legal": len(fundamentos) / max(palavras / 100, 1),  # Fundamentos por 100 palavras
            "complexidade": "alta" if palavras > 2000 else "média" if palavras > 1000 else "baixa"
        }
    
    def exportar_json(self, documento: DocumentoEstruturado, caminho: str) -> str:
        """Exporta documento estruturado em JSON"""
        
        # Converter para dicionário serializable
        dados = asdict(documento)
        
        # Converter datetime para string
        dados["data_analise"] = documento.data_analise.isoformat()
        
        # Salvar arquivo
        caminho_arquivo = Path(caminho)
        caminho_arquivo.parent.mkdir(parents=True, exist_ok=True)
        
        with open(caminho_arquivo, 'w', encoding='utf-8') as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
        
        return str(caminho_arquivo)
    
    def gerar_relatorio_analise(self, documento: DocumentoEstruturado) -> str:
        """Gera relatório detalhado da análise"""
        
        relatorio = f"""
# RELATÓRIO DE ANÁLISE ESTRUTURADA
**Documento:** {documento.id_documento}
**Tipo:** {documento.tipo_documento}
**Data da Análise:** {documento.data_analise.strftime('%d/%m/%Y %H:%M')}

## RESUMO EXECUTIVO
- **Completude:** {documento.completude_score:.1%}
- **Tipo de Ação:** {documento.tipo_acao}
- **Competência:** {documento.competencia_sugerida}
- **Valor da Causa:** {documento.valor_causa or 'Não especificado'}

## PARTES PROCESSUAIS

### AUTOR
- **Nome:** {documento.autor.nome}
- **Tipo:** {documento.autor.tipo}
- **CPF/CNPJ:** {documento.autor.cpf_cnpj or 'Não informado'}
- **Qualificação Completa:** {'✅ Sim' if documento.autor.qualificacao_completa else '❌ Não'}

### RÉU
- **Nome:** {documento.reu.nome}
- **Tipo:** {documento.reu.tipo}
- **CPF/CNPJ:** {documento.reu.cpf_cnpj or 'Não informado'}

## PEDIDOS ({len(documento.pedidos)})
"""
        
        for i, pedido in enumerate(documento.pedidos, 1):
            relatorio += f"""
### Pedido {i}
- **Tipo:** {pedido.tipo}
- **Categoria:** {pedido.categoria}
- **Descrição:** {pedido.descricao[:100]}...
- **Valor:** {pedido.valor_monetario or 'Não especificado'}
"""
        
        relatorio += f"""
## FUNDAMENTAÇÃO LEGAL ({len(documento.fundamentos_legais)})
"""
        
        for fund in documento.fundamentos_legais[:10]:
            relatorio += f"- **{fund.tipo.title()}:** {fund.referencia}\n"
        
        if documento.problemas_identificados:
            relatorio += "\n## PROBLEMAS IDENTIFICADOS\n"
            for problema in documento.problemas_identificados:
                relatorio += f"- ❌ {problema}\n"
        
        if documento.sugestoes_melhoria:
            relatorio += "\n## SUGESTÕES DE MELHORIA\n"
            for sugestao in documento.sugestoes_melhoria:
                relatorio += f"- {sugestao}\n"
        
        relatorio += f"""
## ESTATÍSTICAS
- **Palavras:** {documento.estatisticas['palavras']}
- **Parágrafos:** {documento.estatisticas['paragrafos']}
- **Complexidade:** {documento.estatisticas['complexidade']}
- **Densidade Legal:** {documento.estatisticas['densidade_legal']:.2f} fundamentos/100 palavras

---
*Relatório gerado automaticamente pelo Sistema de Extração Estruturada*
"""
        
        return relatorio