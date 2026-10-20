"""可视化模块。

提供成本会计常用的四类图形，并自动保存到项目 chart 文件夹：
1. 成本结构饼图（plot_cost_pie）；
2. 成本项目结构分析图（plot_structure_chart）；
3. 本期/上期、计划/实际差异对比图（plot_comparison_chart）；
4. 多期趋势图（plot_trend_chart）。

说明：
- 使用 Agg 无界面后端，VSCode/服务器环境无需弹窗即可保存图片；
- 自动检测 Windows 的微软雅黑、黑体等中文字体，解决中文显示为方框的问题；
- 同时设置 axes.unicode_minus=False，修复负号显示异常。
"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

from utils import CHART_DIR, ensure_dirs

try:
    import matplotlib

    matplotlib.use("Agg")  # 无界面后端，保证在 VSCode 中也能保存图片
    import matplotlib.font_manager as font_manager
    import matplotlib.pyplot as plt
    from matplotlib.ticker import PercentFormatter

    _MATPLOTLIB_AVAILABLE = True
    _IMPORT_ERROR: Optional[Exception] = None
except Exception as exc:  # 缺少依赖时给出中文提示，而不是让程序崩溃
    plt = None  # type: ignore[assignment]
    font_manager = None  # type: ignore[assignment]
    PercentFormatter = None  # type: ignore[assignment]
    _MATPLOTLIB_AVAILABLE = False
    _IMPORT_ERROR = exc


def _configure_chinese_font() -> str:
    """检测可用中文字体，解决 matplotlib 中文乱码/方框问题。"""
    if not _MATPLOTLIB_AVAILABLE:
        return "未加载"
    candidates = [
        "Microsoft YaHei",
        "Microsoft YaHei UI",
        "SimHei",
        "SimSun",
        "Noto Sans CJK SC",
        "Source Han Sans SC",
        "PingFang SC",
        "Arial Unicode MS",
    ]
    available = {font.name for font in font_manager.fontManager.ttflist}

    # Windows 字体缓存偶尔不完整，主动注册常见字体文件。
    windows_font_dir = Path("C:/Windows/Fonts")
    for font_file in (
        windows_font_dir / "msyh.ttc",
        windows_font_dir / "msyhbd.ttc",
        windows_font_dir / "simhei.ttf",
        windows_font_dir / "simsun.ttc",
    ):
        if font_file.exists():
            try:
                font_manager.fontManager.addfont(str(font_file))
                available.add(font_manager.FontProperties(fname=str(font_file)).get_name())
            except Exception:
                continue

    selected = next((name for name in candidates if name in available), "DejaVu Sans")
    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["font.sans-serif"] = [selected, "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False
    return selected


CHINESE_FONT = _configure_chinese_font()


def _safe_chart_path(filename: Optional[str], prefix: str) -> Path:
    """生成 chart 文件夹中的唯一图片路径。"""
    ensure_dirs()
    raw = filename or prefix
    safe = re.sub(r"[^0-9A-Za-z_\-\u4e00-\u9fff]+", "_", raw).strip("_") or prefix
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
    return CHART_DIR / f"{safe}_{timestamp}.png"


def _save(fig: Any, filename: Optional[str], prefix: str) -> Optional[Path]:
    """保存图片、关闭画布并返回路径。"""
    if not _MATPLOTLIB_AVAILABLE:
        print(f"[绘图提示] 未安装 matplotlib，无法生成图片。原因：{_IMPORT_ERROR}")
        return None
    path = _safe_chart_path(filename, prefix)
    fig.savefig(path, dpi=160, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"[图片已保存] {path}")
    return path


def _check_values(labels: Sequence[str], values: Sequence[Any], name: str = "数据") -> list[float]:
    """校验绘图数据：标签与数值等长，数值非负且合计大于 0。"""
    if len(labels) != len(values):
        raise ValueError(f"{name}的标签数量与数值数量不一致。")
    if not labels:
        raise ValueError(f"{name}不能为空。")
    numbers: list[float] = []
    for label, value in zip(labels, values):
        try:
            number = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{name}“{label}”的数值无效：{value!r}") from exc
        if number < 0:
            raise ValueError(f"{name}“{label}”不能为负数。")
        numbers.append(number)
    if sum(numbers) <= 0:
        raise ValueError(f"{name}合计必须大于 0。")
    return numbers


def plot_cost_pie(
    labels: Sequence[str],
    values: Sequence[Any],
    title: str = "成本结构饼图",
    filename: Optional[str] = None,
) -> Optional[Path]:
    """绘制成本结构饼图，显示各成本项目占比。"""
    if not _MATPLOTLIB_AVAILABLE:
        print(f"[绘图提示] 未安装 matplotlib，无法生成图片。原因：{_IMPORT_ERROR}")
        return None
    numbers = _check_values(labels, values)
    total = sum(numbers)
    percentages = [value / total * 100 for value in numbers]

    fig, ax = plt.subplots(figsize=(8.6, 6.0))
    colors = ["#2E86AB", "#F18F01", "#C73E1D", "#6A994E", "#7B2CBF", "#8D99AE"]
    wedges, _texts, autotexts = ax.pie(
        numbers,
        labels=list(labels),
        autopct=lambda pct: f"{pct:.1f}%" if pct >= 3 else "",
        startangle=90,
        counterclock=False,
        colors=colors[: len(numbers)],
        wedgeprops={"linewidth": 1.2, "edgecolor": "white"},
        pctdistance=0.72,
    )
    for text in autotexts:
        text.set_fontsize(9)
        text.set_color("white")
        text.set_fontweight("bold")
    ax.set_title(f"{title}\n（合计：{total:,.2f} 元）", fontsize=14, pad=16)
    ax.axis("equal")
    legend_labels = [
        f"{label}：{value:,.2f} 元（{pct:.1f}%）"
        for label, value, pct in zip(labels, numbers, percentages)
    ]
    ax.legend(
        wedges,
        legend_labels,
        title="成本项目",
        loc="center left",
        bbox_to_anchor=(1.02, 0.5),
        frameon=False,
        fontsize=9,
    )
    return _save(fig, filename, "cost_pie")


def plot_structure_chart(
    labels: Sequence[str],
    values: Sequence[Any],
    title: str = "成本项目结构分析",
    filename: Optional[str] = None,
) -> Optional[Path]:
    """绘制横向条形结构图，按金额从大到小排列并标注占比。"""
    if not _MATPLOTLIB_AVAILABLE:
        print(f"[绘图提示] 未安装 matplotlib，无法生成图片。原因：{_IMPORT_ERROR}")
        return None
    numbers = _check_values(labels, values)
    total = sum(numbers)
    pairs = sorted(zip(labels, numbers), key=lambda item: item[1], reverse=True)
    sorted_labels = [item[0] for item in pairs]
    sorted_values = [item[1] for item in pairs]
    percentages = [value / total for value in sorted_values]

    fig, ax = plt.subplots(figsize=(9.2, max(4.6, 0.55 * len(sorted_labels) + 2.0)))
    bars = ax.barh(sorted_labels, sorted_values, color="#2E86AB", height=0.58)
    ax.invert_yaxis()
    ax.set_xlabel("金额（元）")
    ax.set_title(f"{title}\n（合计：{total:,.2f} 元）", fontsize=14, pad=14)
    ax.grid(axis="x", linestyle="--", alpha=0.28)
    max_value = max(sorted_values)
    for bar, value, pct in zip(bars, sorted_values, percentages):
        offset = max_value * 0.015 if max_value > 0 else 0.01
        ax.text(
            bar.get_width() + offset,
            bar.get_y() + bar.get_height() / 2,
            f"{value:,.2f} 元（{pct * 100:.1f}%）",
            va="center",
            fontsize=9,
        )
    ax.set_xlim(0, max_value * 1.22 if max_value > 0 else 1)
    fig.tight_layout()
    return _save(fig, filename, "cost_structure")



def plot_comparison_chart(
    labels: Sequence[str],
    series: Mapping[str, Sequence[Any]],
    title: str = "成本对比分析",
    filename: Optional[str] = None,
    *,
    ylabel: str = "金额（元）",
) -> Optional[Path]:
    """绘制分组柱状对比图。

    series 示例：{"本期实际": [100, 200], "上期实际": [90, 210]}。
    """
    if not _MATPLOTLIB_AVAILABLE:
        print(f"[绘图提示] 未安装 matplotlib，无法生成图片。原因：{_IMPORT_ERROR}")
        return None
    if not labels:
        raise ValueError("对比图的分类标签不能为空。")
    if not series:
        raise ValueError("对比图至少需要一组数据。")
    for name, values in series.items():
        if len(values) != len(labels):
            raise ValueError(f"数据系列“{name}”的数量与分类标签数量不一致。")

    fig, ax = plt.subplots(figsize=(max(8.0, 0.9 * len(labels) + 3.0), 5.0))
    count = len(series)
    width = min(0.8 / count, 0.3)
    colors = ["#2E86AB", "#F18F01", "#6A994E", "#C73E1D", "#7B2CBF"]
    x_positions = list(range(len(labels)))
    for index, (name, values) in enumerate(series.items()):
        numeric = [float(value) for value in values]
        offset = (index - (count - 1) / 2) * width
        bars = ax.bar(
            [x + offset for x in x_positions],
            numeric,
            width=width,
            label=name,
            color=colors[index % len(colors)],
        )
        for bar, value in zip(bars, numeric):
            ax.annotate(
                f"{value:,.0f}",
                xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
                xytext=(0, 3),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=7.5,
            )
    ax.set_xticks(x_positions)
    ax.set_xticklabels(list(labels))
    ax.set_ylabel(ylabel)
    ax.set_title(title, fontsize=14, pad=12)
    ax.legend(frameon=False)
    ax.grid(axis="y", linestyle="--", alpha=0.28)
    if min([float(v) for values in series.values() for v in values]) >= 0:
        ax.set_ylim(bottom=0)
    fig.tight_layout()
    return _save(fig, filename, "cost_comparison")


def plot_trend_chart(
    labels: Sequence[str],
    series: Mapping[str, Sequence[Any]],
    title: str = "成本趋势分析",
    filename: Optional[str] = None,
    *,
    ylabel: str = "金额（元）",
) -> Optional[Path]:
    """绘制折线趋势图，适合多期实际成本、计划成本对比。"""
    if not _MATPLOTLIB_AVAILABLE:
        print(f"[绘图提示] 未安装 matplotlib，无法生成图片。原因：{_IMPORT_ERROR}")
        return None
    if not labels or not series:
        raise ValueError("趋势图需要分类标签和至少一组数据。")
    for name, values in series.items():
        if len(values) != len(labels):
            raise ValueError(f"数据系列“{name}”的数量与分类标签数量不一致。")

    fig, ax = plt.subplots(figsize=(max(8.0, 0.9 * len(labels) + 3.0), 4.8))
    colors = ["#2E86AB", "#F18F01", "#6A994E", "#C73E1D", "#7B2CBF"]
    for index, (name, values) in enumerate(series.items()):
        numeric = [float(value) for value in values]
        ax.plot(
            list(range(len(labels))),
            numeric,
            marker="o",
            linewidth=2,
            label=name,
            color=colors[index % len(colors)],
        )
        for x, value in enumerate(numeric):
            ax.annotate(
                f"{value:,.0f}",
                xy=(x, value),
                xytext=(0, 7),
                textcoords="offset points",
                ha="center",
                fontsize=8,
            )
    ax.set_xticks(list(range(len(labels))))
    ax.set_xticklabels(list(labels))
    ax.set_ylabel(ylabel)
    ax.set_title(title, fontsize=14, pad=12)
    ax.legend(frameon=False)
    ax.grid(linestyle="--", alpha=0.28)
    fig.tight_layout()
    return _save(fig, filename, "cost_trend")

