# 🚀 Guia de Configuração para Produção

Este guia detalha o processo completo para configurar o Sistema Jurídico em ambiente de produção com dados reais, conexões seguras e alta disponibilidade.

## 📋 Índice

1. [Requisitos do Sistema](#requisitos-do-sistema)
2. [Preparação do Ambiente](#preparação-do-ambiente)
3. [Instalação e Configuração](#instalação-e-configuração)
4. [Configuração de Credenciais](#configuração-de-credenciais)
5. [Certificados Digitais](#certificados-digitais)
6. [Configuração dos Tribunais](#configuração-dos-tribunais)
7. [Banco de Dados](#banco-de-dados)
8. [Segurança](#segurança)
9. [Deploy e Execução](#deploy-e-execução)
10. [Monitoramento](#monitoramento)
11. [Backup e Recuperação](#backup-e-recuperação)
12. [Troubleshooting](#troubleshooting)

## 🖥️ Requisitos do Sistema

### Hardware Mínimo
- **CPU**: 4 cores (8 recomendado)
- **RAM**: 8 GB (16 GB recomendado)
- **Disco**: 100 GB SSD (200 GB recomendado)
- **Rede**: 100 Mbps (1 Gbps recomendado)

### Software
- **OS**: Ubuntu 20.04 LTS ou superior
- **Python**: 3.8 ou superior
- **PostgreSQL**: 13 ou superior
- **Redis**: 6.0 ou superior
- **Nginx**: 1.18 ou superior
- **Docker**: 20.10 ou superior (opcional)

### Portas Necessárias
- `8000`: API REST
- `8501`: Interface Streamlit
- `5432`: PostgreSQL
- `6379`: Redis
- `9200`: Elasticsearch (opcional)
- `3000`: Grafana (monitoramento)
- `9090`: Prometheus (métricas)

## 🛠️ Preparação do Ambiente

### 1. Atualizar Sistema
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y build-essential python3-dev python3-pip git curl wget
```

### 2. Instalar Dependências do Sistema
```bash
# PostgreSQL
sudo apt install -y postgresql postgresql-contrib

# Redis
sudo apt install -y redis-server

# Nginx
sudo apt install -y nginx

# Certificados SSL
sudo apt install -y certbot python3-certbot-nginx

# Ferramentas auxiliares
sudo apt install -y supervisor fail2ban ufw
```

### 3. Criar Usuário do Sistema
```bash
sudo useradd -m -s /bin/bash jurisprudencia
sudo usermod -aG sudo jurisprudencia
```

## 📦 Instalação e Configuração

### 1. Clonar Repositório
```bash
cd /opt
sudo git clone https://github.com/seu-usuario/jurisprudencia-platform.git
sudo chown -R jurisprudencia:jurisprudencia jurisprudencia-platform
cd jurisprudencia-platform
```

### 2. Ambiente Virtual Python
```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
```

### 3. Instalar Dependências Python
```bash
pip install -r requirements.txt
```

### 4. Executar Script de Setup
```bash
chmod +x setup_production.py
./setup_production.py
```

O script irá:
- ✅ Verificar requisitos do sistema
- ✅ Criar estrutura de diretórios
- ✅ Gerar chaves secretas
- ✅ Configurar arquivo `.env.production`
- ✅ Criar certificados SSL auto-assinados
- ✅ Gerar arquivos de serviço systemd

## 🔐 Configuração de Credenciais

### 1. Editar `.env.production`
```bash
nano .env.production
```

### 2. Configurar APIs
```env
# APIs de IA
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxx
GOOGLE_API_KEY=AIzaxxxxxxxxxxxxxxxxxxxxx
BRLAW_MCP_API_KEY=xxxxxxxxxxxxxxxxxxxxx
```

### 3. Configurar Tribunais
Para cada tribunal, configure:
```env
# TJSP
TJSP_CPF_CNPJ=12345678900
TJSP_SENHA=sua_senha_segura
TJSP_AUTH_TOKEN=token_se_necessario
```

### 4. Usar Interface Administrativa
```bash
streamlit run src/interface/admin_config.py
```

Acesse: http://localhost:8501

- Login: admin / admin123 (altere imediatamente!)
- Configure credenciais pela interface gráfica
- Teste conectividade de cada tribunal

## 🔏 Certificados Digitais

### 1. Certificados A3/Token

#### Instalar Driver do Token
```bash
# Safenet/Gemalto
sudo apt install -y libaetpkss libgclib

# Configure o token
pcsc_scan  # Verificar se token é detectado
```

#### Converter Certificado para PEM
```bash
# Exportar do Windows/token
openssl pkcs12 -in certificado.p12 -out certificado.pem -nodes
```

#### Configurar no Sistema
```bash
# Copiar para diretório seguro
sudo mkdir -p /opt/certs
sudo cp certificado.pem /opt/certs/
sudo chmod 600 /opt/certs/certificado.pem
sudo chown jurisprudencia:jurisprudencia /opt/certs/certificado.pem
```

### 2. SSL/TLS para Produção

#### Gerar Certificado Let's Encrypt
```bash
sudo certbot --nginx -d seu-dominio.com.br
```

#### Configurar Renovação Automática
```bash
sudo crontab -e
# Adicionar:
0 0 1 * * certbot renew --quiet
```

## 🏛️ Configuração dos Tribunais

### 1. Editar `config/tribunais.yaml`
```yaml
tribunais:
  tjsp:
    urls:
      rest: https://api.tjsp.jus.br
      base: https://esaj.tjsp.jus.br
    rate_limit:
      requests_por_minuto: 20  # Ajustar conforme necessário
    headers:
      User-Agent: "Sistema Jurídico Autorizado/1.0"
```

### 2. Testar Conectividade
```python
# test_tribunal.py
from src.pje_super.connection_manager import ConnectionManager
import asyncio

async def test():
    async with ConnectionManager() as cm:
        result = await cm.test_connectivity('tjsp')
        print(result)

asyncio.run(test())
```

## 🗄️ Banco de Dados

### 1. Configurar PostgreSQL
```bash
sudo -u postgres psql

CREATE DATABASE jurisprudencia_db;
CREATE USER jurisprudencia_user WITH ENCRYPTED PASSWORD 'senha_forte';
GRANT ALL PRIVILEGES ON DATABASE jurisprudencia_db TO jurisprudencia_user;

-- Extensões necessárias
\c jurisprudencia_db
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
```

### 2. Configurar Conexão
```bash
# postgresql.conf
sudo nano /etc/postgresql/13/main/postgresql.conf

# Ajustar:
max_connections = 200
shared_buffers = 256MB
```

### 3. Executar Migrações
```bash
cd /opt/jurisprudencia-platform
source venv/bin/activate
alembic upgrade head
```

## 🔒 Segurança

### 1. Firewall (UFW)
```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 8501/tcp  # Apenas se necessário externamente
sudo ufw enable
```

### 2. Fail2Ban
```bash
# Criar jail para aplicação
sudo nano /etc/fail2ban/jail.local

[jurisprudencia]
enabled = true
port = 8000,8501
filter = jurisprudencia
logpath = /opt/jurisprudencia-platform/logs/access.log
maxretry = 5
bantime = 3600
```

### 3. Nginx como Proxy Reverso
```nginx
# /etc/nginx/sites-available/jurisprudencia
server {
    listen 80;
    server_name seu-dominio.com.br;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name seu-dominio.com.br;
    
    ssl_certificate /etc/letsencrypt/live/seu-dominio.com.br/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/seu-dominio.com.br/privkey.pem;
    
    # API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Streamlit
    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

### 4. Hardening Adicional
```bash
# Desabilitar root SSH
sudo nano /etc/ssh/sshd_config
# PermitRootLogin no

# Configurar 2FA
sudo apt install libpam-google-authenticator
google-authenticator
```

## 🚀 Deploy e Execução

### 1. Serviços Systemd

#### API Service
```bash
sudo cp /tmp/jurisprudencia-api.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable jurisprudencia-api
sudo systemctl start jurisprudencia-api
```

#### Worker Service
```bash
sudo cp /tmp/jurisprudencia-worker.service /etc/systemd/system/
sudo systemctl enable jurisprudencia-worker
sudo systemctl start jurisprudencia-worker
```

### 2. Supervisor (Alternativa)
```ini
# /etc/supervisor/conf.d/jurisprudencia.conf
[program:jurisprudencia-api]
command=/opt/jurisprudencia-platform/venv/bin/uvicorn src.api.main:app --host 0.0.0.0 --port 8000
directory=/opt/jurisprudencia-platform
user=jurisprudencia
autostart=true
autorestart=true
```

### 3. Docker Compose (Opcional)
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## 📊 Monitoramento

### 1. Prometheus
```bash
# prometheus.yml já configurado
cd monitoring
docker-compose -f docker-compose.monitoring.yml up -d
```

### 2. Grafana
- Acesse: http://localhost:3000
- Login: admin / admin123
- Importe dashboards de `monitoring/grafana-dashboards/`

### 3. Logs Centralizados
```bash
# Visualizar logs
tail -f /opt/jurisprudencia-platform/logs/api.log
tail -f /opt/jurisprudencia-platform/logs/worker.log

# Logs do sistema
journalctl -u jurisprudencia-api -f
```

### 4. Alertas
Configure alertas no AlertManager para:
- API fora do ar
- Alto uso de CPU/memória
- Erros frequentes
- Filas congestionadas

## 💾 Backup e Recuperação

### 1. Backup Automático
```bash
# Script de backup
sudo nano /opt/scripts/backup-jurisprudencia.sh

#!/bin/bash
BACKUP_DIR="/backups/jurisprudencia"
DATE=$(date +%Y%m%d_%H%M%S)

# Backup do banco
pg_dump jurisprudencia_db > $BACKUP_DIR/db_$DATE.sql

# Backup de arquivos
tar -czf $BACKUP_DIR/files_$DATE.tar.gz /opt/jurisprudencia-platform/data

# Manter apenas últimos 30 dias
find $BACKUP_DIR -name "*.sql" -mtime +30 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
```

### 2. Cron para Backup
```bash
sudo crontab -e
# Adicionar:
0 3 * * * /opt/scripts/backup-jurisprudencia.sh
```

### 3. Recuperação
```bash
# Restaurar banco
psql jurisprudencia_db < backup.sql

# Restaurar arquivos
tar -xzf files_backup.tar.gz -C /
```

## 🔧 Troubleshooting

### Problemas Comuns

#### 1. Erro de Conexão com Tribunal
```bash
# Verificar logs
grep ERROR logs/api.log | tail -20

# Testar conectividade
curl -I https://esaj.tjsp.jus.br

# Verificar rate limiting
# Reduzir requests_por_minuto em config/tribunais.yaml
```

#### 2. Certificado Digital Não Reconhecido
```bash
# Verificar certificado
openssl x509 -in /opt/certs/certificado.pem -text -noout

# Testar com curl
curl --cert /opt/certs/certificado.pem https://tribunal.jus.br
```

#### 3. Performance Lenta
```bash
# Verificar recursos
htop
iotop

# Otimizar PostgreSQL
sudo -u postgres psql -c "VACUUM ANALYZE;"

# Verificar índices
psql jurisprudencia_db -c "\di"
```

#### 4. Erros de Validação CNJ
```python
# Testar validador
from src.utils.cnj_validator import validar_numero_cnj
print(validar_numero_cnj("0000001-02.2023.8.26.0001"))
```

### Logs Úteis
- API: `/opt/jurisprudencia-platform/logs/api.log`
- Worker: `/opt/jurisprudencia-platform/logs/worker.log`
- Nginx: `/var/log/nginx/access.log`
- PostgreSQL: `/var/log/postgresql/postgresql-13-main.log`

### Comandos de Diagnóstico
```bash
# Status dos serviços
systemctl status jurisprudencia-*

# Conexões ativas
ss -tulpn | grep LISTEN

# Uso de recursos
ps aux | grep python

# Espaço em disco
df -h
```

## 📞 Suporte

Para problemas não cobertos neste guia:

1. Consulte os logs detalhados
2. Verifique a documentação da API do tribunal
3. Entre em contato com o suporte técnico
4. Abra uma issue no repositório

## 🎯 Checklist Final

- [ ] Sistema operacional atualizado
- [ ] Dependências instaladas
- [ ] Credenciais configuradas
- [ ] Certificados digitais instalados
- [ ] Banco de dados configurado
- [ ] Redis rodando
- [ ] Nginx configurado
- [ ] SSL/TLS ativo
- [ ] Firewall configurado
- [ ] Serviços systemd ativos
- [ ] Monitoramento funcionando
- [ ] Backup automático configurado
- [ ] Testes de integração passando

🚀 **Sistema pronto para produção!**