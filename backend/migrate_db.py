#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库迁移脚本 - 为 orders 表添加退款相关字段
"""
import sys
import io
import sqlite3
from pathlib import Path

# Windows 编码兼容
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

db_path = Path(__file__).parent / "storage" / "app.db"

if not db_path.exists():
    print("错误：数据库不存在")
    exit(1)

conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

# 检查表是否存在
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='orders'")
if not cursor.fetchone():
    print("错误：orders 表不存在")
    conn.close()
    exit(1)

# 获取现有列
cursor.execute("PRAGMA table_info(orders)")
existing_columns = {row[1] for row in cursor.fetchall()}
print(f"现有字段: {existing_columns}")

# 添加缺失的字段
columns_to_add = {
    'refund_reason': 'TEXT',
    'refund_reject_reason': 'TEXT',
    'refund_applied_at': 'DATETIME'
}

for col_name, col_type in columns_to_add.items():
    if col_name not in existing_columns:
        try:
            cursor.execute(f"ALTER TABLE orders ADD COLUMN {col_name} {col_type}")
            print(f"✓ 已添加列: {col_name}")
        except sqlite3.OperationalError as e:
            print(f"✗ 添加列 {col_name} 失败: {e}")
    else:
        print(f"✓ 列已存在: {col_name}")

conn.commit()
conn.close()

print("\n数据库迁移完成！")
