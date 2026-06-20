# 微信登录 - 快速开始指南

## 已完成的配置

✅ 微信公众号凭证已配置到 `backend/.env`：
```
WECHAT_LOGIN_APP_ID=wx1dd36333719608b4
WECHAT_APP_SECRET=0cb4744497a19ef7b6d6a74428853b57
```

✅ 后端微信登录端点已实现（在 `backend/app/api/v1/auth.py`）：
- `GET /api/v1/auth/wechat/url` - 获取微信登录二维码 URL
- `GET /api/v1/auth/wechat/callback` - 微信授权回调

✅ 前端微信回调处理已创建（`frontend/src/views/WechatCallback.vue`）

✅ 路由已配置（`frontend/src/router/index.js`）

---

## 快速测试步骤

### 1️⃣ 启动后端

```bash
cd backend
python -m venv venv
venv\Scripts\activate              # Windows
# source venv/bin/activate         # Linux/Mac
pip install -r requirements.txt
python -m app.main
```

**确认输出：**
```
===================================================
  论文评价检验系统  v2.0.0  启动
  API 文档: http://localhost:8000/docs
  ...
===================================================
```

### 2️⃣ 启动前端

在新的终端窗口：

```bash
cd frontend
npm install
npm run dev
```

**确认输出：**
```
VITE v4.x.x  ready in xxx ms
➜  Local:   http://localhost:5173/
```

### 3️⃣ 验证微信登录 URL 生成

打开浏览器，访问：
```
http://localhost:8000/api/v1/auth/wechat/url
```

应该看到类似的响应：
```json
{
  "url": "https://open.weixin.qq.com/connect/qrconnect?appid=wx1dd36333719608b4&redirect_uri=http%3A%2F%2Flocalhost%3A8000%2Fapi%2Fv1%2Fauth%2Fwechat%2Fcallback&response_type=code&scope=snsapi_login&state=login#wechat_redirect"
}
```

### 4️⃣ 前端登录页面测试

打开前端：
```
http://localhost:5173/login
```

你应该看到：
- ✅ 登录表单
- ✅ 手机号登录标签页
- ✅ 注册标签页
- ✅ **微信登录按钮**（绿色的微信图标）

### 5️⃣ 点击微信登录按钮

1. 点击 Login.vue 中的微信图标
2. 应该跳转到微信扫码授权页面（或微信 Web 登录界面）
3. 用你的微信账号授权
4. 自动跳转回 `http://localhost:5173/auth/wechat/callback?code=xxx&state=login`
5. 显示 "登录成功" 提示
6. 2 秒后自动跳转回首页

---

## 现有实现的完整流程

```
用户点击微信登录按钮
         ↓
前端 -> /api/v1/auth/wechat/url 获取授权 URL
         ↓
跳转到微信扫码授权页面 (open.weixin.qq.com)
         ↓
用户扫码授权
         ↓
微信服务器重定向回：localhost:8000/api/v1/auth/wechat/callback?code=xxx
         ↓
后端验证 code，调用微信 API 获取用户信息
         ↓
在数据库中查找或创建用户（基于 openid）
         ↓
返回 JWT token
         ↓
前端保存 token 到 localStorage
         ↓
自动跳转回首页
```

---

## 数据库验证

微信登录成功后，会在 SQLite 数据库中创建用户记录。

### 查看创建的微信用户

```bash
cd backend
sqlite3 storage/paper_check.db

# 在 sqlite3 命令行中执行：
SELECT id, username, wechat_openid, nickname, created_at FROM user WHERE wechat_openid IS NOT NULL;
```

输出示例：
```
1|wx_abc12345|o1234567890abcdef|张三|2025-04-08 10:30:45
```

---

## 常见问题速查

| 问题 | 原因 | 解决方案 |
|------|------|--------|
| 点击微信登录无反应 | WECHAT_APP_ID 为空或格式错误 | 检查 `.env` 文件中的 WECHAT_APP_ID |
| "Invalid redirect_uri" | 回调地址不匹配 | 确保 WECHAT_REDIRECT_URI = http://localhost:8000/api/v1/auth/wechat/callback |
| code 已过期 | 授权 code 有效期 10 分钟 | 重新扫码 |
| CORS 错误 | 跨域配置问题 | 检查 `config.py` 中的 CORS_ORIGINS |
| 回调页面显示错误 | 网络问题或后端故障 | 查看浏览器控制台和后端日志 |

---

## 日志查看

查看实时日志，以便调试：

```bash
cd backend
tail -f logs/app_*.log
```

关键日志内容包括：
- 微信 API 调用记录
- 用户创建记录
- Token 生成记录

---

## 生产部署准备

当准备上线时，更新 `.env`：

```env
# 开发环境（当前配置）
WECHAT_REDIRECT_URI=http://localhost:8000/api/v1/auth/wechat/callback

# 生产环境（修改为实际域名）
WECHAT_REDIRECT_URI=https://your-domain.com/api/v1/auth/wechat/callback
```

同时在微信开放平台网站添加生产域名到回调域名白名单。

---

## 扩展

如需支持以下功能，已预留代码框架：
- ✅ 账号绑定微信（见 WECHAT_LOGIN_SETUP.md）
- ✅ 支付宝登录（配置方式相同）
- ✅ 手机号登录（已实现）
- ✅ 邮箱注册（已实现）

---

## 技术栈

| 层 | 技术 | 文件 |
|----|------|------|
| API | FastAPI + OAuth2 | `backend/app/api/v1/auth.py` |
| Service | httpx + 微信 API | `backend/app/services/oauth_service.py` |
| DB | SQLAlchemy ORM | `backend/app/models/user.py` |
| 前端 | Vue 3 + axios | `frontend/src/views/WechatCallback.vue` |
| Auth | JWT | `backend/app/api/v1/auth.py` (line 79-83) |

---

## 下一步

1. 测试微信登录流程
2. 验证用户是否正确创建
3. 检查 token 是否正确保存
4. 测试已登录用户访问受保护的路由（如 /evaluation）

祝你测试顺利！🎉
