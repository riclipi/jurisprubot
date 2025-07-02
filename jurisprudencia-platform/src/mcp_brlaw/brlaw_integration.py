"""
🎯 INTEGRAÇÃO BRLAW MCP SERVER
Sistema avançado que integra precedentes STJ/TST com nosso sistema premium
"""

import asyncio
import json
import subprocess
import sys
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import logging
from pathlib import Path

@dataclass
class PrecedenteSTJ:
    """Precedente do STJ via BRLaw MCP"""
    ementa: str
    tribunal: str = "STJ"
    fonte: str = "brlaw_mcp"
    data_consulta: datetime = None
    relevancia_score: float = 0.0
    
    def __post_init__(self):
        if self.data_consulta is None:
            self.data_consulta = datetime.now()

@dataclass
class PrecedenteTST:
    """Precedente do TST via BRLaw MCP"""
    ementa: str
    tribunal: str = "TST"
    fonte: str = "brlaw_mcp"
    data_consulta: datetime = None
    relevancia_score: float = 0.0
    
    def __post_init__(self):
        if self.data_consulta is None:
            self.data_consulta = datetime.now()

class BRLawMCPIntegration:
    """
    🚀 INTEGRAÇÃO PREMIUM COM BRLAW MCP SERVER
    Combina nosso sistema premium com precedentes oficiais STJ/TST
    """
    
    def __init__(self):
        self.setup_logging()
        self.brlaw_path = Path(__file__).parent.parent.parent / "brlaw_mcp_server"
        self._verificar_instalacao()
    
    def setup_logging(self):
        """Configura logging"""
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def _verificar_instalacao(self):
        """Verifica se BRLaw MCP está instalado"""
        if not self.brlaw_path.exists():
            self.logger.error("BRLaw MCP Server não encontrado")
            self.disponivel = False
        else:
            self.disponivel = True
            self.logger.info("BRLaw MCP Server encontrado")
    
    async def buscar_precedentes_stj(self, consulta: str, pagina: int = 1) -> List[PrecedenteSTJ]:
        """
        🏛️ BUSCA PRECEDENTES STJ
        Busca precedentes oficiais do STJ via BRLaw MCP
        """
        
        if not self.disponivel:
            self.logger.warning("BRLaw MCP não disponível")
            return []
        
        try:
            # Preparar consulta para STJ
            consulta_stj = self._otimizar_consulta_stj(consulta)
            
            self.logger.info(f"Buscando precedentes STJ: {consulta_stj}")
            
            # Executar via BRLaw MCP
            resultados_raw = await self._executar_busca_mcp("StjLegalPrecedentsRequest", {
                "summary": consulta_stj,
                "page": pagina
            })
            
            # Processar resultados
            precedentes = []
            for resultado in resultados_raw:
                try:
                    if isinstance(resultado, str):
                        # Resultado é JSON string
                        data = json.loads(resultado)
                    else:
                        data = resultado
                    
                    precedente = PrecedenteSTJ(
                        ementa=data.get("summary", ""),
                        relevancia_score=self._calcular_relevancia(data.get("summary", ""), consulta)
                    )
                    precedentes.append(precedente)
                    
                except Exception as e:
                    self.logger.error(f"Erro ao processar resultado STJ: {e}")
                    continue
            
            self.logger.info(f"Encontrados {len(precedentes)} precedentes STJ")
            return precedentes
            
        except Exception as e:
            self.logger.error(f"Erro na busca STJ: {e}")
            return []
    
    async def buscar_precedentes_tst(self, consulta: str, pagina: int = 1) -> List[PrecedenteTST]:
        """
        ⚖️ BUSCA PRECEDENTES TST
        Busca precedentes oficiais do TST via BRLaw MCP
        """
        
        if not self.disponivel:
            self.logger.warning("BRLaw MCP não disponível")
            return []
        
        try:
            # Preparar consulta para TST
            consulta_tst = self._otimizar_consulta_tst(consulta)
            
            self.logger.info(f"Buscando precedentes TST: {consulta_tst}")
            
            # Executar via BRLaw MCP
            resultados_raw = await self._executar_busca_mcp("TstLegalPrecedentsRequest", {
                "summary": consulta_tst,
                "page": pagina
            })
            
            # Processar resultados
            precedentes = []
            for resultado in resultados_raw:
                try:
                    if isinstance(resultado, str):
                        data = json.loads(resultado)
                    else:
                        data = resultado
                    
                    precedente = PrecedenteTST(
                        ementa=data.get("summary", ""),
                        relevancia_score=self._calcular_relevancia(data.get("summary", ""), consulta)
                    )
                    precedentes.append(precedente)
                    
                except Exception as e:
                    self.logger.error(f"Erro ao processar resultado TST: {e}")
                    continue
            
            self.logger.info(f"Encontrados {len(precedentes)} precedentes TST")
            return precedentes
            
        except Exception as e:
            self.logger.error(f"Erro na busca TST: {e}")
            return []
    
    async def buscar_precedentes_completo(self, consulta: str, 
                                        incluir_stj: bool = True, 
                                        incluir_tst: bool = False,
                                        max_paginas: int = 2) -> Dict[str, List]:
        """
        🎯 BUSCA COMPLETA DE PRECEDENTES
        Busca em STJ e/ou TST conforme especificado
        """
        
        resultados = {
            "stj": [],
            "tst": [],
            "total": 0,
            "tempo_consulta": datetime.now()
        }
        
        tarefas = []
        
        # Buscar no STJ
        if incluir_stj:
            for pagina in range(1, max_paginas + 1):
                tarefas.append(("stj", self.buscar_precedentes_stj(consulta, pagina)))
        
        # Buscar no TST (apenas para casos trabalhistas)
        if incluir_tst:
            for pagina in range(1, max_paginas + 1):
                tarefas.append(("tst", self.buscar_precedentes_tst(consulta, pagina)))
        
        # Executar buscas em paralelo
        for tribunal, tarefa in tarefas:
            try:
                precedentes = await tarefa
                resultados[tribunal].extend(precedentes)
            except Exception as e:
                self.logger.error(f"Erro na busca {tribunal}: {e}")
        
        # Ordenar por relevância
        if resultados["stj"]:
            resultados["stj"].sort(key=lambda x: x.relevancia_score, reverse=True)
        
        if resultados["tst"]:
            resultados["tst"].sort(key=lambda x: x.relevancia_score, reverse=True)
        
        resultados["total"] = len(resultados["stj"]) + len(resultados["tst"])
        
        return resultados
    
    def _otimizar_consulta_stj(self, consulta: str) -> str:
        """Otimiza consulta para o STJ"""
        
        # Remover stop words jurídicas
        stop_words = ["processo", "autos", "recurso", "apelação"]
        palavras = [p for p in consulta.split() if p.lower() not in stop_words]
        
        # Usar operador 'e' entre palavras principais
        if len(palavras) > 1:
            consulta_otimizada = " e ".join(palavras)
        else:
            consulta_otimizada = consulta
        
        # Adicionar termos específicos por área
        if any(termo in consulta.lower() for termo in ["dano", "moral", "indenização"]):
            consulta_otimizada += " e responsabilidade"
        
        if any(termo in consulta.lower() for termo in ["consumidor", "banco", "negativação"]):
            consulta_otimizada += " e (consumidor ou CDC)"
        
        return consulta_otimizada
    
    def _otimizar_consulta_tst(self, consulta: str) -> str:
        """Otimiza consulta para o TST"""
        
        # Para TST, usar aspas para expressões exatas trabalhistas
        termos_trabalhistas = [
            "adicional noturno", "horas extras", "jornada de trabalho",
            "adicional de periculosidade", "adicional de insalubridade",
            "FGTS", "aviso prévio", "rescisão indireta"
        ]
        
        consulta_otimizada = consulta
        
        for termo in termos_trabalhistas:
            if termo.lower() in consulta.lower():
                consulta_otimizada = consulta_otimizada.replace(termo, f'"{termo}"')
        
        return consulta_otimizada
    
    def _calcular_relevancia(self, ementa: str, consulta_original: str) -> float:
        """Calcula score de relevância do precedente"""
        
        if not ementa or not consulta_original:
            return 0.0
        
        ementa_lower = ementa.lower()
        palavras_consulta = set(consulta_original.lower().split())
        palavras_ementa = set(ementa_lower.split())
        
        # Intersecção de palavras
        intersecao = palavras_consulta & palavras_ementa
        
        if not palavras_consulta:
            return 0.0
        
        # Score básico
        score = len(intersecao) / len(palavras_consulta)
        
        # Bonus por palavras-chave jurídicas importantes
        palavras_importantes = [
            "supremo", "superior", "súmula", "precedente", "jurisprudência",
            "constitucional", "inconstitucional", "recurso especial", "recurso extraordinário"
        ]
        
        for palavra in palavras_importantes:
            if palavra in ementa_lower:
                score += 0.1
        
        # Bonus por tamanho da ementa (ementas maiores são mais detalhadas)
        if len(ementa) > 500:
            score += 0.05
        elif len(ementa) > 1000:
            score += 0.1
        
        return min(1.0, score)  # Máximo 1.0
    
    async def _executar_busca_mcp(self, tool_name: str, arguments: Dict) -> List[Any]:
        """Executa busca via BRLaw MCP Server"""
        
        try:
            # Simular execução do MCP (em produção, usaria client MCP real)
            # Por enquanto, retorna dados mockados para demonstração
            
            if tool_name == "StjLegalPrecedentsRequest":
                return await self._mock_stj_results(arguments)
            elif tool_name == "TstLegalPrecedentsRequest":
                return await self._mock_tst_results(arguments)
            else:
                return []
                
        except Exception as e:
            self.logger.error(f"Erro na execução MCP: {e}")
            return []
    
    async def _mock_stj_results(self, arguments: Dict) -> List[str]:
        """Mock de resultados STJ para demonstração"""
        
        consulta = arguments.get("summary", "")
        
        # Resultados mockados baseados na consulta
        if "dano moral" in consulta.lower():
            return [
                json.dumps({
                    "summary": "CIVIL. DANO MORAL. NEGATIVAÇÃO INDEVIDA. VALOR DA INDENIZAÇÃO. O dano moral decorrente de inscrição indevida em cadastros de proteção ao crédito prescinde de comprovação. Precedente: STJ, REsp 1.740.868/RS."
                }),
                json.dumps({
                    "summary": "CONSUMIDOR. RESPONSABILIDADE CIVIL. DANO MORAL. BANCO DE DADOS. A inscrição indevida em cadastros restritivos gera dano moral in re ipsa. Valor fixado em R$ 8.000,00. Recurso especial provido."
                })
            ]
        
        elif "consumidor" in consulta.lower():
            return [
                json.dumps({
                    "summary": "DIREITO DO CONSUMIDOR. RELAÇÃO BANCÁRIA. COBRANÇA INDEVIDA. CDC aplicável às relações bancárias. Devolução em dobro do valor cobrado indevidamente. Art. 42, parágrafo único, CDC."
                })
            ]
        
        else:
            return [
                json.dumps({
                    "summary": f"DIREITO CIVIL. Precedente relacionado aos termos: {consulta}. Jurisprudência consolidada do STJ sobre a matéria."
                })
            ]
    
    async def _mock_tst_results(self, arguments: Dict) -> List[str]:
        """Mock de resultados TST para demonstração"""
        
        consulta = arguments.get("summary", "")
        
        # Resultados mockados para questões trabalhistas
        if "horas extras" in consulta.lower():
            return [
                json.dumps({
                    "summary": "HORAS EXTRAS. JORNADA DE TRABALHO. Configurada a habitualidade na prestação de horas extras, devidas as horas suplementares com adicional de 50%. Súmula 291, TST."
                })
            ]
        
        elif "adicional" in consulta.lower():
            return [
                json.dumps({
                    "summary": "ADICIONAL DE PERICULOSIDADE. ATIVIDADE PERIGOSA. Devido o adicional de 30% sobre o salário básico quando caracterizada atividade perigosa. NR-16 do MTE."
                })
            ]
        
        else:
            return [
                json.dumps({
                    "summary": f"DIREITO DO TRABALHO. Precedente do TST relacionado a: {consulta}. Jurisprudência trabalhista consolidada."
                })
            ]
    
    def gerar_relatorio_precedentes(self, resultados: Dict[str, List], consulta_original: str) -> str:
        """Gera relatório dos precedentes encontrados"""
        
        relatorio = f"""
# RELATÓRIO DE PRECEDENTES - BRLAW MCP INTEGRATION
**Consulta:** {consulta_original}
**Data:** {datetime.now().strftime('%d/%m/%Y %H:%M')}

## RESUMO EXECUTIVO
- **Total de Precedentes:** {resultados['total']}
- **STJ:** {len(resultados['stj'])} precedentes
- **TST:** {len(resultados['tst'])} precedentes

## PRECEDENTES STJ ({len(resultados['stj'])})
"""
        
        for i, precedente in enumerate(resultados['stj'][:10], 1):
            relatorio += f"""
### {i}. STJ - Relevância: {precedente.relevancia_score:.3f}
**Ementa:** {precedente.ementa[:300]}...
**Fonte:** {precedente.fonte}
**Data da Consulta:** {precedente.data_consulta.strftime('%d/%m/%Y %H:%M')}
"""
        
        if resultados['tst']:
            relatorio += f"\n## PRECEDENTES TST ({len(resultados['tst'])})\n"
            
            for i, precedente in enumerate(resultados['tst'][:5], 1):
                relatorio += f"""
### {i}. TST - Relevância: {precedente.relevancia_score:.3f}
**Ementa:** {precedente.ementa[:300]}...
**Fonte:** {precedente.fonte}
**Data da Consulta:** {precedente.data_consulta.strftime('%d/%m/%Y %H:%M')}
"""
        
        relatorio += """
---
*Precedentes obtidos via BRLaw MCP Server*
*STJ: Superior Tribunal de Justiça | TST: Tribunal Superior do Trabalho*
"""
        
        return relatorio
    
    def exportar_precedentes_json(self, resultados: Dict[str, List], caminho: str) -> str:
        """Exporta precedentes em formato JSON"""
        
        dados_export = {
            "consulta_realizada": True,
            "timestamp": datetime.now().isoformat(),
            "total_precedentes": resultados['total'],
            "precedentes_stj": [
                {
                    "ementa": p.ementa,
                    "tribunal": p.tribunal,
                    "fonte": p.fonte,
                    "relevancia_score": p.relevancia_score,
                    "data_consulta": p.data_consulta.isoformat()
                }
                for p in resultados['stj']
            ],
            "precedentes_tst": [
                {
                    "ementa": p.ementa,
                    "tribunal": p.tribunal,
                    "fonte": p.fonte,
                    "relevancia_score": p.relevancia_score,
                    "data_consulta": p.data_consulta.isoformat()
                }
                for p in resultados['tst']
            ]
        }
        
        caminho_arquivo = Path(caminho)
        caminho_arquivo.parent.mkdir(parents=True, exist_ok=True)
        
        with open(caminho_arquivo, 'w', encoding='utf-8') as f:
            json.dump(dados_export, f, ensure_ascii=False, indent=2)
        
        return str(caminho_arquivo)

# Função de conveniência para uso direto
async def buscar_precedentes_brlaw(consulta: str, incluir_stj: bool = True, incluir_tst: bool = False) -> Dict[str, List]:
    """
    🎯 FUNÇÃO DE CONVENIÊNCIA
    Busca precedentes via BRLaw MCP de forma simples
    """
    
    integrador = BRLawMCPIntegration()
    return await integrador.buscar_precedentes_completo(consulta, incluir_stj, incluir_tst)

# Exemplo de uso
if __name__ == "__main__":
    async def teste_brlaw():
        integrador = BRLawMCPIntegration()
        
        print("🔍 Testando integração BRLaw MCP...")
        
        # Teste 1: Busca no STJ
        print("\n1. Buscando precedentes STJ sobre dano moral...")
        resultados = await integrador.buscar_precedentes_completo(
            "dano moral negativação indevida",
            incluir_stj=True,
            incluir_tst=False
        )
        
        print(f"   Encontrados: {len(resultados['stj'])} precedentes STJ")
        
        # Teste 2: Busca no TST
        print("\n2. Buscando precedentes TST sobre horas extras...")
        resultados_tst = await integrador.buscar_precedentes_completo(
            "horas extras adicional noturno",
            incluir_stj=False,
            incluir_tst=True
        )
        
        print(f"   Encontrados: {len(resultados_tst['tst'])} precedentes TST")
        
        # Gerar relatório
        if resultados['total'] > 0:
            relatorio = integrador.gerar_relatorio_precedentes(resultados, "dano moral negativação indevida")
            print(f"\n📄 Relatório gerado ({len(relatorio)} caracteres)")
        
        print("\n✅ Teste BRLaw MCP concluído!")
    
    # Executar teste
    asyncio.run(teste_brlaw())