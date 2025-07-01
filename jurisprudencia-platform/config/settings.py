"""Configuration settings for the jurisprudence platform."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_PDF_DIR = DATA_DIR / "raw_pdfs"
PROCESSED_DIR = DATA_DIR / "processed"
VECTOR_STORE_DIR = DATA_DIR / "vectorstore"

# Create directories if they don't exist
for dir_path in [RAW_PDF_DIR, PROCESSED_DIR, VECTOR_STORE_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

# TJSP Configuration
TJSP_BASE_URL = os.getenv("TJSP_BASE_URL", "https://esaj.tjsp.jus.br")
TJSP_SEARCH_URL = f"{TJSP_BASE_URL}/cjsg/pesquisar.do"
TJSP_PDF_URL = f"{TJSP_BASE_URL}/cjsg/getArquivo.do"

# Scraper settings
SCRAPER_CONFIG = {
    "timeout": 30,
    "max_retries": 3,
    "retry_delay": 2,
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "headless": True,
    "page_size": 10,
}

# Text processing settings
CHUNK_CONFIG = {
    "chunk_size": 1000,
    "chunk_overlap": 200,
    "separators": ["\n\n", "\n", ".", "!", "?", ";", ":", " ", ""],
    "length_function": len,
}

# Embedding settings
EMBEDDING_CONFIG = {
    "model_name": "sentence-transformers/all-MiniLM-L6-v2",
    "device": "cpu",
    "normalize_embeddings": True,
}

# Vector store settings
VECTORSTORE_CONFIG = {
    "collection_name": "jurisprudencia",
    "distance_metric": "cosine",
    "persist_directory": str(VECTOR_STORE_DIR),
}

# LLM settings
LLM_CONFIG = {
    "openai": {
        "model": "gpt-3.5-turbo",
        "temperature": 0.2,
        "max_tokens": 2000,
    },
    "google": {
        "model": "gemini-pro",
        "temperature": 0.2,
        "max_output_tokens": 2000,
    },
}

# Search settings
SEARCH_CONFIG = {
    "top_k": 5,
    "score_threshold": 0.7,
    "rerank": True,
}

# Streamlit settings
STREAMLIT_CONFIG = {
    "page_title": "Plataforma de Jurisprudência",
    "page_icon": "⚖️",
    "layout": "wide",
    "initial_sidebar_state": "expanded",
}

# Logging settings
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "filename": "jurisprudencia.log",
}