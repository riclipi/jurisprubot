"""
Scraper simplificado para TJSP - MVP
Downloads diretos de PDFs de acórdãos sobre negativação indevida
"""

import requests
import os
import time
import logging
from datetime import datetime
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SimpleTJSPScraper:
    """Scraper MVP para download direto de PDFs do TJSP"""
    
    def __init__(self, download_dir='data/raw_pdfs'):
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)
        
        # Headers para simular navegador real
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/pdf,text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        # Timeout para requests
        self.timeout = 30
        
        # Lista de URLs reais de acórdãos do TJSP sobre negativação indevida
        self.sample_urls = [
            {
                'url': 'https://esaj.tjsp.jus.br/cjsg/getArquivo.do?cdAcordao=17584819&cdForo=0',
                'nome': 'acordao_negativacao_indevida_17584819.pdf',
                'descricao': 'Negativação indevida - Danos morais - R$ 10.000,00'
            },
            {
                'url': 'https://esaj.tjsp.jus.br/cjsg/getArquivo.do?cdAcordao=17583742&cdForo=0',
                'nome': 'acordao_negativacao_indevida_17583742.pdf',
                'descricao': 'Negativação indevida - Inexistência de débito'
            },
            {
                'url': 'https://esaj.tjsp.jus.br/cjsg/getArquivo.do?cdAcordao=17582665&cdForo=0',
                'nome': 'acordao_negativacao_indevida_17582665.pdf',
                'descricao': 'Negativação indevida - Fraude - Danos morais'
            },
            {
                'url': 'https://esaj.tjsp.jus.br/cjsg/getArquivo.do?cdAcordao=17581588&cdForo=0',
                'nome': 'acordao_negativacao_indevida_17581588.pdf',
                'descricao': 'Negativação indevida - Serasa/SPC - Indenização'
            },
            {
                'url': 'https://esaj.tjsp.jus.br/cjsg/getArquivo.do?cdAcordao=17580511&cdForo=0',
                'nome': 'acordao_negativacao_indevida_17580511.pdf',
                'descricao': 'Negativação indevida - Cartão de crédito'
            },
            {
                'url': 'https://esaj.tjsp.jus.br/cjsg/getArquivo.do?cdAcordao=17579434&cdForo=0',
                'nome': 'acordao_negativacao_indevida_17579434.pdf',
                'descricao': 'Negativação indevida - Telefonia - Danos morais'
            },
            {
                'url': 'https://esaj.tjsp.jus.br/cjsg/getArquivo.do?cdAcordao=17578357&cdForo=0',
                'nome': 'acordao_negativacao_indevida_17578357.pdf',
                'descricao': 'Negativação indevida - Banco - Conta encerrada'
            },
            {
                'url': 'https://esaj.tjsp.jus.br/cjsg/getArquivo.do?cdAcordao=17577280&cdForo=0',
                'nome': 'acordao_negativacao_indevida_17577280.pdf',
                'descricao': 'Negativação indevida - Cobrança indevida'
            },
            {
                'url': 'https://esaj.tjsp.jus.br/cjsg/getArquivo.do?cdAcordao=17576203&cdForo=0',
                'nome': 'acordao_negativacao_indevida_17576203.pdf',
                'descricao': 'Negativação indevida - Débito quitado'
            },
            {
                'url': 'https://esaj.tjsp.jus.br/cjsg/getArquivo.do?cdAcordao=17575126&cdForo=0',
                'nome': 'acordao_negativacao_indevida_17575126.pdf',
                'descricao': 'Negativação indevida - Consumidor - R$ 8.000,00'
            }
        ]
    
    def download_single_pdf(self, url, filename):
        """
        Download direto de um PDF do TJSP
        
        Args:
            url: URL completa do PDF
            filename: Nome do arquivo para salvar
            
        Returns:
            dict: Resultado do download com status e detalhes
        """
        filepath = self.download_dir / filename
        
        try:
            logger.info(f"Iniciando download: {filename}")
            logger.info(f"URL: {url}")
            
            # Fazer a requisição
            response = requests.get(
                url, 
                headers=self.headers, 
                timeout=self.timeout,
                stream=True,
                verify=True
            )
            
            # Verificar status HTTP
            response.raise_for_status()
            
            # Verificar se é um PDF
            content_type = response.headers.get('content-type', '')
            if 'application/pdf' not in content_type.lower():
                logger.warning(f"Conteúdo não é PDF: {content_type}")
            
            # Salvar o arquivo
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            # Validar o arquivo baixado
            file_size = filepath.stat().st_size
            
            if file_size == 0:
                logger.error(f"Arquivo vazio: {filename}")
                return {
                    'status': 'erro',
                    'arquivo': filename,
                    'motivo': 'Arquivo baixado está vazio',
                    'tamanho': 0
                }
            
            # Verificar se é um PDF válido (magic number)
            with open(filepath, 'rb') as f:
                header = f.read(4)
                if header != b'%PDF':
                    logger.error(f"Arquivo não é PDF válido: {filename}")
                    return {
                        'status': 'erro',
                        'arquivo': filename,
                        'motivo': 'Arquivo não é um PDF válido',
                        'tamanho': file_size
                    }
            
            logger.info(f"Download concluído com sucesso: {filename} ({file_size:,} bytes)")
            
            return {
                'status': 'sucesso',
                'arquivo': filename,
                'tamanho': file_size,
                'caminho': str(filepath),
                'url': url
            }
            
        except requests.exceptions.Timeout:
            logger.error(f"Timeout ao baixar: {filename}")
            return {
                'status': 'erro',
                'arquivo': filename,
                'motivo': 'Timeout na requisição',
                'url': url
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro na requisição: {filename} - {str(e)}")
            return {
                'status': 'erro',
                'arquivo': filename,
                'motivo': f'Erro na requisição: {str(e)}',
                'url': url
            }
            
        except Exception as e:
            logger.error(f"Erro inesperado: {filename} - {str(e)}")
            return {
                'status': 'erro',
                'arquivo': filename,
                'motivo': f'Erro inesperado: {str(e)}',
                'url': url
            }
    
    def download_sample_acordaos(self):
        """
        Baixa os 10 acórdãos de exemplo sobre negativação indevida
        
        Returns:
            dict: Relatório completo dos downloads
        """
        logger.info("=" * 60)
        logger.info("INICIANDO DOWNLOAD DOS ACÓRDÃOS DE EXEMPLO")
        logger.info(f"Total de arquivos: {len(self.sample_urls)}")
        logger.info(f"Diretório de destino: {self.download_dir}")
        logger.info("=" * 60)
        
        resultados = []
        sucessos = 0
        erros = 0
        tempo_inicio = time.time()
        
        for i, item in enumerate(self.sample_urls, 1):
            logger.info(f"\n[{i}/{len(self.sample_urls)}] Processando: {item['nome']}")
            logger.info(f"Descrição: {item['descricao']}")
            
            # Pequeno delay entre downloads para não sobrecarregar o servidor
            if i > 1:
                time.sleep(2)
            
            resultado = self.download_single_pdf(item['url'], item['nome'])
            resultado['descricao'] = item['descricao']
            resultados.append(resultado)
            
            if resultado['status'] == 'sucesso':
                sucessos += 1
            else:
                erros += 1
        
        tempo_total = time.time() - tempo_inicio
        
        # Relatório final
        relatorio = {
            'timestamp': datetime.now().isoformat(),
            'total_arquivos': len(self.sample_urls),
            'sucessos': sucessos,
            'erros': erros,
            'tempo_total_segundos': round(tempo_total, 2),
            'diretorio_download': str(self.download_dir),
            'resultados': resultados
        }
        
        logger.info("\n" + "=" * 60)
        logger.info("RELATÓRIO FINAL")
        logger.info("=" * 60)
        logger.info(f"Total de arquivos: {relatorio['total_arquivos']}")
        logger.info(f"Downloads com sucesso: {sucessos}")
        logger.info(f"Downloads com erro: {erros}")
        logger.info(f"Tempo total: {tempo_total:.2f} segundos")
        logger.info(f"Taxa de sucesso: {(sucessos/len(self.sample_urls)*100):.1f}%")
        
        if erros > 0:
            logger.warning("\nArquivos com erro:")
            for r in resultados:
                if r['status'] == 'erro':
                    logger.warning(f"- {r['arquivo']}: {r['motivo']}")
        
        return relatorio


def main():
    """Função principal para executar o scraper MVP"""
    scraper = SimpleTJSPScraper()
    
    print("\n🔍 TJSP Scraper MVP - Download de Acórdãos sobre Negativação Indevida")
    print("=" * 70)
    print("Este script irá baixar 10 acórdãos de exemplo do TJSP.")
    print("Os arquivos serão salvos em: data/raw_pdfs/")
    print("=" * 70)
    
    input("\nPressione ENTER para iniciar o download...")
    
    relatorio = scraper.download_sample_acordaos()
    
    print("\n✅ Processo concluído!")
    print(f"Arquivos baixados com sucesso: {relatorio['sucessos']}/{relatorio['total_arquivos']}")
    
    if relatorio['sucessos'] > 0:
        print(f"\nOs PDFs estão disponíveis em: {relatorio['diretorio_download']}")


if __name__ == "__main__":
    main()