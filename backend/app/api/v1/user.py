"""
用户API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta
from jose import jwt
import httpx
import uuid

from app.db.database import get_db
from app.config import settings
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.user import (
    WechatLoginRequest, 
    UserLoginResponse, 
    UserProfileResponse
)
from app.api.deps import get_current_user

router = APIRouter()


def generate_user_id() -> str:
    """生成用户ID"""
    return f"U{uuid.uuid4().hex[:11].upper()}"


def create_access_token(user_id: str) -> str:
    """创建访问Token"""
    expire = datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    payload = {
        "sub": user_id,
        "exp": expire
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


async def get_wechat_openid(code: str) -> dict:
    """通过code获取微信openid"""
    url = "https://api.weixin.qq.com/sns/jscode2session"
    params = {
        "appid": settings.WECHAT_APPID,
        "secret": settings.WECHAT_SECRET,
        "js_code": code,
        "grant_type": "authorization_code"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        data = response.json()
        
        if "errcode" in data and data["errcode"] != 0:
            raise HTTPException(
                status_code=400,
                detail=f"微信登录失败: {data.get('errmsg', '未知错误')}"
            )
        
        return data


@router.post("/login/wechat", response_model=ResponseModel)
async def wechat_login(
    request: WechatLoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """微信登录"""
    # 获取openid
    wx_data = await get_wechat_openid(request.code)
    openid = wx_data.get("openid")
    unionid = wx_data.get("unionid")
    
    if not openid:
        raise HTTPException(status_code=400, detail="获取openid失败")
    
    # 查询用户是否存在
    result = await db.execute(
        select(User).where(User.openid == openid)
    )
    user = result.scalar_one_or_none()
    
    is_new_user = False
    
    if not user:
        # 创建新用户
        user = User(
            user_id=generate_user_id(),
            openid=openid,
            unionid=unionid,
            nickname="回收达人",
            last_login_at=datetime.now()
        )
        db.add(user)
        is_new_user = True
    else:
        # 更新登录时间
        user.last_login_at = datetime.now()
    
    await db.commit()
    await db.refresh(user)
    
    # 生成Token
    token = create_access_token(user.user_id)
    
    return ResponseModel(data=UserLoginResponse(
        token=token,
        user_id=user.user_id,
        nickname=user.nickname,
        avatar_url=user.avatar_url,
        is_new_user=is_new_user
    ))


@router.get("/profile", response_model=ResponseModel)
async def get_profile(
    current_user: User = Depends(get_current_user)
):
    """获取用户信息"""
    return ResponseModel(data=UserProfileResponse(
        user_id=current_user.user_id,
        nickname=current_user.nickname,
        avatar_url=current_user.avatar_url,
        phone=current_user.phone,
        is_verified=current_user.is_verified,
        balance=current_user.balance,
        points=current_user.points,
        total_weight=current_user.total_weight,
        total_carbon=current_user.total_carbon,
        total_count=current_user.total_count
    ))

