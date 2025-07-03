"""
🔐 GERENCIADOR DE CREDENCIAIS SEGURO
Sistema de gerenciamento seguro de credenciais com criptografia
"""

import os
import json
import base64
from pathlib import Path
from typing import Dict, Optional, Any
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import keyring
from dotenv import load_dotenv, set_key
import logging

logger = logging.getLogger(__name__)


class CredentialsManager:
    """
    Gerenciador seguro de credenciais com criptografia
    Suporta armazenamento local criptografado e integração com serviços externos
    """
    
    def __init__(self, config_path: str = ".credentials"):
        self.config_path = Path(config_path)
        self.config_path.mkdir(exist_ok=True)
        self.credentials_file = self.config_path / "credentials.enc"
        self.key_file = self.config_path / ".key"
        self.env_file = Path(".env.production")
        
        # Inicializar chave de criptografia
        self._init_encryption()
        
        # Cache de credenciais
        self._credentials_cache = {}
        
    def _init_encryption(self):
        """Inicializa sistema de criptografia"""
        if not self.key_file.exists():
            # Gerar nova chave
            salt = os.urandom(16)
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            
            # Usar uma senha mestre (em produção, isso deve vir de variável de ambiente)
            master_password = os.getenv("MASTER_PASSWORD", "default_dev_password").encode()
            key = base64.urlsafe_b64encode(kdf.derive(master_password))
            
            # Salvar chave e salt
            with open(self.key_file, 'wb') as f:
                f.write(salt + key)
            
            # Proteger arquivo
            os.chmod(self.key_file, 0o600)
        
        # Carregar chave
        with open(self.key_file, 'rb') as f:
            data = f.read()
            self.salt = data[:16]
            self.key = data[16:]
            self.cipher = Fernet(self.key)
    
    def set_credential(self, service: str, key: str, value: str, 
                      category: str = "general") -> bool:
        """
        Armazena uma credencial de forma segura
        
        Args:
            service: Nome do serviço (ex: "tjsp", "openai")
            key: Chave da credencial (ex: "api_key", "password")
            value: Valor da credencial
            category: Categoria (ex: "tribunal", "api", "certificado")
        """
        try:
            # Carregar credenciais existentes
            credentials = self._load_credentials()
            
            # Estruturar credenciais
            if category not in credentials:
                credentials[category] = {}
            
            if service not in credentials[category]:
                credentials[category][service] = {}
            
            # Criptografar valor individualmente para maior segurança
            encrypted_value = self.cipher.encrypt(value.encode()).decode()
            credentials[category][service][key] = encrypted_value
            
            # Salvar credenciais
            self._save_credentials(credentials)
            
            # Atualizar cache
            self._credentials_cache = credentials
            
            # Log de auditoria (sem expor o valor)
            logger.info(f"Credencial atualizada: {category}/{service}/{key}")
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao salvar credencial: {e}")
            return False
    
    def get_credential(self, service: str, key: str, 
                      category: str = "general") -> Optional[str]:
        """
        Recupera uma credencial de forma segura
        
        Args:
            service: Nome do serviço
            key: Chave da credencial
            category: Categoria
            
        Returns:
            Valor descriptografado ou None
        """
        try:
            credentials = self._load_credentials()
            
            if (category in credentials and 
                service in credentials[category] and 
                key in credentials[category][service]):
                
                encrypted_value = credentials[category][service][key]
                decrypted_value = self.cipher.decrypt(encrypted_value.encode()).decode()
                
                # Log de auditoria (sem expor o valor)
                logger.info(f"Credencial acessada: {category}/{service}/{key}")
                
                return decrypted_value
            
            return None
            
        except Exception as e:
            logger.error(f"Erro ao recuperar credencial: {e}")
            return None
    
    def set_tribunal_credentials(self, tribunal: str, cpf_cnpj: str, 
                                senha: str, certificado_path: Optional[str] = None,
                                certificado_senha: Optional[str] = None) -> bool:
        """
        Configura credenciais específicas de um tribunal
        
        Args:
            tribunal: Código do tribunal (ex: "tjsp", "trf3")
            cpf_cnpj: CPF ou CNPJ para acesso
            senha: Senha de acesso
            certificado_path: Caminho para certificado digital (opcional)
            certificado_senha: Senha do certificado (opcional)
        """
        success = True
        
        # Salvar credenciais básicas
        success &= self.set_credential(tribunal, "cpf_cnpj", cpf_cnpj, "tribunal")
        success &= self.set_credential(tribunal, "senha", senha, "tribunal")
        
        # Salvar certificado se fornecido
        if certificado_path:
            success &= self.set_credential(tribunal, "cert_path", certificado_path, "tribunal")
            if certificado_senha:
                success &= self.set_credential(tribunal, "cert_senha", certificado_senha, "tribunal")
        
        return success
    
    def get_tribunal_credentials(self, tribunal: str) -> Optional[Dict[str, str]]:
        """
        Recupera todas as credenciais de um tribunal
        
        Args:
            tribunal: Código do tribunal
            
        Returns:
            Dicionário com credenciais ou None
        """
        creds = {}
        
        # Credenciais básicas
        cpf_cnpj = self.get_credential(tribunal, "cpf_cnpj", "tribunal")
        senha = self.get_credential(tribunal, "senha", "tribunal")
        
        if not cpf_cnpj or not senha:
            return None
        
        creds["cpf_cnpj"] = cpf_cnpj
        creds["senha"] = senha
        
        # Certificado (opcional)
        cert_path = self.get_credential(tribunal, "cert_path", "tribunal")
        if cert_path:
            creds["cert_path"] = cert_path
            cert_senha = self.get_credential(tribunal, "cert_senha", "tribunal")
            if cert_senha:
                creds["cert_senha"] = cert_senha
        
        return creds
    
    def set_api_key(self, service: str, api_key: str) -> bool:
        """
        Armazena uma chave de API
        
        Args:
            service: Nome do serviço (ex: "openai", "google", "brlaw")
            api_key: Chave de API
        """
        return self.set_credential(service, "api_key", api_key, "api")
    
    def get_api_key(self, service: str) -> Optional[str]:
        """
        Recupera uma chave de API
        
        Args:
            service: Nome do serviço
            
        Returns:
            Chave de API ou None
        """
        return self.get_credential(service, "api_key", "api")
    
    def update_env_file(self, updates: Dict[str, str]) -> bool:
        """
        Atualiza arquivo .env.production com novas variáveis
        
        Args:
            updates: Dicionário com variáveis a atualizar
        """
        try:
            # Criar arquivo se não existir
            if not self.env_file.exists():
                self.env_file.touch()
            
            # Atualizar cada variável
            for key, value in updates.items():
                set_key(str(self.env_file), key, value)
            
            logger.info(f"Arquivo {self.env_file} atualizado com {len(updates)} variáveis")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao atualizar .env.production: {e}")
            return False
    
    def test_credential(self, service: str, category: str = "general") -> bool:
        """
        Testa se uma credencial está configurada e acessível
        
        Args:
            service: Nome do serviço
            category: Categoria da credencial
            
        Returns:
            True se a credencial existe e pode ser acessada
        """
        try:
            credentials = self._load_credentials()
            
            return (category in credentials and 
                   service in credentials[category] and 
                   len(credentials[category][service]) > 0)
            
        except Exception:
            return False
    
    def list_configured_services(self) -> Dict[str, list]:
        """
        Lista todos os serviços configurados por categoria
        
        Returns:
            Dicionário com categorias e seus serviços
        """
        try:
            credentials = self._load_credentials()
            result = {}
            
            for category, services in credentials.items():
                result[category] = list(services.keys())
            
            return result
            
        except Exception:
            return {}
    
    def remove_credential(self, service: str, key: str = None, 
                         category: str = "general") -> bool:
        """
        Remove uma credencial ou todas de um serviço
        
        Args:
            service: Nome do serviço
            key: Chave específica (se None, remove todas do serviço)
            category: Categoria
        """
        try:
            credentials = self._load_credentials()
            
            if category not in credentials:
                return False
            
            if service not in credentials[category]:
                return False
            
            if key:
                # Remover chave específica
                if key in credentials[category][service]:
                    del credentials[category][service][key]
                    logger.info(f"Credencial removida: {category}/{service}/{key}")
            else:
                # Remover todo o serviço
                del credentials[category][service]
                logger.info(f"Todas credenciais removidas: {category}/{service}")
            
            # Limpar categorias vazias
            if not credentials[category]:
                del credentials[category]
            
            self._save_credentials(credentials)
            self._credentials_cache = credentials
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao remover credencial: {e}")
            return False
    
    def export_safe_config(self) -> Dict[str, Any]:
        """
        Exporta configuração segura (sem valores sensíveis)
        
        Returns:
            Dicionário com estrutura de configuração
        """
        try:
            credentials = self._load_credentials()
            safe_config = {}
            
            for category, services in credentials.items():
                safe_config[category] = {}
                for service, keys in services.items():
                    safe_config[category][service] = list(keys.keys())
            
            return safe_config
            
        except Exception:
            return {}
    
    def _load_credentials(self) -> Dict:
        """Carrega credenciais do arquivo criptografado"""
        if self._credentials_cache:
            return self._credentials_cache
        
        if not self.credentials_file.exists():
            return {}
        
        try:
            with open(self.credentials_file, 'rb') as f:
                encrypted_data = f.read()
            
            decrypted_data = self.cipher.decrypt(encrypted_data)
            credentials = json.loads(decrypted_data)
            
            self._credentials_cache = credentials
            return credentials
            
        except Exception as e:
            logger.error(f"Erro ao carregar credenciais: {e}")
            return {}
    
    def _save_credentials(self, credentials: Dict):
        """Salva credenciais no arquivo criptografado"""
        try:
            json_data = json.dumps(credentials, indent=2)
            encrypted_data = self.cipher.encrypt(json_data.encode())
            
            with open(self.credentials_file, 'wb') as f:
                f.write(encrypted_data)
            
            # Proteger arquivo
            os.chmod(self.credentials_file, 0o600)
            
        except Exception as e:
            logger.error(f"Erro ao salvar credenciais: {e}")
            raise


# Instância global para uso facilitado
credentials_manager = CredentialsManager()


def get_tribunal_access(tribunal: str) -> Optional[Dict[str, str]]:
    """
    Função helper para obter credenciais de acesso a um tribunal
    
    Args:
        tribunal: Código do tribunal
        
    Returns:
        Dicionário com credenciais ou None
    """
    return credentials_manager.get_tribunal_credentials(tribunal)


def get_api_key(service: str) -> Optional[str]:
    """
    Função helper para obter chave de API
    
    Args:
        service: Nome do serviço
        
    Returns:
        Chave de API ou None
    """
    return credentials_manager.get_api_key(service)


if __name__ == "__main__":
    # Teste básico
    cm = CredentialsManager()
    
    # Testar tribunal
    cm.set_tribunal_credentials(
        "tjsp",
        "123.456.789-00",
        "senha_teste",
        "/path/to/cert.p12",
        "cert_password"
    )
    
    # Testar API
    cm.set_api_key("openai", "sk-test123456789")
    
    # Listar configurados
    print("Serviços configurados:", cm.list_configured_services())
    
    # Testar recuperação
    tjsp_creds = cm.get_tribunal_credentials("tjsp")
    print("Credenciais TJSP:", tjsp_creds is not None)
    
    api_key = cm.get_api_key("openai")
    print("API Key OpenAI:", api_key is not None)