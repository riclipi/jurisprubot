#!/usr/bin/env python3
"""
Script de teste completo para o SimpleTJSPScraper
Verifica downloads, valida PDFs e gera relatório detalhado
"""

import sys
import os
import json
from datetime import datetime
from pathlib import Path

# Adicionar o diretório src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from scraper.tjsp_scraper import SimpleTJSPScraper
except ImportError as e:
    print(f"❌ Erro ao importar SimpleTJSPScraper: {e}")
    print("Verifique se o arquivo src/scraper/tjsp_scraper.py existe.")
    sys.exit(1)


def verificar_pdf(filepath):
    """Verifica se um arquivo é um PDF válido"""
    try:
        with open(filepath, 'rb') as f:
            header = f.read(4)
            return header == b'%PDF'
    except:
        return False


def test_scraper():
    """Testa o scraper com relatório detalhado e tratamento de erros"""
    print("\n" + "="*80)
    print("🔍 TESTE COMPLETO DO TJSP SCRAPER MVP")
    print("="*80)
    print(f"📅 Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"📂 Diretório de trabalho: {os.getcwd()}")
    print("="*80)
    
    try:
        # Inicializar o scraper
        print("\n1️⃣ Inicializando o scraper...")
        scraper = SimpleTJSPScraper()
        print("   ✅ Scraper inicializado com sucesso")
        print(f"   📁 Diretório de download: {scraper.download_dir}")
        
        # Executar downloads
        print("\n2️⃣ Iniciando download dos acórdãos...")
        print("   ⏳ Isso pode levar alguns minutos...")
        
        relatorio = scraper.download_sample_acordaos()
        
        # Análise dos resultados
        print("\n3️⃣ Analisando resultados...")
        print("="*80)
        print("📊 RESUMO DO PROCESSO")
        print("="*80)
        print(f"   Total de arquivos: {relatorio['total_arquivos']}")
        print(f"   ✅ Downloads com sucesso: {relatorio['sucessos']}")
        print(f"   ❌ Downloads com erro: {relatorio['erros']}")
        print(f"   ⏱️  Tempo total: {relatorio['tempo_total_segundos']} segundos")
        print(f"   📈 Taxa de sucesso: {(relatorio['sucessos']/relatorio['total_arquivos']*100):.1f}%")
        
        # Verificar integridade dos PDFs baixados
        print("\n4️⃣ Verificando integridade dos PDFs...")
        pdfs_validos = 0
        pdfs_invalidos = 0
        tamanho_total = 0
        
        if relatorio['sucessos'] > 0:
            print(f"\n   📂 Verificando arquivos em: {relatorio['diretorio_download']}")
            
            for resultado in relatorio['resultados']:
                if resultado['status'] == 'sucesso':
                    filepath = Path(resultado['caminho'])
                    if filepath.exists():
                        if verificar_pdf(filepath):
                            pdfs_validos += 1
                            tamanho_total += resultado['tamanho']
                            print(f"   ✅ {resultado['arquivo']} - PDF válido ({resultado['tamanho']:,} bytes)")
                        else:
                            pdfs_invalidos += 1
                            print(f"   ❌ {resultado['arquivo']} - PDF inválido!")
                    else:
                        print(f"   ⚠️  {resultado['arquivo']} - Arquivo não encontrado!")
        
        print(f"\n   📊 PDFs válidos: {pdfs_validos}")
        print(f"   📊 PDFs inválidos: {pdfs_invalidos}")
        print(f"   💾 Tamanho total: {tamanho_total:,} bytes ({tamanho_total/1024/1024:.2f} MB)")
        
        # Detalhes dos erros (se houver)
        if relatorio['erros'] > 0:
            print("\n5️⃣ Detalhes dos erros encontrados:")
            print("="*80)
            for resultado in relatorio['resultados']:
                if resultado['status'] == 'erro':
                    print(f"\n   ❌ Arquivo: {resultado['arquivo']}")
                    print(f"      Motivo: {resultado['motivo']}")
                    print(f"      URL: {resultado.get('url', 'N/A')}")
        
        # Salvar relatório em JSON
        print("\n6️⃣ Salvando relatório detalhado...")
        relatorio_path = Path('relatorio_scraper.json')
        with open(relatorio_path, 'w', encoding='utf-8') as f:
            json.dump(relatorio, f, ensure_ascii=False, indent=2)
        print(f"   ✅ Relatório salvo em: {relatorio_path}")
        
        # Resultado final
        print("\n" + "="*80)
        if relatorio['sucessos'] == relatorio['total_arquivos']:
            print("🎉 TESTE CONCLUÍDO COM SUCESSO!")
            print("Todos os arquivos foram baixados corretamente.")
        elif relatorio['sucessos'] > 0:
            print("⚠️  TESTE CONCLUÍDO COM AVISOS")
            print(f"Alguns arquivos não puderam ser baixados ({relatorio['erros']} erros).")
        else:
            print("❌ TESTE FALHOU")
            print("Nenhum arquivo foi baixado com sucesso.")
        print("="*80)
        
        # Mostrar próximos passos
        if relatorio['sucessos'] > 0:
            print("\n📌 PRÓXIMOS PASSOS:")
            print("1. Os PDFs estão prontos para processamento")
            print("2. Execute o processador de PDFs para extrair o texto")
            print("3. Configure o sistema RAG para busca semântica")
            print(f"4. Arquivos disponíveis em: {relatorio['diretorio_download']}")
        
        return relatorio['sucessos'] > 0
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Teste interrompido pelo usuário!")
        return False
        
    except Exception as e:
        print(f"\n\n❌ Erro inesperado durante o teste: {type(e).__name__}")
        print(f"   Detalhes: {str(e)}")
        import traceback
        print("\n📋 Stack trace:")
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Executar o teste
    sucesso = test_scraper()
    
    # Código de saída
    sys.exit(0 if sucesso else 1)