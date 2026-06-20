#!/bin/bash
# 启动脚本 - 一键启动应用（Gunicorn + 3个 Celery Worker）

set -e

cd /digital_human_dev/pdf_check/backend

echo "=========================================="
echo "启动论文评价检验系统 v1.0.0"
echo "=========================================="

# 启动 Gunicorn
echo "[1/4] 启动 Gunicorn (FastAPI 服务)..."
nohup gunicorn -c gunicorn_config.py app.main:app > /tmp/gunicorn.log 2>&1 &
echo "✅ Gunicorn 已启动 (PID: $!)"
sleep 2

# 启动 Celery Worker 1：校对任务
echo "[2/4] 启动 Celery Worker 1 (校对任务)..."
export APP_ENV=production
nohup celery -A app.workers.celery_app worker \
  --loglevel=info \
  --queues=proofread \
  --concurrency=64 \
  --pool=threads \
  --hostname=worker-proofread@%h > /tmp/celery_proofread.log 2>&1 &
echo "✅ Worker 1 已启动"
sleep 1

# 启动 Celery Worker 2：评价任务
echo "[3/4] 启动 Celery Worker 2 (评价任务)..."
export APP_ENV=production
nohup celery -A app.workers.celery_app worker \
  --loglevel=info \
  --queues=evaluation \
  --concurrency=48 \
  --pool=threads \
  --hostname=worker-evaluation@%h > /tmp/celery_evaluation.log 2>&1 &
echo "✅ Worker 2 已启动"
sleep 1

# 启动 Celery Worker 3：其他任务
echo "[4/4] 启动 Celery Worker 3 (排版/查重/默认)..."
export APP_ENV=production
nohup celery -A app.workers.celery_app worker \
  --loglevel=info \
  --queues=formatter,plagiarism,default \
  --concurrency=32 \
  --pool=threads \
  --hostname=worker-misc@%h > /tmp/celery_misc.log 2>&1 &
echo "✅ Worker 3 已启动"

echo ""
echo "=========================================="
echo "✅ 所有服务已启动！"
echo "=========================================="
echo ""
echo "📊 检查状态："
echo "  • Gunicorn:  lsof -i :5001"
echo "  • Celery:    ps aux | grep celery"
echo ""
echo "📖 查看日志："
echo "  • Gunicorn:     tail -f /tmp/gunicorn.log"
echo "  • Worker 1:     tail -f /tmp/celery_proofread.log"
echo "  • Worker 2:     tail -f /tmp/celery_evaluation.log"
echo "  • Worker 3:     tail -f /tmp/celery_misc.log"
echo ""
echo "🛑 停止服务："
echo "  killall gunicorn"
echo "  killall celery"
