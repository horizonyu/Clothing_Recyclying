"""
微信支付服务 - 商家转账到零钱
使用微信支付 API v3
"""
import os
import uuid
import requests
import json
import time
from typing import Optional, Dict
from loguru import logger
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend
import base64
from app.config import settings


class WeChatPayService:
    """微信支付服务类 - 商家转账到零钱"""
    
    def __init__(self):
        """初始化微信支付客户端"""
        if not all([
            settings.WECHAT_MCH_ID,
            settings.WECHAT_MCH_SERIAL_NO,
            settings.WECHAT_APIV3_KEY
        ]):
            logger.warning("微信支付配置不完整，提现功能将不可用")
            self.mch_id = None
            self.mch_serial_no = None
            self.api_v3_key = None
            self.private_key = None
            self.appid = settings.WECHAT_APPID
            return
        
        # 读取商户私钥
        private_key_path = settings.WECHAT_MCH_PRIVATE_KEY_PATH
        
        if not os.path.exists(private_key_path):
            logger.error(f"商户私钥文件不存在: {private_key_path}")
            self.mch_id = None
            return
        
        try:
            with open(private_key_path, 'r') as f:
                private_key_pem = f.read()
            
            # 解析私钥
            self.private_key = serialization.load_pem_private_key(
                private_key_pem.encode('utf-8'),
                password=None,
                backend=default_backend()
            )
            
            self.mch_id = settings.WECHAT_MCH_ID
            self.mch_serial_no = settings.WECHAT_MCH_SERIAL_NO
            self.api_v3_key = settings.WECHAT_APIV3_KEY
            self.appid = settings.WECHAT_APPID
            
            logger.info("微信支付客户端初始化成功")
        except Exception as e:
            logger.error(f"微信支付客户端初始化失败: {e}")
            self.mch_id = None
            self.private_key = None
    
    def is_available(self) -> bool:
        """检查服务是否可用"""
        return self.mch_id is not None and self.private_key is not None
    
    def _sign(self, method: str, url: str, timestamp: str, nonce: str, body: str = "") -> str:
        """生成请求签名"""
        message = f"{method}\n{url}\n{timestamp}\n{nonce}\n{body}\n"
        
        signature = self.private_key.sign(
            message.encode('utf-8'),
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        
        return base64.b64encode(signature).decode('utf-8')
    
    def _get_authorization(self, method: str, url: str, body: str = "") -> str:
        """获取请求头Authorization"""
        timestamp = str(int(time.time()))
        nonce = uuid.uuid4().hex
        
        signature = self._sign(method, url, timestamp, nonce, body)
        
        authorization = (
            f'WECHATPAY2-SHA256-RSA2048 '
            f'mchid="{self.mch_id}",'
            f'nonce_str="{nonce}",'
            f'signature="{signature}",'
            f'timestamp="{timestamp}",'
            f'serial_no="{self.mch_serial_no}"'
        )
        
        return authorization
    
    async def transfer_to_balance(
        self,
        openid: str,
        amount: float,
        description: str = "回收收益提现",
        withdraw_id: str = None
    ) -> Dict:
        """
        转账到微信零钱 - 使用商家转账到零钱 API v3
        
        Args:
            openid: 用户微信OpenID
            amount: 转账金额（元）
            description: 转账说明
            withdraw_id: 提现单号（用于关联）
        
        Returns:
            dict: {
                "batch_id": "微信批次单号",
                "out_batch_no": "商户批次单号",
                "status": "success"
            }
        """
        if not self.is_available():
            raise Exception("微信支付服务未配置或不可用")
        
        # 金额转换为分（微信支付使用分为单位）
        amount_cents = int(amount * 100)
        
        if amount_cents < 100:  # 最低1元
            raise ValueError("提现金额不能少于1元")
        
        # 生成批次单号（需要唯一，最多32个字符）
        if not withdraw_id:
            withdraw_id = f"WD{int(time.time())}{uuid.uuid4().hex[:12].upper()}"
        else:
            # 确保不超过32个字符
            withdraw_id = withdraw_id[:32]
        
        # 生成明细单号
        detail_no = f"{withdraw_id}D001"[:32]
        
        # 构建转账请求数据
        data = {
            "appid": self.appid,
            "out_batch_no": withdraw_id,  # 商户批次单号
            "batch_name": description[:32] if len(description) <= 32 else description[:29] + "...",  # 批次名称，最多32字符
            "batch_remark": description[:56] if len(description) <= 56 else description[:53] + "...",  # 批次备注，最多56字符
            "total_amount": amount_cents,
            "total_num": 1,
            "transfer_detail_list": [
                {
                    "out_detail_no": detail_no,  # 商户明细单号
                    "transfer_amount": amount_cents,
                    "transfer_remark": description[:56] if len(description) <= 56 else description[:53] + "...",  # 转账备注
                    "openid": openid
                }
            ]
        }
        
        try:
            logger.info(f"发起微信转账请求: openid={openid}, amount={amount}, withdraw_id={withdraw_id}")
            
            # API v3 转账接口URL
            url = "https://api.mch.weixin.qq.com/v3/transfer/batches"
            
            # 请求体
            body_str = json.dumps(data, ensure_ascii=False)
            
            # 获取Authorization
            authorization = self._get_authorization("POST", url, body_str)
            
            # 发送请求
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": authorization,
                "Wechatpay-Serial": self.mch_serial_no
            }
            
            response = requests.post(
                url,
                headers=headers,
                data=body_str.encode('utf-8'),
                timeout=30
            )
            
            logger.info(f"微信转账响应状态码: {response.status_code}")
            logger.info(f"微信转账响应内容: {response.text}")
            
            # 解析响应
            if response.status_code == 200:
                result = response.json()
                return {
                    "batch_id": result.get('batch_id'),
                    "out_batch_no": result.get('out_batch_no'),
                    "status": "success",
                    "message": "转账申请已提交"
                }
            else:
                error_data = response.json() if response.text else {}
                error_msg = error_data.get('message', f'HTTP {response.status_code}')
                error_code = error_data.get('code', 'UNKNOWN_ERROR')
                raise Exception(f"转账失败 [{error_code}]: {error_msg}")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"微信转账网络异常: {e}")
            raise Exception(f"转账请求失败: {str(e)}")
        except Exception as e:
            logger.error(f"微信转账异常: {e}")
            raise Exception(f"转账失败: {str(e)}")
    
    async def query_transfer_status(
        self,
        batch_id: str,
        detail_id: str = None
    ) -> Dict:
        """
        查询转账状态
        
        Args:
            batch_id: 微信批次单号
            detail_id: 微信明细单号（可选）
        
        Returns:
            dict: 转账状态信息
        """
        if not self.is_available():
            raise Exception("微信支付服务未配置或不可用")
        
        try:
            if detail_id:
                # 查询明细单
                url = f"https://api.mch.weixin.qq.com/v3/transfer/batches/out-batch-no/{batch_id}/details/out-detail-no/{detail_id}"
            else:
                # 查询批次单
                url = f"https://api.mch.weixin.qq.com/v3/transfer/batches/out-batch-no/{batch_id}"
            
            authorization = self._get_authorization("GET", url, "")
            
            headers = {
                "Accept": "application/json",
                "Authorization": authorization,
                "Wechatpay-Serial": self.mch_serial_no
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            else:
                error_data = response.json() if response.text else {}
                error_msg = error_data.get('message', f'HTTP {response.status_code}')
                raise Exception(f"查询失败: {error_msg}")
                
        except Exception as e:
            logger.error(f"查询转账状态失败: {e}")
            raise Exception(f"查询失败: {str(e)}")


# 全局服务实例
wechat_pay_service = WeChatPayService()
