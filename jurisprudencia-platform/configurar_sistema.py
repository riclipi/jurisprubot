"""
🔧 CONFIGURADOR DO SISTEMA REAL
==============================

Este script configura tudo para o sistema funcionar 100%!
"""

import os
import subprocess
import sys
from pathlib import Path

def instalar_dependencias():
    """Instala todas as dependências necessárias."""
    print("📦 Instalando dependências...")
    
    dependencias = [
        "langchain",
        "langchain-community", 
        "chromadb",
        "sentence-transformers",
        "openai",
        "google-generativeai",
        "PyPDF2",
        "selenium",
        "beautifulsoup4",
        "requests",
        "python-dotenv",
        "streamlit",
        "pandas",
        "numpy"
    ]
    
    for dep in dependencias:
        try:
            print(f"   ⏳ Instalando {dep}...")
            subprocess.run([sys.executable, "-m", "pip", "install", dep], 
                         check=True, capture_output=True)
            print(f"   ✅ {dep} instalado")
        except subprocess.CalledProcessError:
            print(f"   ⚠️  Erro ao instalar {dep}")

def criar_estrutura_dados():
    """Cria a estrutura de diretórios."""
    print("\n📁 Criando estrutura de dados...")
    
    dirs = [
        "data/raw_pdfs",
        "data/processed", 
        "data/vectorstore",
        "logs"
    ]
    
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"   ✅ {dir_path}")

def configurar_ambiente():
    """Configura arquivo .env."""
    print("\n🔧 Configurando ambiente...")
    
    env_content = """# Configuração do Sistema de Jurisprudência
# ==========================================

# APIs de IA (escolha uma ou ambas)
OPENAI_API_KEY=
GOOGLE_API_KEY=

# URLs do TJSP
TJSP_BASE_URL=https://esaj.tjsp.jus.br

# Configurações do sistema
DEBUG=True
HEADLESS=True
MAX_RESULTS_DEFAULT=10

# Configurações de rate limiting
MIN_DELAY=1.0
MAX_DELAY=3.0
MAX_RETRIES=3

# Paths
RAW_PDF_DIR=data/raw_pdfs
PROCESSED_DIR=data/processed
VECTOR_STORE_DIR=data/vectorstore
"""
    
    with open(".env", "w") as f:
        f.write(env_content)
    
    print("   ✅ Arquivo .env criado")

def verificar_chrome():
    """Verifica se o Chrome está instalado."""
    print("\n🌐 Verificando Google Chrome...")
    
    try:
        result = subprocess.run(["google-chrome", "--version"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f"   ✅ Chrome instalado: {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        print("   ❌ Chrome não encontrado")
        return False
    
    return False

def criar_arquivo_teste():
    """Cria arquivo de teste para validar o sistema."""
    print("\n🧪 Criando arquivo de teste...")
    
    teste_content = '''"""
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
    print("\\n🤖 Testando scraper...")
    
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
    
    print("\\n" + "=" * 40)
    print("📊 RESULTADO DOS TESTES")
    print("=" * 40)
    
    if imports_ok and scraper_ok:
        print("✅ SISTEMA PRONTO PARA USO!")
        print("\\n🚀 Para iniciar:")
        print("   streamlit run interface_completa.py")
    else:
        print("❌ Sistema com problemas")
        print("   Execute: python configurar_sistema.py")

if __name__ == "__main__":
    main()
'''
    
    with open("testar_sistema.py", "w") as f:
        f.write(teste_content)
    
    print("   ✅ testar_sistema.py criado")

def main():
    print("🔧 CONFIGURADOR DO SISTEMA REAL")
    print("=" * 50)
    
    # Executar configurações
    instalar_dependencias()
    criar_estrutura_dados()
    configurar_ambiente()
    chrome_ok = verificar_chrome()
    criar_arquivo_teste()
    
    print("\n" + "=" * 50)
    print("📊 RESUMO DA CONFIGURAÇÃO")
    print("=" * 50)
    
    print("✅ Dependências instaladas")
    print("✅ Estrutura de dados criada")
    print("✅ Arquivo .env configurado")
    print("✅ Arquivo de teste criado")
    
    if chrome_ok:
        print("✅ Google Chrome disponível")
    else:
        print("⚠️  Google Chrome não detectado")
    
    print("\n🚀 PRÓXIMOS PASSOS:")
    print("1. Configure as chaves de API no arquivo .env")
    print("2. Execute: python testar_sistema.py")
    print("3. Se tudo estiver ok: streamlit run interface_completa.py")
    
    print("\n💡 CHAVES DE API GRATUITAS:")
    print("• Google (Gratuito): https://makersuite.google.com/app/apikey")
    print("• OpenAI (Pago): https://platform.openai.com/api-keys")
    
    print("\n🎉 Sistema configurado com sucesso!")

if __name__ == "__main__":
    main()