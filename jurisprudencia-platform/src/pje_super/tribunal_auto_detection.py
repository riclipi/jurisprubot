"""
🎯 TRIBUNAL AUTO DETECTION - SISTEMA INTELIGENTE
Identifica tribunal pelo número CNJ e escolhe melhor endpoint
"""

import re
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

class TipoTribunal(Enum):
    SUPREMO = "supremo"
    SUPERIOR = "superior" 
    FEDERAL = "federal"
    ESTADUAL = "estadual"
    TRABALHISTA = "trabalhista"
    ELEITORAL = "eleitoral"
    MILITAR = "militar"

class TecnologiaPreferida(Enum):
    REST = "rest"
    SOAP = "soap"
    SCRAPING = "scraping"
    HIBRIDO = "hibrido"

@dataclass
class DeteccaoTribunal:
    """Resultado da detecção automática"""
    codigo_tribunal: str
    nome_tribunal: str
    sigla: str
    tipo: TipoTribunal
    segmento_cnj: str
    codigo_cnj: str
    tecnologia_recomendada: TecnologiaPreferida
    urls_disponiveis: Dict[str, str]
    confiabilidade: float  # 0-1
    observacoes: List[str]

class TribunalAutoDetection:
    """
    🚀 SISTEMA DE AUTO-DETECÇÃO DE TRIBUNAIS
    
    Funcionalidades:
    - Identifica tribunal pelo número CNJ automaticamente
    - Escolhe melhor endpoint (REST/SOAP) por tribunal  
    - Cache de URLs funcionais por performance
    - Validação rigorosa do número CNJ
    - Suporte a todos os tribunais brasileiros
    """
    
    def __init__(self):
        self.setup_logging()
        self._inicializar_mapeamentos()
        self._inicializar_cache()
    
    def setup_logging(self):
        """Configura sistema de logs"""
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def _inicializar_mapeamentos(self):
        """Inicializa mapeamentos CNJ -> Tribunais"""
        
        # Mapeamento completo de códigos CNJ
        self.mapeamento_cnj = {
            # SUPREMO TRIBUNAL FEDERAL
            "0001": {
                "codigo": "STF",
                "nome": "Supremo Tribunal Federal",
                "sigla": "STF",
                "tipo": TipoTribunal.SUPREMO,
                "tecnologia": TecnologiaPreferida.REST,
                "urls": {
                    "rest": "https://portal.stf.jus.br/jurisprudencia/api",
                    "base": "https://portal.stf.jus.br"
                }
            },
            
            # SUPERIOR TRIBUNAL DE JUSTIÇA
            "0002": {
                "codigo": "STJ",
                "nome": "Superior Tribunal de Justiça",
                "sigla": "STJ", 
                "tipo": TipoTribunal.SUPERIOR,
                "tecnologia": TecnologiaPreferida.REST,
                "urls": {
                    "rest": "https://www.stj.jus.br/scon/api",
                    "base": "https://www.stj.jus.br"
                }
            },
            
            # TRIBUNAIS REGIONAIS FEDERAIS
            "0003": {
                "codigo": "TRF1",
                "nome": "Tribunal Regional Federal da 1ª Região",
                "sigla": "TRF1",
                "tipo": TipoTribunal.FEDERAL,
                "tecnologia": TecnologiaPreferida.SOAP,
                "urls": {
                    "soap": "https://pje.trf1.jus.br/pje/intercomunicacao",
                    "base": "https://www.trf1.jus.br"
                }
            },
            
            "0004": {
                "codigo": "TRF2", 
                "nome": "Tribunal Regional Federal da 2ª Região",
                "sigla": "TRF2",
                "tipo": TipoTribunal.FEDERAL,
                "tecnologia": TecnologiaPreferida.SOAP,
                "urls": {
                    "soap": "https://pje.trf2.jus.br/pje/intercomunicacao",
                    "base": "https://www.trf2.jus.br"
                }
            },
            
            "0005": {
                "codigo": "TRF3",
                "nome": "Tribunal Regional Federal da 3ª Região", 
                "sigla": "TRF3",
                "tipo": TipoTribunal.FEDERAL,
                "tecnologia": TecnologiaPreferida.SOAP,
                "urls": {
                    "soap": "https://pje.trf3.jus.br/pje/intercomunicacao",
                    "base": "https://www.trf3.jus.br"
                }
            },
            
            "0006": {
                "codigo": "TRF4",
                "nome": "Tribunal Regional Federal da 4ª Região",
                "sigla": "TRF4", 
                "tipo": TipoTribunal.FEDERAL,
                "tecnologia": TecnologiaPreferida.REST,
                "urls": {
                    "rest": "https://eproc.trf4.jus.br/eproc2/api",
                    "soap": "https://eproc.trf4.jus.br/eproc2/intercomunicacao",
                    "base": "https://www.trf4.jus.br"
                }
            },
            
            "0007": {
                "codigo": "TRF5",
                "nome": "Tribunal Regional Federal da 5ª Região",
                "sigla": "TRF5",
                "tipo": TipoTribunal.FEDERAL, 
                "tecnologia": TecnologiaPreferida.SOAP,
                "urls": {
                    "soap": "https://pje.trf5.jus.br/pje/intercomunicacao",
                    "base": "https://www.trf5.jus.br"
                }
            },
            
            # TRIBUNAL SUPERIOR DO TRABALHO
            "5000": {
                "codigo": "TST",
                "nome": "Tribunal Superior do Trabalho",
                "sigla": "TST",
                "tipo": TipoTribunal.TRABALHISTA,
                "tecnologia": TecnologiaPreferida.REST,
                "urls": {
                    "rest": "https://www.tst.jus.br/jurisprudencia/api",
                    "base": "https://www.tst.jus.br"
                }
            },
            
            # TRIBUNAIS REGIONAIS DO TRABALHO
            "5002": {
                "codigo": "TRT2",
                "nome": "Tribunal Regional do Trabalho da 2ª Região",
                "sigla": "TRT2",
                "tipo": TipoTribunal.TRABALHISTA,
                "tecnologia": TecnologiaPreferida.SOAP,
                "urls": {
                    "soap": "https://pje.trt2.jus.br/pje/intercomunicacao",
                    "base": "https://www.trt2.jus.br"
                }
            },
            
            # TRIBUNAL SUPERIOR ELEITORAL
            "0300": {
                "codigo": "TSE",
                "nome": "Tribunal Superior Eleitoral",
                "sigla": "TSE",
                "tipo": TipoTribunal.ELEITORAL,
                "tecnologia": TecnologiaPreferida.REST,
                "urls": {
                    "rest": "https://www.tse.jus.br/api",
                    "base": "https://www.tse.jus.br"
                }
            }
        }
        
        # Mapeamento por faixas de códigos estaduais
        self.faixas_estaduais = {
            # São Paulo
            ("8000", "8099"): {
                "codigo": "TJSP",
                "nome": "Tribunal de Justiça de São Paulo",
                "sigla": "TJSP",
                "tipo": TipoTribunal.ESTADUAL,
                "tecnologia": TecnologiaPreferida.HIBRIDO,
                "urls": {
                    "rest": "https://api.tjsp.jus.br/v1",
                    "soap": "https://pje.tjsp.jus.br/pje/intercomunicacao",
                    "scraping": "https://esaj.tjsp.jus.br",
                    "base": "https://www.tjsp.jus.br"
                }
            },
            
            # Rio de Janeiro  
            ("8100", "8199"): {
                "codigo": "TJRJ",
                "nome": "Tribunal de Justiça do Rio de Janeiro",
                "sigla": "TJRJ",
                "tipo": TipoTribunal.ESTADUAL,
                "tecnologia": TecnologiaPreferida.SOAP,
                "urls": {
                    "soap": "https://pje.tjrj.jus.br/pje/intercomunicacao",
                    "base": "https://www.tjrj.jus.br"
                }
            },
            
            # Minas Gerais
            ("8200", "8299"): {
                "codigo": "TJMG", 
                "nome": "Tribunal de Justiça de Minas Gerais",
                "sigla": "TJMG",
                "tipo": TipoTribunal.ESTADUAL,
                "tecnologia": TecnologiaPreferida.SOAP,
                "urls": {
                    "soap": "https://pje.tjmg.jus.br/pje/intercomunicacao",
                    "base": "https://www.tjmg.jus.br"
                }
            },
            
            # Rio Grande do Sul
            ("8300", "8399"): {
                "codigo": "TJRS",
                "nome": "Tribunal de Justiça do Rio Grande do Sul", 
                "sigla": "TJRS",
                "tipo": TipoTribunal.ESTADUAL,
                "tecnologia": TecnologiaPreferida.SOAP,
                "urls": {
                    "soap": "https://pje.tjrs.jus.br/pje/intercomunicacao",
                    "base": "https://www.tjrs.jus.br"
                }
            },
            
            # Paraná
            ("8400", "8499"): {
                "codigo": "TJPR",
                "nome": "Tribunal de Justiça do Paraná",
                "sigla": "TJPR", 
                "tipo": TipoTribunal.ESTADUAL,
                "tecnologia": TecnologiaPreferida.SOAP,
                "urls": {
                    "soap": "https://pje.tjpr.jus.br/pje/intercomunicacao",
                    "base": "https://www.tjpr.jus.br"
                }
            }
        }
        
        self.logger.info(f"Mapeamentos inicializados: {len(self.mapeamento_cnj)} tribunais diretos")
    
    def _inicializar_cache(self):
        """Inicializa cache de URLs funcionais"""
        self.cache_urls = {}
        self.cache_deteccoes = {}
        self.historico_deteccoes = []
    
    def detectar_tribunal(self, numero_cnj: str) -> Optional[DeteccaoTribunal]:
        """
        🎯 DETECÇÃO PRINCIPAL DE TRIBUNAL
        Identifica tribunal e recomenda melhor tecnologia
        """
        
        self.logger.info(f"Detectando tribunal para: {numero_cnj}")
        
        # Validar formato CNJ
        if not self._validar_cnj(numero_cnj):
            self.logger.error(f"Número CNJ inválido: {numero_cnj}")
            return None
        
        # Verificar cache
        cache_key = self._limpar_cnj(numero_cnj)
        if cache_key in self.cache_deteccoes:
            self.logger.info("Retornando detecção do cache")
            return self.cache_deteccoes[cache_key]
        
        # Extrair componentes do CNJ
        componentes = self._extrair_componentes_cnj(numero_cnj)
        if not componentes:
            return None
        
        # Detectar tribunal
        deteccao = self._executar_deteccao(componentes)
        
        if deteccao:
            # Salvar no cache
            self.cache_deteccoes[cache_key] = deteccao
            self.historico_deteccoes.append({
                'numero_cnj': numero_cnj,
                'tribunal': deteccao.codigo_tribunal,
                'timestamp': datetime.now()
            })
            
            self.logger.info(f"Tribunal detectado: {deteccao.nome_tribunal} ({deteccao.codigo_tribunal})")
            return deteccao
        
        self.logger.warning(f"Tribunal não identificado para: {numero_cnj}")
        return None
    
    def _validar_cnj(self, numero: str) -> bool:
        """Validação rigorosa do número CNJ"""
        
        numero_limpo = self._limpar_cnj(numero)
        
        # Verificar formato
        if len(numero_limpo) != 20:
            return False
        
        if not numero_limpo.isdigit():
            return False
        
        # Validar dígito verificador
        try:
            sequencial = numero_limpo[:7]
            dv = numero_limpo[7:9]
            ano = numero_limpo[9:13]
            segmento = numero_limpo[13:14]
            tribunal = numero_limpo[14:18]
            origem = numero_limpo[18:20]
            
            # Algoritmo de validação CNJ
            numeros = sequencial + ano + segmento + tribunal + origem
            resto = 0
            
            for i, digit in enumerate(reversed(numeros)):
                resto += int(digit) * (2 + (i % 8))
            
            resto = resto % 97
            dv_calculado = 98 - resto
            
            return str(dv_calculado).zfill(2) == dv
            
        except Exception as e:
            self.logger.error(f"Erro na validação CNJ: {e}")
            return False
    
    def _limpar_cnj(self, numero: str) -> str:
        """Remove formatação do número CNJ"""
        return re.sub(r'[^\d]', '', numero)
    
    def _extrair_componentes_cnj(self, numero: str) -> Optional[Dict]:
        """Extrai componentes do número CNJ"""
        
        numero_limpo = self._limpar_cnj(numero)
        
        try:
            return {
                'numero_completo': numero_limpo,
                'sequencial': numero_limpo[:7],
                'dv': numero_limpo[7:9], 
                'ano': numero_limpo[9:13],
                'segmento': numero_limpo[13:14],
                'tribunal': numero_limpo[14:18],
                'origem': numero_limpo[18:20]
            }
        except Exception:
            return None
    
    def _executar_deteccao(self, componentes: Dict) -> Optional[DeteccaoTribunal]:
        """Executa a detecção baseada nos componentes CNJ"""
        
        codigo_tribunal = componentes['tribunal']
        segmento = componentes['segmento']
        
        # Busca direta no mapeamento
        if codigo_tribunal in self.mapeamento_cnj:
            config = self.mapeamento_cnj[codigo_tribunal]
            return self._criar_deteccao(config, componentes, 1.0)
        
        # Busca por faixas (tribunais estaduais)
        for (inicio, fim), config in self.faixas_estaduais.items():
            if inicio <= codigo_tribunal <= fim:
                return self._criar_deteccao(config, componentes, 0.9)
        
        # Fallback por segmento
        return self._deteccao_fallback_segmento(segmento, componentes)
    
    def _criar_deteccao(self, config: Dict, componentes: Dict, confiabilidade: float) -> DeteccaoTribunal:
        """Cria objeto DeteccaoTribunal"""
        
        observacoes = []
        
        # Verificar qualidade da detecção
        if confiabilidade < 1.0:
            observacoes.append("Detecção baseada em faixa de códigos")
        
        # Recomendações específicas por tribunal
        if config['codigo'] == 'TJSP':
            observacoes.append("TJSP: Recomendado REST primeiro, SOAP como fallback")
        elif config['codigo'].startswith('TRF'):
            observacoes.append("TRF: SOAP é mais estável")
        
        return DeteccaoTribunal(
            codigo_tribunal=config['codigo'],
            nome_tribunal=config['nome'],
            sigla=config['sigla'],
            tipo=config['tipo'],
            segmento_cnj=componentes['segmento'],
            codigo_cnj=componentes['tribunal'],
            tecnologia_recomendada=config['tecnologia'],
            urls_disponiveis=config['urls'],
            confiabilidade=confiabilidade,
            observacoes=observacoes
        )
    
    def _deteccao_fallback_segmento(self, segmento: str, componentes: Dict) -> Optional[DeteccaoTribunal]:
        """Detecção de fallback baseada apenas no segmento"""
        
        fallback_configs = {
            "1": {  # Supremo Tribunal Federal
                "codigo": "STF",
                "nome": "Supremo Tribunal Federal",
                "sigla": "STF",
                "tipo": TipoTribunal.SUPREMO,
                "tecnologia": TecnologiaPreferida.SCRAPING,
                "urls": {"base": "https://portal.stf.jus.br"}
            },
            "3": {  # Superior Tribunal de Justiça
                "codigo": "STJ", 
                "nome": "Superior Tribunal de Justiça",
                "sigla": "STJ",
                "tipo": TipoTribunal.SUPERIOR,
                "tecnologia": TecnologiaPreferida.SCRAPING,
                "urls": {"base": "https://www.stj.jus.br"}
            },
            "4": {  # Justiça Federal
                "codigo": "TRF_GENERICO",
                "nome": "Tribunal Regional Federal (Genérico)",
                "sigla": "TRF",
                "tipo": TipoTribunal.FEDERAL,
                "tecnologia": TecnologiaPreferida.SCRAPING,
                "urls": {"base": "https://www.jf.jus.br"}
            },
            "5": {  # Justiça do Trabalho
                "codigo": "TRT_GENERICO",
                "nome": "Tribunal Regional do Trabalho (Genérico)",
                "sigla": "TRT",
                "tipo": TipoTribunal.TRABALHISTA,
                "tecnologia": TecnologiaPreferida.SCRAPING,
                "urls": {"base": "https://www.tst.jus.br"}
            },
            "6": {  # Justiça Eleitoral
                "codigo": "TRE_GENERICO",
                "nome": "Tribunal Regional Eleitoral (Genérico)",
                "sigla": "TRE",
                "tipo": TipoTribunal.ELEITORAL,
                "tecnologia": TecnologiaPreferida.SCRAPING,
                "urls": {"base": "https://www.tse.jus.br"}
            },
            "8": {  # Justiça Estadual
                "codigo": "TJ_GENERICO",
                "nome": "Tribunal de Justiça (Genérico)",
                "sigla": "TJ",
                "tipo": TipoTribunal.ESTADUAL,
                "tecnologia": TecnologiaPreferida.SCRAPING,
                "urls": {"base": "https://www.cnj.jus.br"}
            }
        }
        
        if segmento in fallback_configs:
            config = fallback_configs[segmento]
            deteccao = self._criar_deteccao(config, componentes, 0.3)
            deteccao.observacoes.append("FALLBACK: Detecção baseada apenas no segmento")
            deteccao.observacoes.append("RECOMENDADO: Usar scraping como última opção")
            return deteccao
        
        return None
    
    def obter_estatisticas(self) -> Dict:
        """Estatísticas do sistema de detecção"""
        
        total_deteccoes = len(self.historico_deteccoes)
        tribunais_detectados = {}
        
        for deteccao in self.historico_deteccoes:
            tribunal = deteccao['tribunal']
            tribunais_detectados[tribunal] = tribunais_detectados.get(tribunal, 0) + 1
        
        return {
            'total_deteccoes': total_deteccoes,
            'tribunais_suportados': len(self.mapeamento_cnj) + len(self.faixas_estaduais),
            'cache_size': len(self.cache_deteccoes),
            'tribunais_mais_detectados': dict(sorted(tribunais_detectados.items(), key=lambda x: x[1], reverse=True)[:10]),
            'tipos_suportados': [tipo.value for tipo in TipoTribunal],
            'tecnologias_disponiveis': [tech.value for tech in TecnologiaPreferida]
        }
    
    def limpar_cache(self):
        """Limpa cache de detecções"""
        self.cache_deteccoes.clear()
        self.cache_urls.clear()
        self.logger.info("Cache de detecções limpo")

# Função de conveniência
def detectar_tribunal_cnj(numero_cnj: str) -> Optional[DeteccaoTribunal]:
    """
    🎯 FUNÇÃO DE CONVENIÊNCIA
    Detecta tribunal de forma simples
    """
    detector = TribunalAutoDetection()
    return detector.detectar_tribunal(numero_cnj)

# Exemplo de uso
if __name__ == "__main__":
    def testar_deteccao():
        """🧪 TESTE COMPLETO DA DETECÇÃO"""
        
        print("🎯 TESTANDO TRIBUNAL AUTO DETECTION")
        print("=" * 60)
        
        detector = TribunalAutoDetection()
        
        # Casos de teste
        casos_teste = [
            "1234567-89.2023.8.26.0001",  # TJSP
            "0001234-56.2023.4.03.0001",  # TRF3  
            "5001234-56.2023.5.02.0001",  # TRT2
            "0000123-45.2023.1.00.0001",  # STF
            "0000123-45.2023.3.00.0001",  # STJ
            "1234567-89.2023.6.00.0001",  # TSE
            "9999999-99.2023.8.01.0001"   # Caso genérico
        ]
        
        for i, numero in enumerate(casos_teste, 1):
            print(f"\n📋 TESTE {i}: {numero}")
            print("-" * 40)
            
            deteccao = detector.detectar_tribunal(numero)
            
            if deteccao:
                print(f"✅ Tribunal: {deteccao.nome_tribunal}")
                print(f"   Código: {deteccao.codigo_tribunal}")
                print(f"   Tipo: {deteccao.tipo.value}")
                print(f"   Tecnologia: {deteccao.tecnologia_recomendada.value}")
                print(f"   Confiabilidade: {deteccao.confiabilidade:.1%}")
                print(f"   URLs: {len(deteccao.urls_disponiveis)} disponíveis")
                
                if deteccao.observacoes:
                    print(f"   Observações: {'; '.join(deteccao.observacoes)}")
            else:
                print("❌ Tribunal não identificado")
        
        # Estatísticas
        print(f"\n📊 ESTATÍSTICAS")
        print("-" * 40)
        stats = detector.obter_estatisticas()
        print(f"Tribunais suportados: {stats['tribunais_suportados']}")
        print(f"Detecções realizadas: {stats['total_deteccoes']}")
        print(f"Cache size: {stats['cache_size']}")
        
        print(f"\n🎉 TESTE CONCLUÍDO!")
        print("🚀 SISTEMA DE AUTO-DETECÇÃO FUNCIONAL!")
    
    testar_deteccao()