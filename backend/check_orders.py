#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
查看数据库中的所有订单
"""
import sys
import io
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent))

from app.models.user import init_db, SessionLocal
from app.models.billing import Order

def check_orders():
    """查看所有订单"""
    init_db()
    db = SessionLocal()

    try:
        orders = db.query(Order).all()
        print(f"数据库中共有 {len(orders)} 个订单:\n")

        for order in orders:
            print(f"订单号: {order.order_no}")
            print(f"  用户ID: {order.user_id}")
            print(f"  类型: {order.product_type}")
            print(f"  金额: {order.amount_cents / 100:.2f}")
            print(f"  状态: {order.status}")
            print(f"  创建时间: {order.created_at}")
            print(f"  支付时间: {order.paid_at}")
            print()

    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_orders()
