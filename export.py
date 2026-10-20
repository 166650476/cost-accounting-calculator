"""CSV 导出模块。

功能：
1. 每次计算自动生成一份“完整计算记录”CSV，包含题意、公式、步骤、表格、分录、总结；
2. 同时向 output/计算记录汇总.csv 追加一行摘要，便于在 Excel 中筛选、统计；
3. 所有 CSV 均使用 utf-8-sig（带 BOM），Windows 下用 Excel 双击打开不会乱码；
4. 支持单独导出一张表格，供课程作业直接使用。
"""

from __future__ import annotations

import csv
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, List, Optional, Sequence, Tuple

from utils import OUTPUT_DIR, ensure_dirs, format_money


SUMMARY_FILE = OUTPUT_DIR / "计算记录汇总.csv"
SUMMARY_HEADERS = ["记录时间", "章节", "计算项目", "主要结论", "明细CSV文件"]


def _safe_filename(text: str, fallback: str = "计算记录", max_length: int = 60) -> str:
    """把章节名/项目名转换为 Windows 可用的文件名。"""
    clean = re.sub(r'[\\/:*?"<>|\r\n\t]+', "_", str(text)).strip(" ._")
    clean = re.sub(r"_+", "_", clean)
    if not clean:
        clean = fallback
    return clean[:max_length]


def _stringify(value: Any) -> str:
    """把单元格内容转换为适合 CSV 写入的文本。"""
    if value is None:
        return ""
    if isinstance(value, float):
        return format_money(value) if abs(value) >= 0.005 else f"{value:.6f}".rstrip("0").rstrip(".")
    return str(value)


def _write_rows(path: Path, rows: Iterable[Sequence[Any]]) -> Path:
    """写入 CSV 行，统一使用 UTF-8 BOM。"""
    ensure_dirs()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        for row in rows:
            writer.writerow([_stringify(cell) for cell in row])
    return path


def _ensure_summary() -> None:
    """确保汇总文件存在且带有表头。"""
    ensure_dirs()
    if not SUMMARY_FILE.exists() or SUMMARY_FILE.stat().st_size == 0:
        with SUMMARY_FILE.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(SUMMARY_HEADERS)


def append_summary(chapter: str, title: str, conclusion: str, detail_file: str) -> Path:
    """向计算记录汇总.csv 追加一行摘要。"""
    _ensure_summary()
    with SUMMARY_FILE.open("a", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                chapter,
                title,
                conclusion,
                detail_file,
            ]
        )
    return SUMMARY_FILE


def save_calculation(
    chapter: str,
    title: str,
    *,
    question: str = "",
    formulas: Optional[Sequence[str]] = None,
    steps: Optional[Sequence[str]] = None,
    tables: Optional[Sequence[Tuple[str, Sequence[Any], Sequence[Sequence[Any]]]]] = None,
    journal: Optional[Sequence[str]] = None,
    summary: Optional[Sequence[str]] = None,
    conclusion: Optional[str] = None,
) -> Path:
    """保存一次完整计算。

    参数：
        chapter: 章节名称，例如“第二章 要素费用”。
        title: 计算项目名称。
        question: 文字题意。
        formulas: 公式列表。
        steps: 分步计算过程。
        tables: [(表格标题, 表头, 数据行), ...]。
        journal: 会计分录行。
        summary: 总结/提示行。
        conclusion: 写入汇总表的一行结论；默认取 summary 的第一行。
    """
    ensure_dirs()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
    filename = f"{_safe_filename(chapter)}_{_safe_filename(title)}_{timestamp}.csv"
    path = OUTPUT_DIR / filename

    rows: List[List[Any]] = []
    rows.append(["成本会计学 Python 综合计算器——计算记录"])
    rows.append(["章节", chapter])
    rows.append(["计算项目", title])
    rows.append(["生成时间", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
    rows.append(["使用说明", "本记录为学习验算用途，案例为模拟教学案例。"])

    if question:
        rows.append([])
        rows.append(["一、文字题意"])
        for line in str(question).splitlines():
            rows.append([line])

    if formulas:
        rows.append([])
        rows.append(["二、计算公式"])
        for item in formulas:
            rows.append([item])

    if steps:
        rows.append([])
        rows.append(["三、分步计算过程"])
        for index, item in enumerate(steps, start=1):
            rows.append([f"（{index}）", item])

    if tables:
        rows.append([])
        rows.append(["四、计算表"])
        for table_title, headers, body in tables:
            rows.append([f"【{table_title}】"])
            rows.append(list(headers))
            for body_row in body:
                rows.append(list(body_row))
            rows.append([])

    if journal:
        rows.append(["五、会计分录（单位：元）"])
        for item in journal:
            rows.append([item])

    if summary:
        rows.append([])
        rows.append(["六、总结与核对提示"])
        for item in summary:
            rows.append([item])

    _write_rows(path, rows)
    detail_name = path.name
    conclusion_text = conclusion
    if conclusion_text is None:
        conclusion_text = summary[0] if summary else "计算完成，详见明细CSV。"
    append_summary(chapter, title, conclusion_text, detail_name)
    print(f"\n[CSV已保存] {path}")
    print(f"[汇总记录] {SUMMARY_FILE}")
    return path


def save_table(
    filename: str,
    headers: Sequence[Any],
    rows: Sequence[Sequence[Any]],
    *,
    title: Optional[str] = None,
) -> Path:
    """单独导出一张表格到 output 文件夹，便于直接复制到 Excel。"""
    ensure_dirs()
    safe_name = _safe_filename(filename, "表格", max_length=80)
    if not safe_name.lower().endswith(".csv"):
        safe_name += ".csv"
    path = OUTPUT_DIR / safe_name
    content: List[List[Any]] = []
    if title:
        content.append([title])
        content.append([])
    content.append(list(headers))
    content.extend([list(row) for row in rows])
    _write_rows(path, content)
    print(f"[表格已导出] {path}")
    return path


def get_summary_path() -> Path:
    """返回汇总文件路径。"""
    return SUMMARY_FILE
