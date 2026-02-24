# 论文评价检验系统 - 项目目录结构

## 完整目录树

```
pdf_check/
├── backend/                          # 后端服务（FastAPI）
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                   # FastAPI应用入口
│   │   ├── config.py                 # 配置文件（API Key、数据库等）
│   │   │
│   │   ├── api/                      # API路由层
│   │   │   ├── __init__.py
│   │   │   ├── v1/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── endpoints/
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── spell_check.py      # 错别字检查API
│   │   │   │   │   ├── evaluation.py       # 智能评价API
│   │   │   │   │   └── formatting.py       # 模板排版API
│   │   │   │   └── router.py              # 路由汇总
│   │   │
│   │   ├── core/                     # 核心业务逻辑层
│   │   │   ├── __init__.py
│   │   │   ├── spell_checker/        # 功能一：错别字检查
│   │   │   │   ├── __init__.py
│   │   │   │   ├── detector.py       # 检测算法（错别字、标点）
│   │   │   │   ├── corrector.py      # 修正建议生成
│   │   │   │   ├── docx_handler.py   # Word文档解析和修订标注
│   │   │   │   └── rules/            # 检测规则
│   │   │   │       ├── __init__.py
│   │   │   │       ├── typo_dict.json       # 错别字词典
│   │   │   │       ├── punctuation.py       # 标点规则
│   │   │   │       └── spacing.py           # 空格规范
│   │   │   │
│   │   │   ├── evaluator/            # 功能二：智能评价
│   │   │   │   ├── __init__.py
│   │   │   │   ├── bailian_client.py # 百炼API调用客户端
│   │   │   │   ├── prompts.py        # 提示词模板（硬编码）
│   │   │   │   ├── report_generator.py # 评价报告生成
│   │   │   │   └── chart_generator.py  # 雷达图生成
│   │   │   │
│   │   │   └── formatter/            # 功能三：模板排版
│   │   │       ├── __init__.py
│   │   │       ├── template_parser.py   # 模板解析
│   │   │       ├── structure_recognizer.py # 论文结构识别
│   │   │       ├── style_applier.py     # 样式应用
│   │   │       └── template_library/    # 预设模板库
│   │   │           ├── default_thesis.docx
│   │   │           └── README.md
│   │   │
│   │   ├── models/                   # 数据模型（可选，如需数据库）
│   │   │   ├── __init__.py
│   │   │   ├── user.py              # 用户模型
│   │   │   └── task.py              # 任务记录模型
│   │   │
│   │   ├── schemas/                  # Pydantic数据验证模型
│   │   │   ├── __init__.py
│   │   │   ├── spell_check.py       # 错别字检查请求/响应模型
│   │   │   ├── evaluation.py        # 评价请求/响应模型
│   │   │   └── formatting.py        # 排版请求/响应模型
│   │   │
│   │   ├── services/                 # 服务层（处理复杂业务逻辑）
│   │   │   ├── __init__.py
│   │   │   ├── file_service.py      # 文件上传/下载/清理
│   │   │   ├── task_service.py      # 异步任务管理（Celery）
│   │   │   └── cache_service.py     # Redis缓存服务
│   │   │
│   │   └── utils/                    # 工具函数
│   │       ├── __init__.py
│   │       ├── file_utils.py        # 文件操作工具
│   │       ├── logger.py            # 日志配置
│   │       └── exceptions.py        # 自定义异常
│   │
│   ├── tests/                        # 测试代码
│   │   ├── __init__.py
│   │   ├── test_spell_check.py
│   │   ├── test_evaluation.py
│   │   └── test_formatting.py
│   │
│   ├── storage/                      # 文件存储目录
│   │   ├── uploads/                 # 用户上传文件
│   │   ├── outputs/                 # 处理结果文件
│   │   └── temp/                    # 临时文件
│   │
│   ├── requirements.txt              # Python依赖
│   ├── Dockerfile                    # Docker配置
│   └── .env.example                  # 环境变量示例
│
├── frontend/                         # 前端服务（Vue 3）
│   ├── public/
│   │   ├── index.html
│   │   └── favicon.ico
│   │
│   ├── src/
│   │   ├── main.js                   # 入口文件
│   │   ├── App.vue
│   │   │
│   │   ├── assets/                   # 静态资源
│   │   │   ├── images/
│   │   │   └── styles/
│   │   │       └── global.css
│   │   │
│   │   ├── components/               # 通用组件
│   │   │   ├── FileUpload.vue        # 文件上传组件
│   │   │   ├── ProgressBar.vue       # 进度条组件
│   │   │   ├── RadarChart.vue        # 雷达图组件
│   │   │   └── ResultCard.vue        # 结果展示卡片
│   │   │
│   │   ├── views/                    # 页面视图
│   │   │   ├── Home.vue              # 首页（功能入口）
│   │   │   ├── SpellCheck.vue        # 错别字检查页面
│   │   │   ├── Evaluation.vue        # 智能评价页面
│   │   │   ├── Formatting.vue        # 模板排版页面
│   │   │   └── History.vue           # 历史记录页面（可选）
│   │   │
│   │   ├── router/                   # 路由配置
│   │   │   └── index.js
│   │   │
│   │   ├── store/                    # 状态管理（Pinia）
│   │   │   ├── index.js
│   │   │   └── modules/
│   │   │       ├── task.js           # 任务状态管理
│   │   │       └── user.js           # 用户状态（可选）
│   │   │
│   │   ├── api/                      # API调用封装
│   │   │   ├── index.js
│   │   │   ├── spellCheck.js
│   │   │   ├── evaluation.js
│   │   │   └── formatting.js
│   │   │
│   │   └── utils/                    # 工具函数
│   │       ├── request.js            # Axios封装
│   │       └── fileUtils.js          # 文件处理工具
│   │
│   ├── package.json
│   ├── vite.config.js                # Vite配置
│   └── .env.example
│
├── database/                         # 数据库相关
│   ├── migrations/                   # 数据库迁移脚本
│   └── init.sql                      # 初始化SQL
│
├── docker/                           # Docker配置
│   ├── docker-compose.yml            # 容器编排
│   ├── nginx/
│   │   └── nginx.conf                # Nginx配置
│   └── redis/
│       └── redis.conf
│
├── docs/                             # 文档
│   ├── PRD_论文评价检验系统.md       # PRD文档（已创建）
│   ├── API文档.md                    # API接口文档
│   └── 部署指南.md
│
├── scripts/                          # 脚本工具
│   ├── clean_files.sh                # 定时清理临时文件
│   └── init_db.sh                    # 数据库初始化
│
├── .gitignore
├── README.md                         # 项目说明
└── LICENSE
```

---

## 目录说明

### 后端（backend/）

#### 1. app/api/ - API路由层
- 负责接收HTTP请求、参数验证、返回响应
- 按版本划分（v1/），便于未来API升级
- 三个核心endpoint对应三个功能模块

#### 2. app/core/ - 核心业务逻辑层
**spell_checker/** - 错别字检查模块
- `detector.py`: 实现错别字、标点、空格检测算法
- `docx_handler.py`: 使用python-docx进行Word解析和修订标注
- `rules/`: 存储检测规则和词典

**evaluator/** - 智能评价模块
- `bailian_client.py`: 封装百炼API调用逻辑
- `prompts.py`: 硬编码4个维度的提示词模板
- `report_generator.py`: 生成Word评价报告
- `chart_generator.py`: 使用matplotlib生成雷达图

**formatter/** - 模板排版模块
- `template_parser.py`: 解析Word模板样式
- `structure_recognizer.py`: 识别论文结构（标题、章节等）
- `style_applier.py`: 将模板样式应用到论文
- `template_library/`: 存放预设模板文件

#### 3. app/services/ - 服务层
- `file_service.py`: 文件上传/下载/24小时自动清理
- `task_service.py`: Celery异步任务管理
- `cache_service.py`: Redis缓存操作

#### 4. app/schemas/ - 数据模型
- 使用Pydantic定义API请求/响应的数据结构
- 自动进行数据验证和文档生成

---

### 前端（frontend/）

#### 1. src/views/ - 页面视图
- `Home.vue`: 首页，展示三个功能入口卡片
- `SpellCheck.vue`: 错别字检查页面（上传→检测→下载修订版）
- `Evaluation.vue`: 智能评价页面（上传→评价→查看报告→下载）
- `Formatting.vue`: 模板排版页面（上传论文+选择模板→排版→下载）

#### 2. src/components/ - 通用组件
- `FileUpload.vue`: 可复用的文件上传组件（拖拽支持）
- `ProgressBar.vue`: 处理进度展示
- `RadarChart.vue`: 评价维度雷达图展示

#### 3. src/api/ - API调用
- 封装所有后端API调用
- 统一错误处理和loading状态管理

---

## 技术栈对应

| 目录/文件 | 技术栈 |
|----------|--------|
| backend/app/ | FastAPI |
| backend/app/core/spell_checker/ | python-docx, pycorrector |
| backend/app/core/evaluator/ | requests（百炼API）, matplotlib |
| backend/app/core/formatter/ | python-docx |
| backend/app/services/task_service.py | Celery + Redis |
| frontend/src/ | Vue 3 + Vite |
| frontend/src/components/ | Element Plus / Ant Design Vue |
| frontend/src/api/ | Axios |
| database/ | MySQL / PostgreSQL |
| docker/ | Docker + Nginx |

---

## 关键文件说明

### 后端关键文件

**backend/app/config.py**
```python
# 存储配置信息
BAILIAN_API_KEY = "..."
BAILIAN_ENDPOINT = "..."
DATABASE_URL = "..."
REDIS_URL = "..."
FILE_STORAGE_PATH = "./storage"
FILE_RETENTION_HOURS = 24
```

**backend/app/core/evaluator/prompts.py**
```python
# 硬编码4个维度的提示词模板
PROMPT_ACADEMIC_STANDARD = """
你是一位资深的学术专家...
论文标题：{{title}}
论文内容：{{content}}
...
"""

PROMPT_LOGIC_INNOVATION = """..."""
PROMPT_LANGUAGE_QUALITY = """..."""
PROMPT_CITATION_STANDARD = """..."""
```

**backend/requirements.txt**
```
fastapi==0.104.1
uvicorn==0.24.0
python-docx==1.0.0
pycorrector==0.9.0
requests==2.31.0
matplotlib==3.8.0
celery==5.3.4
redis==5.0.1
sqlalchemy==2.0.23
pydantic==2.5.0
python-multipart==0.0.6
```

### 前端关键文件

**frontend/package.json**
```json
{
  "dependencies": {
    "vue": "^3.3.4",
    "vue-router": "^4.2.5",
    "pinia": "^2.1.7",
    "axios": "^1.6.0",
    "element-plus": "^2.4.4",
    "echarts": "^5.4.3"
  }
}
```

---

## Docker部署结构

**docker/docker-compose.yml**
```yaml
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    depends_on:
      - db
      - redis

  frontend:
    build: ./frontend
    ports:
      - "80:80"

  db:
    image: mysql:8.0
    volumes:
      - db_data:/var/lib/mysql

  redis:
    image: redis:7.2

  nginx:
    image: nginx:alpine
    volumes:
      - ./docker/nginx/nginx.conf:/etc/nginx/nginx.conf
    ports:
      - "80:80"
```

---

## MVP（V1.0）开发顺序建议

### 第一阶段（Week 1-2）：基础框架搭建
1. 初始化后端FastAPI项目，配置基础路由
2. 初始化前端Vue项目，配置路由和UI框架
3. 搭建Docker开发环境

### 第二阶段（Week 3-4）：功能一开发
1. 后端：实现错别字检测逻辑（`spell_checker/`）
2. 后端：实现Word修订标注功能
3. 前端：开发SpellCheck.vue页面
4. 联调测试

### 第三阶段（Week 5-6）：功能二开发
1. 后端：对接百炼API（`bailian_client.py`）
2. 后端：实现评价报告生成（`report_generator.py`）
3. 前端：开发Evaluation.vue页面
4. 联调测试

### 第四阶段（Week 7-8）：优化与上线
1. 文件上传/下载优化
2. 错误处理和用户提示
3. 性能测试和优化
4. 部署上线

---

## 下一步建议

1. **创建项目骨架**：使用脚本自动生成目录结构
2. **初始化Git仓库**：版本控制
3. **配置开发环境**：Python虚拟环境、Node.js环境
4. **编写README.md**：项目说明和快速开始指南

需要我帮你生成：
- [ ] 自动创建目录结构的脚本
- [ ] requirements.txt详细依赖列表
- [ ] docker-compose.yml配置文件
- [ ] 示例代码文件（如prompts.py、bailian_client.py）
- [ ] README.md项目说明

请告诉我你想先生成哪部分！
