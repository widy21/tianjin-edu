#!/usr/bin/env python3
"""
检查数据库配置项是否有效
用法: python check_config.py
"""
import sys
import os
import json

# 添加项目根目录到 sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.db import Database

def check_config():
    db = Database()
    
    print("=" * 60)
    print("检查数据库配置项")
    print("=" * 60)
    
    # 检查 JSON 格式的配置项
    json_keys = ['bid_dict', 'data_cfg']
    
    for key in json_keys:
        value = db.get_config(key)
        print(f"\n--- {key} ---")
        if value is None:
            print(f"  状态: ❌ 未配置")
            continue
        
        print(f"  长度: {len(value)} 字符")
        print(f"  前100字符: {value[:100]}...")
        
        try:
            parsed = json.loads(value)
            print(f"  状态: ✅ 有效 JSON")
            if isinstance(parsed, dict):
                print(f"  包含 {len(parsed)} 个键")
        except json.JSONDecodeError as e:
            print(f"  状态: ❌ JSON 解析失败")
            print(f"  错误: {e}")
            print(f"  完整值: {value}")
    
    # 检查其他关键配置
    print("\n--- 其他配置 ---")
    other_keys = ['tust_username', 'tust_password', 'env', 'chrome_binary_path', 'chromedriver_path',
                  'smtp_server', 'smtp_port', 'sender_email', 'sender_password']
    
    for key in other_keys:
        value = db.get_config(key)
        if value:
            # 敏感信息脱敏
            if 'password' in key.lower():
                display = '***' if value else '(未设置)'
            else:
                display = value[:50] + '...' if len(str(value)) > 50 else value
            print(f"  {key}: {display}")
        else:
            print(f"  {key}: (未设置)")
    
    print("\n" + "=" * 60)
    print("检查完成")
    print("=" * 60)

if __name__ == '__main__':
    check_config()
