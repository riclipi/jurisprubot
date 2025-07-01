"""
🤖 CONFIGURADOR DE IA - GOOGLE GEMINI GRATUITO
==============================================

Este script ajuda você a configurar a IA do Google (gratuita!)
"""

import os
from pathlib import Path

def configurar_google_api():
    """Configura a API do Google Gemini."""
    print("🤖 CONFIGURAÇÃO DA IA GOOGLE GEMINI")
    print("=" * 50)
    
    print("\n📝 PASSOS PARA CONSEGUIR SUA CHAVE GRÁTIS:")
    print("1. Acesse: https://makersuite.google.com/app/apikey")
    print("2. Faça login com sua conta Google")
    print("3. Clique em 'Create API key'")
    print("4. Copie a chave gerada")
    print("5. Cole aqui quando solicitado")
    
    print("\n⚠️  IMPORTANTE:")
    print("• A API do Google Gemini é GRATUITA")
    print("• Limite generoso para testes")
    print("• Não precisa cartão de crédito")
    
    # Verificar se arquivo .env existe
    env_path = Path(".env")
    if not env_path.exists():
        print("\n❌ Arquivo .env não encontrado!")
        print("Execute primeiro: python configurar_sistema.py")
        return
    
    # Ler arquivo atual
    with open(env_path, 'r') as f:
        env_content = f.read()
    
    # Solicitar chave
    print(f"\n🔑 Cole sua chave de API do Google:")
    api_key = input("GOOGLE_API_KEY: ").strip()
    
    if not api_key:
        print("❌ Chave vazia. Operação cancelada.")
        return
    
    if not api_key.startswith('AI'):
        print("⚠️  Atenção: Chaves do Google geralmente começam com 'AI'")
        confirmar = input("Continuar mesmo assim? (s/n): ").strip().lower()
        if confirmar not in ['s', 'sim', 'y', 'yes']:
            print("Operação cancelada.")
            return
    
    # Atualizar arquivo .env
    lines = env_content.split('\n')
    updated_lines = []
    
    for line in lines:
        if line.startswith('GOOGLE_API_KEY='):
            updated_lines.append(f'GOOGLE_API_KEY={api_key}')
        else:
            updated_lines.append(line)
    
    # Salvar arquivo atualizado
    with open(env_path, 'w') as f:
        f.write('\n'.join(updated_lines))
    
    print(f"\n✅ Chave configurada com sucesso!")
    print(f"📁 Arquivo .env atualizado")
    
    # Testar a chave
    print(f"\n🧪 Testando a chave...")
    
    try:
        import google.generativeai as genai
        
        # Configurar API
        genai.configure(api_key=api_key)
        
        # Testar com uma pergunta simples
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content("Diga apenas 'API funcionando' se você conseguir ler isto.")
        
        if response and response.text:
            print(f"✅ TESTE PASSOU! Resposta: {response.text}")
            print(f"\n🎉 IA CONFIGURADA E FUNCIONANDO!")
            print(f"\n🚀 Agora execute:")
            print(f"   streamlit run sistema_real.py")
        else:
            print(f"⚠️  Teste não retornou resposta esperada")
            
    except Exception as e:
        print(f"❌ Erro no teste: {str(e)}")
        print(f"💡 Verifique se a chave está correta")

def verificar_configuracao():
    """Verifica se a IA já está configurada."""
    env_path = Path(".env")
    
    if not env_path.exists():
        return False, "Arquivo .env não encontrado"
    
    with open(env_path, 'r') as f:
        content = f.read()
    
    # Verificar Google
    if 'GOOGLE_API_KEY=' in content:
        google_key = content.split('GOOGLE_API_KEY=')[1].split('\n')[0].strip()
        if google_key and len(google_key) > 10:
            return True, f"Google API configurada: {google_key[:10]}..."
    
    # Verificar OpenAI
    if 'OPENAI_API_KEY=' in content:
        openai_key = content.split('OPENAI_API_KEY=')[1].split('\n')[0].strip()
        if openai_key and len(openai_key) > 10:
            return True, f"OpenAI API configurada: {openai_key[:10]}..."
    
    return False, "Nenhuma API configurada"

def main():
    print("🤖 CONFIGURADOR DE IA")
    print("=" * 30)
    
    # Verificar status atual
    configured, status = verificar_configuracao()
    
    print(f"\n📊 Status atual: {status}")
    
    if configured:
        print("✅ IA já configurada!")
        
        resposta = input("\nDeseja reconfigurar? (s/n): ").strip().lower()
        if resposta not in ['s', 'sim', 'y', 'yes']:
            print("Mantendo configuração atual.")
            return
    
    # Configurar
    configurar_google_api()

if __name__ == "__main__":
    main()