"""
图表生成器 - 生成评价维度雷达图
使用matplotlib生成评价维度的可视化图表
"""

import matplotlib
# 必须在导入 pyplot 之前设置后端为非交互式，避免 Tkinter 线程问题
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

# 设置中文字体支持：动态探测可用字体，优先选用 Linux 服务器上常见的 CJK 字体
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
            logger.info(f"[字体] 找到中文字体: {candidate}")
    
    if not found:
        logger.warning("[字体] 未找到任何中文字体，将使用 DejaVu Sans（不支持中文）")
        logger.warning("[字体] 建议安装: sudo apt-get install fonts-noto-cjk")
        logger.warning(f"[字体] 当前可用字体: {list(available_fonts.keys())[:10]}...")
    
    # 添加回退字体
    found.append('DejaVu Sans')
    
    logger.info(f"[字体] 最终字体列表: {found}")
    return found

matplotlib.rcParams['font.sans-serif'] = _find_cjk_font()
matplotlib.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
logger.info(f"[字体] matplotlib 配置完成: {matplotlib.rcParams['font.sans-serif']}")

class ChartGenerator:
    """评价图表生成器"""

    def __init__(self):
        """初始化图表生成器"""
        pass

    def generate_radar_chart(
        self,
        dimensions: Dict[str, int],
        output_path: Path,
        title: str = "论文评价雷达图",
        figsize: tuple = (8, 8)
    ) -> Path:
        """
        生成雷达图

        :param dimensions: 维度和分数的字典，例如 {"学术规范性": 85, "逻辑与创新性": 80}
        :param output_path: 输出文件路径
        :param title: 图表标题
        :param figsize: 图表尺寸
        :return: 生成的图表文件路径
        """
        try:
            # 提取维度名称和分数
            labels = list(dimensions.keys())
            values = list(dimensions.values())

            # 计算雷达图的角度
            num_vars = len(labels)
            angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()

            # 闭合雷达图（首尾相接）
            values += values[:1]
            angles += angles[:1]

            # 创建图表
            fig, ax = plt.subplots(figsize=figsize, subplot_kw=dict(projection='polar'))

            # 绘制雷达图
            ax.plot(angles, values, 'o-', linewidth=2, color='#1f77b4', label='得分')
            ax.fill(angles, values, alpha=0.25, color='#1f77b4')

            # 设置刻度标签
            ax.set_xticks(angles[:-1])
            ax.set_xticklabels(labels, fontsize=12)

            # 设置Y轴范围（0-100分）
            ax.set_ylim(0, 100)
            ax.set_yticks([20, 40, 60, 80, 100])
            ax.set_yticklabels(['20', '40', '60', '80', '100'], fontsize=10)

            # 添加网格
            ax.grid(True, linestyle='--', alpha=0.7)

            # 添加标题
            plt.title(title, fontsize=16, fontweight='bold', pad=20)

            # 添加图例
            plt.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))

            # 保存图表
            output_path.parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
            plt.close(fig)

            logger.info(f"雷达图生成成功: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"雷达图生成失败: {str(e)}")
            raise ChartGenerationError(f"雷达图生成失败: {str(e)}")

    def generate_bar_chart(
        self,
        dimensions: Dict[str, int],
        output_path: Path,
        title: str = "论文评价柱状图",
        figsize: tuple = (10, 6)
    ) -> Path:
        """
        生成柱状图（备用选项）

        :param dimensions: 维度和分数的字典
        :param output_path: 输出文件路径
        :param title: 图表标题
        :param figsize: 图表尺寸
        :return: 生成的图表文件路径
        """
        try:
            # 提取维度名称和分数
            labels = list(dimensions.keys())
            values = list(dimensions.values())

            # 创建图表
            fig, ax = plt.subplots(figsize=figsize)

            # 创建柱状图
            bars = ax.bar(range(len(labels)), values, color='#1f77b4', alpha=0.8)

            # 在柱子上添加数值标签
            for bar in bars:
                height = bar.get_height()
                ax.text(
                    bar.get_x() + bar.get_width() / 2.,
                    height,
                    f'{int(height)}',
                    ha='center',
                    va='bottom',
                    fontsize=12,
                    fontweight='bold'
                )

            # 设置坐标轴
            ax.set_xticks(range(len(labels)))
            ax.set_xticklabels(labels, fontsize=12, rotation=15, ha='right')
            ax.set_ylabel('得分', fontsize=12)
            ax.set_ylim(0, 100)
            ax.set_yticks(range(0, 101, 20))

            # 添加网格
            ax.grid(True, axis='y', linestyle='--', alpha=0.7)

            # 添加标题
            ax.set_title(title, fontsize=16, fontweight='bold', pad=20)

            # 调整布局
            plt.tight_layout()

            # 保存图表
            output_path.parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
            plt.close(fig)

            logger.info(f"柱状图生成成功: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"柱状图生成失败: {str(e)}")
            raise ChartGenerationError(f"柱状图生成失败: {str(e)}")


class ChartGenerationError(Exception):
    """图表生成错误"""
    pass


# 工厂函数
def generate_radar_chart(
    dimensions: Dict[str, int],
    output_path: Path,
    title: str = "论文评价雷达图"
) -> Path:
    """
    生成雷达图的便捷函数

    :param dimensions: 维度和分数字典
    :param output_path: 输出路径
    :param title: 图表标题
    :return: 图表文件路径
    """
    generator = ChartGenerator()
    return generator.generate_radar_chart(dimensions, output_path, title)


def generate_bar_chart(
    dimensions: Dict[str, int],
    output_path: Path,
    title: str = "论文评价柱状图"
) -> Path:
    """
    生成柱状图的便捷函数

    :param dimensions: 维度和分数字典
    :param output_path: 输出路径
    :param title: 图表标题
    :return: 图表文件路径
    """
    generator = ChartGenerator()
    return generator.generate_bar_chart(dimensions, output_path, title)