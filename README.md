# 论文评价检验系统

基于百炼大模型的论文质量检测、智能评价和格式规范化一站式解决方案。

## 功能特性

### 核心功能

1. **错别字及标点检查**
   - 自动检测论文中的错别字、标点符号错误
   - 使用Word修订模式标注，不改变原文内容
   - 支持空格规范、专业术语检查

2. **智能评价**
   - 调用阿里云百炼大模型API进行多维度评价
   - 四大评价维度：
     - 学术规范性
     - 逻辑与创新性
     - 语言质量
     - 文献引用规范性
   - 生成详细评价报告（Word/PDF）

3. **模板排版**（V2.0）
   - 支持用户上传论文模板
   - 内置常见高校/期刊模板库
   - 自动识别论文结构并应用格式

## 技术架构

### 后端
- **框架**: FastAPI
- **文档处理**: python-docx
- **AI调用**: 阿里云百炼（通义千问）
- **任务队列**: Celery + Redis
- **数据库**: MySQL 8.0

### 前端
- **框架**: Vue 3 + Vite
- **UI库**: Element Plus
- **图表**: ECharts
- **状态管理**: Pinia

### 部署
- **容器化**: Docker + Docker Compose
- **Web服务器**: Nginx
- **缓存**: Redis

## 快速开始

### 环境要求

- Python 3.9+
- Node.js 18+
- MySQL 8.0+（可选）
- Redis 7.0+（可选）

### 1. 克隆项目

```bash
git clone <repository-url>
cd pdf_check
```

### 2. 后端配置

```bash
cd backend

# 创建虚拟环境
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
copy .env.example .env  # Windows
# cp .env.example .env  # Linux/Mac

# 编辑.env文件，填入百炼API Key
# BAILIAN_API_KEY=your_api_key_here

# 后端启动服务
 python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

后端将运行在 http://localhost:8000

API文档：http://localhost:8000/docs

### 3. 前端配置

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端将运行在 http://localhost:5173

### 4. Docker部署（推荐）

```bash
# 配置环境变量
copy backend\.env.example backend\.env
# 编辑backend\.env，填入配置

# 构建并启动所有服务
docker-compose -f docker/docker-compose.yml up -d

# 查看日志
docker-compose -f docker/docker-compose.yml logs -f
```

## 项目结构

```
pdf_check/
├── backend/                 # 后端服务
│   ├── app/
│   │   ├── api/            # API接口
│   │   ├── core/           # 核心业务逻辑
│   │   │   ├── evaluator/  # 智能评价（含提示词）
│   │   │   ├── spell_checker/  # 错别字检查
│   │   │   └── formatter/  # 模板排版
│   │   ├── services/       # 服务层
│   │   └── schemas/        # 数据模型
│   └── storage/            # 文件存储
├── frontend/               # 前端服务
│   ├── src/
│   │   ├── views/         # 页面
│   │   ├── components/    # 组件
│   │   └── api/           # API调用
├── docker/                # Docker配置
└── docs/                  # 文档
```

详细结构见：[PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)

## 配置说明

### 百炼API配置

在`backend/.env`中配置：

```env
BAILIAN_API_KEY=your_api_key_here
BAILIAN_MODEL=qwen-max
```

获取API Key：https://dashscope.aliyun.com/

### 文件存储配置

```env
MAX_FILE_SIZE=20  # 最大文件大小（MB）
FILE_RETENTION_HOURS=24  # 文件保留时间（小时）
```

文件将在上传后24小时自动清理。

## 文档

- [PRD文档](docs/PRD_论文评价检验系统.md)
- [项目结构说明](PROJECT_STRUCTURE.md)
- [创建报告](CREATION_REPORT.md)
- [API文档](http://localhost:8000/docs)

## 开发路线

### V1.0（当前版本）
- [x] 项目结构搭建
- [x] 提示词模板
- [ ] 错别字检查功能
- [ ] 智能评价功能

### V2.0（计划中）
- [ ] 模板排版功能
- [ ] 用户系统
- [ ] 历史记录

### V3.0（未来）
- [ ] 批量处理
- [ ] 移动端适配
- [ ] 英文论文支持

## 许可证

MIT License

---

**注意**：本项目调用阿里云百炼大模型API，需要自行申请API Key并承担相应费用。
