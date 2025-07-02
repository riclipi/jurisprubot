#!/usr/bin/env python3
"""
Script de instalação das funcionalidades extras MCP
Execute este script para ativar recursos opcionais
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, description):
    """Executar comando com tratamento de erro"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} - Concluído!")
            return True
        else:
            print(f"⚠️ {description} - Aviso: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ {description} - Erro: {e}")
        return False

def check_python_packages():
    """Verificar e instalar pacotes Python opcionais"""
    packages = {
        'PyPDF2': 'Suporte completo a PDFs',
        'pandas': 'Análise de dados avançada',
        'matplotlib': 'Gráficos estatísticos'
    }
    
    installed = []
    missing = []
    
    for package, description in packages.items():
        try:
            __import__(package.lower() if package != 'PyPDF2' else 'PyPDF2')
            print(f"✅ {package} - {description} (já instalado)")
            installed.append(package)
        except ImportError:
            print(f"⚪ {package} - {description} (não instalado)")
            missing.append(package)
    
    return installed, missing

def install_optional_packages(packages):
    """Instalar pacotes opcionais"""
    if not packages:
        print("✅ Todos os pacotes opcionais já estão instalados!")
        return True
    
    print(f"\n📦 Instalando pacotes opcionais: {', '.join(packages)}")
    
    install_cmd = f"{sys.executable} -m pip install {' '.join(packages)}"
    
    return run_command(install_cmd, "Instalação de pacotes")

def setup_directories():
    """Configurar diretórios necessários"""
    directories = [
        "data/mcp_documents",
        "data/mcp_backups", 
        "data/mcp_organized",
        "data/pdf_cache",
        "data/temp_pdf"
    ]
    
    print("📁 Configurando diretórios...")
    
    for directory in directories:
        path = Path(directory)
        path.mkdir(parents=True, exist_ok=True)
        print(f"  ✅ {directory}")
    
    return True

def create_config_file():
    """Criar arquivo de configuração MCP"""
    config = {
        "mcp_settings": {
            "auto_organize": True,
            "backup_enabled": True,
            "pdf_processing": True,
            "max_file_size_mb": 100,
            "supported_formats": ["txt", "pdf"]
        },
        "directories": {
            "documents": "data/mcp_documents",
            "organized": "data/mcp_organized", 
            "backups": "data/mcp_backups",
            "cache": "data/pdf_cache"
        }
    }
    
    config_path = Path("mcp_config.json")
    
    try:
        import json
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
        
        print(f"✅ Configuração criada: {config_path}")
        return True
    except Exception as e:
        print(f"❌ Erro ao criar configuração: {e}")
        return False

def test_mcp_modules():
    """Testar se módulos MCP funcionam"""
    print("🧪 Testando módulos MCP...")
    
    try:
        # Testar importação dos módulos
        sys.path.append('.')
        
        from src.mcp_integration import MCPDocumentManager, FileOrganizer, PDFProcessor
        
        # Teste básico
        manager = MCPDocumentManager()
        organizer = FileOrganizer()
        processor = PDFProcessor()
        
        print("✅ MCPDocumentManager - OK")
        print("✅ FileOrganizer - OK")
        print(f"✅ PDFProcessor - {'Completo' if processor.pdf_available else 'Básico'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao testar módulos: {e}")
        return False

def main():
    """Função principal de instalação"""
    print("🚀 Instalação das Funcionalidades Extras MCP")
    print("=" * 50)
    print()
    
    # 1. Verificar pacotes Python
    print("1️⃣ Verificando pacotes Python...")
    installed, missing = check_python_packages()
    print()
    
    # 2. Perguntar se quer instalar pacotes opcionais
    if missing:
        print("📋 Pacotes opcionais disponíveis:")
        for package in missing:
            print(f"  • {package}")
        print()
        
        response = input("Deseja instalar os pacotes opcionais? (s/n): ").lower().strip()
        
        if response in ['s', 'sim', 'y', 'yes']:
            if install_optional_packages(missing):
                print("✅ Pacotes instalados com sucesso!")
            else:
                print("⚠️ Alguns pacotes podem não ter sido instalados")
        else:
            print("⏭️ Pulando instalação de pacotes opcionais")
    
    print()
    
    # 3. Configurar diretórios
    print("2️⃣ Configurando diretórios...")
    setup_directories()
    print()
    
    # 4. Criar configuração
    print("3️⃣ Criando arquivo de configuração...")
    create_config_file()
    print()
    
    # 5. Testar módulos
    print("4️⃣ Testando módulos MCP...")
    test_success = test_mcp_modules()
    print()
    
    # Resumo final
    print("📊 RESUMO DA INSTALAÇÃO")
    print("=" * 30)
    
    if test_success:
        print("✅ Instalação concluída com sucesso!")
        print()
        print("🚀 Próximos passos:")
        print("1. Execute: streamlit run src/interface/app.py")
        print("2. Acesse a aba '📁 Gestão MCP'")
        print("3. Teste as funcionalidades extras")
        print()
        print("📚 Funcionalidades disponíveis:")
        print("• Upload e gestão avançada de documentos")
        print("• Organização automática por categoria/ano")
        print("• Processamento de PDFs com extração de texto")
        print("• Backup automático de documentos importantes")
        print("• Estatísticas e relatórios detalhados")
    else:
        print("⚠️ Instalação concluída com avisos")
        print("A aba MCP estará disponível, mas algumas funcionalidades podem estar limitadas")
        print()
        print("💡 Para resolver:")
        print("1. Verifique se todos os arquivos estão no lugar correto")
        print("2. Execute novamente este script")
        print("3. Se o problema persistir, use apenas a aba de busca principal")

if __name__ == "__main__":
    main()