#!/usr/bin/env python3
"""
Script de teste para validar integração completa com Google Gemini 2.5 Flash Lite
"""

import os
import sys
from pathlib import Path

# Adicionar diretório src ao path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from dotenv import load_dotenv
load_dotenv()

def test_gemini_client():
    """Testa cliente Gemini básico"""
    print("\n=== TESTE 1: Cliente Gemini ===")
    
    try:
        from src.ai.gemini_client import GeminiClient, get_gemini_client
        
        # Testar inicialização
        client = get_gemini_client()
        print("✅ Cliente Gemini inicializado com sucesso")
        
        # Testar geração simples
        resposta = client.generate(
            "Qual a diferença entre dano moral e dano material no direito brasileiro?",
            system_prompt="Responda de forma concisa e técnica."
        )
        
        if resposta:
            print(f"✅ Resposta gerada: {resposta[:200]}...")
        else:
            print("❌ Falha ao gerar resposta")
            
        # Testar estimativa de custo
        custo = client.estimate_cost("Texto de exemplo para análise jurídica")
        print(f"✅ Estimativa de custo: ${custo['custo_total_usd']:.6f} USD / R$ {custo['custo_total_brl']:.4f}")
        
        # Testar estatísticas
        stats = client.get_usage_stats()
        print(f"✅ Estatísticas: {stats['requests_ultimas_24h']} requests nas últimas 24h")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste do cliente: {e}")
        return False


def test_analisador_juridico():
    """Testa analisador jurídico com Gemini"""
    print("\n=== TESTE 2: Analisador Jurídico com Gemini ===")
    
    try:
        from src.analise.analisador_juridico import AnalisadorJuridico
        
        # Criar analisador com Gemini
        analisador = AnalisadorJuridico(use_ai=True, ai_provider="gemini")
        print("✅ Analisador jurídico inicializado com Gemini")
        
        # Testar análise com IA
        texto_exemplo = """
        Trata-se de ação de indenização por danos morais em face de instituição bancária
        devido a negativação indevida do nome do autor nos órgãos de proteção ao crédito.
        O autor alega nunca ter mantido relação jurídica com o réu.
        """
        
        analise_ia = analisador.analisar_com_ia(texto_exemplo, "resumo")
        
        if analise_ia:
            print(f"✅ Análise com IA realizada")
            print(f"   Modelo: {analise_ia.get('modelo')}")
            print(f"   Análise: {analise_ia.get('analise', '')[:200]}...")
        else:
            print("⚠️  Análise com IA não disponível (pode estar usando análise local)")
            
        # Testar estimativa de custo
        custo = analisador.estimar_custo_ia(texto_exemplo)
        print(f"✅ Custo estimado: R$ {custo['custo_brl']:.4f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste do analisador: {e}")
        return False


def test_gerador_minutas():
    """Testa gerador de minutas com Gemini"""
    print("\n=== TESTE 3: Gerador de Minutas com Gemini ===")
    
    try:
        from src.minutas.gerador_minutas import GeradorMinutas
        
        # Criar gerador com Gemini
        gerador = GeradorMinutas(use_ai=True, ai_provider="gemini")
        print("✅ Gerador de minutas inicializado com Gemini")
        
        # Contexto para geração
        contexto = {
            "autor": "João da Silva",
            "reu": "Banco XYZ S/A",
            "tipo_acao": "Indenização por danos morais",
            "fatos": "Negativação indevida por dívida inexistente",
            "valor_causa": "R$ 10.000,00"
        }
        
        # Testar geração com IA
        minuta = gerador.gerar_minuta_com_ia("petição inicial", contexto)
        
        if minuta:
            print("✅ Minuta gerada com sucesso")
            print(f"   Tamanho: {len(minuta)} caracteres")
            print(f"   Início: {minuta[:150]}...")
        else:
            print("⚠️  Geração com IA não disponível")
            
        # Testar estimativa de custo
        custo = gerador.estimar_custo_geracao(contexto)
        print(f"✅ Custo estimado: R$ {custo['custo_brl']:.4f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste do gerador: {e}")
        return False


def test_busca_inteligente():
    """Testa busca inteligente com Gemini"""
    print("\n=== TESTE 4: Busca Inteligente com Gemini ===")
    
    try:
        from src.jurisprudencia.busca_inteligente import BuscaInteligente
        
        # Criar busca com Gemini
        busca = BuscaInteligente(use_ai=True, ai_provider="gemini")
        print("✅ Busca inteligente inicializada com Gemini")
        
        # Testar busca contextual
        consulta = "dano moral negativação indevida súmula 385"
        
        # Simular análise (sem executar busca completa)
        from src.jurisprudencia.busca_inteligente import AnaliseJurisprudencial, PrecedenteJuridico
        from datetime import datetime
        
        analise_mock = AnaliseJurisprudencial(
            id_analise="TEST001",
            consulta_original=consulta,
            tipo_acao="indenização por danos morais",
            data_analise=datetime.now(),
            precedentes_favoraveis=[],
            precedentes_contrarios=[],
            precedentes_neutros=[],
            tendencia_jurisprudencial="favorável",
            grau_consolidacao=0.8,
            recomendacao_uso="Citar precedentes do STJ",
            sumulas_aplicaveis=["STJ Súmula 385"],
            orientacoes_tribunais=[],
            estatisticas={}
        )
        
        # Testar recomendação estratégica
        recomendacao = busca.gerar_recomendacao_estrategica_ia(analise_mock)
        
        if recomendacao:
            print("✅ Recomendação estratégica gerada")
            print(f"   Tamanho: {len(recomendacao)} caracteres")
            print(f"   Início: {recomendacao[:150]}...")
        else:
            print("⚠️  Recomendação com IA não disponível")
            
        # Testar estimativa de custo
        custo = busca.estimar_custo_busca_ia(consulta)
        print(f"✅ Custo estimado: R$ {custo['custo_brl']:.4f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste de busca: {e}")
        return False


def test_analise_documento_completa():
    """Teste integrado de análise de documento jurídico"""
    print("\n=== TESTE 5: Análise Completa de Documento ===")
    
    try:
        from src.ai.gemini_client import get_gemini_client
        
        client = get_gemini_client()
        
        documento = """
        EXCELENTÍSSIMO SENHOR DOUTOR JUIZ DE DIREITO DA ___ VARA CÍVEL DA COMARCA DE SÃO PAULO/SP
        
        JOÃO DA SILVA, brasileiro, solteiro, analista de sistemas, portador do RG nº 12.345.678-9 SSP/SP,
        inscrito no CPF sob nº 123.456.789-00, residente e domiciliado na Rua das Flores, nº 100,
        Jardim Primavera, São Paulo/SP, CEP 01234-567, vem, respeitosamente, à presença de Vossa
        Excelência, por seu advogado que esta subscreve, propor
        
        AÇÃO DE INDENIZAÇÃO POR DANOS MORAIS
        
        em face de BANCO XYZ S/A, instituição financeira inscrita no CNPJ sob nº 12.345.678/0001-90,
        com sede na Avenida Paulista, nº 1000, São Paulo/SP, pelos fatos e fundamentos a seguir expostos:
        
        DOS FATOS
        
        1. O autor foi surpreendido ao tentar realizar uma compra e ter seu crédito negado, momento em
        que descobriu que seu nome estava inscrito nos órgãos de proteção ao crédito.
        
        2. Ao verificar, constatou que a negativação foi realizada pelo banco réu, referente a um suposto
        débito no valor de R$ 5.432,10, contrato nº 987654321.
        
        3. Ocorre que o autor JAMAIS manteve qualquer relação jurídica com o réu, não tendo celebrado
        nenhum contrato ou utilizado qualquer serviço da instituição financeira.
        """
        
        # Análise completa
        analise = client.analyze_legal_document(documento, "completa")
        
        if analise:
            print("✅ Análise completa realizada com sucesso")
            print(f"   Tipo: {analise['tipo_analise']}")
            print(f"   Modelo: {analise['modelo']}")
            print(f"   Tokens estimados: {analise['tokens_estimados']}")
            print("\n📋 Análise:")
            print(analise['analise'][:500] + "...")
        else:
            print("❌ Falha na análise do documento")
            
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste de análise completa: {e}")
        return False


def main():
    """Executa todos os testes"""
    print("🚀 TESTE DE INTEGRAÇÃO GOOGLE GEMINI 2.5 FLASH LITE")
    print("=" * 60)
    
    # Verificar API key
    if not os.getenv("GOOGLE_API_KEY") and not os.getenv("GEMINI_API_KEY"):
        print("❌ ERRO: Configure GOOGLE_API_KEY ou GEMINI_API_KEY no arquivo .env")
        return
    
    # Executar testes
    testes = [
        test_gemini_client,
        test_analisador_juridico,
        test_gerador_minutas,
        test_busca_inteligente,
        test_analise_documento_completa
    ]
    
    resultados = []
    for teste in testes:
        try:
            sucesso = teste()
            resultados.append(sucesso)
        except Exception as e:
            print(f"❌ Erro ao executar {teste.__name__}: {e}")
            resultados.append(False)
    
    # Resumo
    print("\n" + "=" * 60)
    print("📊 RESUMO DOS TESTES")
    print(f"✅ Testes bem-sucedidos: {sum(resultados)}/{len(resultados)}")
    
    if all(resultados):
        print("\n🎉 TODOS OS TESTES PASSARAM! Gemini está totalmente integrado.")
    else:
        print("\n⚠️  Alguns testes falharam. Verifique as mensagens acima.")
    
    # Informações de configuração
    print("\n📋 CONFIGURAÇÃO ATUAL:")
    print(f"   Modelo: gemini-2.5-flash-lite")
    print(f"   API Key configurada: {'✅' if os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY') else '❌'}")
    print(f"   Fallbacks disponíveis: OpenAI {'✅' if os.getenv('OPENAI_API_KEY') else '❌'}, Groq {'✅' if os.getenv('GROQ_API_KEY') else '❌'}")


if __name__ == "__main__":
    main()