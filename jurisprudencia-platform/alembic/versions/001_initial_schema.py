"""Initial database schema

Revision ID: 001
Revises: 
Create Date: 2025-07-02 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create extensions
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pg_trgm"')
    
    # Admin users table
    op.create_table('admin_users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('email', sa.String(length=100), nullable=False),
        sa.Column('hashed_password', sa.String(length=200), nullable=False),
        sa.Column('totp_secret', sa.String(length=100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('is_2fa_enabled', sa.Boolean(), nullable=True, default=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.Column('failed_attempts', sa.Integer(), nullable=True, default=0),
        sa.Column('locked_until', sa.DateTime(), nullable=True),
        sa.Column('password_changed_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.String(length=50), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('updated_by', sa.String(length=50), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_admin_users_email'), 'admin_users', ['email'], unique=True)
    op.create_index(op.f('ix_admin_users_username'), 'admin_users', ['username'], unique=True)
    
    # Tribunais table
    op.create_table('tribunais',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('codigo', sa.String(length=20), nullable=False),
        sa.Column('nome', sa.String(length=200), nullable=False),
        sa.Column('sigla', sa.String(length=20), nullable=False),
        sa.Column('tipo', sa.String(length=50), nullable=False),
        sa.Column('uf', sa.String(length=2), nullable=True),
        sa.Column('url_rest', sa.String(length=500), nullable=True),
        sa.Column('url_soap', sa.String(length=500), nullable=True),
        sa.Column('url_base', sa.String(length=500), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tribunais_codigo'), 'tribunais', ['codigo'], unique=True)
    
    # Processos table
    op.create_table('processos',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('numero_cnj', sa.String(length=25), nullable=False),
        sa.Column('tribunal_id', sa.Integer(), nullable=False),
        sa.Column('classe_processual', sa.String(length=200), nullable=True),
        sa.Column('assunto', sa.String(length=500), nullable=True),
        sa.Column('valor_causa', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('data_distribuicao', sa.Date(), nullable=True),
        sa.Column('status', sa.String(length=100), nullable=True),
        sa.Column('ultima_atualizacao', sa.DateTime(), nullable=True),
        sa.Column('dados_completos', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['tribunal_id'], ['tribunais.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_processos_numero_cnj'), 'processos', ['numero_cnj'], unique=True)
    op.create_index('ix_processos_tribunal_id', 'processos', ['tribunal_id'])
    
    # Partes table
    op.create_table('partes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('processo_id', sa.Integer(), nullable=False),
        sa.Column('tipo', sa.String(length=50), nullable=False),
        sa.Column('nome', sa.String(length=300), nullable=False),
        sa.Column('documento', sa.String(length=20), nullable=True),
        sa.Column('advogados', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['processo_id'], ['processos.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_partes_processo_id', 'partes', ['processo_id'])
    op.create_index('ix_partes_nome', 'partes', ['nome'])
    
    # Documentos table
    op.create_table('documentos',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('processo_id', sa.Integer(), nullable=False),
        sa.Column('nome', sa.String(length=300), nullable=False),
        sa.Column('tipo', sa.String(length=100), nullable=False),
        sa.Column('data_documento', sa.Date(), nullable=True),
        sa.Column('url_original', sa.String(length=1000), nullable=True),
        sa.Column('caminho_local', sa.String(length=500), nullable=True),
        sa.Column('hash_arquivo', sa.String(length=64), nullable=True),
        sa.Column('tamanho_bytes', sa.BigInteger(), nullable=True),
        sa.Column('conteudo_extraido', sa.Text(), nullable=True),
        sa.Column('metadados', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['processo_id'], ['processos.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_documentos_processo_id', 'documentos', ['processo_id'])
    op.create_index('ix_documentos_hash_arquivo', 'documentos', ['hash_arquivo'])
    
    # Movimentacoes table
    op.create_table('movimentacoes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('processo_id', sa.Integer(), nullable=False),
        sa.Column('data', sa.DateTime(), nullable=False),
        sa.Column('descricao', sa.Text(), nullable=False),
        sa.Column('tipo', sa.String(length=100), nullable=True),
        sa.Column('complemento', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['processo_id'], ['processos.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_movimentacoes_processo_id', 'movimentacoes', ['processo_id'])
    op.create_index('ix_movimentacoes_data', 'movimentacoes', ['data'])
    
    # Analises table
    op.create_table('analises',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('processo_id', sa.Integer(), nullable=False),
        sa.Column('tipo_analise', sa.String(length=100), nullable=False),
        sa.Column('resultado', sa.JSON(), nullable=False),
        sa.Column('confianca', sa.Float(), nullable=True),
        sa.Column('modelo_usado', sa.String(length=100), nullable=True),
        sa.Column('tempo_processamento', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.String(length=50), nullable=True),
        sa.ForeignKeyConstraint(['processo_id'], ['processos.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_analises_processo_id', 'analises', ['processo_id'])
    
    # Minutas table
    op.create_table('minutas',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('processo_id', sa.Integer(), nullable=True),
        sa.Column('tipo', sa.String(length=100), nullable=False),
        sa.Column('titulo', sa.String(length=300), nullable=False),
        sa.Column('conteudo', sa.Text(), nullable=False),
        sa.Column('fundamentacao', sa.JSON(), nullable=True),
        sa.Column('qualidade_score', sa.Float(), nullable=True),
        sa.Column('tempo_geracao', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.String(length=50), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['processo_id'], ['processos.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_minutas_processo_id', 'minutas', ['processo_id'])
    
    # Audit_logs table
    op.create_table('audit_logs',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('user_id', sa.String(length=50), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('resource_type', sa.String(length=100), nullable=True),
        sa.Column('resource_id', sa.String(length=100), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=True),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=True, default=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_audit_logs_timestamp', 'audit_logs', ['timestamp'])
    op.create_index('ix_audit_logs_user_id', 'audit_logs', ['user_id'])
    op.create_index('ix_audit_logs_event_type', 'audit_logs', ['event_type'])
    
    # Metricas table
    op.create_table('metricas',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('metric_name', sa.String(length=100), nullable=False),
        sa.Column('metric_value', sa.Float(), nullable=False),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_metricas_timestamp', 'metricas', ['timestamp'])
    op.create_index('ix_metricas_metric_name', 'metricas', ['metric_name'])
    
    # Configuracoes table
    op.create_table('configuracoes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('chave', sa.String(length=100), nullable=False),
        sa.Column('valor', sa.JSON(), nullable=False),
        sa.Column('descricao', sa.String(length=500), nullable=True),
        sa.Column('tipo', sa.String(length=50), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('updated_by', sa.String(length=50), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_configuracoes_chave'), 'configuracoes', ['chave'], unique=True)
    
    # Create initial data
    op.execute("""
        INSERT INTO tribunais (codigo, nome, sigla, tipo, uf, created_at)
        VALUES 
        ('STF', 'Supremo Tribunal Federal', 'STF', 'supremo', NULL, NOW()),
        ('STJ', 'Superior Tribunal de Justiça', 'STJ', 'superior', NULL, NOW()),
        ('TST', 'Tribunal Superior do Trabalho', 'TST', 'superior', NULL, NOW()),
        ('TJSP', 'Tribunal de Justiça de São Paulo', 'TJSP', 'estadual', 'SP', NOW()),
        ('TJRJ', 'Tribunal de Justiça do Rio de Janeiro', 'TJRJ', 'estadual', 'RJ', NOW()),
        ('TJMG', 'Tribunal de Justiça de Minas Gerais', 'TJMG', 'estadual', 'MG', NOW()),
        ('TRF1', 'Tribunal Regional Federal da 1ª Região', 'TRF1', 'federal', NULL, NOW()),
        ('TRF2', 'Tribunal Regional Federal da 2ª Região', 'TRF2', 'federal', NULL, NOW()),
        ('TRF3', 'Tribunal Regional Federal da 3ª Região', 'TRF3', 'federal', NULL, NOW()),
        ('TRT2', 'Tribunal Regional do Trabalho da 2ª Região', 'TRT2', 'trabalho', 'SP', NOW())
    """)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('configuracoes')
    op.drop_table('metricas')
    op.drop_table('audit_logs')
    op.drop_table('minutas')
    op.drop_table('analises')
    op.drop_table('movimentacoes')
    op.drop_table('documentos')
    op.drop_table('partes')
    op.drop_table('processos')
    op.drop_table('tribunais')
    op.drop_table('admin_users')
    
    # Drop extensions
    op.execute('DROP EXTENSION IF EXISTS "pg_trgm"')
    op.execute('DROP EXTENSION IF EXISTS "pgcrypto"')
    op.execute('DROP EXTENSION IF EXISTS "uuid-ossp"')