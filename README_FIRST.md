# 🚀 论文评价检验系统 - 立即开始

**感觉卡顿了？** → 快速查看：[故障排除清单](TROUBLESHOOTING_CHECKLIST.md)  
**想了解系统原理？** → 详细阅读：[系统架构说明](SYSTEM_ARCHITECTURE_EXPLAINED.md)  
**要完整启动指南？** → 查看：[快速启动指南](QUICK_START_GUIDE.md)  

---

## ⚡ 5分钟快速启动

### 前置要求
- Windows 10+ / Linux / macOS
- Python 3.9+
- Node.js 16+
- Docker（推荐运行 Redis）

### 步骤1：启动 Redis（任务队列）
```bash
docker run -d -p 6379:6379 redis:latest
```

### 步骤2：启动后端（FastAPI）
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# 编辑 .env，添加 API Key
# BAILIAN_API_KEY=sk_xxxxx  或  DEEPSEEK_API_KEY=sk_xxxxx

uvicorn app.main:app --reload
```

### 步骤3：启动任务处理（Celery Worker）
```bash
cd backend
celery -A app.workers.celery_app worker -l info --pool=threads -Q evaluation,proofread,formatter,default
```

### 步骤4：启动前端（Vue）
```bash
cd frontend
npm install
npm run dev
```

### 步骤5：打开浏览器
```
http://localhost:5173
```

---

## 📋 核心概念速览

| 组件 | 端口 | 用途 |
|------|------|------|
| **Redis** | 6379 | 消息队列 + 结果存储 |
| **FastAPI** | 8000 | HTTP API 服务器 |
| **Celery Worker** | - | 后台评价任务执行 |
| **Vue** | 5173 | 前端用户界面 |

## 🔄 数据流

```
用户上传论文
    ↓
FastAPI 接收 → 返回 task_id（1秒内）
    ↓
前端显示进度条
    ↓
Celery Worker 后台执行评价（1-3分钟）
    ↓
完成后显示评价报告
```

---

## ⚠️ 常见问题

### Q: 上传后卡在"正在检测中..."
**A:** 这是**异步任务处理**，不是 Bug。需要检查：
1. ✅ Redis 运行了吗？`redis-cli ping`
2. ✅ Celery Worker 运行了吗？(看启动终端)
3. ✅ API Key 配置了吗？(编辑 .env)

详见：[故障排除](TROUBLESHOOTING_CHECKLIST.md)

### Q: 为什么需要 Celery？
**A:** AI 评价耗时 1-3 分钟，不能让前端等待（会超时）。  
Celery 让评价在**后台执行**，前端通过轮询查看进度。

### Q: API Key 如何获取？
- **阿里云百炼**（推荐）：https://dashscope.aliyun.com
- **DeepSeek**（可选）：https://platform.deepseek.com

### Q: 卡顿时怎么调试？
```bash
cd backend
python check_services.py  # 自动诊断所有服务
```

---

## 📚 详细文档导航

| 文档 | 适用场景 |
|------|---------|
| [快速启动指南](QUICK_START_GUIDE.md) | 完整的分步启动教程 |
| [故障排除清单](TROUBLESHOOTING_CHECKLIST.md) | 遇到问题时快速查阅 |
| [系统架构说明](SYSTEM_ARCHITECTURE_EXPLAINED.md) | 理解系统设计和原理 |
| [诊断报告](DIAGNOSIS_REPORT.md) | 深入的技术分析 |
| [项目说明](CLAUDE.md) | 开发者指南和约定 |

---

## 🎯 使用场景

### 场景1：首次启动系统
1. 按照上面的"5分钟快速启动"操作
2. 打开 http://localhost:5173
3. 上传论文测试

### 场景2：遇到卡顿问题
1. 查看 [故障排除清单](TROUBLESHOOTING_CHECKLIST.md)
2. 运行 `python backend/check_services.py`
3. 按照提示修复问题

### 场景3：想理解系统工作原理
1. 阅读 [系统架构说明](SYSTEM_ARCHITECTURE_EXPLAINED.md)
2. 查看对应的源代码文件

### 场景4：部署到生产环境
```bash
docker-compose -f docker/docker-compose.yml up -d
```

---

## 🛠️ 开发者快速参考

```bash
# 后端开发
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --reload-dirs=app

# 前端开发
cd frontend
npm install
npm run dev

# 运行测试
cd backend
pytest tests/ -v
```

---

## 📞 获得帮助

1. **检查日志**：
   - FastAPI 终端：搜索 `[evaluation]`
   - Celery Worker 终端：搜索 `task` 或 `evaluation`
   - 浏览器控制台（F12）：搜索 `[evaluation`

2. **运行诊断**：
   ```bash
   python backend/check_services.py
   ```

3. **查看详细文档**：
   - [完整诊断报告](DIAGNOSIS_REPORT.md)
   - [系统架构](SYSTEM_ARCHITECTURE_EXPLAINED.md)

---

## 🎨 系统特色

✨ **完整的论文评价系统**
- 智能评价：多维度分析（学术规范、逻辑创新、语言质量、文献规范）
- 错别字检查：AI 驱动的拼写和语法检查
- 模板排版：一键应用多种学术格式
- 论文查重：SimHash + AI 语义增强

🔐 **企业级可靠性**
- 异步任务处理：支持并发
- Redis 持久化：数据不丢失
- Celery 重试机制：失败自动重试
- 详细日志追踪：便于调试

💰 **完整的商业系统**
- 按次购买：¥3/次
- 月度订阅：¥99/月
- 微信/支付宝支付：安全可靠
- 用户管理：权限控制和配额管理

---

## 版本信息

- **系统版本**：2.0.0
- **更新日期**：2026-04-02
- **Python**：3.9+
- **Node.js**：16+
- **主要框架**：FastAPI + Vue 3 + Celery + Redis

---

## 🎓 学习路径

初学者：
1. 启动系统（5 分钟）
2. 测试功能（5 分钟）
3. 查看[快速启动指南](QUICK_START_GUIDE.md)（15 分钟）

中级开发者：
1. 阅读[系统架构说明](SYSTEM_ARCHITECTURE_EXPLAINED.md)（20 分钟）
2. 查看后端源代码（`backend/app/workers/evaluation_tasks.py`）
3. 查看前端源代码（`frontend/src/store/modules/evaluation.js`）

高级开发者：
1. 理解 Celery 任务队列设计
2. 修改评价提示词（`backend/app/core/evaluator/prompts.py`）
3. 扩展支付方式或评价维度

---

**准备好了吗？[现在就开始吧！](QUICK_START_GUIDE.md)** 🚀

---

**需要帮助？**
- 💬 查看 [故障排除清单](TROUBLESHOOTING_CHECKLIST.md)
- 📖 阅读 [系统架构说明](SYSTEM_ARCHITECTURE_EXPLAINED.md)
- 🔧 运行 `python backend/check_services.py`
