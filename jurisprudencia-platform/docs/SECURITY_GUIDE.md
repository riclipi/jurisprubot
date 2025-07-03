# 🔒 GUIA DE SEGURANÇA DA PLATAFORMA

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Autenticação e Autorização](#autenticação-e-autorização)
3. [Criptografia](#criptografia)
4. [Segurança de API](#segurança-de-api)
5. [Segurança de Dados](#segurança-de-dados)
6. [Certificados Digitais](#certificados-digitais)
7. [Auditoria](#auditoria)
8. [Compliance](#compliance)
9. [Resposta a Incidentes](#resposta-a-incidentes)

## 🎯 Visão Geral

Este guia detalha todas as medidas de segurança implementadas na plataforma.

### Princípios de Segurança

1. **Defense in Depth**: Múltiplas camadas de segurança
2. **Least Privilege**: Mínimo privilégio necessário
3. **Zero Trust**: Verificar sempre, nunca confiar
4. **Encryption Everywhere**: Criptografia em todos os níveis

## 🔐 Autenticação e Autorização

### Sistema de Autenticação

#### JWT (JSON Web Tokens)
```python
# Configuração JWT
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 30
JWT_REFRESH_TOKEN_EXPIRE_DAYS = 7
```

#### Autenticação em 2 Fatores (2FA)
```python
# Usando TOTP (Time-based One-Time Password)
from src.auth.admin_auth import AdminAuthManager

auth_manager = AdminAuthManager()

# Gerar QR Code para 2FA
qr_code = auth_manager.generate_2fa_qr(username)

# Verificar código TOTP
is_valid = auth_manager.verify_totp(username, totp_code)
```

### Políticas de Senha

```python
# Requisitos mínimos
PASSWORD_MIN_LENGTH = 12
PASSWORD_REQUIRE_UPPERCASE = True
PASSWORD_REQUIRE_LOWERCASE = True
PASSWORD_REQUIRE_DIGITS = True
PASSWORD_REQUIRE_SPECIAL = True
PASSWORD_HISTORY_SIZE = 5
PASSWORD_MAX_AGE_DAYS = 90
```

### Rate Limiting

```python
# Configuração de rate limiting
RATE_LIMIT_STRATEGIES = {
    "default": {
        "rate": "100/minute",
        "burst": 20
    },
    "auth": {
        "rate": "5/minute",
        "burst": 2
    },
    "api": {
        "rate": "1000/hour",
        "burst": 100
    }
}
```

## 🔐 Criptografia

### Criptografia de Credenciais

```python
from src.config.credentials_manager import CredentialsManager

# Gerenciar credenciais com segurança
cred_manager = CredentialsManager()

# Adicionar credencial criptografada
cred_manager.add_credential(
    name="tribunal_api",
    username="user",
    password="pass",
    api_key="key",
    extra_data={"endpoint": "https://api.tribunal.jus.br"}
)

# Recuperar credencial descriptografada
cred = cred_manager.get_credential("tribunal_api")
```

### Criptografia de Dados em Trânsito

```nginx
# Configuração SSL/TLS no Nginx
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
ssl_prefer_server_ciphers off;
ssl_session_cache shared:SSL:10m;
ssl_session_timeout 10m;
ssl_stapling on;
ssl_stapling_verify on;
```

### Criptografia de Dados em Repouso

```python
# Backup criptografado
from cryptography.fernet import Fernet

def encrypt_backup(data: bytes, key: bytes) -> bytes:
    f = Fernet(key)
    return f.encrypt(data)

def decrypt_backup(encrypted_data: bytes, key: bytes) -> bytes:
    f = Fernet(key)
    return f.decrypt(encrypted_data)
```

## 🛡️ Segurança de API

### Headers de Segurança

```python
# Middleware de segurança
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://app.jurisprudencia.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Trusted Host
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["api.jurisprudencia.com", "*.jurisprudencia.com"]
)

# Security Headers
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response
```

### Validação de Input

```python
from pydantic import BaseModel, validator, Field
from typing import Optional
import re

class ProcessoInput(BaseModel):
    numero_cnj: str = Field(..., regex=r'^\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}$')
    titulo: str = Field(..., min_length=1, max_length=200)
    
    @validator('numero_cnj')
    def validate_cnj(cls, v):
        from src.utils.cnj_validator import validar_numero_cnj
        if not validar_numero_cnj(v):
            raise ValueError('Número CNJ inválido')
        return v
    
    @validator('titulo')
    def sanitize_titulo(cls, v):
        # Remove caracteres perigosos
        return re.sub(r'[<>\"\'&]', '', v)
```

### Proteção contra Injeção

```python
# SQL Injection Prevention
from sqlalchemy import text
from sqlalchemy.orm import Session

def safe_query(db: Session, user_input: str):
    # NUNCA fazer isso:
    # query = f"SELECT * FROM processos WHERE titulo = '{user_input}'"
    
    # Sempre usar parâmetros
    stmt = text("SELECT * FROM processos WHERE titulo = :titulo")
    result = db.execute(stmt, {"titulo": user_input})
    return result.fetchall()

# NoSQL Injection Prevention
def safe_mongo_query(collection, user_input: str):
    # Sanitizar input
    sanitized = re.escape(user_input)
    
    # Query segura
    return collection.find({
        "titulo": {"$regex": sanitized, "$options": "i"}
    })
```

## 💾 Segurança de Dados

### Classificação de Dados

```python
from enum import Enum

class DataClassification(Enum):
    PUBLIC = "public"           # Dados públicos
    INTERNAL = "internal"       # Uso interno apenas
    CONFIDENTIAL = "confidential"  # Dados sensíveis
    RESTRICTED = "restricted"   # Altamente sensível

# Aplicar políticas baseadas na classificação
def apply_security_policy(data_class: DataClassification):
    policies = {
        DataClassification.PUBLIC: {
            "encryption": False,
            "audit": False,
            "retention_days": 365
        },
        DataClassification.CONFIDENTIAL: {
            "encryption": True,
            "audit": True,
            "retention_days": 2555  # 7 anos
        },
        DataClassification.RESTRICTED: {
            "encryption": True,
            "audit": True,
            "retention_days": 3650,  # 10 anos
            "access_control": "strict"
        }
    }
    return policies.get(data_class)
```

### Anonimização de Dados

```python
import hashlib
from faker import Faker

fake = Faker('pt_BR')

def anonymize_personal_data(data: dict) -> dict:
    """Anonimizar dados pessoais"""
    anonymized = data.copy()
    
    # Substituir nomes
    if 'nome' in anonymized:
        anonymized['nome'] = fake.name()
    
    # Mascarar CPF
    if 'cpf' in anonymized:
        cpf = anonymized['cpf']
        anonymized['cpf'] = f"***.***.{cpf[-6:-2]}-**"
    
    # Hash de email
    if 'email' in anonymized:
        email_hash = hashlib.sha256(anonymized['email'].encode()).hexdigest()[:8]
        anonymized['email'] = f"user_{email_hash}@example.com"
    
    return anonymized
```

### Backup Seguro

```python
import subprocess
import os
from datetime import datetime

def secure_backup():
    """Realizar backup seguro e criptografado"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 1. Dump do banco
    dump_file = f"/tmp/backup_{timestamp}.sql"
    subprocess.run([
        "pg_dump",
        "-h", os.getenv("DB_HOST"),
        "-U", os.getenv("DB_USER"),
        "-d", os.getenv("DB_NAME"),
        "-f", dump_file
    ])
    
    # 2. Criptografar
    encrypted_file = f"/backups/backup_{timestamp}.sql.enc"
    subprocess.run([
        "openssl", "enc", "-aes-256-cbc",
        "-salt", "-pbkdf2",
        "-in", dump_file,
        "-out", encrypted_file,
        "-k", os.getenv("BACKUP_PASSWORD")
    ])
    
    # 3. Remover arquivo não criptografado
    os.remove(dump_file)
    
    # 4. Upload para storage seguro
    subprocess.run([
        "aws", "s3", "cp",
        encrypted_file,
        f"s3://jurisprudencia-backups/{timestamp}/",
        "--sse", "AES256"
    ])
```

## 📜 Certificados Digitais

### Integração com A3/Token

```python
from src.certificates.pkcs11_manager import PKCS11Manager

# Configurar PKCS#11
pkcs11_manager = PKCS11Manager(
    library_path="/usr/lib/libaetpkss.so",
    token_label="Certificado A3"
)

# Listar certificados
certificates = pkcs11_manager.list_certificates()

# Assinar documento
with open("documento.pdf", "rb") as f:
    document_data = f.read()

signature = pkcs11_manager.sign_data(
    data=document_data,
    cert_id=certificates[0]['id'],
    pin="123456"
)
```

### Validação de Certificados

```python
from cryptography import x509
from cryptography.x509.oid import NameOID
from datetime import datetime

def validate_certificate(cert_data: bytes) -> dict:
    """Validar certificado digital"""
    cert = x509.load_pem_x509_certificate(cert_data)
    
    # Verificar validade
    now = datetime.utcnow()
    is_valid = cert.not_valid_before <= now <= cert.not_valid_after
    
    # Extrair informações
    subject = cert.subject
    cn = subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value
    
    # Verificar cadeia de certificação
    # TODO: Implementar verificação completa da cadeia
    
    return {
        "valid": is_valid,
        "common_name": cn,
        "not_before": cert.not_valid_before,
        "not_after": cert.not_valid_after,
        "serial_number": str(cert.serial_number)
    }
```

## 📝 Auditoria

### Sistema de Auditoria Completo

```python
from src.audit.audit_system import AuditSystem, AuditEvent

audit_system = AuditSystem()

# Registrar evento
await audit_system.log_event(
    AuditEvent(
        event_type="data_access",
        user_id="admin",
        resource_id="processo_123",
        action="read",
        ip_address="192.168.1.100",
        user_agent="Mozilla/5.0...",
        details={
            "fields_accessed": ["numero_cnj", "partes"],
            "purpose": "consulta_judicial"
        }
    )
)

# Buscar eventos suspeitos
suspicious = await audit_system.find_suspicious_activity(
    user_id="admin",
    hours=24
)
```

### Monitoramento em Tempo Real

```python
# Detectar anomalias
async def detect_anomalies():
    """Detectar comportamento anômalo"""
    # Taxa de requisições anormal
    high_rate_users = await audit_system.get_high_rate_users(
        threshold=1000,  # requisições/hora
        window_hours=1
    )
    
    # Acessos fora do horário
    after_hours = await audit_system.get_after_hours_access(
        start_hour=22,
        end_hour=6
    )
    
    # Múltiplas tentativas de login falhas
    failed_logins = await audit_system.get_failed_logins(
        threshold=5,
        window_minutes=10
    )
    
    return {
        "high_rate_users": high_rate_users,
        "after_hours_access": after_hours,
        "failed_logins": failed_logins
    }
```

## ✅ Compliance

### LGPD (Lei Geral de Proteção de Dados)

```python
class LGPDCompliance:
    """Conformidade com LGPD"""
    
    async def export_user_data(self, user_id: str) -> dict:
        """Exportar todos os dados do usuário (Art. 18)"""
        data = {
            "profile": await self.get_user_profile(user_id),
            "processos": await self.get_user_processos(user_id),
            "logs": await self.get_user_logs(user_id),
            "consents": await self.get_user_consents(user_id)
        }
        return data
    
    async def delete_user_data(self, user_id: str, reason: str):
        """Deletar dados do usuário (Art. 18, V)"""
        # Registrar solicitação
        await self.log_deletion_request(user_id, reason)
        
        # Anonimizar dados que devem ser mantidos
        await self.anonymize_user_data(user_id)
        
        # Deletar dados pessoais
        await self.delete_personal_data(user_id)
        
        # Notificar sistemas dependentes
        await self.notify_deletion(user_id)
    
    async def get_data_retention_policy(self) -> dict:
        """Política de retenção de dados"""
        return {
            "access_logs": {"days": 90, "reason": "segurança"},
            "audit_logs": {"days": 2555, "reason": "compliance"},
            "user_data": {"days": 1825, "reason": "legal"},
            "backups": {"days": 365, "reason": "recuperação"}
        }
```

### Segurança Judicial

```python
class JudicialSecurity:
    """Segurança específica para dados judiciais"""
    
    def validate_access_permission(self, user: User, processo: Processo) -> bool:
        """Validar permissão de acesso a processo"""
        # Verificar se processo é sigiloso
        if processo.sigilo:
            return user.has_permission("access_sigiloso")
        
        # Verificar se usuário é parte
        if user.cpf in processo.partes_cpfs:
            return True
        
        # Verificar se é advogado
        if user.oab and user.oab in processo.advogados_oabs:
            return True
        
        # Verificar permissões gerais
        return user.has_permission("access_processo")
    
    def mask_sensitive_data(self, processo: dict) -> dict:
        """Mascarar dados sensíveis"""
        masked = processo.copy()
        
        # Mascarar CPFs
        if 'partes' in masked:
            for parte in masked['partes']:
                if 'cpf' in parte:
                    parte['cpf'] = self._mask_cpf(parte['cpf'])
        
        # Ocultar valores em segredo de justiça
        if masked.get('segredo_justica'):
            masked['valor_causa'] = "***SIGILOSO***"
            masked['detalhes'] = "***SIGILOSO***"
        
        return masked
```

## 🚨 Resposta a Incidentes

### Plano de Resposta

```python
class IncidentResponse:
    """Sistema de resposta a incidentes"""
    
    async def handle_security_incident(self, incident_type: str, details: dict):
        """Responder a incidente de segurança"""
        incident_id = str(uuid.uuid4())
        
        # 1. Contenção
        if incident_type == "brute_force":
            await self.block_ip(details['ip_address'])
        elif incident_type == "data_breach":
            await self.disable_affected_accounts(details['user_ids'])
        
        # 2. Investigação
        investigation = await self.investigate_incident(incident_type, details)
        
        # 3. Notificação
        await self.notify_security_team(incident_id, incident_type, investigation)
        
        # 4. Documentação
        await self.document_incident(incident_id, {
            "type": incident_type,
            "details": details,
            "investigation": investigation,
            "actions_taken": self.get_actions_log(incident_id)
        })
        
        # 5. Recuperação
        if incident_type == "ransomware":
            await self.initiate_disaster_recovery()
        
        return incident_id
```

### Procedimentos de Emergência

```bash
#!/bin/bash
# emergency_lockdown.sh

echo "🚨 INICIANDO LOCKDOWN DE EMERGÊNCIA"

# 1. Bloquear todo tráfego externo
iptables -I INPUT -j DROP
iptables -I OUTPUT -j DROP
iptables -I INPUT -s 10.0.0.0/8 -j ACCEPT  # Permitir apenas rede interna

# 2. Parar serviços expostos
docker-compose -f docker-compose.production.yml stop nginx

# 3. Backup emergencial
/scripts/emergency_backup.sh

# 4. Notificar equipe
curl -X POST https://api.slack.com/notify \
  -H "Content-Type: application/json" \
  -d '{"text":"🚨 LOCKDOWN DE EMERGÊNCIA ATIVADO!"}'

echo "✅ Lockdown completo. Aguardando instruções..."
```

## 📊 Métricas de Segurança

### KPIs de Segurança

```python
class SecurityMetrics:
    """Métricas de segurança"""
    
    async def calculate_security_score(self) -> dict:
        """Calcular score de segurança"""
        metrics = {
            "patch_compliance": await self.get_patch_compliance(),
            "vulnerability_count": await self.get_open_vulnerabilities(),
            "incident_response_time": await self.get_avg_response_time(),
            "failed_login_rate": await self.get_failed_login_rate(),
            "encryption_coverage": await self.get_encryption_coverage(),
            "audit_compliance": await self.get_audit_compliance()
        }
        
        # Calcular score (0-100)
        score = 100
        score -= metrics["vulnerability_count"] * 5
        score -= (100 - metrics["patch_compliance"]) * 0.3
        score -= max(0, metrics["incident_response_time"] - 30) * 0.1
        score -= metrics["failed_login_rate"] * 10
        score -= (100 - metrics["encryption_coverage"]) * 0.2
        score -= (100 - metrics["audit_compliance"]) * 0.2
        
        return {
            "score": max(0, min(100, score)),
            "metrics": metrics,
            "rating": self._get_rating(score)
        }
```

---

**Última atualização**: Janeiro 2025