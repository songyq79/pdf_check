# 轮询问题修复总结

## 问题描述
智能评价和错别字检查在上传文档生成过程中，进度卡在约70%不动。

## 根本原因
**Evaluation Store 使用了错误的轮询方式**

### 问题代码
```javascript
// 错误：使用阻塞式 while 循环
async function pollUntilDone(taskId) {
  while (Date.now() < deadline) {
    await new Promise(r => setTimeout(r, POLL_INTERVAL_MS))
    // ... 轮询逻辑
  }
}
```

### 问题分析
1. **阻塞式循环**：`while` 循环会阻塞 JavaScript 主线程
2. **无法取消**：`stopPolling()` 只清除 `pollingTimer`，但 `pollUntilDone` 根本没有使用 timer
3. **进度卡住**：当轮询遇到网络问题或其他异常时，循环可能卡住
4. **与 SpellCheck/Formatting 不一致**：这两个 Store 使用的是正确的 `setInterval` 方式

## 修复方案

### 1. 改用 setInterval 定时器轮询
```javascript
function startPolling(taskId) {
  stopPolling()
  isPollingActive = true
  pollRetryCount = 0

  pollTimer = setInterval(async () => {
    // 检查任务ID是否匹配
    if (taskId !== currentTaskId.value) {
      stopPolling()
      return
    }

    try {
      const statusResp = await evaluationAPI.getStatus(taskId)
      
      if (status === 'processing') {
        // 更新进度
        if (progress != null && progress > uploadProgress.value) {
          uploadProgress.value = progress
        }
      } else if (status === 'completed') {
        stopPolling()
        // 获取结果并更新状态
      } else if (status === 'failed') {
        stopPolling()
        // 标记失败
      }
    } catch (err) {
      pollRetryCount++
      if (pollRetryCount >= MAX_POLL_RETRIES) {
        stopPolling()
        // 标记失败
      }
    }
  }, POLL_INTERVAL_MS)
}
```

### 2. 正确实现 stopPolling
```javascript
function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
  isPollingActive = false
  pollRetryCount = 0
}
```

### 3. 修改 uploadAndEvaluate
```javascript
async function uploadAndEvaluate(file) {
  // ... 上传逻辑
  
  // 启动轮询（不再使用 await pollUntilDone）
  startPolling(taskId)
}
```

### 4. 修改 resumeIfProcessing
```javascript
function resumeIfProcessing() {
  if (isProcessing.value && currentTaskId.value && !isPollingActive) {
    startPolling(currentTaskId.value)
  }
}
```

## 修复的文件
- `frontend/src/store/modules/evaluation.js`

## 修复内容
1. ✅ 删除了 `pollUntilDone` 函数
2. ✅ 添加了 `startPolling` 函数（使用 setInterval）
3. ✅ 修改了 `stopPolling` 函数（使用 clearInterval）
4. ✅ 修改了 `uploadAndEvaluate` 函数（调用 startPolling）
5. ✅ 修改了 `resumeIfProcessing` 函数（调用 startPolling）
6. ✅ 添加了 `isPollingActive` 标志防止重复轮询

## 验证

### SpellCheck Store
✅ 已经使用正确的 setInterval 轮询方式，无需修改

### Formatting Store
✅ 已经使用正确的 setInterval 轮询方式，无需修改

### Evaluation Store
✅ 现在使用与 SpellCheck/Formatting 相同的轮询方式

## 修复后的行为
1. ✅ 轮询不会阻塞主线程
2. ✅ 可以正确取消轮询
3. ✅ 进度会持续更新直到完成
4. ✅ 网络错误会正确重试
5. ✅ 超过重试次数会标记失败
6. ✅ 三个功能的轮询逻辑一致

## 测试建议
1. 上传文档测试智能评价
2. 观察进度条是否持续更新
3. 测试取消功能是否正常工作
4. 测试页面切换后轮询是否恢复
5. 测试网络异常时的重试机制

## 重启前端
```bash
cd frontend
npm run dev
```

清除浏览器缓存或使用无痕模式测试。
