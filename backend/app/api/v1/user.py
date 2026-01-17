"""
用户API
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta
from jose import jwt
import httpx
import uuid
import os
import aiofiles

from app.db.database import get_db
from app.config import settings
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.user import (
    WechatLoginRequest, 
    UserLoginResponse, 
    UserProfileResponse,
    UpdateProfileRequest
)
from app.api.deps import get_current_user

router = APIRouter()

# 头像上传目录
AVATAR_UPLOAD_DIR = "static/avatars"


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


@router.put("/profile", response_model=ResponseModel)
async def update_profile(
    request: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """更新用户信息"""
    # 更新昵称
    if request.nickname is not None:
        # 验证昵称长度
        if len(request.nickname) > 20:
            raise HTTPException(status_code=400, detail="昵称不能超过20个字符")
        if len(request.nickname.strip()) == 0:
            raise HTTPException(status_code=400, detail="昵称不能为空")
        current_user.nickname = request.nickname.strip()
    
    # 更新头像
    if request.avatar_url is not None:
        current_user.avatar_url = request.avatar_url
    
    await db.commit()
    await db.refresh(current_user)
    
    return ResponseModel(
        message="更新成功",
        data=UserProfileResponse(
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
        )
    )


@router.post("/avatar/upload", response_model=ResponseModel)
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """上传头像"""
    # 验证文件类型
    allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="只支持 JPG、PNG、GIF、WEBP 格式的图片")
    
    # 验证文件大小（最大 2MB）
    content = await file.read()
    if len(content) > 2 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="图片大小不能超过 2MB")
    
    # 生成文件名
    ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    filename = f"{current_user.user_id}_{int(datetime.now().timestamp())}.{ext}"
    
    # 确保目录存在
    os.makedirs(AVATAR_UPLOAD_DIR, exist_ok=True)
    
    # 保存文件
    file_path = os.path.join(AVATAR_UPLOAD_DIR, filename)
    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)
    
    # 生成访问 URL
    avatar_url = f"/static/avatars/{filename}"
    
    # 更新用户头像
    current_user.avatar_url = avatar_url
    await db.commit()
    await db.refresh(current_user)
    
    return ResponseModel(
        message="上传成功",
        data={"avatar_url": avatar_url}
    )

