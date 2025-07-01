"""
Router para autenticação e gerenciamento de usuários
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import List

from src.auth.auth import (
    Token, User, UserCreate, UserUpdate,
    user_manager, create_tokens_for_user,
    get_current_active_user, require_admin,
    decode_token
)

router = APIRouter()


@router.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Endpoint de login OAuth2
    
    Use username e password para obter tokens de acesso
    
    Usuários de exemplo:
    - admin / admin123 (todas as permissões)
    - user / user123 (apenas leitura)
    """
    user = user_manager.authenticate_user(form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    tokens = create_tokens_for_user(user)
    return tokens


@router.post("/refresh", response_model=Token)
async def refresh_token(refresh_token: str):
    """
    Renova token de acesso usando refresh token
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Decodificar refresh token
    payload = decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise credentials_exception
    
    username = payload.get("sub")
    if not username:
        raise credentials_exception
    
    # Buscar usuário
    user = user_manager.get_user(username)
    if not user or user.disabled:
        raise credentials_exception
    
    # Criar novos tokens
    tokens = create_tokens_for_user(user)
    return tokens


@router.get("/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """
    Retorna informações do usuário atual
    """
    return current_user


@router.put("/me", response_model=User)
async def update_user_me(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """
    Atualiza informações do próprio usuário
    """
    # Não permitir alterar roles
    if user_update.roles is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot update own roles"
        )
    
    updated_user = user_manager.update_user(current_user.username, user_update)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return updated_user


@router.post("/register", response_model=User)
async def register(user_data: UserCreate):
    """
    Registra novo usuário (público, mas com role limitada)
    """
    # Forçar role viewer para auto-registro
    user_data.roles = ["viewer"]
    
    try:
        user = user_manager.create_user(user_data)
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# Endpoints administrativos
@router.get("/users", response_model=List[User])
async def list_users(
    current_user: User = Depends(require_admin)
):
    """
    Lista todos os usuários (requer admin)
    """
    users = []
    for user_in_db in user_manager.users.values():
        user = User(**user_in_db.dict(exclude={"hashed_password"}))
        users.append(user)
    
    return users


@router.get("/users/{username}", response_model=User)
async def get_user(
    username: str,
    current_user: User = Depends(require_admin)
):
    """
    Busca usuário específico (requer admin)
    """
    user = user_manager.get_user(username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return User(**user.dict(exclude={"hashed_password"}))


@router.post("/users", response_model=User)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(require_admin)
):
    """
    Cria novo usuário com qualquer role (requer admin)
    """
    try:
        user = user_manager.create_user(user_data)
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/users/{username}", response_model=User)
async def update_user(
    username: str,
    user_update: UserUpdate,
    current_user: User = Depends(require_admin)
):
    """
    Atualiza usuário (requer admin)
    """
    updated_user = user_manager.update_user(username, user_update)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return updated_user


@router.delete("/users/{username}")
async def delete_user(
    username: str,
    current_user: User = Depends(require_admin)
):
    """
    Remove usuário (requer admin)
    """
    if username == current_user.username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete own account"
        )
    
    if username in user_manager.users:
        del user_manager.users[username]
        return {"detail": "User deleted successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )


@router.get("/permissions")
async def get_my_permissions(
    current_user: User = Depends(get_current_active_user)
):
    """
    Retorna permissões do usuário atual
    """
    return {
        "username": current_user.username,
        "roles": current_user.roles,
        "scopes": current_user.scopes,
        "permissions": {
            "can_read": "read" in current_user.scopes,
            "can_write": "write" in current_user.scopes,
            "can_delete": "delete" in current_user.scopes,
            "is_admin": "admin" in current_user.scopes
        }
    }


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_active_user)):
    """
    Logout (cliente deve descartar tokens)
    
    Em produção, implementar blacklist de tokens
    """
    return {
        "detail": "Successfully logged out",
        "user": current_user.username
    }