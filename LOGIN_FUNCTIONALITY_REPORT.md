# 登录功能诊断报告

## 总体状态

| 功能 | 状态 | 是否可用 |
|------|------|--------|
| 账号密码登录 | ✅ 已配置 | ✅ 可用 |
| 手机号短信登录 | ⚠️ 缺少配置 | ❌ 不可用 |
| 微信扫码登录 | ⚠️ 缺少配置 | ❌ 不可用 |
| 支付宝登录 | ⚠️ 缺少配置 | ❌ 不可用 |

---

## 详细分析

### 1. 账号密码登录 ✅ 可用

**状态**：完整可用

**前端**：`src/views/Login.vue` - "登录"标签
**后端**：`api/v1/auth.py` - `/login` 端点
**配置**：无需外部配置

---

### 2. 手机号短信登录 ❌ **需要配置**

**前端**：✅ 完整
- `src/views/Login.vue` - "手机号登录"标签
- 包含手机号验证、验证码倒计时等完整UI

**后端**：✅ 完整
- `api/v1/auth.py` - `/sms/send` 和 `/sms/login` 端点
- `services/sms_service.py` - 短信发送和验证逻辑

**缺少的配置** ⚠️：
```
# backend/.env 中需要添加
ALIYUN_SMS_ACCESS_KEY=              # 阿里云短信 ACCESS_KEY
ALIYUN_SMS_ACCESS_SECRET=           # 阿里云短信 SECRET
ALIYUN_SMS_SIGN_NAME=               # 短信签名名称
ALIYUN_SMS_TEMPLATE_CODE=           # 短信模板编号
```

**阿里云配置位置**：
1. 登录 https://dysmsapi.aliyun.com
2. 申请短信签名和模板
3. 获取 ACCESS_KEY（在 https://ram.console.aliyun.com）
4. 将值填入 .env

**问题**：
- 如果没有配置，`send_code()` 会调用 `_send_aliyun_sms()` 时异常
- 异常会被捕获，用户看到 "短信发送失败，请稍后再试"

---

### 3. 微信扫码登录 ❌ **需要配置**

**前端**：✅ 完整
- `src/views/Login.vue` 中的微信图标按钮
- 所有标签页都有微信登录选项
- `api/auth.js` 中的 `getWechatLoginUrl()` 函数

**后端**：✅ 完整
- `api/v1/auth.py` - `/wechat/url` 和 `/wechat/callback` 端点
- `services/oauth_service.py` - 微信登录处理逻辑
- 支持通过 code 获取用户信息

**缺少的配置** ⚠️：
```
# backend/.env 中需要添加
WECHAT_APP_SECRET=                  # 微信开放平台 APP 密钥
WECHAT_REDIRECT_URI=http://localhost:8000/api/v1/auth/wechat/callback
```

**微信配置位置**：
1. 登录 https://open.weixin.qq.com/
2. 创建移动应用
3. 获取 APPID（已有：`wx2cb1c82fab0793f8`）
4. 获取 APP 密钥（SECRET）
5. 配置授权回调地址：`http://localhost:8000/api/v1/auth/wechat/callback`

**问题**：
- 如果没有 APP_SECRET，无法通过 code 换取 access_token
- `wechat_code_to_user()` 会在获取 token 时失败
- 用户看不到错误信息，页面静默失败

**前端可能的问题**：
- 微信登录使用 `window.location.href = res.data.url` 重定向
- 如果跳转到微信登录页面，用户会看到"应用未认证"或类似错误

---

### 4. 支付宝登录 ❌ **需要配置**

**前端**：❌ 缺少
- Login.vue 中没有支付宝登录按钮
- 虽然 auth.js 中有 `getAlipayLoginUrl()` 但没有被使用

**后端**：✅ 完整
- `api/v1/auth.py` - `/alipay/url` 和 `/alipay/callback` 端点
- `services/oauth_service.py` - 支付宝登录处理逻辑

**缺少的配置** ⚠️：
```
# backend/.env 中需要添加
ALIPAY_REDIRECT_URI=http://localhost:8000/api/v1/auth/alipay/callback
```

**注意**：
- ALIPAY_APP_ID 已配置：`2021005115637729`
- 支付宝的私钥和公钥已创建在 `storage/alipay/`

---

## 短信发送流程

```
用户输入手机号 → 点击"发送验证码"
    ↓
调用 POST /api/v1/auth/sms/send { phone }
    ↓
服务端验证手机号 + Redis 冷却检查
    ↓
生成6位随机验证码
    ↓
调用阿里云短信 API 发送短信
    ❌ 失败：无法连接或配置错误
    ↓ ✅ 成功
验证码存储到 Redis（5分钟过期）
    ↓
返回 {"success": true, "message": "验证码已发送"}
    ↓
用户输入验证码 → 点击"登录"
    ↓
调用 POST /api/v1/auth/sms/login { phone, code, invite_code? }
    ↓
服务端验证码验证
    ❌ 失败：验证码错误或已过期
    ✅ 成功：
        - 查询或创建用户
        - 返回 access_token
```

---

## 微信登录流程

```
用户点击微信按钮
    ↓
调用 GET /api/v1/auth/wechat/url
    ↓
返回微信授权 URL
    ↓
前端重定向到微信登录页面
    ↓
用户扫码确认
    ↓
微信重定向回 /api/v1/auth/wechat/callback?code=xxx&state=login
    ↓
服务端用 code 换取 access_token
    ❌ 失败：无 APP_SECRET 配置或 SECRET 错误
    ✓ 成功：
        ↓
        用 access_token 获取用户信息 (openid, nickname, avatar)
        ↓
        查询或创建用户（通过 wechat_openid）
        ↓
        返回本系统的 access_token
        ↓
        前端跳转到首页
```

---

## 修复步骤

### 步骤 1：获取阿里云短信配置
1. 登录 https://dysmsapi.aliyun.com/
2. 左侧菜单 → "设置" → 获取 Access Key ID 和 Secret
3. 创建短信签名（需要验证）
4. 创建短信模板（需要审核，通常1-2小时）
5. 记录：
   - Access Key ID
   - Secret
   - 签名名称
   - 模板编号

### 步骤 2：获取微信开放平台配置
1. 登录 https://open.weixin.qq.com/
2. 已有 APPID: `wx2cb1c82fab0793f8`
3. 进入应用设置
4. 获取 "App Secret"
5. 在"发布"页面配置授权回调地址
6. 添加：`http://localhost:8000/api/v1/auth/wechat/callback`

### 步骤 3：更新 .env 文件
```bash
# 短信配置
ALIYUN_SMS_ACCESS_KEY=<从阿里云获取>
ALIYUN_SMS_ACCESS_SECRET=<从阿里云获取>
ALIYUN_SMS_SIGN_NAME=<您的签名名称>
ALIYUN_SMS_TEMPLATE_CODE=<您的模板编号>

# 微信登录配置
WECHAT_APP_SECRET=<从微信开放平台获取>
WECHAT_REDIRECT_URI=http://localhost:8000/api/v1/auth/wechat/callback

# 支付宝登录配置（可选）
ALIPAY_REDIRECT_URI=http://localhost:8000/api/v1/auth/alipay/callback
```

### 步骤 4：重启后端服务
```bash
cd backend
uvicorn app.main:app --reload
```

---

## 当前可用的登录方式

✅ **账号密码登录** - 直接可用，无需额外配置

---

## 当前不可用的登录方式

❌ **手机号短信登录** - 需要阿里云短信配置
❌ **微信扫码登录** - 需要微信 APP Secret
❌ **支付宝登录** - 需要支付宝回调地址配置

---

## Redis 依赖

短信服务依赖 Redis：
- 验证码存储：`sms:code:{phone}`（5分钟过期）
- 发送冷却：`sms:cd:{phone}`（60秒）
- 每日计数：`sms:daily:{phone}`（24小时）

确保 Redis 在运行：
```bash
# Redis 服务器应该在 localhost:6379
# 配置：CELERY_BROKER_URL=redis://localhost:6379/0
```

---

## 测试建议

### 测试账号密码登录
1. 在管理后台创建用户或使用默认用户 `admin:admin123`
2. 访问 http://localhost:5173/login
3. 输入用户名密码，应该能成功登录

### 测试手机号登录（配置完成后）
1. 输入手机号 13800138000
2. 点击"发送验证码"
3. 查看手机短信，应收到 6 位验证码
4. 输入验证码登录

### 测试微信登录（配置完成后）
1. 点击微信登录按钮
2. 应跳转到微信扫码登录页面
3. 用微信扫描二维码
4. 确认授权后应自动登录

---

## 相关配置文件路径

| 文件 | 用途 |
|------|------|
| `backend/.env` | 所有环境变量配置 |
| `backend/app/config.py` | 配置类定义 |
| `backend/app/services/sms_service.py` | 短信发送实现 |
| `backend/app/services/oauth_service.py` | 第三方登录实现 |
| `frontend/src/views/Login.vue` | 登录页面 UI |
| `frontend/src/api/auth.js` | 前端 API 调用 |
