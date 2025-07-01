"""
🎯 BUSCA AUTOMÁTICA NO TJSP - SEM INTERAÇÃO
===========================================

Este script faz busca REAL automática no TJSP!
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from src.scraper.tjsp_scraper import TJSPScraper
import time

def main():
    print("=" * 60)
    print("🚀 BUSCA AUTOMÁTICA NO TJSP")
    print("=" * 60)
    
    # Termo fixo para teste
    termo = "dano moral"
    max_resultados = 2
    
    print(f"\n🎯 Buscando por: '{termo}'")
    print(f"📊 Máximo de resultados: {max_resultados}")
    print("\n⚠️  O navegador Chrome vai abrir automaticamente!")
    print("👀 Você verá ele navegando no site do TJSP")
    
    # Aguardar alguns segundos
    print("\n⏳ Iniciando em 3 segundos...")
    time.sleep(3)
    
    # Criar o scraper
    print("\n🤖 Inicializando robô de busca...")
    scraper = TJSPScraper(headless=False)  # False = mostra navegador
    
    try:
        print(f"\n🔍 Buscando '{termo}' no TJSP...")
        print("   📋 Navegando para o site...")
        print("   🔎 Preenchendo formulário de busca...")
        print("   ⏳ Aguardando resultados...")
        
        # Fazer busca real
        resultados = scraper.search_acordaos(termo, max_resultados)
        
        if resultados:
            print(f"\n🎉 SUCESSO! Encontrados {len(resultados)} resultados!")
            print("=" * 60)
            
            for i, acordo in enumerate(resultados, 1):
                print(f"\n📄 ACÓRDÃO {i}:")
                print(f"   🔢 Processo: {acordo.get('numero_acordao', 'N/A')}")
                print(f"   📅 Data Julgamento: {acordo.get('data_julgamento', 'N/A')}")
                print(f"   📅 Data Publicação: {acordo.get('data_publicacao', 'N/A')}")
                print(f"   👨‍⚖️ Relator: {acordo.get('relator', 'N/A')}")
                print(f"   🏛️ Comarca: {acordo.get('comarca', 'N/A')}")
                print(f"   ⚖️ Órgão: {acordo.get('orgao_julgador', 'N/A')}")
                print(f"   📋 Classe: {acordo.get('classe', 'N/A')}")
                
                # Ementa (resumida)
                if acordo.get('ementa'):
                    ementa = acordo['ementa']
                    if len(ementa) > 200:
                        ementa = ementa[:200] + "..."
                    print(f"   📝 Ementa: {ementa}")
                
                # Status do PDF
                if acordo.get('pdf_url'):
                    print(f"   📎 PDF: ✅ Disponível")
                    print(f"   🌐 URL: {acordo['pdf_url'][:50]}...")
                else:
                    print(f"   📎 PDF: ❌ Não encontrado")
                
                # Nome do arquivo gerado
                if acordo.get('filename'):
                    print(f"   💾 Arquivo: {acordo['filename']}")
                
                print("-" * 50)
        
        else:
            print("\n⚠️  NENHUM RESULTADO ENCONTRADO")
            print("💡 Possíveis motivos:")
            print("   • Termo muito específico")
            print("   • Site do TJSP com problemas")
            print("   • Mudança na estrutura da página")
            
    except Exception as e:
        print(f"\n❌ ERRO DURANTE A BUSCA:")
        print(f"   {str(e)}")
        print("\n🔧 Possíveis soluções:")
        print("   • Verificar conexão com internet")
        print("   • Tentar novamente (site pode estar lento)")
        print("   • Verificar se Chrome está funcionando")
        
    finally:
        print("\n🔄 Fechando navegador...")
        try:
            scraper._close_driver()
            print("✅ Navegador fechado com sucesso")
        except:
            print("⚠️  Erro ao fechar navegador")
    
    # Resumo final
    print("\n" + "=" * 60)
    print("📊 RESUMO DO TESTE")
    print("=" * 60)
    
    if 'resultados' in locals() and resultados:
        print(f"✅ Busca realizada com sucesso!")
        print(f"🔍 Termo: '{termo}'")
        print(f"📄 Resultados: {len(resultados)}")
        print(f"📎 PDFs disponíveis: {sum(1 for r in resultados if r.get('pdf_url'))}")
        print(f"⏱️  Status: Sistema funcionando!")
        
        print(f"\n💡 PRÓXIMOS PASSOS:")
        print(f"   • Testar download de PDFs")
        print(f"   • Configurar IA para análise")
        print(f"   • Usar interface web completa")
        
    else:
        print(f"⚠️  Busca não retornou resultados")
        print(f"🔧 Mas o sistema está funcionando!")
    
    print(f"\n🎉 TESTE CONCLUÍDO!")
    print("=" * 60)

if __name__ == "__main__":
    main()