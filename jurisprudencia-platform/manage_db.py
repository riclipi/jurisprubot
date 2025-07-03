#!/usr/bin/env python3
"""
🗄️ GERENCIADOR DE BANCO DE DADOS
Script para gerenciar migrações e banco de dados
"""

import os
import sys
import click
import subprocess
from pathlib import Path
from datetime import datetime
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseManager:
    """Gerenciador de banco de dados"""
    
    def __init__(self):
        self.db_host = os.getenv('DB_HOST', 'localhost')
        self.db_port = os.getenv('DB_PORT', '5432')
        self.db_name = os.getenv('DB_NAME', 'jurisprudencia_db')
        self.db_user = os.getenv('DB_USER', 'jurisprudencia_user')
        self.db_password = os.getenv('DB_PASSWORD', '')
        
        # URLs de conexão
        self.admin_url = f"postgresql://postgres@{self.db_host}:{self.db_port}/postgres"
        self.db_url = f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
        
        # Configuração Alembic
        self.alembic_cfg = Config("alembic.ini")
        
    def create_database(self):
        """Cria o banco de dados se não existir"""
        try:
            # Conectar como postgres para criar DB
            conn = psycopg2.connect(self.admin_url)
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = conn.cursor()
            
            # Verificar se DB existe
            cursor.execute(
                "SELECT 1 FROM pg_database WHERE datname = %s",
                (self.db_name,)
            )
            
            if cursor.fetchone():
                logger.info(f"Banco de dados '{self.db_name}' já existe")
            else:
                # Criar banco
                cursor.execute(f'CREATE DATABASE "{self.db_name}"')
                logger.info(f"Banco de dados '{self.db_name}' criado")
            
            cursor.close()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao criar banco de dados: {e}")
            return False
    
    def create_user(self):
        """Cria usuário do banco se não existir"""
        try:
            conn = psycopg2.connect(self.admin_url)
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = conn.cursor()
            
            # Verificar se usuário existe
            cursor.execute(
                "SELECT 1 FROM pg_user WHERE usename = %s",
                (self.db_user,)
            )
            
            if cursor.fetchone():
                logger.info(f"Usuário '{self.db_user}' já existe")
                # Atualizar senha
                cursor.execute(
                    f"ALTER USER {self.db_user} WITH PASSWORD %s",
                    (self.db_password,)
                )
            else:
                # Criar usuário
                cursor.execute(
                    f"CREATE USER {self.db_user} WITH PASSWORD %s",
                    (self.db_password,)
                )
                logger.info(f"Usuário '{self.db_user}' criado")
            
            # Garantir privilégios
            cursor.execute(
                f'GRANT ALL PRIVILEGES ON DATABASE "{self.db_name}" TO {self.db_user}'
            )
            
            cursor.close()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao criar usuário: {e}")
            return False
    
    def init_extensions(self):
        """Inicializa extensões do PostgreSQL"""
        try:
            engine = create_engine(self.db_url)
            
            with engine.connect() as conn:
                # Criar extensões
                extensions = [
                    'uuid-ossp',
                    'pgcrypto',
                    'pg_trgm',
                    'unaccent'
                ]
                
                for ext in extensions:
                    try:
                        conn.execute(text(f'CREATE EXTENSION IF NOT EXISTS "{ext}"'))
                        conn.commit()
                        logger.info(f"Extensão '{ext}' criada/verificada")
                    except Exception as e:
                        logger.warning(f"Erro ao criar extensão '{ext}': {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao inicializar extensões: {e}")
            return False
    
    def run_migrations(self):
        """Executa migrações pendentes"""
        try:
            logger.info("Executando migrações...")
            command.upgrade(self.alembic_cfg, "head")
            logger.info("Migrações executadas com sucesso")
            return True
        except Exception as e:
            logger.error(f"Erro ao executar migrações: {e}")
            return False
    
    def create_migration(self, message: str):
        """Cria nova migração"""
        try:
            logger.info(f"Criando migração: {message}")
            command.revision(self.alembic_cfg, autogenerate=True, message=message)
            logger.info("Migração criada com sucesso")
            return True
        except Exception as e:
            logger.error(f"Erro ao criar migração: {e}")
            return False
    
    def rollback_migration(self, revision: str = "-1"):
        """Reverte migração"""
        try:
            logger.info(f"Revertendo para revisão: {revision}")
            command.downgrade(self.alembic_cfg, revision)
            logger.info("Migração revertida com sucesso")
            return True
        except Exception as e:
            logger.error(f"Erro ao reverter migração: {e}")
            return False
    
    def show_history(self):
        """Mostra histórico de migrações"""
        try:
            command.history(self.alembic_cfg)
            return True
        except Exception as e:
            logger.error(f"Erro ao mostrar histórico: {e}")
            return False
    
    def show_current(self):
        """Mostra revisão atual"""
        try:
            command.current(self.alembic_cfg)
            return True
        except Exception as e:
            logger.error(f"Erro ao mostrar revisão atual: {e}")
            return False
    
    def backup_database(self, output_dir: str = "backups"):
        """Faz backup do banco de dados"""
        try:
            # Criar diretório se não existir
            Path(output_dir).mkdir(exist_ok=True)
            
            # Nome do arquivo
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = f"{output_dir}/backup_{self.db_name}_{timestamp}.sql"
            
            # Comando pg_dump
            cmd = [
                'pg_dump',
                '-h', self.db_host,
                '-p', self.db_port,
                '-U', self.db_user,
                '-d', self.db_name,
                '-f', backup_file,
                '--verbose',
                '--clean',
                '--if-exists'
            ]
            
            # Executar backup
            env = os.environ.copy()
            env['PGPASSWORD'] = self.db_password
            
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"Backup criado: {backup_file}")
                
                # Comprimir
                subprocess.run(['gzip', backup_file])
                logger.info(f"Backup comprimido: {backup_file}.gz")
                
                return True
            else:
                logger.error(f"Erro no backup: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao fazer backup: {e}")
            return False
    
    def restore_database(self, backup_file: str):
        """Restaura banco de dados de um backup"""
        try:
            # Verificar se arquivo existe
            if not Path(backup_file).exists():
                logger.error(f"Arquivo não encontrado: {backup_file}")
                return False
            
            # Descomprimir se necessário
            if backup_file.endswith('.gz'):
                subprocess.run(['gunzip', '-k', backup_file])
                backup_file = backup_file[:-3]
            
            # Comando psql
            cmd = [
                'psql',
                '-h', self.db_host,
                '-p', self.db_port,
                '-U', self.db_user,
                '-d', self.db_name,
                '-f', backup_file
            ]
            
            # Executar restore
            env = os.environ.copy()
            env['PGPASSWORD'] = self.db_password
            
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("Banco de dados restaurado com sucesso")
                return True
            else:
                logger.error(f"Erro na restauração: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao restaurar banco: {e}")
            return False


@click.group()
def cli():
    """Gerenciador de banco de dados"""
    pass


@cli.command()
def init():
    """Inicializa banco de dados completo"""
    manager = DatabaseManager()
    
    print("🗄️  INICIALIZANDO BANCO DE DADOS")
    print("=" * 50)
    
    # Criar banco
    if not manager.create_database():
        print("❌ Erro ao criar banco de dados")
        sys.exit(1)
    
    # Criar usuário
    if not manager.create_user():
        print("❌ Erro ao criar usuário")
        sys.exit(1)
    
    # Inicializar extensões
    if not manager.init_extensions():
        print("❌ Erro ao inicializar extensões")
        sys.exit(1)
    
    # Executar migrações
    if not manager.run_migrations():
        print("❌ Erro ao executar migrações")
        sys.exit(1)
    
    print("\n✅ Banco de dados inicializado com sucesso!")


@cli.command()
def migrate():
    """Executa migrações pendentes"""
    manager = DatabaseManager()
    manager.run_migrations()


@cli.command()
@click.option('--message', '-m', required=True, help='Mensagem da migração')
def create_migration(message):
    """Cria nova migração"""
    manager = DatabaseManager()
    manager.create_migration(message)


@cli.command()
@click.option('--revision', '-r', default='-1', help='Revisão alvo')
def rollback(revision):
    """Reverte migração"""
    manager = DatabaseManager()
    manager.rollback_migration(revision)


@cli.command()
def history():
    """Mostra histórico de migrações"""
    manager = DatabaseManager()
    manager.show_history()


@cli.command()
def current():
    """Mostra revisão atual"""
    manager = DatabaseManager()
    manager.show_current()


@cli.command()
@click.option('--output', '-o', default='backups', help='Diretório de saída')
def backup(output):
    """Faz backup do banco de dados"""
    manager = DatabaseManager()
    manager.backup_database(output)


@cli.command()
@click.argument('backup_file')
def restore(backup_file):
    """Restaura banco de dados"""
    if not click.confirm(f'⚠️  Isso sobrescreverá o banco atual. Continuar?'):
        return
    
    manager = DatabaseManager()
    manager.restore_database(backup_file)


@cli.command()
def reset():
    """Reseta banco de dados (CUIDADO!)"""
    if not click.confirm('⚠️  Isso APAGARÁ todos os dados. Continuar?'):
        return
    
    if not click.confirm('⚠️  Tem CERTEZA? Digite "SIM" para confirmar'):
        return
    
    manager = DatabaseManager()
    
    # Fazer backup antes
    print("📦 Fazendo backup de segurança...")
    manager.backup_database("backups/emergency")
    
    # Reverter todas as migrações
    print("🔄 Revertendo migrações...")
    manager.rollback_migration("base")
    
    # Recriar
    print("🔧 Recriando banco...")
    manager.run_migrations()
    
    print("✅ Banco de dados resetado")


@cli.command()
def status():
    """Mostra status do banco de dados"""
    manager = DatabaseManager()
    
    print("🗄️  STATUS DO BANCO DE DADOS")
    print("=" * 50)
    
    try:
        # Testar conexão
        engine = create_engine(manager.db_url)
        with engine.connect() as conn:
            # Versão do PostgreSQL
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"✅ PostgreSQL: {version.split(',')[0]}")
            
            # Tamanho do banco
            result = conn.execute(text(
                f"SELECT pg_size_pretty(pg_database_size('{manager.db_name}'))"
            ))
            size = result.scalar()
            print(f"📊 Tamanho: {size}")
            
            # Contagem de tabelas
            result = conn.execute(text(
                "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'"
            ))
            tables = result.scalar()
            print(f"📋 Tabelas: {tables}")
            
            # Revisão atual
            print(f"\n📌 Migração atual:")
            manager.show_current()
            
    except Exception as e:
        print(f"❌ Erro ao conectar: {e}")


if __name__ == "__main__":
    cli()