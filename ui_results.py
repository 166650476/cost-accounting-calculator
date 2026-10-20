"""把各章纯计算函数转换为 Streamlit 统一结果对象 CostResult。

本模块不直接创建页面，只负责：
- 调用章节纯计算函数；
- 组织题意、公式、步骤、表格、分录和结论；
- 让 ui_pages.py 可以专注于表单控件。
"""

from __future__ import annotations

from typing import Any, Dict, List, Sequence, Tuple

import chapter2_element_cost as ch2
import chapter3_auxiliary_cost as ch3
import chapter4_factory_cost_loss as ch4
import chapter5_wip_allocation as ch5
import chapter6_variety_method as ch6
import chapter7_batch_method as ch7
import chapter8_step_method as ch8
import chapter9_special_method as ch9
import chapter10_cost_analysis as ch10
import visual
from ui_core import CostResult
from utils import format_money, format_percent


def _m(value: Any) -> str:
    return format_money(value)


def _p(value: Any, digits: int = 2) -> str:
    return format_percent(value, digits)


# ---------------------------------------------------------------------------
# 第二章 要素费用
# ---------------------------------------------------------------------------
def material_result(total: float, products: Sequence[Dict[str, Any]], method: str) -> CostResult:
    r = ch2.allocate_material(total, products, method)
    basis_name = {
        "定额消耗量比例法": "定额消耗量",
        "定额费用比例法": "定额费用",
        "产品重量比例法": "产品重量",
        "产量比例法": "产量",
    }[method]
    question = (
        f"某企业本月耗用材料实际费用 {_m(r['total'])} 元，生产 {len(r['names'])} 种产品，"
        f"采用{method}分配材料费用。要求计算分配率、各产品材料费用并编制分录。"
    )
    formulas = [
        f"某产品分配标准 = 产量 × 单位{basis_name}（产量比例法直接用产量）",
        "材料费用分配率 = 材料实际费用总额 ÷ 分配标准合计",
        "某产品材料费用 = 该产品分配标准 × 分配率",
        "单位材料成本 = 该产品材料费用 ÷ 该产品产量",
    ]
    steps = []
    for name, output, basis, amount, unit_cost in zip(
        r["names"], r["outputs"], r["bases"], r["allocations"], r["unit_costs"]
    ):
        steps.append(
            f"{name}：分配标准 {basis:,.2f} × 分配率 {r['rate']:.6f} = {_m(amount)} 元；"
            f"单位材料成本 = {_m(amount)} ÷ {output:,.2f} = {_m(unit_cost)} 元/件。"
        )
    steps.append(f"验算：各产品材料费用合计 {_m(sum(r['allocations']))} 元，与材料费用总额一致。")
    headers = ["产品名称", "产量", "分配标准", "分配率", "分配金额（元）", "单位材料成本（元/件）"]
    rows = [
        [name, f"{output:,.2f}", f"{basis:,.2f}", f"{r['rate']:.6f}", _m(amount), _m(unit_cost)]
        for name, output, basis, amount, unit_cost in zip(
            r["names"], r["outputs"], r["bases"], r["allocations"], r["unit_costs"]
        )
    ]
    rows.append(["合计", f"{sum(r['outputs']):,.2f}", f"{r['total_basis']:,.2f}", "—", _m(sum(r["allocations"])), "—"])
    journal = ["借：生产成本——基本生产成本"]
    for name, amount in zip(r["names"], r["allocations"]):
        journal.append(f"    ——{name}     {_m(amount)}")
    journal.append(f"贷：原材料     {_m(r['total'])}")
    return CostResult(
        chapter="第二章 要素费用",
        title=f"材料费用分配——{method}",
        description="按定额消耗量、定额费用、重量或产量比例分配材料费用。",
        question=question,
        formulas=formulas,
        steps=steps,
        tables=[("材料费用分配表", headers, rows)],
        journal=journal,
        summary=[
            f"采用{method}，材料费用分配率为 {r['rate']:.6f}。",
            "分配标准口径必须与分配率分母一致，尾差已调整到最后一个产品。",
        ],
        metrics={"分配率": f"{r['rate']:.6f}", "材料费用合计": _m(r["total"]), "产品种数": str(len(r["names"]))},
        conclusion=f"各产品材料费用合计 {_m(sum(r['allocations']))} 元，分配平衡。",
    )


def power_result(total: float, products: Sequence[Dict[str, Any]]) -> CostResult:
    r = ch2.allocate_power(total, products)
    question = f"本月外购动力费用 {_m(r['total'])} 元，按机器工时比例分配。要求计算分配率并编制分录。"
    formulas = [
        "动力费用分配率 = 外购动力费用总额 ÷ 各产品机器工时合计",
        "某产品动力费用 = 该产品机器工时 × 分配率",
    ]
    steps = [
        f"机器工时合计 = {r['total_hours']:,.2f}；分配率 = {_m(r['total'])} ÷ {r['total_hours']:,.2f} = {r['rate']:.6f}。",
    ]
    for name, hours, amount in zip(r["names"], r["hours"], r["allocations"]):
        steps.append(f"{name}：{hours:,.2f} × {r['rate']:.6f} = {_m(amount)} 元。")
    headers = ["产品名称", "机器工时", "分配率", "分配金额（元）"]
    rows = [[name, f"{hours:,.2f}", f"{r['rate']:.6f}", _m(amount)] for name, hours, amount in zip(r["names"], r["hours"], r["allocations"])]
    rows.append(["合计", f"{r['total_hours']:,.2f}", "—", _m(sum(r["allocations"]))])
    journal = ["借：生产成本——基本生产成本"]
    for name, amount in zip(r["names"], r["allocations"]):
        journal.append(f"    ——{name}     {_m(amount)}")
    journal.append(f"贷：应付账款——供电公司     {_m(r['total'])}")
    return CostResult(
        chapter="第二章 要素费用",
        title="外购动力费用分配",
        description="按机器工时分配外购电力等动力费用。",
        question=question,
        formulas=formulas,
        steps=steps,
        tables=[("外购动力费用分配表", headers, rows)],
        journal=journal,
        summary=["动力费用按机器工时分配，符合受益原则。", "若动力用于车间照明或行政管理，应先计入制造费用或管理费用。"],
        metrics={"分配率": f"{r['rate']:.6f}", "动力费用合计": _m(r["total"])},
        conclusion=f"动力费用分配额合计 {_m(sum(r['allocations']))} 元。",
    )


def payroll_result(total_wage: float, products: Sequence[Dict[str, Any]], welfare_rate: float, social_rate: float) -> CostResult:
    r = ch2.allocate_payroll(total_wage, products, welfare_rate, social_rate)
    question = (
        f"生产工人工资总额 {_m(r['total'])} 元，按生产工时分配；福利费 {_p(r['welfare_rate'])}、"
        f"社会保险费 {_p(r['social_rate'])}。要求计算各产品职工薪酬并编制分录。"
    )
    formulas = [
        "工资分配率 = 工资总额 ÷ 生产工时合计",
        "某产品工资 = 该产品工时 × 工资分配率",
        "福利费 = 工资 × 福利费比例；社会保险费 = 工资 × 社保比例",
    ]
    steps = [f"生产工时合计 = {r['total_hours']:,.2f}；工资分配率 = {r['rate']:.6f}。"]
    for name, wage, welfare, social, total in zip(r["names"], r["wages"], r["welfare"], r["social"], r["totals"]):
        steps.append(f"{name}：工资 {_m(wage)} 元，福利费 {_m(welfare)} 元，社保 {_m(social)} 元，合计 {_m(total)} 元。")
    headers = ["产品名称", "生产工时", "工资（元）", "福利费（元）", "社会保险费（元）", "合计（元）"]
    rows = [
        [name, f"{hours:,.2f}", _m(wage), _m(welfare), _m(social), _m(total)]
        for name, hours, wage, welfare, social, total in zip(
            r["names"], r["hours"], r["wages"], r["welfare"], r["social"], r["totals"]
        )
    ]
    rows.append(["合计", f"{r['total_hours']:,.2f}", _m(sum(r["wages"])), _m(sum(r["welfare"])), _m(sum(r["social"])), _m(sum(r["totals"]))])
    journal = ["借：生产成本——基本生产成本"]
    for name, total in zip(r["names"], r["totals"]):
        journal.append(f"    ——{name}     {_m(total)}")
    journal.append(f"贷：应付职工薪酬——工资     {_m(sum(r['wages']))}")
    journal.append(f"贷：应付职工薪酬——职工福利     {_m(sum(r['welfare']))}")
    journal.append(f"贷：应付职工薪酬——社会保险费     {_m(sum(r['social']))}")
    return CostResult(
        chapter="第二章 要素费用",
        title="职工薪酬费用分配",
        description="按生产工时分配工资，并计提福利费和社会保险费。",
        question=question,
        formulas=formulas,
        steps=steps,
        tables=[("职工薪酬费用分配表", headers, rows)],
        journal=journal,
        summary=["工资按生产工时分配，福利费和社保以各产品工资为基数计提。", "核对工资、福利费、社保的计提基数是否一致。"],
        metrics={"工资分配率": f"{r['rate']:.6f}", "职工薪酬合计": _m(sum(r["totals"]))},
        conclusion=f"职工薪酬合计 {_m(sum(r['totals']))} 元。",
    )


def depreciation_result(assets: Sequence[Dict[str, Any]]) -> CostResult:
    r = ch2.calculate_depreciation(assets)
    question = "采用年限平均法计提固定资产折旧，要求计算月折旧额、按部门汇总并编制分录。"
    formulas = ["月折旧额 = 原值 ×（1 - 净残值率）÷ 使用年限 ÷ 12"]
    steps = [f"{item['name']}：月折旧额 {_m(item['monthly'])} 元，计入{item['department']}。" for item in r["rows"]]
    for dept, amount in r["departments"].items():
        steps.append(f"{dept}合计 = {_m(amount)} 元。")
    headers = ["固定资产", "原值（元）", "净残值率", "使用年限", "月折旧额（元）", "受益部门"]
    rows = [
        [item["name"], _m(item["original"]), _p(item["residual_rate"]), f"{item['life']:g} 年", _m(item["monthly"]), item["department"]]
        for item in r["rows"]
    ]
    rows.append(["合计", "—", "—", "—", _m(r["total"]), "—"])
    journal = []
    for dept, amount in r["departments"].items():
        journal.append(f"借：{dept}——折旧费     {_m(amount)}")
    journal.append(f"贷：累计折旧     {_m(r['total'])}")
    return CostResult(
        chapter="第二章 要素费用",
        title="折旧费用计算与分配",
        description="年限平均法下按受益部门归集折旧费用。",
        question=question,
        formulas=formulas,
        steps=steps,
        tables=[("折旧费用计算与分配表", headers, rows)],
        journal=journal,
        summary=["生产车间折旧计入制造费用，行政管理部门计入管理费用，销售部门计入销售费用。"],
        metrics={"本月折旧合计": _m(r["total"])},
        conclusion=f"本月折旧费用合计 {_m(r['total'])} 元。",
    )



def low_value_result(items: Sequence[Dict[str, Any]], method: str) -> CostResult:
    r = ch2.amortize_low_value(items, method)
    question = f"低值易耗品采用{method}，要求计算本月摊销额、按部门汇总并编制分录。"
    formulas = ["一次转销法：本月摊销额 = 领用金额", "五五摊销法：本月摊销额 = 领用金额 × 50%"]
    steps = [f"{item['name']}：本月摊销 {_m(item['current'])} 元，计入{item['department']}。" for item in r["rows"]]
    steps.append(f"本月摊销合计 {_m(r['total'])} 元。")
    headers = ["低值易耗品", "领用金额（元）", "本月摊销（元）", "尚待摊销（元）", "受益部门"]
    rows = [[item["name"], _m(item["amount"]), _m(item["current"]), _m(item["remaining"]), item["department"]] for item in r["rows"]]
    rows.append(["合计", _m(sum(item["amount"] for item in r["rows"])), _m(r["total"]), _m(sum(item["remaining"] for item in r["rows"])), "—"])
    journal = [f"借：{dept}——低值易耗品摊销     {_m(amount)}" for dept, amount in r["departments"].items()]
    credit_account = "周转材料——低值易耗品（摊销）" if method == "五五摊销法" else "周转材料——低值易耗品"
    journal.append(f"贷：{credit_account}     {_m(r['total'])}")
    return CostResult(
        chapter="第二章 要素费用",
        title=f"低值易耗品摊销——{method}",
        description="按一次转销法或五五摊销法计算本月摊销额。",
        question=question,
        formulas=formulas,
        steps=steps,
        tables=[("低值易耗品摊销分配表", headers, rows)],
        journal=journal,
        summary=[f"采用{method}，本月摊销额 {_m(r['total'])} 元。"],
        metrics={"本月摊销额": _m(r["total"])},
        conclusion=f"本月低值易耗品摊销 {_m(r['total'])} 元。",
    )


def taxes_result(items: Sequence[Dict[str, Any]]) -> CostResult:
    r = ch2.allocate_taxes_other(items)
    question = "归集税金和其他支出，按受益部门汇总并编制分录。"
    formulas = ["某部门费用 = 该部门各明细项目金额之和", "税金贷记应交税费；其他支出贷记银行存款等。"]
    steps = [f"{item['name']}：{_m(item['amount'])} 元，计入{item['department']}。" for item in r["rows"]]
    steps.append(f"全部项目合计 {_m(r['total'])} 元。")
    headers = ["费用项目", "金额（元）", "类别", "受益部门"]
    rows = [[item["name"], _m(item["amount"]), item["kind"], item["department"]] for item in r["rows"]]
    rows.append(["合计", _m(r["total"]), "—", "—"])
    journal = [f"借：{item['department']}——{item['name']}     {_m(item['amount'])}" for item in r["rows"]]
    if r["kinds"]["税金"]:
        journal.append(f"贷：应交税费     {_m(r['kinds']['税金'])}")
    if r["kinds"]["其他支出"]:
        journal.append(f"贷：银行存款等     {_m(r['kinds']['其他支出'])}")
    return CostResult(
        chapter="第二章 要素费用",
        title="税金和其他支出费用分配",
        description="按受益部门归集税金和其他支出。",
        question=question,
        formulas=formulas,
        steps=steps,
        tables=[("税金和其他支出分配表", headers, rows)],
        journal=journal,
        summary=["税金和其他支出按受益部门归集，不直接全部计入产品成本。"],
        metrics={"费用合计": _m(r["total"]), "税金": _m(r["kinds"]["税金"]), "其他支出": _m(r["kinds"]["其他支出"])},
        conclusion=f"税金和其他支出合计 {_m(r['total'])} 元。",
    )



# ---------------------------------------------------------------------------
# 第三章 辅助生产费用
# ---------------------------------------------------------------------------
def _recipient_account(name: str) -> str:
    return {"基本生产车间": "制造费用", "行政管理部门": "管理费用", "销售部门": "销售费用"}.get(name, f"辅助生产成本——{name}")


def aux_result(
    method: str,
    names: Sequence[str],
    costs: Sequence[float],
    q: Sequence[Sequence[float]],
    planned_rates: Sequence[float] | None = None,
) -> CostResult:
    external_names = list(names) + ["基本生产车间", "行政管理部门", "销售部门"]
    external_names = external_names[len(names):]
    if method == "直接分配法":
        r = ch3.direct_method(costs, q, names)
        headers = ["辅助车间", "直接费用（元）", "对外劳务量", "分配率"] + external_names + ["分配合计（元）"]
        rows = [
            [row["name"], _m(row["cost"]), f"{row['external_qty']:,.2f}", f"{row['rate']:.6f}",
             *[_m(x) for x in row["allocations"]], _m(sum(row["allocations"]))]
            for row in r["rows"]
        ]
        rows.append(["合计", _m(r["total"]), "—", "—", *[_m(x) for x in r["external_totals"]], _m(sum(r["external_totals"]))])
        steps = [
            f"{row['name']}：分配率 = {_m(row['cost'])} ÷ {row['external_qty']:,.2f} = {row['rate']:.6f}。"
            for row in r["rows"]
        ]
        steps.append(f"对外分配总额 = {_m(sum(r['external_totals']))} 元。")
        journal = []
        for name, amount in zip(external_names, r["external_totals"]):
            journal.append(f"借：{_recipient_account(name)}     {_m(amount)}")
        for row in r["rows"]:
            journal.append(f"贷：辅助生产成本——{row['name']}     {_m(row['cost'])}")
        tables = [("辅助生产费用分配表——直接分配法", headers, rows)]
        result = CostResult(
            chapter="第三章 辅助生产费用",
            title="辅助生产费用分配——直接分配法",
            description="不考虑辅助生产车间之间相互提供劳务，直接对外分配。",
            question="辅助车间之间相互服务较少，采用直接分配法分配辅助生产费用。",
            formulas=["分配率 = 辅助车间直接费用 ÷ 对外劳务量", "受益对象费用 = 接受劳务量 × 分配率"],
            steps=steps, tables=tables, journal=journal,
            summary=["直接分配法计算简便，但未考虑辅助车间之间的交互服务。"],
            metrics={"对外分配总额": _m(sum(r["external_totals"]))},
            conclusion=f"辅助生产费用对外分配总额 {_m(sum(r['external_totals']))} 元。",
        )
        return result

    if method == "一次交互分配法":
        r = ch3.interactive_method(costs, q, names)
        first_headers = ["辅助车间", "直接费用（元）", "劳务总量", "交互分配率"] + list(names) + ["转出合计（元）"]
        first_rows = [
            [row["name"], _m(row["cost"]), f"{row['total_service']:,.2f}", f"{row['rate']:.6f}",
             *[_m(x) for x in row["allocations"]], _m(row["out_total"])]
            for row in r["first_rows"]
        ]
        second_headers = ["辅助车间", "调整后费用（元）", "对外劳务量", "对外分配率"] + external_names + ["分配合计（元）"]
        second_rows = [
            [row["name"], _m(row["adjusted_cost"]), f"{row['external_qty']:,.2f}", f"{row['rate']:.6f}",
             *[_m(x) for x in row["allocations"]], _m(sum(row["allocations"]))]
            for row in r["second_rows"]
        ]
        second_rows.append(["合计", _m(r["total_adjusted"]), "—", "—", *[_m(x) for x in r["external_totals"]], _m(sum(r["external_totals"]))])
        steps = [
            f"{name} 调整后费用 = {_m(costs[i])} + 转入 {_m(r['transferred_in'][i])} - 转出 {_m(r['transferred_out'][i])} = {_m(r['adjusted_costs'][i])}。"
            for i, name in enumerate(names)
        ]
        steps.append(f"交互分配后调整费用合计 {_m(r['total_adjusted'])} 元。")
        journal = []
        for i, name in enumerate(names):
            for j, amount in enumerate(r["first_rows"][i]["allocations"]):
                if j != i and amount:
                    journal.append(f"借：辅助生产成本——{names[j]}     {_m(amount)}")
                    journal.append(f"贷：辅助生产成本——{name}     {_m(amount)}")
        for name, amount in zip(external_names, r["external_totals"]):
            journal.append(f"借：{_recipient_account(name)}     {_m(amount)}")
        for i, name in enumerate(names):
            journal.append(f"贷：辅助生产成本——{name}     {_m(r['adjusted_costs'][i])}")
        result = CostResult(
            chapter="第三章 辅助生产费用",
            title="辅助生产费用分配——一次交互分配法",
            description="先在辅助车间之间交互分配，再对外分配调整后的费用。",
            question="辅助车间之间相互提供劳务，采用一次交互分配法。",
            formulas=["交互分配率 = 直接费用 ÷ 劳务总量", "调整后费用 = 直接费用 + 转入 - 转出", "对外分配率 = 调整后费用 ÷ 对外劳务量"],
            steps=steps,
            tables=[("第一阶段：辅助车间交互分配表", first_headers, first_rows), ("第二阶段：对外分配表", second_headers, second_rows)],
            journal=journal,
            summary=["一次交互分配法考虑了辅助车间之间的相互服务，结果比直接分配法更准确。"],
            metrics={"调整后费用合计": _m(r["total_adjusted"]), "对外分配总额": _m(sum(r["external_totals"]))},
            conclusion=f"交互分配后调整费用合计 {_m(r['total_adjusted'])} 元。",
        )
        return result



    if method == "计划成本分配法":
        if not planned_rates:
            raise ValueError("计划成本分配法需要输入各辅助车间的计划单位成本。")
        r = ch3.planned_method(costs, q, names, planned_rates)
        recipients = list(names) + external_names
        headers = ["辅助车间", "计划单位成本", "劳务总量", "计划分配额（元）"] + recipients + ["分配合计（元）"]
        rows = [
            [row["name"], f"{row['planned_rate']:.2f}", f"{row['total_service']:,.2f}", _m(row["planned_out"]),
             *[_m(x) for x in row["allocations"]], _m(sum(row["allocations"]))]
            for row in r["rows"]
        ]
        diff_headers = ["辅助车间", "直接费用", "计划转入", "实际成本", "计划转出", "成本差异", "性质"]
        diff_rows = [
            [name, _m(costs[i]), _m(r["planned_in"][i]), _m(r["actual_costs"][i]), _m(r["planned_out"][i]),
             _m(r["differences"][i]), "超支" if r["differences"][i] >= 0 else "节约"]
            for i, name in enumerate(names)
        ]
        diff_rows.append(["合计", _m(sum(costs)), _m(sum(r["planned_in"])), _m(sum(r["actual_costs"])), _m(sum(r["planned_out"])), _m(r["total_difference"]), "—"])
        steps = [
            f"{row['name']}：计划分配额 = {row['planned_rate']:.2f} × {row['total_service']:,.2f} = {_m(row['planned_out'])} 元。"
            for row in r["rows"]
        ]
        for i, name in enumerate(names):
            steps.append(f"{name}：实际成本 {_m(r['actual_costs'][i])} 元，成本差异 {_m(r['differences'][i])} 元。")
        journal = []
        for i, row in enumerate(r["rows"]):
            for j, amount in enumerate(row["allocations"]):
                if amount:
                    journal.append(f"借：{_recipient_account(recipients[j])}     {_m(amount)}")
            journal.append(f"贷：辅助生产成本——{row['name']}     {_m(row['planned_out'])}")
        for i, name in enumerate(names):
            diff = r["differences"][i]
            if abs(diff) < 0.005:
                continue
            if diff > 0:
                journal.append(f"借：管理费用——辅助生产成本差异     {_m(diff)}")
                journal.append(f"贷：辅助生产成本——{name}     {_m(diff)}")
            else:
                journal.append(f"借：辅助生产成本——{name}     {_m(-diff)}")
                journal.append(f"贷：管理费用——辅助生产成本差异     {_m(-diff)}")
        result = CostResult(
            chapter="第三章 辅助生产费用",
            title="辅助生产费用分配——计划成本分配法",
            description="按计划单位成本分配，并计算、结转成本差异。",
            question="辅助车间计划单位成本已知，采用计划成本分配法分配辅助生产费用。",
            formulas=["计划分配额 = 计划单位成本 × 劳务总量", "实际成本 = 直接费用 + 计划转入", "成本差异 = 实际成本 - 计划转出"],
            steps=steps,
            tables=[("辅助生产费用计划成本分配表", headers, rows), ("辅助生产成本差异计算表", diff_headers, diff_rows)],
            journal=journal,
            summary=[f"计划分配额合计 {_m(sum(r['planned_out']))} 元，成本差异合计 {_m(r['total_difference'])} 元。"],
            metrics={"计划分配额": _m(sum(r["planned_out"])), "成本差异": _m(r["total_difference"])},
            conclusion=f"成本差异合计 {_m(r['total_difference'])} 元，已结转管理费用。",
        )
        return result

    r = ch3.algebraic_method(costs, q, names)
    recipients = r["recipient_names"]
    unit_headers = ["辅助车间", "直接费用（元）", "劳务总量", "待分配总成本（元）", "单位成本（元/单位）"]
    unit_rows = [
        [row["name"], _m(costs[i]), f"{row['total_service']:,.2f}", _m(row["total_cost"]), f"{row['unit_cost']:.6f}"]
        for i, row in enumerate(r["rows"])
    ]
    alloc_headers = ["辅助车间"] + recipients + ["分配合计（元）"]
    alloc_rows = [
        [row["name"], *[_m(x) for x in row["allocations"]], _m(sum(row["allocations"]))]
        for row in r["rows"]
    ]
    alloc_rows.append(["合计", *[_m(x) for x in r["recipient_totals"]], _m(r["total_allocated"])])
    steps = [
        f"{name}：待分配总成本 {_m(r['total_costs'][i])} 元，单位成本 {r['unit_costs'][i]:.6f} 元/单位。"
        for i, name in enumerate(names)
    ]
    steps.append(f"对外分配总额 {_m(r['external_total'])} 元，与直接费用合计 {_m(r['total'])} 元一致。")
    journal = []
    for row in r["rows"]:
        for j, amount in enumerate(row["allocations"]):
            if amount:
                journal.append(f"借：{_recipient_account(recipients[j])}     {_m(amount)}")
        journal.append(f"贷：辅助生产成本——{row['name']}     {_m(sum(row['allocations']))}")
    result = CostResult(
        chapter="第三章 辅助生产费用",
        title="辅助生产费用分配——代数分配法",
        description="联立方程求解各辅助车间单位成本，再按受益对象分配。",
        question="辅助车间相互提供劳务，采用代数分配法精确求解单位成本。",
        formulas=["x_i = 直接费用_i + Σ（j向i提供劳务 ÷ j劳务总量）× x_j", "单位成本 = x_i ÷ 劳务总量"],
        steps=steps,
        tables=[("代数分配法单位成本计算表", unit_headers, unit_rows), ("代数分配法费用分配表", alloc_headers, alloc_rows)],
        journal=journal,
        summary=["代数分配法同时考虑辅助车间之间的交互服务，分配结果最精确。", "对外分配总额应与辅助车间直接费用合计一致。"],
        metrics={"对外分配总额": _m(r["external_total"]), "直接费用合计": _m(r["total"])},
        conclusion=f"代数分配法对外分配总额 {_m(r['external_total'])} 元。",
    )
    return result



# ---------------------------------------------------------------------------
# 第四章 制造费用、生产损失与期间费用
# ---------------------------------------------------------------------------
def overhead_collect_result(items: Sequence[Dict[str, Any]]) -> CostResult:
    r = ch4.collect_overhead(items)
    question = "归集基本生产车间本月制造费用，要求编制明细表并写出会计分录。"
    formulas = ["制造费用合计 = 各明细项目金额之和"]
    steps = [f"{item['name']}：{_m(item['amount'])} 元，贷记“{item['source']}”。" for item in r["rows"]]
    steps.append(f"制造费用合计 {_m(r['total'])} 元。")
    headers = ["费用项目", "金额（元）", "贷方来源"]
    rows = [[item["name"], _m(item["amount"]), item["source"]] for item in r["rows"]]
    rows.append(["合计", _m(r["total"]), "—"])
    journal = [f"借：制造费用     {_m(r['total'])}"]
    for source, amount in r["sources"].items():
        journal.append(f"贷：{source}     {_m(amount)}")
    return CostResult(
        chapter="第四章 制造费用与生产损失",
        title="制造费用归集",
        description="按费用明细归集车间间接费用。",
        question=question, formulas=formulas, steps=steps,
        tables=[("制造费用明细表", headers, rows)], journal=journal,
        summary=["制造费用先归集，再按生产工时、工资或机器工时分配。"],
        metrics={"制造费用合计": _m(r["total"])},
        conclusion=f"制造费用归集总额 {_m(r['total'])} 元。",
    )


def overhead_allocate_result(total: float, products: Sequence[Dict[str, Any]], method: str) -> CostResult:
    r = ch4.allocate_overhead(total, products, method)
    basis_name = {"生产工时比例法": "生产工时", "生产工资比例法": "生产工资", "机器工时比例法": "机器工时"}[method]
    question = f"制造费用总额 {_m(r['total'])} 元，采用{method}分配。"
    formulas = [f"分配率 = 制造费用总额 ÷ {basis_name}合计", f"某产品制造费用 = 该产品{basis_name} × 分配率"]
    steps = [
        f"{basis_name}合计 = {r['total_base']:,.2f}；分配率 = {r['rate']:.6f}。",
    ]
    for name, base, amount in zip(r["names"], r["bases"], r["allocations"]):
        steps.append(f"{name}：{base:,.2f} × {r['rate']:.6f} = {_m(amount)} 元。")
    headers = ["产品名称", basis_name, "分配率", "分配金额（元）"]
    rows = [[name, f"{base:,.2f}", f"{r['rate']:.6f}", _m(amount)] for name, base, amount in zip(r["names"], r["bases"], r["allocations"])]
    rows.append(["合计", f"{r['total_base']:,.2f}", "—", _m(sum(r["allocations"]))])
    journal = ["借：生产成本——基本生产成本"]
    for name, amount in zip(r["names"], r["allocations"]):
        journal.append(f"    ——{name}     {_m(amount)}")
    journal.append(f"贷：制造费用     {_m(r['total'])}")
    return CostResult(
        chapter="第四章 制造费用与生产损失",
        title=f"制造费用分配——{method}",
        description="将归集的制造费用分配计入各产品成本。",
        question=question, formulas=formulas, steps=steps,
        tables=[("制造费用分配表", headers, rows)], journal=journal,
        summary=[f"采用{method}，分配率 {r['rate']:.6f}。"],
        metrics={"分配率": f"{r['rate']:.6f}", "制造费用合计": _m(r["total"])},
        conclusion=f"制造费用分配额合计 {_m(sum(r['allocations']))} 元。",
    )


def annual_planned_result(annual: float, annual_hours: float, monthly: float, products: Sequence[Dict[str, Any]]) -> CostResult:
    r = ch4.annual_planned_rate(annual, annual_hours, monthly, products)
    question = (
        f"年度计划制造费用 {_m(r['annual'])} 元，年度计划定额工时 {r['annual_hours']:,.2f}；"
        f"本月实际制造费用 {_m(r['monthly'])} 元。采用年度计划分配率法分配。"
    )
    formulas = ["年度计划分配率 = 年度计划制造费用 ÷ 年度计划定额工时", "本月分配额 = 本月实际工时 × 年度计划分配率", "成本差异 = 本月实际制造费用 - 本月分配额合计"]
    steps = [f"年度计划分配率 = {_m(r['annual'])} ÷ {r['annual_hours']:,.2f} = {r['rate']:.6f}。"]
    for name, hours, amount in zip(r["names"], r["hours"], r["allocations"]):
        steps.append(f"{name}：{hours:,.2f} × {r['rate']:.6f} = {_m(amount)} 元。")
    steps.append(f"本月分配额合计 {_m(r['allocated_total'])} 元，成本差异 {_m(r['difference'])} 元。")
    headers = ["产品名称", "本月实际工时", "年度计划分配率", "本月分配额（元）"]
    rows = [[name, f"{hours:,.2f}", f"{r['rate']:.6f}", _m(amount)] for name, hours, amount in zip(r["names"], r["hours"], r["allocations"])]
    rows.append(["合计", f"{sum(r['hours']):,.2f}", "—", _m(r["allocated_total"])])
    journal = ["借：生产成本——基本生产成本"]
    for name, amount in zip(r["names"], r["allocations"]):
        journal.append(f"    ——{name}     {_m(amount)}")
    journal.append(f"贷：制造费用     {_m(r['allocated_total'])}")
    if r["difference"] > 0:
        journal.append(f"借：生产成本——基本生产成本     {_m(r['difference'])}")
        journal.append(f"贷：制造费用     {_m(r['difference'])}")
    elif r["difference"] < 0:
        journal.append(f"借：制造费用     {_m(-r['difference'])}")
        journal.append(f"贷：生产成本——基本生产成本     {_m(-r['difference'])}")
    return CostResult(
        chapter="第四章 制造费用与生产损失",
        title="制造费用分配——年度计划分配率法",
        description="按年度计划分配率分配制造费用，并计算月末差异。",
        question=question, formulas=formulas, steps=steps,
        tables=[("年度计划分配率法制造费用分配表", headers, rows)], journal=journal,
        summary=[f"年度计划分配率 {r['rate']:.6f}，本月分配额 {_m(r['allocated_total'])} 元，成本差异 {_m(r['difference'])} 元。"],
        metrics={"年度计划分配率": f"{r['rate']:.6f}", "本月分配额": _m(r["allocated_total"]), "成本差异": _m(r["difference"])},
        conclusion=f"本月制造费用分配完成，差异 {_m(r['difference'])} 元。",
    )



def unrepairable_quota_result(product: str, qty: float, material: float, labor: float, overhead: float, scrap: float, compensation: float) -> CostResult:
    r = ch4.unrepairable_quota(qty, {"material": material, "labor": labor, "overhead": overhead}, scrap, compensation)
    question = (
        f"{product}发现不可修复废品 {qty:g} 件，单位材料/人工/制造费用定额分别为 {_m(material)}、{_m(labor)}、{_m(overhead)} 元；"
        f"残料 {_m(scrap)} 元，赔款 {_m(compensation)} 元。按定额成本计算废品损失。"
    )
    formulas = ["废品定额成本 = 废品数量 ×（材料定额 + 人工定额 + 制造费用定额）", "废品净损失 = 废品定额成本 - 残料 - 赔款"]
    steps = [
        f"材料定额成本 {_m(r['material_total'])} 元，人工定额成本 {_m(r['labor_total'])} 元，制造费用定额成本 {_m(r['overhead_total'])} 元。",
        f"废品定额成本 {_m(r['total'])} 元，净损失 {_m(r['net_loss'])} 元。",
    ]
    headers = ["成本项目", "单位定额", "废品数量", "定额成本（元）"]
    rows = [
        ["直接材料", _m(material), f"{qty:g}", _m(r["material_total"])],
        ["直接人工", _m(labor), f"{qty:g}", _m(r["labor_total"])],
        ["制造费用", _m(overhead), f"{qty:g}", _m(r["overhead_total"])],
        ["合计", "—", f"{qty:g}", _m(r["total"])],
        ["减：残料", "—", "—", _m(r["scrap"])],
        ["减：赔款", "—", "—", _m(r["compensation"])],
        ["废品净损失", "—", "—", _m(r["net_loss"])],
    ]
    journal = [
        f"借：废品损失——{product}     {_m(r['total'])}",
        f"贷：生产成本——基本生产成本（{product}）     {_m(r['total'])}",
        f"借：原材料     {_m(r['scrap'])}",
        f"借：其他应收款     {_m(r['compensation'])}",
        f"贷：废品损失——{product}     {_m(r['scrap'] + r['compensation'])}",
        f"借：生产成本——基本生产成本（{product}）——废品损失     {_m(r['net_loss'])}",
        f"贷：废品损失——{product}     {_m(r['net_loss'])}",
    ]
    return CostResult(
        chapter="第四章 制造费用与生产损失",
        title="不可修复废品损失——按定额成本",
        description="按单位定额成本计算不可修复废品损失。",
        question=question, formulas=formulas, steps=steps,
        tables=[("不可修复废品损失计算表（定额成本）", headers, rows)], journal=journal,
        summary=["按定额成本计算废品损失，适用于定额资料比较健全的企业。"],
        metrics={"废品定额成本": _m(r["total"]), "废品净损失": _m(r["net_loss"])},
        conclusion=f"废品净损失 {_m(r['net_loss'])} 元。",
    )


def unrepairable_actual_result(product: str, total_cost: float, total_output: float, qty: float, scrap: float, compensation: float) -> CostResult:
    r = ch4.unrepairable_actual(total_cost, total_output, qty, scrap, compensation)
    question = f"{product}实际总成本 {_m(total_cost)} 元，总产量 {total_output:,.2f} 件，不可修复废品 {qty:g} 件。按实际成本计算废品损失。"
    formulas = ["实际单位成本 = 实际总成本 ÷ 总产量", "废品实际成本 = 废品数量 × 实际单位成本", "废品净损失 = 废品实际成本 - 残料 - 赔款"]
    steps = [
        f"实际单位成本 = {_m(r['total_cost'])} ÷ {r['total_output']:,.2f} = {_m(r['unit_cost'])} 元/件。",
        f"废品实际成本 = {qty:g} × {_m(r['unit_cost'])} = {_m(r['defective_cost'])} 元，净损失 {_m(r['net_loss'])} 元。",
    ]
    headers = ["项目", "金额/数量"]
    rows = [
        ["实际总成本（元）", _m(r["total_cost"])],
        ["总产量（件）", f"{r['total_output']:,.2f}"],
        ["实际单位成本（元/件）", _m(r["unit_cost"])],
        ["废品数量（件）", f"{r['defective_qty']:g}"],
        ["废品实际成本（元）", _m(r["defective_cost"])],
        ["减：残料（元）", _m(r["scrap"])],
        ["减：赔款（元）", _m(r["compensation"])],
        ["废品净损失（元）", _m(r["net_loss"])],
    ]
    journal = [
        f"借：废品损失——{product}     {_m(r['defective_cost'])}",
        f"贷：生产成本——基本生产成本（{product}）     {_m(r['defective_cost'])}",
        f"借：原材料     {_m(r['scrap'])}",
        f"借：其他应收款     {_m(r['compensation'])}",
        f"贷：废品损失——{product}     {_m(r['scrap'] + r['compensation'])}",
        f"借：生产成本——基本生产成本（{product}）——废品损失     {_m(r['net_loss'])}",
        f"贷：废品损失——{product}     {_m(r['net_loss'])}",
    ]
    return CostResult(
        chapter="第四章 制造费用与生产损失",
        title="不可修复废品损失——按实际成本",
        description="按实际单位成本计算不可修复废品损失。",
        question=question, formulas=formulas, steps=steps,
        tables=[("不可修复废品损失计算表（实际成本）", headers, rows)], journal=journal,
        summary=["按实际成本计算要求完整的产量和成本资料。"],
        metrics={"实际单位成本": _m(r["unit_cost"]), "废品净损失": _m(r["net_loss"])},
        conclusion=f"废品净损失 {_m(r['net_loss'])} 元。",
    )



def repairable_result(product: str, material: float, labor: float, overhead: float, scrap: float, compensation: float) -> CostResult:
    r = ch4.repairable_loss(material, labor, overhead, scrap, compensation)
    question = f"{product}发现可修复废品，修复耗用材料 {_m(material)}、人工 {_m(labor)}、制造费用 {_m(overhead)}；残料 {_m(scrap)}、赔款 {_m(compensation)}。"
    formulas = ["修复费用 = 材料 + 人工 + 制造费用", "可修复废品净损失 = 修复费用 - 残料 - 赔款"]
    steps = [
        f"修复费用合计 {_m(r['total'])} 元。",
        f"可修复废品净损失 = {_m(r['total'])} - {_m(r['scrap'])} - {_m(r['compensation'])} = {_m(r['net_loss'])} 元。",
    ]
    headers = ["成本项目", "金额（元）"]
    rows = [
        ["修复用材料", _m(r["material"])],
        ["修复用人工", _m(r["labor"])],
        ["修复用制造费用", _m(r["overhead"])],
        ["修复费用合计", _m(r["total"])],
        ["减：残料", _m(r["scrap"])],
        ["减：赔款", _m(r["compensation"])],
        ["可修复废品净损失", _m(r["net_loss"])],
    ]
    journal = [
        f"借：废品损失——{product}     {_m(r['total'])}",
        f"贷：原材料     {_m(r['material'])}",
        f"贷：应付职工薪酬     {_m(r['labor'])}",
        f"贷：制造费用     {_m(r['overhead'])}",
        f"借：原材料     {_m(r['scrap'])}",
        f"借：其他应收款     {_m(r['compensation'])}",
        f"贷：废品损失——{product}     {_m(r['scrap'] + r['compensation'])}",
        f"借：生产成本——基本生产成本（{product}）——废品损失     {_m(r['net_loss'])}",
        f"贷：废品损失——{product}     {_m(r['net_loss'])}",
    ]
    return CostResult(
        chapter="第四章 制造费用与生产损失",
        title="可修复废品损失",
        description="计算修复费用及扣除残料、赔款后的净损失。",
        question=question, formulas=formulas, steps=steps,
        tables=[("可修复废品损失计算表", headers, rows)], journal=journal,
        summary=["可修复废品修复后仍可作为合格品出售，只将净损失计入产品成本。"],
        metrics={"修复费用": _m(r["total"]), "净损失": _m(r["net_loss"])},
        conclusion=f"可修复废品净损失 {_m(r['net_loss'])} 元。",
    )


def downtime_result(total_loss: float, is_normal: bool, insurance: float) -> CostResult:
    r = ch4.downtime_loss(total_loss, is_normal, insurance)
    question = f"停工损失 {_m(total_loss)} 元，取得赔偿 {_m(insurance)} 元，属于{'正常' if is_normal else '非正常'}停工。"
    formulas = ["停工净损失 = 停工损失总额 - 赔偿", "正常停工计入生产成本；非正常停工计入营业外支出。"]
    steps = [f"停工净损失 = {_m(r['total'])} - {_m(r['insurance'])} = {_m(r['net'])} 元。", f"处理方式：{r['treatment']}。"]
    headers = ["项目", "金额（元）"]
    rows = [["停工损失总额", _m(r["total"])], ["减：赔偿", _m(r["insurance"])], ["停工净损失", _m(r["net"])], ["处理方向", r["treatment"]]]
    journal = [
        f"借：停工损失     {_m(r['total'])}",
        f"贷：应付职工薪酬/制造费用等     {_m(r['total'])}",
    ]
    if r["insurance"]:
        journal.append(f"借：其他应收款     {_m(r['insurance'])}")
    journal.append(f"借：{'生产成本——基本生产成本（停工损失）' if is_normal else '营业外支出——非常损失'}     {_m(r['net'])}")
    journal.append(f"贷：停工损失     {_m(r['total'])}")
    return CostResult(
        chapter="第四章 制造费用与生产损失",
        title="停工损失核算",
        description="区分正常停工与非正常停工进行会计处理。",
        question=question, formulas=formulas, steps=steps,
        tables=[("停工损失计算表", headers, rows)], journal=journal,
        summary=[f"停工净损失 {_m(r['net'])} 元，{r['treatment']}。"],
        metrics={"停工净损失": _m(r["net"]), "处理方式": r["treatment"]},
        conclusion=f"停工净损失 {_m(r['net'])} 元。",
    )


def period_expense_result(sales: float, admin: float, finance: float) -> CostResult:
    r = ch4.period_expenses(sales, admin, finance)
    question = f"销售费用 {_m(sales)}、管理费用 {_m(admin)}、财务费用 {_m(finance)}，期末结转本年利润。"
    formulas = ["期间费用合计 = 销售费用 + 管理费用 + 财务费用"]
    steps = [f"期间费用合计 = {_m(r['sales'])} + {_m(r['admin'])} + {_m(r['finance'])} = {_m(r['total'])} 元。"]
    headers = ["期间费用项目", "金额（元）", "结转方向"]
    rows = [["销售费用", _m(r["sales"]), "本年利润"], ["管理费用", _m(r["admin"]), "本年利润"], ["财务费用", _m(r["finance"]), "本年利润"], ["合计", _m(r["total"]), "—"]]
    journal = [
        f"借：本年利润     {_m(r['total'])}",
        f"贷：销售费用     {_m(r['sales'])}",
        f"贷：管理费用     {_m(r['admin'])}",
        f"贷：财务费用     {_m(r['finance'])}",
    ]
    return CostResult(
        chapter="第四章 制造费用与生产损失",
        title="期间费用结转",
        description="销售费用、管理费用、财务费用期末结转本年利润。",
        question=question, formulas=formulas, steps=steps,
        tables=[("期间费用结转表", headers, rows)], journal=journal,
        summary=["期间费用不计入产品成本，直接影响当期利润。"],
        metrics={"期间费用合计": _m(r["total"])},
        conclusion=f"期间费用合计 {_m(r['total'])} 元，已结转本年利润。",
    )



# ---------------------------------------------------------------------------
# 第五章 完工产品与在产品分配
# ---------------------------------------------------------------------------
def _wip_result(
    title: str,
    question: str,
    formulas: Sequence[str],
    steps: Sequence[str],
    sheet: Dict[str, Any],
    *,
    extra_tables: Sequence[Tuple[str, Sequence[Any], Sequence[Sequence[Any]]]] = (),
    summary: Sequence[str] = (),
) -> CostResult:
    tables = [("产品成本计算单", ch5.COST_SHEET_HEADERS, sheet["rows"])]
    tables.extend(extra_tables)
    return CostResult(
        chapter="第五章 完工产品与在产品分配",
        title=title,
        description="将生产费用在完工产品和月末在产品之间分配。",
        question=question,
        formulas=formulas,
        steps=steps,
        tables=tables,
        journal=ch5.finished_goods_journal(sheet),
        summary=summary or ["完工产品成本与期末在产品成本之和应等于生产费用总额。"],
        metrics={"完工产品总成本": _m(sheet["completed_total"]), "期末在产品成本": _m(sheet["wip_total"]), "单位完工成本": _m(sheet["unit_cost"])},
        conclusion=f"完工产品成本 {_m(sheet['completed_total'])} 元，单位成本 {_m(sheet['unit_cost'])} 元/件。",
    )


def no_wip_result(product: str, completed: float, material: float, labor: float, overhead: float) -> CostResult:
    sheet = ch5.method_no_wip(material, labor, overhead, completed)
    return _wip_result(
        "不计算在产品成本法",
        f"{product}完工 {completed:,.2f} 件，月末在产品很少，采用不计算在产品成本法。",
        ["完工产品总成本 = 本月生产费用总额", "单位成本 = 完工产品总成本 ÷ 完工数量"],
        [f"生产费用总额 {_m(sheet['total_cost'])} 元，全部由完工产品负担。", f"单位成本 {_m(sheet['unit_cost'])} 元/件。"],
        sheet,
        summary=["不计算在产品成本法适用于月末在产品数量很少或价值较低的情况。"],
    )


def fixed_wip_result(product: str, completed: float, wip: float, material: float, labor: float, overhead: float, fixed_material: float, fixed_labor: float, fixed_overhead: float) -> CostResult:
    sheet = ch5.method_fixed_wip(material, labor, overhead, {"material": fixed_material, "labor": fixed_labor, "overhead": fixed_overhead}, completed)
    return _wip_result(
        "在产品按固定成本计价法",
        f"{product}完工 {completed:,.2f} 件，在产品 {wip:,.2f} 件，在产品按固定成本计价。",
        ["在产品成本 = 固定材料 + 固定人工 + 固定制造费用", "完工产品成本 = 生产费用总额 - 在产品固定成本"],
        [f"固定在产品成本 {_m(sheet['wip_total'])} 元；完工产品成本 {_m(sheet['completed_total'])} 元。"],
        sheet,
        summary=["适用于各月末在产品数量较少或数量变化不大的情况。"],
    )


def material_only_result(product: str, completed: float, wip: float, material: float, labor: float, overhead: float) -> CostResult:
    sheet = ch5.method_material_only(material, labor, overhead, completed, wip)
    return _wip_result(
        "在产品按原材料费用计价法",
        f"{product}完工 {completed:,.2f} 件，在产品 {wip:,.2f} 件；原材料一次投入，在产品只负担材料费用。",
        ["材料分配率 = 材料总额 ÷（完工数量 + 在产品数量）", "在产品材料成本 = 在产品数量 × 材料分配率", "加工费用全部由完工产品负担"],
        [f"在产品材料成本 {_m(sheet['wip'][0])} 元；完工产品材料成本 {_m(sheet['completed'][0])} 元。", f"完工产品总成本 {_m(sheet['completed_total'])} 元。"],
        sheet,
        summary=["适用于材料费用占产品成本比重很大、材料一次投入的企业。"],
    )



def equivalent_result(product: str, completed: float, wip: float, material: float, labor: float, overhead: float, material_completion: float, processing_completion: float) -> CostResult:
    r = ch5.method_equivalent(material, labor, overhead, completed, wip, material_completion, processing_completion)
    sheet = r["sheet"]
    extra_headers = ["成本项目", "费用总额", "约当产量", "分配率", "完工产品成本", "期末在产品成本"]
    extra_rows = [
        ["直接材料", _m(material), f"{r['material_eq']:,.2f}", f"{r['material_rate']:.6f}", _m(sheet["completed"][0]), _m(sheet["wip"][0])],
        ["直接人工", _m(labor), f"{r['processing_eq']:,.2f}", f"{r['labor_rate']:.6f}", _m(sheet["completed"][1]), _m(sheet["wip"][1])],
        ["制造费用", _m(overhead), f"{r['processing_eq']:,.2f}", f"{r['overhead_rate']:.6f}", _m(sheet["completed"][2]), _m(sheet["wip"][2])],
    ]
    return _wip_result(
        "约当产量比例法",
        f"{product}完工 {completed:,.2f} 件，在产品 {wip:,.2f} 件，材料投料程度 {_p(material_completion)}，加工完工程度 {_p(processing_completion)}。",
        ["材料约当产量 = 完工数量 + 在产品数量 × 投料程度", "加工费约当产量 = 完工数量 + 在产品数量 × 完工程度", "分配率 = 费用总额 ÷ 约当产量"],
        [f"材料约当产量 {r['material_eq']:,.2f}；加工费约当产量 {r['processing_eq']:,.2f}。", f"完工产品成本 {_m(sheet['completed_total'])} 元，期末在产品 {_m(sheet['wip_total'])} 元。"],
        sheet,
        extra_tables=[("约当产量与费用分配表", extra_headers, extra_rows)],
        summary=["材料按投料程度折算，人工和制造费用按加工完工程度折算。"],
    )


def quota_wip_result(product: str, completed: float, wip: float, material: float, labor: float, overhead: float, unit_material: float, unit_labor: float, unit_overhead: float) -> CostResult:
    sheet = ch5.method_quota_wip(material, labor, overhead, wip, {"material": unit_material, "labor": unit_labor, "overhead": unit_overhead}, completed)
    return _wip_result(
        "在产品按定额成本计价法",
        f"{product}完工 {completed:,.2f} 件，在产品 {wip:,.2f} 件，按单位定额成本计价。",
        ["在产品定额成本 = 在产品数量 × 单位定额成本", "完工产品成本 = 费用总额 - 在产品定额成本"],
        [f"在产品定额成本 {_m(sheet['wip_total'])} 元；完工产品成本 {_m(sheet['completed_total'])} 元。"],
        sheet,
        summary=["实际成本与定额成本的差异全部由完工产品负担。"],
    )


def quota_ratio_result(product: str, completed: float, wip: float, material: float, labor: float, overhead: float, unit_material_quota: float, material_completion: float, unit_hour_quota: float, processing_completion: float) -> CostResult:
    completed_material_quota = completed * unit_material_quota
    wip_material_quota = wip * unit_material_quota * material_completion
    completed_hours = completed * unit_hour_quota
    wip_hours = wip * unit_hour_quota * processing_completion
    r = ch5.method_quota_ratio(material, labor, overhead, completed_material_quota, wip_material_quota, completed_hours, wip_hours, completed)
    sheet = r["sheet"]
    extra_headers = ["成本项目", "费用总额", "分配标准合计", "分配率", "完工产品成本", "期末在产品成本"]
    extra_rows = [
        ["直接材料", _m(material), f"{r['material_base']:,.2f}", f"{r['material_rate']:.6f}", _m(sheet["completed"][0]), _m(sheet["wip"][0])],
        ["直接人工", _m(labor), f"{r['hours_base']:,.2f}", f"{r['labor_rate']:.6f}", _m(sheet["completed"][1]), _m(sheet["wip"][1])],
        ["制造费用", _m(overhead), f"{r['hours_base']:,.2f}", f"{r['overhead_rate']:.6f}", _m(sheet["completed"][2]), _m(sheet["wip"][2])],
    ]
    return _wip_result(
        "定额比例法",
        f"{product}完工 {completed:,.2f} 件，在产品 {wip:,.2f} 件；材料按材料定额、加工费按工时定额分配。",
        ["材料分配率 = 材料总额 ÷ 材料定额合计", "人工/制造费用分配率 = 费用总额 ÷ 工时定额合计"],
        [f"完工产品材料定额 {completed_material_quota:,.2f}，在产品材料定额 {wip_material_quota:,.2f}。", f"完工产品总成本 {_m(sheet['completed_total'])} 元，在产品成本 {_m(sheet['wip_total'])} 元。"],
        sheet,
        extra_tables=[("定额比例法费用分配表", extra_headers, extra_rows)],
        summary=["材料定额与工时定额分别与材料费用、加工费用对应，不能交叉使用。"],
    )



# ---------------------------------------------------------------------------
# 第六章 品种法
# ---------------------------------------------------------------------------
def single_variety_result(product: str, material: float, labor: float, overhead: float, completed: float, wip: float, completion: float) -> CostResult:
    r = ch6.single_variety(material, labor, overhead, completed, wip, completion, product)
    sheet = r["sheet"]
    steps = [
        f"材料约当产量 = {completed:,.2f} + {wip:,.2f} = {r['material_eq']:,.2f}。",
        f"加工费约当产量 = {completed:,.2f} + {wip:,.2f} × {_p(completion)} = {r['processing_eq']:,.2f}。",
        f"材料分配率 {r['material_rate']:.6f}，人工分配率 {r['labor_rate']:.6f}，制造费用分配率 {r['overhead_rate']:.6f}。",
        f"完工产品成本 {_m(sheet['completed_total'])} 元，单位成本 {_m(sheet['unit_cost'])} 元/件。",
    ]
    journal = [
        f"借：生产成本——基本生产成本（{product}）     {_m(sheet['total_cost'])}",
        f"贷：原材料     {_m(material)}",
        f"贷：应付职工薪酬     {_m(labor)}",
        f"贷：制造费用     {_m(overhead)}",
        f"借：库存商品——{product}     {_m(sheet['completed_total'])}",
        f"贷：生产成本——基本生产成本（{product}）     {_m(sheet['completed_total'])}",
    ]
    return CostResult(
        chapter="第六章 品种法",
        title="单一品种品种法",
        description="按产品品种归集生产费用，按约当产量分配完工与在产品成本。",
        question=f"{product}完工 {completed:,.2f} 件，在产品 {wip:,.2f} 件，完工程度 {_p(completion)}；材料、人工、制造费用分别为 {_m(material)}、{_m(labor)}、{_m(overhead)} 元。",
        formulas=["材料约当产量 = 完工数量 + 在产品数量", "加工费约当产量 = 完工数量 + 在产品数量 × 完工程度"],
        steps=steps,
        tables=[("产品成本计算单", ch5.COST_SHEET_HEADERS, sheet["rows"])],
        journal=journal,
        summary=["品种法以产品品种为成本计算对象，月末在完工产品与在产品之间分配生产费用。"],
        metrics={"完工产品总成本": _m(sheet["completed_total"]), "单位成本": _m(sheet["unit_cost"]), "在产品成本": _m(sheet["wip_total"])},
        conclusion=f"完工产品成本 {_m(sheet['completed_total'])} 元，单位成本 {_m(sheet['unit_cost'])} 元/件。",
    )


def multi_variety_result(total_material: float, total_labor: float, total_overhead: float, products: Sequence[Dict[str, Any]]) -> CostResult:
    r = ch6.multi_variety(total_material, total_labor, total_overhead, products)
    alloc_headers = ["产品名称", "完工产量", "材料定额标准", "生产工时", "材料分配额", "人工分配额", "制造费用分配额", "费用合计"]
    alloc_rows = [
        [item["name"], f"{item['output']:,.2f}", f"{item['material_base']:,.2f}", f"{item['hour_base']:,.2f}",
         _m(item["material_alloc"]), _m(item["labor_alloc"]), _m(item["overhead_alloc"]),
         _m(item["material_alloc"] + item["labor_alloc"] + item["overhead_alloc"])]
        for item in r["products"]
    ]
    alloc_rows.append(["合计", f"{sum(item['output'] for item in r['products']):,.2f}", f"{r['material_base_total']:,.2f}", f"{r['hour_total']:,.2f}",
                       _m(sum(item['material_alloc'] for item in r["products"])), _m(sum(item['labor_alloc'] for item in r["products"])),
                       _m(sum(item['overhead_alloc'] for item in r["products"])), _m(r["total_cost"])])
    tables: List[Tuple[str, Sequence[Any], Sequence[Sequence[Any]]]] = [("多品种共同费用分配表", alloc_headers, alloc_rows)]
    summary_rows = []
    for item in r["products"]:
        sheet = item["sheet"]
        tables.append((f"{item['name']}产品成本计算单", ch5.COST_SHEET_HEADERS, sheet["rows"]))
        summary_rows.append([item["name"], _m(sheet["completed_total"]), _m(sheet["wip_total"]), _m(sheet["unit_cost"])])
    summary_rows.append(["合计", _m(r["total_completed"]), _m(r["total_wip"]), "—"])
    tables.append(("多品种完工产品成本汇总表", ["产品名称", "完工总成本", "期末在产品成本", "单位成本"], summary_rows))
    journal = ["借：生产成本——基本生产成本"]
    for item in r["products"]:
        journal.append(f"    ——{item['name']}     {_m(item['material_alloc'] + item['labor_alloc'] + item['overhead_alloc'])}")
    journal.append(f"贷：原材料     {_m(total_material)}")
    journal.append(f"贷：应付职工薪酬     {_m(total_labor)}")
    journal.append(f"贷：制造费用     {_m(total_overhead)}")
    for item in r["products"]:
        sheet = item["sheet"]
        journal.append(f"借：库存商品——{item['name']}     {_m(sheet['completed_total'])}")
        journal.append(f"贷：生产成本——基本生产成本（{item['name']}）     {_m(sheet['completed_total'])}")
    steps = [
        f"材料分配率 {r['material_rate']:.6f}，人工分配率 {r['labor_rate']:.6f}，制造费用分配率 {r['overhead_rate']:.6f}。",
        "各产品费用分配后，分别按约当产量法分配完工与在产品成本。",
    ]
    return CostResult(
        chapter="第六章 品种法",
        title="多品种品种法",
        description="共同费用按材料定额和生产工时分配，再分别计算各产品成本。",
        question=f"本月生产 {len(r['products'])} 种产品，直接材料 {_m(total_material)}、直接人工 {_m(total_labor)}、制造费用 {_m(total_overhead)} 元。",
        formulas=["材料分配率 = 材料总额 ÷ Σ（产量 × 单位材料定额）", "人工/制造费用分配率 = 费用总额 ÷ Σ生产工时", "各产品按约当产量法分配完工与在产品"],
        steps=steps, tables=tables, journal=journal,
        summary=["多品种品种法先分配共同费用，再分别计算各产品完工成本与在产品成本。"],
        metrics={"完工产品成本合计": _m(r["total_completed"]), "在产品成本合计": _m(r["total_wip"]), "产品种数": str(len(r["products"]))},
        conclusion=f"多品种完工产品成本合计 {_m(r['total_completed'])} 元。",
    )



# ---------------------------------------------------------------------------
# 第七章 分批法
# ---------------------------------------------------------------------------
def normal_batch_result(overhead: float, batches: Sequence[Dict[str, Any]]) -> CostResult:
    r = ch7.normal_batch(batches, overhead)
    headers = ["批次号", "产品", "直接材料", "直接人工", "生产工时", "制造费用", "总成本", "完工数量", "单位成本"]
    rows = [
        [row["name"], row["product"], _m(row["material"]), _m(row["labor"]), f"{row['hours']:,.2f}", _m(row["overhead"]),
         _m(row["total"]), f"{row['completed_qty']:,.2f}", _m(row["unit_cost"]) if row["unit_cost"] is not None else "在产品"]
        for row in r["rows"]
    ]
    rows.append(["合计", "—", _m(sum(row["material"] for row in r["rows"])), _m(sum(row["labor"] for row in r["rows"])), f"{r['total_hours']:,.2f}", _m(r["overhead"]), _m(r["total"]), "—", "—"])
    steps = [f"制造费用分配率 = {_m(r['overhead'])} ÷ {r['total_hours']:,.2f} = {r['rate']:.6f}。"]
    for row in r["rows"]:
        steps.append(f"{row['name']}：制造费用 {_m(row['overhead'])}，总成本 {_m(row['total'])}" + (f"，单位成本 {_m(row['unit_cost'])}。" if row["completed"] else "，未完工保留为在产品。"))
    journal = ["借：生产成本——基本生产成本"]
    for row in r["rows"]:
        journal.append(f"    ——{row['name']}（{row['product']}）     {_m(row['overhead'])}")
    journal.append(f"贷：制造费用     {_m(r['overhead'])}")
    for row in r["rows"]:
        if row["completed"]:
            journal.append(f"借：库存商品——{row['product']}     {_m(row['total'])}")
            journal.append(f"贷：生产成本——基本生产成本（{row['name']}）     {_m(row['total'])}")
    return CostResult(
        chapter="第七章 分批法",
        title="普通分批法",
        description="按批别归集直接费用，制造费用按生产工时分配。",
        question=f"本月 {len(batches)} 个批次，制造费用 {_m(overhead)} 元，按生产工时分配。",
        formulas=["制造费用分配率 = 制造费用总额 ÷ 各批工时合计", "某批总成本 = 直接材料 + 直接人工 + 制造费用", "完工批次单位成本 = 总成本 ÷ 完工数量"],
        steps=steps,
        tables=[("普通分批法产品成本计算表", headers, rows)],
        journal=journal,
        summary=["普通分批法下未完工批次也负担制造费用，全部成本保留为在产品。"],
        metrics={"完工批次成本": _m(r["completed_total"]), "在产品成本": _m(r["wip_total"]), "制造费用分配率": f"{r['rate']:.6f}"},
        conclusion=f"完工批次成本 {_m(r['completed_total'])} 元，在产品成本 {_m(r['wip_total'])} 元。",
    )


def simplified_batch_result(overhead: float, batches: Sequence[Dict[str, Any]]) -> CostResult:
    r = ch7.simplified_batch(batches, overhead)
    headers = ["批次号", "产品", "累计材料", "累计人工", "累计工时", "分配间接费用", "完工成本", "在产品直接成本", "完工数量", "单位成本"]
    rows = [
        [row["name"], row["product"], _m(row["material"]), _m(row["labor"]), f"{row['hours']:,.2f}", _m(row["overhead"]),
         _m(row["total"]) if row["completed"] else "—", _m(row["wip_direct"]) if not row["completed"] else "—",
         f"{row['completed_qty']:,.2f}", _m(row["unit_cost"]) if row["unit_cost"] is not None else "—"]
        for row in r["rows"]
    ]
    steps = [f"累计间接费用分配率 = {_m(r['overhead'])} ÷ {r['total_hours']:,.2f} = {r['rate']:.6f}。"]
    for row in r["rows"]:
        if row["completed"]:
            steps.append(f"{row['name']}：分配间接费用 {_m(row['overhead'])}，总成本 {_m(row['total'])}。")
        else:
            steps.append(f"{row['name']}：未完工，不分配间接费用，直接费用 {_m(row['total'])} 保留为在产品。")
    steps.append(f"未分配累计间接费用 {_m(r['unallocated_overhead'])} 元留在基本生产成本二级账。")
    journal = ["借：生产成本——基本生产成本（完工批次）"]
    for row in r["rows"]:
        if row["completed"]:
            journal.append(f"    ——{row['name']}（{row['product']}）     {_m(row['overhead'])}")
    journal.append(f"贷：制造费用     {_m(r['allocated_total'])}")
    for row in r["rows"]:
        if row["completed"]:
            journal.append(f"借：库存商品——{row['product']}     {_m(row['total'])}")
            journal.append(f"贷：生产成本——基本生产成本（{row['name']}）     {_m(row['total'])}")
    balance_headers = ["项目", "金额（元）"]
    balance_rows = [
        ["累计制造费用", _m(r["overhead"])], ["已分配累计间接费用", _m(r["allocated_total"])],
        ["未分配累计间接费用", _m(r["unallocated_overhead"])], ["完工批次成本合计", _m(r["completed_total"])],
        ["未完工批次直接成本", _m(r["wip_direct_total"])], ["期末在产品成本（含未分配间接费用）", _m(r["wip_total_with_overhead"])],
    ]
    return CostResult(
        chapter="第七章 分批法",
        title="简化分批法（累计间接费用分配法）",
        description="只对完工批次分配累计间接费用，未完工批次保留直接费用。",
        question=f"累计制造费用 {_m(overhead)} 元，各批累计工時和直接费用已知。",
        formulas=["累计间接费用分配率 = 累计制造费用 ÷ 累计工时合计", "完工批次间接费用 = 该批累计工时 × 分配率", "未完工批次不分配间接费用"],
        steps=steps,
        tables=[("简化分批法产品成本计算表", headers, rows), ("基本生产成本二级账平衡表", balance_headers, balance_rows)],
        journal=journal,
        summary=["未分配累计间接费用留在基本生产成本二级账，与未完工批次直接成本共同构成期末在产品成本。"],
        metrics={"累计间接费用分配率": f"{r['rate']:.6f}", "完工批次成本": _m(r["completed_total"]), "未分配间接费用": _m(r["unallocated_overhead"])},
        conclusion=f"完工批次成本 {_m(r['completed_total'])} 元，未分配间接费用 {_m(r['unallocated_overhead'])} 元。",
    )



# ---------------------------------------------------------------------------
# 第八章 分步法
# ---------------------------------------------------------------------------
def comprehensive_step_result(steps: Sequence[Dict[str, Any]]) -> CostResult:
    r = ch8.step_comprehensive(steps)
    tables: List[Tuple[str, Sequence[Any], Sequence[Sequence[Any]]]] = []
    for item in r["results"]:
        headers = ["成本项目", "费用总额（元）", "约当产量/数量", "分配率", "完工产品成本", "期末在产品成本"]
        tables.append((f"{item['step']['name']}产品成本计算单（综合结转）", headers, item["rows"]))
    restoration_headers = ["成本项目", "还原前成本", "半成品还原", "还原后成本"]
    tables.append(("产成品成本还原计算表", restoration_headers, r["restoration_rows"]))
    final_qty = steps[-1]["completed_qty"]
    final_headers = ["成本项目", "还原后金额（元）", "单位成本（元/件）"]
    final_rows = [
        ["直接材料", _m(r["restored"]["直接材料"]), _m(r["restored"]["直接材料"] / final_qty)],
        ["直接人工", _m(r["restored"]["直接人工"]), _m(r["restored"]["直接人工"] / final_qty)],
        ["制造费用", _m(r["restored"]["制造费用"]), _m(r["restored"]["制造费用"] / final_qty)],
        ["合计", _m(r["restored_total"]), _m(r["restored_total"] / final_qty)],
    ]
    tables.append(("还原后产成品成本计算单", final_headers, final_rows))
    steps_lines = []
    for i, item in enumerate(r["results"]):
        steps_lines.append(f"{item['step']['name']}完工成本 {_m(item['completed_total'])} 元，期末在产品成本 {_m(item['wip_total'])} 元。")
        if i > 0:
            steps_lines.append(f"上一步骤转入半成品成本 {_m(r['completed_totals'][i - 1])} 元。")
    if len(steps) > 1:
        steps_lines.append(f"成本还原后：直接材料 {_m(r['restored']['直接材料'])} 元，直接人工 {_m(r['restored']['直接人工'])} 元，制造费用 {_m(r['restored']['制造费用'])} 元。")
    journal = []
    for i in range(len(steps) - 1):
        journal.append(f"借：生产成本——基本生产成本（{steps[i + 1]['name']}）     {_m(r['completed_totals'][i])}")
        journal.append(f"贷：生产成本——基本生产成本（{steps[i]['name']}）     {_m(r['completed_totals'][i])}")
    journal.append(f"借：库存商品——{steps[-1]['product']}     {_m(r['final_total'])}")
    journal.append(f"贷：生产成本——基本生产成本（{steps[-1]['name']}）     {_m(r['final_total'])}")
    return CostResult(
        chapter="第八章 分步法",
        title="逐步结转分步法——综合结转（含成本还原）",
        description="半成品成本以“半成品”综合项目结转，最终产成品进行成本还原。",
        question="多步骤生产，半成品成本综合结转，要求编制各步骤成本计算单、成本还原表并编制结转分录。",
        formulas=["某步骤加工费约当产量 = 完工数量 + 在产品数量 × 完工程度", "半成品约当产量 = 完工数量 + 在产品数量", "成本还原率 = 产成品所耗半成品成本 ÷ 上一步骤完工半成品总成本"],
        steps=steps_lines, tables=tables, journal=journal,
        summary=["综合结转法下最终产成品成本需要成本还原；成本还原只用于分析，不改变总成本。"],
        metrics={"最终产成品成本": _m(r["final_total"]), "还原后直接材料": _m(r["restored"]["直接材料"]), "期末在产品成本": _m(r["final_wip"])},
        conclusion=f"产成品成本 {_m(r['final_total'])} 元，还原后仍为 {_m(r['restored_total'])} 元。",
    )


def itemized_step_result(steps: Sequence[Dict[str, Any]]) -> CostResult:
    r = ch8.step_itemized(steps)
    tables: List[Tuple[str, Sequence[Any], Sequence[Sequence[Any]]]] = []
    for item in r["results"]:
        headers = ["成本项目", "费用总额（元）", "约当产量/数量", "分配率", "完工产品成本", "期末在产品成本"]
        tables.append((f"{item['step']['name']}产品成本计算单（分项结转）", headers, item["rows"]))
    final_qty = steps[-1]["completed_qty"]
    final_components = r["final_components"]
    final_headers = ["成本项目", "完工总成本（元）", "单位成本（元/件）"]
    final_rows = [
        ["直接材料", _m(final_components["直接材料"]), _m(final_components["直接材料"] / final_qty)],
        ["直接人工", _m(final_components["直接人工"]), _m(final_components["直接人工"] / final_qty)],
        ["制造费用", _m(final_components["制造费用"]), _m(final_components["制造费用"] / final_qty)],
        ["合计", _m(r["final_total"]), _m(r["final_total"] / final_qty)],
    ]
    tables.append(("分项结转法最终产成品成本计算单", final_headers, final_rows))
    steps_lines = [f"最终产成品成本 {_m(r['final_total'])} 元，直接材料 {_m(final_components['直接材料'])} 元。" ]
    steps_lines.append("上步转入成本按实物数量比例分配，本步加工费按约当产量分配。")
    journal = []
    for i in range(len(steps) - 1):
        journal.append(f"借：生产成本——基本生产成本（{steps[i + 1]['name']}）     {_m(r['results'][i]['completed_total'])}")
        journal.append(f"贷：生产成本——基本生产成本（{steps[i]['name']}）     {_m(r['results'][i]['completed_total'])}")
    journal.append(f"借：库存商品——{steps[-1]['product']}     {_m(r['final_total'])}")
    journal.append(f"贷：生产成本——基本生产成本（{steps[-1]['name']}）     {_m(r['final_total'])}")
    return CostResult(
        chapter="第八章 分步法",
        title="逐步结转分步法——分项结转",
        description="半成品成本按成本项目分项结转，最终产成品保留原始成本项目。",
        question="多步骤生产，半成品成本按直接材料、直接人工、制造费用分项结转。",
        formulas=["上步转入成本按实物数量比例分配", "本步加工费按约当产量分配", "分项结转一般不需要成本还原"],
        steps=steps_lines, tables=tables, journal=journal,
        summary=["分项结转法保留原始成本项目，但转账工作量相对较大。"],
        metrics={"最终产成品成本": _m(r["final_total"]), "直接材料": _m(final_components["直接材料"]), "期末在产品成本": _m(r["final_wip"])},
        conclusion=f"分项结转法最终产成品成本 {_m(r['final_total'])} 元。",
    )



def parallel_step_result(final_qty: float, steps: Sequence[Dict[str, Any]]) -> CostResult:
    r = ch8.parallel_method(final_qty, steps)
    tables: List[Tuple[str, Sequence[Any], Sequence[Sequence[Any]]]] = []
    headers = ["成本项目", "本步骤费用（元）", "约当产量", "分配率", "产成品份额（元）", "广义在产品成本（元）"]
    for item in r["results"]:
        tables.append((f"{item['step']['name']}成本份额计算表", headers, item["rows"]))
    final_headers = ["成本项目", "产成品成本（元）", "单位成本（元/件）"]
    final_rows = [
        ["直接材料", _m(r["shares"]["直接材料"]), _m(r["shares"]["直接材料"] / final_qty)],
        ["直接人工", _m(r["shares"]["直接人工"]), _m(r["shares"]["直接人工"] / final_qty)],
        ["制造费用", _m(r["shares"]["制造费用"]), _m(r["shares"]["制造费用"] / final_qty)],
        ["合计", _m(r["final_total"]), _m(r["final_total"] / final_qty)],
    ]
    tables.append(("平行结转法产成品成本汇总表", final_headers, final_rows))
    wip_headers = ["项目", "金额（元）"]
    wip_rows = [
        ["各步骤费用总额", _m(r["total_cost"])], ["产成品成本", _m(r["final_total"])],
        ["广义在产品成本合计", _m(r["total_wip"])], ["平衡校验", _m(r["total_cost"] - r["final_total"])],
    ]
    tables.append(("平行结转法成本平衡表", wip_headers, wip_rows))
    steps_lines = [
        f"{item['step']['name']}：产成品份额 {_m(item['share'])} 元，广义在产品成本 {_m(item['wip'])} 元。"
        for item in r["results"]
    ]
    steps_lines.append(f"产成品成本合计 {_m(r['final_total'])} 元，广义在产品成本 {_m(r['total_wip'])} 元。")
    journal = [f"借：库存商品——甲产品     {_m(r['final_total'])}"]
    for item in r["results"]:
        journal.append(f"贷：生产成本——基本生产成本（{item['step']['name']}）     {_m(item['share'])}")
    return CostResult(
        chapter="第八章 分步法",
        title="平行结转分步法（广义在产品）",
        description="各步骤只计算应计入最终产成品的份额，不结转半成品成本。",
        question=f"最终产成品 {final_qty:,.2f} 件，各步骤在产品数量和本步骤费用已知。要求计算产成品份额和广义在产品成本。",
        formulas=["某步骤约当产量 = 最终产成品数量 + 本步骤在产品约当产量 + 后续步骤在产品数量", "产成品份额 = 最终产成品数量 × 分配率", "广义在产品成本 = 本步骤费用 - 产成品份额"],
        steps=steps_lines, tables=tables, journal=journal,
        summary=["平行结转法下各步骤只计算份额，不逐步结转半成品成本；关键是正确确定广义在产品。"],
        metrics={"产成品成本": _m(r["final_total"]), "广义在产品成本": _m(r["total_wip"]), "费用总额": _m(r["total_cost"])},
        conclusion=f"产成品成本 {_m(r['final_total'])} 元，广义在产品成本 {_m(r['total_wip'])} 元。",
    )



# ---------------------------------------------------------------------------
# 第九章 辅助成本计算方法
# ---------------------------------------------------------------------------
def classification_result(category: str, total: float, products: Sequence[Dict[str, Any]]) -> CostResult:
    r = ch9.classification_method(category, total, products)
    headers = ["产品名称", "产量", "系数", "标准产量", "分配率", "分配成本（元）", "单位成本（元/件）"]
    rows = [
        [name, f"{output:,.2f}", f"{coef:g}", f"{standard:,.2f}", f"{r['rate']:.6f}", _m(amount), _m(unit_cost)]
        for name, output, coef, standard, amount, unit_cost in zip(
            r["names"], r["outputs"], r["coefficients"], r["standards"], r["allocations"], r["unit_costs"]
        )
    ]
    rows.append(["合计", f"{sum(r['outputs']):,.2f}", "—", f"{r['standard_total']:,.2f}", "—", _m(sum(r["allocations"])), "—"])
    steps = [
        f"标准产量合计 {r['standard_total']:,.2f}；分类法分配率 {r['rate']:.6f}。",
    ]
    for name, amount, unit_cost in zip(r["names"], r["allocations"], r["unit_costs"]):
        steps.append(f"{name}：分配成本 {_m(amount)} 元，单位成本 {_m(unit_cost)} 元/件。")
    journal = [f"借：库存商品——{name}     {_m(amount)}" for name, amount in zip(r["names"], r["allocations"])]
    journal.append(f"贷：生产成本——基本生产成本（{category}）     {_m(r['total'])}")
    return CostResult(
        chapter="第九章 辅助成本计算方法",
        title="产品成本分类法",
        description="按类别归集成本，再按系数折算标准产量分配。",
        question=f"{category}类别总成本 {_m(r['total'])} 元，类内各产品产量和系数已知。",
        formulas=["标准产量 = 产量 × 系数", "分配率 = 类别总成本 ÷ 标准产量合计", "某产品成本 = 标准产量 × 分配率"],
        steps=steps, tables=[("分类法产品成本计算表", headers, rows)], journal=journal,
        summary=["系数应能反映各产品之间的成本差异。"],
        metrics={"分配率": f"{r['rate']:.6f}", "类别总成本": _m(r["total"])},
        conclusion=f"分类法分配率 {r['rate']:.6f}，类别成本已分配。",
    )


def joint_result(total: float, products: Sequence[Dict[str, Any]], method: str) -> CostResult:
    r = ch9.joint_products(total, products, method)
    headers = ["联产品", "产量", "售价（元/件）", "售价总额（元）", "进一步加工成本（元）", "分配基础", "分配联合成本（元）", "单位成本（元/件）", "毛利（元）"]
    rows = []
    for i, name in enumerate(r["names"]):
        rows.append([
            name, f"{r['outputs'][i]:,.2f}", _m(r["prices"][i]), _m(r["sales_values"][i]),
            _m(r["further_costs"][i]), f"{r['weights'][i]:,.2f}", _m(r["allocations"][i]),
            _m(r["unit_costs"][i]), _m(r["margins"][i]),
        ])
    rows.append(["合计", "—", "—", _m(sum(r["sales_values"])), _m(sum(r["further_costs"])), f"{r['weight_total']:,.2f}", _m(sum(r["allocations"])), "—", _m(sum(r["margins"]))])
    journal = ["借：库存商品"]
    for name, amount in zip(r["names"], r["allocations"]):
        journal.append(f"    ——{name}     {_m(amount)}")
    journal.append(f"贷：生产成本——联产品联合成本     {_m(r['total'])}")
    steps = [f"分配基础合计 {r['weight_total']:,.2f}；联合成本分配率 {r['rate']:.6f}。"]
    for i, name in enumerate(r["names"]):
        steps.append(f"{name}：分配联合成本 {_m(r['allocations'][i])} 元，单位成本 {_m(r['unit_costs'][i])} 元/件。")
    return CostResult(
        chapter="第九章 辅助成本计算方法",
        title=f"联产品成本分配——{method}",
        description="按售价、实物量或可变现净值分配联合成本。",
        question=f"联合成本 {_m(r['total'])} 元，采用{method}分配。",
        formulas=["售价法：按售价总额分配", "实物量法：按产量分配", "可变现净值法：按售价 - 进一步加工成本分配"],
        steps=steps, tables=[(f"联产品成本分配表——{method}", headers, rows)], journal=journal,
        summary=["售价法适用于分离点售价可靠的产品；可变现净值法考虑了进一步加工成本。"],
        metrics={"分配率": f"{r['rate']:.6f}", "联合成本": _m(r["total"])},
        conclusion=f"{method}联合成本分配完成，分配额合计 {_m(sum(r['allocations']))} 元。",
    )



def byproduct_result(total: float, main_output: float, by_output: float, by_price: float, further: float) -> CostResult:
    r = ch9.byproduct_method(total, main_output, by_output, by_price, further)
    question = f"联合成本 {_m(r['total'])} 元，主产品 {r['main_output']:,.2f} 件，副产品 {r['byproduct_output']:,.2f} 件，副产品售价 {_m(r['byproduct_price'])} 元/件。"
    formulas = ["副产品价值 = 副产品产量 × 售价 - 进一步加工成本", "主产品联合成本 = 联合成本 - 副产品价值"]
    steps = [
        f"副产品价值 {_m(r['byproduct_value'])} 元；主产品应负担联合成本 {_m(r['main_cost'])} 元。",
        f"主产品单位成本 {_m(r['main_unit_cost'])} 元/件，副产品单位成本 {_m(r['byproduct_unit_cost'])} 元/件。",
    ]
    headers = ["项目", "主产品", "副产品", "合计"]
    rows = [
        ["产量", f"{r['main_output']:,.2f}", f"{r['byproduct_output']:,.2f}", "—"],
        ["应负担成本（元）", _m(r["main_cost"]), _m(r["byproduct_value"]), _m(r["total"])],
        ["单位成本（元/件）", _m(r["main_unit_cost"]), _m(r["byproduct_unit_cost"]), "—"],
    ]
    journal = [
        f"借：库存商品——主产品     {_m(r['main_cost'])}",
        f"借：库存商品——副产品     {_m(r['byproduct_value'])}",
        f"贷：生产成本——联合成本     {_m(r['total'])}",
    ]
    return CostResult(
        chapter="第九章 辅助成本计算方法",
        title="副产品成本计算",
        description="按副产品价值冲减联合成本，计算主产品成本和副产品成本。",
        question=question, formulas=formulas, steps=steps,
        tables=[("主产品与副产品成本计算表", headers, rows)], journal=journal,
        summary=["副产品价值通常按售价扣除进一步加工成本后的净额确定。"],
        metrics={"副产品价值": _m(r["byproduct_value"]), "主产品成本": _m(r["main_cost"]), "主产品单位成本": _m(r["main_unit_cost"])},
        conclusion=f"主产品成本 {_m(r['main_cost'])} 元，副产品价值 {_m(r['byproduct_value'])} 元。",
    )


def norm_result(completed: float, wip: float, new_quota: Dict[str, float], old_quota: Dict[str, float], actual: Dict[str, float], material_rate: float) -> CostResult:
    r = ch9.norm_method(completed, wip, new_quota, old_quota, actual, material_rate)
    quota_headers = ["成本项目", "定额成本", "实际费用", "脱离定额差异", "定额变动差异", "材料成本差异"]
    alloc_headers = ["项目", "定额成本", "差异分配", "调整后成本"]
    steps = [
        f"定额成本合计 {_m(r['quota_total'])} 元，实际费用合计 {_m(r['actual_total'])} 元。",
        f"脱离定额差异 {_m(sum(r['deviation_values']))} 元，定额变动差异 {_m(sum(r['change_values']))} 元，材料成本差异 {_m(r['material_difference'])} 元。",
        f"完工产品实际成本 {_m(r['completed_actual'])} 元，单位成本 {_m(r['unit_cost'])} 元/件。",
    ]
    journal = [
        f"借：库存商品     {_m(r['completed_actual'])}",
        f"贷：生产成本——基本生产成本     {_m(r['completed_actual'])}",
    ]
    return CostResult(
        chapter="第九章 辅助成本计算方法",
        title="定额法（定额成本与三类差异）",
        description="计算定额成本、脱离定额差异、定额变动差异和材料成本差异。",
        question=f"完工 {completed:,.2f} 件，在产品 {wip:,.2f} 件，材料成本差异率 {_p(material_rate)}。",
        formulas=["实际成本 = 定额成本 ± 脱离定额差异 ± 定额变动差异 ± 材料成本差异", "差异按完工与在产品定额成本比例分配"],
        steps=steps,
        tables=[("定额成本与差异计算表", quota_headers, r["quota_rows"]), ("完工产品与在产品成本计算表", alloc_headers, r["allocation_rows"])],
        journal=journal,
        summary=["定额法把定额成本与各类差异分开反映，便于成本控制和差异分析。"],
        metrics={"完工产品实际成本": _m(r["completed_actual"]), "单位成本": _m(r["unit_cost"]), "差异合计": _m(r["difference_total"])},
        conclusion=f"完工产品实际成本 {_m(r['completed_actual'])} 元，单位成本 {_m(r['unit_cost'])} 元/件。",
    )



# ---------------------------------------------------------------------------
# 第十章 成本报表与成本分析
# ---------------------------------------------------------------------------
def production_report_result(products: Sequence[Dict[str, Any]]) -> CostResult:
    r = ch10.production_cost_report(products)
    headers = ["产品", "产量", "实际材料", "实际人工", "实际制造费用", "实际总成本", "单位实际成本", "计划总成本", "差异"]
    rows = [
        [row["name"], f"{row['output']:,.2f}", _m(row["actual_material"]), _m(row["actual_labor"]), _m(row["actual_overhead"]),
         _m(row["actual_total"]), _m(row["unit_actual"]), _m(row["plan_total"]), _m(row["difference"])]
        for row in r["rows"]
    ]
    rows.append(["合计", "—", _m(sum(row["actual_material"] for row in r["rows"])), _m(sum(row["actual_labor"] for row in r["rows"])),
                 _m(sum(row["actual_overhead"] for row in r["rows"])), _m(r["total_actual"]), "—", _m(r["total_plan"]), _m(r["difference"])])
    chart = visual.plot_comparison_chart(
        [row["name"] for row in r["rows"]],
        {"实际总成本": [row["actual_total"] for row in r["rows"]], "计划总成本": [row["plan_total"] for row in r["rows"]]},
        "全部产品实际与计划总成本对比",
        "web_全部产品生产成本对比",
    )
    chart_paths = [str(chart)] if chart else []
    return CostResult(
        chapter="第十章 成本报表与分析",
        title="全部产品生产成本报表",
        description="编制全部产品实际与计划生产成本报表。",
        question="各产品产量、实际单位成本和计划单位成本已知，要求编制全部产品生产成本报表。",
        formulas=["实际总成本 = 产量 × 单位实际成本", "计划总成本 = 产量 × 单位计划成本", "差异 = 实际总成本 - 计划总成本"],
        steps=[f"全部产品实际总成本 {_m(r['total_actual'])} 元，计划总成本 {_m(r['total_plan'])} 元，差异 {_m(r['difference'])} 元。"],
        tables=[("全部产品生产成本报表", headers, rows)],
        journal=["本报表为成本报表编制，不涉及单独会计分录。"],
        summary=["成本报表应结合产量、品种结构和单位成本进一步分析。"],
        metrics={"实际总成本": _m(r["total_actual"]), "计划总成本": _m(r["total_plan"]), "成本差异": _m(r["difference"])},
        chart_paths=chart_paths,
        conclusion=f"全部产品实际总成本 {_m(r['total_actual'])} 元，差异 {_m(r['difference'])} 元。",
    )


def comparable_result(products: Sequence[Dict[str, Any]]) -> CostResult:
    r = ch10.comparable_product_analysis(products)
    headers = ["产品", "计划产量", "实际产量", "上年单位成本", "计划单位成本", "实际单位成本", "计划降低额", "实际降低额"]
    rows = [
        [row["name"], f"{row['plan_output']:,.2f}", f"{row['actual_output']:,.2f}", _m(row["last_year_unit"]),
         _m(row["plan_unit"]), _m(row["actual_unit"]), _m(row["plan_reduction"]), _m(row["actual_reduction"])]
        for row in r["rows"]
    ]
    rows.append(["合计", "—", "—", "—", "—", "—", _m(r["plan_reduction"]), _m(r["actual_reduction"])])
    factor_headers = ["影响因素", "影响金额（元）", "说明"]
    factor_rows = [
        ["产量变动", _m(r["output_effect"]), "产量变化对降低额的影响"],
        ["品种结构变动", _m(r["structure_effect"]), "产品结构变化对降低额的影响"],
        ["单位成本变动", _m(r["unit_cost_effect"]), "单位成本变化对降低额的影响"],
        ["合计", _m(r["factor_total"]), "应等于实际降低额 - 计划降低额"],
    ]
    chart = visual.plot_comparison_chart(
        [row["name"] for row in r["rows"]],
        {"上年基准": [row["actual_base"] for row in r["rows"]], "按计划单位成本计算": [row["plan_cost_at_actual"] for row in r["rows"]], "本年实际": [row["actual_cost"] for row in r["rows"]]},
        "可比产品成本对比",
        "web_可比产品成本对比",
    )
    chart_paths = [str(chart)] if chart else []
    return CostResult(
        chapter="第十章 成本报表与分析",
        title="可比产品成本降低额与降低率分析",
        description="计算计划/实际降低额、降低率，并进行三因素分析。",
        question="各可比产品计划产量、实际产量及上年、计划、实际单位成本已知。",
        formulas=["降低额 = 按上年单位成本计算的总成本 - 实际总成本", "降低率 = 降低额 ÷ 按上年单位成本计算的总成本", "三因素：产量、品种结构、单位成本"],
        steps=[
            f"计划降低额 {_m(r['plan_reduction'])} 元，计划降低率 {_p(r['plan_rate'])}。",
            f"实际降低额 {_m(r['actual_reduction'])} 元，实际降低率 {_p(r['actual_rate'])}。",
            f"产量影响 {_m(r['output_effect'])}，结构影响 {_m(r['structure_effect'])}，单位成本影响 {_m(r['unit_cost_effect'])}。",
        ],
        tables=[("可比产品成本降低额计算表", headers, rows), ("可比产品成本降低因素分析表", factor_headers, factor_rows)],
        journal=["本分析为成本报表分析，不涉及单独会计分录。"],
        summary=["三因素影响合计应与实际降低额减计划降低额一致。"],
        metrics={"计划降低率": _p(r["plan_rate"]), "实际降低率": _p(r["actual_rate"]), "实际降低额": _m(r["actual_reduction"])},
        chart_paths=chart_paths,
        conclusion=f"实际降低额 {_m(r['actual_reduction'])} 元，实际降低率 {_p(r['actual_rate'])}。",
    )



def unit_cost_result(data: Dict[str, Any]) -> CostResult:
    r = ch10.unit_cost_analysis(data)
    headers = ["成本项目", "上年实际", "本年计划", "本年实际", "比计划差异", "比上年差异", "比计划差异率"]
    rows = []
    for row in r["rows"]:
        rows.append([
            row["name"], _m(row["last_year"]), _m(row["plan"]), _m(row["actual"]),
            _m(row["diff_plan"]), _m(row["diff_last_year"]), _p(row["change_rate"]) if row["change_rate"] is not None else "—",
        ])
    rows.append(["合计", _m(r["last_year_total"]), _m(r["plan_total"]), _m(r["actual_total"]), _m(r["difference"]), _m(r["difference_last_year"]), "—"])
    factor_headers = ["差异因素", "影响金额（元）", "说明"]
    factor_rows = [
        ["材料用量差异", _m(r["material_qty_effect"]), "（实际用量 - 计划用量）× 计划单价"],
        ["材料价格差异", _m(r["material_price_effect"]), "（实际单价 - 计划单价）× 实际用量"],
        ["人工效率差异", _m(r["labor_efficiency_effect"]), "（实际工时 - 计划工时）× 计划工资率"],
        ["工资率差异", _m(r["labor_rate_effect"]), "（实际工资率 - 计划工资率）× 实际工时"],
        ["制造费用差异", _m(r["overhead_effect"]), "实际制造费用 - 计划制造费用"],
        ["合计", _m(r["factor_total"]), "应等于单位成本实际与计划的差异"],
    ]
    chart = visual.plot_comparison_chart(
        [row["name"] for row in r["rows"]],
        {"上年实际": [row["last_year"] for row in r["rows"]], "本年计划": [row["plan"] for row in r["rows"]], "本年实际": [row["actual"] for row in r["rows"]]},
        f"{r['product']}单位成本项目对比",
        f"web_{r['product']}_单位成本对比",
    )
    chart_paths = [str(chart)] if chart else []
    return CostResult(
        chapter="第十章 成本报表与分析",
        title=f"主要产品单位成本分析——{r['product']}",
        description="分析单位成本项目差异，并分解材料量价差异、人工效率与工资率差异。",
        question=f"{r['product']}上年、计划、实际单位成本及材料、人工用量价格资料已知。",
        formulas=["材料用量差异 =（实际用量 - 计划用量）× 计划单价", "材料价格差异 =（实际单价 - 计划单价）× 实际用量", "人工效率差异 =（实际工时 - 计划工时）× 计划工资率", "工资率差异 =（实际工资率 - 计划工资率）× 实际工时"],
        steps=[
            f"实际单位成本 {_m(r['actual_total'])} 元/件，比计划 {_m(r['difference'])}，比上年 {_m(r['difference_last_year'])}。",
            f"材料用量差异 {_m(r['material_qty_effect'])}，材料价格差异 {_m(r['material_price_effect'])}。",
            f"人工效率差异 {_m(r['labor_efficiency_effect'])}，工资率差异 {_m(r['labor_rate_effect'])}。",
        ],
        tables=[("主要产品单位成本分析表", headers, rows), ("单位成本差异因素分析表", factor_headers, factor_rows)],
        journal=["本分析为成本报表分析，不涉及单独会计分录。"],
        summary=["差异因素合计应与单位成本实际与计划的差异一致。"],
        metrics={"实际单位成本": _m(r["actual_total"]), "比计划差异": _m(r["difference"]), "差异因素合计": _m(r["factor_total"])},
        chart_paths=chart_paths,
        conclusion=f"实际单位成本 {_m(r['actual_total'])} 元/件，比计划 {_m(r['difference'])} 元/件。",
    )


def structure_result(items: Sequence[Dict[str, Any]]) -> CostResult:
    r = ch10.cost_structure_analysis(items)
    headers = ["成本项目", "本期金额", "上期金额", "本期结构", "上期结构", "结构变动", "金额变动", "变动率", "对总变动贡献"]
    rows = []
    for row in r["rows"]:
        rows.append([
            row["name"], _m(row["current"]), _m(row["prior"]), _p(row["current_structure"]), _p(row["prior_structure"]),
            f"{row['structure_change'] * 100:+.2f} 个百分点", _m(row["change"]),
            _p(row["change_rate"]) if row["change_rate"] is not None else "—",
            _p(row["contribution"]) if row["contribution"] is not None else "—",
        ])
    rows.append(["合计", _m(r["current_total"]), _m(r["prior_total"]), "100.00%", "100.00%", "—", _m(r["total_change"]), _p(r["total_change_rate"]), "100.00%"])
    labels = [row["name"] for row in r["rows"]]
    current = [row["current"] for row in r["rows"]]
    prior = [row["prior"] for row in r["rows"]]
    chart_paths = []
    for path in (
        visual.plot_cost_pie(labels, current, "本期成本项目结构饼图", "web_成本结构饼图"),
        visual.plot_structure_chart(labels, current, "本期成本项目结构分析", "web_成本结构分析"),
        visual.plot_comparison_chart(labels, {"本期实际": current, "上期实际": prior}, "成本项目同比对比", "web_成本同比对比"),
    ):
        if path:
            chart_paths.append(str(path))
    return CostResult(
        chapter="第十章 成本报表与分析",
        title="成本项目结构与同比变动分析",
        description="计算结构占比、结构变动、金额变动率和对总变动贡献，并自动生成三张图。",
        question="各成本项目本期和上期金额已知，要求进行结构分析和同比变动分析。",
        formulas=["结构占比 = 项目金额 ÷ 成本合计", "结构变动 = 本期结构 - 上期结构", "对总变动贡献 = 项目金额变动 ÷ 成本总变动"],
        steps=[
            f"本期成本合计 {_m(r['current_total'])} 元，上期 {_m(r['prior_total'])} 元，总变动 {_m(r['total_change'])} 元。",
            f"总变动率 {_p(r['total_change_rate'])}。",
        ],
        tables=[("成本项目结构与同比变动分析表", headers, rows)],
        journal=["本分析为成本报表分析，不涉及单独会计分录。"],
        summary=["结构分析应结合金额变动率和结构变动百分点判断成本变动来源。"],
        metrics={"本期成本": _m(r["current_total"]), "上期成本": _m(r["prior_total"]), "总变动": _m(r["total_change"]), "总变动率": _p(r["total_change_rate"])},
        chart_paths=chart_paths,
        conclusion=f"本期成本 {_m(r['current_total'])} 元，较上期变动 {_m(r['total_change'])} 元。",
    )

