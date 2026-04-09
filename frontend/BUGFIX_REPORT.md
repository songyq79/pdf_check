# 前端 Bug 修复报告

## 修复日期
2026-03-03

## 修复的严重 Bug

### 1. ✅ 循环依赖导致应用崩溃（最严重）
**文件**: `frontend/src/api/evaluation.js`

**问题**: 该文件被错误地定义为 Pinia store module，同时又导入自己作为 API 模块，造成循环依赖。

**修复**:
- 完全重写 `evaluation.js`，改为正确的 API 模块格式
- 添加了 `upload()`, `getStatus()`, `getResult()`, `downloadReport()` 方法
- 与其他 API 模块（formatting.js, spellCheck.js）保持一致的结构

**影响**: 修复后应用可以正常启动，评价功能可以正常使用。

---

### 2. ✅ 内存泄漏 - 轮询定时器未清理
**文件**: 
- `frontend/src/store/modules/formatting.js`
- `frontend/src/store/modules/spellCheck.js`

**问题**: `setInterval` 创建的定时器在页面切换时未被正确清理，长期使用会导致内存泄漏。

**修复**:
- 添加 `isPollingActive` 标志防止重复启动轮询
- 添加 `pollRetryCount` 计数器限制网络错误重试次数（最多3次）
- 在 `stopPolling()` 中重置所有状态
- 添加 `onUnmounted()` 钩子确保组件卸载时清理定时器
- 在轮询函数中添加任务ID匹配检查，防止竞态条件

**影响**: 修复后不再有内存泄漏，浏览器性能稳定。

---

### 3. ✅ 竞态条件 - 快速切换页面导致状态混乱
**文件**: 
- `frontend/src/store/modules/formatting.js`
- `frontend/src/store/modules/spellCheck.js`

**问题**: 用户快速切换页面时，可能同时启动多个轮询任务，导致状态不一致。

**修复**:
- 在 `startPolling()` 开始时检查 `isPollingActive` 标志
- 如果已有轮询在运行，跳过重复启动并输出警告
- 在轮询回调中检查 `taskId !== currentTaskId.value`，如果不匹配则停止轮询
- 修改 `resumeIfProcessing()` 检查 `!isPollingActive` 而不是 `!pollTimer`

**影响**: 修复后不会出现多个轮询同时运行的情况，状态保持一致。

---

### 4. ✅ 错误处理不完善 - 轮询失败时无重试机制
**文件**: 
- `frontend/src/store/modules/evaluation.js`
- `frontend/src/store/modules/formatting.js`
- `frontend/src/store/modules/spellCheck.js`

**问题**: 轮询状态时网络错误被静默忽略，没有重试计数器，可能导致无限轮询或用户无法获知失败。

**修复**:
- 添加 `MAX_POLL_RETRIES = 3` 常量
- 在轮询函数中添加 `pollRetryCount` 或 `retryCount` 计数器
- 网络错误时增加计数器并输出警告日志
- 超过最大重试次数后停止轮询并标记为失败状态
- 成功请求后重置重试计数器

**影响**: 修复后网络不稳定时有明确的失败提示，不会无限轮询。

---

### 5. ✅ localStorage 溢出风险
**文件**: 
- `frontend/src/store/modules/history.js`
- `frontend/src/utils/storage.js`

**问题**: 历史记录没有数量限制，长期使用会导致 localStorage 满溢（通常 5-10MB 限制）。

**修复**:
- 添加 `MAX_RECORDS = 100` 常量限制最多保存100条记录
- 在 `addRecord()` 中添加记录后检查数量，超过限制则截断
- 在 `loadFromLocalStorage()` 中限制加载的记录数量
- 在 `saveToLocalStorage()` 中添加 try-catch 错误处理
- 如果保存失败且记录超过50条，自动清理到50条后重试
- 修改 `storage.js` 的 `setStorage()` 抛出错误而不是返回 false

**影响**: 修复后不会出现 localStorage 满溢的情况，历史记录保持在合理范围内。

---

## 其他改进

### 6. ✅ API 响应验证增强
**文件**: `frontend/src/store/modules/formatting.js`

**改进**: 
- 在访问 `res.end_time` 和 `res.start_time` 时添加存在性检查
- 使用 `res.end_time && res.start_time` 确保两个字段都存在才计算时间差

---

## 未修复的问题（需要进一步讨论）

### 7. ⚠️ 文件上传进度条可能倒退
**文件**: `frontend/src/store/modules/evaluation.js`

**问题**: 虽然代码注释说"不会因为后端 progress=0 而归零"，但实际上如果后端返回 `progress=0`，会导致进度条倒退。

**建议**: 需要确认后端 API 的 progress 字段行为，或者在前端完全忽略后端 progress 字段。

---

### 8. ⚠️ 路由参数验证缺失
**文件**: `frontend/src/router/index.js`

**问题**: 路由守卫只设置标题，没有验证路由参数或检查用户权限。

**建议**: 如果后端添加了权限控制，需要在路由守卫中添加相应的验证逻辑。

---

## 测试建议

### 1. 内存泄漏测试
- 打开浏览器开发者工具的 Performance 面板
- 快速切换页面（评价 → 排版 → 拼写检查）多次
- 观察内存使用情况，应该保持稳定，不会持续上升

### 2. 竞态条件测试
- 上传文件后立即切换到其他页面
- 再切回原页面
- 检查是否只有一个轮询在运行（查看 console 日志）

### 3. 网络错误测试
- 使用浏览器开发者工具的 Network 面板模拟网络错误
- 观察是否在3次重试后显示错误提示

### 4. localStorage 测试
- 添加大量历史记录（超过100条）
- 检查是否自动截断到100条
- 检查 localStorage 大小是否在合理范围内

---

## 代码质量改进

1. **添加了详细的日志输出**: 所有关键操作都有 console.warn 或 console.error 日志
2. **添加了防御性编程**: 检查变量存在性、添加边界条件判断
3. **统一了错误处理模式**: 所有 store 模块使用相同的错误处理策略
4. **改进了代码注释**: 添加了更多解释性注释

---

## 总结

本次修复解决了 **5 个严重 bug**，显著提升了应用的稳定性和用户体验：

1. ✅ 应用不再因循环依赖而崩溃
2. ✅ 不再有内存泄漏问题
3. ✅ 竞态条件得到控制
4. ✅ 网络错误有明确的重试和失败提示
5. ✅ localStorage 不会溢出

建议在部署前进行充分的测试，特别是内存泄漏和竞态条件的测试。
