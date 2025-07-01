#!/usr/bin/env python3
"""
Teste simples da interface para verificar se está funcionando
"""

import sys
sys.path.append('.')

def test_interface():
    """Testa se a interface pode ser importada e executada"""
    print("🧪 Testando interface Streamlit...")
    
    try:
        # Testar importação
        from src.interface.app import load_local_search_engine, load_realtime_search_engine, perform_search
        print("✅ Interface importada com sucesso!")
        
        # Testar carregamento do sistema de busca local
        print("🚀 Testando carregamento do sistema local...")
        local_engine = load_local_search_engine()
        print("✅ Sistema de busca local carregado!")
        
        # Testar carregamento do sistema de tempo real
        print("🌐 Testando carregamento do sistema tempo real...")
        realtime_engine = load_realtime_search_engine()
        print("✅ Sistema de busca tempo real carregado!")
        
        # Testar uma busca simples local
        print("🔍 Testando busca local...")
        results = local_engine.search("negativação indevida", top_k=2)
        print(f"✅ Busca local executada! {len(results)} resultados encontrados")
        
        # Mostrar primeiro resultado
        if results:
            result = results[0]
            print(f"\n📄 Resultado de exemplo:")
            print(f"   Score: {result['score']:.3f}")
            print(f"   Arquivo: {result['metadata']['file']}")
            print(f"   Trecho: {result['preview'][:100]}...")
        
        print("\n🎉 Interface funcionando perfeitamente!")
        print("💡 Para acessar a interface web, execute:")
        print("   streamlit run src/interface/app.py")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

if __name__ == "__main__":
    test_interface()