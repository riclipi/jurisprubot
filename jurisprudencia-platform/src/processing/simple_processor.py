"""
Processador SIMPLES de PDFs - MVP
Apenas extrai texto de PDF usando PyPDF2
"""

import PyPDF2
import os
from pathlib import Path


def process_single_pdf(pdf_path):
    """
    Lê um PDF e extrai o texto
    
    Args:
        pdf_path: Caminho para o arquivo PDF
        
    Returns:
        str: Texto extraído do PDF
    """
    try:
        print(f"📄 Processando: {pdf_path}")
        
        # Abrir o PDF
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            # Verificar se tem páginas
            num_pages = len(pdf_reader.pages)
            print(f"   Páginas encontradas: {num_pages}")
            
            # Extrair texto de todas as páginas
            text = ""
            for page_num in range(num_pages):
                page = pdf_reader.pages[page_num]
                text += page.extract_text() + "\n"
            
            # Limpar texto básico
            text = text.strip()
            text = text.replace('\n\n', '\n')  # Reduzir quebras duplas
            
            print(f"   ✅ Texto extraído: {len(text)} caracteres")
            return text
            
    except Exception as e:
        print(f"   ❌ Erro ao processar {pdf_path}: {e}")
        return ""


def test_one_pdf():
    """
    Testa processamento do primeiro PDF encontrado
    """
    print("🚀 TESTE SIMPLES DE EXTRAÇÃO DE PDF")
    print("=" * 50)
    
    # Encontrar pasta de PDFs
    pdf_dir = Path("data/raw_pdfs")
    
    if not pdf_dir.exists():
        print("❌ Pasta data/raw_pdfs não encontrada!")
        return
    
    # Pegar primeiro PDF
    pdf_files = list(pdf_dir.glob("*.pdf"))
    
    if not pdf_files:
        print("❌ Nenhum PDF encontrado na pasta!")
        return
    
    # Processar primeiro PDF
    first_pdf = pdf_files[0]
    print(f"📁 Usando PDF: {first_pdf.name}")
    
    # Extrair texto
    text = process_single_pdf(first_pdf)
    
    if text:
        print("\n" + "=" * 50)
        print("📖 TEXTO EXTRAÍDO (primeiros 500 caracteres):")
        print("=" * 50)
        print(text[:500])
        print("...")
        print(f"\n📊 Total de caracteres: {len(text)}")
        print(f"📊 Total de palavras: {len(text.split())}")
        
        # Verificar se parece ser um acórdão
        keywords = ["negativação", "indevida", "dano", "moral", "tjsp", "acórdão", "apelação"]
        found_keywords = [kw for kw in keywords if kw.lower() in text.lower()]
        
        print(f"🔍 Palavras-chave encontradas: {found_keywords}")
        
        if found_keywords:
            print("✅ Parece ser um acórdão sobre negativação indevida!")
        else:
            print("⚠️ Não identificou palavras-chave esperadas")
            
    else:
        print("❌ Não conseguiu extrair texto!")


def save_extracted_text(text, pdf_filename, output_dir):
    """
    Salva texto extraído em arquivo .txt
    
    Args:
        text: Texto extraído do PDF
        pdf_filename: Nome do arquivo PDF original
        output_dir: Diretório de saída
        
    Returns:
        str: Caminho do arquivo .txt criado
    """
    # Criar nome do arquivo .txt (mesmo nome do PDF)
    txt_filename = pdf_filename.replace('.pdf', '.txt')
    txt_path = Path(output_dir) / txt_filename
    
    # Criar diretório se não existir
    txt_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Salvar texto
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write(text)
    
    print(f"   💾 Salvo em: {txt_path}")
    return str(txt_path)


def generate_report(results):
    """
    Gera relatório detalhado do processamento
    
    Args:
        results: Lista de resultados do processamento
    """
    print("\n" + "=" * 60)
    print("📊 RELATÓRIO FINAL DE PROCESSAMENTO")
    print("=" * 60)
    
    total_pdfs = len(results)
    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]
    
    print(f"📁 Total de PDFs encontrados: {total_pdfs}")
    print(f"✅ Processados com sucesso: {len(successful)}")
    print(f"❌ Falharam: {len(failed)}")
    
    if successful:
        total_chars = sum(r['characters'] for r in successful)
        total_words = sum(r['words'] for r in successful)
        total_pages = sum(r['pages'] for r in successful)
        
        print(f"\n📈 ESTATÍSTICAS GERAIS:")
        print(f"   📄 Total de páginas: {total_pages}")
        print(f"   📝 Total de caracteres: {total_chars:,}")
        print(f"   📖 Total de palavras: {total_words:,}")
        print(f"   📊 Média de caracteres por PDF: {total_chars//len(successful):,}")
        print(f"   📊 Média de palavras por PDF: {total_words//len(successful):,}")
        
        print(f"\n📂 ARQUIVOS CRIADOS:")
        for result in successful:
            print(f"   ✅ {result['txt_file']}")
    
    if failed:
        print(f"\n❌ PROBLEMAS ENCONTRADOS:")
        for result in failed:
            print(f"   ❌ {result['pdf_file']}: {result['error']}")
    
    print("\n" + "=" * 60)


def process_all_pdfs():
    """
    Processa todos os PDFs da pasta e salva os textos
    
    Returns:
        list: Lista com resultados do processamento
    """
    print("🚀 PROCESSANDO TODOS OS PDFs")
    print("=" * 60)
    
    pdf_dir = Path("data/raw_pdfs")
    output_dir = Path("data/processed")
    
    # Verificar se pasta existe
    if not pdf_dir.exists():
        print("❌ Pasta data/raw_pdfs não encontrada!")
        return []
    
    # Criar pasta de saída
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Listar todos os PDFs
    pdf_files = list(pdf_dir.glob("*.pdf"))
    
    if not pdf_files:
        print("❌ Nenhum PDF encontrado na pasta!")
        return []
    
    print(f"📁 Encontrados {len(pdf_files)} PDFs para processar\n")
    
    results = []
    
    # Processar cada PDF
    for i, pdf_file in enumerate(pdf_files, 1):
        print(f"[{i}/{len(pdf_files)}] {pdf_file.name}")
        
        result = {
            'pdf_file': pdf_file.name,
            'success': False,
            'txt_file': '',
            'characters': 0,
            'words': 0,
            'pages': 0,
            'error': ''
        }
        
        try:
            # Extrair texto
            text = process_single_pdf(pdf_file)
            
            if text:
                # Salvar texto
                txt_path = save_extracted_text(text, pdf_file.name, output_dir)
                
                # Calcular estatísticas
                result.update({
                    'success': True,
                    'txt_file': txt_path,
                    'characters': len(text),
                    'words': len(text.split()),
                    'pages': len(PyPDF2.PdfReader(open(pdf_file, 'rb')).pages)
                })
            else:
                result['error'] = 'Texto vazio extraído'
                
        except Exception as e:
            result['error'] = str(e)
            print(f"   ❌ Erro: {e}")
        
        results.append(result)
        print()  # Linha em branco
    
    # Gerar relatório
    generate_report(results)
    
    return results


if __name__ == "__main__":
    # Comentar teste individual
    # test_one_pdf()
    
    # Executar processamento completo
    process_all_pdfs()