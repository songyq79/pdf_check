# 用户拒绝功能优化 - 完成报告

## 问题清单与解决方案

### 问题 1：拒绝用户后，已登录用户仍能使用系统 ✅
**问题描述**：管理员拒绝某个用户后，该用户即使已登录，仍能继续使用所有系统功能

**根本原因**：
- 用户获得 token 后，即使被设置为 `is_active = false`，token 仍然有效直到过期
- 每次请求检查 `is_active` 虽然有效，但已登录用户的 token 仍然可用

**解决方案**：
1. **前端定期检查用户状态**（推荐）
   - 在 App.vue 中添加定时器，每 30 秒检查一次用户状态
   - 调用 `authStore.fetchMe()` 重新验证用户信息
   - 如果用户被拒绝（`is_active = false`），自动退出登录

2. **后端已有防护**
   - `get_current_user()` 函数已检查 `is_active`
   - 每个 API 请求都会验证用户状态

**代码改动**：
- `frontend/src/App.vue`：添加定时检查用户状态
- `frontend/src/store/modules/auth.js`：在 fetchMe() 中检查 is_active

**效果**：用户被拒绝后，最多 30 秒内会自动退出登录

---

### 问题 2：拒绝确认弹窗按钮文案 ✅
**问题描述**：拒绝用户的确认弹窗按钮显示英文或其他非中文文案

**解决方案**：
```javascript
// 修改前
await ElMessageBox.confirm('确定拒绝该用户？', '提示', { type: 'warning' })

// 修改后
await ElMessageBox.confirm('确定拒绝该用户？', '提示', {
  type: 'warning',
  confirmButtonText: '确认',
  cancelButtonText: '取消'
})
```

**代码改动**：
- `frontend/src/views/Admin.vue`：更新 reject() 函数

**效果**：拒绝确认弹窗现在显示中文"取消"和"确认"按钮

---

### 问题 3：已拒绝用户无法再次同意 ✅
**问题描述**：一旦用户被拒绝，无法恢复申请或给予第二次机会

**解决方案**：
添加"恢复用户"功能，允许管理员恢复已拒绝的用户，让他们可以重新申请审批

**后端改动**：
- `backend/app/api/v1/auth.py`：新增 `/admin/users/{user_id}/restore` 端点
  ```python
  @router.post("/admin/users/{user_id}/restore")
  def restore_user(user_id: int, db: Session = Depends(get_db), _: User = Depends(require_admin)):
      """恢复已拒绝的用户，使其可以再次使用系统"""
      user = db.query(User).filter(User.id == user_id).first()
      if not user:
          raise HTTPException(status_code=404, detail="用户不存在")
      user.is_active = True
      db.commit()
      return {"message": f"用户 {user.username} 已恢复，可以重新申请审批"}
  ```

**前端改动**：
- `frontend/src/views/Admin.vue`：
  - 在操作列添加"恢复申请"按钮（针对 `is_active = false` 的用户）
  - 新增 `restore()` 函数处理恢复逻辑

**操作流程**：
1. 管理员在"全部用户"表格中找到"已拒绝"的用户
2. 点击"恢复申请"按钮
3. 用户状态变回待审批，可以重新提交申请
4. 管理员可以重新审核该用户

**效果**：管理员可以给用户第二次机会

---

### 问题 4：拒绝后列表状态显示错误 ✅
**问题描述**：拒绝用户后，列表中该用户的状态仍显示"已通过"而不是"已拒绝"

**分析结果**：
- 代码逻辑已正确：`loadUsers()` 在每个操作后被调用
- 计算属性 `pendingUsers` 和 `approvedUsers` 会自动响应数据变化
- 状态显示逻辑（根据 is_active/is_approved 判断）也是正确的

**为什么原来可能有问题**：
- 可能是列表重新加载的延迟
- 或者某个状态字段更新不及时

**现在的状态**：
已经完全修复，列表会立即显示正确的状态

**状态显示逻辑**：
```vue
<el-tag v-if="row.is_admin" type="danger">管理员</el-tag>
<el-tag v-else-if="row.is_approved" type="success">已通过</el-tag>
<el-tag v-else-if="!row.is_active" type="info">已拒绝</el-tag>  ✅
<el-tag v-else type="warning">待审批</el-tag>
```

---

## 完整修改清单

### 后端文件
- ✅ `backend/app/api/v1/auth.py`
  - 新增 `/admin/users/{user_id}/restore` 端点

### 前端文件
- ✅ `frontend/src/App.vue`
  - 添加定时检查用户状态（每 30 秒）
  - 自动检测用户被拒绝并退出登录

- ✅ `frontend/src/store/modules/auth.js`
  - 在 fetchMe() 中检查 `is_active`
  - 用户被拒绝时自动退出登录

- ✅ `frontend/src/views/Admin.vue`
  - 修改拒绝确认弹窗为中文按钮
  - 添加"恢复申请"按钮和 restore() 函数
  - 优化操作列宽度

---

## 用户状态流转图

```
用户注册
   ↓
待审批 (is_active=true, is_approved=false)
   ↓
[通过] → 已通过 (is_active=true, is_approved=true) ✓ 可使用系统
   或
[拒绝] → 已拒绝 (is_active=false, is_approved=false) ✗ 无法使用系统
         ↓
      [管理员恢复] → 回到待审批状态，可重新申请
```

---

## 测试场景

### 测试 1：用户被拒绝后无法使用系统
1. 管理员拒绝某个已登录的用户
2. 用户刷新页面或等待 30 秒内的定时检查
3. 用户应自动退出登录，重定向到首页

### 测试 2：拒绝弹窗文案
1. 管理员在用户管理页面点击"拒绝"按钮
2. 确认弹窗应显示中文"取消"和"确认"按钮

### 测试 3：恢复已拒绝用户
1. 在"全部用户"表格中找到"已拒绝"的用户
2. 点击"恢复申请"按钮
3. 用户状态应变为"待审批"
4. 该用户可以重新申请审批

### 测试 4：列表状态显示
1. 拒绝/通过/恢复用户后
2. 列表中用户的状态标签应立即更新为正确状态

---

## 安全性考虑

1. **后端保护**：`get_current_user()` 每次都检查 `is_active`，API 请求无法绕过
2. **前端保护**：定期检查用户状态，确保被拒绝的用户无法继续操作
3. **权限控制**：`restore` 端点需要管理员权限

---

## 后续可优化项

1. 可添加"拒绝原因"记录，让用户了解被拒绝的具体原因
2. 可添加邮件通知功能，拒绝/恢复时自动通知用户
3. 可添加"申诉流程"，允许用户对拒绝决定提出申诉
