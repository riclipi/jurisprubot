"""
Sistema de busca SIMPLES usando embeddings
Sem banco vetorial - apenas arrays em memória
"""

from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from pathlib import Path
import re


class SimpleSearchEngine:
    def __init__(self):
        """Inicializa o motor de busca"""
        print("🚀 Inicializando Sistema de Busca Simples...")
        
        # Carregar modelo de embedding (modelo pequeno e rápido)
        print("📥 Carregando modelo de embedding...")
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        print("✅ Modelo carregado!")
        
        # Estruturas de dados
        self.documents = []  # Lista de documentos
        self.chunks = []     # Lista de chunks de texto
        self.embeddings = None  # Array de embeddings
        self.chunk_metadata = []  # Metadados dos chunks (arquivo origem, etc.)
        
        # Carregar documentos e criar embeddings
        self.load_documents()
        self.create_embeddings()
        
        print(f"✅ Sistema pronto! {len(self.chunks)} chunks indexados")

    def load_documents(self):
        """Lê todos os .txt e divide em chunks"""
        print("📂 Carregando documentos...")
        
        txt_dir = Path("data/processed")
        
        if not txt_dir.exists():
            print("❌ Pasta data/processed não encontrada!")
            return
        
        txt_files = list(txt_dir.glob("*.txt"))
        
        if not txt_files:
            print("❌ Nenhum arquivo .txt encontrado!")
            return
        
        print(f"📄 Encontrados {len(txt_files)} arquivos")
        
        for txt_file in txt_files:
            try:
                # Ler arquivo
                with open(txt_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Dividir em chunks
                chunks = self.split_into_chunks(content, chunk_size=500)
                
                # Adicionar à lista
                for i, chunk in enumerate(chunks):
                    self.chunks.append(chunk)
                    self.chunk_metadata.append({
                        'file': txt_file.name,
                        'chunk_id': i,
                        'file_path': str(txt_file)
                    })
                
                print(f"   ✅ {txt_file.name}: {len(chunks)} chunks")
                
            except Exception as e:
                print(f"   ❌ Erro em {txt_file.name}: {e}")
        
        print(f"📊 Total de chunks: {len(self.chunks)}")

    def split_into_chunks(self, text, chunk_size=500, overlap=50):
        """Divide texto em chunks com sobreposição"""
        # Limpar texto
        text = self.clean_text(text)
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # Se não é o último chunk, tentar quebrar em palavra
            if end < len(text):
                # Procurar espaço ou quebra de linha próxima
                while end > start and text[end] not in [' ', '\n', '.', '!', '?']:
                    end -= 1
                
                # Se não encontrou quebra boa, usar posição original
                if end == start:
                    end = start + chunk_size
            
            chunk = text[start:end].strip()
            
            if chunk:  # Só adicionar chunks não vazios
                chunks.append(chunk)
            
            # Próximo chunk com sobreposição
            start = end - overlap if end < len(text) else end
        
        return chunks

    def clean_text(self, text):
        """Limpa texto básico"""
        # Remover espaços extras
        text = re.sub(r'\s+', ' ', text)
        # Remover caracteres especiais problemáticos
        text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)]', ' ', text)
        return text.strip()

    def create_embeddings(self):
        """Cria embeddings para todos os chunks"""
        if not self.chunks:
            print("❌ Nenhum chunk para processar!")
            return
        
        print("🧠 Criando embeddings...")
        print("   (Isso pode demorar alguns segundos...)")
        
        # Criar embeddings em batch para eficiência
        self.embeddings = self.model.encode(
            self.chunks,
            show_progress_bar=True,
            convert_to_numpy=True
        )
        
        print(f"✅ Embeddings criados: {self.embeddings.shape}")

    def search(self, query, top_k=3):
        """
        Busca semântica na base de documentos
        
        Args:
            query: Pergunta/consulta
            top_k: Número de resultados
            
        Returns:
            list: Lista de resultados ordenados por relevância
        """
        if self.embeddings is None or len(self.chunks) == 0:
            print("❌ Sistema não inicializado!")
            return []
        
        print(f"🔍 Buscando: '{query}'")
        
        # Criar embedding da consulta
        query_embedding = self.model.encode([query], convert_to_numpy=True)
        
        # Calcular similaridade com todos os chunks
        similarities = cosine_similarity(query_embedding, self.embeddings)[0]
        
        # Obter índices dos top_k mais similares
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        # Preparar resultados
        results = []
        for i, idx in enumerate(top_indices):
            result = {
                'rank': i + 1,
                'score': float(similarities[idx]),
                'text': self.chunks[idx],
                'metadata': self.chunk_metadata[idx],
                'preview': self.chunks[idx][:200] + "..." if len(self.chunks[idx]) > 200 else self.chunks[idx]
            }
            results.append(result)
        
        return results

    def test_search(self):
        """Testa o sistema com algumas consultas"""
        print("\n" + "=" * 60)
        print("🧪 TESTE DO SISTEMA DE BUSCA")
        print("=" * 60)
        
        # Consultas de teste
        test_queries = [
            "negativação indevida banco",
            "dano moral indenização",
            "serasa spc nome",
            "valor da condenação"
        ]
        
        for query in test_queries:
            print(f"\n🔍 CONSULTA: '{query}'")
            print("-" * 40)
            
            results = self.search(query, top_k=3)
            
            if results:
                for result in results:
                    print(f"\n📄 #{result['rank']} - Score: {result['score']:.3f}")
                    print(f"📁 Arquivo: {result['metadata']['file']}")
                    print(f"📝 Trecho: {result['preview']}")
            else:
                print("❌ Nenhum resultado encontrado")
        
        print("\n" + "=" * 60)

    def interactive_search(self):
        """Interface interativa de busca"""
        print("\n" + "=" * 60)
        print("🔍 BUSCA INTERATIVA")
        print("=" * 60)
        print("Digite sua consulta (ou 'quit' para sair):")
        
        while True:
            query = input("\n🔍 Consulta: ").strip()
            
            if query.lower() in ['quit', 'sair', 'exit']:
                print("👋 Até logo!")
                break
            
            if not query:
                continue
            
            results = self.search(query, top_k=3)
            
            if results:
                print(f"\n📊 Encontrados {len(results)} resultados:")
                for result in results:
                    print(f"\n📄 #{result['rank']} - Score: {result['score']:.3f}")
                    print(f"📁 {result['metadata']['file']}")
                    print(f"📝 {result['preview']}")
            else:
                print("❌ Nenhum resultado encontrado")


def main():
    """Função principal"""
    try:
        # Criar sistema de busca
        search_engine = SimpleSearchEngine()
        
        # Executar teste automático
        search_engine.test_search()
        
        # Oferecer busca interativa
        print("\n🤖 Quer fazer uma busca personalizada? (y/n)")
        choice = input().strip().lower()
        
        if choice in ['y', 'yes', 'sim', 's']:
            search_engine.interactive_search()
        
    except Exception as e:
        print(f"❌ Erro: {e}")


if __name__ == "__main__":
    main()