"""
支付相关API - 微信支付回调等
"""
from fastapi import APIRouter, Request, HTTPException, Depends
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import get_db
from app.models.withdraw import WithdrawRecord, WithdrawStatus
from app.schemas.common import ResponseModel

router = APIRouter(prefix="/payment", tags=["支付"])


@router.post("/wechat/notify/transfer")
async def wechat_transfer_notify(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    微信转账回调通知
    注意：实际使用时需要在微信商户平台配置回调URL
    """
    try:
        # 获取请求头
        headers = dict(request.headers)
        signature = headers.get("Wechatpay-Signature")
        timestamp = headers.get("Wechatpay-Timestamp")
        nonce = headers.get("Wechatpay-Nonce")
        serial = headers.get("Wechatpay-Serial")
        
        # 获取请求体
        body = await request.body()
        
        logger.info(f"收到微信转账回调: signature={signature}, timestamp={timestamp}")
        logger.info(f"回调数据: {body.decode('utf-8')}")
        
        # TODO: 验证签名
        # 这里需要验证微信回调的签名，确保请求来自微信
        
        # 解析回调数据
        import json
        data = json.loads(body.decode('utf-8'))
        
        # 根据回调类型处理
        event_type = data.get("event_type")
        resource = data.get("resource", {})
        
        if event_type == "TRANSFER.SUCCESS":
            # 转账成功
            batch_id = resource.get("batch_id")
            out_batch_no = resource.get("out_batch_no")
            
            # 查找提现记录
            result = await db.execute(
                select(WithdrawRecord).where(
                    WithdrawRecord.withdraw_id == out_batch_no
                )
            )
            withdraw_record = result.scalar_one_or_none()
            
            if withdraw_record:
                withdraw_record.status = WithdrawStatus.SUCCESS.value
                await db.commit()
                logger.info(f"提现成功更新: withdraw_id={out_batch_no}")
            else:
                logger.warning(f"未找到提现记录: withdraw_id={out_batch_no}")
        
        elif event_type == "TRANSFER.FAILED":
            # 转账失败
            batch_id = resource.get("batch_id")
            out_batch_no = resource.get("out_batch_no")
            fail_reason = resource.get("fail_reason", "未知错误")
            
            # 查找提现记录
            result = await db.execute(
                select(WithdrawRecord).where(
                    WithdrawRecord.withdraw_id == out_batch_no
                )
            )
            withdraw_record = result.scalar_one_or_none()
            
            if withdraw_record:
                withdraw_record.status = WithdrawStatus.FAILED.value
                withdraw_record.error_message = fail_reason
                # TODO: 解冻金额并退款
                await db.commit()
                logger.info(f"提现失败更新: withdraw_id={out_batch_no}, reason={fail_reason}")
            else:
                logger.warning(f"未找到提现记录: withdraw_id={out_batch_no}")
        
        # 返回成功响应
        return {"code": "SUCCESS", "message": "成功"}
        
    except Exception as e:
        logger.error(f"处理微信转账回调异常: {e}")
        return {"code": "FAIL", "message": str(e)}


@router.get("/withdraw/{withdraw_id}")
async def get_withdraw_status(
    withdraw_id: str,
    db: AsyncSession = Depends(get_db)
):
    """查询提现状态"""
    result = await db.execute(
        select(WithdrawRecord).where(
            WithdrawRecord.withdraw_id == withdraw_id
        )
    )
    record = result.scalar_one_or_none()
    
    if not record:
        raise HTTPException(status_code=404, detail="提现记录不存在")
    
    return ResponseModel(data={
        "withdraw_id": record.withdraw_id,
        "amount": record.amount,
        "status": record.status,
        "channel": record.channel,
        "created_at": record.created_at,
        "completed_at": record.completed_at,
        "error_message": record.error_message
    })
