#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
快速创建测试订单脚本
"""
import sys
import os
from datetime import datetime
from pathlib import Path

# Windows 编码兼容
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from app.models.user import init_db, SessionLocal
from app.models.billing import Order

def create_test_order():
    """创建测试订单"""
    # 初始化数据库
    init_db()
    db = SessionLocal()

    try:
        # 查询第一个用户
        from app.models.user import User
        user = db.query(User).first()
        if not user:
            print("❌ 错误：数据库中没有用户，请先注册一个用户")
            return

        print(f"✅ 找到用户：{user.username} (ID: {user.id})")

        # 创建测试订单
        test_order = Order(
            order_no=f"TEST{datetime.now().strftime('%Y%m%d%H%M%S')}",
            user_id=user.id,
            product_type='monthly',
            quantity=1,
            amount_cents=9900,
            status='paid',
            pay_method='wechat',
            paid_at=datetime.utcnow(),
        )

        db.add(test_order)
        db.commit()

        print(f"✅ 测试订单已创建！")
        print(f"   订单号: {test_order.order_no}")
        print(f"   用户: {user.username}")
        print(f"   金额: ¥99.00 (包月订阅)")
        print(f"   状态: paid (已支付)")
        print(f"\n现在请：")
        print(f"1. 刷新浏览器用户中心页面")
        print(f"2. 应该能看到'我的订单'卡片，里面有这个订单")
        print(f"3. 点击'申请退款'按钮进行测试")

    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    create_test_order()
