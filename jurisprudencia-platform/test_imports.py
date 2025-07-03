#!/usr/bin/env python3
"""
Script de teste para verificar se os imports estão funcionando corretamente
após a correção de imports absolutos para relativos.
"""

import sys
import os
from pathlib import Path

# Cores para output
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def test_imports():
    """Testa se os imports estão funcionando corretamente"""
    print(f"{BLUE}=== Teste de Imports Corrigidos ==={RESET}\n")
    
    # Adicionar src ao path para simular execução normal
    src_path = Path(__file__).parent / 'src'
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    
    errors = []
    successes = []
    
    # Lista de imports para testar
    imports_to_test = [
        # Interface imports
        ("interface.app", "SimpleSearchEngine", "from interface.app"),
        ("interface.app", "RealtimeJurisprudenceSearch", "from interface.app"),
        ("interface.interface_premium", "InterfacePremium", "from interface.interface_premium"),
        ("interface.mcp_tab", "render_mcp_tab", "from interface.mcp_tab"),
        
        # RAG imports
        ("rag.simple_search", "SimpleSearchEngine", "from rag.simple_search"),
        
        # Scraper imports
        ("scraper.realtime_search", "RealtimeJurisprudenceSearch", "from scraper.realtime_search"),
    ]
    
    print(f"Testando {len(imports_to_test)} imports...\n")
    
    for module_name, class_name, import_desc in imports_to_test:
        try:
            # Tentar importar o módulo
            module = __import__(module_name, fromlist=[class_name])
            
            # Verificar se a classe/função existe
            if hasattr(module, class_name):
                successes.append(f"{import_desc}: {class_name}")
                print(f"{GREEN}✓{RESET} {import_desc}: {class_name}")
            else:
                errors.append(f"{import_desc}: {class_name} não encontrado no módulo")
                print(f"{RED}✗{RESET} {import_desc}: {class_name} não encontrado no módulo")
                
        except ImportError as e:
            errors.append(f"{import_desc}: {str(e)}")
            print(f"{RED}✗{RESET} {import_desc}: {str(e)}")
        except Exception as e:
            errors.append(f"{import_desc}: Erro inesperado - {str(e)}")
            print(f"{RED}✗{RESET} {import_desc}: Erro inesperado - {str(e)}")
    
    # Resumo
    print(f"\n{BLUE}=== Resumo ==={RESET}")
    print(f"{GREEN}Sucessos:{RESET} {len(successes)}")
    print(f"{RED}Erros:{RESET} {len(errors)}")
    
    if errors:
        print(f"\n{RED}Detalhes dos erros:{RESET}")
        for error in errors:
            print(f"  - {error}")
            
    return len(errors) == 0

def test_streamlit_execution():
    """Testa se o app.py pode ser executado pelo Streamlit"""
    print(f"\n{BLUE}=== Teste de Execução Streamlit ==={RESET}\n")
    
    app_path = Path(__file__).parent / 'src' / 'interface' / 'app.py'
    
    if not app_path.exists():
        print(f"{RED}✗{RESET} app.py não encontrado em {app_path}")
        return False
    
    print(f"{GREEN}✓{RESET} app.py encontrado em {app_path}")
    
    # Simular execução do Streamlit (apenas verifica sintaxe)
    original_dir = os.getcwd()
    try:
        # Mudar para o diretório do app.py
        os.chdir(app_path.parent)
        
        # Tentar compilar o arquivo
        with open('app.py', 'r', encoding='utf-8') as f:
            code = f.read()
        
        compile(code, 'app.py', 'exec')
        print(f"{GREEN}✓{RESET} app.py tem sintaxe válida")
        
        # Verificar imports relativos
        if 'from ..rag.simple_search' in code:
            print(f"{GREEN}✓{RESET} Imports relativos detectados corretamente")
        else:
            print(f"{YELLOW}⚠{RESET} Imports podem não estar usando caminhos relativos")
            
        return True
        
    except SyntaxError as e:
        print(f"{RED}✗{RESET} Erro de sintaxe em app.py: {e}")
        return False
    except Exception as e:
        print(f"{RED}✗{RESET} Erro ao verificar app.py: {e}")
        return False
    finally:
        os.chdir(original_dir)

def check_data_paths():
    """Verifica se os caminhos de dados estão acessíveis"""
    print(f"\n{BLUE}=== Verificação de Caminhos de Dados ==={RESET}\n")
    
    base_path = Path(__file__).parent
    data_paths = [
        'data/processed',
        'data/raw_pdfs',
        'data/documents/juridicos',
        'data/templates',
        'data/mcp_documents',
        'data/mcp_organized',
        'data/mcp_backups',
        'data/pdf_cache',
        'data/temp_pdf'
    ]
    
    accessible = 0
    for data_path in data_paths:
        full_path = base_path / data_path
        if full_path.exists():
            print(f"{GREEN}✓{RESET} {data_path} - Existe")
            accessible += 1
        else:
            print(f"{YELLOW}⚠{RESET} {data_path} - Não existe (será criado quando necessário)")
    
    print(f"\n{accessible}/{len(data_paths)} diretórios de dados existem")
    return True

def main():
    """Função principal"""
    print(f"{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}VERIFICAÇÃO DE CORREÇÃO DE IMPORTS{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")
    
    all_tests_passed = True
    
    # Teste 1: Imports
    if not test_imports():
        all_tests_passed = False
    
    # Teste 2: Execução Streamlit
    if not test_streamlit_execution():
        all_tests_passed = False
    
    # Teste 3: Caminhos de dados
    if not check_data_paths():
        all_tests_passed = False
    
    # Resultado final
    print(f"\n{BLUE}{'='*60}{RESET}")
    if all_tests_passed:
        print(f"{GREEN}✓ TODOS OS TESTES PASSARAM!{RESET}")
        print(f"\nOs imports foram corrigidos com sucesso.")
        print(f"O app.py está pronto para ser executado no Streamlit Cloud.")
    else:
        print(f"{RED}✗ ALGUNS TESTES FALHARAM{RESET}")
        print(f"\nVerifique os erros acima antes de fazer o deploy.")
    print(f"{BLUE}{'='*60}{RESET}")

if __name__ == '__main__':
    main()