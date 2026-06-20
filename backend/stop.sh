#!/bin/bash
# 停止脚本 - 优雅停止所有服务

echo "=========================================="
echo "停止论文评价检验系统"
echo "=========================================="

# 停止 Gunicorn
echo "[1/2] 停止 Gunicorn..."
if [ -f gunicorn.pid ]; then
    kill $(cat gunicorn.pid) 2>/dev/null && echo "✅ Gunicorn 已停止" || echo "⚠️ Gunicorn 未运行"
    rm -f gunicorn.pid
else
    killall gunicorn 2>/dev/null && echo "✅ Gunicorn 已停止" || echo "⚠️ Gunicorn 未运行"
fi

# 停止 Celery
echo "[2/2] 停止 Celery Workers..."
killall celery 2>/dev/null && echo "✅ Celery Workers 已停止" || echo "⚠️ Celery 未运行"

echo ""
echo "=========================================="
echo "✅ 所有服务已停止"
echo "=========================================="
