# 排版模块行间距问题修复

## 问题描述

用户报告：排版模板中设置的行间距（如 1.3倍）在下载的文档中被错误地转换为 1.5倍。

**原因分析：**
python-docx 中 `paragraph_format.line_spacing` 有两种解释模式：
1. **MULTIPLE 模式**（倍数）：1.3 表示 1.3 倍行距
2. **其他模式**：1.5 可能被解释为 1.5pt（固定值）或自动优化为标准值

当设置 `line_spacing = 1.3` 而不设置 `line_spacing_rule = MULTIPLE` 时，Word 会自动将其调整为最接近的标准值（1.5倍），导致原始配置丢失。

## 解决方案

### 修改文件

#### 1. `backend/app/core/formatter/template_manager.py`

**新增配置字段：**
- `TemplateConfig.default_toc_line_spacing_rule` - 目录行距规则（默认 'MULTIPLE'）

**修改 `_extract_styles()` 方法：**
```python
# 行距规则（关键：倍数 vs 固定值）
line_spacing_rule = self._resolve_style_attr(style, 'line_spacing_rule')
if line_spacing_rule is not None:
    # 转换为字符串便于序列化和比对
    style_config["line_spacing_rule"] = str(line_spacing_rule)
```

**作用：** 在提取模板样式时，同时获取行距规则（SINGLE / ONE_POINT_FIVE / DOUBLE / MULTIPLE 等）

---

#### 2. `backend/app/core/formatter/style_applicator.py`

**修改 `_apply_format()` 方法：**
```python
# 行距（含行距规则）
if config.get('line_spacing'):
    line_spacing_val = config['line_spacing']
    
    # 优先根据 line_spacing_rule 设置
    line_spacing_rule = config.get('line_spacing_rule')
    if line_spacing_rule:
        # 将字符串转换为 WD_LINE_SPACING 枚举
        pf.line_spacing_rule = rule_map.get(rule_str, WD_LINE_SPACING.MULTIPLE)
    else:
        # 根据值自动判断
        if line_spacing_val not in (1.0, 1.5, 2.0):
            # 非标准值（如 1.3）必须使用 MULTIPLE 模式
            pf.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
    
    pf.line_spacing = line_spacing_val
```

**作用：** 应用样式时恢复行距规则，确保 1.3 倍等非标准值被正确保存

**修改 `_apply_toc_spacing()` 方法：**
- 同样添加行距规则的设置和自动判断逻辑

**修改 `_apply_caption_format()` 方法：**
- 同样添加行距规则的设置和自动判断逻辑

---

## 技术细节

### 行距规则映射表

| 枚举值 | 含义 | 使用场景 |
|--------|------|----------|
| `SINGLE` (0) | 单倍行距 | 1.0 倍 |
| `ONE_POINT_FIVE` (1) | 1.5 倍 | 标准 1.5 倍 |
| `DOUBLE` (2) | 双倍行距 | 2.0 倍 |
| `AT_LEAST` (3) | 至少（固定最小值） | 按 pt 值 |
| `EXACTLY` (4) | 精确（固定值） | 按 pt 值 |
| `MULTIPLE` (5) | 倍数 | **非标准倍数，如 1.3** |

### 自动判断逻辑

```
if line_spacing in (1.0, 1.5, 2.0):
    # Word 标准值，直接设置（自动优化）
    pf.line_spacing = value
else:
    # 非标准值，必须设置 MULTIPLE 规则
    pf.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
    pf.line_spacing = value
```

---

## 测试验证

### 测试场景

1. **模板提取**
   ```
   模板中 1.3 倍行距 → 提取时保存 line_spacing_rule='MULTIPLE'
   模板中 1.5 倍行距 → 提取时可能是 line_spacing_rule='ONE_POINT_FIVE' 或 'MULTIPLE'
   ```

2. **应用到文档**
   ```
   应用时检查 line_spacing_rule
   如果是 MULTIPLE，直接应用原始值 1.3
   如果是 ONE_POINT_FIVE，直接应用 1.5（Word 自动优化）
   如果缺失，根据值自动判断
   ```

3. **保存和重新打开**
   ```
   1.3 倍行距 → 保存 → 重新打开 → 仍是 1.3 倍（MULTIPLE 规则）
   1.5 倍行距 → 保存 → 重新打开 → 仍是 1.5 倍（ONE_POINT_FIVE 规则）
   ```

---

## 适用范围

该修复影响以下应用位置：

1. **正文段落** - 通过 `_apply_format()` 应用
2. **目录段落** - 通过 `_apply_toc_spacing()` 应用
3. **图表/表题** - 通过 `_apply_caption_format()` 应用

---

## 向后兼容性

✓ **完全向后兼容**

- 如果模板中缺少 `line_spacing_rule` 字段，系统会根据行距值自动判断
- 标准值（1.0, 1.5, 2.0）的处理保持不变
- 现有模板无需修改，会自动适配新逻辑

---

## 结果

修复前：
```
模板: 1.3 倍行距
下载: 1.5 倍行距（错误转换）
```

修复后：
```
模板: 1.3 倍行距
下载: 1.3 倍行距（正确保留）
```
