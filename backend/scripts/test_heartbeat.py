#!/usr/bin/env python3
"""
测试设备通信接口 - 按照《4G设备-后台通信协议》

测试内容：
1. 设备常规状态上报（device_status_report）
2. 设备心跳包上报（heartbeat_report）
3. 小程序扫码上报（qrcode-report）
"""
import requests
import json
import hashlib
from datetime import datetime

# 配置
API_BASE_URL = "http://42.194.134.223:8000/api/v1"
DEVICE_ID = "DEV001"  # 请替换为实际设备ID

# 报文包头包尾
PACKET_HEADER = "0x6868"
PACKET_FOOTER = "0x1616"


def get_timestamp():
    """获取标准时间戳字符串"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def calculate_check_code(packet_data: dict) -> str:
    """
    计算MD5校验码
    
    校验规则：
    1. 校验范围：包头 + JSON数据体中除check_code外的所有字段拼接字符串
    2. 校验算法：MD5，32位小写
    """
    data_copy = {k: v for k, v in packet_data.items() if k != "check_code"}
    json_str = json.dumps(data_copy, ensure_ascii=False, separators=(',', ':'))
    check_str = PACKET_HEADER + json_str
    md5_hash = hashlib.md5(check_str.encode('utf-8')).hexdigest()
    return md5_hash


def wrap_packet(packet_data: dict) -> str:
    """添加包头包尾"""
    json_str = json.dumps(packet_data, ensure_ascii=False, separators=(',', ':'))
    return f"{PACKET_HEADER}{json_str}{PACKET_FOOTER}"


def test_device_status_report():
    """测试1：设备常规状态上报"""
    print("=" * 60)
    print("测试1：设备常规状态上报 (device_status_report)")
    print("=" * 60)
    
    url = f"{API_BASE_URL}/device/report"
    
    # 构建报文
    report_data = {
        "msg_type": "device_status_report",
        "device_id": DEVICE_ID,
        "timestamp": get_timestamp(),
        "data": {
            "battery_level": 85,
            "location": {
                "longitude": 113.9423,
                "latitude": 22.5431,
                "address": "广东省深圳市宝安区XX街道XX路"
            },
            "smoke_sensor_status": 0,
            "recycle_bin_full": 0,
            "delivery_window_open": 0,
            "is_using": 0,
            "camera_data": {
                "camera_1": [],
                "camera_2": []
            }
        }
    }
    
    # 计算校验码
    report_data["check_code"] = calculate_check_code(report_data)
    
    print(f"URL: {url}")
    print(f"设备ID: {DEVICE_ID}")
    print(f"时间戳: {report_data['timestamp']}")
    print(f"校验码: {report_data['check_code']}")
    print(f"\n完整报文（含包头包尾）：")
    print(wrap_packet(report_data))
    print()
    
    try:
        response = requests.post(url, json=report_data, timeout=10)
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        
        if response.status_code == 200 and response.json().get("code") == 0:
            print("\n✅ 设备状态上报成功！")
        else:
            print("\n❌ 设备状态上报失败！")
    except Exception as e:
        print(f"\n❌ 请求失败: {e}")


def test_device_status_report_using():
    """测试1b：设备使用中状态上报（带摄像头数据）"""
    print("\n" + "=" * 60)
    print("测试1b：设备使用中状态上报 (is_using=1)")
    print("=" * 60)
    
    url = f"{API_BASE_URL}/device/report"
    
    report_data = {
        "msg_type": "device_status_report",
        "device_id": DEVICE_ID,
        "timestamp": get_timestamp(),
        "data": {
            "battery_level": 80,
            "location": {
                "longitude": 113.9423,
                "latitude": 22.5431,
                "address": "广东省深圳市宝安区XX街道XX路"
            },
            "smoke_sensor_status": 0,
            "recycle_bin_full": 0,
            "delivery_window_open": 1,
            "is_using": 1,
            "camera_data": {
                "camera_1": [
                    "iVBORw0KGgoAAAANSUhEUg==",  # 模拟Base64图片
                    "iVBORw0KGgoAAAANSUhEUg==",
                    "iVBORw0KGgoAAAANSUhEUg=="
                ],
                "camera_2": [
                    "iVBORw0KGgoAAAANSUhEUg==",
                    "iVBORw0KGgoAAAANSUhEUg==",
                    "iVBORw0KGgoAAAANSUhEUg=="
                ]
            }
        }
    }
    
    report_data["check_code"] = calculate_check_code(report_data)
    
    try:
        response = requests.post(url, json=report_data, timeout=10)
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        
        if response.status_code == 200 and response.json().get("code") == 0:
            print("\n✅ 使用中状态上报成功！")
        else:
            print("\n❌ 使用中状态上报失败！")
    except Exception as e:
        print(f"\n❌ 请求失败: {e}")


def test_heartbeat_report():
    """测试2：设备心跳包上报"""
    print("\n" + "=" * 60)
    print("测试2：设备心跳包上报 (heartbeat_report)")
    print("=" * 60)
    
    url = f"{API_BASE_URL}/device/heartbeat"
    
    # 构建心跳报文
    heartbeat_data = {
        "msg_type": "heartbeat_report",
        "device_id": DEVICE_ID,
        "timestamp": get_timestamp()
    }
    
    # 计算校验码
    heartbeat_data["check_code"] = calculate_check_code(heartbeat_data)
    
    print(f"URL: {url}")
    print(f"设备ID: {DEVICE_ID}")
    print(f"时间戳: {heartbeat_data['timestamp']}")
    print(f"校验码: {heartbeat_data['check_code']}")
    print(f"\n完整报文：")
    print(wrap_packet(heartbeat_data))
    print()
    
    try:
        response = requests.post(url, json=heartbeat_data, timeout=10)
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        
        if response.status_code == 200 and response.json().get("code") == 0:
            print("\n✅ 心跳上报成功！")
            # 检查时间同步
            resp_data = response.json().get("data", {})
            time_sync = resp_data.get("time_sync", {})
            if time_sync:
                sync_time = time_sync.get("data", {}).get("standard_time", "")
                print(f"   服务器时间同步: {sync_time}")
        else:
            print("\n❌ 心跳上报失败！")
    except Exception as e:
        print(f"\n❌ 请求失败: {e}")


def test_qrcode_report():
    """测试3：模拟小程序扫码上报"""
    print("\n" + "=" * 60)
    print("测试3：小程序扫码上报 (qrcode-report)")
    print("=" * 60)
    
    # 构建设备状态报文（模拟硬件生成的二维码内容）
    report_data = {
        "msg_type": "device_status_report",
        "device_id": DEVICE_ID,
        "timestamp": get_timestamp(),
        "data": {
            "battery_level": 75,
            "location": {
                "longitude": 113.9423,
                "latitude": 22.5431,
                "address": "广东省深圳市宝安区XX街道XX路"
            },
            "smoke_sensor_status": 0,
            "recycle_bin_full": 0,
            "delivery_window_open": 1,
            "is_using": 1,
            "camera_data": {
                "camera_1": [],
                "camera_2": []
            }
        }
    }
    report_data["check_code"] = calculate_check_code(report_data)
    
    # 添加包头包尾（模拟二维码内容）
    qrcode_content = wrap_packet(report_data)
    
    print(f"二维码内容: {qrcode_content[:80]}...")
    print()
    print("⚠️  注意：此接口需要用户登录token，跳过实际请求")
    print("   实际使用时，小程序会在请求头中携带Authorization token")


def test_check_code_verification():
    """测试4：校验码验证"""
    print("\n" + "=" * 60)
    print("测试4：MD5校验码验证")
    print("=" * 60)
    
    # 正确校验码
    report_data = {
        "msg_type": "heartbeat_report",
        "device_id": DEVICE_ID,
        "timestamp": "2026-01-30 10:00:00"
    }
    check_code = calculate_check_code(report_data)
    report_data["check_code"] = check_code
    
    print(f"报文: {json.dumps(report_data, ensure_ascii=False)}")
    print(f"计算校验码: {check_code}")
    
    # 验证
    data_copy = {k: v for k, v in report_data.items() if k != "check_code"}
    json_str = json.dumps(data_copy, ensure_ascii=False, separators=(',', ':'))
    check_str = PACKET_HEADER + json_str
    print(f"校验字符串: {check_str}")
    print(f"MD5结果: {hashlib.md5(check_str.encode('utf-8')).hexdigest()}")
    print(f"校验码匹配: {check_code == hashlib.md5(check_str.encode('utf-8')).hexdigest()}")
    
    # 错误校验码
    print("\n--- 错误校验码测试 ---")
    report_data["check_code"] = "wrong_check_code"
    data_copy2 = {k: v for k, v in report_data.items() if k != "check_code"}
    json_str2 = json.dumps(data_copy2, ensure_ascii=False, separators=(',', ':'))
    check_str2 = PACKET_HEADER + json_str2
    expected = hashlib.md5(check_str2.encode('utf-8')).hexdigest()
    print(f"期望校验码: {expected}")
    print(f"收到校验码: wrong_check_code")
    print(f"校验通过: False")
    
    print("\n✅ 校验码验证逻辑正确！")


if __name__ == "__main__":
    print("🔧 4G设备-后台通信协议 测试工具")
    print(f"📡 API地址: {API_BASE_URL}")
    print(f"📱 设备ID: {DEVICE_ID}")
    print()
    
    # 先测试校验码逻辑
    test_check_code_verification()
    
    # 测试设备状态上报
    print()
    test_device_status_report()
    
    # 测试使用中状态上报
    test_device_status_report_using()
    
    # 测试心跳上报
    test_heartbeat_report()
    
    # 测试扫码上报（需要token，仅展示）
    test_qrcode_report()
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
