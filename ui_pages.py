"""Streamlit 各章节页面。

每个页面负责收集输入，并调用 ui_results 中的结果构建函数；
统一的结果展示、CSV 保存和下载由 ui_core 处理。
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

import chapter1_intro as ch1
import ui_results as ur
from ui_core import (
    calculate_and_store,
    decimal_input,
    demo_button,
    editable_table,
    money_input,
    page_header,
    primary_button,
    rate_input,
    render_saved,
)


# ---------------------------------------------------------------------------
# 第一章：知识点
# ---------------------------------------------------------------------------
def page_chapter1() -> None:
    page_header("1", "成本会计总论", "成本概念、分类、成本会计对象与职能、核算流程、核算原则和科目体系。")
    tabs = st.tabs(["成本概念与作用", "成本分类", "对象·职能·任务", "核算流程与原则", "科目体系", "考点提示"])
    with tabs[0]:
        for line in ch1.COST_CONCEPT:
            st.markdown(f"- {line}")
    with tabs[1]:
        for title, lines in ch1.COST_CLASSIFICATION:
            with st.expander(title, expanded=False):
                for line in lines:
                    st.markdown(f"- {line}")
    with tabs[2]:
        for title, lines in ch1.OBJECT_FUNCTION_TASK:
            with st.expander(title, expanded=False):
                for line in lines:
                    st.markdown(f"- {line}")
    with tabs[3]:
        for title, lines in ch1.PROCEDURE_PRINCIPLES:
            with st.expander(title, expanded=False):
                for line in lines:
                    st.markdown(f"- {line}")
    with tabs[4]:
        for title, lines in ch1.ACCOUNT_SYSTEM:
            with st.expander(title, expanded=False):
                for line in lines:
                    st.markdown(f"- {line}")
    with tabs[5]:
        st.info("第一章以概念和框架为主，后续章节会把这些概念应用到具体计算中。")
        st.markdown(
            "- 成本是对象化的费用；产品成本计入存货，期间费用计入当期损益。\n"
            "- 成本按经济用途分为直接材料、直接人工、制造费用。\n"
            "- 成本核算程序：确定对象→设置账户→归集分配要素费用→辅助生产→制造费用→完工与在产品分配→结转→报表分析。"
        )


# ---------------------------------------------------------------------------
# 第二章：要素费用
# ---------------------------------------------------------------------------
MATERIAL_METHODS = ["定额消耗量比例法", "定额费用比例法", "产品重量比例法", "产量比例法"]


def page_chapter2() -> None:
    page_header("2", "要素费用的归集与分配", "材料、外购动力、职工薪酬、折旧、低值易耗品、税金和其他支出的归集与分配。")
    calc_type = st.selectbox(
        "计算类型",
        ["材料费用分配", "外购动力费用分配", "职工薪酬费用分配", "折旧费用计算", "低值易耗品摊销", "税金和其他支出"],
        key="ch2_type",
    )

    if calc_type == "材料费用分配":
        method = st.selectbox("材料分配方法", MATERIAL_METHODS, key="ch2_material_method")
        with st.form("ch2_material_form"):
            total = money_input("材料实际费用总额（元）", 48000, "ch2_material_total")
            st.caption("可编辑产品数据：产量、单位定额消耗量、材料计划单价、单位重量。")
            frame = editable_table(
                [
                    {"产品名称": "甲产品", "产量": 200, "单位定额消耗量": 15, "材料计划单价": 10, "单位重量": 2.0},
                    {"产品名称": "乙产品", "产量": 150, "单位定额消耗量": 12, "材料计划单价": 10, "单位重量": 2.5},
                ],
                "ch2_material_table",
            )
            submitted = primary_button()
        if submitted:
            products = [
                {
                    "name": row["产品名称"],
                    "output": row["产量"],
                    "quota": row["单位定额消耗量"],
                    "unit_price": row["材料计划单价"],
                    "weight": row["单位重量"],
                }
                for _, row in frame.iterrows()
            ]
            calculate_and_store("ch2_material", lambda: ur.material_result(total, products, method))
        demo_button(
            "ch2_material",
            lambda: ur.material_result(
                48000,
                [
                    {"name": "甲产品", "output": 200, "quota": 15, "unit_price": 10, "weight": 2.0},
                    {"name": "乙产品", "output": 150, "quota": 12, "unit_price": 10, "weight": 2.5},
                ],
                method,
            ),
        )
        render_saved("ch2_material")

    elif calc_type == "外购动力费用分配":
        with st.form("ch2_power_form"):
            total = money_input("外购动力费用总额（元）", 18000, "ch2_power_total")
            frame = editable_table(
                [{"产品名称": "甲产品", "机器工时": 1200}, {"产品名称": "乙产品", "机器工时": 800}],
                "ch2_power_table",
            )
            submitted = primary_button()
        if submitted:
            products = [{"name": row["产品名称"], "machine_hours": row["机器工时"]} for _, row in frame.iterrows()]
            calculate_and_store("ch2_power", lambda: ur.power_result(total, products))
        demo_button("ch2_power", lambda: ur.power_result(18000, [{"name": "甲产品", "machine_hours": 1200}, {"name": "乙产品", "machine_hours": 800}]))
        render_saved("ch2_power")

    elif calc_type == "职工薪酬费用分配":
        with st.form("ch2_payroll_form"):
            total = money_input("生产工人工资总额（元）", 60000, "ch2_payroll_total")
            col1, col2 = st.columns(2)
            with col1:
                welfare = rate_input("职工福利费计提比例", 14.0, "ch2_payroll_welfare")
            with col2:
                social = rate_input("社会保险费计提比例", 26.0, "ch2_payroll_social")
            frame = editable_table(
                [{"产品名称": "甲产品", "生产工时": 2000}, {"产品名称": "乙产品", "生产工时": 1000}],
                "ch2_payroll_table",
            )
            submitted = primary_button()
        if submitted:
            products = [{"name": row["产品名称"], "hours": row["生产工时"]} for _, row in frame.iterrows()]
            calculate_and_store("ch2_payroll", lambda: ur.payroll_result(total, products, welfare, social))
        demo_button("ch2_payroll", lambda: ur.payroll_result(60000, [{"name": "甲产品", "hours": 2000}, {"name": "乙产品", "hours": 1000}], 0.14, 0.26))
        render_saved("ch2_payroll")

    elif calc_type == "折旧费用计算":
        with st.form("ch2_depreciation_form"):
            st.caption("固定资产原值、净残值率（%）、使用年限和受益部门可编辑。")
            frame = editable_table(
                [
                    {"固定资产": "生产车间机器设备", "原值": 600000.0, "净残值率(%)": 5.0, "使用年限": 10, "受益部门": "制造费用"},
                    {"固定资产": "行政办公楼", "原值": 900000.0, "净残值率(%)": 5.0, "使用年限": 20, "受益部门": "管理费用"},
                    {"固定资产": "销售部门运输设备", "原值": 240000.0, "净残值率(%)": 5.0, "使用年限": 5, "受益部门": "销售费用"},
                ],
                "ch2_depreciation_table",
            )
            submitted = primary_button()
        if submitted:
            assets = [
                {
                    "name": row["固定资产"], "original": row["原值"], "residual_rate": float(row["净残值率(%)"]) / 100,
                    "life_years": row["使用年限"], "department": row["受益部门"],
                }
                for _, row in frame.iterrows()
            ]
            calculate_and_store("ch2_depreciation", lambda: ur.depreciation_result(assets))
        demo_button("ch2_depreciation", lambda: ur.depreciation_result([
            {"name": "生产车间机器设备", "original": 600000, "residual_rate": 0.05, "life_years": 10, "department": "制造费用"},
            {"name": "行政办公楼", "original": 900000, "residual_rate": 0.05, "life_years": 20, "department": "管理费用"},
            {"name": "销售部门运输设备", "original": 240000, "residual_rate": 0.05, "life_years": 5, "department": "销售费用"},
        ]))
        render_saved("ch2_depreciation")

    elif calc_type == "低值易耗品摊销":
        method = st.selectbox("摊销方法", ["一次转销法", "五五摊销法"], key="ch2_low_method")
        with st.form("ch2_low_form"):
            frame = editable_table(
                [
                    {"名称": "生产车间工具", "领用金额": 12000.0, "受益部门": "制造费用"},
                    {"名称": "行政办公用具", "领用金额": 6000.0, "受益部门": "管理费用"},
                    {"名称": "销售包装器具", "领用金额": 4000.0, "受益部门": "销售费用"},
                ],
                "ch2_low_table",
            )
            submitted = primary_button()
        if submitted:
            items = [{"name": row["名称"], "amount": row["领用金额"], "department": row["受益部门"]} for _, row in frame.iterrows()]
            calculate_and_store("ch2_low", lambda: ur.low_value_result(items, method))
        demo_button("ch2_low", lambda: ur.low_value_result([
            {"name": "生产车间工具", "amount": 12000, "department": "制造费用"},
            {"name": "行政办公用具", "amount": 6000, "department": "管理费用"},
            {"name": "销售包装器具", "amount": 4000, "department": "销售费用"},
        ], method))
        render_saved("ch2_low")

    else:
        with st.form("ch2_taxes_form"):
            frame = editable_table(
                [
                    {"项目名称": "房产税", "金额": 3000.0, "受益部门": "管理费用", "类别": "税金"},
                    {"项目名称": "土地使用税", "金额": 2000.0, "受益部门": "管理费用", "类别": "税金"},
                    {"项目名称": "生产车间办公费", "金额": 1500.0, "受益部门": "制造费用", "类别": "其他支出"},
                    {"项目名称": "销售部门差旅费", "金额": 2500.0, "受益部门": "销售费用", "类别": "其他支出"},
                    {"项目名称": "行政管理部门其他支出", "金额": 1000.0, "受益部门": "管理费用", "类别": "其他支出"},
                ],
                "ch2_taxes_table",
            )
            submitted = primary_button()
        if submitted:
            items = [
                {"name": row["项目名称"], "amount": row["金额"], "department": row["受益部门"], "kind": row["类别"]}
                for _, row in frame.iterrows()
            ]
            calculate_and_store("ch2_taxes", lambda: ur.taxes_result(items))
        demo_button("ch2_taxes", lambda: ur.taxes_result([
            {"name": "房产税", "amount": 3000, "department": "管理费用", "kind": "税金"},
            {"name": "土地使用税", "amount": 2000, "department": "管理费用", "kind": "税金"},
            {"name": "生产车间办公费", "amount": 1500, "department": "制造费用", "kind": "其他支出"},
            {"name": "销售部门差旅费", "amount": 2500, "department": "销售费用", "kind": "其他支出"},
            {"name": "行政管理部门其他支出", "amount": 1000, "department": "管理费用", "kind": "其他支出"},
        ]))
        render_saved("ch2_taxes")



# ---------------------------------------------------------------------------
# 第三章：辅助生产费用
# ---------------------------------------------------------------------------
AUX_METHODS = ["直接分配法", "一次交互分配法", "计划成本分配法", "代数分配法"]
AUX_NAMES = ["供电车间", "供水车间"]
AUX_RECIPIENTS = ["供电车间", "供水车间", "基本生产车间", "行政管理部门", "销售部门"]


def _aux_service_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"服务车间": "供电车间", "供电车间": 0, "供水车间": 3000, "基本生产车间": 20000, "行政管理部门": 4000, "销售部门": 3000},
            {"服务车间": "供水车间", "供电车间": 500, "供水车间": 0, "基本生产车间": 7000, "行政管理部门": 1500, "销售部门": 1000},
        ]
    )


def page_chapter3() -> None:
    page_header("3", "辅助生产费用的归集与分配", "直接分配法、一次交互分配法、计划成本分配法和代数分配法。")
    method = st.selectbox("分配方法", AUX_METHODS, key="ch3_method")
    with st.form("ch3_form"):
        col1, col2 = st.columns(2)
        with col1:
            power_cost = money_input("供电车间直接费用（元）", 24000, "ch3_power_cost")
        with col2:
            water_cost = money_input("供水车间直接费用（元）", 16000, "ch3_water_cost")
        st.caption("服务量矩阵：行是提供服务的辅助车间，列是受益对象；对角线应为 0。")
        frame = editable_table(_aux_service_frame(), "ch3_service_table", num_rows="fixed")
        planned_rates = None
        if method == "计划成本分配法":
            c1, c2 = st.columns(2)
            with c1:
                p_rate = decimal_input("供电计划单位成本（元/千瓦时）", 0.85, "ch3_p_rate", step=0.01)
            with c2:
                w_rate = decimal_input("供水计划单位成本（元/吨）", 1.70, "ch3_w_rate", step=0.01)
            planned_rates = [p_rate, w_rate]
        submitted = primary_button()
    if submitted:
        q = frame[AUX_RECIPIENTS].to_numpy().tolist()
        calculate_and_store("ch3_result", lambda: ur.aux_result(method, AUX_NAMES, [power_cost, water_cost], q, planned_rates))
    demo_button(
        "ch3_result",
        lambda: ur.aux_result(method, AUX_NAMES, [24000, 16000], _aux_service_frame()[AUX_RECIPIENTS].to_numpy().tolist(), [0.85, 1.70]),
    )
    render_saved("ch3_result")



# ---------------------------------------------------------------------------
# 第四章：制造费用、生产损失、期间费用
# ---------------------------------------------------------------------------
def page_chapter4() -> None:
    page_header("4", "制造费用、生产损失与期间费用", "制造费用归集分配、不可修复/可修复废品损失、停工损失和期间费用结转。")
    calc_type = st.selectbox(
        "计算类型",
        ["制造费用归集", "制造费用分配", "不可修复废品损失", "可修复废品损失", "停工损失", "期间费用结转"],
        key="ch4_type",
    )

    if calc_type == "制造费用归集":
        with st.form("ch4_collect"):
            frame = editable_table(
                [
                    {"费用项目": "机物料消耗", "金额": 8000.0, "贷方来源": "原材料"},
                    {"费用项目": "车间管理人员工资", "金额": 12000.0, "贷方来源": "应付职工薪酬"},
                    {"费用项目": "车间固定资产折旧", "金额": 10000.0, "贷方来源": "累计折旧"},
                    {"费用项目": "车间水电费", "金额": 5000.0, "贷方来源": "银行存款"},
                    {"费用项目": "车间劳动保护费", "金额": 3000.0, "贷方来源": "银行存款"},
                ],
                "ch4_collect_table",
            )
            submitted = primary_button()
        if submitted:
            items = [{"name": row["费用项目"], "amount": row["金额"], "source": row["贷方来源"]} for _, row in frame.iterrows()]
            calculate_and_store("ch4_collect_result", lambda: ur.overhead_collect_result(items))
        demo_button("ch4_collect_result", lambda: ur.overhead_collect_result([
            {"name": "机物料消耗", "amount": 8000, "source": "原材料"},
            {"name": "车间管理人员工资", "amount": 12000, "source": "应付职工薪酬"},
            {"name": "车间固定资产折旧", "amount": 10000, "source": "累计折旧"},
            {"name": "车间水电费", "amount": 5000, "source": "银行存款"},
            {"name": "车间劳动保护费", "amount": 3000, "source": "银行存款"},
        ]))
        render_saved("ch4_collect_result")

    elif calc_type == "制造费用分配":
        method = st.selectbox("分配方法", ["生产工时比例法", "生产工资比例法", "机器工时比例法", "年度计划分配率法"], key="ch4_alloc_method")
        if method == "年度计划分配率法":
            with st.form("ch4_annual_form"):
                annual = money_input("年度计划制造费用（元）", 480000, "ch4_annual")
                annual_hours = decimal_input("年度计划定额工时", 120000, "ch4_annual_hours", step=100)
                monthly = money_input("本月实际制造费用（元）", 12500, "ch4_monthly")
                frame = editable_table([{"产品名称": "甲产品", "本月实际工时": 2000}, {"产品名称": "乙产品", "本月实际工时": 1000}], "ch4_annual_table")
                submitted = primary_button()
            if submitted:
                products = [{"name": row["产品名称"], "monthly_hours": row["本月实际工时"]} for _, row in frame.iterrows()]
                calculate_and_store("ch4_annual_result", lambda: ur.annual_planned_result(annual, annual_hours, monthly, products))
            demo_button("ch4_annual_result", lambda: ur.annual_planned_result(480000, 120000, 12500, [{"name": "甲产品", "monthly_hours": 2000}, {"name": "乙产品", "monthly_hours": 1000}]))
            render_saved("ch4_annual_result")
        else:
            with st.form("ch4_alloc_form"):
                total = money_input("制造费用总额（元）", 38000, "ch4_alloc_total")
                frame = editable_table(
                    [
                        {"产品名称": "甲产品", "生产工时": 2000, "生产工资": 40000, "机器工时": 1200},
                        {"产品名称": "乙产品", "生产工时": 1000, "生产工资": 20000, "机器工时": 800},
                    ],
                    "ch4_alloc_table",
                )
                submitted = primary_button()
            if submitted:
                products = [
                    {"name": row["产品名称"], "hours": row["生产工时"], "wages": row["生产工资"], "machine_hours": row["机器工时"]}
                    for _, row in frame.iterrows()
                ]
                calculate_and_store("ch4_alloc", lambda: ur.overhead_allocate_result(total, products, method))
            demo_button("ch4_alloc", lambda: ur.overhead_allocate_result(38000, [
                {"name": "甲产品", "hours": 2000, "wages": 40000, "machine_hours": 1200},
                {"name": "乙产品", "hours": 1000, "wages": 20000, "machine_hours": 800},
            ], method))
            render_saved("ch4_alloc")


    elif calc_type == "不可修复废品损失":
        method = st.selectbox("计算口径", ["按定额成本", "按实际成本"], key="ch4_waste_method")
        product = st.text_input("产品名称", "甲产品", key="ch4_waste_product")
        if method == "按定额成本":
            with st.form("ch4_waste_quota_form"):
                qty = decimal_input("废品数量", 20, "ch4_waste_qty", step=1)
                c1, c2, c3 = st.columns(3)
                with c1:
                    material = money_input("单位材料定额", 80, "ch4_waste_material", step=10)
                with c2:
                    labor = money_input("单位人工定额", 40, "ch4_waste_labor", step=10)
                with c3:
                    overhead = money_input("单位制造费用定额", 20, "ch4_waste_overhead", step=10)
                c4, c5 = st.columns(2)
                with c4:
                    scrap = money_input("残料价值", 300, "ch4_waste_scrap", step=10)
                with c5:
                    compensation = money_input("应收赔款", 500, "ch4_waste_comp", step=10)
                submitted = primary_button()
            if submitted:
                calculate_and_store("ch4_waste", lambda: ur.unrepairable_quota_result(product, qty, material, labor, overhead, scrap, compensation))
            demo_button("ch4_waste", lambda: ur.unrepairable_quota_result("甲产品", 20, 80, 40, 20, 300, 500))
            render_saved("ch4_waste")
        else:
            with st.form("ch4_waste_actual_form"):
                total = money_input("产品实际总成本（元）", 100000, "ch4_waste_total")
                output = decimal_input("产品总产量", 1000, "ch4_waste_output", step=10)
                qty = decimal_input("废品数量", 20, "ch4_waste_actual_qty", step=1)
                c1, c2 = st.columns(2)
                with c1:
                    scrap = money_input("残料价值", 300, "ch4_waste_actual_scrap", step=10)
                with c2:
                    compensation = money_input("应收赔款", 500, "ch4_waste_actual_comp", step=10)
                submitted = primary_button()
            if submitted:
                calculate_and_store("ch4_waste_actual", lambda: ur.unrepairable_actual_result(product, total, output, qty, scrap, compensation))
            demo_button("ch4_waste_actual", lambda: ur.unrepairable_actual_result("乙产品", 100000, 1000, 20, 300, 500))
            render_saved("ch4_waste_actual")

    elif calc_type == "可修复废品损失":
        with st.form("ch4_repair_form"):
            product = st.text_input("产品名称", "丙产品", key="ch4_repair_product")
            c1, c2, c3 = st.columns(3)
            with c1:
                material = money_input("修复用材料", 800, "ch4_repair_material", step=10)
            with c2:
                labor = money_input("修复用人工", 1200, "ch4_repair_labor", step=10)
            with c3:
                overhead = money_input("修复用制造费用", 500, "ch4_repair_overhead", step=10)
            c4, c5 = st.columns(2)
            with c4:
                scrap = money_input("残料价值", 100, "ch4_repair_scrap", step=10)
            with c5:
                compensation = money_input("应收赔款", 200, "ch4_repair_comp", step=10)
            submitted = primary_button()
        if submitted:
            calculate_and_store("ch4_repair", lambda: ur.repairable_result(product, material, labor, overhead, scrap, compensation))
        demo_button("ch4_repair", lambda: ur.repairable_result("丙产品", 800, 1200, 500, 100, 200))
        render_saved("ch4_repair")

    elif calc_type == "停工损失":
        with st.form("ch4_downtime_form"):
            total_loss = money_input("停工损失总额（元）", 9000, "ch4_downtime_loss")
            is_normal = st.checkbox("属于正常停工", value=True, key="ch4_downtime_normal")
            insurance = money_input("保险/责任赔偿（元）", 0 if is_normal else 2000, "ch4_downtime_insurance")
            submitted = primary_button()
        if submitted:
            calculate_and_store("ch4_downtime", lambda: ur.downtime_result(total_loss, is_normal, insurance))
        demo_button("ch4_downtime", lambda: ur.downtime_result(9000, False, 2000))
        render_saved("ch4_downtime")

    else:
        with st.form("ch4_period_form"):
            c1, c2, c3 = st.columns(3)
            with c1:
                sales = money_input("销售费用", 20000, "ch4_sales")
            with c2:
                admin = money_input("管理费用", 30000, "ch4_admin")
            with c3:
                finance = money_input("财务费用", 8000, "ch4_finance")
            submitted = primary_button()
        if submitted:
            calculate_and_store("ch4_period", lambda: ur.period_expense_result(sales, admin, finance))
        demo_button("ch4_period", lambda: ur.period_expense_result(20000, 30000, 8000))
        render_saved("ch4_period")



# ---------------------------------------------------------------------------
# 第五章：完工产品与在产品分配
# ---------------------------------------------------------------------------
WIP_METHODS = ["不计算在产品成本法", "在产品按固定成本计价法", "在产品按原材料费用计价法", "约当产量比例法", "在产品按定额成本计价法", "定额比例法"]


def page_chapter5() -> None:
    page_header("5", "生产费用在完工产品与在产品之间分配", "六种完工产品与在产品成本分配方法。")
    method = st.selectbox("分配方法", WIP_METHODS, key="ch5_method")
    if method == "不计算在产品成本法":
        with st.form("ch5_no_form"):
            product = st.text_input("产品名称", "甲产品", key="ch5_no_product")
            completed = decimal_input("完工产品数量", 800, "ch5_no_completed", step=10)
            material = money_input("直接材料", 50000, "ch5_no_material")
            labor = money_input("直接人工", 18000, "ch5_no_labor")
            overhead = money_input("制造费用", 9000, "ch5_no_overhead")
            submitted = primary_button()
        if submitted:
            calculate_and_store("ch5_no", lambda: ur.no_wip_result(product, completed, material, labor, overhead))
        demo_button("ch5_no", lambda: ur.no_wip_result("甲产品", 800, 50000, 18000, 9000))
        render_saved("ch5_no")

    elif method == "在产品按固定成本计价法":
        with st.form("ch5_fixed_form"):
            product = st.text_input("产品名称", "甲产品", key="ch5_fixed_product")
            completed = decimal_input("完工产品数量", 800, "ch5_fixed_completed", step=10)
            wip = decimal_input("月末在产品数量", 200, "ch5_fixed_wip", step=10)
            material = money_input("直接材料", 50000, "ch5_fixed_material")
            labor = money_input("直接人工", 18000, "ch5_fixed_labor")
            overhead = money_input("制造费用", 9000, "ch5_fixed_overhead")
            c1, c2, c3 = st.columns(3)
            with c1:
                fixed_m = money_input("固定材料成本", 10000, "ch5_fixed_m")
            with c2:
                fixed_l = money_input("固定人工成本", 2000, "ch5_fixed_l")
            with c3:
                fixed_o = money_input("固定制造费用", 1000, "ch5_fixed_o")
            submitted = primary_button()
        if submitted:
            calculate_and_store("ch5_fixed", lambda: ur.fixed_wip_result(product, completed, wip, material, labor, overhead, fixed_m, fixed_l, fixed_o))
        demo_button("ch5_fixed", lambda: ur.fixed_wip_result("甲产品", 800, 200, 50000, 18000, 9000, 10000, 2000, 1000))
        render_saved("ch5_fixed")

    elif method == "在产品按原材料费用计价法":
        with st.form("ch5_material_form"):
            product = st.text_input("产品名称", "甲产品", key="ch5_material_product")
            completed = decimal_input("完工产品数量", 800, "ch5_material_completed", step=10)
            wip = decimal_input("月末在产品数量", 200, "ch5_material_wip", step=10)
            material = money_input("直接材料", 50000, "ch5_material_material")
            labor = money_input("直接人工", 18000, "ch5_material_labor")
            overhead = money_input("制造费用", 9000, "ch5_material_overhead")
            submitted = primary_button()
        if submitted:
            calculate_and_store("ch5_material", lambda: ur.material_only_result(product, completed, wip, material, labor, overhead))
        demo_button("ch5_material", lambda: ur.material_only_result("甲产品", 800, 200, 50000, 18000, 9000))
        render_saved("ch5_material")


    elif method == "约当产量比例法":
        with st.form("ch5_equiv_form"):
            product = st.text_input("产品名称", "甲产品", key="ch5_eq_product")
            completed = decimal_input("完工产品数量", 800, "ch5_eq_completed", step=10)
            wip = decimal_input("月末在产品数量", 200, "ch5_eq_wip", step=10)
            material = money_input("直接材料", 50000, "ch5_eq_material")
            labor = money_input("直接人工", 18000, "ch5_eq_labor")
            overhead = money_input("制造费用", 9000, "ch5_eq_overhead")
            c1, c2 = st.columns(2)
            with c1:
                material_completion = rate_input("材料投料程度", 100.0, "ch5_eq_material_rate")
            with c2:
                processing_completion = rate_input("加工完工程度", 50.0, "ch5_eq_processing_rate")
            submitted = primary_button()
        if submitted:
            calculate_and_store("ch5_eq", lambda: ur.equivalent_result(product, completed, wip, material, labor, overhead, material_completion, processing_completion))
        demo_button("ch5_eq", lambda: ur.equivalent_result("甲产品", 800, 200, 50000, 18000, 9000, 1.0, 0.5))
        render_saved("ch5_eq")

    elif method == "在产品按定额成本计价法":
        with st.form("ch5_quota_form"):
            product = st.text_input("产品名称", "甲产品", key="ch5_quota_product")
            completed = decimal_input("完工产品数量", 800, "ch5_quota_completed", step=10)
            wip = decimal_input("月末在产品数量", 200, "ch5_quota_wip", step=10)
            material = money_input("直接材料", 50000, "ch5_quota_material")
            labor = money_input("直接人工", 18000, "ch5_quota_labor")
            overhead = money_input("制造费用", 9000, "ch5_quota_overhead")
            c1, c2, c3 = st.columns(3)
            with c1:
                unit_m = money_input("单位材料定额", 50, "ch5_quota_unit_m", step=10)
            with c2:
                unit_l = money_input("单位人工定额", 10, "ch5_quota_unit_l", step=10)
            with c3:
                unit_o = money_input("单位制造费用定额", 5, "ch5_quota_unit_o", step=10)
            submitted = primary_button()
        if submitted:
            calculate_and_store("ch5_quota", lambda: ur.quota_wip_result(product, completed, wip, material, labor, overhead, unit_m, unit_l, unit_o))
        demo_button("ch5_quota", lambda: ur.quota_wip_result("甲产品", 800, 200, 50000, 18000, 9000, 50, 10, 5))
        render_saved("ch5_quota")

    else:
        with st.form("ch5_ratio_form"):
            product = st.text_input("产品名称", "甲产品", key="ch5_ratio_product")
            completed = decimal_input("完工产品数量", 600, "ch5_ratio_completed", step=10)
            wip = decimal_input("月末在产品数量", 200, "ch5_ratio_wip", step=10)
            material = money_input("直接材料", 60000, "ch5_ratio_material")
            labor = money_input("直接人工", 20000, "ch5_ratio_labor")
            overhead = money_input("制造费用", 10000, "ch5_ratio_overhead")
            c1, c2 = st.columns(2)
            with c1:
                unit_material_quota = money_input("单位产品材料定额（元/件）", 80, "ch5_ratio_unit_m", step=10)
            with c2:
                material_completion = rate_input("在产品材料投料程度", 100.0, "ch5_ratio_material_rate")
            c3, c4 = st.columns(2)
            with c3:
                unit_hour_quota = decimal_input("单位产品工时定额（小时/件）", 15, "ch5_ratio_unit_h", step=1)
            with c4:
                processing_completion = rate_input("在产品加工完工程度", 40.0, "ch5_ratio_processing_rate")
            submitted = primary_button()
        if submitted:
            calculate_and_store("ch5_ratio", lambda: ur.quota_ratio_result(product, completed, wip, material, labor, overhead, unit_material_quota, material_completion, unit_hour_quota, processing_completion))
        demo_button("ch5_ratio", lambda: ur.quota_ratio_result("甲产品", 600, 200, 60000, 20000, 10000, 80, 1.0, 15, 0.4))
        render_saved("ch5_ratio")



# ---------------------------------------------------------------------------
# 第六章：品种法
# ---------------------------------------------------------------------------
def page_chapter6() -> None:
    page_header("6", "产品成本计算——品种法", "单一品种和多品种品种法完整核算流程。")
    calc_type = st.selectbox("计算类型", ["单一品种品种法", "多品种品种法"], key="ch6_type")
    if calc_type == "单一品种品种法":
        with st.form("ch6_single_form"):
            product = st.text_input("产品名称", "甲产品", key="ch6_single_product")
            completed = decimal_input("完工产品数量", 800, "ch6_single_completed", step=10)
            wip = decimal_input("月末在产品数量", 200, "ch6_single_wip", step=10)
            completion = rate_input("在产品完工程度", 50.0, "ch6_single_rate")
            material = money_input("直接材料", 50000, "ch6_single_material")
            labor = money_input("直接人工", 18000, "ch6_single_labor")
            overhead = money_input("制造费用", 9000, "ch6_single_overhead")
            submitted = primary_button()
        if submitted:
            calculate_and_store("ch6_single", lambda: ur.single_variety_result(product, material, labor, overhead, completed, wip, completion))
        demo_button("ch6_single", lambda: ur.single_variety_result("甲产品", 50000, 18000, 9000, 800, 200, 0.5))
        render_saved("ch6_single")
    else:
        with st.form("ch6_multi_form"):
            c1, c2, c3 = st.columns(3)
            with c1:
                total_material = money_input("直接材料总额", 60000, "ch6_multi_material")
            with c2:
                total_labor = money_input("直接人工总额", 25000, "ch6_multi_labor")
            with c3:
                total_overhead = money_input("制造费用总额", 15000, "ch6_multi_overhead")
            frame = editable_table(
                [
                    {"产品名称": "甲产品", "完工产量": 600, "在产品数量": 100, "完工程度(%)": 50.0, "单位材料定额": 50, "生产工时": 3000},
                    {"产品名称": "乙产品", "完工产量": 400, "在产品数量": 100, "完工程度(%)": 50.0, "单位材料定额": 40, "生产工时": 2000},
                ],
                "ch6_multi_table",
            )
            submitted = primary_button()
        if submitted:
            products = [
                {
                    "name": row["产品名称"], "output": row["完工产量"], "wip_qty": row["在产品数量"],
                    "completion": float(row["完工程度(%)"]) / 100, "material_quota": row["单位材料定额"], "labor_hours": row["生产工时"],
                }
                for _, row in frame.iterrows()
            ]
            calculate_and_store("ch6_multi", lambda: ur.multi_variety_result(total_material, total_labor, total_overhead, products))
        demo_button("ch6_multi", lambda: ur.multi_variety_result(60000, 25000, 15000, [
            {"name": "甲产品", "output": 600, "wip_qty": 100, "completion": 0.5, "material_quota": 50, "labor_hours": 3000},
            {"name": "乙产品", "output": 400, "wip_qty": 100, "completion": 0.5, "material_quota": 40, "labor_hours": 2000},
        ]))
        render_saved("ch6_multi")



# ---------------------------------------------------------------------------
# 第七章：分批法
# ---------------------------------------------------------------------------
def page_chapter7() -> None:
    page_header("7", "产品成本计算——分批法", "普通分批法和简化分批法（累计间接费用分配法）。")
    method = st.selectbox("计算方法", ["普通分批法", "简化分批法"], key="ch7_method")
    if method == "普通分批法":
        with st.form("ch7_normal_form"):
            overhead = money_input("本月制造费用总额", 14000, "ch7_normal_overhead")
            frame = editable_table(
                [
                    {"批次号": "601批", "产品": "甲产品", "直接材料": 30000, "直接人工": 12000, "生产工时": 1500, "已完工": True, "完工数量": 20},
                    {"批次号": "602批", "产品": "乙产品", "直接材料": 24000, "直接人工": 10000, "生产工时": 1200, "已完工": True, "完工数量": 15},
                    {"批次号": "603批", "产品": "丙产品", "直接材料": 18000, "直接人工": 8000, "生产工时": 800, "已完工": False, "完工数量": 0},
                ],
                "ch7_normal_table",
            )
            submitted = primary_button()
        if submitted:
            batches = [
                {
                    "name": row["批次号"], "product": row["产品"], "direct_material": row["直接材料"],
                    "direct_labor": row["直接人工"], "labor_hours": row["生产工时"],
                    "completed": bool(row["已完工"]), "completed_qty": row["完工数量"] if row["已完工"] else 0,
                }
                for _, row in frame.iterrows()
            ]
            calculate_and_store("ch7_normal", lambda: ur.normal_batch_result(overhead, batches))
        demo_button("ch7_normal", lambda: ur.normal_batch_result(14000, [
            {"name": "601批", "product": "甲产品", "direct_material": 30000, "direct_labor": 12000, "labor_hours": 1500, "completed": True, "completed_qty": 20},
            {"name": "602批", "product": "乙产品", "direct_material": 24000, "direct_labor": 10000, "labor_hours": 1200, "completed": True, "completed_qty": 15},
            {"name": "603批", "product": "丙产品", "direct_material": 18000, "direct_labor": 8000, "labor_hours": 800, "completed": False, "completed_qty": 0},
        ]))
        render_saved("ch7_normal")
    else:
        with st.form("ch7_simplified_form"):
            overhead = money_input("累计制造费用", 18000, "ch7_simple_overhead")
            frame = editable_table(
                [
                    {"批次号": "701批", "产品": "A产品", "累计材料": 40000, "累计人工": 18000, "累计工时": 2000, "已完工": True, "完工数量": 100},
                    {"批次号": "702批", "产品": "B产品", "累计材料": 30000, "累计人工": 14000, "累计工时": 1500, "已完工": True, "完工数量": 80},
                    {"批次号": "703批", "产品": "C产品", "累计材料": 25000, "累计人工": 12000, "累计工时": 1000, "已完工": False, "完工数量": 0},
                ],
                "ch7_simple_table",
            )
            submitted = primary_button()
        if submitted:
            batches = [
                {
                    "name": row["批次号"], "product": row["产品"], "direct_material": row["累计材料"],
                    "direct_labor": row["累计人工"], "cumulative_hours": row["累计工时"],
                    "completed": bool(row["已完工"]), "completed_qty": row["完工数量"] if row["已完工"] else 0,
                }
                for _, row in frame.iterrows()
            ]
            calculate_and_store("ch7_simple", lambda: ur.simplified_batch_result(overhead, batches))
        demo_button("ch7_simple", lambda: ur.simplified_batch_result(18000, [
            {"name": "701批", "product": "A产品", "direct_material": 40000, "direct_labor": 18000, "cumulative_hours": 2000, "completed": True, "completed_qty": 100},
            {"name": "702批", "product": "B产品", "direct_material": 30000, "direct_labor": 14000, "cumulative_hours": 1500, "completed": True, "completed_qty": 80},
            {"name": "703批", "product": "C产品", "direct_material": 25000, "direct_labor": 12000, "cumulative_hours": 1000, "completed": False, "completed_qty": 0},
        ]))
        render_saved("ch7_simple")



# ---------------------------------------------------------------------------
# 第八章：分步法
# ---------------------------------------------------------------------------
DEFAULT_STEP_ROWS = [
    {"步骤": "第一车间", "产品": "甲半成品", "完工数量": 800, "在产品数量": 200, "完工程度(%)": 50.0, "直接材料": 50000, "直接人工": 18000, "制造费用": 9000},
    {"步骤": "第二车间", "产品": "甲产成品", "完工数量": 700, "在产品数量": 100, "完工程度(%)": 50.0, "直接材料": 0, "直接人工": 21000, "制造费用": 14000},
]


def page_chapter8() -> None:
    page_header("8", "产品成本计算——分步法", "综合结转（含成本还原）、分项结转和平行结转分步法。")
    method = st.selectbox("计算方法", ["逐步结转——综合结转", "逐步结转——分项结转", "平行结转"], key="ch8_method")
    if method == "平行结转":
        with st.form("ch8_parallel_form"):
            final_qty = decimal_input("最终产成品数量", 700, "ch8_parallel_final", step=10)
            frame = editable_table(
                [
                    {"步骤": "第一车间", "在产品数量": 200, "完工程度(%)": 50.0, "直接材料": 50000, "直接人工": 18000, "制造费用": 9000},
                    {"步骤": "第二车间", "在产品数量": 100, "完工程度(%)": 50.0, "直接材料": 0, "直接人工": 21000, "制造费用": 14000},
                ],
                "ch8_parallel_table",
            )
            submitted = primary_button()
        if submitted:
            steps = [
                {
                    "name": row["步骤"], "wip_qty": row["在产品数量"], "completion": float(row["完工程度(%)"]) / 100,
                    "material": row["直接材料"], "labor": row["直接人工"], "overhead": row["制造费用"],
                }
                for _, row in frame.iterrows()
            ]
            calculate_and_store("ch8_parallel", lambda: ur.parallel_step_result(final_qty, steps))
        demo_button("ch8_parallel", lambda: ur.parallel_step_result(700, [
            {"name": "第一车间", "wip_qty": 200, "completion": 0.5, "material": 50000, "labor": 18000, "overhead": 9000},
            {"name": "第二车间", "wip_qty": 100, "completion": 0.5, "material": 0, "labor": 21000, "overhead": 14000},
        ]))
        render_saved("ch8_parallel")
    else:
        with st.form("ch8_step_form"):
            frame = editable_table(DEFAULT_STEP_ROWS, "ch8_step_table")
            submitted = primary_button()
        if submitted:
            steps = [
                {
                    "name": row["步骤"], "product": row["产品"], "completed_qty": row["完工数量"], "wip_qty": row["在产品数量"],
                    "completion": float(row["完工程度(%)"]) / 100, "material": row["直接材料"], "labor": row["直接人工"], "overhead": row["制造费用"],
                }
                for _, row in frame.iterrows()
            ]
            if method == "逐步结转——综合结转":
                calculate_and_store("ch8_comprehensive", lambda: ur.comprehensive_step_result(steps))
            else:
                calculate_and_store("ch8_itemized", lambda: ur.itemized_step_result(steps))
        demo_steps = [
            {"name": "第一车间", "product": "甲半成品", "completed_qty": 800, "wip_qty": 200, "completion": 0.5, "material": 50000, "labor": 18000, "overhead": 9000},
            {"name": "第二车间", "product": "甲产成品", "completed_qty": 700, "wip_qty": 100, "completion": 0.5, "material": 0, "labor": 21000, "overhead": 14000},
        ]
        demo_button(
            "ch8_comprehensive" if method == "逐步结转——综合结转" else "ch8_itemized",
            lambda: ur.comprehensive_step_result(demo_steps) if method == "逐步结转——综合结转" else ur.itemized_step_result(demo_steps),
        )
        render_saved("ch8_comprehensive" if method == "逐步结转——综合结转" else "ch8_itemized")



# ---------------------------------------------------------------------------
# 第九章：辅助成本计算方法
# ---------------------------------------------------------------------------
def page_chapter9() -> None:
    page_header("9", "产品成本计算辅助方法", "分类法、联产品、副产品和定额法。")
    calc_type = st.selectbox("计算类型", ["分类法", "联产品成本分配", "副产品成本计算", "定额法"], key="ch9_type")
    if calc_type == "分类法":
        with st.form("ch9_class_form"):
            category = st.text_input("产品类别", "A类产品", key="ch9_class_category")
            total = money_input("类别总成本", 120000, "ch9_class_total")
            frame = editable_table(
                [
                    {"产品名称": "甲产品", "产量": 1000, "系数": 1.0},
                    {"产品名称": "乙产品", "产量": 600, "系数": 1.2},
                    {"产品名称": "丙产品", "产量": 400, "系数": 0.8},
                ],
                "ch9_class_table",
            )
            submitted = primary_button()
        if submitted:
            products = [{"name": row["产品名称"], "output": row["产量"], "coefficient": row["系数"]} for _, row in frame.iterrows()]
            calculate_and_store("ch9_class", lambda: ur.classification_result(category, total, products))
        demo_button("ch9_class", lambda: ur.classification_result("A类产品", 120000, [
            {"name": "甲产品", "output": 1000, "coefficient": 1.0},
            {"name": "乙产品", "output": 600, "coefficient": 1.2},
            {"name": "丙产品", "output": 400, "coefficient": 0.8},
        ]))
        render_saved("ch9_class")

    elif calc_type == "联产品成本分配":
        method = st.selectbox("分配方法", ["售价法", "实物量法", "可变现净值法"], key="ch9_joint_method")
        with st.form("ch9_joint_form"):
            total = money_input("联合成本", 200000, "ch9_joint_total")
            frame = editable_table(
                [
                    {"联产品": "甲联产品", "产量": 1000, "售价": 100.0, "进一步加工成本": 10000.0},
                    {"联产品": "乙联产品", "产量": 500, "售价": 160.0, "进一步加工成本": 20000.0},
                ],
                "ch9_joint_table",
            )
            submitted = primary_button()
        if submitted:
            products = [
                {"name": row["联产品"], "output": row["产量"], "unit_price": row["售价"], "further_cost": row["进一步加工成本"]}
                for _, row in frame.iterrows()
            ]
            calculate_and_store("ch9_joint", lambda: ur.joint_result(total, products, method))
        demo_button("ch9_joint", lambda: ur.joint_result(200000, [
            {"name": "甲联产品", "output": 1000, "unit_price": 100, "further_cost": 10000},
            {"name": "乙联产品", "output": 500, "unit_price": 160, "further_cost": 20000},
        ], method))
        render_saved("ch9_joint")

    elif calc_type == "副产品成本计算":
        with st.form("ch9_by_form"):
            total = money_input("联合成本", 200000, "ch9_by_total")
            main_output = decimal_input("主产品产量", 1000, "ch9_by_main", step=10)
            by_output = decimal_input("副产品产量", 200, "ch9_by_output", step=10)
            by_price = money_input("副产品售价（元/件）", 50, "ch9_by_price", step=10)
            further = money_input("副产品进一步加工成本", 2000, "ch9_by_further", step=100)
            submitted = primary_button()
        if submitted:
            calculate_and_store("ch9_by", lambda: ur.byproduct_result(total, main_output, by_output, by_price, further))
        demo_button("ch9_by", lambda: ur.byproduct_result(200000, 1000, 200, 50, 2000))
        render_saved("ch9_by")

    else:
        with st.form("ch9_norm_form"):
            c1, c2 = st.columns(2)
            with c1:
                completed = decimal_input("完工产品数量", 500, "ch9_norm_completed", step=10)
            with c2:
                wip = decimal_input("月末在产品数量", 100, "ch9_norm_wip", step=10)
            st.caption("现行单位定额（元/件）")
            c1, c2, c3 = st.columns(3)
            with c1:
                new_m = money_input("新材料定额", 80, "ch9_norm_new_m", step=10)
            with c2:
                new_l = money_input("新人工定额", 30, "ch9_norm_new_l", step=10)
            with c3:
                new_o = money_input("新制造费用定额", 20, "ch9_norm_new_o", step=10)
            st.caption("修订前单位定额（元/件）")
            c1, c2, c3 = st.columns(3)
            with c1:
                old_m = money_input("旧材料定额", 75, "ch9_norm_old_m", step=10)
            with c2:
                old_l = money_input("旧人工定额", 30, "ch9_norm_old_l", step=10)
            with c3:
                old_o = money_input("旧制造费用定额", 20, "ch9_norm_old_o", step=10)
            st.caption("本月实际费用（计划价格口径）")
            c1, c2, c3 = st.columns(3)
            with c1:
                actual_m = money_input("实际材料", 46000, "ch9_norm_actual_m")
            with c2:
                actual_l = money_input("实际人工", 16000, "ch9_norm_actual_l")
            with c3:
                actual_o = money_input("实际制造费用", 10000, "ch9_norm_actual_o")
            material_rate = rate_input("材料成本差异率（正数超支、负数节约）", 2.0, "ch9_norm_rate", allow_negative=True)
            submitted = primary_button()
        if submitted:
            calculate_and_store("ch9_norm", lambda: ur.norm_result(
                completed, wip, {"material": new_m, "labor": new_l, "overhead": new_o},
                {"material": old_m, "labor": old_l, "overhead": old_o},
                {"material": actual_m, "labor": actual_l, "overhead": actual_o}, material_rate,
            ))
        demo_button("ch9_norm", lambda: ur.norm_result(
            500, 100, {"material": 80, "labor": 30, "overhead": 20}, {"material": 75, "labor": 30, "overhead": 20},
            {"material": 46000, "labor": 16000, "overhead": 10000}, 0.02,
        ))
        render_saved("ch9_norm")



# ---------------------------------------------------------------------------
# 第十章：成本报表与成本分析
# ---------------------------------------------------------------------------
def page_chapter10() -> None:
    page_header("10", "成本报表编制与成本分析", "全部产品生产成本报表、可比产品降低分析、单位成本分析和成本结构分析。")
    calc_type = st.selectbox("分析类型", ["全部产品生产成本报表", "可比产品成本降低分析", "主要产品单位成本分析", "成本项目结构分析"], key="ch10_type")

    if calc_type == "全部产品生产成本报表":
        with st.form("ch10_report_form"):
            frame = editable_table(
                [
                    {"产品": "甲产品", "产量": 1000, "实际材料": 40, "实际人工": 20, "实际制造费用": 10, "计划材料": 38, "计划人工": 21, "计划制造费用": 11},
                    {"产品": "乙产品", "产量": 500, "实际材料": 60, "实际人工": 30, "实际制造费用": 15, "计划材料": 62, "计划人工": 28, "计划制造费用": 14},
                ],
                "ch10_report_table",
            )
            submitted = primary_button()
        if submitted:
            products = [
                {
                    "name": row["产品"], "output": row["产量"], "actual_material": row["实际材料"], "actual_labor": row["实际人工"],
                    "actual_overhead": row["实际制造费用"], "plan_material": row["计划材料"], "plan_labor": row["计划人工"], "plan_overhead": row["计划制造费用"],
                }
                for _, row in frame.iterrows()
            ]
            calculate_and_store("ch10_report", lambda: ur.production_report_result(products))
        demo_button("ch10_report", lambda: ur.production_report_result([
            {"name": "甲产品", "output": 1000, "actual_material": 40, "actual_labor": 20, "actual_overhead": 10, "plan_material": 38, "plan_labor": 21, "plan_overhead": 11},
            {"name": "乙产品", "output": 500, "actual_material": 60, "actual_labor": 30, "actual_overhead": 15, "plan_material": 62, "plan_labor": 28, "plan_overhead": 14},
        ]))
        render_saved("ch10_report")

    elif calc_type == "可比产品成本降低分析":
        with st.form("ch10_comp_form"):
            frame = editable_table(
                [
                    {"产品": "甲产品", "计划产量": 1000, "实际产量": 1100, "上年单位成本": 100, "计划单位成本": 95, "实际单位成本": 92},
                    {"产品": "乙产品", "计划产量": 500, "实际产量": 480, "上年单位成本": 80, "计划单位成本": 78, "实际单位成本": 79},
                ],
                "ch10_comp_table",
            )
            submitted = primary_button()
        if submitted:
            products = [
                {
                    "name": row["产品"], "plan_output": row["计划产量"], "actual_output": row["实际产量"],
                    "last_year_unit": row["上年单位成本"], "plan_unit": row["计划单位成本"], "actual_unit": row["实际单位成本"],
                }
                for _, row in frame.iterrows()
            ]
            calculate_and_store("ch10_comp", lambda: ur.comparable_result(products))
        demo_button("ch10_comp", lambda: ur.comparable_result([
            {"name": "甲产品", "plan_output": 1000, "actual_output": 1100, "last_year_unit": 100, "plan_unit": 95, "actual_unit": 92},
            {"name": "乙产品", "plan_output": 500, "actual_output": 480, "last_year_unit": 80, "plan_unit": 78, "actual_unit": 79},
        ]))
        render_saved("ch10_comp")


    elif calc_type == "主要产品单位成本分析":
        with st.form("ch10_unit_form"):
            product = st.text_input("产品名称", "甲产品", key="ch10_unit_product")
            st.caption("单位成本（元/件）")
            c1, c2, c3 = st.columns(3)
            with c1:
                ly_m = money_input("上年材料", 52, "ch10_unit_ly_m", step=1)
                ly_l = money_input("上年人工", 48, "ch10_unit_ly_l", step=1)
                ly_o = money_input("上年制造费用", 20, "ch10_unit_ly_o", step=1)
            with c2:
                pl_m = money_input("计划材料", 50, "ch10_unit_pl_m", step=1)
                pl_l = money_input("计划人工", 48, "ch10_unit_pl_l", step=1)
                pl_o = money_input("计划制造费用", 20, "ch10_unit_pl_o", step=1)
            with c3:
                ac_m = money_input("实际材料", 46.8, "ch10_unit_ac_m", step=1)
                ac_l = money_input("实际人工", 48, "ch10_unit_ac_l", step=1)
                ac_o = money_input("实际制造费用", 21, "ch10_unit_ac_o", step=1)
            st.caption("材料用量与价格")
            c1, c2 = st.columns(2)
            with c1:
                plan_qty = decimal_input("计划材料用量", 10, "ch10_unit_plan_qty", step=1)
                plan_price = money_input("计划材料单价", 5, "ch10_unit_plan_price", step=1)
            with c2:
                actual_qty = decimal_input("实际材料用量", 9, "ch10_unit_actual_qty", step=1)
                actual_price = money_input("实际材料单价", 5.2, "ch10_unit_actual_price", step=1)
            st.caption("人工工时与工资率")
            c1, c2 = st.columns(2)
            with c1:
                plan_hours = decimal_input("计划工时", 8, "ch10_unit_plan_hours", step=1)
                plan_rate = money_input("计划工资率", 6, "ch10_unit_plan_rate", step=1)
            with c2:
                actual_hours = decimal_input("实际工时", 7.5, "ch10_unit_actual_hours", step=1)
                actual_rate = money_input("实际工资率", 6.4, "ch10_unit_actual_rate", step=1)
            submitted = primary_button()
        if submitted:
            data = {
                "product": product,
                "last_year": {"material": ly_m, "labor": ly_l, "overhead": ly_o},
                "plan": {"material": pl_m, "labor": pl_l, "overhead": pl_o},
                "actual": {"material": ac_m, "labor": ac_l, "overhead": ac_o},
                "material": {"plan_qty": plan_qty, "plan_price": plan_price, "actual_qty": actual_qty, "actual_price": actual_price},
                "labor": {"plan_hours": plan_hours, "plan_rate": plan_rate, "actual_hours": actual_hours, "actual_rate": actual_rate},
            }
            calculate_and_store("ch10_unit", lambda: ur.unit_cost_result(data))
        demo_button("ch10_unit", lambda: ur.unit_cost_result({
            "product": "甲产品",
            "last_year": {"material": 52, "labor": 48, "overhead": 20},
            "plan": {"material": 50, "labor": 48, "overhead": 20},
            "actual": {"material": 46.8, "labor": 48, "overhead": 21},
            "material": {"plan_qty": 10, "plan_price": 5, "actual_qty": 9, "actual_price": 5.2},
            "labor": {"plan_hours": 8, "plan_rate": 6, "actual_hours": 7.5, "actual_rate": 6.4},
        }))
        render_saved("ch10_unit")

    else:
        with st.form("ch10_structure_form"):
            frame = editable_table(
                [
                    {"成本项目": "直接材料", "本期金额": 60000, "上期金额": 55000},
                    {"成本项目": "直接人工", "本期金额": 25000, "上期金额": 24000},
                    {"成本项目": "制造费用", "本期金额": 15000, "上期金额": 16000},
                ],
                "ch10_structure_table",
            )
            submitted = primary_button()
        if submitted:
            items = [{"name": row["成本项目"], "current": row["本期金额"], "prior": row["上期金额"]} for _, row in frame.iterrows()]
            calculate_and_store("ch10_structure", lambda: ur.structure_result(items))
        demo_button("ch10_structure", lambda: ur.structure_result([
            {"name": "直接材料", "current": 60000, "prior": 55000},
            {"name": "直接人工", "current": 25000, "prior": 24000},
            {"name": "制造费用", "current": 15000, "prior": 16000},
        ]))
        render_saved("ch10_structure")

