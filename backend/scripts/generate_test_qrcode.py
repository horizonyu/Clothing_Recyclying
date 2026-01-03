"""
测试二维码生成脚本

用于模拟硬件生成的二维码，方便测试小程序扫码功能
"""
import json
import base64
import hmac
import hashlib
import time
from datetime import datetime


def generate_signature(data: dict, device_secret: str) -> str:
    """生成签名"""
    sign_str = f"{data['v']}.{data['d']}.{data['vid']}.{data['w']}.{data['p']}.{data['a']}.{data['t']}.{data['e']}"
    signature = hmac.new(
        device_secret.encode(),
        sign_str.encode(),
        hashlib.sha256
    ).hexdigest()
    return signature


def generate_voucher_id(device_id: str, sequence: int = 1) -> str:
    """生成凭证ID"""
    date_str = datetime.now().strftime("%Y%m%d")
    return f"V{date_str}{device_id}{sequence:03d}"


def generate_qrcode_data(
    device_id: str,
    device_secret: str,
    weight_gram: int,
    unit_price_fen: int = 30,
    expire_seconds: int = 3600,
    sequence: int = 1
) -> str:
    """
    生成二维码数据
    
    Args:
        device_id: 设备ID
        device_secret: 设备密钥
        weight_gram: 重量(克)
        unit_price_fen: 单价(分/kg)
        expire_seconds: 过期时间(秒)
        sequence: 当日序号
    
    Returns:
        Base64编码的二维码数据
    """
    now = int(time.time())
    
    # 计算金额(分)
    amount_fen = int(weight_gram * unit_price_fen / 1000)
    
    # 构建数据
    data = {
        "v": 1,  # 版本号
        "d": device_id,  # 设备ID
        "vid": generate_voucher_id(device_id, sequence),  # 凭证ID
        "w": weight_gram,  # 重量(克)
        "p": unit_price_fen,  # 单价(分/kg)
        "a": amount_fen,  # 金额(分)
        "t": now,  # 生成时间
        "e": now + expire_seconds  # 过期时间
    }
    
    # 生成签名
    data["s"] = generate_signature(data, device_secret)
    
    # Base64编码
    json_str = json.dumps(data, separators=(',', ':'))
    qrcode_data = base64.b64encode(json_str.encode()).decode()
    
    return qrcode_data, data


def main():
    """生成测试二维码"""
    print("=" * 60)
    print("测试二维码生成器")
    print("=" * 60)
    
    # 测试设备信息 (需要与数据库中的设备信息匹配)
    # 请在初始化数据库后，从控制台输出中获取设备密钥
    device_id = "DEV001"
    device_secret = input("请输入设备密钥 (device_secret): ").strip()
    
    if not device_secret:
        print("使用默认测试密钥...")
        device_secret = "test_secret_key_12345"
    
    # 生成二维码
    weight = int(input("请输入重量(克，默认3500): ").strip() or "3500")
    
    qrcode_data, raw_data = generate_qrcode_data(
        device_id=device_id,
        device_secret=device_secret,
        weight_gram=weight,
        unit_price_fen=30,  # 0.30元/kg
        expire_seconds=3600  # 10分钟
    )
    
    print("\n" + "=" * 60)
    print("生成结果:")
    print("=" * 60)
    print(f"\n原始数据:")
    print(json.dumps(raw_data, indent=2, ensure_ascii=False))
    
    print(f"\n重量: {weight}克 = {weight/1000}kg")
    print(f"单价: {raw_data['p']}分/kg = {raw_data['p']/100}元/kg")
    print(f"金额: {raw_data['a']}分 = {raw_data['a']/100}元")
    
    print(f"\n📱 二维码数据 (Base64):")
    print("-" * 60)
    print(qrcode_data)
    print("-" * 60)
    
    print(f"\n⏰ 有效期至: {datetime.fromtimestamp(raw_data['e']).strftime('%Y-%m-%d %H:%M:%S')}")
    
    print("\n💡 使用方法:")
    print("1. 复制上面的Base64字符串")
    print("2. 使用在线二维码生成器生成二维码图片")
    print("3. 或直接在小程序中使用扫码功能测试")
    print("\n推荐二维码生成器: https://cli.im/text")


if __name__ == "__main__":
    main()

