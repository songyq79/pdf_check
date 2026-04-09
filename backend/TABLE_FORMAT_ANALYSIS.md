# Word 表格格式错误问题分析

## 问题描述
测试反馈：错别字检查完成后，下载文档，首页表格内的文字错版，未与其他行对齐，并且表格线位置不对。

## 代码分析

### 1. 表格处理流程（pipeline.py）

#### 当前实现
```python
def _collect_tasks(doc: Document):
    """收集所有需要校对的段落"""
    # 第一步：收集表格内的段落ID
    para_elems_in_tables = set()
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    para_elems_in_tables.add(id(p._p))
    
    # 第二步：收集正文段落（排除表格内段落）
    tasks = []
    for p in doc.paragraphs:
        if id(p._p) not in para_elems_in_tables:
            tasks.append((p, "body"))
    
    # 第三步：收集表格单元格段落
    seen_para_ids = set()
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    if id(p._p) not in seen_para_ids:
                        seen_para_ids.add(id(p._p))
                        tasks.append((p, "table_cell"))
    
    return tasks
```

### 2. 修订节点写入逻辑（pipeline.py）

#### 当前实现
```python
def _write_revision(para_elem, original: str, corrected: str, rpr_elem=None) -> int:
    # 1. 计算 diff
    opcodes = compute_diff(original, corrected)
    
    # 2. 找到第一个 run 的位置
    children = list(para_elem)
    insert_index = len(children)
    for i, child in enumerate(children):
        tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
        if tag in ("r", "del", "ins", "hyperlink"):
            insert_index = i
            break
    
    # 3. 移除所有已有的 w:r / w:del / w:ins / w:hyperlink
    to_remove = []
    for child in para_elem:
        tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
        if tag in ("r", "del", "ins", "hyperlink"):
            to_remove.append(child)
    for child in to_remove:
        para_elem.remove(child)
    
    # 4. 构建新的修订节点并插入
    new_nodes = []
    # ... 构建修订节点 ...
    
    # 5. 按顺序插入到 insert_index 之后
    for offset, node in enumerate(new_nodes):
        para_elem.insert(insert_index + offset, node)
    
    return change_count
```

## 🔴 发现的问题

### 问题1：表格段落属性丢失
**位置**: `_write_revision()` 函数

**问题描述**:
- 代码移除了所有 `w:r`、`w:del`、`w:ins`、`w:hyperlink` 节点
- 但**没有保留表格单元格的特殊属性**，如：
  - `w:tcPr`（单元格属性）：边框、对齐方式、垂直对齐
  - `w:pPr`（段落属性）：对齐方式、缩进、行距
  - `w:tblPr`（表格属性）：表格边框、单元格间距

**影响**:
- 表格单元格的对齐方式丢失
- 表格边框可能错位
- 文字垂直对齐失效

### 问题2：段落属性（w:pPr）可能被破坏
**位置**: `_write_revision()` 函数

**问题描述**:
- 虽然代码注释说"保留 w:pPr"，但实际上：
  1. 找到 `insert_index` 后
  2. 删除所有 run 节点
  3. 在 `insert_index` 位置插入新节点
- 如果 `w:pPr` 在 run 节点之后，可能会被错误地放置在新节点之前

**Word XML 正确结构**:
```xml
<w:p>
    <w:pPr><!-- 段落属性，必须在最前面 --></w:pPr>
    <w:r><!-- run 节点 --></w:r>
    <w:del><!-- 删除修订 --></w:del>
    <w:ins><!-- 插入修订 --></w:ins>
</w:p>
```

### 问题3：表格单元格段落的特殊处理缺失
**位置**: `_proofread_cell()` 和 `_write_revision()`

**问题描述**:
- 表格单元格段落和正文段落使用相同的 `_write_revision()` 函数
- 但表格单元格有特殊的 XML 结构：
  ```xml
  <w:tc><!-- 单元格 -->
      <w:tcPr><!-- 单元格属性 --></w:tcPr>
      <w:p><!-- 段落 -->
          <w:pPr><!-- 段落属性 --></w:pPr>
          <w:r><!-- 文字 --></w:r>
      </w:p>
  </w:tc>
  ```
- 修改段落时，可能影响到父级单元格的属性

### 问题4：run 属性（w:rPr）继承不完整
**位置**: `_get_rpr()` 函数

**问题描述**:
```python
def _get_rpr(para_elem):
    """取第一个直接子 w:r 的 w:rPr"""
    ns_w = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
    r = para_elem.find(f"{{{ns_w}}}r")
    if r is not None:
        rpr = r.find(f"{{{ns_w}}}rPr")
        return rpr
    return None
```

**问题**:
- 只取第一个 run 的样式
- 如果表格单元格内有多个不同样式的 run，后续 run 的样式会丢失
- 表格中常见的情况：加粗标题 + 普通文字

## 🔧 修复建议

### 建议1：保留段落属性（w:pPr）的正确位置
```python
def _write_revision(para_elem, original: str, corrected: str, rpr_elem=None) -> int:
    # ... 前面的代码 ...
    
    # 1. 先保存 w:pPr（如果存在）
    ns_w = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
    ppr_elem = para_elem.find(f"{{{ns_w}}}pPr")
    
    # 2. 移除所有 run 节点
    to_remove = []
    for child in para_elem:
        tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
        if tag in ("r", "del", "ins", "hyperlink"):
            to_remove.append(child)
    for child in to_remove:
        para_elem.remove(child)
    
    # 3. 确保 w:pPr 在最前面
    if ppr_elem is not None:
        para_elem.remove(ppr_elem)
        para_elem.insert(0, ppr_elem)
        insert_index = 1  # run 节点从 w:pPr 之后开始
    else:
        insert_index = 0
    
    # 4. 插入新的修订节点
    for offset, node in enumerate(new_nodes):
        para_elem.insert(insert_index + offset, node)
    
    return change_count
```

### 建议2：为表格单元格段落添加特殊处理
```python
def _write_revision_for_table_cell(para_elem, original: str, corrected: str, rpr_elem=None) -> int:
    """
    专门用于表格单元格段落的修订写入。
    保留表格特有的属性和格式。
    """
    # 1. 保存所有重要属性
    ns_w = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
    ppr_elem = para_elem.find(f"{{{ns_w}}}pPr")
    
    # 2. 检查是否在表格单元格内
    parent = para_elem.getparent()
    is_in_table = parent is not None and parent.tag.endswith("}tc")
    
    # 3. 如果在表格内，额外保留对齐方式
    if is_in_table and ppr_elem is not None:
        # 确保段落属性包含对齐方式
        jc = ppr_elem.find(f"{{{ns_w}}}jc")
        if jc is None:
            # 默认左对齐
            jc = OxmlElement("w:jc")
            jc.set(qn("w:val"), "left")
            ppr_elem.insert(0, jc)
    
    # 4. 调用标准修订写入逻辑
    return _write_revision_standard(para_elem, original, corrected, rpr_elem, ppr_elem)
```

### 建议3：改进 run 属性继承
```python
def _get_rpr_list(para_elem):
    """
    获取段落中所有 run 的样式属性。
    返回 [(start_pos, end_pos, rpr_elem), ...]
    """
    ns_w = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
    rpr_list = []
    pos = 0
    
    for r in para_elem.findall(f"{{{ns_w}}}r"):
        text = ""
        for t in r.findall(f"{{{ns_w}}}t"):
            text += t.text or ""
        
        if text:
            rpr = r.find(f"{{{ns_w}}}rPr")
            rpr_list.append((pos, pos + len(text), rpr))
            pos += len(text)
    
    return rpr_list

def _apply_rpr_to_text(text: str, rpr_list: list) -> list:
    """
    根据原始文字的样式信息，为修改后的文字应用样式。
    返回 [(text_segment, rpr_elem), ...]
    """
    # 实现样式映射逻辑
    pass
```

### 建议4：添加表格边框保护
```python
def _protect_table_structure(doc: Document):
    """
    在处理前保护表格结构。
    确保表格边框、单元格属性不被修改。
    """
    ns_w = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
    
    for table in doc.tables:
        # 保存表格属性
        tbl_elem = table._element
        tbl_pr = tbl_elem.find(f"{{{ns_w}}}tblPr")
        
        if tbl_pr is not None:
            # 确保表格边框存在
            tbl_borders = tbl_pr.find(f"{{{ns_w}}}tblBorders")
            if tbl_borders is None:
                # 添加默认边框
                tbl_borders = OxmlElement("w:tblBorders")
                # ... 设置边框属性 ...
                tbl_pr.append(tbl_borders)
        
        # 保护每个单元格的属性
        for row in table.rows:
            for cell in row.cells:
                tc_elem = cell._element
                tc_pr = tc_elem.find(f"{{{ns_w}}}tcPr")
                
                if tc_pr is not None:
                    # 确保单元格边框存在
                    tc_borders = tc_pr.find(f"{{{ns_w}}}tcBorders")
                    if tc_borders is None:
                        # 继承表格边框
                        pass
```

## 🎯 优先级修复顺序

1. **高优先级**：修复建议1 - 保留段落属性的正确位置
   - 这是最可能导致对齐问题的原因
   - 修复简单，影响大

2. **高优先级**：修复建议2 - 为表格单元格添加特殊处理
   - 确保表格单元格的对齐方式不丢失
   - 需要区分正文段落和表格段落

3. **中优先级**：修复建议4 - 添加表格边框保护
   - 防止表格线位置错误
   - 需要在处理前后验证表格结构

4. **低优先级**：修复建议3 - 改进 run 属性继承
   - 处理复杂样式的情况
   - 实现较复杂，但影响相对较小

## 🧪 测试建议

### 测试用例1：简单表格
创建包含以下内容的表格：
```
| 标题1 | 标题2 | 标题3 |
|-------|-------|-------|
| 内容1 | 内容2 | 内容3 |
| 内容4 | 内容5 | 内容6 |
```

### 测试用例2：带格式的表格
- 加粗的标题行
- 居中对齐的单元格
- 不同字体大小

### 测试用例3：复杂表格
- 合并单元格
- 嵌套表格
- 带边框样式

### 验证点
1. 表格边框是否完整
2. 单元格对齐方式是否正确
3. 文字是否与其他行对齐
4. 表格线位置是否正确
5. 修订标记是否正确显示

## 📝 总结

**根本原因**：
`_write_revision()` 函数在处理表格单元格段落时，没有正确保留和恢复段落属性（w:pPr），特别是对齐方式（w:jc）和其他格式属性。

**核心问题**：
1. 段落属性（w:pPr）的位置可能被破坏
2. 表格单元格和正文段落使用相同的处理逻辑，没有区分
3. 缺少对表格结构的保护机制

**建议的修复方案**：
优先实现建议1和建议2，确保段落属性正确保留，并为表格单元格添加特殊处理逻辑。
