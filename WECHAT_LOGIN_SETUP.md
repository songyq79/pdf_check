# 微信扫码登录完整配置指南

## 概述

你的项目已经有完整的微信登录实现框架，包括：
- ✅ 后端 API 端点：`/api/v1/auth/wechat/url` 和 `/api/v1/auth/wechat/callback`
- ✅ 前端 UI：Login.vue 中的微信登录按钮
- ✅ 服务层：`oauth_service.py` 中的微信认证逻辑
- ✅ 数据库支持：User 模型已包含 `wechat_openid` 字段

**剩余工作**：只需配置微信开放平台的凭证。

---

## Step 1: 在微信开放平台申请 App

### 1.1 申请地址
访问 [微信开放平台](https://open.weixin.qq.com/) 并登录

### 1.2 申请网站应用
- 进入 **管理中心** → **网站应用**
- 点击 **创建网站应用**
- 填写基本信息（企业名称、应用名称等）
- **需要通过企业资质认证**（个人认证不支持扫码登录）

### 1.3 获取凭证
申请通过后，进入应用详情页面，你会看到：
```
App ID：wx****（例如 wxe4f4bbf0f3f38d81）
App Secret：****（长字符串，务必保密）
```

### 1.4 配置回调地址
在微信开放平台应用设置中，配置以下 **授权回调域名**（不要包含 http:// 和路径）：
```
localhost:8000        （开发环境）
your-domain.com       （生产环境）
```

---

## Step 2: 配置后端环境变量

编辑 `backend/.env` 文件，添加或更新以下配置：

```env
# ── 微信登录（开放平台）──────────────────────────────
WECHAT_LOGIN_APP_ID=wx****（从微信开放平台复制）
WECHAT_APP_SECRET=****（从微信开放平台复制）
WECHAT_REDIRECT_URI=http://localhost:8000/api/v1/auth/wechat/callback
```

### 生产环境配置
如果部署到生产服务器，修改 `WECHAT_REDIRECT_URI` 为：
```
https://your-domain.com/api/v1/auth/wechat/callback
```

---

## Step 3: 配置前端回调处理

前端登录后会从微信重定向回来，带有 `code` 和 `state` 参数。

### 3.1 修改 `frontend/src/router/index.js`，添加回调路由

找到路由配置，在 routes 数组中添加：

```javascript
{
  path: '/auth/wechat/callback',
  name: 'WechatCallback',
  component: () => import('@/views/WechatCallback.vue'),
  meta: { requiresAuth: false }
}
```

### 3.2 创建回调处理组件

创建新文件 `frontend/src/views/WechatCallback.vue`：

```vue
<template>
  <div class="callback-page">
    <el-result
      :icon="statusIcon"
      :title="statusTitle"
      :sub-title="statusMessage"
    >
      <template #extra>
        <el-button type="primary" @click="handleRedirect">
          {{ buttonText }}
        </el-button>
      </template>
    </el-result>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/store/modules/auth'
import { ElMessage } from 'element-plus'
import axios from 'axios'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const isLoading = ref(true)
const isSuccess = ref(false)
const errorMessage = ref('')

const statusIcon = computed(() => isSuccess.value ? 'success' : 'error')
const statusTitle = computed(() => isSuccess.value ? '登录成功' : '登录失败')
const statusMessage = computed(() => isSuccess.value ? '即将跳转到首页...' : errorMessage.value)
const buttonText = computed(() => isSuccess.value ? '返回首页' : '重新登录')

async function processCallback() {
  const code = route.query.code
  const state = route.query.state || 'login'

  if (!code) {
    errorMessage.value = '无效的回调参数'
    isLoading.value = false
    return
  }

  try {
    // 后端验证 code 并创建用户 + 返回 token
    const response = await axios.get('/api/v1/auth/wechat/callback', {
      params: { code, state }
    })

    const token = response.data.access_token
    await authStore.loginWithToken(token)
    
    isSuccess.value = true
    ElMessage.success('微信登录成功')
    
    // 2秒后自动跳转
    setTimeout(() => {
      const redirect = state === 'login' ? '/' : decodeURIComponent(state)
      router.push(redirect)
    }, 2000)
  } catch (error) {
    isSuccess.value = false
    errorMessage.value = error.response?.data?.detail || '微信授权失败，请检查配置'
    console.error('[WechatCallback]', error)
  } finally {
    isLoading.value = false
  }
}

onMounted(() => {
  processCallback()
})

function handleRedirect() {
  if (isSuccess.value) {
    router.push('/')
  } else {
    router.push('/login')
  }
}
</script>

<style scoped>
.callback-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
</style>
```

---

## Step 4: 测试流程

### 4.1 启动服务

**终端 1 - 后端：**
```bash
cd backend
python -m venv venv
venv\Scripts\activate              # Windows
# source venv/bin/activate         # Linux/Mac
pip install -r requirements.txt
python -m app.main
```

**终端 2 - 前端：**
```bash
cd frontend
npm install
npm run dev
```

### 4.2 测试微信登录

1. 打开 http://localhost:5173/login
2. 点击微信登录按钮
3. 扫描微信二维码（或点击"使用本地测试账号"）
4. 应该跳转回 http://localhost:5173/
5. 检查浏览器控制台，应该看到 access_token 被保存

### 4.3 调试技巧

**查看完整流程日志：**
```bash
cd backend
tail -f logs/app_*.log
```

**测试回调接口：**
```bash
# 使用测试 code（需要真实微信授权）
curl "http://localhost:8000/api/v1/auth/wechat/callback?code=YOUR_CODE&state=login"
```

---

## Step 5: 常见问题排查

### 问题 1: 微信登录按钮点击无反应
**原因：** 后端没配置 WECHAT_LOGIN_APP_ID 或 WECHAT_REDIRECT_URI
**解决：** 检查 `backend/.env` 中这两个配置是否正确

### 问题 2: 扫码后显示 "errcode"
**原因：** 微信验证 code 失败，通常是 App Secret 错误或 code 过期
**解决：** 
- 确认复制的 App Secret 完全正确（不含空格）
- code 有效期 10 分钟，不要扫码太久

### 问题 3: 回调 URL 不匹配
**原因：** 微信开放平台配置的回调域名与代码中使用的不一致
**解决：** 在微信开放平台设置中添加所有可能的域名：
```
localhost:8000
127.0.0.1:8000
your-domain.com
```

### 问题 4: CORS 错误
**原因：** 前端和后端的跨域配置不匹配
**解决：** 在 `backend/app/config.py` 的 `CORS_ORIGINS` 中添加前端地址

---

## Step 6: 数据库验证

微信登录成功后，用户会被自动创建在数据库中。检查用户数据：

```bash
# 进入 backend 目录
cd backend
python

# 在 Python 交互式界面
from app.models.user import User, get_db
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 查询微信用户
db_session = get_db()
wx_users = db_session.query(User).filter(User.wechat_openid != None).all()
for user in wx_users:
    print(f"ID: {user.id}, Username: {user.username}, OpenID: {user.wechat_openid}")
```

---

## Step 7: 生产部署

### 配置生产环境变量

`.env.production`：
```env
# 微信开放平台
WECHAT_LOGIN_APP_ID=真实的APP_ID
WECHAT_APP_SECRET=真实的APP_SECRET
WECHAT_REDIRECT_URI=https://your-domain.com/api/v1/auth/wechat/callback

# JWT密钥（改为随机字符串）
SECRET_KEY=use-random-secret-key-in-production

# 前端CORS源
CORS_ORIGINS=["https://your-domain.com", "http://your-domain.com"]
```

### Docker 部署
```bash
docker-compose -f docker/docker-compose.yml up -d
# 容器会自动读取 .env 文件中的配置
```

---

## 扩展功能

### 绑定已有账号

如果用户已经有传统账号，可以将微信绑定到现有账号：

在 `backend/app/api/v1/auth.py` 中添加：

```python
@router.post("/wechat/bind", response_model=UserOut)
def bind_wechat(
    code: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """将当前账号绑定微信"""
    from app.services.oauth_service import wechat_code_to_user
    
    if current_user.wechat_openid:
        raise HTTPException(status_code=400, detail="此账号已绑定微信")
    
    wx_user = wechat_code_to_user(code)
    if not wx_user:
        raise HTTPException(status_code=400, detail="微信授权失败")
    
    # 检查微信是否已被其他账号绑定
    existing = db.query(User).filter(User.wechat_openid == wx_user["openid"]).first()
    if existing:
        raise HTTPException(status_code=400, detail="此微信已被其他账号绑定")
    
    current_user.wechat_openid = wx_user["openid"]
    current_user.nickname = wx_user.get("nickname", "")
    db.commit()
    db.refresh(current_user)
    return current_user
```

---

## 相关文件索引

| 文件 | 作用 |
|------|------|
| `backend/app/api/v1/auth.py` | 微信登录端点：`/wechat/url` 和 `/wechat/callback` |
| `backend/app/services/oauth_service.py` | 微信 API 调用逻辑 |
| `backend/app/config.py` | 配置管理，包含微信参数 |
| `backend/app/models/user.py` | 用户模型，包含 `wechat_openid` 字段 |
| `frontend/src/api/auth.js` | 前端 API 调用 `getWechatLoginUrl()` |
| `frontend/src/views/Login.vue` | 登录页面，微信登录按钮 |
| `frontend/src/views/WechatCallback.vue` | **需创建** - 微信回调处理页面 |

---

## 安全建议

1. **Secret 保密**：Never commit `.env` file with real secrets
2. **HTTPS 生产**：生产环境务必使用 HTTPS，微信不支持 HTTP
3. **Token 过期**：默认 7 天过期，可在 `ACCESS_TOKEN_EXPIRE_MINUTES` 调整
4. **IP白名单**：可选的加强安全措施，限制调用微信 API 的 IP

---

## 支持的关联功能

- ✅ 微信登录自动注册
- ✅ 邀请码支持（state 参数传递）
- ✅ 昵称和头像保存
- ✅ 账号禁用检测
- ✅ 免费试用额度分配

同时支持支付宝登录，配置方式类似。
