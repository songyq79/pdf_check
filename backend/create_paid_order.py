#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
创建已支付订单脚本
"""
import sys
import io
from datetime import datetime
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent))

from app.models.user import init_db, SessionLocal
from app.models.billing import Order
from app.models.user import User

def create_paid_order():
    """创建已支付订单"""
    init_db()
    db = SessionLocal()

    try:
        # 查询第一个用户
        user = db.query(User).first()
        if not user:
            print("错误：数据库中没有用户")
            return

        print(f"找到用户：{user.username} (ID: {user.id})")

        # 创建已支付订单
        paid_order = Order(
            order_no=f"PAID{datetime.now().strftime('%Y%m%d%H%M%S')}",
            user_id=user.id,
            product_type='monthly',
            quantity=1,
            amount_cents=9900,
            status='paid',  # 关键：已支付状态
            pay_method='wechat',
            paid_at=datetime.now(),
        )

        db.add(paid_order)
        db.commit()

        print(f"已支付订单创建成功！")
        print(f"订单号: {paid_order.order_no}")
        print(f"用户: {user.username}")
        print(f"金额: ¥99.00")
        print(f"状态: paid (已支付)")
        print(f"\n现在请刷新浏览器用户中心页面，应该能看到这个订单")
        print(f"状态应该显示'已支付'，操作列有'申请退款'按钮")

    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    create_paid_order()
