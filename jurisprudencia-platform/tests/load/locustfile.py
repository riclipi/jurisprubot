#!/usr/bin/env python3
"""
🦗 TESTE DE CARGA COM LOCUST
Framework profissional para testes de carga distribuídos
"""

from locust import HttpUser, task, between, events
from locust.env import Environment
from locust.stats import stats_printer, stats_history
from locust.log import setup_logging
import json
import random
import time
from datetime import datetime
import logging

# Configurar logging
setup_logging("INFO", None)
logger = logging.getLogger(__name__)


class JurisprudenciaUser(HttpUser):
    """Usuário simulado do sistema de jurisprudência"""
    
    wait_time = between(1, 3)  # Espera entre 1-3 segundos entre requisições
    
    def on_start(self):
        """Executado quando usuário inicia"""
        # Fazer login se necessário
        self.token = None
        self.processo_ids = []
        self.documento_ids = []
        
        # Tentar fazer login
        response = self.client.post("/auth/login", json={
            "username": "test_user",
            "password": "test_password"
        }, catch_response=True)
        
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("access_token")
            self.client.headers.update({"Authorization": f"Bearer {self.token}"})
            response.success()
        else:
            response.failure("Login failed")
    
    @task(10)
    def list_processos(self):
        """Listar processos (alta frequência)"""
        with self.client.get("/api/processos", 
                            params={"limit": 20, "offset": 0},
                            catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                # Armazenar IDs para outros testes
                if "items" in data:
                    self.processo_ids.extend([p["id"] for p in data["items"]])
                response.success()
            else:
                response.failure(f"Got status code {response.status_code}")
    
    @task(5)
    def get_processo_details(self):
        """Obter detalhes de um processo"""
        if not self.processo_ids:
            return
        
        processo_id = random.choice(self.processo_ids)
        
        with self.client.get(f"/api/processos/{processo_id}",
                            catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                response.failure("Processo not found")
            else:
                response.failure(f"Got status code {response.status_code}")
    
    @task(3)
    def search_processos(self):
        """Buscar processos"""
        search_terms = ["contrato", "indenização", "trabalhista", "civil", "penal"]
        query = random.choice(search_terms)
        
        with self.client.post("/api/processos/search",
                             json={"query": query, "limit": 10},
                             catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Search failed with {response.status_code}")
    
    @task(2)
    def download_documento(self):
        """Download de documento"""
        if not self.documento_ids:
            # Primeiro obter lista de documentos
            response = self.client.get("/api/documentos")
            if response.status_code == 200:
                data = response.json()
                if "items" in data:
                    self.documento_ids = [d["id"] for d in data["items"]]
            
            if not self.documento_ids:
                return
        
        doc_id = random.choice(self.documento_ids)
        
        with self.client.get(f"/api/documentos/{doc_id}/download",
                            catch_response=True,
                            stream=True) as response:
            if response.status_code == 200:
                # Simular download
                content = response.content
                response.success()
            else:
                response.failure(f"Download failed with {response.status_code}")
    
    @task(1)
    def create_processo(self):
        """Criar novo processo (baixa frequência)"""
        processo_data = {
            "numero_cnj": self._generate_cnj(),
            "titulo": f"Processo Teste {random.randint(1000, 9999)}",
            "descricao": "Processo criado durante teste de carga",
            "valor_causa": random.uniform(10000, 1000000),
            "tipo": random.choice(["civil", "trabalhista", "penal"])
        }
        
        with self.client.post("/api/processos",
                             json=processo_data,
                             catch_response=True) as response:
            if response.status_code in [200, 201]:
                data = response.json()
                if "id" in data:
                    self.processo_ids.append(data["id"])
                response.success()
            else:
                response.failure(f"Create failed with {response.status_code}")
    
    @task(8)
    def check_health(self):
        """Verificar saúde do sistema"""
        with self.client.get("/health",
                            catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed with {response.status_code}")
    
    def _generate_cnj(self):
        """Gerar número CNJ válido para teste"""
        # Formato: NNNNNNN-DD.AAAA.J.TR.OOOO
        sequencial = str(random.randint(1, 9999999)).zfill(7)
        ano = datetime.now().year
        segmento = "8"  # Justiça Estadual
        tribunal = "26"  # TJSP
        origem = str(random.randint(1, 9999)).zfill(4)
        
        # Calcular dígitos verificadores (simplificado)
        dv = str(random.randint(10, 99))
        
        return f"{sequencial}-{dv}.{ano}.{segmento}.{tribunal}.{origem}"


class AdminUser(HttpUser):
    """Usuário administrativo com operações diferentes"""
    
    wait_time = between(2, 5)  # Admins fazem menos requisições
    weight = 1  # Proporção menor de admins (10% dos users)
    
    def on_start(self):
        """Login como admin"""
        response = self.client.post("/auth/login", json={
            "username": "admin",
            "password": "admin_password"
        })
        
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("access_token")
            self.client.headers.update({"Authorization": f"Bearer {self.token}"})
    
    @task(5)
    def view_dashboard(self):
        """Visualizar dashboard"""
        self.client.get("/api/admin/dashboard")
    
    @task(3)
    def view_statistics(self):
        """Ver estatísticas"""
        self.client.get("/api/admin/statistics", params={
            "start_date": "2024-01-01",
            "end_date": datetime.now().strftime("%Y-%m-%d")
        })
    
    @task(2)
    def manage_users(self):
        """Gerenciar usuários"""
        self.client.get("/api/admin/users", params={"limit": 50})
    
    @task(1)
    def view_audit_logs(self):
        """Ver logs de auditoria"""
        self.client.get("/api/admin/audit-logs", params={
            "limit": 100,
            "event_type": "data_access"
        })


class MobileUser(HttpUser):
    """Usuário mobile com comportamento específico"""
    
    wait_time = between(3, 8)  # Mobile users são mais lentos
    weight = 3  # 30% dos usuários são mobile
    
    def on_start(self):
        """Configurar headers mobile"""
        self.client.headers.update({
            "User-Agent": "JurisprudenciaApp/1.0 (Android 12)",
            "X-App-Version": "1.0.0",
            "X-Device-ID": f"device_{random.randint(1000, 9999)}"
        })
        
        # Login simplificado
        response = self.client.post("/auth/mobile/login", json={
            "username": "mobile_user",
            "password": "mobile_pass",
            "device_id": self.client.headers["X-Device-ID"]
        })
        
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("access_token")
            self.client.headers.update({"Authorization": f"Bearer {self.token}"})
    
    @task(10)
    def quick_search(self):
        """Busca rápida (mobile)"""
        query = random.choice(["123", "silva", "2024"])
        self.client.get(f"/api/mobile/quick-search", params={
            "q": query,
            "limit": 5
        })
    
    @task(5)
    def view_recent_processos(self):
        """Ver processos recentes"""
        self.client.get("/api/mobile/processos/recent")
    
    @task(3)
    def sync_offline_data(self):
        """Sincronizar dados offline"""
        sync_data = {
            "last_sync": datetime.now().isoformat(),
            "device_id": self.client.headers["X-Device-ID"],
            "pending_changes": []
        }
        
        self.client.post("/api/mobile/sync", json=sync_data)
    
    @task(1)
    def upload_photo(self):
        """Upload de foto de documento"""
        # Simular upload de imagem
        files = {
            'file': ('document.jpg', b'fake image data', 'image/jpeg')
        }
        
        self.client.post("/api/mobile/documents/upload", 
                        files=files,
                        data={"processo_id": "123"})


# Event handlers para coletar métricas customizadas
@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """Handler para cada requisição"""
    if exception:
        logger.error(f"Request failed: {name} - {exception}")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Executado no início do teste"""
    logger.info(f"Teste iniciado com {environment.parsed_options.num_users} usuários")
    logger.info(f"Taxa de spawn: {environment.parsed_options.spawn_rate}/s")
    logger.info(f"Host: {environment.parsed_options.host}")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Executado no final do teste"""
    logger.info("Teste finalizado")
    
    # Salvar estatísticas
    stats_data = {
        "start_time": environment.stats.start_time,
        "total_requests": environment.stats.num_requests,
        "num_failures": environment.stats.num_failures,
        "avg_response_time": environment.stats.total.avg_response_time,
        "median_response_time": environment.stats.total.median_response_time,
        "p95_response_time": environment.stats.total.get_response_time_percentile(0.95),
        "p99_response_time": environment.stats.total.get_response_time_percentile(0.99),
        "requests_per_second": environment.stats.total.current_rps
    }
    
    with open(f"locust_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", "w") as f:
        json.dump(stats_data, f, indent=2)


# Configuração para execução standalone
if __name__ == "__main__":
    # Pode ser executado com:
    # locust -f locustfile.py --host=http://localhost:8000 --users=100 --spawn-rate=10 --run-time=5m
    pass