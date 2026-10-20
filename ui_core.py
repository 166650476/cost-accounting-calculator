"""Streamlit 公共界面组件。

本模块负责：
- 统一定义一次成本计算的结果对象 CostResult；
- 把计算过程自动保存为明细 CSV；
- 在 Streamlit 中渲染 KPI、题意、公式、步骤、表格、分录、图表和下载按钮；
- 提供金额、数量、百分比、数据编辑表格等输入控件。

业务章节只负责计算，不直接处理页面布局。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

import pandas as pd
import streamlit as st

import export
from utils import OUTPUT_DIR, ValidationError, ensure_dirs


@dataclass
class CostResult:
    """一次成本计算的完整结果，供 Streamlit 渲染和 CSV 下载。"""

    chapter: str
    title: str
    description: str = ""
    question: str = ""
    formulas: List[str] = field(default_factory=list)
    steps: List[str] = field(default_factory=list)
    tables: List[Tuple[str, Sequence[Any], Sequence[Sequence[Any]]]] = field(default_factory=list)
    journal: List[str] = field(default_factory=list)
    summary: List[str] = field(default_factory=list)
    metrics: Dict[str, str] = field(default_factory=dict)
    chart_paths: List[str] = field(default_factory=list)
    conclusion: str = ""
    csv_path: Optional[Path] = None


def safe_filename(text: str) -> str:
    """把项目名称转换为安全文件名。"""
    cleaned = re.sub(r'[<>:"/\\|?*]+', "_", text).strip(" .")
    return cleaned or "成本计算结果"


def calculate_and_store(session_key: str, builder: Callable[[], CostResult]) -> Optional[CostResult]:
    """执行计算、保存 CSV，并把结果写入 session_state。"""
    try:
        result = builder()
        if not isinstance(result, CostResult):
            raise TypeError("计算函数必须返回 CostResult。")
        path = export.save_calculation(
            result.chapter,
            result.title,
            question=result.question,
            formulas=result.formulas,
            steps=result.steps,
            tables=result.tables,
            journal=result.journal,
            summary=result.summary,
            conclusion=result.conclusion or (result.summary[0] if result.summary else "计算完成。"),
        )
        result.csv_path = path
        st.session_state[session_key] = result
        st.session_state[f"{session_key}_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.session_state[f"{session_key}_exported"] = True
        st.toast("计算完成，结果已保存", icon=":material/check_circle:")
        return result
    except (ValidationError, ValueError, ZeroDivisionError) as exc:
        st.error(f"输入或计算错误：{exc}", icon=":material/error:")
        return None
    except Exception as exc:
        st.error(f"计算失败：{exc}", icon=":material/error:")
        with st.expander("错误详情", expanded=False):
            st.exception(exc)
        return None


def render_saved(session_key: str) -> None:
    """如果当前页面已有计算结果，则重新渲染最近一次结果。"""
    result = st.session_state.get(session_key)
    if isinstance(result, CostResult):
        render_result(result, session_key)


def render_result(result: CostResult, session_key: str) -> None:
    """渲染完整计算书。"""
    with st.container(border=True):
        st.caption(result.chapter)
        st.subheader(result.title, anchor=False)
        if result.description:
            st.caption(result.description)
        if result.metrics:
            metric_items = list(result.metrics.items())
            for start in range(0, len(metric_items), 4):
                columns = st.columns(4)
                for column, (label, value) in zip(columns, metric_items[start:start + 4]):
                    with column:
                        with st.container(border=True):
                            st.metric(label, value, border=False)

    if result.question:
        st.subheader("题意", icon=":material/description:")
        with st.container(border=True):
            st.write(result.question)

    if result.formulas:
        with st.expander("计算公式", expanded=False, icon=":material/functions:"):
            for formula in result.formulas:
                st.markdown(f"- {formula}")

    if result.steps:
        st.subheader("分步计算过程", icon=":material/format_list_numbered:")
        with st.container(border=True):
            step_lines = [f"**{index}.** {step}" for index, step in enumerate(result.steps, start=1)]
            st.markdown("\n\n".join(step_lines))

    if result.tables:
        st.subheader("计算表", icon=":material/table_view:")
        for index, (title, headers, rows) in enumerate(result.tables):
            with st.expander(title, expanded=index == 0, icon=":material/dataset:"):
                if rows:
                    st.dataframe(
                        pd.DataFrame(list(rows), columns=list(headers)),
                        hide_index=True,
                        width="stretch",
                    )
                else:
                    st.caption("暂无数据。")

    if result.journal:
        st.subheader("会计分录", icon=":material/receipt_long:")
        st.code("\n".join(result.journal), language="text")

    if result.summary:
        st.subheader("结论与核对提示", icon=":material/lightbulb:")
        for item in result.summary:
            if any(word in item for word in ("注意", "风险", "检查", "不能", "核对")):
                st.warning(item, icon=":material/warning:")
            else:
                st.info(item, icon=":material/info:")

    if result.chart_paths:
        st.subheader("图表", icon=":material/show_chart:")
        for path in result.chart_paths:
            if path and Path(path).exists():
                st.image(path, width="stretch")

    if result.conclusion:
        st.success(result.conclusion, icon=":material/check_circle:")

    if result.csv_path and result.csv_path.exists():
        saved_time = st.session_state.get(f"{session_key}_time", "")
        with st.container(horizontal=True, horizontal_alignment="right"):
            st.download_button(
                "下载本次完整计算书 CSV",
                data=result.csv_path.read_bytes(),
                file_name=result.csv_path.name,
                mime="text/csv",
                icon=":material/download:",
                key=f"download_{session_key}",
                width="stretch",
            )
        st.caption(f"已保存：{result.csv_path.name} · {saved_time}")



# ---------------------------------------------------------------------------
# 输入控件
# ---------------------------------------------------------------------------
def money_input(
    label: str,
    value: float,
    key: str,
    *,
    step: float = 1000.0,
    min_value: float | None = 0.0,
    help_text: str = "",
) -> float:
    """金额输入（元）。"""
    return float(
        st.number_input(
            label,
            value=float(value),
            step=float(step),
            min_value=min_value,
            format="%.2f",
            key=key,
            help=help_text or None,
        )
    )


def decimal_input(
    label: str,
    value: float,
    key: str,
    *,
    step: float = 0.01,
    min_value: float | None = 0.0,
    help_text: str = "",
) -> float:
    """数量/系数输入。"""
    return float(
        st.number_input(
            label,
            value=float(value),
            step=float(step),
            min_value=min_value,
            format="%.4f",
            key=key,
            help=help_text or None,
        )
    )


def rate_input(
    label: str,
    value_percent: float,
    key: str,
    *,
    step: float = 0.1,
    allow_negative: bool = False,
    max_value: float = 100.0,
    help_text: str = "",
) -> float:
    """百分数输入，返回小数。"""
    value = st.number_input(
        f"{label}（%）",
        value=float(value_percent),
        step=float(step),
        min_value=-100.0 if allow_negative else 0.0,
        max_value=float(max_value),
        format="%.4f",
        key=key,
        help=help_text or None,
    )
    return float(value) / 100.0


def integer_input(
    label: str,
    value: int,
    key: str,
    *,
    minimum: int = 1,
    maximum: int = 1000,
) -> int:
    """整数输入。"""
    return int(
        st.number_input(
            label,
            value=int(value),
            step=1,
            min_value=int(minimum),
            max_value=int(maximum),
            key=key,
        )
    )


def editable_table(
    data: Sequence[Dict[str, Any]] | pd.DataFrame,
    key: str,
    *,
    num_rows: str = "dynamic",
    column_config: Optional[Dict[str, Any]] = None,
) -> pd.DataFrame:
    """可编辑数据表格。"""
    frame = data.copy() if isinstance(data, pd.DataFrame) else pd.DataFrame(list(data))
    return st.data_editor(
        frame,
        num_rows=num_rows,
        hide_index=True,
        width="stretch",
        key=key,
        column_config=column_config,
    )


def primary_button() -> bool:
    """表单主按钮。"""
    return st.form_submit_button(
        "开始计算",
        type="primary",
        icon=":material/calculate:",
        width="stretch",
    )


def demo_button(session_key: str, builder: Callable[[], CostResult], *, label: str = "运行本页示例") -> None:
    """运行本页默认示例。"""
    if st.button(label, icon=":material/play_arrow:", key=f"demo_{session_key}", width="stretch"):
        calculate_and_store(session_key, builder)


def page_header(module_number: str, title: str, description: str) -> None:
    """章节页标题。"""
    st.caption(f"第 {module_number} 章")
    st.title(title, anchor=False)
    st.write(description)


# ---------------------------------------------------------------------------
# 历史结果文件
# ---------------------------------------------------------------------------
def history_summary_path() -> Path:
    """汇总 CSV 路径。"""
    return export.get_summary_path()


def history_count() -> int:
    """历史计算记录条数。"""
    path = history_summary_path()
    if not path.exists():
        return 0
    try:
        return max(sum(1 for _ in path.open("r", encoding="utf-8-sig", newline="")) - 1, 0)
    except Exception:
        return 0


def all_history_bytes() -> Optional[bytes]:
    """读取历史汇总 CSV 的下载字节。"""
    path = history_summary_path()
    if not path.exists():
        return None
    return path.read_bytes()


def detail_count() -> int:
    """明细 CSV 文件数量。"""
    ensure_dirs()
    count = len(list(OUTPUT_DIR.glob("*.csv")))
    if history_summary_path().exists():
        count -= 1
    return max(count, 0)

