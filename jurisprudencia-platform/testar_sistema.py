"""
Teste do Sistema Completo
========================
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

def testar_imports():
    """Testa se todos os módulos podem ser importados."""
    print("📋 Testando imports...")
    
    try:
        import streamlit
        print("   ✅ Streamlit")
        
        import selenium
        print("   ✅ Selenium")
        
        import bs4
        print("   ✅ BeautifulSoup")
        
        from src.scraper.tjsp_scraper import TJSPScraper
        print("   ✅ TJSP Scraper")
        
        import chromadb
        print("   ✅ ChromaDB")
        
        import sentence_transformers
        print("   ✅ Sentence Transformers")
        
        return True
        
    except ImportError as e:
        print(f"   ❌ Erro: {e}")
        return False

def testar_scraper():
    """Testa o scraper básico."""
    print("\n🤖 Testando scraper...")
    
    try:
        from src.scraper.tjsp_scraper import TJSPScraper
        
        # Teste básico de inicialização
        scraper = TJSPScraper(headless=True)
        print("   ✅ Scraper inicializado")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erro no scraper: {e}")
        return False

def main():
    print("🧪 TESTE COMPLETO DO SISTEMA")
    print("=" * 40)
    
    # Testes
    imports_ok = testar_imports()
    scraper_ok = testar_scraper()
    
    print("\n" + "=" * 40)
    print("📊 RESULTADO DOS TESTES")
    print("=" * 40)
    
    if imports_ok and scraper_ok:
        print("✅ SISTEMA PRONTO PARA USO!")
        print("\n🚀 Para iniciar:")
        print("   streamlit run interface_completa.py")
    else:
        print("❌ Sistema com problemas")
        print("   Execute: python configurar_sistema.py")

if __name__ == "__main__":
    main()
