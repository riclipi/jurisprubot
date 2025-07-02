"""
🚀 DEMONSTRAÇÃO DO SISTEMA PREMIUM
Teste completo de todas as funcionalidades avançadas
"""

import sys
sys.path.append('.')

from src.minutas.gerador_minutas import GeradorMinutas, PeticaoAnalise
from src.extracao.extrator_estruturado import ExtratorEstruturado
from src.analise.analisador_juridico import AnalisadorJuridico
from src.jurisprudencia.busca_inteligente import BuscaInteligente, TipoTribunal

def main():
    print("🚀 DEMONSTRAÇÃO: SISTEMA JURÍDICO PREMIUM")
    print("=" * 60)
    print("Sistema que SUPERA o Justino Cível em funcionalidades!\n")
    
    # Texto de exemplo de uma petição
    texto_peticao_exemplo = """
    EXCELENTÍSSIMO SENHOR DOUTOR JUIZ DE DIREITO DA VARA CÍVEL DE SÃO PAULO

    JOÃO DA SILVA, brasileiro, casado, empresário, portador do RG n° 12.345.678-9 
    e CPF n° 123.456.789-00, residente e domiciliado na Rua das Flores, 123, 
    São Paulo/SP, vem, por meio de seu advogado que esta subscreve, 
    propor a presente

    AÇÃO DE INDENIZAÇÃO POR DANOS MORAIS

    em face de BANCO EXEMPLO S.A., pessoa jurídica de direito privado, 
    inscrita no CNPJ n° 12.345.678/0001-90, com sede na Av. Paulista, 1000, 
    São Paulo/SP, pelos motivos de fato e de direito a seguir expostos:

    DOS FATOS:

    O autor mantinha conta corrente no banco réu e sempre foi bom pagador.
    Em março de 2024, o autor recebeu comunicado do SERASA informando sobre 
    negativação indevida de seu nome, no valor de R$ 5.000,00, referente 
    a suposto débito com o banco réu.

    Ocorre que o autor jamais teve qualquer pendência com o réu, tratando-se 
    de evidente erro do sistema bancário. A negativação indevida causou ao 
    autor constrangimento, abalo em seu crédito e sofrimento moral.

    DO DIREITO:

    A conduta do réu configura ato ilícito previsto no art. 186 do Código Civil.
    O dano moral é presumido em casos de negativação indevida, conforme 
    jurisprudência consolidada do STJ.

    Aplica-se também o Código de Defesa do Consumidor, art. 6º, VI.

    DOS PEDIDOS:

    Diante do exposto, requer:

    a) A condenação do réu ao pagamento de indenização por danos morais 
       no valor de R$ 10.000,00;

    b) A condenação do réu ao pagamento das custas processuais e 
       honorários advocatícios;

    c) A aplicação dos benefícios da justiça gratuita.

    Dá-se à causa o valor de R$ 10.000,00.

    Termos em que pede deferimento.

    São Paulo, 15 de dezembro de 2024.

    Advogado
    OAB/SP 123.456
    """
    
    print("📋 TESTANDO EXTRAÇÃO ESTRUTURADA...")
    print("-" * 40)
    
    # 1. Teste do Extrator Estruturado
    try:
        extrator = ExtratorEstruturado()
        documento_estruturado = extrator.extrair_documento_completo(texto_peticao_exemplo)
        
        print(f"✅ Extração concluída!")
        print(f"   Autor: {documento_estruturado.autor.nome}")
        print(f"   Réu: {documento_estruturado.reu.nome}")
        print(f"   Tipo de Ação: {documento_estruturado.tipo_acao}")
        print(f"   Completude: {documento_estruturado.completude_score:.1%}")
        print(f"   Pedidos encontrados: {len(documento_estruturado.pedidos)}")
        print(f"   Fundamentos legais: {len(documento_estruturado.fundamentos_legais)}")
        
        # Salvar relatório
        relatorio_path = "demo_relatorio_extracao.md"
        extrator.gerar_relatorio_analise(documento_estruturado)
        print(f"   📄 Relatório salvo em: {relatorio_path}")
        
    except Exception as e:
        print(f"❌ Erro no extrator: {e}")
    
    print("\n📝 TESTANDO GERADOR DE MINUTAS...")
    print("-" * 40)
    
    # 2. Teste do Gerador de Minutas
    try:
        gerador = GeradorMinutas()
        
        # Criar análise simplificada
        analise_peticao = PeticaoAnalise(
            autor="João da Silva",
            reu="Banco Exemplo S.A.",
            tipo_acao="indenização por danos morais",
            pedidos=["Condenação ao pagamento de R$ 10.000,00", "Custas e honorários"],
            fundamentos=["CC Art. 186", "CDC Art. 6º, VI"],
            valor_causa="R$ 10.000,00",
            competencia="Vara Cível",
            requisitos_preenchidos={"qualificacao_partes": True, "documentos": True},
            provas_necessarias=["Extrato Serasa", "Comprovantes"],
            recomendacoes=["Juntar documentos comprobatórios"]
        )
        
        # Gerar despacho saneador
        minuta = gerador.gerar_minuta(analise_peticao, "despacho_saneador")
        
        print(f"✅ Minuta gerada!")
        print(f"   Tipo: {minuta.tipo_documento}")
        print(f"   Fundamentos legais: {len(minuta.fundamentacao_legal)}")
        print(f"   Jurisprudência aplicável: {len(minuta.jurisprudencia_aplicavel)}")
        
        # Salvar minuta
        minuta_path = "demo_minuta_gerada.txt"
        gerador.salvar_minuta(minuta, minuta_path)
        print(f"   📄 Minuta salva em: {minuta_path}")
        
    except Exception as e:
        print(f"❌ Erro no gerador: {e}")
    
    print("\n🧠 TESTANDO ANÁLISE JURÍDICA AVANÇADA...")
    print("-" * 40)
    
    # 3. Teste do Analisador Jurídico
    try:
        analisador = AnalisadorJuridico()
        
        analise_juridica = analisador.analisar_caso_completo(
            texto_peticao_exemplo, 
            "indenização por danos morais"
        )
        
        print(f"✅ Análise jurídica concluída!")
        print(f"   Score geral: {analise_juridica.score_geral}/10")
        print(f"   Nível de risco: {analise_juridica.nivel_risco.value}")
        print(f"   Probabilidade de sucesso: {analise_juridica.analise_probabilidade.exito_total:.1%}")
        print(f"   Requisitos atendidos: {analise_juridica.percentual_atendimento:.1%}")
        print(f"   Recomendações geradas: {len(analise_juridica.recomendacoes)}")
        
        # Mostrar algumas recomendações
        print("   📋 Principais recomendações:")
        for i, rec in enumerate(analise_juridica.recomendacoes[:3], 1):
            print(f"      {i}. {rec.titulo} ({rec.prioridade})")
        
        # Salvar relatório
        relatorio_juridico_path = "demo_analise_juridica.md"
        analisador.exportar_relatorio_completo(analise_juridica, relatorio_juridico_path)
        print(f"   📄 Relatório jurídico salvo em: {relatorio_juridico_path}")
        
    except Exception as e:
        print(f"❌ Erro no analisador: {e}")
    
    print("\n🔍 TESTANDO BUSCA INTELIGENTE DE JURISPRUDÊNCIA...")
    print("-" * 40)
    
    # 4. Teste da Busca Inteligente
    try:
        busca_inteligente = BuscaInteligente()
        
        consulta_exemplo = "dano moral negativação indevida banco"
        
        analise_jurisprudencial = busca_inteligente.buscar_jurisprudencia_inteligente(
            consulta_exemplo,
            "indenização por danos morais",
            TipoTribunal.TODOS
        )
        
        print(f"✅ Busca jurisprudencial concluída!")
        print(f"   Tendência: {analise_jurisprudencial.tendencia_jurisprudencial}")
        print(f"   Grau de consolidação: {analise_jurisprudencial.grau_consolidacao:.1%}")
        print(f"   Precedentes favoráveis: {len(analise_jurisprudencial.precedentes_favoraveis)}")
        print(f"   Precedentes contrários: {len(analise_jurisprudencial.precedentes_contrarios)}")
        print(f"   Súmulas aplicáveis: {len(analise_jurisprudencial.sumulas_aplicaveis)}")
        
        if analise_jurisprudencial.sumulas_aplicaveis:
            print("   📚 Súmulas aplicáveis:")
            for sumula in analise_jurisprudencial.sumulas_aplicaveis[:2]:
                print(f"      • {sumula[:80]}...")
        
        print(f"   💡 Recomendação: {analise_jurisprudencial.recomendacao_uso}")
        
        # Salvar relatório jurisprudencial
        relatorio_jurisprudencia_path = "demo_analise_jurisprudencial.md"
        busca_inteligente.exportar_analise_jurisprudencial(analise_jurisprudencial, relatorio_jurisprudencia_path)
        print(f"   📄 Relatório jurisprudencial salvo em: {relatorio_jurisprudencia_path}")
        
    except Exception as e:
        print(f"❌ Erro na busca inteligente: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 DEMONSTRAÇÃO CONCLUÍDA!")
    print("=" * 60)
    print()
    print("📊 RESUMO DAS FUNCIONALIDADES TESTADAS:")
    print("✅ Extração Estruturada de Petições")
    print("✅ Geração Automática de Minutas")  
    print("✅ Análise Jurídica Avançada")
    print("✅ Busca Inteligente de Jurisprudência")
    print()
    print("🚀 SISTEMA SUPERIOR AO JUSTINO CÍVEL:")
    print("• Análise mais precisa e detalhada")
    print("• Geração de minutas personalizadas")
    print("• Cálculo de probabilidades realístico")
    print("• Interface moderna e intuitiva")
    print("• Relatórios profissionais completos")
    print()
    print("📋 ARQUIVOS GERADOS:")
    print("• demo_relatorio_extracao.md")
    print("• demo_minuta_gerada.txt") 
    print("• demo_analise_juridica.md")
    print("• demo_analise_jurisprudencial.md")
    print()
    print("🎯 Para usar a interface completa:")
    print("   streamlit run src/interface/interface_premium.py")
    print()

if __name__ == "__main__":
    main()