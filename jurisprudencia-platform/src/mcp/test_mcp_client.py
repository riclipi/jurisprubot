#!/usr/bin/env python3
"""
Script de teste para o MCP Client
Demonstra como usar o wrapper para trabalhar com documentos jurídicos
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp_client import JurisprudenciaMCPClient
import json

def test_mcp_client():
    print("=== Teste do JurisprudenciaMCPClient ===\n")
    
    # Inicializar cliente
    client = JurisprudenciaMCPClient()
    print(f"✓ Cliente inicializado")
    print(f"  - Base path: {client.base_path}")
    print(f"  - Docs path: {client.docs_path}\n")
    
    # Exemplo de acórdão para teste
    sample_acordao = """
    ACÓRDÃO - Processo: 1234567-89.2023.8.26.0100
    
    APELAÇÃO CÍVEL - RESPONSABILIDADE CIVIL - DANO MORAL
    
    Trata-se de ação de indenização por danos morais decorrente de negativação indevida.
    O autor teve seu nome incluído nos órgãos de proteção ao crédito por dívida já quitada.
    
    Valor da causa: R$ 10.000,00
    Indenização arbitrada: R$ 5.000,00
    
    Aplicação do Código de Defesa do Consumidor.
    Caracterizada a responsabilidade civil da ré.
    Presentes os requisitos: conduta ilícita, nexo de causalidade e dano.
    
    RECURSO PARCIALMENTE PROVIDO.
    """
    
    # Teste 1: Salvar documento
    print("1. Salvando documento de teste...")
    filepath = client.save_document(sample_acordao, "acordao_teste_001.txt")
    print(f"   ✓ Documento salvo em: {filepath}\n")
    
    # Teste 2: Listar documentos
    print("2. Listando documentos disponíveis...")
    docs = client.list_documents()
    print(f"   ✓ Encontrados {len(docs)} documentos:")
    for doc in docs[:5]:  # Mostrar apenas os 5 primeiros
        print(f"     - {doc}")
    if len(docs) > 5:
        print(f"     ... e mais {len(docs) - 5} documentos\n")
    else:
        print()
    
    # Teste 3: Buscar documentos
    print("3. Buscando por 'dano moral'...")
    results = client.search_documents("dano moral")
    print(f"   ✓ Encontrados {len(results)} resultados:")
    for i, result in enumerate(results[:3], 1):
        print(f"\n   Resultado {i}:")
        print(f"   - Arquivo: {result['filename']}")
        print(f"   - Relevância: {result['relevance']}")
        print(f"   - Preview: {result['content'][:100]}...")
    print()
    
    # Teste 4: Processar documento jurídico
    print("4. Processando documento jurídico...")
    analysis = client.process_legal_document(sample_acordao)
    print("   ✓ Análise completa:")
    print(f"   - Tipo: {analysis['document_type']}")
    print(f"   - Entidades encontradas: {len(analysis['key_entities'])}")
    for entity in analysis['key_entities']:
        print(f"     • {entity}")
    print(f"   - Conceitos jurídicos: {len(analysis['legal_concepts'])}")
    for concept in analysis['legal_concepts']:
        print(f"     • {concept}")
    print()
    
    # Teste 5: Extração avançada
    print("5. Testando extração de entidades...")
    entities = client.extract_entities(sample_acordao)
    print(f"   ✓ Entidades extraídas: {entities}\n")
    
    # Teste 6: Conceitos jurídicos
    print("6. Testando extração de conceitos...")
    concepts = client.extract_legal_concepts(sample_acordao)
    print(f"   ✓ Conceitos identificados: {concepts}\n")
    
    print("=== Teste concluído com sucesso! ===")
    
    # Salvar relatório de teste
    test_report = {
        "test_date": "2024-01-02",
        "documents_count": len(docs),
        "search_results": len(results),
        "entities_found": entities,
        "concepts_found": concepts,
        "status": "success"
    }
    
    report_path = os.path.join(client.base_path, "data", "test_report.json")
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(test_report, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 Relatório salvo em: {report_path}")

if __name__ == "__main__":
    test_mcp_client()