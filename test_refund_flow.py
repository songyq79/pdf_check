#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试退款流程：申请 → 审核 → 完成
"""
import sys
import io
import json
import requests
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent / "backend"))

API_URL = "http://127.0.0.1:8000/api/v1"
ADMIN_URL = "http://127.0.0.1:8000/api/v1/admin"

# Test users (username, password)
USER_NAME = "user"
USER_PASSWORD = "123456"
ADMIN_NAME = "admin"
ADMIN_PASSWORD = "admin123"

def login(username: str, password: str) -> str:
    """Login and return access token"""
    resp = requests.post(
        f"{API_URL}/auth/login",
        data={"username": username, "password": password}
    )
    if resp.status_code != 200:
        print(f"Login failed: {resp.json()}")
        return None
    token = resp.json().get("access_token")
    print(f"Login successful for {username}")
    return token

def get_paid_order(token: str):
    """Get first paid order"""
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(
        f"{API_URL}/billing/orders",
        headers=headers
    )
    if resp.status_code != 200:
        print(f"Failed to get orders: {resp.json()}")
        return None

    orders = resp.json()
    paid_orders = [o for o in orders if o['status'] == 'paid']
    if not paid_orders:
        print("No paid orders found")
        return None

    return paid_orders[0]

def apply_refund(token: str, order_no: str, reason: str):
    """Apply for refund"""
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.post(
        f"{API_URL}/billing/orders/{order_no}/refund-request",
        headers=headers,
        json={"reason": reason}
    )
    if resp.status_code != 200:
        print(f"Refund request failed: {resp.json()}")
        return False
    print(f"Refund request submitted: {resp.json()}")
    return True

def get_order_status(token: str, order_no: str):
    """Get current order status"""
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(
        f"{API_URL}/billing/orders",
        headers=headers
    )
    orders = resp.json()
    order = next((o for o in orders if o['order_no'] == order_no), None)
    if order:
        print(f"Order {order_no} status: {order['status']}")
        if order.get('refund_reason'):
            print(f"  Refund reason: {order['refund_reason']}")
        if order.get('refund_reject_reason'):
            print(f"  Rejection reason: {order['refund_reject_reason']}")
    return order

def list_refund_requests(admin_token: str):
    """Get list of pending refunds"""
    headers = {"Authorization": f"Bearer {admin_token}"}
    resp = requests.get(
        f"{ADMIN_URL}/refund-requests",
        headers=headers
    )
    if resp.status_code != 200:
        print(f"Failed to get refund requests: {resp.json()}")
        return []
    requests_data = resp.json()
    print(f"Found {len(requests_data)} pending refund requests")
    for req in requests_data:
        print(f"  - {req['order_no']}: {req.get('refund_reason', 'N/A')}")
    return requests_data

def approve_refund(admin_token: str, order_no: str):
    """Approve refund"""
    headers = {"Authorization": f"Bearer {admin_token}"}
    resp = requests.post(
        f"{ADMIN_URL}/orders/{order_no}/refund-approve",
        headers=headers
    )
    if resp.status_code != 200:
        print(f"Refund approval failed: {resp.json()}")
        return False
    print(f"Refund approved: {resp.json()}")
    return True

def reject_refund(admin_token: str, order_no: str, reason: str):
    """Reject refund"""
    headers = {"Authorization": f"Bearer {admin_token}"}
    resp = requests.post(
        f"{ADMIN_URL}/orders/{order_no}/refund-reject",
        headers=headers,
        json={"reason": reason}
    )
    if resp.status_code != 200:
        print(f"Refund rejection failed: {resp.json()}")
        return False
    print(f"Refund rejected: {resp.json()}")
    return True

def main():
    print("=" * 60)
    print("Testing Refund Workflow")
    print("=" * 60)

    # Step 1: Login as user
    print("\n[1] User Login...")
    user_token = login(USER_NAME, USER_PASSWORD)
    if not user_token:
        return

    # Step 2: Get a paid order
    print("\n[2] Getting paid order...")
    order = get_paid_order(user_token)
    if not order:
        return
    order_no = order['order_no']
    print(f"Selected order: {order_no} (Amount: {order['amount_cents']/100:.2f})")

    # Step 3: Check initial status
    print("\n[3] Initial order status:")
    get_order_status(user_token, order_no)

    # Step 4: User applies for refund
    print("\n[4] User applies for refund...")
    apply_refund(user_token, order_no, "质量不符合预期，需要退款")

    # Step 5: Verify status changed to refund_pending
    print("\n[5] Verify order status after refund request:")
    order = get_order_status(user_token, order_no)
    if order['status'] != 'refund_pending':
        print(f"ERROR: Order status should be 'refund_pending', got '{order['status']}'")
        return

    # Step 6: Admin login
    print("\n[6] Admin Login...")
    admin_token = login(ADMIN_NAME, ADMIN_PASSWORD)
    if not admin_token:
        return

    # Step 7: Admin views pending refund requests
    print("\n[7] Admin views pending refund requests...")
    refund_reqs = list_refund_requests(admin_token)

    # Step 8: Admin approves refund
    print("\n[8] Admin approves refund...")
    approve_refund(admin_token, order_no)

    # Step 9: Verify order status is now 'refunded'
    print("\n[9] Verify order status after approval:")
    order = get_order_status(user_token, order_no)
    if order['status'] != 'refunded':
        print(f"ERROR: Order status should be 'refunded', got '{order['status']}'")
        return

    print("\n" + "=" * 60)
    print("SUCCESS: Refund workflow completed!")
    print("=" * 60)

if __name__ == "__main__":
    main()
