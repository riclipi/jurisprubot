"""
⚖️ VALIDADOR DE NÚMEROS CNJ
Implementação correta do algoritmo oficial de validação CNJ
Formato: NNNNNNN-DD.AAAA.J.TR.OOOO
"""

import re
from typing import Optional, Tuple, Dict


class CNJValidator:
    """
    Validador de números CNJ seguindo o padrão oficial do CNJ
    Implementa o algoritmo de módulo 97 conforme especificação
    """
    
    # Regex para capturar partes do número CNJ
    CNJ_PATTERN = re.compile(
        r'^(\d{7})-(\d{2})\.(\d{4})\.(\d)\.(\d{2})\.(\d{4})$'
    )
    
    # Mapeamento de segmentos do Judiciário
    SEGMENTOS = {
        '1': 'Supremo Tribunal Federal',
        '2': 'Conselho Nacional de Justiça',
        '3': 'Superior Tribunal de Justiça',
        '4': 'Justiça Federal',
        '5': 'Justiça do Trabalho',
        '6': 'Justiça Eleitoral',
        '7': 'Justiça Militar da União',
        '8': 'Justiça dos Estados e do Distrito Federal e Territórios',
        '9': 'Justiça Militar Estadual'
    }
    
    @staticmethod
    def validar(numero_cnj: str) -> bool:
        """
        Valida um número CNJ completo
        
        Args:
            numero_cnj: Número no formato NNNNNNN-DD.AAAA.J.TR.OOOO
            
        Returns:
            True se válido, False caso contrário
        """
        try:
            # Remover espaços em branco
            numero_cnj = numero_cnj.strip()
            
            # Verificar formato
            match = CNJValidator.CNJ_PATTERN.match(numero_cnj)
            if not match:
                return False
            
            # Extrair componentes
            sequencial, dv, ano, segmento, tribunal, origem = match.groups()
            
            # Calcular dígito verificador esperado
            dv_calculado = CNJValidator._calcular_dv(
                sequencial, ano, segmento, tribunal, origem
            )
            
            # Comparar com dígito verificador informado
            return dv == dv_calculado
            
        except Exception:
            return False
    
    @staticmethod
    def _calcular_dv(sequencial: str, ano: str, segmento: str, 
                     tribunal: str, origem: str) -> str:
        """
        Calcula o dígito verificador usando módulo 97
        
        Algoritmo oficial CNJ:
        1. Concatenar: origem + ano + segmento + tribunal + sequencial
        2. Calcular: 98 - (número % 97)
        3. Formatar com 2 dígitos
        """
        # Concatenar na ordem correta (conforme especificação CNJ)
        numero = origem + ano + segmento + tribunal + sequencial
        
        # Converter para inteiro
        numero_int = int(numero)
        
        # Calcular módulo 97
        resto = numero_int % 97
        
        # Calcular DV
        dv = 98 - resto
        
        # Formatar com 2 dígitos
        return f"{dv:02d}"
    
    @staticmethod
    def extrair_componentes(numero_cnj: str) -> Optional[Dict[str, str]]:
        """
        Extrai todos os componentes de um número CNJ
        
        Args:
            numero_cnj: Número CNJ completo
            
        Returns:
            Dicionário com componentes ou None se inválido
        """
        # Remover espaços
        numero_cnj = numero_cnj.strip()
        
        # Verificar formato
        match = CNJValidator.CNJ_PATTERN.match(numero_cnj)
        if not match:
            return None
        
        sequencial, dv, ano, segmento, tribunal, origem = match.groups()
        
        # Validar número completo
        if not CNJValidator.validar(numero_cnj):
            return None
        
        # Retornar componentes
        return {
            'numero_completo': numero_cnj,
            'sequencial': sequencial,
            'digito_verificador': dv,
            'ano': ano,
            'segmento': segmento,
            'segmento_nome': CNJValidator.SEGMENTOS.get(segmento, 'Desconhecido'),
            'tribunal': tribunal,
            'origem': origem,
            'codigo_tribunal': f"{segmento}.{tribunal}",
            'valido': True
        }
    
    @staticmethod
    def formatar(numero_cnj: str) -> Optional[str]:
        """
        Formata um número CNJ removendo caracteres extras
        
        Args:
            numero_cnj: Número CNJ em qualquer formato
            
        Returns:
            Número formatado ou None se inválido
        """
        # Remover tudo exceto números
        apenas_numeros = re.sub(r'\D', '', numero_cnj)
        
        # Verificar se tem 20 dígitos
        if len(apenas_numeros) != 20:
            return None
        
        # Formatar
        formatado = (
            f"{apenas_numeros[0:7]}-"
            f"{apenas_numeros[7:9]}."
            f"{apenas_numeros[9:13]}."
            f"{apenas_numeros[13]}."
            f"{apenas_numeros[14:16]}."
            f"{apenas_numeros[16:20]}"
        )
        
        # Validar antes de retornar
        if CNJValidator.validar(formatado):
            return formatado
        
        return None
    
    @staticmethod
    def gerar_numero_valido(sequencial: int, ano: int, segmento: int,
                           tribunal: int, origem: int) -> str:
        """
        Gera um número CNJ válido com dígito verificador correto
        
        Args:
            sequencial: Número sequencial (0-9999999)
            ano: Ano (0-9999)
            segmento: Segmento do Judiciário (1-9)
            tribunal: Código do tribunal (0-99)
            origem: Código da unidade de origem (0-9999)
            
        Returns:
            Número CNJ completo e válido
        """
        # Formatar componentes
        seq_str = f"{sequencial:07d}"
        ano_str = f"{ano:04d}"
        seg_str = str(segmento)
        trib_str = f"{tribunal:02d}"
        orig_str = f"{origem:04d}"
        
        # Calcular DV
        dv = CNJValidator._calcular_dv(seq_str, ano_str, seg_str, trib_str, orig_str)
        
        # Montar número completo
        return f"{seq_str}-{dv}.{ano_str}.{seg_str}.{trib_str}.{orig_str}"
    
    @staticmethod
    def identificar_tribunal(numero_cnj: str) -> Optional[Tuple[str, str]]:
        """
        Identifica o tribunal a partir do número CNJ
        
        Args:
            numero_cnj: Número CNJ
            
        Returns:
            Tupla (código_tribunal, nome_segmento) ou None
        """
        componentes = CNJValidator.extrair_componentes(numero_cnj)
        if not componentes:
            return None
        
        return (componentes['codigo_tribunal'], componentes['segmento_nome'])


# Funções auxiliares para uso direto
def validar_numero_cnj(numero: str) -> bool:
    """Valida um número CNJ"""
    return CNJValidator.validar(numero)


def extrair_componentes_cnj(numero: str) -> Optional[Dict[str, str]]:
    """Extrai componentes de um número CNJ"""
    return CNJValidator.extrair_componentes(numero)


def formatar_numero_cnj(numero: str) -> Optional[str]:
    """Formata um número CNJ"""
    return CNJValidator.formatar(numero)


def identificar_tribunal_cnj(numero: str) -> Optional[Tuple[str, str]]:
    """Identifica o tribunal de um número CNJ"""
    return CNJValidator.identificar_tribunal(numero)


# Testes e exemplos
if __name__ == "__main__":
    # Números de teste
    numeros_teste = [
        "1234567-89.2023.8.26.0001",  # Inválido (DV incorreto)
        "0002907-45.2023.8.26.0001",  # Válido TJSP
        "0000001-02.2023.1.00.0000",  # STF
        "0000001-02.2023.3.00.0000",  # STJ
        "1000001-02.2023.4.03.0000",  # TRF3
        "5000001-02.2023.5.02.0000",  # TRT2
    ]
    
    print("🧪 TESTANDO VALIDADOR CNJ")
    print("=" * 50)
    
    for numero in numeros_teste:
        valido = validar_numero_cnj(numero)
        print(f"\n📋 Número: {numero}")
        print(f"✅ Válido: {valido}")
        
        if valido:
            componentes = extrair_componentes_cnj(numero)
            if componentes:
                print(f"📊 Componentes:")
                print(f"   • Ano: {componentes['ano']}")
                print(f"   • Segmento: {componentes['segmento_nome']}")
                print(f"   • Tribunal: {componentes['codigo_tribunal']}")
                print(f"   • Origem: {componentes['origem']}")
    
    # Teste de geração
    print("\n🔧 GERANDO NÚMERO VÁLIDO:")
    numero_gerado = CNJValidator.gerar_numero_valido(
        sequencial=1,
        ano=2025,
        segmento=8,
        tribunal=26,
        origem=1
    )
    print(f"Gerado: {numero_gerado}")
    print(f"Válido: {validar_numero_cnj(numero_gerado)}")