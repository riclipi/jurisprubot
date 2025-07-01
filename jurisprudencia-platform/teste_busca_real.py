"""
🎯 TESTE DE BUSCA REAL NO TJSP
=============================

Este script vai fazer uma busca REAL no site do TJSP!
Você vai ver o navegador em ação.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from src.scraper.tjsp_scraper import TJSPScraper
import time

def main():
    print("=" * 60)
    print("🚀 BUSCA REAL NO SITE DO TJSP")
    print("=" * 60)
    
    print("\n⚠️  IMPORTANTE:")
    print("   • O navegador Chrome vai abrir")
    print("   • Você vai ver ele navegando automaticamente")
    print("   • Pode demorar alguns minutos")
    print("   • NÃO feche o navegador manualmente")
    
    # Perguntar o termo de busca
    print("\n🔍 TERMOS SUGERIDOS:")
    print("   1. dano moral")
    print("   2. negativação indevida") 
    print("   3. consumidor")
    print("   4. contrato")
    print("   5. indenização")
    
    termo = input("\n   Digite o termo para buscar (ou escolha 1-5): ").strip()
    
    # Converter número para termo
    termos = {
        "1": "dano moral",
        "2": "negativação indevida", 
        "3": "consumidor",
        "4": "contrato",
        "5": "indenização"
    }
    
    if termo in termos:
        termo = termos[termo]
    
    if not termo:
        termo = "dano moral"  # padrão
    
    print(f"\n   🎯 Vou buscar por: '{termo}'")
    print(f"   📊 Máximo de resultados: 3 (para teste rápido)")
    
    input("\n   📌 Pressione ENTER para começar...")
    
    # Criar o scraper
    print("\n🤖 Inicializando robô...")
    scraper = TJSPScraper(headless=False)  # False = mostra o navegador
    
    try:
        print("\n🔍 Iniciando busca no TJSP...")
        print("   ⏳ Aguarde... (pode demorar 1-2 minutos)")
        
        # Fazer a busca real
        resultados = scraper.search_acordaos(termo, max_resultados=3)
        
        # Mostrar resultados
        if resultados:
            print(f"\n✅ SUCESSO! Encontrei {len(resultados)} resultados:")
            print("=" * 60)
            
            for i, acordo in enumerate(resultados, 1):
                print(f"\n📄 RESULTADO {i}:")
                print(f"   Processo: {acordo.get('numero_acordao', 'N/A')}")
                print(f"   Data: {acordo.get('data_julgamento', 'N/A')}")
                print(f"   Relator: {acordo.get('relator', 'N/A')}")
                print(f"   Comarca: {acordo.get('comarca', 'N/A')}")
                print(f"   Órgão: {acordo.get('orgao_julgador', 'N/A')}")
                
                if acordo.get('ementa'):
                    ementa = acordo['ementa'][:200] + "..." if len(acordo['ementa']) > 200 else acordo['ementa']
                    print(f"   Ementa: {ementa}")
                
                if acordo.get('pdf_url'):
                    print(f"   📎 PDF: Disponível")
                else:
                    print(f"   📎 PDF: Não encontrado")
                
                print("-" * 40)
        
        else:
            print("\n⚠️  Nenhum resultado encontrado")
            print("   💡 Tente outro termo de busca")
            
    except Exception as e:
        print(f"\n❌ ERRO: {str(e)}")
        print("\n💡 Possíveis causas:")
        print("   • Site do TJSP pode estar lento")
        print("   • Estrutura da página mudou")
        print("   • Problema de conexão")
        
    finally:
        print("\n🔄 Fechando navegador...")
        scraper._close_driver()
        
    print("\n" + "=" * 60)
    print("✅ TESTE CONCLUÍDO!")
    print("=" * 60)
    
    if 'resultados' in locals() and resultados:
        print(f"\n📊 RESUMO:")
        print(f"   Termo buscado: {termo}")
        print(f"   Resultados encontrados: {len(resultados)}")
        print(f"   PDFs disponíveis: {sum(1 for r in resultados if r.get('pdf_url'))}")
        
        # Perguntar se quer baixar PDFs
        if any(r.get('pdf_url') for r in resultados):
            baixar = input("\n   🔽 Quer baixar os PDFs? (s/n): ").strip().lower()
            
            if baixar in ['s', 'sim', 'y', 'yes']:
                print("\n📥 Baixando PDFs...")
                
                for resultado in resultados:
                    if resultado.get('pdf_url') and resultado.get('filename'):
                        print(f"   📄 Baixando: {resultado['filename']}")
                        sucesso, caminho = scraper.download_pdf(
                            resultado['pdf_url'], 
                            resultado['filename']
                        )
                        
                        if sucesso:
                            print(f"   ✅ Salvo em: {caminho}")
                        else:
                            print(f"   ❌ Erro: {caminho}")
                        
                        time.sleep(1)  # Pausa entre downloads
    
    print("\n🎉 Obrigado por testar o sistema!")

if __name__ == "__main__":
    main()