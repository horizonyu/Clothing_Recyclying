"""
API v1 路由聚合
"""
from fastapi import APIRouter

from app.api.v1.user import router as user_router
from app.api.v1.order import router as order_router
from app.api.v1.device import router as device_router
from app.api.v1.wallet import router as wallet_router

router = APIRouter()

router.include_router(user_router, prefix="/user", tags=["用户"])
router.include_router(order_router, prefix="/order", tags=["订单"])
router.include_router(device_router, prefix="/device", tags=["设备"])
router.include_router(wallet_router, prefix="/wallet", tags=["钱包"])

