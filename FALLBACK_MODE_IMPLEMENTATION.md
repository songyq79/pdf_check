# 降级处理模式实现总结

## 概述

为三个核心功能（智能评价、错别字检查、模板排版）实现了文档格式异常的降级处理机制，当文档无法正常解析时，自动提取文本内容并进行简化处理，同时在前端显示警告提示。

## 实现原理

### 后端降级处理

当遇到文档格式错误（`no item named` 或 `badzip`）时：

1. **文本提取**：将 .docx 文件当作 ZIP 压缩包打开，解析 `word/document.xml`，提取所有 `<w:t>` 文本节点
2. **简化处理**：
   - 智能评价：从纯文本中提取标题、摘要、关键词、参考文献等结构化信息
   - 错别字检查：创建新文档，添加文本段落，进行正常校对流程
   - 模板排版：创建新文档，添加文本段落，应用基本模板样式
3. **返回警告**：在响应中添加 `warning` 字段，告知用户使用了降级模式

### 前端警告提示

在三个功能页面的完成状态区域添加警告提示框：

```vue
<el-alert
  v-if="store.warning"
  type="warning"
  :title="store.warning"
  :closable="false"
  show-icon
  class="mb-20"
>
  <template #default>
    <div style="font-size: 13px; line-height: 1.6;">
      系统已自动从文档中提取文本内容进行处理，但可能丢失了部分格式信息。
      <br>
      建议：在 Word 中打开文档，选择"另存为"，保存为新的 .docx 文件后重新上传。
    </div>
  </template>
</el-alert>
```

## 修改的文件

### 后端（7个文件）

1. **`backend/app/api/v1/evaluation.py`**
   - 添加 `_extract_text_fallback()` - 文本提取（25行）
   - 添加 `_extract_structure_from_text()` - 从文本提取结构（120行）
   - 修改 `evaluate_paper()` - 降级处理逻辑（30行）
   - 修复中文引号语法错误

2. **`backend/app/api/v1/proofread.py`**
   - 修改 `get_status()` - 返回 warning 字段（8行）

3. **`backend/app/api/v1/formatter.py`**
   - 修改 `get_format_status()` - 返回 warning 字段（5行）

4. **`backend/app/core/proofreadme/pipeline.py`**
   - 添加 `_extract_text_fallback()` - 文本提取（25行）
   - 添加 `_create_simple_proofread_doc()` - 简化校对文档（80行）
   - 添加 `_proofread_tasks_async()` - 异步校对任务（50行）
   - 修改 `process_word()` - 降级处理逻辑（20行）

5. **`backend/app/workers/proofread_tasks.py`**
   - 修改 `run_proofread()` - 返回 warning 信息（10行）

6. **`backend/app/workers/formatter_tasks.py`**
   - 修改 `run_formatting()` - 返回 warning 信息（10行）

7. **`backend/app/core/formatter/format_engine.py`**
   - 已有降级处理实现（之前完成）

### 前端（6个文件）

8. **`frontend/src/store/modules/evaluation.js`**
   - 添加 `warning` 状态
   - 在上传响应中保存 warning
   - 在 reset 和 return 中添加 warning

9. **`frontend/src/store/modules/spellCheck.js`**
   - 添加 `warning` 状态
   - 在轮询完成时保存 warning
   - 在历史记录中保存 warning
   - 在 reset、loadPendingOrKeep 和 return 中添加 warning

10. **`frontend/src/store/modules/formatting.js`**
    - 添加 `warning` 状态
    - 在轮询完成时保存 warning
    - 在历史记录中保存 warning
    - 在 reset、loadPendingOrKeep 和 return 中添加 warning

11. **`frontend/src/views/Evaluation.vue`**
    - 在完成状态显示区域添加警告提示框

12. **`frontend/src/views/SpellCheck.vue`**
    - 在完成状态显示区域添加警告提示框

13. **`frontend/src/views/Formatting.vue`**
    - 在完成状态显示区域添加警告提示框

## 用户体验改进

### 之前
```
❌ 处理失败
文档格式异常，无法解析
```

### 之后
```
⚠️ 处理完成（简化模式）
文档格式异常，已使用简化模式处理（可能丢失部分格式、图片等内容）

系统已自动从文档中提取文本内容进行处理，但可能丢失了部分格式信息。
建议：在 Word 中打开文档，选择"另存为"，保存为新的 .docx 文件后重新上传。

✅ 已生成结果
```

## 技术优势

1. **自动修复**：无需用户手动处理文档，系统自动尝试修复
2. **功能可用**：即使文档损坏，仍能处理文本内容
3. **信息透明**：明确告知用户使用了降级模式及其影响
4. **代码复用**：三个功能使用相同的降级处理思路
5. **用户友好**：提供具体的修复建议

## 局限性

1. **格式丢失**：降级模式只保留文本，丢失图片、表格、复杂格式
2. **样式简化**：只能应用基本样式，无法完全还原原文档
3. **不是万能**：如果 ZIP 结构完全损坏，仍然无法处理

## 测试建议

1. **正常文档**：确保不影响正常文档的处理
2. **损坏文档**：测试各种损坏情况（格式错误、ZIP 损坏等）
3. **特殊文档**：测试包含图片、表格、OLE 对象的文档
4. **警告显示**：确认前端警告提示正确显示
5. **历史记录**：确认历史记录中保存了警告信息

## 后续优化方向

1. **更智能的文本提取**：保留段落结构、标题层级
2. **图片提取**：尝试提取并保留图片
3. **表格提取**：尝试提取并保留表格结构
4. **格式恢复**：尝试恢复部分格式信息（加粗、斜体等）

## 总代码量

- 后端新增：约 400 行
- 前端新增：约 100 行
- 总计：约 500 行

## 完成状态

✅ 所有代码已实现
✅ 语法检查通过
✅ 诊断检查通过
✅ 准备就绪，可以测试
