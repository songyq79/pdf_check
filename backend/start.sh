#!/bin/bash

# 论文评价系统后端启动脚本

echo "======================================"
echo "论文评价检验系统 - 后端启动"
echo "======================================"

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "[1/5] 创建虚拟环境..."
    python -m venv venv
else
    echo "[1/5] 虚拟环境已存在"
fi

# 激活虚拟环境
echo "[2/5] 激活虚拟环境..."
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# 安装依赖
echo "[3/5] 安装依赖..."
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 检查.env文件
if [ ! -f ".env" ]; then
    echo "[4/5] 创建.env文件..."
    cp .env.example .env
    echo "警告: 请编辑.env文件，填入百炼API Key"
else
    echo "[4/5] .env文件已存在"
fi

# 启动服务
echo "[5/5] 启动FastAPI服务..."
echo ""
echo "API文档: http://localhost:8000/docs"
echo "健康检查: http://localhost:8000/health"
echo ""
python -m app.main
