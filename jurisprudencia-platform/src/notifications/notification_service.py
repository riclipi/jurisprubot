#!/usr/bin/env python3
"""
📢 SERVIÇO DE NOTIFICAÇÕES E ALERTAS
Sistema completo para envio de notificações por múltiplos canais
"""

import os
import json
import asyncio
from typing import Dict, List, Optional, Union, Any
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import ssl
from dataclasses import dataclass, asdict
from enum import Enum
import requests
import logging
from pathlib import Path
import jinja2
from sqlalchemy import create_engine, Column, Integer, String, DateTime, JSON, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import aiosmtplib
from twilio.rest import Client as TwilioClient
import telegram
from discord_webhook import DiscordWebhook, DiscordEmbed

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Base SQLAlchemy
Base = declarative_base()


class NotificationType(Enum):
    """Tipos de notificação"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    SUCCESS = "success"


class NotificationChannel(Enum):
    """Canais de notificação"""
    EMAIL = "email"
    SMS = "sms"
    SLACK = "slack"
    TELEGRAM = "telegram"
    DISCORD = "discord"
    WEBHOOK = "webhook"
    DATABASE = "database"


class NotificationPriority(Enum):
    """Prioridade da notificação"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4


@dataclass
class NotificationEvent:
    """Evento de notificação"""
    type: NotificationType
    title: str
    message: str
    priority: NotificationPriority = NotificationPriority.MEDIUM
    channels: List[NotificationChannel] = None
    metadata: Dict[str, Any] = None
    recipient: Optional[str] = None
    template: Optional[str] = None
    retry_count: int = 0
    scheduled_at: Optional[datetime] = None


class NotificationLog(Base):
    """Log de notificações enviadas"""
    __tablename__ = 'notification_logs'
    
    id = Column(Integer, primary_key=True)
    event_id = Column(String(50), index=True)
    type = Column(String(20))
    channel = Column(String(20))
    recipient = Column(String(200))
    title = Column(String(500))
    message = Column(Text)
    metadata = Column(JSON)
    status = Column(String(20))  # sent, failed, pending
    error_message = Column(Text, nullable=True)
    sent_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    retry_count = Column(Integer, default=0)


class NotificationQueue(Base):
    """Fila de notificações pendentes"""
    __tablename__ = 'notification_queue'
    
    id = Column(Integer, primary_key=True)
    event_id = Column(String(50), unique=True, index=True)
    event_data = Column(JSON)
    priority = Column(Integer)
    scheduled_at = Column(DateTime)
    processed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class EmailProvider:
    """Provedor de email"""
    
    def __init__(self):
        self.smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_user = os.getenv('SMTP_USER', '')
        self.smtp_password = os.getenv('SMTP_PASSWORD', '')
        self.from_email = os.getenv('FROM_EMAIL', self.smtp_user)
        self.from_name = os.getenv('FROM_NAME', 'Sistema Jurídico')
        
        # Templates
        self.template_dir = Path(__file__).parent / 'templates'
        self.template_dir.mkdir(exist_ok=True)
        self.jinja_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(self.template_dir))
        )
    
    async def send_async(self, to: str, subject: str, body: str, 
                        html_body: Optional[str] = None) -> bool:
        """Enviar email assíncrono"""
        try:
            message = MIMEMultipart('alternative')
            message['Subject'] = subject
            message['From'] = f"{self.from_name} <{self.from_email}>"
            message['To'] = to
            
            # Adicionar corpo
            message.attach(MIMEText(body, 'plain'))
            if html_body:
                message.attach(MIMEText(html_body, 'html'))
            
            # Enviar
            await aiosmtplib.send(
                message,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.smtp_user,
                password=self.smtp_password,
                start_tls=True
            )
            
            logger.info(f"Email enviado para {to}: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao enviar email: {e}")
            return False
    
    def send_sync(self, to: str, subject: str, body: str, 
                  html_body: Optional[str] = None) -> bool:
        """Enviar email síncrono"""
        try:
            message = MIMEMultipart('alternative')
            message['Subject'] = subject
            message['From'] = f"{self.from_name} <{self.from_email}>"
            message['To'] = to
            
            # Adicionar corpo
            message.attach(MIMEText(body, 'plain'))
            if html_body:
                message.attach(MIMEText(html_body, 'html'))
            
            # Conectar e enviar
            context = ssl.create_default_context()
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(message)
            
            logger.info(f"Email enviado para {to}: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao enviar email: {e}")
            return False


class SlackProvider:
    """Provedor Slack"""
    
    def __init__(self):
        self.webhook_url = os.getenv('SLACK_WEBHOOK_URL', '')
        self.default_channel = os.getenv('SLACK_CHANNEL', '#alertas')
    
    def send(self, message: str, channel: Optional[str] = None,
             attachments: Optional[List[Dict]] = None) -> bool:
        """Enviar mensagem para Slack"""
        try:
            if not self.webhook_url:
                logger.warning("Slack webhook não configurado")
                return False
            
            payload = {
                'text': message,
                'channel': channel or self.default_channel
            }
            
            if attachments:
                payload['attachments'] = attachments
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10
            )
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Erro ao enviar para Slack: {e}")
            return False


class TelegramProvider:
    """Provedor Telegram"""
    
    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN', '')
        self.default_chat_id = os.getenv('TELEGRAM_CHAT_ID', '')
        
        if self.bot_token:
            self.bot = telegram.Bot(token=self.bot_token)
        else:
            self.bot = None
    
    async def send_async(self, message: str, chat_id: Optional[str] = None,
                        parse_mode: str = 'HTML') -> bool:
        """Enviar mensagem para Telegram"""
        try:
            if not self.bot:
                logger.warning("Bot Telegram não configurado")
                return False
            
            await self.bot.send_message(
                chat_id=chat_id or self.default_chat_id,
                text=message,
                parse_mode=parse_mode
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao enviar para Telegram: {e}")
            return False


class SMSProvider:
    """Provedor SMS via Twilio"""
    
    def __init__(self):
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID', '')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN', '')
        self.from_number = os.getenv('TWILIO_FROM_NUMBER', '')
        
        if self.account_sid and self.auth_token:
            self.client = TwilioClient(self.account_sid, self.auth_token)
        else:
            self.client = None
    
    def send(self, to: str, message: str) -> bool:
        """Enviar SMS"""
        try:
            if not self.client:
                logger.warning("Twilio não configurado")
                return False
            
            # Limitar tamanho da mensagem
            if len(message) > 160:
                message = message[:157] + "..."
            
            result = self.client.messages.create(
                body=message,
                from_=self.from_number,
                to=to
            )
            
            return result.status in ['queued', 'sent']
            
        except Exception as e:
            logger.error(f"Erro ao enviar SMS: {e}")
            return False


class DiscordProvider:
    """Provedor Discord"""
    
    def __init__(self):
        self.webhook_url = os.getenv('DISCORD_WEBHOOK_URL', '')
    
    def send(self, title: str, description: str, 
             color: Optional[str] = None, fields: Optional[List[Dict]] = None) -> bool:
        """Enviar mensagem para Discord"""
        try:
            if not self.webhook_url:
                logger.warning("Discord webhook não configurado")
                return False
            
            webhook = DiscordWebhook(url=self.webhook_url)
            
            # Criar embed
            embed = DiscordEmbed(
                title=title,
                description=description,
                color=color or 'FF0000'
            )
            
            if fields:
                for field in fields:
                    embed.add_embed_field(
                        name=field.get('name', ''),
                        value=field.get('value', ''),
                        inline=field.get('inline', False)
                    )
            
            webhook.add_embed(embed)
            response = webhook.execute()
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Erro ao enviar para Discord: {e}")
            return False


class NotificationService:
    """Serviço principal de notificações"""
    
    def __init__(self, db_url: Optional[str] = None):
        # Configurar banco
        if not db_url:
            db_url = os.getenv('DATABASE_URL', 'sqlite:///notifications.db')
        
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        # Inicializar provedores
        self.providers = {
            NotificationChannel.EMAIL: EmailProvider(),
            NotificationChannel.SLACK: SlackProvider(),
            NotificationChannel.TELEGRAM: TelegramProvider(),
            NotificationChannel.SMS: SMSProvider(),
            NotificationChannel.DISCORD: DiscordProvider()
        }
        
        # Templates padrão
        self._create_default_templates()
        
        # Configurações
        self.retry_delays = [60, 300, 900]  # 1min, 5min, 15min
        self.max_retries = 3
    
    def _create_default_templates(self):
        """Criar templates padrão"""
        template_dir = Path(__file__).parent / 'templates'
        template_dir.mkdir(exist_ok=True)
        
        # Template email base
        base_template = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background-color: #007bff; color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; background-color: #f8f9fa; }
        .footer { text-align: center; padding: 10px; color: #6c757d; }
        .alert-{{ type }} { 
            padding: 15px; 
            margin: 10px 0; 
            border-radius: 5px;
        }
        .alert-info { background-color: #d1ecf1; color: #0c5460; }
        .alert-warning { background-color: #fff3cd; color: #856404; }
        .alert-error { background-color: #f8d7da; color: #721c24; }
        .alert-success { background-color: #d4edda; color: #155724; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{{ title }}</h1>
        </div>
        <div class="content">
            <div class="alert-{{ type }}">
                {{ message }}
            </div>
            {% if metadata %}
            <h3>Detalhes:</h3>
            <ul>
            {% for key, value in metadata.items() %}
                <li><strong>{{ key }}:</strong> {{ value }}</li>
            {% endfor %}
            </ul>
            {% endif %}
        </div>
        <div class="footer">
            <p>Sistema Jurídico - {{ timestamp }}</p>
        </div>
    </div>
</body>
</html>
        """
        
        (template_dir / 'email_base.html').write_text(base_template)
    
    def create_event(self, **kwargs) -> NotificationEvent:
        """Criar evento de notificação"""
        return NotificationEvent(**kwargs)
    
    async def send_notification(self, event: NotificationEvent) -> Dict[str, bool]:
        """Enviar notificação por todos os canais configurados"""
        results = {}
        
        # Determinar canais
        channels = event.channels or self._get_default_channels(event.type, event.priority)
        
        # Gerar ID único
        event_id = f"{datetime.utcnow().timestamp()}_{event.type.value}"
        
        # Processar cada canal
        for channel in channels:
            try:
                success = await self._send_to_channel(event, channel)
                results[channel.value] = success
                
                # Registrar no log
                self._log_notification(
                    event_id=event_id,
                    event=event,
                    channel=channel,
                    success=success
                )
                
            except Exception as e:
                logger.error(f"Erro ao enviar para {channel.value}: {e}")
                results[channel.value] = False
        
        return results
    
    async def _send_to_channel(self, event: NotificationEvent, 
                              channel: NotificationChannel) -> bool:
        """Enviar para canal específico"""
        try:
            if channel == NotificationChannel.EMAIL:
                provider = self.providers[channel]
                
                # Renderizar template se especificado
                if event.template:
                    html_body = self._render_template(event)
                else:
                    html_body = None
                
                return await provider.send_async(
                    to=event.recipient or os.getenv('DEFAULT_EMAIL_RECIPIENT', ''),
                    subject=event.title,
                    body=event.message,
                    html_body=html_body
                )
            
            elif channel == NotificationChannel.SLACK:
                provider = self.providers[channel]
                
                # Formatar mensagem
                attachments = [{
                    'color': self._get_color_for_type(event.type),
                    'title': event.title,
                    'text': event.message,
                    'fields': [
                        {'title': k, 'value': str(v), 'short': True}
                        for k, v in (event.metadata or {}).items()
                    ],
                    'footer': 'Sistema Jurídico',
                    'ts': datetime.utcnow().timestamp()
                }]
                
                return provider.send(
                    message=f"*{event.type.value.upper()}*: {event.title}",
                    attachments=attachments
                )
            
            elif channel == NotificationChannel.TELEGRAM:
                provider = self.providers[channel]
                
                # Formatar mensagem HTML
                message = f"""
<b>{event.type.value.upper()}: {event.title}</b>

{event.message}

{self._format_metadata_telegram(event.metadata)}
                """
                
                return await provider.send_async(message)
            
            elif channel == NotificationChannel.SMS:
                provider = self.providers[channel]
                
                # Mensagem curta para SMS
                message = f"{event.type.value.upper()}: {event.title} - {event.message}"
                
                return provider.send(
                    to=event.recipient or os.getenv('DEFAULT_SMS_RECIPIENT', ''),
                    message=message
                )
            
            elif channel == NotificationChannel.DISCORD:
                provider = self.providers[channel]
                
                fields = []
                if event.metadata:
                    fields = [
                        {'name': k, 'value': str(v), 'inline': True}
                        for k, v in event.metadata.items()
                    ]
                
                return provider.send(
                    title=f"{event.type.value.upper()}: {event.title}",
                    description=event.message,
                    color=self._get_color_for_type(event.type),
                    fields=fields
                )
            
            elif channel == NotificationChannel.DATABASE:
                # Apenas registrar no banco
                return True
            
            elif channel == NotificationChannel.WEBHOOK:
                # Enviar para webhook genérico
                webhook_url = os.getenv('GENERIC_WEBHOOK_URL', '')
                if webhook_url:
                    response = requests.post(
                        webhook_url,
                        json=asdict(event),
                        timeout=10
                    )
                    return response.status_code < 400
                return False
            
            else:
                logger.warning(f"Canal não suportado: {channel}")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao enviar para {channel.value}: {e}")
            return False
    
    def _get_default_channels(self, type: NotificationType, 
                            priority: NotificationPriority) -> List[NotificationChannel]:
        """Determinar canais padrão baseado no tipo e prioridade"""
        channels = [NotificationChannel.DATABASE]
        
        if priority == NotificationPriority.URGENT:
            channels.extend([
                NotificationChannel.EMAIL,
                NotificationChannel.SMS,
                NotificationChannel.SLACK,
                NotificationChannel.TELEGRAM
            ])
        elif priority == NotificationPriority.HIGH:
            channels.extend([
                NotificationChannel.EMAIL,
                NotificationChannel.SLACK
            ])
        elif type in [NotificationType.ERROR, NotificationType.CRITICAL]:
            channels.extend([
                NotificationChannel.EMAIL,
                NotificationChannel.SLACK
            ])
        else:
            channels.append(NotificationChannel.SLACK)
        
        # Filtrar apenas canais configurados
        configured_channels = []
        for channel in channels:
            if channel == NotificationChannel.DATABASE:
                configured_channels.append(channel)
            elif channel == NotificationChannel.EMAIL and os.getenv('SMTP_HOST'):
                configured_channels.append(channel)
            elif channel == NotificationChannel.SLACK and os.getenv('SLACK_WEBHOOK_URL'):
                configured_channels.append(channel)
            elif channel == NotificationChannel.TELEGRAM and os.getenv('TELEGRAM_BOT_TOKEN'):
                configured_channels.append(channel)
            elif channel == NotificationChannel.SMS and os.getenv('TWILIO_ACCOUNT_SID'):
                configured_channels.append(channel)
            elif channel == NotificationChannel.DISCORD and os.getenv('DISCORD_WEBHOOK_URL'):
                configured_channels.append(channel)
        
        return configured_channels
    
    def _get_color_for_type(self, type: NotificationType) -> str:
        """Obter cor para tipo de notificação"""
        colors = {
            NotificationType.INFO: '#0066CC',
            NotificationType.WARNING: '#FFCC00',
            NotificationType.ERROR: '#CC0000',
            NotificationType.CRITICAL: '#990000',
            NotificationType.SUCCESS: '#006600'
        }
        return colors.get(type, '#666666')
    
    def _format_metadata_telegram(self, metadata: Optional[Dict]) -> str:
        """Formatar metadata para Telegram"""
        if not metadata:
            return ""
        
        lines = []
        for key, value in metadata.items():
            lines.append(f"<i>{key}:</i> {value}")
        
        return "\n".join(lines)
    
    def _render_template(self, event: NotificationEvent) -> str:
        """Renderizar template"""
        try:
            template_path = Path(__file__).parent / 'templates' / f"{event.template}.html"
            
            if not template_path.exists():
                template_path = Path(__file__).parent / 'templates' / 'email_base.html'
            
            template = jinja2.Template(template_path.read_text())
            
            return template.render(
                title=event.title,
                message=event.message,
                type=event.type.value,
                metadata=event.metadata,
                timestamp=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
            )
            
        except Exception as e:
            logger.error(f"Erro ao renderizar template: {e}")
            return event.message
    
    def _log_notification(self, event_id: str, event: NotificationEvent,
                         channel: NotificationChannel, success: bool):
        """Registrar notificação no banco"""
        try:
            with self.SessionLocal() as session:
                log = NotificationLog(
                    event_id=event_id,
                    type=event.type.value,
                    channel=channel.value,
                    recipient=event.recipient or 'default',
                    title=event.title,
                    message=event.message,
                    metadata=event.metadata,
                    status='sent' if success else 'failed',
                    sent_at=datetime.utcnow() if success else None,
                    retry_count=event.retry_count
                )
                session.add(log)
                session.commit()
                
        except Exception as e:
            logger.error(f"Erro ao registrar log: {e}")
    
    def schedule_notification(self, event: NotificationEvent, 
                            send_at: datetime) -> str:
        """Agendar notificação"""
        try:
            event_id = f"scheduled_{datetime.utcnow().timestamp()}"
            
            with self.SessionLocal() as session:
                queue_item = NotificationQueue(
                    event_id=event_id,
                    event_data=asdict(event),
                    priority=event.priority.value,
                    scheduled_at=send_at
                )
                session.add(queue_item)
                session.commit()
            
            logger.info(f"Notificação agendada: {event_id} para {send_at}")
            return event_id
            
        except Exception as e:
            logger.error(f"Erro ao agendar notificação: {e}")
            return ""
    
    async def process_scheduled_notifications(self):
        """Processar notificações agendadas"""
        try:
            with self.SessionLocal() as session:
                # Buscar notificações pendentes
                pending = session.query(NotificationQueue).filter(
                    NotificationQueue.processed == False,
                    NotificationQueue.scheduled_at <= datetime.utcnow()
                ).order_by(
                    NotificationQueue.priority.desc(),
                    NotificationQueue.scheduled_at
                ).all()
                
                for item in pending:
                    try:
                        # Reconstruir evento
                        event_data = item.event_data
                        event = NotificationEvent(
                            type=NotificationType(event_data['type']),
                            title=event_data['title'],
                            message=event_data['message'],
                            priority=NotificationPriority(event_data.get('priority', 2)),
                            channels=[NotificationChannel(c) for c in event_data.get('channels', [])],
                            metadata=event_data.get('metadata'),
                            recipient=event_data.get('recipient'),
                            template=event_data.get('template')
                        )
                        
                        # Enviar
                        await self.send_notification(event)
                        
                        # Marcar como processado
                        item.processed = True
                        session.commit()
                        
                    except Exception as e:
                        logger.error(f"Erro ao processar notificação {item.event_id}: {e}")
                        
        except Exception as e:
            logger.error(f"Erro ao processar fila: {e}")
    
    async def retry_failed_notifications(self):
        """Retentar notificações falhas"""
        try:
            with self.SessionLocal() as session:
                # Buscar notificações falhas
                failed = session.query(NotificationLog).filter(
                    NotificationLog.status == 'failed',
                    NotificationLog.retry_count < self.max_retries
                ).all()
                
                for log in failed:
                    # Calcular delay
                    delay_index = min(log.retry_count, len(self.retry_delays) - 1)
                    delay = self.retry_delays[delay_index]
                    
                    # Verificar se é hora de retentar
                    retry_after = log.created_at + timedelta(seconds=delay)
                    if datetime.utcnow() >= retry_after:
                        # Reconstruir evento
                        event = NotificationEvent(
                            type=NotificationType(log.type),
                            title=log.title,
                            message=log.message,
                            metadata=log.metadata,
                            recipient=log.recipient,
                            retry_count=log.retry_count + 1
                        )
                        
                        # Reenviar apenas para o canal que falhou
                        channel = NotificationChannel(log.channel)
                        success = await self._send_to_channel(event, channel)
                        
                        if success:
                            log.status = 'sent'
                            log.sent_at = datetime.utcnow()
                        else:
                            log.retry_count += 1
                        
                        session.commit()
                        
        except Exception as e:
            logger.error(f"Erro ao retentar notificações: {e}")
    
    def get_notification_stats(self, days: int = 7) -> Dict:
        """Obter estatísticas de notificações"""
        try:
            since = datetime.utcnow() - timedelta(days=days)
            
            with self.SessionLocal() as session:
                logs = session.query(NotificationLog).filter(
                    NotificationLog.created_at >= since
                ).all()
                
                stats = {
                    'total': len(logs),
                    'sent': len([l for l in logs if l.status == 'sent']),
                    'failed': len([l for l in logs if l.status == 'failed']),
                    'by_type': {},
                    'by_channel': {}
                }
                
                # Agrupar por tipo
                for log in logs:
                    if log.type not in stats['by_type']:
                        stats['by_type'][log.type] = {'sent': 0, 'failed': 0}
                    
                    if log.status == 'sent':
                        stats['by_type'][log.type]['sent'] += 1
                    else:
                        stats['by_type'][log.type]['failed'] += 1
                    
                    # Agrupar por canal
                    if log.channel not in stats['by_channel']:
                        stats['by_channel'][log.channel] = {'sent': 0, 'failed': 0}
                    
                    if log.status == 'sent':
                        stats['by_channel'][log.channel]['sent'] += 1
                    else:
                        stats['by_channel'][log.channel]['failed'] += 1
                
                return stats
                
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas: {e}")
            return {}


# Worker assíncrono
async def notification_worker():
    """Worker para processar notificações"""
    service = NotificationService()
    
    while True:
        try:
            # Processar agendadas
            await service.process_scheduled_notifications()
            
            # Retentar falhas
            await service.retry_failed_notifications()
            
            # Aguardar
            await asyncio.sleep(60)  # Verificar a cada minuto
            
        except Exception as e:
            logger.error(f"Erro no worker: {e}")
            await asyncio.sleep(60)


if __name__ == "__main__":
    # Exemplo de uso
    async def test_notifications():
        service = NotificationService()
        
        # Criar evento
        event = service.create_event(
            type=NotificationType.INFO,
            title="Teste de Notificação",
            message="Esta é uma notificação de teste do sistema",
            priority=NotificationPriority.MEDIUM,
            metadata={
                'sistema': 'Jurídico',
                'módulo': 'Notificações',
                'timestamp': datetime.utcnow().isoformat()
            }
        )
        
        # Enviar
        results = await service.send_notification(event)
        print(f"Resultados: {results}")
        
        # Agendar notificação
        scheduled_event = service.create_event(
            type=NotificationType.WARNING,
            title="Notificação Agendada",
            message="Esta notificação foi agendada para o futuro",
            priority=NotificationPriority.HIGH
        )
        
        event_id = service.schedule_notification(
            scheduled_event,
            datetime.utcnow() + timedelta(minutes=5)
        )
        print(f"Notificação agendada: {event_id}")
        
        # Estatísticas
        stats = service.get_notification_stats()
        print(f"Estatísticas: {stats}")
    
    # Executar teste
    asyncio.run(test_notifications())