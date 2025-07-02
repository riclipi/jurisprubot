"""
Módulo de integração MCP (Model Context Protocol)
Funcionalidades extras independentes para gestão de documentos
"""

from .document_manager import MCPDocumentManager
from .file_organizer import FileOrganizer
from .pdf_processor import PDFProcessor

__all__ = ['MCPDocumentManager', 'FileOrganizer', 'PDFProcessor']