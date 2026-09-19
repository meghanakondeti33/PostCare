from typing import List, Optional
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.domain import User, RoleEnum

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if not payload:
        raise credentials_exception
    user_id: str = payload.get("sub")
    if not user_id:
        raise credentials_exception
        
    stmt = select(User).where(User.id == user_id, User.is_active == True)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        raise credentials_exception
    return user

def require_roles(allowed_roles: List[RoleEnum]):
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {[r.value for r in allowed_roles]}"
            )
        return current_user
    return role_checker

async def get_tenant_hospital_id(
    x_hospital_id: Optional[str] = Header(None, alias="X-Hospital-Id"),
    current_user: User = Depends(get_current_user)
) -> str:
    # If user is associated with a hospital, enforce their hospital_id
    if current_user.role != RoleEnum.PLATFORM_ADMIN:
        if not current_user.hospital_id:
            raise HTTPException(status_code=403, detail="User has no hospital context")
        return current_user.hospital_id
    
    # If Platform Admin, allow passing X-Hospital-Id header
    if x_hospital_id:
        return x_hospital_id
    
    raise HTTPException(status_code=400, detail="Tenant hospital context (X-Hospital-Id) required for this request")
