#!/usr/bin/env python3
"""
Script para testar o sistema de autenticação
"""

import requests
import json
from datetime import datetime

# Base URL
BASE_URL = "http://localhost:8000/api/v1"

def print_response(response, title="Response"):
    """Imprime resposta formatada"""
    print(f"\n{title}:")
    print(f"Status: {response.status_code}")
    try:
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    except:
        print(response.text)


def test_auth_flow():
    """Testa fluxo completo de autenticação"""
    print("="*60)
    print("TESTE DE AUTENTICAÇÃO")
    print("="*60)
    
    # 1. Login com credenciais inválidas
    print("\n1. Testando login com credenciais inválidas...")
    response = requests.post(
        f"{BASE_URL}/auth/token",
        data={
            "username": "invalid",
            "password": "wrong"
        }
    )
    print_response(response, "Login inválido")
    
    # 2. Login com usuário regular
    print("\n2. Testando login com usuário regular...")
    response = requests.post(
        f"{BASE_URL}/auth/token",
        data={
            "username": "user",
            "password": "user123"
        }
    )
    print_response(response, "Login usuário regular")
    
    if response.status_code == 200:
        user_token = response.json()["access_token"]
        print(f"\nToken obtido: {user_token[:20]}...")
    
    # 3. Login com admin
    print("\n3. Testando login com admin...")
    response = requests.post(
        f"{BASE_URL}/auth/token",
        data={
            "username": "admin",
            "password": "admin123"
        }
    )
    print_response(response, "Login admin")
    
    if response.status_code == 200:
        admin_token = response.json()["access_token"]
        refresh_token = response.json().get("refresh_token")
    
    # 4. Buscar informações do usuário atual
    print("\n4. Testando endpoint /me...")
    response = requests.get(
        f"{BASE_URL}/auth/me",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    print_response(response, "Informações do usuário")
    
    # 5. Testar busca autenticada
    print("\n5. Testando busca autenticada...")
    response = requests.post(
        f"{BASE_URL}/search",
        headers={"Authorization": f"Bearer {user_token}"},
        json={
            "query": "negativação indevida",
            "limit": 5
        }
    )
    print_response(response, "Busca autenticada")
    
    # 6. Testar busca sem autenticação
    print("\n6. Testando busca sem autenticação...")
    response = requests.post(
        f"{BASE_URL}/search",
        json={
            "query": "negativação indevida",
            "limit": 5
        }
    )
    print_response(response, "Busca sem autenticação")
    
    # 7. Listar usuários (requer admin)
    print("\n7. Testando listar usuários com admin...")
    response = requests.get(
        f"{BASE_URL}/auth/users",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    print_response(response, "Lista de usuários")
    
    # 8. Tentar listar usuários com user comum
    print("\n8. Testando listar usuários com user comum...")
    response = requests.get(
        f"{BASE_URL}/auth/users",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    print_response(response, "Lista de usuários (sem permissão)")
    
    # 9. Verificar permissões
    print("\n9. Testando verificação de permissões...")
    response = requests.get(
        f"{BASE_URL}/auth/permissions",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    print_response(response, "Permissões do admin")
    
    # 10. Refresh token
    if refresh_token:
        print("\n10. Testando refresh token...")
        response = requests.post(
            f"{BASE_URL}/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        print_response(response, "Refresh token")
    
    # 11. Criar novo usuário
    print("\n11. Testando criação de usuário...")
    new_user = {
        "username": f"test_user_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "email": f"test_{datetime.now().strftime('%Y%m%d%H%M%S')}@example.com",
        "password": "test123",
        "full_name": "Test User",
        "roles": ["viewer"]
    }
    
    response = requests.post(
        f"{BASE_URL}/auth/users",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=new_user
    )
    print_response(response, "Criar usuário")
    
    # 12. Auto-registro
    print("\n12. Testando auto-registro...")
    register_user = {
        "username": f"public_user_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "email": f"public_{datetime.now().strftime('%Y%m%d%H%M%S')}@example.com",
        "password": "public123",
        "full_name": "Public User"
    }
    
    response = requests.post(
        f"{BASE_URL}/auth/register",
        json=register_user
    )
    print_response(response, "Auto-registro")
    
    print("\n" + "="*60)
    print("TESTE CONCLUÍDO")
    print("="*60)


if __name__ == "__main__":
    test_auth_flow()