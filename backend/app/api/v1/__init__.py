"""
API v1 路由聚合
"""
from fastapi import APIRouter

from app.api.v1.user import router as user_router
from app.api.v1.order import router as order_router
from app.api.v1.device import router as device_router
from app.api.v1.device_communication import router as device_comm_router
from app.api.v1.wallet import router as wallet_router
from app.api.v1.payment import router as payment_router
from app.api.v1.admin import router as admin_router
from app.api.v1.admin_device import router as admin_device_router
from app.api.v1.admin_order import router as admin_order_router
from app.api.v1.admin_user import router as admin_user_router

router = APIRouter()

router.include_router(user_router, prefix="/user", tags=["用户"])
router.include_router(order_router, prefix="/order", tags=["订单"])
router.include_router(device_router, prefix="/device", tags=["设备"])
router.include_router(device_comm_router, prefix="/device", tags=["设备通信"])
router.include_router(wallet_router, prefix="/wallet", tags=["钱包"])
router.include_router(payment_router, tags=["支付"])
router.include_router(admin_router, prefix="/admin", tags=["管理后台"])
router.include_router(admin_device_router, prefix="/admin", tags=["管理后台-设备"])
router.include_router(admin_order_router, prefix="/admin", tags=["管理后台-订单"])
router.include_router(admin_user_router, prefix="/admin", tags=["管理后台-用户"])

