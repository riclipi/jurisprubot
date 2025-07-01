"""
Processador de PDFs para extração de texto e metadados
Especializado em acórdãos do TJSP sobre negativação indevida
"""

import os
import re
import json
import logging
from pathlib import Path
from datetime import datetime
import PyPDF2
from typing import Dict, List, Optional, Tuple

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PDFProcessor:
    """Processa PDFs de acórdãos extraindo texto e metadados"""
    
    def __init__(self, pdf_dir='data/raw_pdfs', output_dir='data/processed'):
        self.pdf_dir = Path(pdf_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Diretórios para organizar saída
        self.text_dir = self.output_dir / 'texts'
        self.metadata_dir = self.output_dir / 'metadata'
        self.text_dir.mkdir(exist_ok=True)
        self.metadata_dir.mkdir(exist_ok=True)
        
        # Padrões regex para extração de metadados
        self.patterns = {
            'numero_processo': r'(?:Processo n[º°]?|Apelação Cível n[º°]?)\s*[:.]?\s*(\d{4,7}[-.\s]?\d{2}[-.\s]?\d{4}[-.\s]?\d[-.\s]?\d{2}[-.\s]?\d{4})',
            'relator': r'(?:Relator\(a\)|RELATOR\(A\)|Relator|RELATOR)\s*[:.]?\s*(?:Des\.|Desembargador\(a\)?|DESEMBARGADOR\(A\)?|MM\.|Dr\.|Dra\.)?\s*([A-ZÀ-Ú][A-Za-zÀ-ú\s]+?)(?:\n|$|;)',
            'data_julgamento': r'(?:Data do julgamento|DATA DO JULGAMENTO|Data de Julgamento|julgamento em)\s*[:.]?\s*(\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4})',
            'comarca': r'(?:Comarca|COMARCA)\s*[:.]?\s*([A-ZÀ-Ú][A-Za-zÀ-ú\s\-]+?)(?:\n|$|;|\.)',
            'vara': r'(?:Vara|VARA|Foro)\s*[:.]?\s*([^;\n]+?)(?:\n|$|;)',
            'valor_indenizacao': r'(?:R\$|r\$|reais)\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)',
            'turma_camara': r'(\d+[ªº]?\s*(?:Câmara|CÂMARA)\s*(?:de\s*)?(?:Direito\s*)?(?:Privado|Público|Criminal)?)'
        }
        
        # Palavras-chave para validar se é acórdão sobre negativação
        self.keywords_validacao = [
            'negativação', 'negativacao', 'serasa', 'spc', 'scpc',
            'cadastro de inadimplentes', 'órgãos de proteção ao crédito',
            'inscrição indevida', 'inscricao indevida', 'danos morais',
            'restrição creditícia', 'restricao crediticia'
        ]
        
        # Estatísticas de processamento
        self.stats = {
            'total_arquivos': 0,
            'sucesso': 0,
            'erro': 0,
            'texto_vazio': 0,
            'nao_validado': 0,
            'tempo_total': 0
        }
    
    def extract_text_from_pdf(self, pdf_path: Path) -> str:
        """
        Extrai texto de um arquivo PDF
        
        Args:
            pdf_path: Caminho do arquivo PDF
            
        Returns:
            str: Texto extraído e limpo
        """
        try:
            texto_completo = []
            
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                # Verificar se o PDF está criptografado
                if pdf_reader.is_encrypted:
                    logger.warning(f"PDF criptografado: {pdf_path.name}")
                    try:
                        pdf_reader.decrypt('')  # Tentar sem senha
                    except:
                        raise Exception("PDF protegido por senha")
                
                # Extrair texto de cada página
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        texto = page.extract_text()
                        if texto:
                            texto_completo.append(texto)
                    except Exception as e:
                        logger.error(f"Erro ao extrair página {page_num + 1}: {e}")
            
            # Juntar todo o texto
            texto_final = '\n'.join(texto_completo)
            
            # Limpar o texto
            texto_final = self._clean_text(texto_final)
            
            return texto_final
            
        except Exception as e:
            logger.error(f"Erro ao extrair texto de {pdf_path.name}: {e}")
            raise
    
    def _clean_text(self, text: str) -> str:
        """Limpa e normaliza o texto extraído"""
        if not text:
            return ""
        
        # Remover caracteres de controle
        text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\t')
        
        # Normalizar quebras de linha
        text = re.sub(r'\n{3,}', '\n\n', text)  # Máximo 2 quebras consecutivas
        text = re.sub(r'[ \t]+', ' ', text)     # Espaços múltiplos para um
        text = re.sub(r' +\n', '\n', text)      # Remover espaços antes de quebra
        text = re.sub(r'\n +', '\n', text)      # Remover espaços depois de quebra
        
        # Corrigir palavras quebradas por hifenização
        text = re.sub(r'(\w+)-\n(\w+)', r'\1\2', text)
        
        # Remover páginas em branco ou apenas com números
        lines = text.split('\n')
        lines = [line for line in lines if line.strip() and not line.strip().isdigit()]
        text = '\n'.join(lines)
        
        return text.strip()
    
    def extract_metadata(self, pdf_path: Path, texto: Optional[str] = None) -> Dict:
        """
        Extrai metadados do PDF e do texto
        
        Args:
            pdf_path: Caminho do arquivo PDF
            texto: Texto já extraído (opcional)
            
        Returns:
            dict: Metadados extraídos
        """
        metadata = {
            'arquivo': pdf_path.name,
            'caminho': str(pdf_path),
            'tamanho_bytes': pdf_path.stat().st_size,
            'data_processamento': datetime.now().isoformat(),
            'numero_paginas': 0,
            'texto_extraido': False,
            'validado': False
        }
        
        try:
            # Metadados do arquivo PDF
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                metadata['numero_paginas'] = len(pdf_reader.pages)
                
                # Metadados do PDF (se disponíveis)
                if pdf_reader.metadata:
                    pdf_meta = pdf_reader.metadata
                    metadata['pdf_metadata'] = {
                        'titulo': pdf_meta.get('/Title', ''),
                        'autor': pdf_meta.get('/Author', ''),
                        'assunto': pdf_meta.get('/Subject', ''),
                        'criador': pdf_meta.get('/Creator', ''),
                        'data_criacao': str(pdf_meta.get('/CreationDate', ''))
                    }
            
            # Se texto foi fornecido, extrair metadados do conteúdo
            if texto:
                metadata['texto_extraido'] = True
                metadata['tamanho_texto'] = len(texto)
                
                # Extrair informações usando regex
                for campo, pattern in self.patterns.items():
                    match = re.search(pattern, texto, re.IGNORECASE | re.MULTILINE)
                    if match:
                        valor = match.group(1).strip()
                        # Limpar valor extraído
                        valor = re.sub(r'\s+', ' ', valor)
                        metadata[campo] = valor
                
                # Validar se é acórdão sobre negativação
                texto_lower = texto.lower()
                metadata['validado'] = any(keyword in texto_lower for keyword in self.keywords_validacao)
                
                # Contar menções de palavras-chave
                metadata['mencoes_negativacao'] = sum(
                    texto_lower.count(keyword) for keyword in self.keywords_validacao
                )
                
                # Extrair primeiras linhas como resumo
                primeiras_linhas = '\n'.join(texto.split('\n')[:10])
                metadata['resumo'] = primeiras_linhas[:500] + '...' if len(primeiras_linhas) > 500 else primeiras_linhas
        
        except Exception as e:
            logger.error(f"Erro ao extrair metadados de {pdf_path.name}: {e}")
            metadata['erro_metadata'] = str(e)
        
        return metadata
    
    def process_single_pdf(self, pdf_filename: str) -> Dict:
        """
        Processa um único arquivo PDF
        
        Args:
            pdf_filename: Nome do arquivo PDF
            
        Returns:
            dict: Resultado do processamento
        """
        pdf_path = self.pdf_dir / pdf_filename
        resultado = {
            'arquivo': pdf_filename,
            'status': 'erro',
            'mensagem': '',
            'tempo_processamento': 0
        }
        
        inicio = datetime.now()
        
        try:
            # Verificar se arquivo existe
            if not pdf_path.exists():
                raise FileNotFoundError(f"Arquivo não encontrado: {pdf_filename}")
            
            logger.info(f"Processando: {pdf_filename}")
            
            # Extrair texto
            texto = self.extract_text_from_pdf(pdf_path)
            
            if not texto or len(texto) < 100:
                resultado['status'] = 'erro'
                resultado['mensagem'] = 'Texto extraído muito curto ou vazio'
                self.stats['texto_vazio'] += 1
                return resultado
            
            # Extrair metadados
            metadata = self.extract_metadata(pdf_path, texto)
            
            # Validar conteúdo
            if not metadata.get('validado', False):
                logger.warning(f"Arquivo pode não ser sobre negativação: {pdf_filename}")
                self.stats['nao_validado'] += 1
            
            # Salvar texto extraído
            texto_filename = pdf_filename.replace('.pdf', '.txt')
            texto_path = self.text_dir / texto_filename
            with open(texto_path, 'w', encoding='utf-8') as f:
                f.write(texto)
            
            # Salvar metadados
            metadata_filename = pdf_filename.replace('.pdf', '_metadata.json')
            metadata_path = self.metadata_dir / metadata_filename
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            # Atualizar resultado
            resultado['status'] = 'sucesso'
            resultado['mensagem'] = 'Processado com sucesso'
            resultado['texto_path'] = str(texto_path)
            resultado['metadata_path'] = str(metadata_path)
            resultado['metadata'] = metadata
            
            self.stats['sucesso'] += 1
            logger.info(f"✅ Sucesso: {pdf_filename}")
            
        except Exception as e:
            resultado['status'] = 'erro'
            resultado['mensagem'] = str(e)
            resultado['erro_tipo'] = type(e).__name__
            self.stats['erro'] += 1
            logger.error(f"❌ Erro em {pdf_filename}: {e}")
        
        finally:
            tempo = (datetime.now() - inicio).total_seconds()
            resultado['tempo_processamento'] = tempo
            self.stats['tempo_total'] += tempo
        
        return resultado
    
    def process_all_pdfs(self) -> List[Dict]:
        """
        Processa todos os PDFs no diretório
        
        Returns:
            list: Lista com resultados de cada processamento
        """
        resultados = []
        pdf_files = list(self.pdf_dir.glob('*.pdf'))
        
        if not pdf_files:
            logger.warning(f"Nenhum arquivo PDF encontrado em: {self.pdf_dir}")
            return resultados
        
        self.stats['total_arquivos'] = len(pdf_files)
        logger.info(f"Encontrados {len(pdf_files)} arquivos PDF para processar")
        
        for pdf_file in pdf_files:
            resultado = self.process_single_pdf(pdf_file.name)
            resultados.append(resultado)
        
        return resultados
    
    def test_processing(self) -> None:
        """Testa o processamento e mostra estatísticas detalhadas"""
        print("\n" + "="*80)
        print("🔍 TESTE DO PROCESSADOR DE PDFs")
        print("="*80)
        print(f"📂 Diretório de entrada: {self.pdf_dir}")
        print(f"📂 Diretório de saída: {self.output_dir}")
        print("="*80)
        
        # Processar todos os PDFs
        inicio = datetime.now()
        resultados = self.process_all_pdfs()
        tempo_total = (datetime.now() - inicio).total_seconds()
        
        # Mostrar estatísticas
        print("\n📊 ESTATÍSTICAS DE PROCESSAMENTO")
        print("="*80)
        print(f"Total de arquivos: {self.stats['total_arquivos']}")
        print(f"✅ Processados com sucesso: {self.stats['sucesso']}")
        print(f"❌ Erros no processamento: {self.stats['erro']}")
        print(f"📄 Textos vazios/curtos: {self.stats['texto_vazio']}")
        print(f"⚠️  Não validados como negativação: {self.stats['nao_validado']}")
        print(f"⏱️  Tempo total: {tempo_total:.2f} segundos")
        print(f"⚡ Tempo médio por arquivo: {tempo_total/max(1, self.stats['total_arquivos']):.2f} segundos")
        
        # Detalhes dos processamentos bem-sucedidos
        sucessos = [r for r in resultados if r['status'] == 'sucesso']
        if sucessos:
            print("\n✅ ARQUIVOS PROCESSADOS COM SUCESSO:")
            print("="*80)
            for r in sucessos[:5]:  # Mostrar apenas os 5 primeiros
                meta = r.get('metadata', {})
                print(f"\n📄 {r['arquivo']}")
                print(f"   Páginas: {meta.get('numero_paginas', 'N/A')}")
                print(f"   Tamanho texto: {meta.get('tamanho_texto', 0):,} caracteres")
                print(f"   Processo: {meta.get('numero_processo', 'Não identificado')}")
                print(f"   Relator: {meta.get('relator', 'Não identificado')}")
                print(f"   Data: {meta.get('data_julgamento', 'Não identificada')}")
                print(f"   Validado: {'Sim' if meta.get('validado') else 'Não'}")
                print(f"   Menções negativação: {meta.get('mencoes_negativacao', 0)}")
        
        # Detalhes dos erros
        erros = [r for r in resultados if r['status'] == 'erro']
        if erros:
            print("\n❌ ERROS ENCONTRADOS:")
            print("="*80)
            for r in erros:
                print(f"\n{r['arquivo']}: {r['mensagem']}")
        
        # Salvar relatório completo
        relatorio_path = self.output_dir / 'relatorio_processamento.json'
        relatorio = {
            'timestamp': datetime.now().isoformat(),
            'estatisticas': self.stats,
            'tempo_total': tempo_total,
            'resultados': resultados
        }
        
        with open(relatorio_path, 'w', encoding='utf-8') as f:
            json.dump(relatorio, f, ensure_ascii=False, indent=2)
        
        print(f"\n📊 Relatório completo salvo em: {relatorio_path}")
        print("="*80)


def main():
    """Função principal para testar o processador"""
    processor = PDFProcessor()
    processor.test_processing()


if __name__ == "__main__":
    main()