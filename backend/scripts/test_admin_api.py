"""
测试管理后台 API 接口
"""
import asyncio
import sys
import requests
import json

BASE_URL = "http://localhost:8000/api/v1/admin"

def test_login():
    """测试登录"""
    print("=" * 50)
    print("1. 测试登录接口")
    print("=" * 50)
    
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"username": "admin", "password": "admin123"}
    )
    
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.text}")
    
    if response.status_code == 200:
        data = response.json()
        if data.get("code") == 0:
            token = data.get("data", {}).get("token")
            print(f"✅ 登录成功，Token: {token[:50]}...")
            return token
        else:
            print(f"❌ 登录失败: {data.get('message')}")
    else:
        print(f"❌ 请求失败: {response.text}")
    
    return None

def test_profile(token):
    """测试获取用户信息"""
    print("\n" + "=" * 50)
    print("2. 测试获取用户信息接口")
    print("=" * 50)
    
    if not token:
        print("❌ 没有 token，跳过测试")
        return
    
    response = requests.get(
        f"{BASE_URL}/auth/profile",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.text}")
    
    if response.status_code == 200:
        data = response.json()
        if data.get("code") == 0:
            print("✅ 获取用户信息成功")
        else:
            print(f"❌ 获取失败: {data.get('message')}")
    else:
        print(f"❌ 请求失败: {response.text}")

def test_dashboard_stats(token):
    """测试获取统计数据"""
    print("\n" + "=" * 50)
    print("3. 测试获取统计数据接口")
    print("=" * 50)
    
    if not token:
        print("❌ 没有 token，跳过测试")
        return
    
    response = requests.get(
        f"{BASE_URL}/dashboard/stats",
        headers={"Authorization": f"Bearer {token}"},
        params={"period": "today"}
    )
    
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.text}")
    
    if response.status_code == 200:
        data = response.json()
        if data.get("code") == 0:
            print("✅ 获取统计数据成功")
        else:
            print(f"❌ 获取失败: {data.get('message')}")
    else:
        print(f"❌ 请求失败: {response.text}")

if __name__ == "__main__":
    print("🔍 开始测试管理后台 API 接口...\n")
    
    # 测试登录
    token = test_login()
    
    # 测试获取用户信息
    test_profile(token)
    
    # 测试获取统计数据
    test_dashboard_stats(token)
    
    print("\n" + "=" * 50)
    print("测试完成")
    print("=" * 50)
