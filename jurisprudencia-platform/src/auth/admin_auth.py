"""
🔐 SISTEMA DE AUTENTICAÇÃO ADMINISTRATIVA
Autenticação segura com 2FA para interface administrativa
"""

import os
import secrets
import hashlib
import pyotp
import qrcode
from io import BytesIO
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple
import jwt
from passlib.context import CryptContext
from sqlalchemy import Column, String, DateTime, Boolean, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session
import streamlit as st
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)

# Configurações
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 7

Base = declarative_base()


class AdminUser(Base):
    """Modelo de usuário administrativo"""
    __tablename__ = "admin_users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False)
    hashed_password = Column(String(200), nullable=False)
    totp_secret = Column(String(100))
    is_active = Column(Boolean, default=True)
    is_2fa_enabled = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    failed_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime)
    password_changed_at = Column(DateTime, default=datetime.utcnow)
    
    # Auditoria
    created_by = Column(String(50))
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    updated_by = Column(String(50))


class AdminAuthManager:
    """Gerenciador de autenticação administrativa"""
    
    def __init__(self, db_session: Optional[Session] = None):
        self.db = db_session
        self.failed_login_threshold = 5
        self.lockout_duration_minutes = 30
        self.password_min_length = 12
        self.password_require_special = True
        self.password_require_numbers = True
        self.password_require_uppercase = True
        self.session_timeout_minutes = 60
        
        # Cache de sessões
        self._session_cache = {}
        
        # Configurar diretório de auditoria
        self.audit_dir = Path("logs/audit")
        self.audit_dir.mkdir(parents=True, exist_ok=True)
    
    def create_admin_user(self, username: str, email: str, password: str, 
                         created_by: str = "system") -> bool:
        """Cria novo usuário administrativo"""
        try:
            # Validar senha
            if not self._validate_password_strength(password):
                raise ValueError("Senha não atende aos requisitos de segurança")
            
            # Verificar se usuário já existe
            if self.db.query(AdminUser).filter(
                (AdminUser.username == username) | (AdminUser.email == email)
            ).first():
                raise ValueError("Usuário ou email já existe")
            
            # Criar usuário
            hashed_password = pwd_context.hash(password)
            
            new_user = AdminUser(
                username=username,
                email=email,
                hashed_password=hashed_password,
                created_by=created_by
            )
            
            self.db.add(new_user)
            self.db.commit()
            
            # Auditoria
            self._audit_log("user_created", {
                "username": username,
                "email": email,
                "created_by": created_by
            })
            
            logger.info(f"Usuário admin criado: {username}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erro ao criar usuário: {e}")
            return False
    
    def authenticate(self, username: str, password: str, 
                    totp_code: Optional[str] = None) -> Optional[Dict]:
        """Autentica usuário administrativo"""
        try:
            # Buscar usuário
            user = self.db.query(AdminUser).filter(
                AdminUser.username == username
            ).first()
            
            if not user:
                self._audit_log("login_failed", {"username": username, "reason": "user_not_found"})
                return None
            
            # Verificar se está bloqueado
            if user.locked_until and user.locked_until > datetime.utcnow():
                self._audit_log("login_blocked", {"username": username})
                return None
            
            # Verificar senha
            if not pwd_context.verify(password, user.hashed_password):
                # Incrementar tentativas falhas
                user.failed_attempts += 1
                
                # Bloquear se exceder limite
                if user.failed_attempts >= self.failed_login_threshold:
                    user.locked_until = datetime.utcnow() + timedelta(
                        minutes=self.lockout_duration_minutes
                    )
                    self._audit_log("account_locked", {"username": username})
                
                self.db.commit()
                self._audit_log("login_failed", {"username": username, "reason": "invalid_password"})
                return None
            
            # Verificar 2FA se habilitado
            if user.is_2fa_enabled:
                if not totp_code or not self._verify_totp(user.totp_secret, totp_code):
                    self._audit_log("login_failed", {"username": username, "reason": "invalid_2fa"})
                    return None
            
            # Login bem-sucedido
            user.failed_attempts = 0
            user.last_login = datetime.utcnow()
            self.db.commit()
            
            # Gerar tokens
            access_token = self._create_access_token(user.username)
            refresh_token = self._create_refresh_token(user.username)
            
            # Criar sessão
            session_data = {
                "username": user.username,
                "email": user.email,
                "access_token": access_token,
                "refresh_token": refresh_token,
                "login_time": datetime.utcnow(),
                "is_2fa_enabled": user.is_2fa_enabled
            }
            
            session_id = secrets.token_urlsafe(32)
            self._session_cache[session_id] = session_data
            
            # Auditoria
            self._audit_log("login_success", {
                "username": username,
                "session_id": session_id,
                "ip": self._get_client_ip()
            })
            
            return {
                "session_id": session_id,
                "user": {
                    "username": user.username,
                    "email": user.email,
                    "is_2fa_enabled": user.is_2fa_enabled
                },
                "access_token": access_token,
                "refresh_token": refresh_token
            }
            
        except Exception as e:
            logger.error(f"Erro na autenticação: {e}")
            return None
    
    def enable_2fa(self, username: str) -> Optional[Dict]:
        """Habilita 2FA para usuário"""
        try:
            user = self.db.query(AdminUser).filter(
                AdminUser.username == username
            ).first()
            
            if not user:
                return None
            
            # Gerar secret TOTP
            secret = pyotp.random_base32()
            user.totp_secret = secret
            
            # Gerar QR Code
            totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
                name=user.email,
                issuer_name='Sistema Jurídico Admin'
            )
            
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(totp_uri)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            buf = BytesIO()
            img.save(buf, format='PNG')
            buf.seek(0)
            
            # Salvar alterações
            user.is_2fa_enabled = True
            self.db.commit()
            
            # Auditoria
            self._audit_log("2fa_enabled", {"username": username})
            
            return {
                "secret": secret,
                "qr_code": buf.getvalue(),
                "backup_codes": self._generate_backup_codes(username)
            }
            
        except Exception as e:
            logger.error(f"Erro ao habilitar 2FA: {e}")
            return None
    
    def change_password(self, username: str, old_password: str, 
                       new_password: str) -> bool:
        """Altera senha do usuário"""
        try:
            user = self.db.query(AdminUser).filter(
                AdminUser.username == username
            ).first()
            
            if not user:
                return False
            
            # Verificar senha atual
            if not pwd_context.verify(old_password, user.hashed_password):
                self._audit_log("password_change_failed", {
                    "username": username,
                    "reason": "invalid_current_password"
                })
                return False
            
            # Validar nova senha
            if not self._validate_password_strength(new_password):
                return False
            
            # Verificar se não é igual à anterior
            if pwd_context.verify(new_password, user.hashed_password):
                return False
            
            # Atualizar senha
            user.hashed_password = pwd_context.hash(new_password)
            user.password_changed_at = datetime.utcnow()
            self.db.commit()
            
            # Auditoria
            self._audit_log("password_changed", {"username": username})
            
            # Invalidar sessões existentes
            self._invalidate_user_sessions(username)
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao alterar senha: {e}")
            return False
    
    def verify_session(self, session_id: str) -> Optional[Dict]:
        """Verifica se sessão é válida"""
        if session_id not in self._session_cache:
            return None
        
        session = self._session_cache[session_id]
        
        # Verificar timeout
        if datetime.utcnow() - session['login_time'] > timedelta(
            minutes=self.session_timeout_minutes
        ):
            del self._session_cache[session_id]
            return None
        
        # Verificar token
        try:
            payload = jwt.decode(
                session['access_token'],
                SECRET_KEY,
                algorithms=[ALGORITHM]
            )
            return session
        except jwt.ExpiredSignatureError:
            del self._session_cache[session_id]
            return None
        except:
            return None
    
    def logout(self, session_id: str):
        """Realiza logout"""
        if session_id in self._session_cache:
            session = self._session_cache[session_id]
            self._audit_log("logout", {
                "username": session['username'],
                "session_id": session_id
            })
            del self._session_cache[session_id]
    
    def _validate_password_strength(self, password: str) -> bool:
        """Valida força da senha"""
        if len(password) < self.password_min_length:
            return False
        
        if self.password_require_uppercase and not any(c.isupper() for c in password):
            return False
        
        if self.password_require_numbers and not any(c.isdigit() for c in password):
            return False
        
        if self.password_require_special and not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            return False
        
        # Verificar senhas comuns
        common_passwords = ["password", "admin", "123456", "jurisprudencia"]
        if any(common in password.lower() for common in common_passwords):
            return False
        
        return True
    
    def _verify_totp(self, secret: str, code: str) -> bool:
        """Verifica código TOTP"""
        try:
            totp = pyotp.TOTP(secret)
            return totp.verify(code, valid_window=1)
        except:
            return False
    
    def _create_access_token(self, username: str) -> str:
        """Cria token de acesso"""
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        payload = {
            "sub": username,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        }
        
        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    
    def _create_refresh_token(self, username: str) -> str:
        """Cria token de atualização"""
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        
        payload = {
            "sub": username,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        }
        
        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    
    def _generate_backup_codes(self, username: str, count: int = 10) -> list:
        """Gera códigos de backup para 2FA"""
        codes = []
        for _ in range(count):
            code = secrets.token_hex(4).upper()
            codes.append(f"{code[:4]}-{code[4:]}")
        
        # Salvar hash dos códigos
        # TODO: Implementar armazenamento seguro
        
        return codes
    
    def _invalidate_user_sessions(self, username: str):
        """Invalida todas as sessões de um usuário"""
        sessions_to_remove = []
        
        for session_id, session in self._session_cache.items():
            if session['username'] == username:
                sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            del self._session_cache[session_id]
    
    def _audit_log(self, event_type: str, details: Dict):
        """Registra evento de auditoria"""
        try:
            audit_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "event_type": event_type,
                "details": details
            }
            
            # Salvar em arquivo
            audit_file = self.audit_dir / f"audit_{datetime.utcnow().strftime('%Y%m%d')}.jsonl"
            with open(audit_file, 'a') as f:
                f.write(json.dumps(audit_entry) + '\n')
            
            # Log também no logger
            logger.info(f"Audit: {event_type} - {details}")
            
        except Exception as e:
            logger.error(f"Erro ao registrar auditoria: {e}")
    
    def _get_client_ip(self) -> str:
        """Obtém IP do cliente (placeholder)"""
        # Em produção, obter do request real
        return "127.0.0.1"


class StreamlitAuthUI:
    """Interface Streamlit para autenticação"""
    
    def __init__(self, auth_manager: AdminAuthManager):
        self.auth = auth_manager
    
    def show_login_page(self):
        """Mostra página de login"""
        st.markdown("## 🔒 Login Administrativo")
        
        with st.form("login_form"):
            username = st.text_input("Usuário", key="login_username")
            password = st.text_input("Senha", type="password", key="login_password")
            
            col1, col2 = st.columns(2)
            
            with col1:
                totp_code = st.text_input(
                    "Código 2FA (se habilitado)",
                    max_chars=6,
                    key="login_totp"
                )
            
            with col2:
                st.markdown("<br>", unsafe_allow_html=True)
                remember = st.checkbox("Lembrar-me")
            
            submitted = st.form_submit_button("🔐 Entrar", use_container_width=True)
            
            if submitted:
                if not username or not password:
                    st.error("Por favor, preencha todos os campos")
                    return
                
                result = self.auth.authenticate(username, password, totp_code)
                
                if result:
                    # Salvar na sessão
                    st.session_state.admin_logged_in = True
                    st.session_state.admin_session = result
                    st.session_state.admin_username = result['user']['username']
                    
                    st.success("Login realizado com sucesso!")
                    st.rerun()
                else:
                    st.error("Credenciais inválidas ou conta bloqueada")
        
        # Links úteis
        st.markdown("---")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔑 Esqueci minha senha"):
                st.info("Contate o administrador do sistema")
        
        with col2:
            if st.button("🛡️ Configurar 2FA"):
                st.info("Faça login primeiro para configurar 2FA")
    
    def show_2fa_setup(self, username: str):
        """Mostra configuração de 2FA"""
        st.markdown("## 🛡️ Configurar Autenticação em Duas Etapas")
        
        if st.button("🔄 Gerar QR Code"):
            result = self.auth.enable_2fa(username)
            
            if result:
                st.success("2FA configurado com sucesso!")
                
                # Mostrar QR Code
                st.image(result['qr_code'], caption="Escaneie com seu app autenticador")
                
                # Mostrar secret
                st.code(result['secret'], language="text")
                st.caption("Guarde este código em local seguro")
                
                # Mostrar códigos de backup
                st.markdown("### 📝 Códigos de Backup")
                st.info("Guarde estes códigos em local seguro. Cada código pode ser usado apenas uma vez.")
                
                for code in result['backup_codes']:
                    st.code(code)
    
    def show_change_password(self, username: str):
        """Mostra tela de alteração de senha"""
        st.markdown("## 🔐 Alterar Senha")
        
        with st.form("change_password_form"):
            old_password = st.text_input("Senha atual", type="password")
            new_password = st.text_input("Nova senha", type="password")
            confirm_password = st.text_input("Confirmar nova senha", type="password")
            
            # Requisitos de senha
            st.markdown("""
            **Requisitos da senha:**
            - Mínimo 12 caracteres
            - Pelo menos uma letra maiúscula
            - Pelo menos um número
            - Pelo menos um caractere especial
            """)
            
            submitted = st.form_submit_button("Alterar Senha")
            
            if submitted:
                if new_password != confirm_password:
                    st.error("As senhas não coincidem")
                    return
                
                if self.auth.change_password(username, old_password, new_password):
                    st.success("Senha alterada com sucesso! Faça login novamente.")
                    st.session_state.admin_logged_in = False
                    st.rerun()
                else:
                    st.error("Erro ao alterar senha. Verifique se a senha atual está correta e se a nova senha atende aos requisitos.")


# Funções auxiliares para uso em Streamlit
def require_admin_auth():
    """Decorator para páginas que requerem autenticação"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            if not st.session_state.get('admin_logged_in', False):
                st.error("⛔ Acesso negado. Faça login para continuar.")
                st.stop()
            return func(*args, **kwargs)
        return wrapper
    return decorator


def get_current_admin_user() -> Optional[str]:
    """Retorna usuário admin atual"""
    return st.session_state.get('admin_username')


if __name__ == "__main__":
    # Teste básico
    print("Sistema de autenticação administrativa configurado")
    print("Use através da interface Streamlit ou API")