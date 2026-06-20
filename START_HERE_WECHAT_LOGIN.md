# 🚀 微信登录 - 从这里开始

你的微信登录**已经完全配置好了**！这是一份 3 分钟的快速指南。

---

## ⚡ 快速开始（3 步）

### Step 1: 启动后端
```bash
cd backend
python -m app.main
```

你应该看到：
```
===================================================
  论文评价检验系统  v2.0.0  启动
  API 文档: http://localhost:8000/docs
===================================================
```

### Step 2: 启动前端（新终端）
```bash
cd frontend
npm run dev
```

你应该看到：
```
VITE v4.x.x  ready in xxx ms
➜  Local:   http://localhost:5173/
```

### Step 3: 测试微信登录
1. 打开 http://localhost:5173/login
2. 点击绿色的**微信图标**按钮
3. 扫描二维码（或用你的微信账号授权）
4. ✅ 自动登录到首页

---

## ✨ 这一刻发生了什么

```
你点击微信登录
    ↓
你的微信扫描二维码
    ↓
微信服务器验证你的身份
    ↓
自动创建账号（首次）
    ↓
自动分配试用额度
    ↓
生成 JWT token
    ↓
自动登录并跳转
```

---

## 📊 验证成功

### 在数据库中查看你创建的用户

```bash
cd backend
sqlite3 storage/paper_check.db
SELECT id, username, wechat_openid, nickname FROM user LIMIT 10;
```

你会看到类似的输出：
```
1|wx_abc12345|o1234567890abcdef|张三
```

---

## 🎯 已配置的内容

✅ **微信凭证** (backend/.env)
```
WECHAT_LOGIN_APP_ID=wx1dd36333719608b4
WECHAT_APP_SECRET=0cb4744497a19ef7b6d6a74428853b57
```

✅ **后端 API** (backend/app/api/v1/auth.py)
- `/api/v1/auth/wechat/url` - 获取二维码
- `/api/v1/auth/wechat/callback` - 处理回调

✅ **前端页面** (frontend/src/)
- `views/Login.vue` - 登录页面（含微信按钮）
- `views/WechatCallback.vue` - 回调处理（新创建）
- `router/index.js` - 路由配置（已更新）

---

## 🐛 遇到问题？

### 问题：点击微信登录无反应

**解决**：检查后端是否正确启动
```bash
# 在后端终端按 Ctrl+C 停止，然后重新启动
python -m app.main
```

### 问题：显示"微信授权失败"

**解决**：检查 `.env` 文件中的凭证是否正确复制
```bash
grep WECHAT_APP backend/.env
```

应该看到：
```
WECHAT_LOGIN_APP_ID=wx1dd36333719608b4
WECHAT_APP_SECRET=0cb4744497a19ef7b6d6a74428853b57
```

### 问题：前端显示空白页或 404

**解决**：检查前端是否正确启动
```bash
# 在前端终端按 Ctrl+C 停止，然后重新启动
npm run dev
```

---

## 📚 了解更多

需要详细信息？查看以下文档：

| 文档 | 内容 | 阅读时间 |
|------|------|--------|
| **WECHAT_LOGIN_QUICK_START.md** | 完整测试指南 | 5 分钟 |
| **WECHAT_LOGIN_SETUP.md** | 配置和部署说明 | 15 分钟 |
| **WECHAT_LOGIN_IMPLEMENTATION_SUMMARY.md** | 技术总结 | 10 分钟 |
| **WECHAT_LOGIN_CHANGES_SUMMARY.md** | 代码改动清单 | 5 分钟 |

---

## 🎯 现在你可以做什么

✅ **测试微信登录** - 已完全就绪  
✅ **验证用户创建** - 自动创建并分配试用额度  
✅ **访问受保护页面** - 如 /evaluation（论文评价）  
✅ **查看日志** - tail -f backend/logs/app_*.log  

---

## 🔐 安全提醒

✅ **已做好的安全措施**：
- App Secret 保密存储在 `.env`
- JWT token 自动加密
- 密码使用 bcrypt 哈希
- 禁用账号无法登录

⚠️ **生产环境需要**：
- 修改 `SECRET_KEY` 为随机字符串
- 使用 HTTPS 协议
- 更新回调地址为生产域名

---

## 💡 下一步建议

1. ✅ **现在** - 按上面的 3 步快速测试
2. 🔍 **然后** - 验证用户是否创建成功
3. 📚 **接着** - 阅读 WECHAT_LOGIN_QUICK_START.md 了解详情
4. 🚀 **最后** - 按 WECHAT_LOGIN_SETUP.md 进行生产部署

---

## ❓ 常见问题

**Q: 需要配置微信开放平台吗？**
A: 不需要，凭证已经配置好了。你可以直接测试。

**Q: 支持支付宝登录吗？**
A: 支持！框架完全相同，参考 WECHAT_LOGIN_SETUP.md 中的扩展部分。

**Q: 用户数据会保存在哪里？**
A: SQLite 数据库，路径：`backend/storage/paper_check.db`

**Q: Token 有效期多长？**
A: 默认 7 天，可在 `backend/app/config.py` 中修改 `ACCESS_TOKEN_EXPIRE_MINUTES`

**Q: 能否将微信绑定到现有账号？**
A: 可以，框架已预留支持，见 WECHAT_LOGIN_SETUP.md

---

## 🎉 就是这样！

你的微信登录已完全就绪。现在就去测试吧！

有任何问题，查看对应的文档或检查后端日志：
```bash
tail -f backend/logs/app_*.log
```

**祝你使用愉快！** 🚀
