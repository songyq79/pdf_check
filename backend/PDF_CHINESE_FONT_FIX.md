# PDF 图表中文乱码问题解决方案

## 问题描述
智能评价下载的 PDF 报告中，二维评价分析图（雷达图）出现中文乱码。

## 当前代码状态
✅ 代码已经有中文字体配置（`chart_generator.py` 第 13-26 行）
⚠️ 但可能存在以下问题：
1. 服务器上没有安装中文字体
2. 字体探测逻辑可能失败
3. 字体缓存问题

## 技术解决方案

### 方案1：改进字体探测逻辑（推荐）✅

#### 当前代码问题
```python
def _find_cjk_font() -> list:
    import matplotlib.font_manager as fm
    available = {f.name for f in fm.fontManager.ttflist}
    candidates = [
        'Noto Sans CJK SC', 'Noto Sans CJK JP', 'Noto Sans CJK TC',
        'WenQuanYi Zen Hei', 'WenQuanYi Micro Hei',
        'Source Han Sans CN', 'Source Han Sans',
        'SimHei', 'Microsoft YaHei', 'PingFang SC',
        'Heiti SC', 'STHeiti', 'Arial Unicode MS',
    ]
    found = [c for c in candidates if c in available]
    return found + ['DejaVu Sans']  # DejaVu Sans 作保底
```

**问题**：
- 如果所有候选字体都不存在，会回退到 DejaVu Sans（不支持中文）
- 没有日志输出，无法知道使用了哪个字体
- 字体名称可能不完全匹配

#### 改进方案
```python
def _find_cjk_font() -> list:
    """
    动态探测可用的中文字体。
    优先级：Noto Sans CJK > 文泉驿 > 思源黑体 > Windows字体 > 回退
    """
    import matplotlib.font_manager as fm
    
    # 获取所有可用字体（包括字体文件路径）
    available_fonts = {f.name: f.fname for f in fm.fontManager.ttflist}
    
    # 候选字体列表（按优先级排序）
    candidates = [
        # Linux 服务器常见字体
        'Noto Sans CJK SC',      # Google Noto 简体中文
        'Noto Sans CJK TC',      # Google Noto 繁体中文
        'Noto Sans CJK JP',      # Google Noto 日文
        'WenQuanYi Zen Hei',     # 文泉驿正黑
        'WenQuanYi Micro Hei',   # 文泉驿微米黑
        'Source Han Sans CN',    # 思源黑体简体
        'Source Han Sans SC',    # 思源黑体简体（另一种命名）
        'Source Han Sans',       # 思源黑体
        # Windows 字体
        'SimHei',                # 黑体
        'Microsoft YaHei',       # 微软雅黑
        'SimSun',                # 宋体
        # macOS 字体
        'PingFang SC',           # 苹方简体
        'Heiti SC',              # 黑体简体
        'STHeiti',               # 华文黑体
        'Arial Unicode MS',      # Arial Unicode（支持中文）
    ]
    
    # 查找第一个可用的字体
    found = []
    for candidate in candidates:
        if candidate in available_fonts:
            found.append(candidate)
            logger.info(f"[字体] 找到中文字体: {candidate} ({available_fonts[candidate]})")
    
    if not found:
        logger.warning("[字体] 未找到任何中文字体，将使用 DejaVu Sans（不支持中文）")
        logger.warning("[字体] 建议安装: sudo apt-get install fonts-noto-cjk")
    
    # 添加回退字体
    found.append('DejaVu Sans')
    
    logger.info(f"[字体] 最终字体列表: {found}")
    return found

# 在模块加载时配置字体
matplotlib.rcParams['font.sans-serif'] = _find_cjk_font()
matplotlib.rcParams['axes.unicode_minus'] = False
logger.info(f"[字体] matplotlib 配置完成: {matplotlib.rcParams['font.sans-serif']}")
```

### 方案2：在 Docker 容器中安装中文字体

#### 修改 Dockerfile
```dockerfile
# 在 backend/Dockerfile 中添加
RUN apt-get update && apt-get install -y \
    fonts-noto-cjk \
    fonts-wqy-zenhei \
    fonts-wqy-microhei \
    && rm -rf /var/lib/apt/lists/*

# 清除 matplotlib 字体缓存
RUN rm -rf ~/.cache/matplotlib
```

#### 或者使用 requirements.txt 后的脚本
```bash
# 在容器启动脚本中添加
apt-get update
apt-get install -y fonts-noto-cjk
rm -rf ~/.cache/matplotlib
```

### 方案3：手动指定字体文件路径（最可靠）

#### 下载字体文件
```bash
# 在项目中创建字体目录
mkdir -p backend/fonts

# 下载 Noto Sans CJK SC 字体
wget https://github.com/googlefonts/noto-cjk/raw/main/Sans/OTF/SimplifiedChinese/NotoSansCJKsc-Regular.otf \
     -O backend/fonts/NotoSansCJKsc-Regular.otf
```

#### 修改代码直接使用字体文件
```python
from pathlib import Path
import matplotlib.font_manager as fm

def _setup_chinese_font():
    """
    直接使用项目内置的字体文件。
    这是最可靠的方案，不依赖系统字体。
    """
    # 字体文件路径
    font_dir = Path(__file__).parent.parent.parent / "fonts"
    font_path = font_dir / "NotoSansCJKsc-Regular.otf"
    
    if font_path.exists():
        # 注册字体
        fm.fontManager.addfont(str(font_path))
        font_name = fm.FontProperties(fname=str(font_path)).get_name()
        logger.info(f"[字体] 使用内置字体: {font_name} ({font_path})")
        return [font_name, 'DejaVu Sans']
    else:
        logger.warning(f"[字体] 内置字体不存在: {font_path}")
        # 回退到方案1
        return _find_cjk_font()

matplotlib.rcParams['font.sans-serif'] = _setup_chinese_font()
matplotlib.rcParams['axes.unicode_minus'] = False
```

### 方案4：使用 Pillow 生成图片（备选方案）

如果 matplotlib 字体问题难以解决，可以考虑使用 Pillow 库直接绘制图表：

```python
from PIL import Image, ImageDraw, ImageFont
import numpy as np

def generate_radar_chart_with_pillow(dimensions, output_path):
    """使用 Pillow 生成雷达图（支持中文）"""
    # 创建画布
    img = Image.new('RGB', (800, 800), 'white')
    draw = ImageDraw.Draw(img)
    
    # 加载中文字体
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc", 20)
    except:
        font = ImageFont.load_default()
    
    # 绘制雷达图...
    # （实现略）
    
    img.save(output_path)
```

## 推荐实施步骤

### 第一步：改进字体探测逻辑（立即实施）
修改 `chart_generator.py`，添加详细的日志输出，方便排查问题。

### 第二步：在服务器上安装字体
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y fonts-noto-cjk fonts-wqy-zenhei

# CentOS/RHEL
sudo yum install -y google-noto-sans-cjk-fonts wqy-zenhei-fonts

# 清除 matplotlib 缓存
rm -rf ~/.cache/matplotlib
python -c "import matplotlib.font_manager as fm; fm._rebuild()"
```

### 第三步：验证字体
```python
# 运行测试脚本
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt

# 列出所有可用字体
fonts = [f.name for f in fm.fontManager.ttflist if 'CJK' in f.name or 'Hei' in f.name]
print("可用的中文字体:", fonts)

# 测试绘图
plt.rcParams['font.sans-serif'] = ['Noto Sans CJK SC']
plt.figure()
plt.title('测试中文显示')
plt.text(0.5, 0.5, '这是中文测试', ha='center', va='center', fontsize=20)
plt.savefig('test_chinese.png')
print("测试图片已保存: test_chinese.png")
```

### 第四步：Docker 部署配置
如果使用 Docker，在 Dockerfile 中添加：
```dockerfile
FROM python:3.11-slim

# 安装中文字体
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    fonts-noto-cjk \
    fonts-wqy-zenhei \
    && rm -rf /var/lib/apt/lists/*

# 清除字体缓存
RUN rm -rf /root/.cache/matplotlib

# ... 其他配置 ...
```

## 常见问题排查

### 问题1：字体已安装但仍然乱码
**原因**：matplotlib 字体缓存未更新
**解决**：
```bash
rm -rf ~/.cache/matplotlib
python -c "import matplotlib.font_manager as fm; fm._rebuild()"
```

### 问题2：Docker 容器中字体不生效
**原因**：容器内没有安装字体
**解决**：在 Dockerfile 中添加字体安装命令

### 问题3：字体名称不匹配
**原因**：不同系统字体名称可能不同
**解决**：使用字体文件路径而不是字体名称

### 问题4：权限问题
**原因**：无权限访问字体文件或缓存目录
**解决**：
```bash
chmod -R 755 /usr/share/fonts/
chmod -R 755 ~/.cache/matplotlib
```

## 测试验证

### 测试脚本
```python
# test_chinese_chart.py
from pathlib import Path
from backend.app.core.evaluator.chart_generator import generate_radar_chart

# 测试数据
dimensions = {
    "学术规范性": 85,
    "逻辑与创新性": 80,
    "语言质量": 90,
    "文献引用规范性": 88
}

# 生成图表
output_path = Path("test_radar_chart.png")
generate_radar_chart(dimensions, output_path, title="论文评价雷达图")

print(f"图表已生成: {output_path}")
print("请检查图表中的中文是否正常显示")
```

### 运行测试
```bash
cd backend
python test_chinese_chart.py
```

## 总结

**最简单的解决方案**（推荐）：
1. 改进字体探测逻辑（添加日志）
2. 在服务器上安装 `fonts-noto-cjk`
3. 清除 matplotlib 缓存

**最可靠的解决方案**：
1. 在项目中内置字体文件
2. 代码中直接指定字体文件路径
3. 不依赖系统字体

**时间估算**：
- 方案1（改进代码）：10 分钟
- 方案2（安装字体）：5 分钟
- 方案3（内置字体）：20 分钟

建议先实施方案1+方案2，如果还有问题再考虑方案3。
