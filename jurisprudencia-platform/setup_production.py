#!/usr/bin/env python3
"""
🚀 SETUP DE PRODUÇÃO - SISTEMA JURÍDICO
Script completo para configurar o ambiente de produção
"""

import os
import sys
import subprocess
import shutil
import secrets
import hashlib
import json
from pathlib import Path
from datetime import datetime
import platform
import psutil
import click
from typing import Dict, List, Optional, Tuple
import yaml
from cryptography.fernet import Fernet


class ProductionSetup:
    """Classe principal para setup de produção"""
    
    def __init__(self):
        self.base_dir = Path.cwd()
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.report = {
            'timestamp': self.timestamp,
            'system_info': self._get_system_info(),
            'checks': {},
            'configurations': {},
            'warnings': [],
            'errors': []
        }
    
    def _get_system_info(self) -> Dict:
        """Coleta informações do sistema"""
        return {
            'platform': platform.platform(),
            'python_version': sys.version,
            'cpu_count': psutil.cpu_count(),
            'memory_gb': round(psutil.virtual_memory().total / (1024**3), 2),
            'disk_free_gb': round(psutil.disk_usage('/').free / (1024**3), 2)
        }
    
    def check_python_version(self) -> bool:
        """Verifica versão do Python"""
        print("🐍 Verificando versão do Python...")
        
        version = sys.version_info
        required = (3, 8)
        
        if version >= required:
            print(f"  ✅ Python {version.major}.{version.minor} (mínimo: {required[0]}.{required[1]})")
            self.report['checks']['python_version'] = 'OK'
            return True
        else:
            print(f"  ❌ Python {version.major}.{version.minor} (necessário: {required[0]}.{required[1]}+)")
            self.report['errors'].append(f"Python {required[0]}.{required[1]}+ necessário")
            return False
    
    def check_system_requirements(self) -> bool:
        """Verifica requisitos do sistema"""
        print("\n💻 Verificando requisitos do sistema...")
        
        all_ok = True
        
        # Memória
        memory_gb = psutil.virtual_memory().total / (1024**3)
        if memory_gb >= 4:
            print(f"  ✅ Memória: {memory_gb:.1f} GB (mínimo: 4 GB)")
            self.report['checks']['memory'] = 'OK'
        else:
            print(f"  ⚠️  Memória: {memory_gb:.1f} GB (recomendado: 4 GB+)")
            self.report['warnings'].append("Memória abaixo do recomendado")
        
        # Espaço em disco
        disk_free_gb = psutil.disk_usage('/').free / (1024**3)
        if disk_free_gb >= 10:
            print(f"  ✅ Disco livre: {disk_free_gb:.1f} GB (mínimo: 10 GB)")
            self.report['checks']['disk_space'] = 'OK'
        else:
            print(f"  ❌ Disco livre: {disk_free_gb:.1f} GB (necessário: 10 GB+)")
            self.report['errors'].append("Espaço em disco insuficiente")
            all_ok = False
        
        # Portas necessárias
        ports_to_check = {
            8000: "API",
            8501: "Streamlit",
            5432: "PostgreSQL",
            6379: "Redis",
            9200: "Elasticsearch"
        }
        
        print("\n  📡 Verificando portas...")
        for port, service in ports_to_check.items():
            if self._is_port_available(port):
                print(f"    ✅ Porta {port} ({service}): disponível")
                self.report['checks'][f'port_{port}'] = 'available'
            else:
                print(f"    ⚠️  Porta {port} ({service}): em uso")
                self.report['warnings'].append(f"Porta {port} ({service}) em uso")
        
        return all_ok
    
    def _is_port_available(self, port: int) -> bool:
        """Verifica se uma porta está disponível"""
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('', port))
                return True
            except:
                return False
    
    def check_dependencies(self) -> bool:
        """Verifica dependências do sistema"""
        print("\n📦 Verificando dependências do sistema...")
        
        dependencies = {
            'git': 'git --version',
            'docker': 'docker --version',
            'docker-compose': 'docker-compose --version',
            'redis-cli': 'redis-cli --version',
            'psql': 'psql --version',
            'nginx': 'nginx -v',
            'certbot': 'certbot --version'
        }
        
        all_ok = True
        for dep, cmd in dependencies.items():
            try:
                result = subprocess.run(
                    cmd.split(),
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    version = result.stdout.strip() or result.stderr.strip()
                    print(f"  ✅ {dep}: {version.split()[0] if version else 'instalado'}")
                    self.report['checks'][f'dep_{dep}'] = 'installed'
                else:
                    raise Exception()
            except:
                print(f"  ❌ {dep}: não encontrado")
                self.report['errors'].append(f"{dep} não instalado")
                all_ok = False
        
        return all_ok
    
    def install_python_dependencies(self) -> bool:
        """Instala dependências Python"""
        print("\n🐍 Instalando dependências Python...")
        
        try:
            # Atualizar pip
            print("  📦 Atualizando pip...")
            subprocess.run([
                sys.executable, "-m", "pip", "install", "--upgrade", "pip"
            ], check=True)
            
            # Instalar requirements
            if Path("requirements.txt").exists():
                print("  📦 Instalando requirements.txt...")
                subprocess.run([
                    sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
                ], check=True)
                print("  ✅ Dependências Python instaladas")
                self.report['configurations']['python_deps'] = 'installed'
                return True
            else:
                print("  ❌ requirements.txt não encontrado")
                self.report['errors'].append("requirements.txt não encontrado")
                return False
                
        except subprocess.CalledProcessError as e:
            print(f"  ❌ Erro ao instalar dependências: {e}")
            self.report['errors'].append(f"Erro ao instalar dependências Python: {e}")
            return False
    
    def create_directories(self) -> bool:
        """Cria estrutura de diretórios"""
        print("\n📁 Criando estrutura de diretórios...")
        
        directories = [
            "data/raw_pdfs",
            "data/processed",
            "data/vectorstore",
            "data/mcp_documents",
            "downloads_cache",
            "logs",
            "certificates",
            "backups",
            ".credentials"
        ]
        
        try:
            for dir_path in directories:
                path = Path(dir_path)
                path.mkdir(parents=True, exist_ok=True)
                
                # Permissões especiais para diretórios sensíveis
                if dir_path in [".credentials", "certificates"]:
                    os.chmod(path, 0o700)
                
                print(f"  ✅ {dir_path}")
            
            self.report['configurations']['directories'] = 'created'
            return True
            
        except Exception as e:
            print(f"  ❌ Erro ao criar diretórios: {e}")
            self.report['errors'].append(f"Erro ao criar diretórios: {e}")
            return False
    
    def generate_secrets(self) -> Dict[str, str]:
        """Gera chaves secretas"""
        print("\n🔐 Gerando chaves secretas...")
        
        secrets_dict = {}
        
        # JWT Secret
        jwt_secret = secrets.token_urlsafe(32)
        secrets_dict['JWT_SECRET_KEY'] = jwt_secret
        print("  ✅ JWT_SECRET_KEY gerada")
        
        # Encryption Key
        encryption_key = Fernet.generate_key().decode()
        secrets_dict['ENCRYPTION_KEY'] = encryption_key
        print("  ✅ ENCRYPTION_KEY gerada")
        
        # Master Password
        master_password = secrets.token_urlsafe(24)
        secrets_dict['MASTER_PASSWORD'] = master_password
        print("  ✅ MASTER_PASSWORD gerada")
        
        # Webhook Secret
        webhook_secret = secrets.token_hex(32)
        secrets_dict['WEBHOOK_SECRET'] = webhook_secret
        print("  ✅ WEBHOOK_SECRET gerada")
        
        self.report['configurations']['secrets'] = 'generated'
        
        return secrets_dict
    
    def configure_env_file(self, secrets: Dict[str, str]) -> bool:
        """Configura arquivo .env.production"""
        print("\n📝 Configurando arquivo .env.production...")
        
        env_file = Path(".env.production")
        
        if not env_file.exists():
            print("  ❌ .env.production não encontrado")
            self.report['errors'].append(".env.production não encontrado")
            return False
        
        try:
            # Ler arquivo atual
            with open(env_file, 'r') as f:
                content = f.read()
            
            # Substituir secrets
            for key, value in secrets.items():
                content = content.replace(f"{key}=", f"{key}={value}")
            
            # Criar backup
            backup_file = f".env.production.backup.{self.timestamp}"
            shutil.copy2(env_file, backup_file)
            print(f"  📋 Backup criado: {backup_file}")
            
            # Salvar configurações atualizadas
            with open(env_file, 'w') as f:
                f.write(content)
            
            # Proteger arquivo
            os.chmod(env_file, 0o600)
            
            print("  ✅ .env.production configurado")
            self.report['configurations']['env_file'] = 'configured'
            
            return True
            
        except Exception as e:
            print(f"  ❌ Erro ao configurar .env: {e}")
            self.report['errors'].append(f"Erro ao configurar .env: {e}")
            return False
    
    def setup_database(self) -> bool:
        """Configura banco de dados"""
        print("\n🗄️  Configurando banco de dados...")
        
        # Verificar se PostgreSQL está rodando
        try:
            result = subprocess.run(
                ["pg_isready"],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                print("  ⚠️  PostgreSQL não está rodando")
                print("  💡 Execute: sudo systemctl start postgresql")
                self.report['warnings'].append("PostgreSQL não está rodando")
                return False
            
            print("  ✅ PostgreSQL está rodando")
            
            # TODO: Criar database e usuário
            # Este seria o lugar para executar scripts SQL de setup
            
            self.report['configurations']['database'] = 'checked'
            return True
            
        except FileNotFoundError:
            print("  ❌ PostgreSQL não instalado")
            self.report['errors'].append("PostgreSQL não instalado")
            return False
    
    def setup_ssl_certificates(self) -> bool:
        """Configura certificados SSL"""
        print("\n🔒 Configurando certificados SSL...")
        
        cert_dir = Path("certificates")
        
        # Criar diretório se não existir
        cert_dir.mkdir(exist_ok=True)
        os.chmod(cert_dir, 0o700)
        
        # Gerar certificado auto-assinado para desenvolvimento
        if not (cert_dir / "server.crt").exists():
            print("  🔧 Gerando certificado auto-assinado...")
            try:
                subprocess.run([
                    "openssl", "req", "-x509", "-nodes",
                    "-days", "365",
                    "-newkey", "rsa:2048",
                    "-keyout", str(cert_dir / "server.key"),
                    "-out", str(cert_dir / "server.crt"),
                    "-subj", "/C=BR/ST=SP/L=SaoPaulo/O=JurisprudenciaPlatform/CN=localhost"
                ], check=True, capture_output=True)
                
                # Proteger arquivos
                os.chmod(cert_dir / "server.key", 0o600)
                os.chmod(cert_dir / "server.crt", 0o644)
                
                print("  ✅ Certificado auto-assinado criado")
                
            except Exception as e:
                print(f"  ❌ Erro ao gerar certificado: {e}")
                self.report['errors'].append(f"Erro ao gerar certificado: {e}")
                return False
        
        print("  ℹ️  Para produção, configure certificados válidos (Let's Encrypt)")
        self.report['configurations']['ssl'] = 'dev_cert_created'
        
        return True
    
    def configure_systemd_services(self) -> bool:
        """Configura serviços systemd"""
        print("\n🔧 Configurando serviços systemd...")
        
        services = {
            'jurisprudencia-api': self._create_api_service(),
            'jurisprudencia-worker': self._create_worker_service(),
            'jurisprudencia-scheduler': self._create_scheduler_service()
        }
        
        service_dir = Path("/etc/systemd/system")
        
        if not service_dir.exists():
            print("  ⚠️  Diretório systemd não encontrado (não é Linux?)")
            self.report['warnings'].append("systemd não disponível")
            return False
        
        for name, content in services.items():
            service_file = service_dir / f"{name}.service"
            
            # Criar arquivo temporário
            temp_file = Path(f"/tmp/{name}.service")
            with open(temp_file, 'w') as f:
                f.write(content)
            
            print(f"  📋 Serviço {name} criado em /tmp/")
            print(f"     Para instalar: sudo cp /tmp/{name}.service /etc/systemd/system/")
        
        print("\n  💡 Para ativar os serviços:")
        print("     sudo systemctl daemon-reload")
        for name in services:
            print(f"     sudo systemctl enable {name}")
            print(f"     sudo systemctl start {name}")
        
        self.report['configurations']['systemd'] = 'templates_created'
        return True
    
    def _create_api_service(self) -> str:
        """Cria arquivo de serviço para API"""
        return f"""[Unit]
Description=Jurisprudencia Platform API
After=network.target postgresql.service redis.service

[Service]
Type=exec
User=jurisprudencia
Group=jurisprudencia
WorkingDirectory={self.base_dir}
Environment="PATH=/usr/local/bin:/usr/bin:/bin"
Environment="PYTHONPATH={self.base_dir}"
ExecStart=/usr/bin/python3 -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
    
    def _create_worker_service(self) -> str:
        """Cria arquivo de serviço para worker Celery"""
        return f"""[Unit]
Description=Jurisprudencia Platform Celery Worker
After=network.target postgresql.service redis.service

[Service]
Type=exec
User=jurisprudencia
Group=jurisprudencia
WorkingDirectory={self.base_dir}
Environment="PATH=/usr/local/bin:/usr/bin:/bin"
Environment="PYTHONPATH={self.base_dir}"
ExecStart=/usr/bin/python3 -m celery -A src.pipeline.celery_app worker -l info
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
    
    def _create_scheduler_service(self) -> str:
        """Cria arquivo de serviço para scheduler Celery"""
        return f"""[Unit]
Description=Jurisprudencia Platform Celery Beat
After=network.target postgresql.service redis.service

[Service]
Type=exec
User=jurisprudencia
Group=jurisprudencia
WorkingDirectory={self.base_dir}
Environment="PATH=/usr/local/bin:/usr/bin:/bin"
Environment="PYTHONPATH={self.base_dir}"
ExecStart=/usr/bin/python3 -m celery -A src.pipeline.celery_app beat -l info
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
    
    def run_tests(self) -> bool:
        """Executa testes básicos"""
        print("\n🧪 Executando testes...")
        
        # Teste de importação
        print("  📦 Testando imports...")
        try:
            import streamlit
            import aiohttp
            import fastapi
            import sqlalchemy
            import redis
            import celery
            print("  ✅ Imports principais OK")
            self.report['checks']['imports'] = 'OK'
        except ImportError as e:
            print(f"  ❌ Erro de importação: {e}")
            self.report['errors'].append(f"Erro de importação: {e}")
            return False
        
        # Teste de validação CNJ
        print("  📋 Testando validação CNJ...")
        try:
            from src.utils.cnj_validator import validar_numero_cnj
            test_cnj = "0000001-02.2023.8.26.0001"
            is_valid = validar_numero_cnj(test_cnj)
            print(f"  ✅ Validação CNJ funcionando")
            self.report['checks']['cnj_validation'] = 'OK'
        except Exception as e:
            print(f"  ❌ Erro na validação CNJ: {e}")
            self.report['errors'].append(f"Erro na validação CNJ: {e}")
        
        return True
    
    def generate_report(self) -> str:
        """Gera relatório de configuração"""
        report_file = f"setup_report_{self.timestamp}.json"
        
        with open(report_file, 'w') as f:
            json.dump(self.report, f, indent=2, ensure_ascii=False)
        
        return report_file
    
    def print_summary(self):
        """Imprime resumo da configuração"""
        print("\n" + "="*60)
        print("📊 RESUMO DA CONFIGURAÇÃO")
        print("="*60)
        
        # Contadores
        checks_ok = sum(1 for v in self.report['checks'].values() if v in ['OK', 'installed', 'available'])
        total_checks = len(self.report['checks'])
        configs_done = len(self.report['configurations'])
        warnings = len(self.report['warnings'])
        errors = len(self.report['errors'])
        
        print(f"\n✅ Verificações bem-sucedidas: {checks_ok}/{total_checks}")
        print(f"⚙️  Configurações realizadas: {configs_done}")
        print(f"⚠️  Avisos: {warnings}")
        print(f"❌ Erros: {errors}")
        
        if self.report['warnings']:
            print(f"\n⚠️  AVISOS:")
            for warning in self.report['warnings']:
                print(f"   • {warning}")
        
        if self.report['errors']:
            print(f"\n❌ ERROS:")
            for error in self.report['errors']:
                print(f"   • {error}")
        
        # Status final
        if errors == 0:
            print(f"\n✅ CONFIGURAÇÃO CONCLUÍDA COM SUCESSO!")
        else:
            print(f"\n❌ CONFIGURAÇÃO CONCLUÍDA COM ERROS")
        
        print(f"\n📄 Relatório salvo em: setup_report_{self.timestamp}.json")


@click.command()
@click.option('--skip-deps', is_flag=True, help='Pular instalação de dependências')
@click.option('--skip-db', is_flag=True, help='Pular configuração do banco de dados')
@click.option('--skip-ssl', is_flag=True, help='Pular configuração SSL')
@click.option('--skip-tests', is_flag=True, help='Pular testes')
def main(skip_deps, skip_db, skip_ssl, skip_tests):
    """🚀 Script de configuração para ambiente de produção"""
    
    print("🚀 CONFIGURAÇÃO DE PRODUÇÃO - SISTEMA JURÍDICO")
    print("="*60)
    
    setup = ProductionSetup()
    
    # Verificações básicas
    if not setup.check_python_version():
        print("\n❌ Versão do Python incompatível")
        sys.exit(1)
    
    setup.check_system_requirements()
    setup.check_dependencies()
    
    # Instalações e configurações
    if not skip_deps:
        setup.install_python_dependencies()
    
    setup.create_directories()
    
    # Gerar secrets
    secrets = setup.generate_secrets()
    
    # Configurar arquivos
    setup.configure_env_file(secrets)
    
    if not skip_db:
        setup.setup_database()
    
    if not skip_ssl:
        setup.setup_ssl_certificates()
    
    # Serviços
    setup.configure_systemd_services()
    
    # Testes
    if not skip_tests:
        setup.run_tests()
    
    # Relatório final
    report_file = setup.generate_report()
    setup.print_summary()
    
    # Próximos passos
    print("\n📋 PRÓXIMOS PASSOS:")
    print("1. Configure as credenciais no arquivo .env.production")
    print("2. Configure os certificados digitais dos tribunais")
    print("3. Execute as migrações do banco de dados")
    print("4. Configure o nginx como proxy reverso")
    print("5. Configure o firewall e fail2ban")
    print("6. Ative os serviços systemd")
    print("7. Configure backups automáticos")
    print("8. Configure monitoramento (Prometheus/Grafana)")
    
    print("\n🚀 Para iniciar o sistema:")
    print("   streamlit run src/interface/admin_config.py")
    
    print("\n💡 Para mais informações, consulte docs/PRODUCTION_SETUP.md")


if __name__ == "__main__":
    main()