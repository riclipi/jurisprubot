"""Embeddings module for creating and managing document embeddings."""

import logging
from typing import List, Dict, Optional, Union
from pathlib import Path
import numpy as np

from sentence_transformers import SentenceTransformer
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document
import chromadb
from chromadb.config import Settings

from config.settings import EMBEDDING_CONFIG, VECTORSTORE_CONFIG, VECTOR_STORE_DIR

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmbeddingsManager:
    """Manage document embeddings and vector store operations."""
    
    def __init__(self, model_name: Optional[str] = None):
        """
        Initialize the embeddings manager.
        
        Args:
            model_name: Name of the embedding model (default from config)
        """
        self.model_name = model_name or EMBEDDING_CONFIG['model_name']
        self.device = EMBEDDING_CONFIG['device']
        
        # Initialize embedding model
        self.embeddings = HuggingFaceEmbeddings(
            model_name=self.model_name,
            model_kwargs={'device': self.device},
            encode_kwargs={'normalize_embeddings': EMBEDDING_CONFIG['normalize_embeddings']}
        )
        
        # Initialize ChromaDB client
        self.chroma_client = chromadb.PersistentClient(
            path=str(VECTOR_STORE_DIR),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Get or create collection
        self.collection_name = VECTORSTORE_CONFIG['collection_name']
        self.collection = self._get_or_create_collection()
        
    def _get_or_create_collection(self):
        """Get or create ChromaDB collection."""
        try:
            collection = self.chroma_client.get_collection(
                name=self.collection_name,
                embedding_function=self.embeddings
            )
            logger.info(f"Using existing collection: {self.collection_name}")
        except:
            collection = self.chroma_client.create_collection(
                name=self.collection_name,
                embedding_function=self.embeddings,
                metadata={"hnsw:space": VECTORSTORE_CONFIG['distance_metric']}
            )
            logger.info(f"Created new collection: {self.collection_name}")
        
        return collection
    
    def embed_documents(self, documents: List[Document]) -> List[List[float]]:
        """
        Create embeddings for a list of documents.
        
        Args:
            documents: List of Document objects
            
        Returns:
            List of embedding vectors
        """
        texts = [doc.page_content for doc in documents]
        embeddings = self.embeddings.embed_documents(texts)
        logger.info(f"Created embeddings for {len(documents)} documents")
        return embeddings
    
    def embed_query(self, query: str) -> List[float]:
        """
        Create embedding for a query string.
        
        Args:
            query: Query text
            
        Returns:
            Embedding vector
        """
        return self.embeddings.embed_query(query)
    
    def add_documents(self, documents: List[Document], batch_size: int = 100) -> List[str]:
        """
        Add documents to the vector store.
        
        Args:
            documents: List of Document objects
            batch_size: Number of documents to process at once
            
        Returns:
            List of document IDs
        """
        all_ids = []
        
        # Process in batches
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i+batch_size]
            
            # Prepare data for ChromaDB
            texts = [doc.page_content for doc in batch]
            metadatas = [doc.metadata for doc in batch]
            ids = [f"doc_{i+j}" for j in range(len(batch))]
            
            # Add to collection
            self.collection.add(
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )
            
            all_ids.extend(ids)
            logger.info(f"Added batch {i//batch_size + 1} ({len(batch)} documents)")
        
        logger.info(f"Added total of {len(all_ids)} documents to vector store")
        return all_ids
    
    def search(self, query: str, k: int = 5, filter_dict: Optional[Dict] = None) -> List[Dict]:
        """
        Search for similar documents.
        
        Args:
            query: Search query
            k: Number of results to return
            filter_dict: Metadata filters
            
        Returns:
            List of search results with documents and scores
        """
        # Perform search
        results = self.collection.query(
            query_texts=[query],
            n_results=k,
            where=filter_dict
        )
        
        # Format results
        formatted_results = []
        if results['documents'] and results['documents'][0]:
            for i, doc in enumerate(results['documents'][0]):
                result = {
                    'content': doc,
                    'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                    'distance': results['distances'][0][i] if results['distances'] else None,
                    'id': results['ids'][0][i] if results['ids'] else None
                }
                formatted_results.append(result)
        
        logger.info(f"Found {len(formatted_results)} results for query: {query[:50]}...")
        return formatted_results
    
    def similarity_search_with_score(self, query: str, k: int = 5, 
                                   score_threshold: Optional[float] = None) -> List[tuple]:
        """
        Search with similarity scores.
        
        Args:
            query: Search query
            k: Number of results
            score_threshold: Minimum similarity score
            
        Returns:
            List of (document, score) tuples
        """
        results = self.search(query, k)
        
        # Convert to tuples with documents
        doc_score_pairs = []
        for result in results:
            # Convert distance to similarity score (for cosine distance)
            score = 1 - (result['distance'] or 0)
            
            # Apply threshold if specified
            if score_threshold is None or score >= score_threshold:
                doc = Document(
                    page_content=result['content'],
                    metadata=result['metadata']
                )
                doc_score_pairs.append((doc, score))
        
        return doc_score_pairs
    
    def delete_collection(self):
        """Delete the current collection."""
        self.chroma_client.delete_collection(self.collection_name)
        logger.info(f"Deleted collection: {self.collection_name}")
        
    def get_collection_stats(self) -> Dict:
        """Get statistics about the collection."""
        count = self.collection.count()
        
        stats = {
            'collection_name': self.collection_name,
            'document_count': count,
            'embedding_model': self.model_name,
            'vector_dimension': len(self.embed_query("test")) if count > 0 else 0,
        }
        
        return stats
    
    def update_document(self, doc_id: str, document: Document):
        """
        Update a document in the vector store.
        
        Args:
            doc_id: Document ID
            document: New document content
        """
        self.collection.update(
            ids=[doc_id],
            documents=[document.page_content],
            metadatas=[document.metadata]
        )
        logger.info(f"Updated document: {doc_id}")
    
    def get_document(self, doc_id: str) -> Optional[Document]:
        """
        Retrieve a document by ID.
        
        Args:
            doc_id: Document ID
            
        Returns:
            Document or None if not found
        """
        results = self.collection.get(ids=[doc_id])
        
        if results['documents'] and results['documents'][0]:
            return Document(
                page_content=results['documents'][0],
                metadata=results['metadatas'][0] if results['metadatas'] else {}
            )
        
        return None
    
    def bulk_similarity_search(self, queries: List[str], k: int = 5) -> Dict[str, List[Dict]]:
        """
        Perform similarity search for multiple queries.
        
        Args:
            queries: List of query strings
            k: Number of results per query
            
        Returns:
            Dictionary mapping queries to results
        """
        results_dict = {}
        
        for query in queries:
            results = self.search(query, k)
            results_dict[query] = results
        
        return results_dict


if __name__ == "__main__":
    # Example usage
    manager = EmbeddingsManager()
    
    # Create sample documents
    sample_docs = [
        Document(
            page_content="Contrato de compra e venda de imóvel residencial.",
            metadata={"case_number": "123456", "type": "contract"}
        ),
        Document(
            page_content="Ação de cobrança por inadimplemento contratual.",
            metadata={"case_number": "789012", "type": "lawsuit"}
        )
    ]
    
    # Add documents
    ids = manager.add_documents(sample_docs)
    print(f"Added documents with IDs: {ids}")
    
    # Search
    results = manager.search("contrato de compra", k=2)
    for result in results:
        print(f"Found: {result['content'][:50]}... (score: {result['distance']})")
    
    # Get stats
    stats = manager.get_collection_stats()
    print(f"Collection stats: {stats}")