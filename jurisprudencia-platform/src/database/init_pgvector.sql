-- Script para inicializar pgvector no PostgreSQL
-- Execute este script após criar o banco de dados

-- Criar extensão pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- Criar tabela de embeddings com coluna vetorial
CREATE TABLE IF NOT EXISTS embeddings_vector (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    chunk_id UUID NOT NULL REFERENCES text_chunks(id) ON DELETE CASCADE,
    embedding vector(384),  -- Dimensão para all-MiniLM-L6-v2
    model_name VARCHAR(100) DEFAULT 'all-MiniLM-L6-v2',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Índices
    CONSTRAINT embeddings_vector_chunk_unique UNIQUE (chunk_id)
);

-- Criar índice HNSW para busca aproximada rápida
CREATE INDEX IF NOT EXISTS embeddings_vector_embedding_idx 
ON embeddings_vector 
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- Criar índice para case_id
CREATE INDEX IF NOT EXISTS embeddings_vector_case_idx 
ON embeddings_vector(case_id);

-- Função para busca por similaridade
CREATE OR REPLACE FUNCTION search_similar_embeddings(
    query_embedding vector(384),
    limit_count INT DEFAULT 10,
    similarity_threshold FLOAT DEFAULT 0.7
)
RETURNS TABLE (
    embedding_id UUID,
    case_id UUID,
    chunk_id UUID,
    similarity FLOAT,
    case_number VARCHAR(50),
    chunk_text TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        ev.id as embedding_id,
        ev.case_id,
        ev.chunk_id,
        1 - (ev.embedding <=> query_embedding) as similarity,
        c.case_number,
        tc.chunk_text
    FROM embeddings_vector ev
    JOIN cases c ON ev.case_id = c.id
    JOIN text_chunks tc ON ev.chunk_id = tc.id
    WHERE 1 - (ev.embedding <=> query_embedding) >= similarity_threshold
    ORDER BY ev.embedding <=> query_embedding
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;

-- Função para busca híbrida (semântica + palavras-chave)
CREATE OR REPLACE FUNCTION hybrid_search(
    query_embedding vector(384),
    keywords TEXT[],
    limit_count INT DEFAULT 20,
    semantic_weight FLOAT DEFAULT 0.7
)
RETURNS TABLE (
    case_id UUID,
    case_number VARCHAR(50),
    chunk_id UUID,
    chunk_text TEXT,
    semantic_score FLOAT,
    keyword_score FLOAT,
    final_score FLOAT
) AS $$
BEGIN
    RETURN QUERY
    WITH semantic_results AS (
        -- Busca semântica
        SELECT 
            ev.case_id,
            ev.chunk_id,
            1 - (ev.embedding <=> query_embedding) as semantic_score
        FROM embeddings_vector ev
        ORDER BY ev.embedding <=> query_embedding
        LIMIT limit_count * 2
    ),
    keyword_results AS (
        -- Busca por palavras-chave
        SELECT 
            d.case_id,
            tc.id as chunk_id,
            COUNT(DISTINCT keyword) / ARRAY_LENGTH(keywords, 1)::FLOAT as keyword_score
        FROM documents d
        JOIN text_chunks tc ON tc.document_id = d.id
        CROSS JOIN UNNEST(keywords) as keyword
        WHERE LOWER(tc.chunk_text) LIKE '%' || LOWER(keyword) || '%'
        GROUP BY d.case_id, tc.id
        HAVING COUNT(DISTINCT keyword) > 0
        ORDER BY keyword_score DESC
        LIMIT limit_count * 2
    )
    -- Combinar resultados
    SELECT DISTINCT
        COALESCE(sr.case_id, kr.case_id) as case_id,
        c.case_number,
        COALESCE(sr.chunk_id, kr.chunk_id) as chunk_id,
        tc.chunk_text,
        COALESCE(sr.semantic_score, 0) as semantic_score,
        COALESCE(kr.keyword_score, 0) as keyword_score,
        (COALESCE(sr.semantic_score, 0) * semantic_weight + 
         COALESCE(kr.keyword_score, 0) * (1 - semantic_weight)) as final_score
    FROM semantic_results sr
    FULL OUTER JOIN keyword_results kr 
        ON sr.case_id = kr.case_id AND sr.chunk_id = kr.chunk_id
    JOIN cases c ON c.id = COALESCE(sr.case_id, kr.case_id)
    JOIN text_chunks tc ON tc.id = COALESCE(sr.chunk_id, kr.chunk_id)
    ORDER BY final_score DESC
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;

-- Estatísticas de embeddings
CREATE OR REPLACE VIEW embedding_statistics AS
SELECT 
    COUNT(*) as total_embeddings,
    COUNT(DISTINCT case_id) as unique_cases,
    COUNT(DISTINCT chunk_id) as unique_chunks,
    AVG(ARRAY_LENGTH(embedding::float[], 1)) as avg_dimension,
    MIN(created_at) as oldest_embedding,
    MAX(created_at) as newest_embedding
FROM embeddings_vector;

-- Trigger para manter consistência
CREATE OR REPLACE FUNCTION cleanup_orphan_embeddings()
RETURNS TRIGGER AS $$
BEGIN
    -- Remover embeddings órfãos quando chunk é deletado
    DELETE FROM embeddings_vector 
    WHERE chunk_id = OLD.id;
    
    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER cleanup_embeddings_on_chunk_delete
BEFORE DELETE ON text_chunks
FOR EACH ROW
EXECUTE FUNCTION cleanup_orphan_embeddings();