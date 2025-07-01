"""
Sistema de autenticação e autorização com JWT
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, List
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
import os

# Configurações
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Contexto de criptografia
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


# Modelos
class Token(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: Optional[str] = None
    scopes: List[str] = []


class User(BaseModel):
    id: str
    username: str
    email: str
    full_name: Optional[str] = None
    disabled: bool = False
    roles: List[str] = []
    created_at: datetime
    
    @property
    def scopes(self) -> List[str]:
        """Converte roles em scopes"""
        scopes = []
        role_scopes = {
            "admin": ["read", "write", "delete", "admin"],
            "editor": ["read", "write"],
            "viewer": ["read"]
        }
        
        for role in self.roles:
            scopes.extend(role_scopes.get(role, []))
        
        return list(set(scopes))  # Remove duplicatas


class UserInDB(User):
    hashed_password: str


class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    full_name: Optional[str] = None
    roles: List[str] = ["viewer"]


class UserUpdate(BaseModel):
    email: Optional[str] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    disabled: Optional[bool] = None
    roles: Optional[List[str]] = None


# Funções de hash
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica se a senha está correta"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Gera hash da senha"""
    return pwd_context.hash(password)


# Funções de token
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Cria token de acesso JWT"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt


def create_refresh_token(data: dict):
    """Cria token de refresh JWT"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt


def decode_token(token: str) -> Dict:
    """Decodifica e valida token JWT"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


# Gerenciador de usuários (simplificado - usar banco em produção)
class UserManager:
    """Gerenciador de usuários em memória (substituir por banco)"""
    
    def __init__(self):
        # Usuários de exemplo
        self.users = {
            "admin": UserInDB(
                id="1",
                username="admin",
                email="admin@jurisprudencia.com",
                full_name="Administrator",
                hashed_password=get_password_hash("admin123"),
                disabled=False,
                roles=["admin"],
                created_at=datetime.utcnow()
            ),
            "user": UserInDB(
                id="2",
                username="user",
                email="user@jurisprudencia.com",
                full_name="Regular User",
                hashed_password=get_password_hash("user123"),
                disabled=False,
                roles=["viewer"],
                created_at=datetime.utcnow()
            )
        }
    
    def get_user(self, username: str) -> Optional[UserInDB]:
        """Busca usuário por username"""
        return self.users.get(username)
    
    def get_user_by_email(self, email: str) -> Optional[UserInDB]:
        """Busca usuário por email"""
        for user in self.users.values():
            if user.email == email:
                return user
        return None
    
    def create_user(self, user_data: UserCreate) -> User:
        """Cria novo usuário"""
        # Verificar se já existe
        if self.get_user(user_data.username):
            raise ValueError("Username já existe")
        
        if self.get_user_by_email(user_data.email):
            raise ValueError("Email já cadastrado")
        
        # Criar usuário
        user_id = str(len(self.users) + 1)
        user = UserInDB(
            id=user_id,
            username=user_data.username,
            email=user_data.email,
            full_name=user_data.full_name,
            hashed_password=get_password_hash(user_data.password),
            disabled=False,
            roles=user_data.roles,
            created_at=datetime.utcnow()
        )
        
        self.users[user_data.username] = user
        
        # Retornar sem senha
        return User(**user.dict(exclude={"hashed_password"}))
    
    def update_user(self, username: str, user_update: UserUpdate) -> Optional[User]:
        """Atualiza usuário"""
        user = self.get_user(username)
        if not user:
            return None
        
        update_data = user_update.dict(exclude_unset=True)
        
        # Hash nova senha se fornecida
        if "password" in update_data:
            update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
        
        # Atualizar campos
        for field, value in update_data.items():
            setattr(user, field, value)
        
        return User(**user.dict(exclude={"hashed_password"}))
    
    def authenticate_user(self, username: str, password: str) -> Optional[UserInDB]:
        """Autentica usuário"""
        user = self.get_user(username)
        if not user:
            return None
        
        if not verify_password(password, user.hashed_password):
            return None
        
        return user


# Instância global do gerenciador
user_manager = UserManager()


# Dependências de autenticação
async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """Obtém usuário atual do token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Decodificar token
    payload = decode_token(token)
    if payload is None:
        raise credentials_exception
    
    # Verificar tipo de token
    if payload.get("type") != "access":
        raise credentials_exception
    
    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception
    
    # Buscar usuário
    user = user_manager.get_user(username=username)
    if user is None:
        raise credentials_exception
    
    if user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    return User(**user.dict(exclude={"hashed_password"}))


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Verifica se usuário está ativo"""
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def check_permissions(required_scopes: List[str]):
    """Decorator para verificar permissões"""
    async def permission_checker(
        current_user: User = Depends(get_current_active_user)
    ):
        user_scopes = current_user.scopes
        
        for scope in required_scopes:
            if scope not in user_scopes:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Not enough permissions. Required: {required_scopes}"
                )
        
        return current_user
    
    return permission_checker


# Aliases para permissões comuns
require_read = check_permissions(["read"])
require_write = check_permissions(["write"])
require_admin = check_permissions(["admin"])


# Funções auxiliares
def create_tokens_for_user(user: UserInDB) -> Dict[str, str]:
    """Cria tokens de acesso e refresh para usuário"""
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Dados do token
    token_data = {
        "sub": user.username,
        "scopes": user.scopes
    }
    
    # Criar tokens
    access_token = create_access_token(
        data=token_data,
        expires_delta=access_token_expires
    )
    
    refresh_token = create_refresh_token(data={"sub": user.username})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }