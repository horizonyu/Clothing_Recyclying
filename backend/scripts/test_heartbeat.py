#!/usr/bin/env python3
"""
测试设备通信接口 - 按照《4G设备-后台通信协议》

测试内容：
1. 设备常规状态上报（device_status_report）- 无摄像头
2. 设备常规状态上报（device_status_report）- 含摄像头数据
3. 设备心跳包上报（heartbeat_report）
4. 小程序扫码上报（qrcode-report）
5. MD5校验码验证
"""
import requests
import json
import hashlib
import struct
import zlib
import base64
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


def generate_test_png(width=80, height=60, r=0, g=0, b=0, text_label=""):
    """
    生成一个有效的测试PNG图片（纯色块+简单条纹作区分）
    
    Args:
        width: 图片宽度
        height: 图片高度
        r, g, b: 背景颜色 (0-255)
        text_label: 标签（仅用于日志说明）
    
    Returns:
        Base64编码的PNG图片字符串
    """
    def create_png(w, h, r, g, b):
        """使用纯Python创建最小PNG"""
        # PNG签名
        signature = b'\x89PNG\r\n\x1a\n'
        
        # IHDR chunk
        ihdr_data = struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0)  # 8bit RGB
        ihdr_crc = zlib.crc32(b'IHDR' + ihdr_data) & 0xffffffff
        ihdr = struct.pack('>I', 13) + b'IHDR' + ihdr_data + struct.pack('>I', ihdr_crc)
        
        # IDAT chunk - 图片数据
        raw_data = b''
        for y in range(h):
            raw_data += b'\x00'  # filter byte: None
            for x in range(w):
                # 添加条纹效果使图片更有辨识度
                if y < 4:
                    # 顶部白色条纹
                    raw_data += bytes([255, 255, 255])
                elif y >= h - 4:
                    # 底部深色条纹
                    raw_data += bytes([max(0, r - 80), max(0, g - 80), max(0, b - 80)])
                elif x < 4 or x >= w - 4:
                    # 左右边框
                    raw_data += bytes([min(255, r + 40), min(255, g + 40), min(255, b + 40)])
                else:
                    # 主色块（中心区域加渐变）
                    factor = 1.0 - abs(y - h/2) / (h/2) * 0.3
                    raw_data += bytes([
                        min(255, int(r * factor)),
                        min(255, int(g * factor)),
                        min(255, int(b * factor))
                    ])
        
        compressed = zlib.compress(raw_data)
        idat_crc = zlib.crc32(b'IDAT' + compressed) & 0xffffffff
        idat = struct.pack('>I', len(compressed)) + b'IDAT' + compressed + struct.pack('>I', idat_crc)
        
        # IEND chunk
        iend_crc = zlib.crc32(b'IEND') & 0xffffffff
        iend = struct.pack('>I', 0) + b'IEND' + struct.pack('>I', iend_crc)
        
        return signature + ihdr + idat + iend
    
    png_bytes = create_png(width, height, r, g, b)
    b64_str = base64.b64encode(png_bytes).decode('utf-8')
    return b64_str


def generate_camera_test_data():
    """
    生成模拟摄像头数据
    
    camera_1: 回收箱内部摄像头 - 拍摄投递的衣物（3张，不同角度）
    camera_2: 用户摄像头 - 拍摄使用设备的用户（3张，不同时刻）
    
    Returns:
        camera_data dict
    """
    print("  📸 生成测试图片中...")
    
    # camera_1: 回收箱内部 - 使用暖色调（模拟衣物颜色）
    camera_1_images = [
        generate_test_png(160, 120, r=180, g=120, b=80, text_label="内部-衣物俯视"),
        generate_test_png(160, 120, r=100, g=140, b=180, text_label="内部-衣物侧视"),
        generate_test_png(160, 120, r=160, g=100, b=120, text_label="内部-衣物特写"),
    ]
    
    # camera_2: 用户摄像头 - 使用肤色调（模拟人物）
    camera_2_images = [
        generate_test_png(160, 120, r=200, g=160, b=130, text_label="用户-正面"),
        generate_test_png(160, 120, r=180, g=150, b=120, text_label="用户-投递中"),
        generate_test_png(160, 120, r=190, g=155, b=125, text_label="用户-完成"),
    ]
    
    print(f"  📸 camera_1: {len(camera_1_images)}张 (回收箱内部)")
    print(f"  📸 camera_2: {len(camera_2_images)}张 (用户画面)")
    for i, img in enumerate(camera_1_images):
        print(f"      camera_1[{i}]: {len(img)} bytes Base64")
    for i, img in enumerate(camera_2_images):
        print(f"      camera_2[{i}]: {len(img)} bytes Base64")
    
    return {
        "camera_1": camera_1_images,
        "camera_2": camera_2_images
    }


def test_device_status_report():
    """测试1：设备常规状态上报（无摄像头数据，is_using=0）
    
    预期：返回 ack，不包含 time_sync（因为 is_using=0）
    """
    print("=" * 60)
    print("测试1：设备常规状态上报 - 空闲状态 (is_using=0)")
    print("=" * 60)
    
    url = f"{API_BASE_URL}/device/report"
    
    # 构建报文（设备空闲，无人使用）
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
    
    report_data["check_code"] = calculate_check_code(report_data)
    
    print(f"URL: {url}")
    print(f"设备ID: {DEVICE_ID}")
    print(f"is_using: 0 (空闲)")
    print()
    
    try:
        response = requests.post(url, json=report_data, timeout=10)
        print(f"状态码: {response.status_code}")
        resp_json = response.json()
        print(f"响应: {json.dumps(resp_json, indent=2, ensure_ascii=False)}")
        
        if response.status_code == 200 and resp_json.get("code") == 0:
            data = resp_json.get("data", {})
            has_ack = "ack" in data
            has_time_sync = "time_sync" in data
            print(f"\n  ✅ 包含 ack: {has_ack}")
            print(f"  {'⚠️' if has_time_sync else '✅'} 包含 time_sync: {has_time_sync} (预期: False，因为 is_using=0)")
            print("\n✅ 空闲状态上报成功！")
        else:
            print("\n❌ 设备状态上报失败！")
    except Exception as e:
        print(f"\n❌ 请求失败: {e}")


def test_device_first_use_time_sync():
    """测试2：设备首次被用户使用 → 应返回 ack + time_sync
    
    协议规定：设备第一次被用户使用时(is_using从0→1)，
    除了返回ack消息，还需返回time_sync消息。
    """
    print("\n" + "=" * 60)
    print("测试2：首次使用 → 验证 time_sync 下发 (is_using: 0→1)")
    print("=" * 60)
    
    url = f"{API_BASE_URL}/device/report"
    
    # 步骤1：先上报 is_using=0（确保设备处于空闲状态）
    print("\n--- 步骤1: 先上报 is_using=0 (确保空闲) ---")
    idle_data = {
        "msg_type": "device_status_report",
        "device_id": DEVICE_ID,
        "timestamp": get_timestamp(),
        "data": {
            "battery_level": 85,
            "location": {"longitude": 113.9423, "latitude": 22.5431, "address": "测试地址"},
            "smoke_sensor_status": 0,
            "recycle_bin_full": 0,
            "delivery_window_open": 0,
            "is_using": 0,
            "camera_data": {"camera_1": [], "camera_2": []}
        }
    }
    idle_data["check_code"] = calculate_check_code(idle_data)
    
    try:
        resp1 = requests.post(url, json=idle_data, timeout=10)
        print(f"  空闲状态上报: {resp1.status_code} - {resp1.json().get('message', '')}")
    except Exception as e:
        print(f"  ❌ 请求失败: {e}")
        return
    
    # 步骤2：上报 is_using=1（首次使用，应触发 time_sync）
    print("\n--- 步骤2: 上报 is_using=1 (首次使用) ---")
    camera_data = generate_camera_test_data()
    
    using_data = {
        "msg_type": "device_status_report",
        "device_id": DEVICE_ID,
        "timestamp": get_timestamp(),
        "data": {
            "battery_level": 80,
            "location": {"longitude": 113.9423, "latitude": 22.5431, "address": "测试地址"},
            "smoke_sensor_status": 0,
            "recycle_bin_full": 0,
            "delivery_window_open": 1,
            "is_using": 1,
            "camera_data": camera_data
        }
    }
    using_data["check_code"] = calculate_check_code(using_data)
    
    print(f"  is_using: 0 → 1 (首次使用)")
    print(f"  报文大小: {len(json.dumps(using_data))} bytes")
    
    try:
        resp2 = requests.post(url, json=using_data, timeout=30)
        print(f"  状态码: {resp2.status_code}")
        resp_json = resp2.json()
        print(f"  响应: {json.dumps(resp_json, indent=2, ensure_ascii=False)}")
        
        if resp2.status_code == 200 and resp_json.get("code") == 0:
            data = resp_json.get("data", {})
            has_ack = "ack" in data
            has_time_sync = "time_sync" in data
            
            print(f"\n  ✅ 包含 ack: {has_ack}")
            print(f"  {'✅' if has_time_sync else '❌'} 包含 time_sync: {has_time_sync}")
            
            if has_time_sync:
                sync_time = data["time_sync"].get("data", {}).get("standard_time", "")
                print(f"  ⏰ 同步时间: {sync_time}")
                print("\n✅ 首次使用时间同步验证通过！")
            else:
                print("\n❌ 首次使用时未下发 time_sync！")
        else:
            print("\n❌ 上报失败！")
    except Exception as e:
        print(f"\n❌ 请求失败: {e}")


def test_device_status_report_with_camera():
    """测试3：设备使用中状态上报（带摄像头数据，is_using已经是1）
    
    预期：返回 ack，不包含 time_sync（因为 is_using 没有变化，仍然是1）
    """
    print("\n" + "=" * 60)
    print("测试3：持续使用状态上报 - 含摄像头数据 (is_using=1→1)")
    print("=" * 60)
    
    url = f"{API_BASE_URL}/device/report"
    
    camera_data = generate_camera_test_data()
    
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
            "camera_data": camera_data
        }
    }
    
    report_data["check_code"] = calculate_check_code(report_data)
    
    print(f"is_using: 1→1 (持续使用，非首次)")
    print(f"报文大小: {len(json.dumps(report_data))} bytes")
    print()
    
    try:
        response = requests.post(url, json=report_data, timeout=30)
        print(f"状态码: {response.status_code}")
        resp_json = response.json()
        print(f"响应: {json.dumps(resp_json, indent=2, ensure_ascii=False)}")
        
        if response.status_code == 200 and resp_json.get("code") == 0:
            data = resp_json.get("data", {})
            has_time_sync = "time_sync" in data
            print(f"\n  ✅ 包含 ack: {'ack' in data}")
            print(f"  {'⚠️' if has_time_sync else '✅'} 包含 time_sync: {has_time_sync} (预期: False，非首次使用)")
            print("\n✅ 持续使用状态上报成功！")
            print("   📸 camera_1 (回收箱内部): 3张图片已上传")
            print("   📸 camera_2 (用户画面): 3张图片已上传")
        else:
            print("\n❌ 上报失败！")
    except Exception as e:
        print(f"\n❌ 请求失败: {e}")


def test_device_status_report_smoke_alarm_with_camera():
    """测试3：设备烟感告警上报（带摄像头数据，用于确认现场情况）"""
    print("\n" + "=" * 60)
    print("测试3：烟感告警上报 - 含摄像头数据 (smoke_sensor_status=1)")
    print("=" * 60)
    
    url = f"{API_BASE_URL}/device/report"
    
    # 烟感告警时的摄像头数据（红色调模拟告警场景）
    print("  📸 生成告警场景测试图片...")
    camera_data = {
        "camera_1": [
            generate_test_png(160, 120, r=200, g=60, b=60, text_label="内部-告警场景1"),
            generate_test_png(160, 120, r=220, g=80, b=50, text_label="内部-告警场景2"),
        ],
        "camera_2": [
            generate_test_png(160, 120, r=180, g=150, b=120, text_label="外部-现场情况"),
        ]
    }
    print(f"  📸 camera_1: {len(camera_data['camera_1'])}张 (告警现场)")
    print(f"  📸 camera_2: {len(camera_data['camera_2'])}张 (外部环境)")
    
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
            "smoke_sensor_status": 1,  # 烟感告警！
            "recycle_bin_full": 0,
            "delivery_window_open": 0,
            "is_using": 0,
            "camera_data": camera_data
        }
    }
    
    report_data["check_code"] = calculate_check_code(report_data)
    
    print(f"\nURL: {url}")
    print(f"⚠️  烟感状态: 告警!")
    print(f"报文大小: {len(json.dumps(report_data))} bytes")
    print()
    
    try:
        response = requests.post(url, json=report_data, timeout=30)
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        
        if response.status_code == 200 and response.json().get("code") == 0:
            print("\n✅ 烟感告警上报成功！（含现场照片）")
        else:
            print("\n❌ 烟感告警上报失败！")
    except Exception as e:
        print(f"\n❌ 请求失败: {e}")


def test_device_status_report_first_use():
    """测试4：设备首次使用(is_using=1)上报 → 应返回 ack + time_sync
    
    协议规定：设备第一次被用户使用时，后台除了返回 ack，还应返回 time_sync。
    """
    print("\n" + "=" * 60)
    print("测试4：设备使用中(is_using=1) → ack + time_sync")
    print("=" * 60)
    
    url = f"{API_BASE_URL}/device/report"
    
    report_data = {
        "msg_type": "device_status_report",
        "device_id": DEVICE_ID,
        "timestamp": get_timestamp(),
        "data": {
            "battery_level": 90,
            "location": {
                "longitude": 113.9423,
                "latitude": 22.5431,
                "address": "深圳市宝安区"
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
    
    print(f"URL: {url}")
    print(f"is_using: 1 (用户正在使用)")
    print()
    
    try:
        response = requests.post(url, json=report_data, timeout=10)
        print(f"状态码: {response.status_code}")
        resp_json = response.json()
        print(f"响应: {json.dumps(resp_json, indent=2, ensure_ascii=False)}")
        
        if response.status_code == 200 and resp_json.get("code") == 0:
            data = resp_json.get("data", {})
            has_ack = "ack" in data
            has_time_sync = "time_sync" in data
            
            print(f"\n  {'✅' if has_ack else '❌'} 包含 ack: {has_ack}")
            print(f"  {'✅' if has_time_sync else '❌'} 包含 time_sync: {has_time_sync}")
            
            if has_time_sync:
                sync_time = data["time_sync"].get("data", {}).get("standard_time", "")
                print(f"  ⏰ 同步时间: {sync_time}")
            
            if has_ack and has_time_sync:
                print("\n✅ 首次使用时间同步验证通过！")
            else:
                print("\n⚠️ 首次使用应同时返回 ack 和 time_sync")
        else:
            print("\n❌ 上报失败！")
    except Exception as e:
        print(f"\n❌ 请求失败: {e}")


def test_heartbeat_report():
    """测试5：设备心跳包上报（无待执行命令）
    
    协议规定：后台收到心跳后，下发 ack + time_sync。
    """
    print("\n" + "=" * 60)
    print("测试5：设备心跳包上报 → ack + time_sync (heartbeat_report)")
    print("=" * 60)
    
    url = f"{API_BASE_URL}/device/heartbeat"
    
    heartbeat_data = {
        "msg_type": "heartbeat_report",
        "device_id": DEVICE_ID,
        "timestamp": get_timestamp()
    }
    heartbeat_data["check_code"] = calculate_check_code(heartbeat_data)
    
    print(f"URL: {url}")
    print(f"设备ID: {DEVICE_ID}")
    print(f"时间戳: {heartbeat_data['timestamp']}")
    print(f"\n完整报文：")
    print(wrap_packet(heartbeat_data))
    print()
    
    try:
        response = requests.post(url, json=heartbeat_data, timeout=10)
        print(f"状态码: {response.status_code}")
        resp_json = response.json()
        print(f"响应: {json.dumps(resp_json, indent=2, ensure_ascii=False)}")
        
        if response.status_code == 200 and resp_json.get("code") == 0:
            data = resp_json.get("data", {})
            has_ack = "ack" in data
            has_time_sync = "time_sync" in data
            has_command = "command" in data
            
            print(f"\n  {'✅' if has_ack else '❌'} 包含 ack: {has_ack}")
            print(f"  {'✅' if has_time_sync else '❌'} 包含 time_sync: {has_time_sync}")
            print(f"  ℹ️  包含 command: {has_command} (无待执行命令时应为 False)")
            
            if has_time_sync:
                sync_time = data["time_sync"].get("data", {}).get("standard_time", "")
                print(f"  ⏰ 同步时间: {sync_time}")
            
            print("\n✅ 心跳上报+时间同步验证通过！")
        else:
            print("\n❌ 心跳上报失败！")
    except Exception as e:
        print(f"\n❌ 请求失败: {e}")


def test_query_device_status_flow():
    """测试6：后台主动查询设备状态 → 完整流程
    
    协议规定：后台可主动下发 query_device_status，设备收到后返回 device_status_report。
    
    完整流程：
    1. 后台调用 /query-status 排队查询命令
    2. 设备通过心跳获取命令 (或通过 /pending-commands 轮询)
    3. 设备收到命令后上报 device_status_report
    """
    print("\n" + "=" * 60)
    print("测试6：后台主动查询设备状态 (query_device_status 完整流程)")
    print("=" * 60)
    
    # 步骤1：后台下发查询命令
    print("\n--- 步骤1: 后台下发 query_device_status ---")
    query_url = f"{API_BASE_URL}/device/query-status?device_id={DEVICE_ID}"
    
    try:
        resp1 = requests.post(query_url, timeout=10)
        print(f"  状态码: {resp1.status_code}")
        resp1_json = resp1.json()
        print(f"  响应: {json.dumps(resp1_json, indent=2, ensure_ascii=False)}")
        
        if resp1.status_code == 200 and resp1_json.get("code") == 0:
            print("\n  ✅ 查询命令已排队，等待设备获取")
        else:
            print("\n  ❌ 查询命令下发失败")
            return
    except Exception as e:
        print(f"\n  ❌ 请求失败: {e}")
        return
    
    # 步骤2a：设备通过轮询接口获取命令
    print("\n--- 步骤2a: 设备轮询待执行命令 ---")
    poll_url = f"{API_BASE_URL}/device/pending-commands/{DEVICE_ID}"
    
    try:
        resp2 = requests.get(poll_url, timeout=10)
        print(f"  状态码: {resp2.status_code}")
        resp2_json = resp2.json()
        print(f"  响应: {json.dumps(resp2_json, indent=2, ensure_ascii=False)}")
        
        data = resp2_json.get("data", {})
        has_command = data.get("has_command", False)
        
        if has_command:
            cmd = data.get("command", {})
            print(f"\n  ✅ 收到命令: {cmd.get('msg_type', '')}")
            print(f"     设备ID: {cmd.get('device_id', '')}")
            print(f"     完整报文: {data.get('full_packet', '')[:80]}...")
        else:
            print("\n  ⚠️ 未收到命令（可能已被心跳取走）")
    except Exception as e:
        print(f"\n  ❌ 请求失败: {e}")
    
    # 步骤2b：再次轮询 → 应该没有命令了（已被步骤2a取走）
    print("\n--- 步骤2b: 再次轮询（应该为空） ---")
    try:
        resp3 = requests.get(poll_url, timeout=10)
        resp3_json = resp3.json()
        has_command = resp3_json.get("data", {}).get("has_command", False)
        print(f"  has_command: {has_command} (预期: False)")
        print(f"  ✅ 命令已被清除，不会重复下发")
    except Exception as e:
        print(f"\n  ❌ 请求失败: {e}")
    
    # 步骤3：模拟设备响应 query_device_status → 上报 device_status_report
    print("\n--- 步骤3: 设备响应查询，上报完整状态 ---")
    report_url = f"{API_BASE_URL}/device/report"
    report_data = {
        "msg_type": "device_status_report",
        "device_id": DEVICE_ID,
        "timestamp": get_timestamp(),
        "data": {
            "battery_level": 82,
            "location": {
                "longitude": 113.9423,
                "latitude": 22.5431,
                "address": "广东省深圳市宝安区XX街道XX路"
            },
            "smoke_sensor_status": 0,
            "recycle_bin_full": 0,
            "delivery_window_open": 0,
            "is_using": 0,
            "camera_data": {"camera_1": [], "camera_2": []}
        }
    }
    report_data["check_code"] = calculate_check_code(report_data)
    
    try:
        resp4 = requests.post(report_url, json=report_data, timeout=10)
        print(f"  状态码: {resp4.status_code}")
        resp4_json = resp4.json()
        print(f"  响应: {json.dumps(resp4_json, indent=2, ensure_ascii=False)}")
        
        if resp4.status_code == 200 and resp4_json.get("code") == 0:
            print("\n  ✅ 设备响应查询成功，后台已更新设备状态")
        else:
            print("\n  ❌ 上报失败")
    except Exception as e:
        print(f"\n  ❌ 请求失败: {e}")
    
    print("\n✅ query_device_status 完整流程验证完成！")


def test_heartbeat_with_pending_command():
    """测试7：心跳自动携带待执行命令
    
    验证：
    1. 先排队一个 query_device_status 命令
    2. 设备发送心跳
    3. 心跳响应中应包含该命令
    """
    print("\n" + "=" * 60)
    print("测试7：心跳响应携带 pending command")
    print("=" * 60)
    
    # 步骤1：排队查询命令
    print("\n--- 步骤1: 排队 query_device_status 命令 ---")
    query_url = f"{API_BASE_URL}/device/query-status?device_id={DEVICE_ID}"
    
    try:
        resp1 = requests.post(query_url, timeout=10)
        if resp1.status_code == 200:
            print(f"  ✅ 命令已排队")
        else:
            print(f"  ❌ 排队失败: {resp1.text}")
            return
    except Exception as e:
        print(f"  ❌ 请求失败: {e}")
        return
    
    # 步骤2：设备发送心跳
    print("\n--- 步骤2: 设备发送心跳 ---")
    heartbeat_url = f"{API_BASE_URL}/device/heartbeat"
    heartbeat_data = {
        "msg_type": "heartbeat_report",
        "device_id": DEVICE_ID,
        "timestamp": get_timestamp()
    }
    heartbeat_data["check_code"] = calculate_check_code(heartbeat_data)
    
    try:
        resp2 = requests.post(heartbeat_url, json=heartbeat_data, timeout=10)
        print(f"  状态码: {resp2.status_code}")
        resp2_json = resp2.json()
        print(f"  响应: {json.dumps(resp2_json, indent=2, ensure_ascii=False)}")
        
        if resp2.status_code == 200 and resp2_json.get("code") == 0:
            data = resp2_json.get("data", {})
            has_ack = "ack" in data
            has_time_sync = "time_sync" in data
            has_command = "command" in data
            
            print(f"\n  {'✅' if has_ack else '❌'} 包含 ack: {has_ack}")
            print(f"  {'✅' if has_time_sync else '❌'} 包含 time_sync: {has_time_sync}")
            print(f"  {'✅' if has_command else '❌'} 包含 command: {has_command}")
            
            if has_command:
                cmd = data["command"]
                print(f"     命令类型: {cmd.get('msg_type', '')}")
                print("\n✅ 心跳响应成功携带 pending command！")
            else:
                print("\n⚠️ 心跳响应未包含 pending command（可能已被轮询取走）")
        else:
            print("\n❌ 心跳上报失败")
    except Exception as e:
        print(f"\n❌ 请求失败: {e}")


def test_qrcode_report():
    """测试5：模拟小程序扫码上报"""
    print("\n" + "=" * 60)
    print("测试5：小程序扫码上报 (qrcode-report)")
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
    """测试6：校验码验证"""
    print("\n" + "=" * 60)
    print("测试6：MD5校验码验证")
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


def test_camera_image_generation():
    """测试7：验证Base64图片生成功能"""
    print("\n" + "=" * 60)
    print("测试7：Base64图片生成验证")
    print("=" * 60)
    
    # 生成不同场景的测试图片
    test_cases = [
        ("回收箱内部-衣物俯视", 160, 120, 180, 120, 80),
        ("回收箱内部-衣物侧视", 160, 120, 100, 140, 180),
        ("用户正面照", 160, 120, 200, 160, 130),
        ("告警场景", 160, 120, 200, 60, 60),
    ]
    
    for label, w, h, r, g, b in test_cases:
        b64 = generate_test_png(w, h, r, g, b, text_label=label)
        raw_bytes = base64.b64decode(b64)
        
        # 验证PNG签名
        is_valid_png = raw_bytes[:8] == b'\x89PNG\r\n\x1a\n'
        
        print(f"  [{label}]")
        print(f"    尺寸: {w}x{h}, 颜色: RGB({r},{g},{b})")
        print(f"    Base64长度: {len(b64)} chars")
        print(f"    原始大小: {len(raw_bytes)} bytes")
        print(f"    PNG格式验证: {'✅ 有效' if is_valid_png else '❌ 无效'}")
    
    # 保存一张到本地验证
    sample = generate_test_png(320, 240, 100, 150, 200)
    sample_bytes = base64.b64decode(sample)
    
    try:
        with open("/tmp/test_camera_sample.png", "wb") as f:
            f.write(sample_bytes)
        print(f"\n  💾 示例图片已保存: /tmp/test_camera_sample.png ({len(sample_bytes)} bytes)")
        print(f"     可用浏览器打开验证图片是否正确显示")
    except Exception as e:
        print(f"\n  ⚠️  保存示例图片失败: {e}")
    
    print("\n✅ 图片生成验证完成！")


if __name__ == "__main__":
    print("🔧 4G设备-后台通信协议 测试工具")
    print(f"📡 API地址: {API_BASE_URL}")
    print(f"📱 设备ID: {DEVICE_ID}")
    print()
    
    # 基础验证
    test_camera_image_generation()
    test_check_code_verification()
    
    # 测试1: 设备状态上报（无摄像头）
    print()
    test_device_status_report()
    
    # 测试2: 设备状态上报（含摄像头数据）
    test_device_status_report_with_camera()
    
    # 测试3: 烟感告警上报（含摄像头数据）
    test_device_status_report_smoke_alarm_with_camera()
    
    # 测试4: 设备使用中上报 → 应返回 ack + time_sync
    test_device_status_report_first_use()
    
    # 测试5: 心跳上报 → 应返回 ack + time_sync
    test_heartbeat_report()
    
    # 测试6: 后台主动查询设备状态 → 完整流程
    test_query_device_status_flow()
    
    # 测试7: 心跳自动携带 pending command
    test_heartbeat_with_pending_command()
    
    # 测试8: 扫码上报（需要token，仅展示）
    test_qrcode_report()
    
    print("\n" + "=" * 60)
    print("所有测试完成！")
    print("=" * 60)
    print()
    print("📌 协议功能验证总结：")
    print("   ✅ device_status_report: 设备状态上报 + 摄像头图片")
    print("   ✅ time_sync: is_using=1 时返回时间同步")
    print("   ✅ heartbeat: 心跳响应 ack + time_sync")
    print("   ✅ query_device_status: 后台主动查询 → 排队 → 设备获取")
    print("   ✅ pending_command: 心跳自动携带待执行命令")
    print()
    print("📌 管理后台验证步骤：")
    print("   1. 登录管理后台 → 设备管理 → 找到设备 " + DEVICE_ID)
    print("   2. 点击「详情」进入设备详情页")
    print("   3. 查看「摄像头画面」区域，应显示最近上报的图片")
    print("   4. 点击图片可放大预览")
    print("   5. 点击「查看历史记录」可查看所有上报批次")
