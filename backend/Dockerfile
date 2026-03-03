FROM python:3.9-slim

WORKDIR /app

# 安装系统依赖和中文字体
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    fonts-noto-cjk \
    fonts-wqy-zenhei \
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

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
