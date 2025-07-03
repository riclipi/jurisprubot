#!/usr/bin/env python3
"""
🔥 TESTES DE CARGA E STRESS
Testes de desempenho para validar capacidade do sistema
"""

import asyncio
import aiohttp
import time
import random
import statistics
import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from concurrent.futures import ThreadPoolExecutor
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class TestResult:
    """Resultado de um teste individual"""
    request_id: str
    endpoint: str
    method: str
    status_code: int
    response_time: float
    timestamp: datetime
    error: Optional[str] = None
    response_size: int = 0


@dataclass
class TestMetrics:
    """Métricas agregadas de teste"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_time: float = 0
    response_times: List[float] = field(default_factory=list)
    status_codes: Dict[int, int] = field(default_factory=lambda: defaultdict(int))
    errors: List[str] = field(default_factory=list)
    requests_per_second: float = 0
    
    @property
    def success_rate(self) -> float:
        if self.total_requests == 0:
            return 0
        return (self.successful_requests / self.total_requests) * 100
    
    @property
    def avg_response_time(self) -> float:
        if not self.response_times:
            return 0
        return statistics.mean(self.response_times)
    
    @property
    def median_response_time(self) -> float:
        if not self.response_times:
            return 0
        return statistics.median(self.response_times)
    
    def percentile(self, p: int) -> float:
        if not self.response_times:
            return 0
        return np.percentile(self.response_times, p)


class LoadTestScenario:
    """Cenário de teste de carga"""
    
    def __init__(self, name: str, base_url: str):
        self.name = name
        self.base_url = base_url
        self.endpoints: List[Dict[str, Any]] = []
        self.auth_token: Optional[str] = None
        self.headers: Dict[str, str] = {}
    
    def add_endpoint(self, method: str, path: str, 
                    weight: float = 1.0, 
                    payload: Optional[Dict] = None,
                    params: Optional[Dict] = None):
        """Adicionar endpoint ao cenário"""
        self.endpoints.append({
            'method': method,
            'path': path,
            'weight': weight,
            'payload': payload,
            'params': params
        })
    
    def set_auth(self, token: str):
        """Configurar autenticação"""
        self.auth_token = token
        self.headers['Authorization'] = f'Bearer {token}'
    
    def get_random_endpoint(self) -> Dict[str, Any]:
        """Obter endpoint aleatório baseado em pesos"""
        if not self.endpoints:
            raise ValueError("Nenhum endpoint configurado")
        
        weights = [e['weight'] for e in self.endpoints]
        return random.choices(self.endpoints, weights=weights)[0]


class LoadTester:
    """Executor de testes de carga"""
    
    def __init__(self):
        self.results: List[TestResult] = []
        self.metrics = TestMetrics()
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
    
    async def run_scenario(self, scenario: LoadTestScenario,
                          duration_seconds: int = 60,
                          concurrent_users: int = 10,
                          ramp_up_seconds: int = 0) -> TestMetrics:
        """Executar cenário de teste"""
        logger.info(f"Iniciando teste: {scenario.name}")
        logger.info(f"Duração: {duration_seconds}s, Usuários: {concurrent_users}")
        
        self.start_time = time.time()
        end_time = self.start_time + duration_seconds
        
        # Criar sessões para usuários
        sessions = []
        for i in range(concurrent_users):
            session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            )
            sessions.append(session)
        
        try:
            # Iniciar usuários com ramp-up
            tasks = []
            for i, session in enumerate(sessions):
                delay = (i / concurrent_users) * ramp_up_seconds if ramp_up_seconds > 0 else 0
                task = asyncio.create_task(
                    self._user_loop(session, scenario, end_time, delay)
                )
                tasks.append(task)
            
            # Aguardar conclusão
            await asyncio.gather(*tasks)
            
        finally:
            # Fechar sessões
            for session in sessions:
                await session.close()
        
        self.end_time = time.time()
        
        # Calcular métricas
        self._calculate_metrics()
        
        return self.metrics
    
    async def _user_loop(self, session: aiohttp.ClientSession,
                        scenario: LoadTestScenario,
                        end_time: float,
                        initial_delay: float = 0):
        """Loop de requisições de um usuário"""
        if initial_delay > 0:
            await asyncio.sleep(initial_delay)
        
        request_count = 0
        
        while time.time() < end_time:
            # Selecionar endpoint
            endpoint = scenario.get_random_endpoint()
            
            # Executar requisição
            result = await self._make_request(
                session,
                scenario.base_url,
                endpoint,
                scenario.headers
            )
            
            self.results.append(result)
            request_count += 1
            
            # Think time aleatório (0-100ms)
            await asyncio.sleep(random.uniform(0, 0.1))
        
        logger.debug(f"Usuário completou {request_count} requisições")
    
    async def _make_request(self, session: aiohttp.ClientSession,
                           base_url: str,
                           endpoint: Dict[str, Any],
                           headers: Dict[str, str]) -> TestResult:
        """Fazer requisição HTTP"""
        url = f"{base_url}{endpoint['path']}"
        method = endpoint['method']
        request_id = f"{time.time()}_{random.randint(1000, 9999)}"
        
        start_time = time.time()
        
        try:
            async with session.request(
                method=method,
                url=url,
                headers=headers,
                json=endpoint.get('payload'),
                params=endpoint.get('params')
            ) as response:
                response_time = time.time() - start_time
                content = await response.read()
                
                return TestResult(
                    request_id=request_id,
                    endpoint=endpoint['path'],
                    method=method,
                    status_code=response.status,
                    response_time=response_time * 1000,  # ms
                    timestamp=datetime.now(),
                    response_size=len(content)
                )
                
        except asyncio.TimeoutError:
            return TestResult(
                request_id=request_id,
                endpoint=endpoint['path'],
                method=method,
                status_code=0,
                response_time=(time.time() - start_time) * 1000,
                timestamp=datetime.now(),
                error="Timeout"
            )
            
        except Exception as e:
            return TestResult(
                request_id=request_id,
                endpoint=endpoint['path'],
                method=method,
                status_code=0,
                response_time=(time.time() - start_time) * 1000,
                timestamp=datetime.now(),
                error=str(e)
            )
    
    def _calculate_metrics(self):
        """Calcular métricas agregadas"""
        self.metrics.total_requests = len(self.results)
        
        for result in self.results:
            if 200 <= result.status_code < 400:
                self.metrics.successful_requests += 1
            else:
                self.metrics.failed_requests += 1
                
            self.metrics.response_times.append(result.response_time)
            self.metrics.status_codes[result.status_code] += 1
            
            if result.error:
                self.metrics.errors.append(result.error)
        
        if self.start_time and self.end_time:
            self.metrics.total_time = self.end_time - self.start_time
            self.metrics.requests_per_second = (
                self.metrics.total_requests / self.metrics.total_time
            )


class StressTester(LoadTester):
    """Teste de stress com aumento gradual de carga"""
    
    async def run_stress_test(self, scenario: LoadTestScenario,
                            initial_users: int = 10,
                            max_users: int = 1000,
                            step_users: int = 10,
                            step_duration: int = 30) -> List[TestMetrics]:
        """Executar teste de stress"""
        logger.info(f"Iniciando teste de stress: {scenario.name}")
        logger.info(f"Usuários: {initial_users} -> {max_users}, Step: {step_users}")
        
        all_metrics = []
        current_users = initial_users
        
        while current_users <= max_users:
            logger.info(f"\n=== Testando com {current_users} usuários ===")
            
            # Reset para novo teste
            self.results = []
            self.metrics = TestMetrics()
            
            # Executar teste
            metrics = await self.run_scenario(
                scenario,
                duration_seconds=step_duration,
                concurrent_users=current_users
            )
            
            # Adicionar informação de usuários
            metrics.concurrent_users = current_users
            all_metrics.append(metrics)
            
            # Verificar breaking point
            if metrics.success_rate < 95 or metrics.percentile(95) > 5000:
                logger.warning(f"Sistema degradando com {current_users} usuários")
                logger.warning(f"Taxa de sucesso: {metrics.success_rate:.1f}%")
                logger.warning(f"P95: {metrics.percentile(95):.0f}ms")
                
                if metrics.success_rate < 80:
                    logger.error("Breaking point atingido!")
                    break
            
            current_users += step_users
        
        return all_metrics


class LoadTestReporter:
    """Gerador de relatórios de teste"""
    
    def __init__(self):
        self.report_dir = "load_test_reports"
        self._ensure_report_dir()
    
    def _ensure_report_dir(self):
        """Garantir que diretório de relatórios existe"""
        import os
        os.makedirs(self.report_dir, exist_ok=True)
    
    def generate_report(self, test_name: str, metrics: TestMetrics,
                       results: Optional[List[TestResult]] = None):
        """Gerar relatório de teste"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_name = f"{test_name}_{timestamp}"
        
        # Relatório texto
        self._generate_text_report(report_name, metrics)
        
        # Gráficos
        if results:
            self._generate_charts(report_name, metrics, results)
        
        # JSON detalhado
        self._generate_json_report(report_name, metrics)
        
        logger.info(f"Relatório gerado: {self.report_dir}/{report_name}")
    
    def _generate_text_report(self, report_name: str, metrics: TestMetrics):
        """Gerar relatório em texto"""
        report_path = f"{self.report_dir}/{report_name}.txt"
        
        with open(report_path, 'w') as f:
            f.write(f"RELATÓRIO DE TESTE DE CARGA\n")
            f.write(f"{'=' * 50}\n\n")
            
            f.write(f"Resumo Geral:\n")
            f.write(f"  Total de requisições: {metrics.total_requests:,}\n")
            f.write(f"  Requisições bem-sucedidas: {metrics.successful_requests:,}\n")
            f.write(f"  Requisições falhas: {metrics.failed_requests:,}\n")
            f.write(f"  Taxa de sucesso: {metrics.success_rate:.2f}%\n")
            f.write(f"  Duração total: {metrics.total_time:.2f}s\n")
            f.write(f"  Requisições por segundo: {metrics.requests_per_second:.2f}\n\n")
            
            f.write(f"Tempos de Resposta (ms):\n")
            f.write(f"  Mínimo: {min(metrics.response_times):.2f}\n")
            f.write(f"  Médio: {metrics.avg_response_time:.2f}\n")
            f.write(f"  Mediana: {metrics.median_response_time:.2f}\n")
            f.write(f"  P90: {metrics.percentile(90):.2f}\n")
            f.write(f"  P95: {metrics.percentile(95):.2f}\n")
            f.write(f"  P99: {metrics.percentile(99):.2f}\n")
            f.write(f"  Máximo: {max(metrics.response_times):.2f}\n\n")
            
            f.write(f"Códigos de Status:\n")
            for code, count in sorted(metrics.status_codes.items()):
                percentage = (count / metrics.total_requests) * 100
                f.write(f"  {code}: {count:,} ({percentage:.1f}%)\n")
            
            if metrics.errors:
                f.write(f"\nErros Encontrados:\n")
                error_counts = defaultdict(int)
                for error in metrics.errors:
                    error_counts[error] += 1
                
                for error, count in sorted(error_counts.items(), 
                                         key=lambda x: x[1], reverse=True):
                    f.write(f"  {error}: {count}\n")
    
    def _generate_charts(self, report_name: str, metrics: TestMetrics,
                        results: List[TestResult]):
        """Gerar gráficos do teste"""
        plt.style.use('seaborn-v0_8-darkgrid')
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        
        # 1. Distribuição de tempos de resposta
        ax1 = axes[0, 0]
        ax1.hist(metrics.response_times, bins=50, alpha=0.7, color='blue', edgecolor='black')
        ax1.axvline(metrics.avg_response_time, color='red', linestyle='--', 
                   label=f'Média: {metrics.avg_response_time:.0f}ms')
        ax1.axvline(metrics.percentile(95), color='orange', linestyle='--',
                   label=f'P95: {metrics.percentile(95):.0f}ms')
        ax1.set_xlabel('Tempo de Resposta (ms)')
        ax1.set_ylabel('Frequência')
        ax1.set_title('Distribuição de Tempos de Resposta')
        ax1.legend()
        
        # 2. Timeline de requisições
        ax2 = axes[0, 1]
        timestamps = [r.timestamp for r in results]
        response_times = [r.response_time for r in results]
        
        # Agrupar por segundo
        seconds = defaultdict(list)
        for ts, rt in zip(timestamps, response_times):
            second = ts.replace(microsecond=0)
            seconds[second].append(rt)
        
        x = sorted(seconds.keys())
        y_avg = [statistics.mean(seconds[s]) for s in x]
        y_max = [max(seconds[s]) for s in x]
        
        ax2.plot(x, y_avg, label='Média', color='blue')
        ax2.plot(x, y_max, label='Máximo', color='red', alpha=0.5)
        ax2.set_xlabel('Tempo')
        ax2.set_ylabel('Tempo de Resposta (ms)')
        ax2.set_title('Evolução do Tempo de Resposta')
        ax2.legend()
        ax2.tick_params(axis='x', rotation=45)
        
        # 3. Taxa de requisições por segundo
        ax3 = axes[1, 0]
        req_per_sec = defaultdict(int)
        for r in results:
            second = r.timestamp.replace(microsecond=0)
            req_per_sec[second] += 1
        
        x = sorted(req_per_sec.keys())
        y = [req_per_sec[s] for s in x]
        
        ax3.plot(x, y, color='green')
        ax3.fill_between(x, y, alpha=0.3, color='green')
        ax3.set_xlabel('Tempo')
        ax3.set_ylabel('Requisições/s')
        ax3.set_title('Taxa de Requisições')
        ax3.tick_params(axis='x', rotation=45)
        
        # 4. Status codes
        ax4 = axes[1, 1]
        codes = list(metrics.status_codes.keys())
        counts = list(metrics.status_codes.values())
        colors = ['green' if 200 <= c < 300 else 'red' for c in codes]
        
        ax4.bar([str(c) for c in codes], counts, color=colors)
        ax4.set_xlabel('Código de Status')
        ax4.set_ylabel('Quantidade')
        ax4.set_title('Distribuição de Códigos de Status')
        
        plt.tight_layout()
        plt.savefig(f"{self.report_dir}/{report_name}_charts.png", dpi=300, bbox_inches='tight')
        plt.close()
    
    def _generate_json_report(self, report_name: str, metrics: TestMetrics):
        """Gerar relatório em JSON"""
        report_path = f"{self.report_dir}/{report_name}.json"
        
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_requests': metrics.total_requests,
                'successful_requests': metrics.successful_requests,
                'failed_requests': metrics.failed_requests,
                'success_rate': metrics.success_rate,
                'total_time': metrics.total_time,
                'requests_per_second': metrics.requests_per_second
            },
            'response_times': {
                'min': min(metrics.response_times) if metrics.response_times else 0,
                'avg': metrics.avg_response_time,
                'median': metrics.median_response_time,
                'p90': metrics.percentile(90),
                'p95': metrics.percentile(95),
                'p99': metrics.percentile(99),
                'max': max(metrics.response_times) if metrics.response_times else 0
            },
            'status_codes': dict(metrics.status_codes),
            'errors': list(set(metrics.errors))
        }
        
        with open(report_path, 'w') as f:
            json.dump(report_data, f, indent=2)
    
    def generate_stress_report(self, test_name: str, 
                             all_metrics: List[TestMetrics]):
        """Gerar relatório de teste de stress"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_name = f"{test_name}_stress_{timestamp}"
        
        # Gráfico de escalabilidade
        plt.figure(figsize=(12, 8))
        
        users = [m.concurrent_users for m in all_metrics]
        success_rates = [m.success_rate for m in all_metrics]
        p95_times = [m.percentile(95) for m in all_metrics]
        rps = [m.requests_per_second for m in all_metrics]
        
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 12))
        
        # Taxa de sucesso
        ax1.plot(users, success_rates, marker='o', color='green')
        ax1.axhline(y=95, color='orange', linestyle='--', label='Limite aceitável (95%)')
        ax1.set_xlabel('Usuários Concorrentes')
        ax1.set_ylabel('Taxa de Sucesso (%)')
        ax1.set_title('Taxa de Sucesso vs. Carga')
        ax1.legend()
        ax1.grid(True)
        
        # Tempo de resposta P95
        ax2.plot(users, p95_times, marker='o', color='blue')
        ax2.axhline(y=1000, color='orange', linestyle='--', label='Limite aceitável (1s)')
        ax2.set_xlabel('Usuários Concorrentes')
        ax2.set_ylabel('P95 Tempo de Resposta (ms)')
        ax2.set_title('Tempo de Resposta (P95) vs. Carga')
        ax2.legend()
        ax2.grid(True)
        
        # Throughput
        ax3.plot(users, rps, marker='o', color='purple')
        ax3.set_xlabel('Usuários Concorrentes')
        ax3.set_ylabel('Requisições por Segundo')
        ax3.set_title('Throughput vs. Carga')
        ax3.grid(True)
        
        plt.tight_layout()
        plt.savefig(f"{self.report_dir}/{report_name}_scalability.png", 
                   dpi=300, bbox_inches='tight')
        plt.close()
        
        # Relatório texto
        report_path = f"{self.report_dir}/{report_name}.txt"
        with open(report_path, 'w') as f:
            f.write("RELATÓRIO DE TESTE DE STRESS\n")
            f.write("=" * 50 + "\n\n")
            
            f.write("Resultados por Carga:\n")
            f.write("-" * 50 + "\n")
            
            for m in all_metrics:
                f.write(f"\nUsuários: {m.concurrent_users}\n")
                f.write(f"  Taxa de sucesso: {m.success_rate:.1f}%\n")
                f.write(f"  RPS: {m.requests_per_second:.1f}\n")
                f.write(f"  P95: {m.percentile(95):.0f}ms\n")
                
                if m.success_rate < 95:
                    f.write("  ⚠️  Taxa de sucesso abaixo do limite!\n")
                if m.percentile(95) > 1000:
                    f.write("  ⚠️  Tempo de resposta acima do limite!\n")
            
            # Encontrar breaking point
            breaking_point = None
            for m in all_metrics:
                if m.success_rate < 80 or m.percentile(95) > 5000:
                    breaking_point = m.concurrent_users
                    break
            
            f.write(f"\n{'=' * 50}\n")
            if breaking_point:
                f.write(f"Breaking Point: {breaking_point} usuários\n")
            else:
                f.write(f"Breaking Point: >{max(users)} usuários\n")
            
            # Capacidade máxima recomendada (80% do breaking point)
            if breaking_point:
                recommended = int(breaking_point * 0.8)
            else:
                recommended = int(max(users) * 0.8)
            
            f.write(f"Capacidade Recomendada: {recommended} usuários\n")


# Cenários de teste pré-definidos
def create_api_test_scenario(base_url: str) -> LoadTestScenario:
    """Criar cenário de teste para API"""
    scenario = LoadTestScenario("API Test", base_url)
    
    # Endpoints com diferentes pesos
    scenario.add_endpoint("GET", "/api/processos", weight=5)
    scenario.add_endpoint("GET", "/api/processos/123456", weight=3)
    scenario.add_endpoint("POST", "/api/processos/search", weight=2, 
                         payload={"query": "test"})
    scenario.add_endpoint("GET", "/health", weight=1)
    
    return scenario


def create_mixed_scenario(base_url: str) -> LoadTestScenario:
    """Criar cenário misto de teste"""
    scenario = LoadTestScenario("Mixed Workload", base_url)
    
    # Leitura pesada
    scenario.add_endpoint("GET", "/api/processos", weight=4)
    scenario.add_endpoint("GET", "/api/documentos", weight=3)
    
    # Busca
    scenario.add_endpoint("POST", "/api/search", weight=2,
                         payload={"q": "juridico", "limit": 10})
    
    # Escrita
    scenario.add_endpoint("POST", "/api/processos", weight=1,
                         payload={"titulo": "Teste", "descricao": "Teste de carga"})
    
    # Download
    scenario.add_endpoint("GET", "/api/documentos/download/123", weight=0.5)
    
    return scenario


# CLI para execução
async def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Testes de Carga e Stress")
    parser.add_argument("--url", default="http://localhost:8000", 
                       help="URL base da API")
    parser.add_argument("--test-type", choices=["load", "stress"], 
                       default="load", help="Tipo de teste")
    parser.add_argument("--duration", type=int, default=60, 
                       help="Duração do teste em segundos")
    parser.add_argument("--users", type=int, default=10, 
                       help="Número de usuários concorrentes")
    parser.add_argument("--scenario", choices=["api", "mixed"], 
                       default="api", help="Cenário de teste")
    parser.add_argument("--auth-token", help="Token de autenticação")
    
    args = parser.parse_args()
    
    # Criar cenário
    if args.scenario == "api":
        scenario = create_api_test_scenario(args.url)
    else:
        scenario = create_mixed_scenario(args.url)
    
    if args.auth_token:
        scenario.set_auth(args.auth_token)
    
    # Criar reporter
    reporter = LoadTestReporter()
    
    if args.test_type == "load":
        # Teste de carga
        tester = LoadTester()
        logger.info("Executando teste de carga...")
        
        metrics = await tester.run_scenario(
            scenario,
            duration_seconds=args.duration,
            concurrent_users=args.users,
            ramp_up_seconds=10
        )
        
        # Gerar relatório
        reporter.generate_report(f"load_test_{args.scenario}", 
                               metrics, tester.results)
        
        # Resumo no console
        print(f"\n{'=' * 50}")
        print("RESUMO DO TESTE")
        print(f"{'=' * 50}")
        print(f"Total de requisições: {metrics.total_requests:,}")
        print(f"Taxa de sucesso: {metrics.success_rate:.1f}%")
        print(f"RPS: {metrics.requests_per_second:.1f}")
        print(f"Tempo médio: {metrics.avg_response_time:.0f}ms")
        print(f"P95: {metrics.percentile(95):.0f}ms")
        
    else:
        # Teste de stress
        tester = StressTester()
        logger.info("Executando teste de stress...")
        
        all_metrics = await tester.run_stress_test(
            scenario,
            initial_users=10,
            max_users=args.users,
            step_users=10,
            step_duration=30
        )
        
        # Gerar relatório
        reporter.generate_stress_report(f"stress_test_{args.scenario}", 
                                      all_metrics)
        
        # Resumo no console
        print(f"\n{'=' * 50}")
        print("RESUMO DO TESTE DE STRESS")
        print(f"{'=' * 50}")
        
        breaking_point = None
        for m in all_metrics:
            if m.success_rate < 80:
                breaking_point = m.concurrent_users
                break
        
        if breaking_point:
            print(f"Breaking point: {breaking_point} usuários")
            print(f"Capacidade recomendada: {int(breaking_point * 0.8)} usuários")
        else:
            print(f"Sistema suportou até {all_metrics[-1].concurrent_users} usuários")


if __name__ == "__main__":
    asyncio.run(main())