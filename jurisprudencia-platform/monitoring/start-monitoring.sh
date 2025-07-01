#!/bin/bash

# Script para iniciar stack de monitoramento

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}=== Iniciando Stack de Monitoramento ===${NC}"

# Verificar se Docker está rodando
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}Erro: Docker não está rodando${NC}"
    exit 1
fi

# Criar network se não existir
if ! docker network ls | grep -q jurisprudencia-network; then
    echo -e "${YELLOW}Criando network jurisprudencia-network...${NC}"
    docker network create jurisprudencia-network
fi

# Criar diretórios necessários
echo -e "${YELLOW}Criando diretórios...${NC}"
mkdir -p logs
mkdir -p data/prometheus
mkdir -p data/grafana
mkdir -p data/elasticsearch

# Definir permissões
echo -e "${YELLOW}Configurando permissões...${NC}"
sudo chown -R 1000:1000 data/grafana
sudo chown -R 1000:1000 data/elasticsearch

# Verificar se aplicação principal está rodando
if ! docker-compose ps api | grep -q "Up"; then
    echo -e "${YELLOW}Aplicação principal não está rodando. Iniciando...${NC}"
    docker-compose up -d
    
    echo -e "${YELLOW}Aguardando aplicação ficar pronta...${NC}"
    sleep 30
fi

# Iniciar stack de monitoramento
echo -e "${YELLOW}Iniciando serviços de monitoramento...${NC}"
docker-compose -f monitoring/docker-compose.monitoring.yml up -d

# Aguardar serviços ficarem prontos
echo -e "${YELLOW}Aguardando serviços ficarem prontos...${NC}"
sleep 20

# Verificar status
echo -e "\n${YELLOW}Status dos serviços:${NC}"
docker-compose -f monitoring/docker-compose.monitoring.yml ps

# Verificar se serviços estão respondendo
echo -e "\n${YELLOW}Verificando conectividade...${NC}"

check_service() {
    local service=$1
    local url=$2
    local timeout=30
    local count=0
    
    echo -ne "${YELLOW}Verificando $service...${NC}"
    
    while [ $count -lt $timeout ]; do
        if curl -s "$url" > /dev/null 2>&1; then
            echo -e " ${GREEN}✓${NC}"
            return 0
        fi
        sleep 1
        count=$((count + 1))
        echo -ne "."
    done
    
    echo -e " ${RED}✗${NC}"
    return 1
}

# Verificar serviços
check_service "Prometheus" "http://localhost:9090/-/healthy"
check_service "Grafana" "http://localhost:3000/api/health"
check_service "AlertManager" "http://localhost:9093/-/healthy"
check_service "Elasticsearch" "http://localhost:9200/_cluster/health"
check_service "Kibana" "http://localhost:5601/api/status"

echo -e "\n${GREEN}=== Stack de Monitoramento Iniciada ===${NC}"
echo -e "${YELLOW}URLs de acesso:${NC}"
echo -e "  Prometheus: http://localhost:9090"
echo -e "  Grafana: http://localhost:3000 (admin/admin123)"
echo -e "  AlertManager: http://localhost:9093"
echo -e "  Kibana: http://localhost:5601"
echo -e "  Flower: http://localhost:5555"
echo -e "  API Metrics: http://localhost:8000/metrics"

echo -e "\n${YELLOW}Para parar o monitoramento:${NC}"
echo -e "  docker-compose -f monitoring/docker-compose.monitoring.yml down"

echo -e "\n${YELLOW}Para visualizar logs:${NC}"
echo -e "  docker-compose -f monitoring/docker-compose.monitoring.yml logs -f [service]"