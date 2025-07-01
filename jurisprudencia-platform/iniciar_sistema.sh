#!/bin/bash
echo "🚀 INICIANDO SISTEMA DE JURISPRUDÊNCIA..."
echo "====================================="
echo ""
echo "📌 A interface web vai abrir em:"
echo "   http://localhost:8501"
echo ""
echo "⏳ Aguarde alguns segundos..."
echo ""

# Iniciar Streamlit
cd /workspaces/jurisprubot/jurisprudencia-platform
streamlit run src/interface/streamlit_app.py