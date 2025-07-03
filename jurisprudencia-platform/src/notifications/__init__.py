"""
Sistema de Notificações e Alertas
"""

from .notification_service import (
    NotificationService,
    NotificationEvent,
    NotificationType,
    NotificationChannel,
    NotificationPriority,
    EmailProvider,
    SlackProvider,
    TelegramProvider,
    SMSProvider,
    DiscordProvider,
    notification_worker
)

from .alert_rules import (
    AlertEngine,
    AlertRule,
    AlertCondition,
    AlertCategory,
    alert_processor
)

__all__ = [
    # Notification Service
    'NotificationService',
    'NotificationEvent',
    'NotificationType',
    'NotificationChannel',
    'NotificationPriority',
    'EmailProvider',
    'SlackProvider',
    'TelegramProvider',
    'SMSProvider',
    'DiscordProvider',
    'notification_worker',
    
    # Alert Rules
    'AlertEngine',
    'AlertRule',
    'AlertCondition',
    'AlertCategory',
    'alert_processor'
]