#!/usr/bin/env python3
"""
🧪 TESTE DO SISTEMA DE NOTIFICAÇÕES
Testa o sistema completo de notificações e alertas
"""

import asyncio
import os
from datetime import datetime, timedelta
from pathlib import Path

# Adicionar src ao path
import sys
sys.path.append(str(Path(__file__).parent))

from src.notifications import (
    NotificationService, NotificationEvent, NotificationType,
    NotificationPriority, NotificationChannel,
    AlertEngine, AlertRule, AlertCategory, AlertCondition
)


async def test_notifications():
    """Testar sistema de notificações"""
    print("=" * 60)
    print("🧪 TESTE DO SISTEMA DE NOTIFICAÇÕES")
    print("=" * 60)
    
    # Criar serviço
    service = NotificationService()
    
    # Teste 1: Notificação simples
    print("\n📧 Teste 1: Notificação Simples")
    print("-" * 40)
    
    event = service.create_event(
        type=NotificationType.INFO,
        title="Teste de Sistema",
        message="Esta é uma notificação de teste do sistema de alertas",
        priority=NotificationPriority.MEDIUM,
        channels=[NotificationChannel.DATABASE],  # Apenas banco para teste
        metadata={
            'teste_id': '001',
            'sistema': 'Notificações',
            'ambiente': 'Teste'
        }
    )
    
    results = await service.send_notification(event)
    print(f"✅ Resultados: {results}")
    
    # Teste 2: Notificação agendada
    print("\n⏰ Teste 2: Notificação Agendada")
    print("-" * 40)
    
    scheduled_event = service.create_event(
        type=NotificationType.WARNING,
        title="Notificação Agendada",
        message="Esta notificação foi agendada para 5 segundos no futuro",
        priority=NotificationPriority.HIGH,
        channels=[NotificationChannel.DATABASE]
    )
    
    event_id = service.schedule_notification(
        scheduled_event,
        datetime.utcnow() + timedelta(seconds=5)
    )
    print(f"✅ Notificação agendada com ID: {event_id}")
    
    # Teste 3: Diferentes tipos de notificação
    print("\n🎯 Teste 3: Tipos de Notificação")
    print("-" * 40)
    
    tipos = [
        (NotificationType.SUCCESS, "Operação concluída com sucesso"),
        (NotificationType.WARNING, "Atenção: recurso próximo do limite"),
        (NotificationType.ERROR, "Erro ao processar solicitação"),
        (NotificationType.CRITICAL, "CRÍTICO: Sistema em falha")
    ]
    
    for tipo, mensagem in tipos:
        event = service.create_event(
            type=tipo,
            title=f"Teste {tipo.value.upper()}",
            message=mensagem,
            priority=NotificationPriority.MEDIUM,
            channels=[NotificationChannel.DATABASE]
        )
        
        results = await service.send_notification(event)
        print(f"  {tipo.value}: {results}")
    
    # Teste 4: Estatísticas
    print("\n📊 Teste 4: Estatísticas")
    print("-" * 40)
    
    stats = service.get_notification_stats(days=1)
    print(f"Total de notificações: {stats.get('total', 0)}")
    print(f"Enviadas com sucesso: {stats.get('sent', 0)}")
    print(f"Falhas: {stats.get('failed', 0)}")
    
    if stats.get('by_type'):
        print("\nPor tipo:")
        for tipo, counts in stats['by_type'].items():
            print(f"  {tipo}: {counts}")
    
    # Aguardar notificação agendada
    print("\n⏳ Aguardando notificação agendada...")
    await asyncio.sleep(6)
    await service.process_scheduled_notifications()
    print("✅ Notificações agendadas processadas")


async def test_alert_engine():
    """Testar motor de alertas"""
    print("\n" + "=" * 60)
    print("🚨 TESTE DO MOTOR DE ALERTAS")
    print("=" * 60)
    
    # Criar motor
    engine = AlertEngine()
    
    # Teste 1: Adicionar regra customizada
    print("\n📋 Teste 1: Regra Customizada")
    print("-" * 40)
    
    custom_rule = AlertRule(
        id="test_high_value",
        name="Processo de alto valor",
        description="Alerta para processos acima de R$ 500.000",
        category=AlertCategory.BUSINESS,
        conditions=[
            {
                "field": "tipo",
                "condition": AlertCondition.EQUALS.value,
                "value": "novo_processo"
            },
            {
                "field": "valor",
                "condition": AlertCondition.GREATER_THAN.value,
                "value": 500000
            }
        ],
        actions=[
            {
                "type": "notification",
                "channels": ["database"]
            }
        ],
        priority=NotificationPriority.HIGH,
        cooldown_minutes=5
    )
    
    success = engine.add_rule(custom_rule)
    print(f"✅ Regra adicionada: {success}")
    
    # Teste 2: Simular eventos
    print("\n🎯 Teste 2: Simulação de Eventos")
    print("-" * 40)
    
    # Evento que deve disparar alerta
    event1 = {
        "tipo": "novo_processo",
        "valor": 750000,
        "numero": "1234567-89.2024.8.26.0100",
        "partes": ["Empresa X", "Empresa Y"]
    }
    
    triggered = await engine.process_event(event1)
    print(f"Evento 1 - Alertas disparados: {triggered}")
    
    # Evento que NÃO deve disparar alerta
    event2 = {
        "tipo": "novo_processo",
        "valor": 100000,
        "numero": "9876543-21.2024.8.26.0100"
    }
    
    triggered = await engine.process_event(event2)
    print(f"Evento 2 - Alertas disparados: {triggered}")
    
    # Teste 3: Métricas e thresholds
    print("\n📈 Teste 3: Métricas e Thresholds")
    print("-" * 40)
    
    # Adicionar métricas
    for i in range(5):
        engine.add_metric("cpu_usage", 45 + i * 10)
        await asyncio.sleep(0.1)
    
    print("✅ Métricas adicionadas")
    
    # Teste 4: Múltiplas tentativas de login
    print("\n🔐 Teste 4: Segurança - Login Falho")
    print("-" * 40)
    
    # Simular múltiplas falhas
    for i in range(6):
        event = {
            "event_type": "login_failed",
            "ip_address": "192.168.1.100",
            "username": "admin",
            "attempt": i + 1
        }
        triggered = await engine.process_event(event)
        if triggered:
            print(f"  Tentativa {i+1}: ALERTA DISPARADO! {triggered}")
        else:
            print(f"  Tentativa {i+1}: Sem alerta")
        
        await asyncio.sleep(0.5)
    
    # Teste 5: Estatísticas de alertas
    print("\n📊 Teste 5: Estatísticas de Alertas")
    print("-" * 40)
    
    stats = engine.get_alert_stats(days=1)
    print(f"Total de alertas: {stats.get('total_alerts', 0)}")
    print(f"Taxa de sucesso: {stats.get('success_rate', 0):.2%}")
    
    if stats.get('by_rule'):
        print("\nPor regra:")
        for rule_id, count in stats['by_rule'].items():
            print(f"  {rule_id}: {count} alertas")


async def test_integration():
    """Teste de integração completo"""
    print("\n" + "=" * 60)
    print("🔗 TESTE DE INTEGRAÇÃO")
    print("=" * 60)
    
    # Criar serviços
    notification_service = NotificationService()
    alert_engine = AlertEngine()
    
    # Simular cenário real
    print("\n🏢 Cenário: Novo processo judicial de alto valor")
    print("-" * 40)
    
    # 1. Processo é cadastrado
    processo_data = {
        "event_type": "processo_criado",
        "numero_cnj": "1234567-89.2024.8.26.0100",
        "tribunal": "TJSP",
        "valor_causa": 2500000.00,  # R$ 2.5 milhões
        "classe": "Ação de Indenização",
        "partes": {
            "autor": "Empresa ABC Ltda",
            "reu": "Empresa XYZ S.A."
        },
        "timestamp": datetime.utcnow().isoformat()
    }
    
    print(f"📄 Processo criado:")
    print(f"   Número: {processo_data['numero_cnj']}")
    print(f"   Valor: R$ {processo_data['valor_causa']:,.2f}")
    
    # 2. Motor de alertas processa
    triggered = await alert_engine.process_event(processo_data)
    print(f"\n🚨 Alertas disparados: {triggered}")
    
    # 3. Verificar notificações
    await asyncio.sleep(1)
    stats = notification_service.get_notification_stats(days=1)
    print(f"\n📊 Notificações enviadas: {stats.get('total', 0)}")
    
    # 4. Simular análise de risco
    print("\n🔍 Análise de risco automática iniciada...")
    
    risk_event = notification_service.create_event(
        type=NotificationType.WARNING,
        title="Análise de Risco - Processo Alto Valor",
        message=f"Processo {processo_data['numero_cnj']} requer análise de risco",
        priority=NotificationPriority.HIGH,
        channels=[NotificationChannel.DATABASE],
        metadata={
            'processo': processo_data['numero_cnj'],
            'valor': processo_data['valor_causa'],
            'risco_estimado': 'ALTO',
            'ações_recomendadas': [
                'Revisar documentação',
                'Consultar jurídico sênior',
                'Preparar provisão contábil'
            ]
        }
    )
    
    await notification_service.send_notification(risk_event)
    print("✅ Notificação de risco enviada")


async def main():
    """Executar todos os testes"""
    try:
        # Configurar ambiente de teste
        os.environ.setdefault('DATABASE_URL', 'sqlite:///test_notifications.db')
        
        # Executar testes
        await test_notifications()
        await test_alert_engine()
        await test_integration()
        
        print("\n" + "=" * 60)
        print("✅ TODOS OS TESTES CONCLUÍDOS COM SUCESSO!")
        print("=" * 60)
        
        # Limpar banco de teste
        test_db = Path('test_notifications.db')
        if test_db.exists():
            test_db.unlink()
            print("\n🧹 Banco de testes removido")
        
    except Exception as e:
        print(f"\n❌ ERRO NOS TESTES: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())