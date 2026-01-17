"""
应用配置管理
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """应用配置"""
    
    # 应用配置
    APP_NAME: str = "智能旧衣回收箱"
    APP_ENV: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "your-secret-key"
    
    # 数据库配置
    DATABASE_URL: str = "mysql+aiomysql://root:password@localhost:3306/clothing_recycle"
    
    # Redis配置
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # 微信小程序配置
    WECHAT_APPID: str = ""
    WECHAT_SECRET: str = ""
    
    # 微信支付配置
    WECHAT_MCH_ID: Optional[str] = ""  # 商户号
    WECHAT_MCH_SERIAL_NO: Optional[str] = ""  # 商户证书序列号
    WECHAT_MCH_PRIVATE_KEY_PATH: Optional[str] = ""  # 商户私钥文件路径
    WECHAT_MCH_CERT_PATH: Optional[str] = ""  # 商户证书文件路径
    WECHAT_APIV3_KEY: Optional[str] = ""  # APIv3密钥
    
    # JWT配置
    JWT_SECRET_KEY: str = "your-jwt-secret"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 10080  # 7天
    
    # 回收配置
    DEFAULT_UNIT_PRICE: float = 0.30  # 元/kg
    CARBON_COEFFICIENT: float = 2.5   # 1kg衣物 = 2.5kg CO2
    POINTS_COEFFICIENT: int = 10      # 1kg CO2 = 10积分
    QRCODE_EXPIRE_SECONDS: int = 600  # 二维码有效期10分钟
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# 全局配置实例
settings = Settings()

