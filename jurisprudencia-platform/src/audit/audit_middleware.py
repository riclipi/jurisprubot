#!/usr/bin/env python3
"""
🔍 MIDDLEWARE DE AUDITORIA
Intercepta e registra todas as requisições da API
"""

import time
import json
import uuid
from typing import Callable, Optional, Dict, Any
from datetime import datetime
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import logging

from .audit_service import AuditService, AuditEventType, AuditSeverity, audit_context

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AuditMiddleware(BaseHTTPMiddleware):
    """Middleware para auditoria de requisições HTTP"""
    
    def __init__(self, app: ASGIApp, audit_service: AuditService,
                 exclude_paths: Optional[List[str]] = None):
        super().__init__(app)
        self.audit_service = audit_service
        self.exclude_paths = exclude_paths or ['/health', '/metrics', '/docs', '/openapi.json']
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Processar requisição e registrar auditoria"""
        # Verificar se deve auditar
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)
        
        # Gerar ID da requisição
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Tempo inicial
        start_time = time.time()
        
        # Extrair informações do usuário
        user_info = await self._extract_user_info(request)
        
        # Capturar corpo da requisição
        request_body = None
        if request.method in ['POST', 'PUT', 'PATCH']:
            try:
                body_bytes = await request.body()
                request_body = body_bytes.decode('utf-8')
                # Recriar o stream do body
                async def receive():
                    return {"type": "http.request", "body": body_bytes}
                request._receive = receive
            except Exception as e:
                logger.warning(f"Erro ao capturar body da requisição: {e}")
        
        # Determinar tipo de evento
        event_type = self._determine_event_type(request)
        
        # Variáveis para resposta
        response = None
        response_body = None
        error_message = None
        stack_trace = None
        
        try:
            # Processar requisição
            response = await call_next(request)
            
            # Capturar corpo da resposta
            if response.status_code < 400:
                try:
                    # Para respostas de streaming
                    body_bytes = b''
                    async for chunk in response.body_iterator:
                        body_bytes += chunk
                    
                    response_body = body_bytes.decode('utf-8')
                    
                    # Recriar resposta
                    response = Response(
                        content=body_bytes,
                        status_code=response.status_code,
                        headers=dict(response.headers),
                        media_type=response.media_type
                    )
                except Exception as e:
                    logger.warning(f"Erro ao capturar body da resposta: {e}")
            
            return response
            
        except Exception as e:
            # Capturar erro
            error_message = str(e)
            import traceback
            stack_trace = traceback.format_exc()
            
            # Criar resposta de erro
            response = JSONResponse(
                status_code=500,
                content={
                    "error": "Internal Server Error",
                    "request_id": request_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            raise
            
        finally:
            # Calcular duração
            duration_ms = (time.time() - start_time) * 1000
            
            # Determinar severidade
            if response:
                if response.status_code >= 500:
                    severity = AuditSeverity.ERROR
                elif response.status_code >= 400:
                    severity = AuditSeverity.WARNING
                else:
                    severity = AuditSeverity.INFO
            else:
                severity = AuditSeverity.ERROR
            
            # Criar evento de auditoria
            event = self.audit_service.create_event(
                event_type=event_type,
                severity=severity,
                user_id=user_info.get('user_id'),
                user_name=user_info.get('user_name'),
                ip_address=user_info.get('ip_address'),
                user_agent=user_info.get('user_agent'),
                session_id=user_info.get('session_id'),
                resource_type='api_endpoint',
                resource_id=request.url.path,
                action=request.method,
                result='success' if response and response.status_code < 400 else 'error',
                error_message=error_message,
                duration_ms=duration_ms,
                stack_trace=stack_trace,
                metadata={
                    'request_id': request_id,
                    'method': request.method,
                    'path': request.url.path,
                    'query_params': dict(request.query_params),
                    'status_code': response.status_code if response else None,
                    'content_type': request.headers.get('content-type'),
                    'response_size': len(response_body) if response_body else 0
                },
                request_data=self._sanitize_request_data(request_body),
                response_data=self._sanitize_response_data(response_body)
            )
            
            # Registrar evento
            await self.audit_service.log_event(event)
    
    async def _extract_user_info(self, request: Request) -> Dict[str, Any]:
        """Extrair informações do usuário da requisição"""
        user_info = {}
        
        # IP do cliente
        if request.client:
            user_info['ip_address'] = request.client.host
        
        # Verificar headers de proxy
        forwarded_for = request.headers.get('x-forwarded-for')
        if forwarded_for:
            user_info['ip_address'] = forwarded_for.split(',')[0].strip()
        
        # User agent
        user_info['user_agent'] = request.headers.get('user-agent', '')
        
        # Informações de autenticação (se disponível)
        if hasattr(request.state, 'user'):
            user = request.state.user
            user_info['user_id'] = getattr(user, 'id', None)
            user_info['user_name'] = getattr(user, 'name', None) or getattr(user, 'username', None)
        
        # Session ID (se disponível)
        session_id = request.headers.get('x-session-id') or request.cookies.get('session_id')
        if session_id:
            user_info['session_id'] = session_id
        
        return user_info
    
    def _determine_event_type(self, request: Request) -> AuditEventType:
        """Determinar tipo de evento baseado na requisição"""
        path = request.url.path.lower()
        method = request.method.upper()
        
        # Autenticação
        if '/login' in path:
            return AuditEventType.LOGIN
        elif '/logout' in path:
            return AuditEventType.LOGOUT
        elif '/password' in path:
            return AuditEventType.PASSWORD_CHANGE
        
        # CRUD operations
        elif method == 'POST':
            return AuditEventType.CREATE
        elif method in ['PUT', 'PATCH']:
            return AuditEventType.UPDATE
        elif method == 'DELETE':
            return AuditEventType.DELETE
        
        # Data access
        elif '/export' in path or '/download' in path:
            return AuditEventType.DATA_EXPORT
        elif method == 'GET':
            return AuditEventType.DATA_ACCESS
        
        # Default
        return AuditEventType.API_CALL
    
    def _sanitize_request_data(self, data: Optional[str]) -> Optional[Dict]:
        """Sanitizar dados da requisição (remover senhas, etc)"""
        if not data:
            return None
        
        try:
            # Parse JSON
            if isinstance(data, str):
                parsed = json.loads(data)
            else:
                parsed = data
            
            # Remover campos sensíveis
            sensitive_fields = [
                'password', 'senha', 'token', 'api_key', 'secret',
                'credit_card', 'cvv', 'cpf', 'cnpj', 'rg'
            ]
            
            return self._remove_sensitive_fields(parsed, sensitive_fields)
            
        except json.JSONDecodeError:
            # Se não for JSON, retornar resumo
            return {'raw_data': data[:200] + '...' if len(data) > 200 else data}
        except Exception as e:
            logger.warning(f"Erro ao sanitizar request data: {e}")
            return None
    
    def _sanitize_response_data(self, data: Optional[str]) -> Optional[Dict]:
        """Sanitizar dados da resposta"""
        if not data:
            return None
        
        try:
            # Parse JSON
            if isinstance(data, str):
                parsed = json.loads(data)
            else:
                parsed = data
            
            # Para respostas grandes, retornar apenas resumo
            if isinstance(parsed, list) and len(parsed) > 10:
                return {
                    'type': 'list',
                    'count': len(parsed),
                    'sample': parsed[:3]
                }
            
            # Remover campos sensíveis
            sensitive_fields = ['token', 'api_key', 'secret']
            return self._remove_sensitive_fields(parsed, sensitive_fields)
            
        except json.JSONDecodeError:
            # Se não for JSON, retornar resumo
            return {'raw_data': data[:200] + '...' if len(data) > 200 else data}
        except Exception as e:
            logger.warning(f"Erro ao sanitizar response data: {e}")
            return None
    
    def _remove_sensitive_fields(self, data: Any, fields: List[str]) -> Any:
        """Remover campos sensíveis recursivamente"""
        if isinstance(data, dict):
            result = {}
            for key, value in data.items():
                if any(field in key.lower() for field in fields):
                    result[key] = '***REDACTED***'
                else:
                    result[key] = self._remove_sensitive_fields(value, fields)
            return result
        
        elif isinstance(data, list):
            return [self._remove_sensitive_fields(item, fields) for item in data]
        
        else:
            return data


class AuditWebSocketMiddleware:
    """Middleware para auditoria de conexões WebSocket"""
    
    def __init__(self, app: ASGIApp, audit_service: AuditService):
        self.app = app
        self.audit_service = audit_service
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "websocket":
            # Extrair informações
            connection_id = str(uuid.uuid4())
            client_ip = None
            if scope.get("client"):
                client_ip = scope["client"][0]
            
            # Registrar conexão
            event = self.audit_service.create_event(
                event_type=AuditEventType.API_CALL,
                severity=AuditSeverity.INFO,
                ip_address=client_ip,
                resource_type='websocket',
                resource_id=scope["path"],
                action='connect',
                metadata={
                    'connection_id': connection_id,
                    'headers': dict(scope.get("headers", []))
                }
            )
            await self.audit_service.log_event(event)
            
            # Adicionar ID à scope
            scope["connection_id"] = connection_id
            
            # Processar
            try:
                await self.app(scope, receive, send)
            finally:
                # Registrar desconexão
                event = self.audit_service.create_event(
                    event_type=AuditEventType.API_CALL,
                    severity=AuditSeverity.INFO,
                    ip_address=client_ip,
                    resource_type='websocket',
                    resource_id=scope["path"],
                    action='disconnect',
                    metadata={
                        'connection_id': connection_id
                    }
                )
                await self.audit_service.log_event(event)
        else:
            await self.app(scope, receive, send)