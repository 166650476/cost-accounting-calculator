"""成本会计学 Python 综合计算器——Streamlit 图形界面入口。

本地运行：
    python -m streamlit run app.py

Windows 用户可双击“启动成本会计计算器.bat”。
"""

from __future__ import annotations

from datetime import datetime
from typing import Callable, Dict, List, Optional, Tuple

import streamlit as st

import ui_pages
from ui_core import all_history_bytes, detail_count, history_count
from utils import CHART_DIR, OUTPUT_DIR


st.set_page_config(
    page_title="成本会计学综合计算器",
    page_icon=":material/calculate:",
    layout="wide",
    initial_sidebar_state="expanded",
)


MODULE_CARDS: List[Tuple[str, str, str, str]] = [
    ("1 成本会计总论", "概念 / 分类 / 科目", "成本概念、分类、职能、核算流程和科目体系。", "menu_book"),
    ("2 要素费用分配", "材料 / 动力 / 薪酬", "材料、动力、职工薪酬、折旧、低值易耗品和税费。", "inventory_2"),
    ("3 辅助生产费用", "四大分配方法", "直接分配、一次交互、计划成本和代数分配法。", "account_tree"),
    ("4 制造费用与损失", "制造费用 / 废品 / 停工", "制造费用归集分配、废品损失、停工损失和期间费用。", "factory"),
    ("5 完工与在产品", "六种分配方法", "约当产量、定额成本、定额比例等六种方法。", "pie_chart"),
    ("6 品种法", "单一 / 多品种", "按产品品种归集费用并完成完工结转。", "view_list"),
    ("7 分批法", "普通 / 简化", "分批法和累计间接费用分配法。", "layers"),
    ("8 分步法", "逐步 / 平行 / 还原", "综合结转、分项结转、平行结转和成本还原。", "account_tree"),
    ("9 辅助成本方法", "分类 / 联副 / 定额", "分类法、联产品、副产品和定额法。", "functions"),
    ("10 成本报表分析", "报表 / 降低率 / 结构", "生产成本报表、可比产品分析、单位成本和结构图。", "analytics"),
]

PAGES: Dict[str, Optional[Callable[[], None]]] = {
    "概览": None,
    "1 成本会计总论": ui_pages.page_chapter1,
    "2 要素费用分配": ui_pages.page_chapter2,
    "3 辅助生产费用": ui_pages.page_chapter3,
    "4 制造费用与损失": ui_pages.page_chapter4,
    "5 完工与在产品": ui_pages.page_chapter5,
    "6 品种法": ui_pages.page_chapter6,
    "7 分批法": ui_pages.page_chapter7,
    "8 分步法": ui_pages.page_chapter8,
    "9 辅助成本方法": ui_pages.page_chapter9,
    "10 成本报表分析": ui_pages.page_chapter10,
}


def _goto(page_name: str) -> None:
    st.session_state["nav"] = page_name


def render_sidebar() -> str:
    """侧边栏：章节导航、结果文件下载、使用提示。"""
    with st.sidebar:
        st.title("成本会计学计算器", anchor=False)
        st.caption("第10版 · 10章全覆盖 · 计算书自动导出")
        page = st.radio(
            "章节导航",
            options=list(PAGES),
            key="nav",
            label_visibility="collapsed",
        )
        st.caption("金额单位：元；比率按百分数输入，例如 14 表示 14%。")
        with st.expander("结果文件", icon=":material/folder_open:"):
            st.caption(f"历史计算记录：{history_count()} 条")
            st.caption(f"明细计算书：{detail_count()} 个")
            data = all_history_bytes()
            if data:
                st.download_button(
                    "下载全部历史汇总 CSV",
                    data=data,
                    file_name="成本会计计算记录汇总.csv",
                    mime="text/csv",
                    icon=":material/download:",
                    width="stretch",
                )
            else:
                st.caption("完成第一次计算后会生成历史汇总文件。")
            st.caption(f"CSV 目录：{OUTPUT_DIR}")
            st.caption(f"图表目录：{CHART_DIR}")
        with st.expander("使用说明", icon=":material/help:"):
            st.markdown(
                "1. 左侧选择章节，再选择具体计算类型。\n"
                "2. 表格可以直接编辑；方括号/默认值为模拟案例。\n"
                "3. 点击“开始计算”，结果自动保存 CSV。\n"
                "4. 每个页面都有“运行本页示例”按钮。\n"
                "5. 图表自动保存到 chart 文件夹，并在页面中展示。\n"
                "6. 关闭启动窗口即可停止本地服务。"
            )
        st.caption("仅供课程学习与作业校验参考。")
    return str(page)


def render_home() -> None:
    """首页：标题、统计卡片和章节入口。"""
    with st.container(border=True):
        st.badge("本地桌面工具", icon=":material/computer:", color="green")
        st.title("成本会计学综合计算器", anchor=False)
        st.write(
            "覆盖本科《成本会计学》10 个章节模块。选择章节、填写或编辑表格，"
            "即可获得完整公式步骤、分配表、成本计算单、会计分录、图表和可下载的 CSV 计算书。"
        )
    st.space("small")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        with st.container(border=True):
            st.metric("章节模块", "10", border=False)
    with c2:
        with st.container(border=True):
            st.metric("计算方法", "40+", border=False)
    with c3:
        with st.container(border=True):
            st.metric("历史计算", f"{history_count()} 条", border=False)
    with c4:
        with st.container(border=True):
            st.metric("图表类型", "4", border=False)

    st.subheader("选择章节", icon=":material/apps:")
    for row_start in range(0, len(MODULE_CARDS), 3):
        columns = st.columns(3)
        for column, card in zip(columns, MODULE_CARDS[row_start:row_start + 3]):
            page_name, subtitle, description, icon = card
            with column:
                with st.container(border=True):
                    st.markdown(f"#### :material/{icon}: {page_name}")
                    st.caption(subtitle)
                    st.write(description)
                    st.button(
                        "进入章节",
                        key=f"home_go_{page_name}",
                        icon=":material/arrow_forward:",
                        on_click=_goto,
                        args=(page_name,),
                        width="stretch",
                    )

    with st.expander("项目说明与免责声明", expanded=False, icon=":material/info:"):
        st.markdown(
            "- 本项目为学生自主开发的学习工具，仅用于成本会计课程学习、习题验算和课程大作业；\n"
            "- 不是出版社官方配套软件，与教材出版社、作者及任何官方机构无隶属或授权关系；\n"
            "- 所有案例均为自行设计的模拟教学案例，不摘抄任何教材原文、原题或图片；\n"
            "- 计算结果仅供学习核对，不能替代企业实际会计核算、审计或税务申报。"
        )


def main() -> None:
    """应用主循环。"""
    st.session_state.setdefault("nav", "概览")
    page_name = render_sidebar()
    page = PAGES.get(page_name)
    if page is None:
        render_home()
    else:
        try:
            page()
        except Exception as exc:
            st.error(f"页面运行失败：{exc}", icon=":material/error:")
            with st.expander("错误详情", expanded=False):
                st.exception(exc)
    st.caption(f"成本会计学综合计算器 · 本地运行 · {datetime.now().strftime('%Y-%m-%d')}")


if __name__ == "__main__":
    main()
