FROM python:3.9-slim

WORKDIR /app

# 安装系统依赖和中文字体
# libreoffice-core + libreoffice-writer: 用于归一化 WPS 生成的 .docx
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    fonts-noto-cjk \
    fonts-wqy-zenhei \
    libreoffice-core \
    libreoffice-writer \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 清除 matplotlib 字体缓存，让它重新扫描字体
RUN rm -rf /root/.cache/matplotlib

# 复制应用代码
COPY . .

# 创建存储目录
RUN mkdir -p storage/uploads storage/outputs storage/temp logs

# 暴露端口
EXPOSE 8000

# 启动命令：gunicorn 多进程 + uvicorn worker
# --workers 16：32核服务器，API接收层 16进程
# --worker-class：每个进程用 uvicorn 异步事件循环
# --timeout 120：AI任务耗时长，防止 gunicorn 误杀
CMD ["gunicorn", "app.main:app", \
     "--workers", "16", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", \
     "--timeout", "120", \
     "--keep-alive", "5"]
