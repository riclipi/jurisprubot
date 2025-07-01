"""Teste rápido do TJSP Scraper."""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from src.scraper.tjsp_scraper import TJSPScraper

def quick_test():
    print("🔍 Teste Rápido do TJSP Scraper\n")
    
    # Criar scraper
    scraper = TJSPScraper(headless=True)
    
    try:
        print("1️⃣ Buscando 2 acórdãos sobre 'dano moral'...")
        
        # Buscar apenas 2 resultados
        results = scraper.search_acordaos("dano moral", max_resultados=2)
        
        if results:
            print(f"\n✅ Encontrados {len(results)} acórdãos!\n")
            
            for i, acordao in enumerate(results, 1):
                print(f"Acórdão {i}:")
                print(f"  Número: {acordao.get('numero_acordao', 'N/A')}")
                print(f"  Data: {acordao.get('data_julgamento', 'N/A')}")
                print(f"  Relator: {acordao.get('relator', 'N/A')}")
                print(f"  PDF URL: {'Sim' if acordao.get('pdf_url') else 'Não'}")
                print()
        else:
            print("❌ Nenhum resultado encontrado")
            
    except Exception as e:
        print(f"❌ Erro: {e}")
    finally:
        scraper._close_driver()
        print("Teste concluído!")

if __name__ == "__main__":
    quick_test()