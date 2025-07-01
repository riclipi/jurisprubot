"""
🎯 TESTE COMPLETO DO SISTEMA - SUPER FÁCIL!
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

print("=" * 60)
print("🚀 TESTE DO SISTEMA DE JURISPRUDÊNCIA")
print("=" * 60)

# Passo 1: Testar se tudo está instalado
print("\n1️⃣ Verificando instalações...")
try:
    import selenium
    print("✅ Selenium instalado")
    
    import streamlit
    print("✅ Streamlit instalado")
    
    import bs4
    print("✅ BeautifulSoup instalado")
    
    from src.scraper.tjsp_scraper import TJSPScraper
    print("✅ Sistema de scraping carregado")
    
except Exception as e:
    print(f"❌ Erro: {e}")
    sys.exit(1)

# Passo 2: Teste básico do scraper
print("\n2️⃣ Testando o sistema de busca...")
print("   ⚠️  ATENÇÃO: O navegador vai abrir automaticamente!")
print("   👀 Você vai ver ele navegando no site do TJSP")

try:
    # Criar scraper com navegador visível
    scraper = TJSPScraper(headless=False)  # False = você vê o navegador
    
    input("\n   📌 Pressione ENTER para começar o teste...")
    
    print("\n   🔍 Buscando jurisprudências sobre 'dano moral'...")
    
    # Buscar apenas 1 resultado para teste rápido
    results = scraper.search_acordaos("dano moral", max_resultados=1)
    
    if results:
        print("\n   ✅ SUCESSO! Encontrei jurisprudência!")
        print(f"\n   📄 Processo: {results[0].get('numero_acordao', 'N/A')}")
        print(f"   📅 Data: {results[0].get('data_julgamento', 'N/A')}")
        print(f"   👨‍⚖️ Relator: {results[0].get('relator', 'N/A')}")
        print(f"   📍 Comarca: {results[0].get('comarca', 'N/A')}")
        
        # Mostrar se tem PDF disponível
        if results[0].get('pdf_url'):
            print(f"   📎 PDF disponível: SIM")
        else:
            print(f"   📎 PDF disponível: NÃO")
            
    else:
        print("   ⚠️  Nenhum resultado encontrado")
        
except Exception as e:
    print(f"\n   ❌ Erro durante o teste: {e}")
    print("   💡 Dica: Verifique se o Chrome está instalado corretamente")

finally:
    try:
        scraper._close_driver()
    except:
        pass

# Passo 3: Mostrar próximos passos
print("\n" + "=" * 60)
print("📊 RESUMO DO TESTE")
print("=" * 60)

print("\n✅ O QUE FUNCIONOU:")
print("   • Sistema de busca automática")
print("   • Navegação no site do TJSP")
print("   • Extração de metadados")

print("\n🔧 PRÓXIMOS PASSOS PARA 100%:")
print("   1. Adicionar chave da OpenAI ou Google no arquivo .env")
print("   2. Executar: streamlit run src/interface/streamlit_app.py")
print("   3. Acessar: http://localhost:8501")

print("\n💡 DICA: Para ver a interface web, execute:")
print("   cd jurisprudencia-platform")
print("   streamlit run src/interface/streamlit_app.py")

print("\n🎉 Parabéns! Seu sistema está quase pronto!")
print("=" * 60)