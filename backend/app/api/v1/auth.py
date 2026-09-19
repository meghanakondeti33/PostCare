from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import verify_password, create_access_token
from app.models.domain import User
from app.schemas.domain import LoginRequest, Token, UserOut
from app.core.dependencies import get_current_user

router = APIRouter()

@router.post("/login", response_model=Token)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    stmt = select(User).where(User.email == req.email, User.is_active == True)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
        
    token = create_access_token(data={"sub": user.id, "role": user.role.value, "hospital_id": user.hospital_id})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user
    }

@router.get("/me", response_model=UserOut)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user
