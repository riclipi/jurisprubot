#!/usr/bin/env python3
"""
Script para executar a API FastAPI
"""

import os
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent))

import uvicorn
from src.api.main import app

if __name__ == "__main__":
    # Configurações
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    workers = int(os.getenv("API_WORKERS", "4"))
    
    print(f"""
    ╔══════════════════════════════════════════╗
    ║        Jurisprudência API v1.0.0         ║
    ╚══════════════════════════════════════════╝
    
    Servidor: http://{host}:{port}
    Documentação: http://{host}:{port}/docs
    Alternativa: http://{host}:{port}/redoc
    
    Pressione CTRL+C para parar
    """)
    
    # Executar servidor
    if workers > 1:
        # Produção com múltiplos workers
        uvicorn.run(
            "src.api.main:app",
            host=host,
            port=port,
            workers=workers,
            log_level="info"
        )
    else:
        # Desenvolvimento com reload
        uvicorn.run(
            "src.api.main:app",
            host=host,
            port=port,
            reload=True,
            log_level="debug"
        )