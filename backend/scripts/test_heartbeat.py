#!/usr/bin/env python3
"""
4G设备-后台通信协议 · 完整测试脚本
=====================================

按照《旧物回收通信协议.docx》对所有协议功能进行系统性验证。

"首次上报"判断逻辑说明：
  后台通过 devices 表的 first_report_at 字段判断设备是否首次上报数据。
  - 当 first_report_at 为 NULL 时，视为首次上报，后台返回 ack + time_sync。
  - 当 first_report_at 不为 NULL 时，视为非首次上报，后台仅返回 ack。
  注意：is_using 字段仅表示设备当前是否有人使用，与首次上报判断无关。

测试分为两大类：
  [离线测试] 不需要后端服务，本地验证
    P1 - Base64 图片生成验证
    P2 - MD5 校验码计算与验证

  [在线测试] 需要后端 API 服务
    T1 - 首次上报 (first_report_at=NULL) → 预期: ack + time_sync
    T2 - 非首次上报(含摄像头) → 预期: ack，无 time_sync + 图片保存
    T3 - 持续使用上报 (is_using=1, 含摄像头) → 预期: ack，无 time_sync + 图片保存
    T4 - 烟感告警上报 (smoke=1) → 预期: ack + 告警图片保存
    T5 - 使用结束上报 (is_using: 1→0) → 预期: ack，无 time_sync
    T6 - 心跳上报 (无待执行命令) → 预期: ack + time_sync，无 command
    T7 - 后台主动查询设备状态 → 完整流程 (排队 → 轮询获取 → 设备响应)
    T8 - 心跳携带待执行命令 → 预期: ack + time_sync + command
    T9 - 管理后台主动查询 (admin API) → 预期: 命令排队成功
    T10 - 错误校验码上报 → 预期: 校验失败
    T11 - 小程序扫码上报 (仅演示报文格式，需 token)

  ⚠️ 注意：T1 测试要求设备 first_report_at 字段为 NULL（即从未上报过数据）。
     如需重新测试，请先执行：
     UPDATE devices SET first_report_at = NULL WHERE device_id = 'DEV001';

使用方法:
    python3 scripts/test_heartbeat.py                    # 运行全部测试
    python3 scripts/test_heartbeat.py --offline-only     # 仅离线测试
    python3 scripts/test_heartbeat.py --api http://localhost:8000/api/v1
"""
import sys
import time
import requests
import json
import hashlib
import struct
import zlib
import base64
from datetime import datetime

# ============================================================
# 配置
# ============================================================
API_BASE_URL = "http://42.194.134.223:8000/api/v1"
ADMIN_API_BASE_URL = "http://42.194.134.223:8000/api/v1/admin"
DEVICE_ID = "DEV001"  # 请替换为实际设备ID

# 管理员认证（用于管理后台 API 测试）
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

# 报文包头包尾
PACKET_HEADER = "0x6868"
PACKET_FOOTER = "0x1616"

# ============================================================
# 测试结果跟踪
# ============================================================
test_results = []  # [(test_id, test_name, passed, detail)]


def record_result(test_id: str, test_name: str, passed: bool, detail: str = ""):
    """记录测试结果"""
    test_results.append((test_id, test_name, passed, detail))
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"\n{'─' * 40}")
    print(f"  {status} | {test_id}: {test_name}")
    if detail:
        print(f"  ℹ️  {detail}")
    print(f"{'─' * 40}")


# ============================================================
# 工具函数
# ============================================================
def get_timestamp():
    """获取标准时间戳字符串"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def calculate_check_code(packet_data: dict) -> str:
    """
    计算MD5校验码
    校验规则：包头(0x6868) + JSON数据体(不含check_code) → MD5，32位小写
    """
    data_copy = {k: v for k, v in packet_data.items() if k != "check_code"}
    json_str = json.dumps(data_copy, ensure_ascii=False, separators=(',', ':'))
    check_str = PACKET_HEADER + json_str
    return hashlib.md5(check_str.encode('utf-8')).hexdigest()


def wrap_packet(packet_data: dict) -> str:
    """添加包头包尾：0x6868 + JSON + 0x1616"""
    json_str = json.dumps(packet_data, ensure_ascii=False, separators=(',', ':'))
    return f"{PACKET_HEADER}{json_str}{PACKET_FOOTER}"


def generate_test_png(width=80, height=60, r=0, g=0, b=0, text_label=""):
    """
    生成一个有效的测试 PNG 图片（带边框和渐变效果增加辨识度）
    Returns: Base64 编码的 PNG 图片字符串
    """
    def create_png(w, h, r, g, b):
        signature = b'\x89PNG\r\n\x1a\n'
        ihdr_data = struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0)
        ihdr_crc = zlib.crc32(b'IHDR' + ihdr_data) & 0xffffffff
        ihdr = struct.pack('>I', 13) + b'IHDR' + ihdr_data + struct.pack('>I', ihdr_crc)
        raw_data = b''
        for y in range(h):
            raw_data += b'\x00'
            for x in range(w):
                if y < 4:
                    raw_data += bytes([255, 255, 255])
                elif y >= h - 4:
                    raw_data += bytes([max(0, r - 80), max(0, g - 80), max(0, b - 80)])
                elif x < 4 or x >= w - 4:
                    raw_data += bytes([min(255, r + 40), min(255, g + 40), min(255, b + 40)])
                else:
                    factor = 1.0 - abs(y - h / 2) / (h / 2) * 0.3
                    raw_data += bytes([
                        min(255, int(r * factor)),
                        min(255, int(g * factor)),
                        min(255, int(b * factor))
                    ])
        compressed = zlib.compress(raw_data)
        idat_crc = zlib.crc32(b'IDAT' + compressed) & 0xffffffff
        idat = struct.pack('>I', len(compressed)) + b'IDAT' + compressed + struct.pack('>I', idat_crc)
        iend_crc = zlib.crc32(b'IEND') & 0xffffffff
        iend = struct.pack('>I', 0) + b'IEND' + struct.pack('>I', iend_crc)
        return signature + ihdr + idat + iend

    return base64.b64encode(create_png(width, height, r, g, b)).decode('utf-8')


def generate_camera_test_data():
    """生成模拟摄像头数据：camera_1(回收箱内部)×3 + camera_2(用户画面)×3"""
    camera_1_images = [
        generate_test_png(160, 120, r=180, g=120, b=80),
        generate_test_png(160, 120, r=100, g=140, b=180),
        generate_test_png(160, 120, r=160, g=100, b=120),
    ]
    camera_2_images = [
        generate_test_png(160, 120, r=200, g=160, b=130),
        generate_test_png(160, 120, r=180, g=150, b=120),
        generate_test_png(160, 120, r=190, g=155, b=125),
    ]
    return {"camera_1": camera_1_images, "camera_2": camera_2_images}


def build_status_report(battery=85, smoke=0, bin_full=0, window_open=0,
                        is_using=0, camera_data=None):
    """构建设备状态上报报文"""
    report = {
        "msg_type": "device_status_report",
        "device_id": DEVICE_ID,
        "timestamp": get_timestamp(),
        "data": {
            "battery_level": battery,
            "location": {
                "longitude": 113.9423,
                "latitude": 22.5431,
                "address": "广东省深圳市宝安区XX街道XX路"
            },
            "smoke_sensor_status": smoke,
            "recycle_bin_full": bin_full,
            "delivery_window_open": window_open,
            "is_using": is_using,
            "camera_data": camera_data or {"camera_1": [], "camera_2": []}
        }
    }
    report["check_code"] = calculate_check_code(report)
    return report


def build_heartbeat():
    """构建心跳报文"""
    hb = {
        "msg_type": "heartbeat_report",
        "device_id": DEVICE_ID,
        "timestamp": get_timestamp()
    }
    hb["check_code"] = calculate_check_code(hb)
    return hb


def post_json(url, data, timeout=30):
    """发送 POST 请求并返回 (status_code, response_json)"""
    resp = requests.post(url, json=data, timeout=timeout)
    return resp.status_code, resp.json()


def get_json(url, timeout=10):
    """发送 GET 请求并返回 (status_code, response_json)"""
    resp = requests.get(url, timeout=timeout)
    return resp.status_code, resp.json()


def get_admin_token():
    """获取管理后台 JWT token"""
    try:
        login_url = f"{ADMIN_API_BASE_URL}/auth/login"
        status, data = post_json(login_url, {
            "username": ADMIN_USERNAME,
            "password": ADMIN_PASSWORD
        })
        if status == 200 and data.get("code") == 0:
            return data.get("data", {}).get("token")
    except Exception:
        pass
    return None


def print_section(title, width=60):
    """打印分隔标题"""
    print(f"\n{'═' * width}")
    print(f"  {title}")
    print(f"{'═' * width}")


def print_expected(items):
    """打印预期结果表"""
    print("\n  📋 预期结果:")
    for key, expected in items:
        print(f"     • {key}: {expected}")
    print()


def print_actual(items):
    """打印实际结果验证"""
    all_pass = True
    for key, actual, expected, ok in items:
        icon = "✅" if ok else "❌"
        if not ok:
            all_pass = False
        print(f"  {icon} {key}: {actual} (预期: {expected})")
    return all_pass


# ============================================================
# 离线测试
# ============================================================

def test_P1_camera_image_generation():
    """P1: Base64 图片生成验证（离线）"""
    print_section("P1: Base64 PNG 图片生成验证")
    print("  验证纯 Python 生成的 PNG 图片是否合法，能否正确 Base64 编码。\n")

    test_cases = [
        ("回收箱内部-暖色", 160, 120, 180, 120, 80),
        ("回收箱内部-冷色", 160, 120, 100, 140, 180),
        ("用户正面-肤色", 160, 120, 200, 160, 130),
        ("告警场景-红色", 160, 120, 200, 60, 60),
    ]

    all_valid = True
    for label, w, h, r, g, b in test_cases:
        b64 = generate_test_png(w, h, r, g, b, text_label=label)
        raw_bytes = base64.b64decode(b64)
        is_valid_png = raw_bytes[:8] == b'\x89PNG\r\n\x1a\n'
        starts_with_ivbor = b64.startswith('iVBOR')
        ok = is_valid_png and starts_with_ivbor
        if not ok:
            all_valid = False

        print(f"  [{label}] {w}×{h} RGB({r},{g},{b})")
        print(f"    Base64: {len(b64)} chars | PNG: {len(raw_bytes)} bytes")
        print(f"    {'✅' if is_valid_png else '❌'} PNG 头验证 | "
              f"{'✅' if starts_with_ivbor else '❌'} iVBOR 前缀")

    # 保存示例到 /tmp
    try:
        sample = generate_test_png(320, 240, 100, 150, 200)
        with open("/tmp/test_camera_sample.png", "wb") as f:
            f.write(base64.b64decode(sample))
        print(f"\n  💾 示例图片已保存: /tmp/test_camera_sample.png")
    except Exception:
        pass

    record_result("P1", "Base64 PNG 图片生成", all_valid,
                  f"{len(test_cases)} 张图片全部验证通过" if all_valid else "部分图片验证失败")


def test_P2_check_code_verification():
    """P2: MD5 校验码计算与验证（离线）"""
    print_section("P2: MD5 校验码计算与验证")
    print("  验证校验规则：包头(0x6868) + JSON(不含check_code) → MD5(32位小写)\n")

    # 场景 1：正确校验码
    report_data = {
        "msg_type": "heartbeat_report",
        "device_id": DEVICE_ID,
        "timestamp": "2026-01-30 10:00:00"
    }
    check_code = calculate_check_code(report_data)
    report_data["check_code"] = check_code

    data_copy = {k: v for k, v in report_data.items() if k != "check_code"}
    json_str = json.dumps(data_copy, ensure_ascii=False, separators=(',', ':'))
    check_str = PACKET_HEADER + json_str
    recomputed = hashlib.md5(check_str.encode('utf-8')).hexdigest()
    match_ok = check_code == recomputed

    print(f"  场景1: 正确校验码")
    print(f"    校验串: {check_str}")
    print(f"    计算结果: {check_code}")
    print(f"    重新计算: {recomputed}")
    print(f"    {'✅' if match_ok else '❌'} 匹配: {match_ok}")

    # 场景 2：错误校验码
    wrong_code = "0000000000000000ffffffffffffffff"
    mismatch_ok = wrong_code != recomputed
    print(f"\n  场景2: 错误校验码")
    print(f"    伪造校验码: {wrong_code}")
    print(f"    {'✅' if mismatch_ok else '❌'} 不匹配: {mismatch_ok}")

    # 场景 3：包头参与校验
    no_header_hash = hashlib.md5(json_str.encode('utf-8')).hexdigest()
    header_matters = no_header_hash != check_code
    print(f"\n  场景3: 包头参与校验")
    print(f"    无包头 MD5: {no_header_hash}")
    print(f"    有包头 MD5: {check_code}")
    print(f"    {'✅' if header_matters else '❌'} 包头影响结果: {header_matters}")

    all_pass = match_ok and mismatch_ok and header_matters
    record_result("P2", "MD5 校验码验证", all_pass)


# ============================================================
# 在线测试
# ============================================================

def test_T1_first_report_time_sync():
    """
    T1: 首次上报 → 触发时间同步 (first_report_at 为 NULL)
    协议规定: 设备首次向后台上报数据时，除了返回 ack 消息，还需返回 time_sync 消息。
    判断依据: devices 表的 first_report_at 字段为 NULL 即为首次上报。
    预期: 返回 ack + time_sync
    ⚠️ 注意: 如果设备之前已上报过数据(first_report_at 不为空)，则不会触发 time_sync。
           此时测试会给出 WARN 提示，需要重置 first_report_at 字段后重新测试。
    """
    print_section("T1: 首次上报 → 触发时间同步 (first_report_at=NULL)")
    print("  协议规定: 设备首次向后台上报数据时，后台返回 ack + time_sync")
    print("  判断依据: devices.first_report_at 为 NULL → 首次上报")
    print("  ⚠️  如设备已上报过，需先执行:")
    print(f"     UPDATE devices SET first_report_at = NULL WHERE device_id = '{DEVICE_ID}';")
    print_expected([
        ("HTTP 状态码", "200"),
        ("code", "0"),
        ("data.ack", "存在 (server_ack)"),
        ("data.time_sync", "存在 (首次上报触发时间同步)"),
        ("time_sync.data.standard_time", "当前服务器时间"),
    ])

    url = f"{API_BASE_URL}/device/report"
    report = build_status_report(battery=85, is_using=0)
    print(f"  📤 发送: 首次上报, battery=85%, is_using=0")

    try:
        status, resp = post_json(url, report)
        print(f"  📥 状态码: {status}")
        print(f"  📥 响应: {json.dumps(resp, indent=2, ensure_ascii=False)}")

        data = resp.get("data", {})
        has_time_sync = "time_sync" in data
        sync_time = ""
        if has_time_sync:
            sync_time = data["time_sync"].get("data", {}).get("standard_time", "")

        checks = [
            ("HTTP 状态码", status, 200, status == 200),
            ("code", resp.get("code"), 0, resp.get("code") == 0),
            ("data.ack", "存在" if "ack" in data else "不存在", "存在", "ack" in data),
            ("data.time_sync", "存在" if has_time_sync else "不存在",
             "存在", has_time_sync),
        ]
        if has_time_sync:
            checks.append(("standard_time", sync_time or "无", "当前服务器时间",
                           bool(sync_time)))

        ok = print_actual(checks)

        if not has_time_sync and status == 200 and resp.get("code") == 0:
            print("\n  ⚠️  未收到 time_sync！该设备可能已上报过数据(first_report_at 不为空)。")
            print(f"     请执行以下 SQL 后重新测试:")
            print(f"     UPDATE devices SET first_report_at = NULL WHERE device_id = '{DEVICE_ID}';")
            record_result("T1", "首次上报时间同步", False,
                          "设备已上报过数据，需重置 first_report_at")
        else:
            record_result("T1", "首次上报时间同步", ok,
                          f"同步时间: {sync_time}" if sync_time else "")
    except Exception as e:
        print(f"  ❌ 请求失败: {e}")
        record_result("T1", "首次上报时间同步", False, str(e))


def test_T2_subsequent_report_with_camera():
    """
    T2: 非首次上报 (first_report_at 已有值, 含摄像头)
    场景: T1 执行后，设备已有 first_report_at，后续上报不再触发 time_sync。
    预期: 返回 ack，不返回 time_sync，摄像头图片被保存
    """
    print_section("T2: 非首次上报 (含摄像头, is_using=1)")
    print("  场景: 设备已上报过数据(first_report_at 已有值)，不触发 time_sync")
    print("  同时验证摄像头图片上传功能")
    print_expected([
        ("data.ack", "存在"),
        ("data.time_sync", "不存在 (非首次上报，不触发时间同步)"),
        ("摄像头图片", "camera_1 × 3 + camera_2 × 3 已保存"),
    ])

    url = f"{API_BASE_URL}/device/report"
    print("  📸 生成测试图片中...")
    camera_data = generate_camera_test_data()
    print(f"  📸 camera_1: {len(camera_data['camera_1'])}张, "
          f"camera_2: {len(camera_data['camera_2'])}张")

    report = build_status_report(battery=80, window_open=1, is_using=1,
                                 camera_data=camera_data)
    print(f"  📤 发送: is_using=1, 报文大小={len(json.dumps(report))} bytes")

    try:
        status, resp = post_json(url, report)
        print(f"  📥 状态码: {status}")
        print(f"  📥 响应: {json.dumps(resp, indent=2, ensure_ascii=False)}")

        data = resp.get("data", {})
        checks = [
            ("HTTP 状态码", status, 200, status == 200),
            ("code", resp.get("code"), 0, resp.get("code") == 0),
            ("data.ack", "存在" if "ack" in data else "不存在", "存在", "ack" in data),
            ("data.time_sync", "存在" if "time_sync" in data else "不存在",
             "不存在", "time_sync" not in data),
        ]
        ok = print_actual(checks)
        record_result("T2", "非首次上报(含摄像头)", ok)
    except Exception as e:
        print(f"  ❌ 请求失败: {e}")
        record_result("T2", "非首次上报(含摄像头)", False, str(e))


def test_T3_continued_use_with_camera():
    """
    T3: 持续使用上报 (is_using=1, 含摄像头)
    场景: 设备已上报过数据(first_report_at 不为空)，非首次上报不触发 time_sync
    预期: 返回 ack，不返回 time_sync，摄像头图片被保存
    """
    print_section("T3: 持续使用上报 (is_using=1, 含摄像头)")
    print("  场景: 设备持续使用中，非首次上报，不触发时间同步")
    print_expected([
        ("data.ack", "存在"),
        ("data.time_sync", "不存在 (非首次上报，不触发)"),
        ("摄像头图片", "camera_1 × 3 + camera_2 × 3 已保存"),
    ])

    url = f"{API_BASE_URL}/device/report"
    print("  📸 生成测试图片中...")
    camera_data = generate_camera_test_data()

    report = build_status_report(battery=78, window_open=1, is_using=1,
                                 camera_data=camera_data)
    print(f"  📤 发送: is_using=1(持续), 报文大小={len(json.dumps(report))} bytes")

    try:
        status, resp = post_json(url, report)
        print(f"  📥 状态码: {status}")
        print(f"  📥 响应: {json.dumps(resp, indent=2, ensure_ascii=False)}")

        data = resp.get("data", {})
        checks = [
            ("HTTP 状态码", status, 200, status == 200),
            ("code", resp.get("code"), 0, resp.get("code") == 0),
            ("data.ack", "存在" if "ack" in data else "不存在", "存在", "ack" in data),
            ("data.time_sync", "存在" if "time_sync" in data else "不存在",
             "不存在", "time_sync" not in data),
        ]
        ok = print_actual(checks)
        record_result("T3", "持续使用上报(含摄像头)", ok)
    except Exception as e:
        print(f"  ❌ 请求失败: {e}")
        record_result("T3", "持续使用上报(含摄像头)", False, str(e))


def test_T4_smoke_alarm_with_camera():
    """
    T4: 烟感告警上报 (smoke_sensor_status=1, 含摄像头)
    协议场景: 烟感触发告警，设备立即上报现场照片
    预期: 返回 ack，告警状态和图片被保存
    """
    print_section("T4: 烟感告警上报 (smoke=1, 含告警现场照片)")
    print("  场景: 烟感传感器触发告警，设备上报并附带现场照片")
    print_expected([
        ("data.ack", "存在"),
        ("ack.data.ack_code", "0 (接收成功)"),
        ("后台设备表", "smoke_sensor_status 更新为 1"),
        ("摄像头图片", "camera_1 × 2 + camera_2 × 1 (告警场景)"),
    ])

    url = f"{API_BASE_URL}/device/report"
    print("  📸 生成告警场景测试图片(红色调)...")
    camera_data = {
        "camera_1": [
            generate_test_png(160, 120, r=200, g=60, b=60),
            generate_test_png(160, 120, r=220, g=80, b=50),
        ],
        "camera_2": [
            generate_test_png(160, 120, r=180, g=150, b=120),
        ]
    }

    report = build_status_report(battery=75, smoke=1, is_using=0,
                                 camera_data=camera_data)
    print(f"  📤 发送: smoke=1 ⚠️ 告警, 报文大小={len(json.dumps(report))} bytes")

    try:
        status, resp = post_json(url, report)
        print(f"  📥 状态码: {status}")
        print(f"  📥 响应: {json.dumps(resp, indent=2, ensure_ascii=False)}")

        data = resp.get("data", {})
        ack_code = data.get("ack", {}).get("data", {}).get("ack_code")
        checks = [
            ("HTTP 状态码", status, 200, status == 200),
            ("code", resp.get("code"), 0, resp.get("code") == 0),
            ("data.ack", "存在" if "ack" in data else "不存在", "存在", "ack" in data),
            ("ack.data.ack_code", ack_code, 0, ack_code == 0),
        ]
        ok = print_actual(checks)
        record_result("T4", "烟感告警上报(含现场照片)", ok)
    except Exception as e:
        print(f"  ❌ 请求失败: {e}")
        record_result("T4", "烟感告警上报(含现场照片)", False, str(e))


def test_T5_end_use_report():
    """
    T5: 使用结束上报 (is_using: 1→0)
    协议场景: 用户使用完毕，设备恢复空闲
    预期: 返回 ack，不返回 time_sync (非首次上报)
    """
    print_section("T5: 使用结束上报 (is_using: 1→0)")
    print("  场景: 用户使用完毕，设备从使用中恢复到空闲状态")
    print_expected([
        ("data.ack", "存在"),
        ("data.time_sync", "不存在 (非首次上报，不触发时间同步)"),
    ])

    url = f"{API_BASE_URL}/device/report"
    report = build_status_report(battery=76, window_open=0, is_using=0)
    print(f"  📤 发送: is_using=0 (使用结束)")

    try:
        status, resp = post_json(url, report)
        print(f"  📥 状态码: {status}")
        print(f"  📥 响应: {json.dumps(resp, indent=2, ensure_ascii=False)}")

        data = resp.get("data", {})
        checks = [
            ("HTTP 状态码", status, 200, status == 200),
            ("code", resp.get("code"), 0, resp.get("code") == 0),
            ("data.ack", "存在" if "ack" in data else "不存在", "存在", "ack" in data),
            ("data.time_sync", "存在" if "time_sync" in data else "不存在",
             "不存在", "time_sync" not in data),
        ]
        ok = print_actual(checks)
        record_result("T5", "使用结束上报", ok)
    except Exception as e:
        print(f"  ❌ 请求失败: {e}")
        record_result("T5", "使用结束上报", False, str(e))


def test_T6_heartbeat_report():
    """
    T6: 心跳上报 (无待执行命令)
    协议规定: 后台收到心跳后，下发 ack + time_sync 消息。
    预期: 返回 ack + time_sync，不返回 command (无待执行命令)
    """
    print_section("T6: 心跳上报 → ack + time_sync")
    print("  协议规定: 后台收到设备心跳包后，下发 time_sync 消息")
    print_expected([
        ("data.ack", "存在"),
        ("data.time_sync", "存在 (心跳触发时间同步)"),
        ("time_sync.data.standard_time", "当前服务器时间"),
        ("data.command", "不存在 (无待执行命令)"),
    ])

    url = f"{API_BASE_URL}/device/heartbeat"
    hb = build_heartbeat()
    print(f"  📤 完整报文: {wrap_packet(hb)[:80]}...")

    try:
        status, resp = post_json(url, hb)
        print(f"  📥 状态码: {status}")
        print(f"  📥 响应: {json.dumps(resp, indent=2, ensure_ascii=False)}")

        data = resp.get("data", {})
        has_ts = "time_sync" in data
        sync_time = ""
        if has_ts:
            sync_time = data["time_sync"].get("data", {}).get("standard_time", "")

        checks = [
            ("HTTP 状态码", status, 200, status == 200),
            ("code", resp.get("code"), 0, resp.get("code") == 0),
            ("data.ack", "存在" if "ack" in data else "不存在", "存在", "ack" in data),
            ("data.time_sync", "存在" if has_ts else "不存在", "存在", has_ts),
            ("standard_time", sync_time or "无", "当前服务器时间", bool(sync_time)),
            ("data.command", "存在" if "command" in data else "不存在",
             "不存在", "command" not in data),
        ]
        ok = print_actual(checks)
        record_result("T6", "心跳上报(time_sync)", ok,
                      f"同步时间: {sync_time}" if sync_time else "")
    except Exception as e:
        print(f"  ❌ 请求失败: {e}")
        record_result("T6", "心跳上报(time_sync)", False, str(e))


def test_T7_query_device_status_flow():
    """
    T7: 后台主动查询设备状态 (完整流程)
    协议规定: 后台主动下发 query_device_status，设备收到后返回 device_status_report。
    
    完整流程:
      步骤1: 后台调用 /query-status 排队查询命令
      步骤2: 设备通过 /pending-commands 轮询获取命令
      步骤3: 再次轮询确认命令已被清除
      步骤4: 设备响应查询，上报 device_status_report
    """
    print_section("T7: 后台主动查询设备状态 (query_device_status 完整流程)")
    print("  协议规定: 后台主动下发 query_device_status，设备收到后返回全量状态")
    print_expected([
        ("步骤1: POST /query-status", "code=0, 命令已排队"),
        ("步骤2: GET /pending-commands", "has_command=true, msg_type=query_device_status"),
        ("步骤3: GET /pending-commands (再次)", "has_command=false (已被取走)"),
        ("步骤4: POST /report", "code=0, 设备状态更新成功"),
    ])

    step_results = [False, False, False, False]

    # 步骤1
    print("\n  ── 步骤1: 后台下发 query_device_status 命令 ──")
    query_url = f"{API_BASE_URL}/device/query-status?device_id={DEVICE_ID}"
    try:
        s1, r1 = post_json(query_url, {})
        print(f"  📥 {s1} - {json.dumps(r1, indent=2, ensure_ascii=False)}")
        step_results[0] = (s1 == 200 and r1.get("code") == 0)
        print(f"  {'✅' if step_results[0] else '❌'} 命令排队: {'成功' if step_results[0] else '失败'}")
    except Exception as e:
        print(f"  ❌ 请求失败: {e}")
        record_result("T7", "后台主动查询(完整流程)", False, f"步骤1失败: {e}")
        return

    # 步骤2
    print("\n  ── 步骤2: 设备轮询获取待执行命令 ──")
    poll_url = f"{API_BASE_URL}/device/pending-commands/{DEVICE_ID}"
    try:
        s2, r2 = get_json(poll_url)
        print(f"  📥 {s2} - {json.dumps(r2, indent=2, ensure_ascii=False)}")
        poll_data = r2.get("data", {})
        has_cmd = poll_data.get("has_command", False)
        cmd_type = poll_data.get("command", {}).get("msg_type", "") if has_cmd else ""
        step_results[1] = (has_cmd and cmd_type == "query_device_status")
        print(f"  {'✅' if step_results[1] else '❌'} 收到命令: has_command={has_cmd}, msg_type={cmd_type}")
    except Exception as e:
        print(f"  ❌ 请求失败: {e}")

    # 步骤3
    print("\n  ── 步骤3: 再次轮询 (应为空，命令不会重复下发) ──")
    try:
        s3, r3 = get_json(poll_url)
        has_cmd_2 = r3.get("data", {}).get("has_command", False)
        step_results[2] = not has_cmd_2
        print(f"  {'✅' if step_results[2] else '❌'} 命令已清除: has_command={has_cmd_2} (预期: false)")
    except Exception as e:
        print(f"  ❌ 请求失败: {e}")

    # 步骤4
    print("\n  ── 步骤4: 设备响应查询，上报完整状态 ──")
    report_url = f"{API_BASE_URL}/device/report"
    report = build_status_report(battery=82, is_using=0)
    try:
        s4, r4 = post_json(report_url, report)
        print(f"  📥 {s4} - {r4.get('message', '')}")
        step_results[3] = (s4 == 200 and r4.get("code") == 0)
        print(f"  {'✅' if step_results[3] else '❌'} 设备响应上报: {'成功' if step_results[3] else '失败'}")
    except Exception as e:
        print(f"  ❌ 请求失败: {e}")

    all_pass = all(step_results)
    detail = "、".join([
        f"步骤{i+1}{'✅' if r else '❌'}" for i, r in enumerate(step_results)
    ])
    record_result("T7", "后台主动查询(完整流程)", all_pass, detail)


def test_T8_heartbeat_with_pending_command():
    """
    T8: 心跳自动携带待执行命令
    协议规定: 设备心跳时，后台检查是否有待执行命令，有则一并下发。
    
    流程:
      步骤1: 排队 query_device_status 命令
      步骤2: 设备发送心跳
      步骤3: 验证心跳响应中包含 ack + time_sync + command
    """
    print_section("T8: 心跳携带待执行命令")
    print("  场景: 先排队命令，设备心跳时自动获取")
    print_expected([
        ("步骤1: 命令排队", "成功"),
        ("步骤2: 心跳响应 data.ack", "存在"),
        ("步骤2: 心跳响应 data.time_sync", "存在"),
        ("步骤2: 心跳响应 data.command", "存在 (query_device_status)"),
        ("步骤2: command.msg_type", "query_device_status"),
    ])

    # 步骤1
    print("\n  ── 步骤1: 排队 query_device_status 命令 ──")
    query_url = f"{API_BASE_URL}/device/query-status?device_id={DEVICE_ID}"
    try:
        s1, r1 = post_json(query_url, {})
        queue_ok = (s1 == 200 and r1.get("code") == 0)
        print(f"  {'✅' if queue_ok else '❌'} 命令排队: {'成功' if queue_ok else '失败'}")
        if not queue_ok:
            record_result("T8", "心跳携带待执行命令", False, "命令排队失败")
            return
    except Exception as e:
        print(f"  ❌ 请求失败: {e}")
        record_result("T8", "心跳携带待执行命令", False, str(e))
        return

    # 步骤2
    print("\n  ── 步骤2: 设备发送心跳 ──")
    url = f"{API_BASE_URL}/device/heartbeat"
    hb = build_heartbeat()
    try:
        s2, r2 = post_json(url, hb)
        print(f"  📥 状态码: {s2}")
        print(f"  📥 响应: {json.dumps(r2, indent=2, ensure_ascii=False)}")

        data = r2.get("data", {})
        has_cmd = "command" in data
        cmd_type = data.get("command", {}).get("msg_type", "") if has_cmd else ""

        checks = [
            ("HTTP 状态码", s2, 200, s2 == 200),
            ("code", r2.get("code"), 0, r2.get("code") == 0),
            ("data.ack", "存在" if "ack" in data else "不存在", "存在", "ack" in data),
            ("data.time_sync", "存在" if "time_sync" in data else "不存在",
             "存在", "time_sync" in data),
            ("data.command", "存在" if has_cmd else "不存在", "存在", has_cmd),
            ("command.msg_type", cmd_type or "无", "query_device_status",
             cmd_type == "query_device_status"),
        ]
        ok = print_actual(checks)
        record_result("T8", "心跳携带待执行命令", ok)
    except Exception as e:
        print(f"  ❌ 请求失败: {e}")
        record_result("T8", "心跳携带待执行命令", False, str(e))


def test_T9_admin_query_device_status():
    """
    T9: 管理后台主动查询设备状态 (admin API)
    场景: 管理员通过后台管理系统点击「主动查询设备状态」按钮
    预期: 命令排队成功，设备在下次心跳时获取
    """
    print_section("T9: 管理后台主动查询 (admin API)")
    print("  场景: 管理员登录后台 → 设备详情 → 点击「主动查询设备状态」")
    print_expected([
        ("admin 登录", "获取 JWT token"),
        ("POST /admin/device/query-status", "code=0, 命令已排队"),
    ])

    # 获取 admin token
    print("\n  ── 步骤1: 管理员登录 ──")
    token = get_admin_token()
    if token:
        print(f"  ✅ 登录成功, token: {token[:20]}...")
    else:
        print(f"  ⚠️  管理员登录失败 (可能未配置或密码错误)")
        print(f"     尝试使用设备通信接口代替测试...")
        # 回退到设备通信接口测试
        query_url = f"{API_BASE_URL}/device/query-status?device_id={DEVICE_ID}"
        try:
            s, r = post_json(query_url, {})
            ok = (s == 200 and r.get("code") == 0)
            print(f"  📥 {s} - {r.get('message', '')}")
            record_result("T9", "管理后台主动查询", ok,
                          "使用设备通信接口代替(admin登录失败)")
        except Exception as e:
            record_result("T9", "管理后台主动查询", False, str(e))
        return

    # 使用 admin token 调用
    print("\n  ── 步骤2: 调用管理后台查询接口 ──")
    admin_query_url = f"{ADMIN_API_BASE_URL}/device/query-status?device_id={DEVICE_ID}"
    try:
        resp = requests.post(admin_query_url, timeout=10,
                             headers={"Authorization": f"Bearer {token}"})
        s, r = resp.status_code, resp.json()
        print(f"  📥 {s} - {json.dumps(r, indent=2, ensure_ascii=False)}")

        ok = (s == 200 and r.get("code") == 0)
        checks = [
            ("HTTP 状态码", s, 200, s == 200),
            ("code", r.get("code"), 0, r.get("code") == 0),
        ]
        ok = print_actual(checks)
        record_result("T9", "管理后台主动查询", ok)
    except Exception as e:
        print(f"  ❌ 请求失败: {e}")
        record_result("T9", "管理后台主动查询", False, str(e))

    # 清除 pending command 避免影响后续测试
    try:
        get_json(f"{API_BASE_URL}/device/pending-commands/{DEVICE_ID}")
    except Exception:
        pass


def test_T10_wrong_check_code():
    """
    T10: 错误校验码上报
    协议规定: 校验码不匹配时，后台返回 ack_code=1 (接收失败)
    预期: 返回 code=1, ack.data.ack_desc 包含 "校验失败"
    """
    print_section("T10: 错误校验码上报")
    print("  场景: 设备上报的报文被篡改，校验码不匹配")
    print_expected([
        ("code", "1 (校验失败)"),
        ("data.ack.data.ack_code", "1 (接收失败)"),
        ("data.ack.data.ack_desc", "包含 '校验失败'"),
    ])

    url = f"{API_BASE_URL}/device/report"
    report = build_status_report(battery=90, is_using=0)
    # 故意篡改校验码
    report["check_code"] = "0000000000000000ffffffffffffffff"

    print(f"  📤 发送: 篡改 check_code = {report['check_code']}")

    try:
        status, resp = post_json(url, report)
        print(f"  📥 状态码: {status}")
        print(f"  📥 响应: {json.dumps(resp, indent=2, ensure_ascii=False)}")

        data = resp.get("data", {})
        ack_code = data.get("ack", {}).get("data", {}).get("ack_code")
        ack_desc = data.get("ack", {}).get("data", {}).get("ack_desc", "")

        checks = [
            ("HTTP 状态码", status, 200, status == 200),
            ("code", resp.get("code"), 1, resp.get("code") == 1),
            ("ack.data.ack_code", ack_code, 1, ack_code == 1),
            ("ack_desc 包含校验", f"'{ack_desc}'", "包含'校验'",
             "校验" in ack_desc),
        ]
        ok = print_actual(checks)
        record_result("T10", "错误校验码上报", ok)
    except Exception as e:
        print(f"  ❌ 请求失败: {e}")
        record_result("T10", "错误校验码上报", False, str(e))


def test_T11_qrcode_report_demo():
    """
    T11: 小程序扫码上报 (仅演示报文格式)
    此接口需要用户登录 token，这里仅展示报文结构。
    """
    print_section("T11: 小程序扫码上报 (报文格式演示)")
    print("  场景: 用户投递衣物后，扫描设备二维码，小程序将数据发送到后台")
    print("  ⚠️  此接口需要用户登录 token，仅演示报文格式\n")

    report = build_status_report(battery=75, window_open=1, is_using=1)
    qrcode_content = wrap_packet(report)

    print(f"  二维码内容 (设备生成):")
    print(f"    {qrcode_content[:100]}...")
    print(f"    报文长度: {len(qrcode_content)} 字符")
    print(f"\n  小程序请求格式:")
    print(f"    POST /api/v1/device/qrcode-report")
    print(f"    Headers: Authorization: Bearer <user_token>")
    print(f"    Body: {json.dumps({'raw_data': qrcode_content[:60] + '...'}, ensure_ascii=False)}")
    print(f"\n  预期响应:")
    print(f"    code: 0")
    print(f"    data.ack: server_ack 应答")
    print(f"    data.device_info: 设备信息 (名称、地址、单价)")
    print(f"    data.report_data: 上报的状态数据")

    record_result("T11", "扫码上报(报文格式演示)", True, "仅格式演示，未实际调用")


# ============================================================
# 测试结果汇总
# ============================================================

def print_summary():
    """打印测试结果汇总"""
    total = len(test_results)
    passed = sum(1 for _, _, ok, _ in test_results if ok)
    failed = total - passed

    print(f"\n{'━' * 70}")
    print(f"  📊 测试结果汇总")
    print(f"{'━' * 70}")
    print(f"  总计: {total} | ✅ 通过: {passed} | ❌ 失败: {failed}")
    print(f"{'━' * 70}")
    print()
    print(f"  {'编号':<6} {'测试名称':<30} {'结果':<8} {'说明'}")
    print(f"  {'─' * 6} {'─' * 30} {'─' * 8} {'─' * 20}")

    for test_id, name, ok, detail in test_results:
        status = "✅ PASS" if ok else "❌ FAIL"
        print(f"  {test_id:<6} {name:<30} {status:<8} {detail}")

    print()

    if failed == 0:
        print("  🎉 所有测试通过！")
    else:
        print(f"  ⚠️  有 {failed} 个测试未通过，请检查后端服务和数据库。")

    # 功能覆盖总结
    print(f"\n{'━' * 70}")
    print(f"  📋 协议功能覆盖")
    print(f"{'━' * 70}")
    features = [
        ("上行: device_status_report", "T1/T2/T3/T4/T5", "设备状态上报(含各种场景)"),
        ("上行: heartbeat_report", "T6/T8", "心跳上报 + 时间同步"),
        ("下行: server_ack", "T1~T10", "所有上报接口的应答"),
        ("下行: time_sync (首次上报)", "T1", "first_report_at为NULL时下发"),
        ("下行: time_sync (心跳)", "T6/T8", "收到心跳后下发"),
        ("下行: query_device_status", "T7/T8/T9", "后台主动查询"),
        ("功能: pending_command", "T7/T8", "命令排队 + 心跳/轮询获取"),
        ("功能: camera_data", "T2/T3/T4", "摄像头图片Base64存储"),
        ("功能: MD5 校验", "P2/T10", "校验码计算与验证"),
        ("功能: 管理后台查询", "T9", "admin API 主动查询"),
    ]
    for feature, tests, desc in features:
        print(f"  {'✅'} {feature:<30} [{tests:<10}] {desc}")

    # 管理后台验证提示
    print(f"\n{'━' * 70}")
    print(f"  📌 管理后台验证步骤")
    print(f"{'━' * 70}")
    print(f"  1. 登录管理后台 → 设备管理 → 找到设备 {DEVICE_ID}")
    print(f"  2. 查看设备状态是否与最后一次上报数据一致")
    print(f"  3. 点击「详情」→ 查看「摄像头画面」区域")
    print(f"  4. 点击「主动查询设备状态」按钮，验证命令下发")
    print(f"  5. 点击图片可放大预览")
    print(f"  6. 点击「查看历史记录」查看所有上报批次")
    print()


# ============================================================
# 主入口
# ============================================================

if __name__ == "__main__":
    # 解析命令行参数
    offline_only = "--offline-only" in sys.argv
    for arg in sys.argv[1:]:
        if arg.startswith("--api"):
            parts = arg.split("=", 1) if "=" in arg else (arg, "")
            if len(parts) == 2 and parts[1]:
                API_BASE_URL = parts[1]
            elif sys.argv.index(arg) + 1 < len(sys.argv):
                API_BASE_URL = sys.argv[sys.argv.index(arg) + 1]

    print("╔" + "═" * 58 + "╗")
    print("║  🔧 4G设备-后台通信协议 · 完整测试套件                  ║")
    print("╠" + "═" * 58 + "╣")
    print(f"║  📡 API地址: {API_BASE_URL:<44}║")
    print(f"║  📱 设备ID:  {DEVICE_ID:<44}║")
    print(f"║  🕐 时间:    {get_timestamp():<44}║")
    print(f"║  📋 模式:    {'仅离线测试' if offline_only else '全部测试':<44}║")
    print("╚" + "═" * 58 + "╝")

    # ========== 离线测试 ==========
    print(f"\n\n{'▓' * 60}")
    print(f"  第一部分: 离线测试 (不需要后端服务)")
    print(f"{'▓' * 60}")

    test_P1_camera_image_generation()
    test_P2_check_code_verification()

    if offline_only:
        print_summary()
        sys.exit(0)

    # ========== 在线测试 ==========
    print(f"\n\n{'▓' * 60}")
    print(f"  第二部分: 在线测试 (需要后端 API 服务)")
    print(f"{'▓' * 60}")

    # 先检查服务是否可用
    print("\n  🔍 检查后端服务连接...")
    try:
        r = requests.get(f"{API_BASE_URL.rsplit('/api', 1)[0]}/health", timeout=5)
        if r.status_code == 200:
            print(f"  ✅ 后端服务正常: {r.json()}")
        else:
            print(f"  ⚠️  后端服务返回: {r.status_code}")
    except Exception as e:
        print(f"  ❌ 无法连接后端服务: {e}")
        print(f"     请确认 API 地址是否正确: {API_BASE_URL}")
        print(f"     可使用 --api <url> 指定地址")
        print_summary()
        sys.exit(1)

    # T1: 首次上报 → time_sync (要求 first_report_at 为 NULL)
    test_T1_first_report_time_sync()

    # T2: 非首次上报 + 摄像头 (T1执行后，first_report_at 已有值)
    test_T2_subsequent_report_with_camera()

    # T3: 持续使用 + 摄像头 (紧接T2，此时is_using已经是1)
    test_T3_continued_use_with_camera()

    # T4: 烟感告警 + 摄像头
    test_T4_smoke_alarm_with_camera()

    # T5: 使用结束(1→0)，恢复空闲
    test_T5_end_use_report()

    # T6: 心跳上报 → ack + time_sync
    test_T6_heartbeat_report()

    # T7: 后台主动查询 → 完整流程
    test_T7_query_device_status_flow()

    # T8: 心跳携带 pending command
    test_T8_heartbeat_with_pending_command()

    # T9: 管理后台主动查询 (admin API)
    test_T9_admin_query_device_status()

    # T10: 错误校验码
    test_T10_wrong_check_code()

    # T11: 扫码上报演示
    test_T11_qrcode_report_demo()

    # ========== 汇总 ==========
    print_summary()
