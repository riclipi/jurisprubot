"""Text chunking module for splitting documents into manageable pieces."""

import logging
from typing import List, Dict, Optional
import re

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document

from config.settings import CHUNK_CONFIG

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TextChunker:
    """Split text documents into chunks for embedding and retrieval."""
    
    def __init__(self, chunk_size: Optional[int] = None, chunk_overlap: Optional[int] = None):
        """
        Initialize the text chunker.
        
        Args:
            chunk_size: Size of text chunks (default from config)
            chunk_overlap: Overlap between chunks (default from config)
        """
        self.chunk_size = chunk_size or CHUNK_CONFIG['chunk_size']
        self.chunk_overlap = chunk_overlap or CHUNK_CONFIG['chunk_overlap']
        self.separators = CHUNK_CONFIG['separators']
        
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=self.separators,
            length_function=len,
        )
    
    def chunk_text(self, text: str, metadata: Optional[Dict] = None) -> List[Document]:
        """
        Split text into chunks with metadata.
        
        Args:
            text: Text to split
            metadata: Metadata to attach to each chunk
            
        Returns:
            List of Document objects with chunked text
        """
        if not text:
            return []
        
        # Create base metadata
        base_metadata = metadata or {}
        
        # Split text
        chunks = self.splitter.split_text(text)
        
        # Create documents with metadata
        documents = []
        for i, chunk in enumerate(chunks):
            chunk_metadata = base_metadata.copy()
            chunk_metadata.update({
                'chunk_id': i,
                'chunk_size': len(chunk),
                'total_chunks': len(chunks),
            })
            
            # Extract chunk context (first sentence or title)
            context = self._extract_chunk_context(chunk)
            if context:
                chunk_metadata['context'] = context
            
            doc = Document(
                page_content=chunk,
                metadata=chunk_metadata
            )
            documents.append(doc)
        
        logger.info(f"Created {len(documents)} chunks from text of length {len(text)}")
        return documents
    
    def _extract_chunk_context(self, chunk: str) -> Optional[str]:
        """
        Extract context information from a chunk.
        
        Args:
            chunk: Text chunk
            
        Returns:
            Context string or None
        """
        # Try to find section headers
        header_patterns = [
            r'^#+\s+(.+)$',  # Markdown headers
            r'^([A-Z][A-Z\s]+):',  # UPPERCASE headers
            r'^(\d+\.?\s+[A-Z].+)$',  # Numbered sections
            r'^([A-Z][a-z]+(?: [A-Z][a-z]+)*):',  # Title case headers
        ]
        
        lines = chunk.split('\n')
        for line in lines[:5]:  # Check first 5 lines
            line = line.strip()
            for pattern in header_patterns:
                match = re.match(pattern, line)
                if match:
                    return match.group(1).strip()
        
        # If no header, return first sentence
        sentences = re.split(r'[.!?]\s+', chunk)
        if sentences:
            first_sentence = sentences[0].strip()
            if len(first_sentence) > 20 and len(first_sentence) < 200:
                return first_sentence
        
        return None
    
    def chunk_documents(self, documents: List[Dict]) -> List[Document]:
        """
        Chunk multiple documents.
        
        Args:
            documents: List of document dictionaries with 'cleaned_text' and 'metadata'
            
        Returns:
            List of all chunks from all documents
        """
        all_chunks = []
        
        for doc in documents:
            if 'cleaned_text' not in doc:
                logger.warning(f"Document missing cleaned_text: {doc.get('filename', 'unknown')}")
                continue
            
            # Prepare metadata
            metadata = doc.get('metadata', {}).copy()
            metadata['source_file'] = doc.get('filename', 'unknown')
            
            # Chunk the document
            chunks = self.chunk_text(doc['cleaned_text'], metadata)
            all_chunks.extend(chunks)
        
        logger.info(f"Created {len(all_chunks)} total chunks from {len(documents)} documents")
        return all_chunks
    
    def smart_chunk_by_sections(self, text: str, metadata: Optional[Dict] = None) -> List[Document]:
        """
        Smart chunking that tries to preserve document sections.
        
        Args:
            text: Text to split
            metadata: Metadata to attach to each chunk
            
        Returns:
            List of Document objects with chunked text
        """
        # Identify section boundaries
        section_patterns = [
            r'\n\n#+\s+',  # Markdown headers
            r'\n\n[A-Z][A-Z\s]+:\n',  # UPPERCASE headers
            r'\n\n\d+\.?\s+[A-Z]',  # Numbered sections
            r'\n\nACÓRDÃO\n',  # Common legal document sections
            r'\n\nRELATÓRIO\n',
            r'\n\nVOTO\n',
            r'\n\nDISPOSITIVO\n',
            r'\n\nEMENTA\n',
        ]
        
        # Combine patterns
        combined_pattern = '|'.join(f'({p})' for p in section_patterns)
        
        # Split by sections
        sections = re.split(combined_pattern, text)
        
        # Clean sections and create chunks
        documents = []
        current_section = ""
        section_num = 0
        
        for part in sections:
            if part and part.strip():
                if re.match(combined_pattern, '\n\n' + part):
                    # This is a section header
                    if current_section:
                        # Chunk the previous section
                        section_docs = self.chunk_text(current_section, metadata)
                        for doc in section_docs:
                            doc.metadata['section_num'] = section_num
                        documents.extend(section_docs)
                        section_num += 1
                    current_section = part
                else:
                    # This is section content
                    current_section += part
        
        # Don't forget the last section
        if current_section:
            section_docs = self.chunk_text(current_section, metadata)
            for doc in section_docs:
                doc.metadata['section_num'] = section_num
            documents.extend(section_docs)
        
        # If no sections found, fall back to regular chunking
        if not documents:
            return self.chunk_text(text, metadata)
        
        return documents
    
    def get_chunk_statistics(self, documents: List[Document]) -> Dict:
        """
        Get statistics about the chunks.
        
        Args:
            documents: List of Document chunks
            
        Returns:
            Dictionary with statistics
        """
        if not documents:
            return {}
        
        chunk_sizes = [len(doc.page_content) for doc in documents]
        
        stats = {
            'total_chunks': len(documents),
            'total_characters': sum(chunk_sizes),
            'avg_chunk_size': sum(chunk_sizes) / len(chunk_sizes),
            'min_chunk_size': min(chunk_sizes),
            'max_chunk_size': max(chunk_sizes),
            'unique_sources': len(set(doc.metadata.get('source_file', '') for doc in documents)),
        }
        
        return stats


if __name__ == "__main__":
    # Example usage
    chunker = TextChunker()
    
    # Example text
    sample_text = """
    ACÓRDÃO
    
    Vistos, relatados e discutidos estes autos de Apelação Cível nº 1234567-89.2023.8.26.0100,
    da Comarca de São Paulo, em que é apelante JOÃO DA SILVA, é apelado MARIA DOS SANTOS.
    
    RELATÓRIO
    
    Trata-se de ação de cobrança ajuizada por João da Silva em face de Maria dos Santos,
    alegando inadimplemento contratual referente a contrato de compra e venda de imóvel.
    
    O autor alega que firmou contrato com a ré em 01/01/2023, no valor de R$ 500.000,00,
    tendo a ré pago apenas R$ 100.000,00 do valor acordado.
    
    VOTO
    
    O recurso comporta provimento.
    
    Com efeito, restou demonstrado nos autos que as partes firmaram contrato de compra e venda,
    devidamente assinado e com firma reconhecida, estabelecendo as condições de pagamento.
    """
    
    # Chunk the text
    chunks = chunker.smart_chunk_by_sections(
        sample_text,
        metadata={'case_number': '1234567-89.2023.8.26.0100'}
    )
    
    # Print results
    print(f"Created {len(chunks)} chunks")
    for i, chunk in enumerate(chunks[:3]):
        print(f"\nChunk {i}:")
        print(f"Content: {chunk.page_content[:100]}...")
        print(f"Metadata: {chunk.metadata}")