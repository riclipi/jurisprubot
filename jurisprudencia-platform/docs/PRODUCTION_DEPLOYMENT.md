# 🚀 GUIA COMPLETO DE DEPLOYMENT PARA PRODUÇÃO

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Requisitos](#requisitos)
3. [Configuração Inicial](#configuração-inicial)
4. [Deploy com Docker](#deploy-com-docker)
5. [Deploy em Kubernetes](#deploy-em-kubernetes)
6. [Segurança](#segurança)
7. [Monitoramento](#monitoramento)
8. [Backup e Recuperação](#backup-e-recuperação)
9. [Troubleshooting](#troubleshooting)

## 🎯 Visão Geral

Este guia cobre o deployment completo da Plataforma de Jurisprudência em ambiente de produção.

### Arquitetura

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Load Balancer │────▶│   Application   │────▶│    Database     │
│    (Nginx)      │     │   (FastAPI)     │     │  (PostgreSQL)   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
         │                       │                        │
         ▼                       ▼                        ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│      CDN        │     │     Redis       │     │   ChromaDB      │
│  (CloudFlare)   │     │    (Cache)      │     │  (Embeddings)   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## 🔧 Requisitos

### Hardware Mínimo
- **CPU**: 4 cores (8 recomendado)
- **RAM**: 16GB (32GB recomendado)
- **Disco**: 100GB SSD (RAID 10 recomendado)
- **Rede**: 1Gbps

### Software
- **OS**: Ubuntu 22.04 LTS
- **Docker**: 24.0+
- **Docker Compose**: 2.20+
- **PostgreSQL**: 15+
- **Redis**: 7.0+
- **Python**: 3.11+

## 🚀 Configuração Inicial

### 1. Preparar Servidor

```bash
# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar dependências
sudo apt install -y \
    curl \
    wget \
    git \
    build-essential \
    python3.11 \
    python3.11-venv \
    postgresql-client \
    redis-tools \
    htop \
    iotop \
    nethogs

# Instalar Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Instalar Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 2. Configurar Firewall

```bash
# UFW (Ubuntu Firewall)
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 5432/tcp  # PostgreSQL (apenas se externo)
sudo ufw allow 6379/tcp  # Redis (apenas se externo)
sudo ufw enable
```

### 3. Configurar Limites do Sistema

```bash
# /etc/security/limits.conf
cat << EOF | sudo tee -a /etc/security/limits.conf
* soft nofile 65536
* hard nofile 65536
* soft nproc 65536
* hard nproc 65536
EOF

# /etc/sysctl.conf
cat << EOF | sudo tee -a /etc/sysctl.conf
# Network optimizations
net.core.somaxconn = 65536
net.ipv4.tcp_max_syn_backlog = 65536
net.ipv4.ip_local_port_range = 1024 65535
net.ipv4.tcp_tw_reuse = 1

# Memory optimizations
vm.overcommit_memory = 1
vm.swappiness = 10
EOF

sudo sysctl -p
```

## 🐳 Deploy com Docker

### 1. Clone e Configure

```bash
# Clone repositório
git clone https://github.com/your-org/jurisprudencia-platform.git
cd jurisprudencia-platform

# Criar arquivo .env
cp .env.example .env.production
```

### 2. Configurar Variáveis de Ambiente

```bash
# .env.production
# Banco de Dados
DATABASE_URL=postgresql://juris_user:STRONG_PASSWORD@db:5432/jurisprudencia
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=40

# Redis
REDIS_URL=redis://redis:6379/0
REDIS_PASSWORD=STRONG_REDIS_PASSWORD

# ChromaDB
CHROMADB_HOST=chromadb
CHROMADB_PORT=8000

# Segurança
SECRET_KEY=your-256-bit-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here
ENCRYPTION_KEY=your-fernet-key-here

# API Keys
TRIBUNAL_API_KEY=your-tribunal-api-key
STJ_API_KEY=your-stj-api-key

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Monitoring
SENTRY_DSN=https://xxx@sentry.io/xxx
PROMETHEUS_ENABLED=true

# Features
ENABLE_CACHE=true
ENABLE_RATE_LIMIT=true
ENABLE_AUDIT=true
```

### 3. Build e Deploy

```bash
# Build images
docker-compose -f docker-compose.production.yml build

# Iniciar em modo detached
docker-compose -f docker-compose.production.yml up -d

# Verificar status
docker-compose -f docker-compose.production.yml ps

# Ver logs
docker-compose -f docker-compose.production.yml logs -f
```

### 4. Inicializar Banco de Dados

```bash
# Executar migrações
docker-compose -f docker-compose.production.yml exec app python manage_db.py init
docker-compose -f docker-compose.production.yml exec app python manage_db.py migrate

# Criar usuário admin
docker-compose -f docker-compose.production.yml exec app python scripts/create_admin.py
```

## ☸️ Deploy em Kubernetes

### 1. Preparar Cluster

```bash
# Instalar kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# Configurar kubectl
mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config
```

### 2. Deploy com Helm

```bash
# Adicionar repo Helm
helm repo add jurisprudencia https://charts.jurisprudencia.com
helm repo update

# Instalar
helm install jurisprudencia jurisprudencia/platform \
  --namespace production \
  --create-namespace \
  --values k8s/values.production.yaml
```

### 3. Configurar Ingress

```yaml
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: jurisprudencia-ingress
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/rate-limit: "100"
spec:
  tls:
  - hosts:
    - api.jurisprudencia.com
    secretName: jurisprudencia-tls
  rules:
  - host: api.jurisprudencia.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: jurisprudencia-api
            port:
              number: 8000
```

## 🔒 Segurança

### 1. SSL/TLS

```bash
# Instalar Certbot
sudo snap install --classic certbot
sudo ln -s /snap/bin/certbot /usr/bin/certbot

# Obter certificado
sudo certbot certonly --standalone -d api.jurisprudencia.com

# Auto-renovação
sudo certbot renew --dry-run
```

### 2. Configurar Nginx

```nginx
# /etc/nginx/sites-available/jurisprudencia
server {
    listen 80;
    server_name api.jurisprudencia.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.jurisprudencia.com;

    ssl_certificate /etc/letsencrypt/live/api.jurisprudencia.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.jurisprudencia.com/privkey.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req zone=api burst=20 nodelay;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

### 3. Hardening do Sistema

```bash
# Fail2ban
sudo apt install fail2ban -y

# Configurar jail
cat << EOF | sudo tee /etc/fail2ban/jail.local
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[sshd]
enabled = true

[nginx-limit-req]
enabled = true
filter = nginx-limit-req
action = iptables-multiport[name=ReqLimit, port="http,https"]
logpath = /var/log/nginx/error.log
EOF

sudo systemctl restart fail2ban
```

## 📊 Monitoramento

### 1. Prometheus + Grafana

```bash
# docker-compose.monitoring.yml
docker-compose -f docker-compose.monitoring.yml up -d

# Acessar
# Grafana: http://localhost:3000 (admin/admin)
# Prometheus: http://localhost:9090
```

### 2. Configurar Alertas

```yaml
# prometheus/alerts.yml
groups:
  - name: jurisprudencia
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is above 5%"

      - alert: HighMemoryUsage
        expr: (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) > 0.9
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage"
          description: "Memory usage is above 90%"
```

### 3. Logs Centralizados

```bash
# ELK Stack
docker run -d \
  --name elasticsearch \
  -p 9200:9200 \
  -e "discovery.type=single-node" \
  -e "ES_JAVA_OPTS=-Xms1g -Xmx1g" \
  elasticsearch:8.10.0

docker run -d \
  --name kibana \
  -p 5601:5601 \
  --link elasticsearch \
  -e "ELASTICSEARCH_HOSTS=http://elasticsearch:9200" \
  kibana:8.10.0
```

## 💾 Backup e Recuperação

### 1. Backup Automático

```bash
#!/bin/bash
# /scripts/backup.sh

# Configurações
BACKUP_DIR="/backups"
DB_NAME="jurisprudencia"
RETENTION_DAYS=30

# Criar diretório
mkdir -p $BACKUP_DIR

# Timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Backup banco de dados
docker-compose -f docker-compose.production.yml exec -T db \
  pg_dump -U postgres $DB_NAME | gzip > $BACKUP_DIR/db_$TIMESTAMP.sql.gz

# Backup arquivos
tar czf $BACKUP_DIR/files_$TIMESTAMP.tar.gz ./uploads ./downloads_cache

# Backup Redis
docker-compose -f docker-compose.production.yml exec -T redis \
  redis-cli BGSAVE

# Limpar backups antigos
find $BACKUP_DIR -type f -mtime +$RETENTION_DAYS -delete

# Upload para S3 (opcional)
aws s3 sync $BACKUP_DIR s3://jurisprudencia-backups/
```

### 2. Cron para Backup

```bash
# Adicionar ao crontab
0 2 * * * /scripts/backup.sh >> /var/log/backup.log 2>&1
```

### 3. Restauração

```bash
#!/bin/bash
# /scripts/restore.sh

BACKUP_FILE=$1
DB_NAME="jurisprudencia"

# Restaurar banco
gunzip -c $BACKUP_FILE | docker-compose -f docker-compose.production.yml exec -T db \
  psql -U postgres $DB_NAME

# Restaurar arquivos
tar xzf files_backup.tar.gz -C /
```

## 🔧 Troubleshooting

### Problemas Comuns

#### 1. Alta Latência
```bash
# Verificar conexões
netstat -an | grep ESTABLISHED | wc -l

# Verificar CPU
htop

# Verificar I/O
iotop

# Logs de slow queries
docker-compose logs db | grep "duration:"
```

#### 2. Memória Insuficiente
```bash
# Verificar memória
free -h

# Verificar swap
swapon --show

# Adicionar swap
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

#### 3. Disco Cheio
```bash
# Verificar espaço
df -h

# Encontrar arquivos grandes
find / -type f -size +100M -exec ls -lh {} \; 2>/dev/null

# Limpar Docker
docker system prune -a --volumes
```

### Comandos Úteis

```bash
# Reiniciar serviços
docker-compose -f docker-compose.production.yml restart

# Escalar serviços
docker-compose -f docker-compose.production.yml up -d --scale app=4

# Backup rápido
docker-compose -f docker-compose.production.yml exec db pg_dump -U postgres jurisprudencia > backup.sql

# Verificar saúde
curl http://localhost:8000/health

# Métricas
curl http://localhost:8000/metrics
```

## 📞 Suporte

- **Email**: suporte@jurisprudencia.com
- **Slack**: jurisprudencia.slack.com
- **Docs**: docs.jurisprudencia.com
- **Status**: status.jurisprudencia.com

---

**Última atualização**: Janeiro 2025